"""現品票手入力発行。生産管理システムで管理していない部番（主に CMR）の現品票を1枚作る。

ロット番号は KARI＋6桁の乱数。i-Reporter の帳票も作る（部品の設定で QR が i-Reporter 用の場合）。
"""

import random
import time
import traceback
from datetime import timedelta

import pandas as pd
import streamlit as st

from genpin import config, conmas, db, irepo, listing, portal_api, tag_excel, ui

DEFAULT_CUSTOMER = "J0003"
# 手入力の現品票の月次は「次」を決めないので '_' 固定。
MANUAL_JI = "_"
# i-Reporter の帳票ができて、DB から読めるようになるまで待つ秒数。
WAIT_AFTER_REPORT_SEC = 30


@st.cache_data(ttl=600, show_spinner=False)
def process_strings(hmcd):
    """工程文字列（VER ごと）。入力のたびに画面が描き直されるので、10分間は覚えておく。"""
    return portal_api.fetch_process_strings(hmcd)


@st.cache_data(ttl=600, show_spinner=False)
def drawing_of(hmcd):
    """図番（1部番ぶん）。"""
    return portal_api.fetch_drawings([hmcd])[0]


@st.cache_data(ttl=600, show_spinner=False)
def customers():
    return irepo.fetch_customers()


def show_process_and_drawing(hmcd, version):
    """入力した部番の工程と図番を表示し、(工程, 図番の辞書) を返す。"""
    try:
        rows = process_strings(hmcd)
        drawing = drawing_of(hmcd)
    except portal_api.PortalApiError as error:
        st.warning(f"業務ポータルから工程・図番を取得できませんでした。{error}")
        rows, drawing = [], {"matched_by": "none"}

    matched = [row for row in rows if row["version"] == version]
    process = matched[0]["process_str"] if len(matched) == 1 else ""
    st.write(f"工程情報：{process or '無し'}")

    if drawing["matched_by"] == "none":
        st.write("図番情報：無し")
        return process, {}

    st.write("図番情報：")
    table = {"完成部番": hmcd}
    for api_key, column in portal_api.DRAWING_COLUMNS.items():
        table[column] = drawing[api_key]
    st.dataframe(pd.DataFrame([table]), hide_index=True)
    return process, {key: drawing[key] for key in ("B1", "B2", "F1", "F2", "L", "R", "C")}


def create_report(values):
    """i-Reporter の帳票を作り、できた帳票の ID を返す（作らない部品なら 0）。"""
    rows = conmas.rows_for_single_report(values)
    if listing.needs_report(rows).empty:
        return 0
    with st.spinner("iReporter帳票作成対象のため、50秒ほどお待ちください"):
        conmas.create_reports(rows)
        time.sleep(WAIT_AFTER_REPORT_SEC)   # 待たないと、帳票が DB に載る前に読みにいってしまう
    reports = irepo.fetch_report_ids()
    found = reports[reports["ロット番号"] == values["ロット番号"]]["帳票発行ID"]
    return int(found.max()) if not found.empty else 0


def main():
    ui.setup_page("現品票手入力発行")
    parts = listing.read_table("buhin_irepo_mst").sort_values("部品名")

    st.markdown("### 現品票手入力発行")
    st.markdown(
        "この画面は生産管理システムで管理していない部番の現品票を発行するためのものです。主にCMRで使用します。  \n"
        "年月、CMR番号、部品名称、完成部番を入力のうえ、「手入力現品票を印刷」から印刷してください。  \n"
        "部品が「i-Reporter対象」の場合は、i-Reporterのチェックリストも作成されます。"
    )
    st.divider()

    default = config.now() + timedelta(days=32)
    col_year, col_month, _ = st.columns([1, 1, 4])
    with col_year:
        year = st.selectbox("年", [default.year - 1, default.year, default.year + 1], index=1)
    with col_month:
        month = st.selectbox("月", [f"{m:02d}" for m in range(1, 13)], index=default.month - 1)

    col_cmr, _ = st.columns([1, 3])
    with col_cmr:
        cmr_no = st.text_input("CMR番号（例：CMR-24003）", "") or "_"

    col_part, col_flag, _ = st.columns([1, 1, 3])
    with col_part:
        part_name = st.selectbox("部品名称", [""] + parts["部品名"].tolist())
    part = parts[parts["部品名"] == part_name]
    with col_flag:
        if not part.empty:
            st.write(" ")
            st.write(" ")
            target = part["ireporter管理flg"].iloc[0] == 1
            st.markdown("##### i-Reporter対象" if target else "##### i-Reporter対象外")

    col_hmcd, col_version, _ = st.columns([2.5, 2.5, 4.3])
    with col_hmcd:
        hmcd = st.text_input("完成部番 (例：565-602BA33)", "")
    with col_version:
        version = st.number_input("工程version（不明な場合は 1）", min_value=1, max_value=99, value=1, step=1)

    process, drawings = ("", {})
    if hmcd:
        process, drawings = show_process_and_drawing(hmcd, version)

    col_code, col_name, _ = st.columns([2, 4, 1])
    with col_code:
        customer_code = st.text_input("客先コード（特に指定のない場合はJ0003）", value=DEFAULT_CUSTOMER)
    matched = customers()[customers()["客先コード"] == customer_code]
    customer_name = matched["客先名"].iloc[0] if not matched.empty else ""
    with col_name:
        if customer_name:
            st.write(" ")
            st.write(" ")
            st.markdown(f"##### 客先名： {customer_name}")

    st.divider()
    if not st.button("手入力現品票を印刷"):
        return
    if part.empty:
        st.warning("部品名称を選んでください。")
        return

    with st.spinner("現品票作成処理　実行中"):
        lot_no = f"KARI{random.randint(100000, 999999)}"
        getsuji = f"{year}{month}{MANUAL_JI}"
        values = {
            "ロット番号": lot_no, "部品名": part_name, "完成部番": hmcd, "月次": getsuji,
            "組立番号": cmr_no, "機種": "", "吋": "", "G": "", "客先コード": customer_code,
            # ﾒｯｷは手入力では指定しない（0＝なし。昔の形の QR には '0' が入る）。
            "客先名": customer_name, "ﾒｯｷ": 0, "工程VERSION": version,
            # ⚠ 手入力は部品の設定に関わらず i-Reporter 管理として扱う（昔からの動き）。
            "ireporter管理flg": 1,
            "QRコードレイアウト区分": int(part["QRコードレイアウト区分"].iloc[0]),
            "縦横区分": int(part["縦横区分"].iloc[0]),
            "帳票発行ID": 0,
        }
        values["帳票発行ID"] = create_report(values)

        if values["QRコードレイアウト区分"] == tag_excel.QR_LAYOUT_LEGACY:
            qr = tag_excel.qr_text(values)
        else:
            qr = tag_excel.ireporter_qr_text(values["帳票発行ID"])
        entry = tag_excel.TagEntry(
            lot_no=lot_no, getsuji=f"{month}月{MANUAL_JI}次", hmcd=hmcd, qty=1,
            assy_no=cmr_no, process=process, drawings=drawings,
            qr_png=tag_excel.make_qr_png(qr),
        )
        data, file_name = tag_excel.build_single_tag(entry)
        db.record_prints([values], db.PRINT_KIND_MANUAL)
    ui.download_excel(data, file_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        traceback.print_exc()
        db.log_error(f"現品票手入力発行: {error}")
        st.error(f"エラーが発生しました：{error}")
