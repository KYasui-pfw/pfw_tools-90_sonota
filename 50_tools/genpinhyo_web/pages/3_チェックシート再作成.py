"""チェックシート再作成。途中で不合格が出た場合など、同じロット番号で2つ目のチェックシートを作る。

i-Reporter の帳票を作り直し（部品の設定が i-Reporter 管理の場合）、【再発行】と入った現品票を1枚作る。
現品票が汚れた・破れたなどで刷り直すだけなら、通常の「現品票発行」画面から印刷する。
"""

import time
import traceback

import pandas as pd
import streamlit as st

from genpin import conmas, db, irepo, listing, tag_excel, ui

REISSUE_HEADER = "【再発行】"
# i-Reporter の帳票ができて、DB から読めるようになるまで待つ秒数。
WAIT_AFTER_REPORT_SEC = 10


def find_lot(lot_no):
    """ロット番号の行（部品の設定・最新の帳票発行ID付き）を返す。無ければ空。"""
    conn = db.connect()
    try:
        rows = pd.read_sql("SELECT * FROM genpinhyo WHERE ロット番号 = ?", conn, params=[lot_no])
    finally:
        conn.close()
    if rows.empty:
        return rows

    rows = rows.merge(listing.read_table("buhin_irepo_mst"), on="部品名", how="left")
    rows = listing.attach_report_ids(rows)
    rows["工程VERSION"] = listing.to_version(rows["工程VERSION"])
    return rows.fillna("")


def recreate_report(row):
    """i-Reporter の帳票を作り直し、新しい帳票の ID を返す（i-Reporter 管理でない部品なら 0）。"""
    if row.get("ireporter管理flg") != 1:
        return 0
    if row.get("QRコードレイアウト区分") == tag_excel.QR_LAYOUT_IREPORTER:
        with st.spinner("iReporter帳票作成対象のため、20秒ほどお待ちください"):
            conmas.create_reports(pd.DataFrame([row]))
            time.sleep(WAIT_AFTER_REPORT_SEC)   # 待たないと、帳票が DB に載る前に読みにいってしまう
    reports = irepo.fetch_report_ids()
    found = reports[reports["ロット番号"] == row["ロット番号"]]["帳票発行ID"]
    return int(found.max()) if not found.empty else 0


def main():
    ui.setup_page("現品票再発行")

    st.markdown("### チェックシート再作成")
    st.markdown(
        "この画面は途中で不合格が出た場合等、**同じロット番号で２つ目のチェックシートを発行する場合**に使用します。  \n"
        "現品票が汚れたり破れた等で現品票を再発行したい場合は、通常の「現品票発行」画面より印刷してください。"
    )
    st.divider()

    col_lot, _ = st.columns([2, 5])
    with col_lot:
        lot_no = st.text_input("ロット番号入力", "").strip()
    rows = find_lot(lot_no) if lot_no else pd.DataFrame()

    if st.button("検索"):
        st.divider()
        st.write("出力対象データ")
        if rows.empty:
            st.write("出力対象データ無し　※ロット番号が正しくありません")
        else:
            st.dataframe(rows.rename(columns={"G": "ｹﾞｰｼﾞ"}))
    st.divider()

    if rows.empty or not st.button("手入力現品票を印刷"):
        return

    with st.spinner("現品票作成処理　実行中"):
        row = rows.iloc[0].to_dict()
        row["帳票発行ID"] = recreate_report(row)

        entry = tag_excel.TagEntry(
            lot_no=row["ロット番号"],
            getsuji=row["月次"],        # ⚠ 再発行は月次をそのまま印字する（昔からの見た目）
            hmcd=row["完成部番"],
            qty=row["必要数"],
            assy_no=row["組立番号"],
            model=row["機種"],
            inch=row["吋"],
            gauge=row["G"],
            process=row["工程"],
            header=REISSUE_HEADER,
            notice=tag_excel.PLATING_NOTICE if tag_excel.is_plating(row["ﾒｯｷ"]) else "",
            drawings=tag_excel.drawings_of(row),
            qr_png=tag_excel.make_qr_png(tag_excel.qr_text(row)),
        )
        data, file_name = tag_excel.build_single_tag(entry)
        db.record_prints([row], db.PRINT_KIND_REISSUE)
    ui.download_excel(data, file_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        traceback.print_exc()
        db.log_error(f"チェックシート再作成: {error}")
        st.error(f"エラーが発生しました：{error}")
