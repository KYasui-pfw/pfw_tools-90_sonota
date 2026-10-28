"""現品票発行（メイン画面）。

起動: Genpin_Start.bat（streamlit run 1_現品票発行.py --server.port 8502）

この画面がするのは「表示」と「ボタンの受け付け」だけ。中身の処理は genpin/ にある:
    データ更新          genpin/update.py   （夜間処理 create_report.py・dbupdate.py と共通）
    一覧の組み立て      genpin/listing.py
    現品票の Excel      genpin/tag_excel.py
    i-Reporter の帳票   genpin/conmas.py
"""

import traceback
from datetime import timedelta

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder

from genpin import config, conmas, db, listing, portal_api, rbom, tag_excel, ui, update

# 一覧で「ゲージ」の列名。DB の列名は G のまま（i-Reporter が G で読んでいるため）、画面だけ名前を変える。
GAUGE_LABEL = "ｹﾞｰｼﾞ"

# 絞り込みのプルダウンを出す列（画面の見出し, 一覧の列名）。
SELECT_FILTERS = [
    ("組立番号", "組立番号"),
    ("機種", "機種"),
    ("部品名", "部品名"),
    ("吋", "吋"),
    (GAUGE_LABEL, "G"),
    ("客先名", "客先名"),
]
# 文字で探す列（画面の見出し, 一覧の列名, 既定の探し方）。
TEXT_FILTERS = [
    ("ロット番号", "ロット番号", "前方一致"),
    ("完成部番", "完成部番", "部分一致"),
    ("L図番", "L図番", "前方一致"),
]
MATCH_KINDS = ("前方一致", "部分一致")

SELECT_ALL_JS = JsCode("function selectAllRows(api) { api.api.selectAll(); }")
DESELECT_ALL_JS = JsCode("function deselectAllRows(api) { api.api.deselectAll(); }")

REPORT_MISSING_MESSAGE = (
    "ireporter管理flgが1かつ、帳票発行IDが未発行のデータがあります（カムリング、ダイヤルキャップは除く）。"
    "右上の「データ更新」を行ってください。"
)


# ---------------------------------------------------------------------------
# データ
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=600)
def load_tag_list(month_prefix, data_version, db_stamp):
    """一覧を読む。引数のどれかが変わると読み直す（同じなら覚えている一覧を返す）。

    data_version … この画面でデータ更新・印刷をしたら増やす
    db_stamp     … DB ファイルの更新日時（db_stamp() の値）
    ⚠ st.cache_data の覚えは**全員で共有**される。夜間処理（create_report.py・dbupdate.py）は
      別のプロセスで DB を書き換えるので、db_stamp を見ないと古い一覧を出し続ける
      （旧アプリで実際に起きた。2026-10-26、夜間処理で消えた25件が画面に残り、件数が24件ずれていた）。
    """
    return listing.load_tag_list(month_prefix)


def db_stamp():
    """DB のファイル（WAL の作業ファイルを含む）の更新日時。どこかで書き込まれると変わる。"""
    stamps = []
    for suffix in ("", "-wal"):
        path = config.GENPINHYO_DB.with_name(config.GENPINHYO_DB.name + suffix)
        stamps.append(path.stat().st_mtime_ns if path.exists() else 0)
    return tuple(stamps)


def refresh_data():
    """次の表示で一覧を読み直させる。"""
    st.session_state["data_version"] = st.session_state.get("data_version", 0) + 1
    load_tag_list.clear()


