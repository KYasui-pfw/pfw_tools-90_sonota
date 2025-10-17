"""
手動マッピングページ
EJ発注番号、rBOM発注番号、rBOM行番号を手動で登録・管理
"""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
import logging

# ロガー設定
logger = logging.getLogger(__name__)

# ページ設定
st.set_page_config(
    page_title="手動マッピング",
    page_icon="✏️",
    layout="wide"
)

# CSS設定
st.markdown("""
<style>
    div[data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    div[data-testid="stDecoration"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    #MainMenu {
        visibility: hidden;
        height: 0%;
    }
    header {
        visibility: hidden;
        height: 0%;
    }
    footer {
        visibility: hidden;
        height: 0%;
    }
    .appview-container .main .block-container {
        padding-top: 1rem;
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 1rem;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """メイン処理"""
    st.title("手動マッピング")

    # データベースマネージャーの初期化
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.db_manager.initialize_database()

    # 入力セクション
    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])

    with col1:
        ej_order_no = st.text_input(
            "EJ発注番号",
            key="ej_order_no_input",
            placeholder="例: 2025000001"
        )

    with col2:
        rbom_order_no = st.text_input(
            "rBOM発注番号",
            key="rbom_order_no_input",
            placeholder="例: 123456789"
        )

    with col3:
        rbom_line_no = st.number_input(
            "rBOM行番号",
            min_value=1,
            max_value=999,
            value=1,
            step=1,
            key="rbom_line_no_input"
        )

    with col4:
        st.write("")  # スペース調整
        register_disabled = not (ej_order_no and rbom_order_no and rbom_line_no is not None)

        if st.button("登録", type="primary", disabled=register_disabled, use_container_width=True):
            try:
                st.session_state.db_manager.save_manual_mapping(
                    ej_order_no.strip(),
                    rbom_order_no.strip(),
                    int(rbom_line_no)
                )
                st.success(f"登録完了: EJ={ej_order_no} ↔ rBOM={rbom_order_no}+{rbom_line_no}")
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "UNIQUE constraint failed" in error_msg:
                    st.error("このマッピングは既に登録されています")
                else:
                    st.error(f"登録エラー: {error_msg}")
                logger.error(f"手動マッピング登録エラー: {error_msg}", exc_info=True)

    # 登録済みデータ表示
    try:
        manual_mappings_df = st.session_state.db_manager.get_manual_mappings()

        if manual_mappings_df.empty:
            st.info("登録されている手動マッピングはありません")
        else:
            # データフレーム表示エリア（左3分の2）
            col_data, col_space = st.columns([2, 1])

            with col_data:
                # 表示用にカラム名を変更（IDと登録日時は除外）
                display_df = manual_mappings_df[['ej_order_no', 'rbom_order_no', 'rbom_line_no']].copy()
                display_df = display_df.rename(columns={
                    'ej_order_no': 'EJ発注番号',
                    'rbom_order_no': 'rBOM発注番号',
                    'rbom_line_no': 'rBOM行番号'
                })

                # rBOM行番号を3桁ゼロ埋め
                display_df['rBOM行番号'] = display_df['rBOM行番号'].apply(lambda x: str(int(x)).zfill(3) if pd.notna(x) else '')

                # データフレーム表示（左詰め）
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=270,
                    column_config={
                        'EJ発注番号': st.column_config.TextColumn(width="medium"),
                        'rBOM発注番号': st.column_config.TextColumn(width="medium"),
                        'rBOM行番号': st.column_config.TextColumn(width="small")
                    }
                )

            # 水平線
            st.markdown("---")

            # 削除セクション
            col_del1, col_del2, col_del3 = st.columns([3, 1, 4])

            with col_del1:
                # 削除対象のIDを選択
                delete_id = st.selectbox(
                    "削除するマッピングを選択",
                    options=manual_mappings_df['id'].tolist(),
                    format_func=lambda x: f"EJ={manual_mappings_df[manual_mappings_df['id']==x]['ej_order_no'].values[0]} ↔ rBOM={manual_mappings_df[manual_mappings_df['id']==x]['rbom_order_no'].values[0]}+{str(int(manual_mappings_df[manual_mappings_df['id']==x]['rbom_line_no'].values[0])).zfill(3)}",
                    key="delete_id_select"
                )

            with col_del2:
                st.write("")  # スペース調整
                st.markdown("""
                <style>
                div[data-testid="stButton"] button[kind="secondary"] {
                    background-color: #ff4b4b;
                    color: white;
                }
                div[data-testid="stButton"] button[kind="secondary"]:hover {
                    background-color: #ff0000;
                    color: white;
                }
                </style>
                """, unsafe_allow_html=True)

                if st.button("削除", type="secondary", use_container_width=True):
                    try:
                        st.session_state.db_manager.delete_manual_mapping(delete_id)
                        st.success(f"ID={delete_id} を削除しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除エラー: {str(e)}")
                        logger.error(f"手動マッピング削除エラー: {str(e)}", exc_info=True)

    except Exception as e:
        st.error(f"データ取得エラー: {str(e)}")
        logger.error(f"手動マッピング取得エラー: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
