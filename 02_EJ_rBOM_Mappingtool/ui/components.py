"""
UI コンポーネント
"""
import streamlit as st
import pandas as pd

# render_sidebar関数は削除（Streamlit Pagesを使用するため）

def render_main_grid(data: pd.DataFrame):
    """Streamlit標準テーブルを表示"""
    
    # データのコピーを作成
    data = data.copy()
    
    # rBOM発注番号+行番号の連結列を作成
    if 'rbom_order_no' in data.columns and 'rbom_line_no' in data.columns:
        data['rbom_order_line'] = data.apply(
            lambda row: f"{str(row['rbom_order_no']).zfill(9)}+{str(row['rbom_line_no']).zfill(3)}" 
            if pd.notna(row['rbom_order_no']) and pd.notna(row['rbom_line_no']) 
            else None, axis=1
        )
    
    # 固定フラグ列を追加（デフォルトはFalse）
    if 'is_fixed' not in data.columns:
        data['is_fixed'] = False
    
    # カラムの順序を指定（EJ発注番号→EJ連番、rBOM発注番号→rBOM連番の順序）
    column_order = []
    display_columns = {}
    
    # EJグループ
    if 'ej_order_no' in data.columns:
        column_order.append('ej_order_no')
        display_columns['ej_order_no'] = 'EJ発注番号'
    if 'ej_m_sequence' in data.columns:
        column_order.append('ej_m_sequence')
        display_columns['ej_m_sequence'] = 'EJ連番'
    if 'ej_item_code' in data.columns:
        column_order.append('ej_item_code')
        display_columns['ej_item_code'] = 'EJ品目コード'
    if 'ej_item_name' in data.columns:
        column_order.append('ej_item_name')
        display_columns['ej_item_name'] = 'EJ品目名'
    if 'ej_quantity' in data.columns:
        column_order.append('ej_quantity')
        display_columns['ej_quantity'] = 'EJ数'
    if 'ej_status' in data.columns:
        column_order.append('ej_status')
        display_columns['ej_status'] = 'EJステータス'
    if 'ej_purch_odr_typ' in data.columns:
        column_order.append('ej_purch_odr_typ')
        display_columns['ej_purch_odr_typ'] = 'EJ発注種別'
    if 'ej_delivery_date' in data.columns:
        column_order.append('ej_delivery_date')
        display_columns['ej_delivery_date'] = 'EJ納期'
    
    # rBOMグループ
    if 'rbom_order_line' in data.columns:
        column_order.append('rbom_order_line')
        display_columns['rbom_order_line'] = 'rBOM発注番号+行番号'
    if 'rbom_m_sequence' in data.columns:
        column_order.append('rbom_m_sequence')
        display_columns['rbom_m_sequence'] = 'rBOM連番'
    if 'rbom_item_code' in data.columns:
        column_order.append('rbom_item_code')
        display_columns['rbom_item_code'] = 'rBOM品目コード'
    if 'rbom_item_name' in data.columns:
        column_order.append('rbom_item_name')
        display_columns['rbom_item_name'] = 'rBOM品目名'
    if 'rbom_quantity' in data.columns:
        column_order.append('rbom_quantity')
        display_columns['rbom_quantity'] = 'rBOM数'
    if 'rbom_delivery_date' in data.columns:
        column_order.append('rbom_delivery_date')
        display_columns['rbom_delivery_date'] = 'rBOM納期'
    
    # 管理項目
    if 'status' in data.columns:
        column_order.append('status')
        display_columns['status'] = '状態'
    if 'mapping_type' in data.columns:
        column_order.append('mapping_type')
        display_columns['mapping_type'] = '種別'
    if 'is_fixed' in data.columns:
        column_order.append('is_fixed')
        display_columns['is_fixed'] = 'マッピング確定'
    
    # カラムの順序を調整
    data_reordered = data[column_order]
    
    # データフレームのカラム名を変更
    display_data = data_reordered.rename(columns=display_columns)
    
    # 手動マッピングの場合は固定チェックボックスを非表示にするため、データを調整
    # 手動マッピングの場合は固定を無効化（編集不可）
    column_config = {}
    disabled_columns = []
    
    # マッピング確定列のみ編集可能に設定
    for col in display_data.columns:
        if col == 'マッピング確定':
            column_config[col] = st.column_config.CheckboxColumn(
                "マッピング確定",
                help="チェックすると次回自動マッピング時に固定されます",
                default=False,
            )
        else:
            disabled_columns.append(col)
    
    # 手動マッピングの行ではマッピング確定チェックボックスを無効化
    if '種別' in display_data.columns and 'マッピング確定' in display_data.columns:
        # 手動マッピングの行のインデックスを取得
        manual_indices = display_data[display_data['種別'] == '手動'].index.tolist()
        
        # session_stateにdisabled行情報を保存
        if 'disabled_fixed_rows' not in st.session_state:
            st.session_state.disabled_fixed_rows = []
        st.session_state.disabled_fixed_rows = manual_indices
    
    # Streamlit data_editor（編集可能なデータグリッド）- パフォーマンス最適化
    edited_data = st.data_editor(
        display_data,
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config=column_config,
        disabled=disabled_columns,
        key="mapping_data_editor",
        num_rows="fixed",
        # パフォーマンス改善のための設定
        width=None,  # 自動幅調整を無効化
    )
    
    # データ統計情報とCSV出力
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col1:
        total_count = len(data)
        st.metric("総件数", total_count)
    
    with col2:
        if 'mapping_type' in data.columns:
            auto_count = len(data[data['mapping_type'] == '自動'])
            st.metric("自動", auto_count)
    
    with col3:
        if 'mapping_type' in data.columns:
            manual_count = len(data[data['mapping_type'] == '手動'])
            st.metric("手動", manual_count)
    
    with col4:
        # マッチングしたデータ（EJとrBOM両方に値があるデータ）
        if len(data) > 0:
            matched_count = len(data.dropna(subset=['ej_order_no', 'rbom_order_no']))
            st.metric("マッチング済", matched_count)
    
    with col5:
        st.write("")  # スペース調整
        # CSV出力
        if st.button("CSV出力"):
            from datetime import datetime
            import io
            
            # BOM付きShift_JISでCSVを生成（Excelでの文字化け防止）
            output = io.StringIO()
            data.to_csv(output, index=False, encoding='utf-8')
            csv_string = output.getvalue()
            
            # UTF-8 BOM付きでエンコード
            csv_bytes = '\ufeff' + csv_string
            csv_data = csv_bytes.encode('utf-8')
            
            st.download_button(
                label="CSVダウンロード",
                data=csv_data,
                file_name=f"mapping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    return edited_data