def run_update(report_month_prefix=None):
    """データ更新を行い、結果を画面に出すためにセッションに残す。

    report_month_prefix を渡すと、更新のあと、その月で i-Reporter の帳票が未作成のロットについて作る。
    """
    try:
        result = update.run_update()
        # 終わったことは表示しない（利用者の指示 2026-10-26）。部品の設定が要るときだけ知らせる。
        if result.new_parts:
            st.session_state["update_message"] = (
                "warning", f"新しい部品名が {result.new_parts}件ありました。部品の設定をしてください。")
    except (portal_api.PortalApiError, rbom.RbomApiError) as error:
        db.log_error(f"データ更新: {error}")
        st.session_state["update_message"] = (
            "error",
            f"業務ポータルまたは rBOM からデータを取得できなかったため、データ更新を中止しました"
            f"（表示は前回更新時のままです）。　{error}",
        )
        return
    except db.DatabaseCorruptedError as error:
        db.log_error(f"データ更新: {error}")
        st.session_state["update_message"] = ("error", f"{error}　DX推進室に連絡してください。")
        return
    finally:
        refresh_data()

    if report_month_prefix:
        targets = listing.needs_report(listing.load_tag_list(report_month_prefix))
        if not targets.empty:
            seconds = conmas.estimate_seconds(len(targets))
            with st.spinner(f"iReporter帳票作成中（{len(targets)}件・目安{seconds}秒）"):
                conmas.create_reports(targets)
            refresh_data()


# ---------------------------------------------------------------------------
# 画面の部品
# ---------------------------------------------------------------------------

@st.dialog("現品票が出ない場合", width="large")
def help_dialog():
    """「現品票が出ない場合」の問い合わせの流れ。文面はこの関数の中だけで直せばよい。"""
    st.markdown("""
現品票が出ないのは、生産管理システム **rBOM** で
**社内加工（内作）の作業指示が出ていない** ことが原因です。

下記の順番に、確認と対応をお願いします。

---
### STEP 1　まず「内作かどうか」を確認する
###### 👤 確認者：マシニング課・シリンダー課のみなさま
購買担当者に、**該当の組立番号の部番が内作（社内加工）かどうか**をご確認ください。

- **内作ではない** … 現品票は出ません。
- **内作である** … STEP 2 へ進んでください。

---
### STEP 2　rBOMの手配状況を確認する
###### 👤 確認者：購買課のみなさま
rBOMの **手配指示入力画面** を開き、該当の部番に
**なんらかの内作工程が構成されているか**をご確認ください。

確認結果によって、下の **ケースA / ケースB** に分かれます。

---
### ケースA　内作工程は構成されているが、手配の状態が「未」の場合
次の手順で社内指示を出してください。

1. 手配区分を **3：社内指示** にする
2. **選択 ⇒ 指示 ⇒ 社内指示** と進む
3. **社内指示登録画面**で「**更新**」を実行する
""")
    st.error("""
**重要：1製番ごとに行ってください。**
複数を選択して、まとめて社内指示を出さないようにしてください。
""")
    st.markdown("""
###### ＜補足＞ 品目工程マスタが「9：手配不要」になっている場合
該当の内作工程が **9：手配不要** になっていると、初期値では社内加工の手配が行われません。

- 初期値を**内作にしたい**場合 … マスタを **3：社内加工** に変更してください。
- 初期値は**外作**で登録し、後から内作に変更する運用の場合 … マスタの変更は不要です。

---
### ケースB　内作工程が構成されていない場合
さらに3つに分かれます。

##### B-1　品目工程マスタの内作工程を削除していた場合
1. **内作工程を登録**する
2. **手配指示入力画面**から **BOMを追加**する
3. **選択 ⇒ 指示 ⇒ 社内指示** と進み、**社内指示登録画面**で「**更新**」を実行する

##### B-2　工程展開後に、品目工程マスタに内作工程を登録した場合
マスタの展開が、部品表の構成に間に合わなかった状態です。
**製番ごとに**、次の2つの作業が必要になります。

1. **手配指示入力画面**から **BOMを追加**する
2. **選択 ⇒ 指示 ⇒ 社内指示** と進み、**社内指示登録画面**で「**更新**」を実行する

##### B-3　B-1・B-2 のどちらにも当てはまらない場合
（なんらかの内作工程が品目工程マスタに登録されているのに、部品表に構成されていない状態）
""")
    st.warning("""
システム的な不具合の可能性があります。
**DX推進室**までご相談ください。
""")
    st.markdown("---")
    st.markdown("### 対応が完了したあとは")
    st.info("""
対応完了後、**1時間～1時間半**を目途に、rBOMからデータが連携されます。
その後、画面右上の「**データ更新**」ボタンを押下いただくと、現品票に表示されます。
""")
    if st.button("閉じる", use_container_width=True):
        st.rerun()


