###
# アッセンブリー課チェックシート
# Start 20250625 ダイヤルキャップとホルダーを開始
# ADD_20250626 ギアボックス追加
###

import streamlit as st
import config
import database
import utils
from tabs import checksheet_tab, master_tab, gearbox_tab, sinker_cap_tab

# --- 1. ページ設定と初期化 ---
# config.py からページタイトルとレイアウト設定を読み込み適用
st.set_page_config(page_title=config.PAGE_TITLE, layout="wide")

# config.py からカスタムCSSを読み込み適用
st.markdown(config.HIDE_ST_STYLE, unsafe_allow_html=True)

# database.py の関数を呼び出し、データベースとテーブルを初期化
database.init_db()

# utils.py の関数を呼び出し、アプリケーション全体で使うセッション変数を初期化
utils.initialize_session_state()


# --- 2. タブの定義と描画 ---
# Streamlitのタブ機能で、4つの主要な画面を定義
tab1, tab2, tab3, tab4, tab5 = st.tabs(["ダイヤルキャップ", "ホルダー", "ギアボックスGr", "シンカーキャップ", "マスター管理"])

# 「ダイヤルキャップ」タブのコンテンツを描画
with tab1:
    # tabs/checksheet_tab.py の render 関数を呼び出す
    # 引数で「ダイヤルキャップ用」であることを伝え、対応するテーブル名を渡す
    checksheet_tab.render(
        checksheet_type='ダイヤルキャップ',
        table_name=config.DIAL_CAP_CHECKSHEET_TABLE
    )

# 「ホルダー」タブのコンテンツを描画
with tab2:
    # 同じ render 関数を、「ホルダー用」の設定で呼び出すことでコードを再利用
    checksheet_tab.render(
        checksheet_type='ホルダー',
        table_name=config.HOLDER_CHECKSHEET_TABLE
    )

# 「ギアボックスGr」タブのコンテンツを描画
with tab3:
    # 新しく作成する tabs/gearbox_tab.py の render 関数を呼び出す
    # 引数で「ギアボックスGr用」であることを伝え、対応するテーブル名を渡す
    gearbox_tab.render(
        checksheet_type='ギアボックスGr',
        table_name=config.GEARBOX_CHECKSHEET_TABLE
    )

# 「シンカーキャップ」タブのコンテンツを描画
with tab4:
    sinker_cap_tab.render(
        checksheet_type='シンカーキャップ',
        table_name=config.SINKER_CAP_CHECKSHEET_TABLE
    )

# 「マスター管理」タブのコンテンツを描画
with tab5:
    # tabs/master_tab.py の render 関数を呼び出す
    master_tab.render()
