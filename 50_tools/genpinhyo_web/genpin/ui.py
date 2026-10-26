"""Streamlit の画面で共通に使う見た目と部品。"""

import streamlit as st

# Streamlit の標準のメニュー・ヘッダー・フッターを隠し、余白を詰める。
_PAGE_STYLE = """
<style>
div[data-testid="stToolbar"], div[data-testid="stDecoration"], #MainMenu, header, footer {
    visibility: hidden;
    height: 0%;
}
header[data-testid="stHeader"] { z-index: -1; }
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 3rem;
    padding-right: 3rem;
}
</style>
"""

# AG Grid の表示文言を日本語にする。
AGGRID_LOCALE = {
    "pinColumn": "ピン止め",
    "noPin": "ピン止め解除",
    "pinLeft": "左ピン止め",
    "pinRight": "右ピン止め",
    "autosizeThiscolumn": "列幅自動調整",
    "autosizeAllColumns": "全ての列幅自動調整",
    "resetColumns": "設定をリセット",
    "contains": "含む",
    "notContains": "含まない",
    "equals": "等しい",
    "notEqual": "等しくない",
    "startsWith": "で始まる",
    "endsWith": "で終わる",
    "lessThan": "より小さい",
    "lessThanOrEqual": "以下",
    "greaterThan": "より大きい",
    "greaterThanOrEqual": "以上",
    "inRange": "範囲内",
    "blank": "空欄",
    "notBlank": "空欄でない",
    "noRowsToShow": "表示する行がありません",
    "copy": "コピー",
    "copyWithHeaders": "ヘッダー付コピー",
    "export": "ファイル出力",
    "csvExport": "csvファイル出力",
    "selectAll": "(全て選択)",
    "blanks": "(空欄)",
}

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def setup_page(title, icon=None):
    """ページの設定と共通の見た目。各画面の先頭で1回だけ呼ぶ。"""
    st.set_page_config(page_title=title, layout="wide", page_icon=icon)
    st.markdown(_PAGE_STYLE, unsafe_allow_html=True)


def download_excel(data, file_name):
    """作った Excel のダウンロードボタンを出す。"""
    st.markdown("処理終了：処理結果のエクセルを以下からダウンロードしてください")
    st.download_button(label="処理結果ダウンロード", data=data, file_name=file_name, mime=XLSX_MIME)