def choose_month():
    """生産計画の年・月・次を選ぶ。既定は1か月ちょっと先（来月分を発行することが多いため）。"""
    default = config.now() + timedelta(days=32)
    col_title, col_year, col_month, col_ji, _, col_update = st.columns([3, 3, 3, 3, 1, 5])
    with col_title:
        st.markdown("### 現品票発行")
    with col_year:
        year = st.selectbox("生産計画年", [default.year - 1, default.year, default.year + 1], index=1)
    with col_month:
        month = st.selectbox("生産計画月", [f"{m:02d}" for m in range(1, 13)], index=default.month - 1)
    with col_ji:
        ji = st.selectbox("生産計画次", ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "_"], index=0)
    return f"{year}{month}", ji, col_update


def update_button(column, month_prefix):
    """データ更新ボタン。押したら処理中は押せないようにする（連打で二重に走らないように）。"""
    with column:
        updating = st.session_state.get("db_updating", False)
        if st.button("データ更新", disabled=updating):
            st.session_state["db_updating"] = True
            st.rerun()
        if updating:
            try:
                with st.spinner("データ更新中…"):
                    run_update(report_month_prefix=month_prefix)
            finally:
                st.session_state["db_updating"] = False
            st.rerun()
        if "update_message" in st.session_state:
            kind, message = st.session_state.pop("update_message")
            (st.error if kind == "error" else st.warning)(message)


def filter_rows(df, ji):
    """抽出条件で絞り込む（すべての条件を満たす行だけ残す）。"""
    mask = pd.Series(True, index=df.index)
    if ji:
        mask &= df["月次"].str[6:] == ji

    with st.expander("抽出条件"):
        columns = st.columns([2, 2.5, 3, 1, 1, 2.8])
        for column, (label, name) in zip(columns, SELECT_FILTERS):
            with column:
                choices = [""] + sorted(set(df[name].astype(str)))
                chosen = st.selectbox(label, choices, index=0)
                if chosen:
                    mask &= df[name].astype(str) == chosen

        columns = st.columns([3, 2, 3, 2, 3, 2, 1])
        for number, (label, name, default_kind) in enumerate(TEXT_FILTERS):
            with columns[number * 2]:
                text = st.text_input(label, "")
            with columns[number * 2 + 1]:
                st.write("")
                kind = st.radio(f"検索{number + 1}", MATCH_KINDS, horizontal=True,
                                index=MATCH_KINDS.index(default_kind), label_visibility="collapsed")
            if text:
                values = df[name].astype(str)
                mask &= values.str.startswith(text) if kind == "前方一致" else values.str.contains(text, regex=False)
        count_place = columns[6]

    filtered = df[mask]
    with count_place:
        st.write("")
        st.write("")
        st.write(f"{len(filtered)}件")
    return filtered


