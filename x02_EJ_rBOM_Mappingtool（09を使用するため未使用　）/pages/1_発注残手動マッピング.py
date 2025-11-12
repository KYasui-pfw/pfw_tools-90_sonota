"""
発注残手動マッピングページ
"""
import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from mapping.mapper import MappingEngine
from data_sources.ej_connector import EJConnector
from data_sources.rbom_connector import RBOMConnector

# ページ設定
st.set_page_config(
    page_title="発注残手動マッピング",
    page_icon="✋",
    layout="wide"
)

# CSS設定（サイドバーは表示）
st.markdown("""
<style>
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    #MainMenu {
        display: none !important;
        height: 0px !important;
    }
    .appview-container .main .block-container{
        padding-top: 1rem;
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 1rem;
    }
    header[data-testid="stHeader"] {
        z-index: -1;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 1rem !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }
    div[data-testid="stButton"] > button {
        height: 38.4px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """メイン処理"""
    
    st.header("手動マッピング機能")
    st.info("この機能は現在開発中です。数が一致しないデータの手動マッピングを行う予定です。")
    
    # データベース初期化
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.db_manager.initialize_database()
    
    # タブ作成
    tab1, tab2, tab3 = st.tabs(["未マッピングデータ", "潜在的マッチング", "手動マッピング設定"])
    
    with tab1:
        render_unmapped_data()
    
    with tab2:
        render_potential_matches()
    
    with tab3:
        render_manual_mapping_settings()

def render_unmapped_data():
    """未マッピングデータを表示"""
    st.subheader("未マッピングデータ")
    
    if 'db_manager' in st.session_state:
        mapping_data = st.session_state.db_manager.get_mapping_results()
        
        if not mapping_data.empty:
            # EJのみのデータ
            ej_only = mapping_data[mapping_data['mapping_type'] == 'EJ_ONLY']
            if not ej_only.empty:
                st.write("### EJ側のみのデータ")
                st.dataframe(
                    ej_only[['ej_order_no', 'ej_item_code', 'ej_item_name', 'ej_quantity', 'ej_delivery_date']],
                    use_container_width=True
                )
            
            # rBOMのみのデータ
            rbom_only = mapping_data[mapping_data['mapping_type'] == 'RBOM_ONLY']
            if not rbom_only.empty:
                st.write("### rBOM側のみのデータ")
                st.dataframe(
                    rbom_only[['rbom_order_no', 'rbom_item_code', 'rbom_item_name', 'rbom_quantity', 'rbom_delivery_date']],
                    use_container_width=True
                )
        else:
            st.info("マッピングデータがありません。メインページで「自動マッピング」を実行してください。")
    else:
        st.info("データベースが初期化されていません。")

def render_potential_matches():
    """潜在的マッチングを表示（品目コードは一致するが数量が異なる）"""
    st.subheader("潜在的マッチング")
    st.write("品目コードは一致するが、数量が異なるデータの候補を表示します。")
    
    if st.button("潜在的マッチングを検索"):
        with st.spinner("潜在的マッチングを検索中..."):
            try:
                # 最新のEJ・rBOMデータを取得して潜在的マッチングを検索
                # （実際の実装では条件を指定する必要がある）
                st.info("実装予定: 品目コードが一致するが数量が異なるデータの一覧を表示")
                
                # 仮のサンプルデータ
                sample_data = pd.DataFrame([
                    {
                        'ej_item_code': 'ITEM001',
                        'ej_quantity': 10.0,
                        'ej_order_no': 'EJ001',
                        'rbom_quantity': 12.0,
                        'rbom_order_no': 'RBOM001',
                        'quantity_diff': 2.0
                    },
                    {
                        'ej_item_code': 'ITEM002',
                        'ej_quantity': 5.0,
                        'ej_order_no': 'EJ002',
                        'rbom_quantity': 4.0,
                        'rbom_order_no': 'RBOM002',
                        'quantity_diff': 1.0
                    }
                ])
                
                if not sample_data.empty:
                    st.write("### 潜在的マッチング候補")
                    st.dataframe(sample_data, use_container_width=True)
                    st.caption("※ 数量差の小さい順に表示されています")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

def render_manual_mapping_settings():
    """手動マッピング設定"""
    st.subheader("手動マッピング設定")
    st.write("手動でEJとrBOMのデータを紐付ける機能です。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### EJ側データ選択")
        ej_order_no = st.text_input("EJ発注番号")
        ej_item_code = st.text_input("EJ品目コード")
        ej_quantity = st.number_input("EJ数量", min_value=0.0, format="%.2f")
    
    with col2:
        st.write("#### rBOM側データ選択")
        rbom_order_no = st.text_input("rBOM発注番号")
        rbom_item_code = st.text_input("rBOM品目コード")
        rbom_quantity = st.number_input("rBOM数量", min_value=0.0, format="%.2f")
    
    st.write("#### マッピング操作")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        if st.button("手動マッピング実行", type="primary"):
            if ej_order_no and rbom_order_no:
                st.success("手動マッピングを実行しました（実装予定）")
                st.info(f"EJ: {ej_order_no} ⟷ rBOM: {rbom_order_no}")
            else:
                st.warning("EJ発注番号とrBOM発注番号を入力してください")
    
    with col4:
        if st.button("マッピング解除"):
            st.info("マッピング解除機能（実装予定）")
    
    with col5:
        if st.button("設定リセット"):
            st.rerun()

if __name__ == "__main__":
    main()