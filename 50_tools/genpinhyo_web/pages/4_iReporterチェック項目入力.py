"""i-Reporter チェック登録への入口。

チェック項目の登録は check_input（NiceGUI・port 8506。Check_input_start.bat で起動）で行う。
このページはそこへのリンクだけを出す（現場はこのサイドバーから開いているため残している）。
⚠ check_input を別のサーバー・ポートに移したら CHECK_INPUT_URL を直す。
"""

import streamlit as st

from genpin import ui

CHECK_INPUT_URL = "http://esrv10:8506/"

ui.setup_page("i-Reporter_チェック登録")
st.markdown("# i-Reporter_チェック登録")
st.write("")
st.markdown(f"### 新しい i-Reporterチェック登録画面は[こちら]({CHECK_INPUT_URL})です")