def show_grid(df):
    """一覧（AG Grid）を出し、チェックされた行を返す（列名は DB の名前に戻してある）。"""
    st.session_state.setdefault("select_all", False)
    col_select, _, col_help = st.columns([1, 4, 1.5])
    with col_select:
        if st.session_state["select_all"]:
            if st.button("全解除"):
                st.session_state["select_all"] = False
        elif st.button("全選択"):
            st.session_state["select_all"] = True
    with col_help:
        if st.button("❓ 現品票が出ない場合"):
            help_dialog()

    shown = df.rename(columns={"G": GAUGE_LABEL})
    extra = [name for name in db.EXTRA_DRAWING_COLUMNS if name in shown.columns]
    if extra and "C図番" in shown.columns:
        rest = [name for name in shown.columns if name not in extra]
        at = rest.index("C図番") + 1
        shown = shown[rest[:at] + extra + rest[at:]]
    builder = GridOptionsBuilder.from_dataframe(shown)
    builder.configure_selection(selection_mode="multiple", use_checkbox=True)
    builder.configure_default_column(filter=False)
    if "ﾒｯｷ" in shown.columns:
        builder.configure_column("ﾒｯｷ", hide=True)
    options = builder.build()
    options["localeText"] = ui.AGGRID_LOCALE
    options["onFirstDataRendered"] = SELECT_ALL_JS if st.session_state["select_all"] else DESELECT_ALL_JS

    grid = AgGrid(
        shown, height=470, gridOptions=options,
        update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
        enable_enterprise_modules=False,   # これが無いと有償版の試用になる
        allow_unsafe_jscode=True, reload_data=True,
    )
    selected = grid["selected_rows"]
    if selected is None or len(selected) == 0:
        return pd.DataFrame(columns=df.columns)
    return pd.DataFrame(selected).rename(columns={GAUGE_LABEL: "G"})


def print_buttons(selected):
    """印刷とCSVのボタン。"""
    col_print, col_shifted, _, col_csv = st.columns([10, 12, 10, 8])
    with col_print:
        if st.button("チェック済の印刷"):
            print_tags(selected, shifted=False)
    with col_shifted:
        if st.button("チェック済の印刷（ずれる場合）"):
            print_tags(selected, shifted=True)
    with col_csv:
        if not selected.empty:
            st.download_button(
                label="CSVダウンロード",
                data=selected.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"現品票リスト_{config.now():%Y%m%d%H%M%S}.csv",
                mime="text/csv",
            )


def print_tags(selected, shifted):
    """チェックした行の現品票を作る。i-Reporter の帳票が未作成の行があれば作らずに知らせる。"""
    if selected.empty:
        st.markdown("データ無し")
        return

    with st.spinner("現品票作成処理　実行中"):
        missing = listing.needs_report(selected)
        if not missing.empty:
            st.markdown(REPORT_MISSING_MESSAGE)
            st.dataframe(missing, hide_index=True)
            return

        rows = selected.sort_values(["月次", "組立番号", "ロット番号"]).to_dict("records")
        data, file_name = tag_excel.build_tag_book(rows, shifted=shifted)
        kind = db.PRINT_KIND_SHIFTED if shifted else db.PRINT_KIND_NORMAL
        db.record_prints(rows, kind)
    ui.download_excel(data, file_name)


# ---------------------------------------------------------------------------
# 本体
# ---------------------------------------------------------------------------

def main():
    ui.setup_page("現品票発行", icon="move.gif")

    # ⚠ 開いたときにはデータ更新をしない（利用者と決定 2026-10-26。開くのに5秒ほど余計にかかっていたため）。
    #   データ更新はタスクスケジューラの dbupdate.py（15分ごと）と、画面の「データ更新」ボタンで行う。
    #   一覧は DB が書き換わると読み直すので（load_tag_list の db_stamp）、夜間処理の結果もそのまま出る。
    #   帳票発行ID は一覧を作るたびに i-Reporter から読むので、データ更新が無くても最新になる。
    month_prefix, ji, update_column = choose_month()
    update_button(update_column, month_prefix)

    df = load_tag_list(month_prefix, st.session_state.get("data_version", 0), db_stamp())
    filtered = filter_rows(df, ji)
    selected = show_grid(filtered)
    print_buttons(selected)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # 画面が真っ白のまま止まらないよう、エラーを画面に出して記録する。
        traceback.print_exc()
        db.log_error(f"現品票発行: {error}")
        st.error(f"エラーが発生しました：{error}")
