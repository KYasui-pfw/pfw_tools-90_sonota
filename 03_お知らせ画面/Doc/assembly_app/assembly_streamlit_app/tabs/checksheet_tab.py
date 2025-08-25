import streamlit as st
import pandas as pd
import datetime
import time

import database
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

def render(checksheet_type: str, table_name: str):
    """
    ダイヤルキャップまたはホルダーのチェックシートタブUIを描画する共通関数。

    Args:
        checksheet_type (str): 'ダイヤルキャップ' または 'ホルダー'。UIのタイトルやマスターデータの取得に使用。
        table_name (str): データベース操作の対象となるテーブル名。
    """
    # st.session_state のキーを動的に生成するためのプレフィックス
    prefix = 'dial_cap_' if checksheet_type == 'ダイヤルキャップ' else 'holder_'

    # --- ヘッダーとセレクター ---
    header_cols = st.columns(2)
    with header_cols[0]:
        st.subheader(f"{checksheet_type}チェックシート")
    with header_cols[1]:
        now = datetime.datetime.now()
        year_options, month_options = [now.year - 1, now.year, now.year + 1], list(range(1, 13))
        suffix_options = [""] + list(range(1, 9))
        
        selector_cols = st.columns(3)
        selected_year = selector_cols[0].selectbox(
            "生産計画年", year_options, index=year_options.index(now.year), key=f"{prefix}main_year")
        selected_month = selector_cols[1].selectbox(
            "生産計画月", month_options, index=now.month - 1, format_func=lambda x: f"{x:02d}", key=f"{prefix}main_month")
        selected_suffix = selector_cols[2].selectbox(
            "生産計画次", suffix_options, index=0, key=f"{prefix}main_suffix")

    # --- データ取得・更新 ---
    # 選択年月が変わった場合のみ外部DBからデータを取得・更新
    if st.session_state[f"{prefix}last_fetched_year_month"] != (selected_year, selected_month):
        with st.spinner(f"{selected_year}年{selected_month}月の{checksheet_type}生産機情報を取得・更新中..."):
            product_type = 'dial_cap' if checksheet_type == 'ダイヤルキャップ' else 'holder'
            fetched_data = database.fetch_production_machine_info(selected_year, selected_month, product_type)
            if not fetched_data.empty:
                database.upsert_production_machine_data(fetched_data, selected_year, selected_month, table_name)
        
        st.session_state[f"{prefix}last_fetched_year_month"] = (selected_year, selected_month)
        # 関連するセッションデータをクリアして再描画
        for key in list(st.session_state.keys()):
            if key.startswith(f"original_df_{prefix}") or key.startswith(f"current_data_{prefix}"):
                del st.session_state[key]
        st.rerun()

    # --- データ準備 for AgGrid ---
    session_key_original_df = f"original_df_{prefix}{selected_year}_{selected_month}"
    session_key_current_data = f"current_data_{prefix}{selected_year}_{selected_month}"
    
    if session_key_current_data not in st.session_state:
        fresh_df = database.get_checksheet_data(selected_year, selected_month, table_name).reset_index(drop=True)
        fresh_df['delete_flag'] = False
        st.session_state[session_key_original_df] = fresh_df.copy()
        st.session_state[session_key_current_data] = fresh_df.copy()

    full_data = st.session_state[session_key_current_data]
    df_filtered = full_data[full_data['production_plan_month_full'].astype(str).str.endswith(
        str(selected_suffix))] if selected_suffix != "" and not full_data.empty else full_data
    df_display = df_filtered.drop(columns=['production_year', 'production_month', 'task3_checker',
                                  'last_modified_timestamp', 'production_plan_month_full'], errors='ignore')

    # --- AgGridの定義 ---
    # JSコードは共通
    date_value_parser = JsCode(""" function(params) { if (params.newValue instanceof Date && !isNaN(params.newValue)) { const d = params.newValue; return `${d.getFullYear()}-${('0' + (d.getMonth() + 1)).slice(-2)}-${('0' + d.getDate()).slice(-2)}`; } return params.newValue; } """)
    date_display_formatter = JsCode(""" function(params) { if (!params.value) { return ''; } let dateObj; if (params.value instanceof Date && !isNaN(params.value)) { dateObj = params.value; } else if (typeof params.value === 'string') { dateObj = new Date(params.value); if (isNaN(dateObj.getTime())) { return params.value.split(' ')[0]; } } else { return ''; } return `${('0' + (dateObj.getMonth() + 1)).slice(-2)}/${('0' + dateObj.getDate()).slice(-2)}`; } """)
    getRowStyle_js = JsCode(""" function(params) { if (params.data.completion_status === '不要') { return { 'background-color': '#A9A9A9' }; } return null; } """)
    base_date_column = {'headerName': '実施日', 'width': 90, 'editable': True, 'cellEditor': 'agDateCellEditor', 'valueParser': date_value_parser, 'valueFormatter': date_display_formatter, 'headerClass': 'ag-header-cell-center-aligned'}

    # マスターデータをDBから取得
    worker_names = database.get_workers_for_checksheet(checksheet_type)['worker_name'].tolist()
    instrument_names = database.get_instruments_for_checksheet(checksheet_type)['instrument_no'].tolist()
    
    # チェックシートタイプによってヘッダー名を変更
    task3_header = 'カムの可動域、針通し、奥行確認' if checksheet_type == 'ホルダー' else 'カムの可動域、平面度確認'

    is_grid_editable = not st.session_state.get(f"{prefix}update_in_progress", False)

    column_defs = [
        {'field': 'machine_no', 'headerName': "機番", 'width': 90, 'pinned': 'left', 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'model_name', 'headerName': "機種名", 'width': 130, 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'size_inch', 'headerName': "吋", 'width': 50, 'headerClass': 'ag-header-cell-center-aligned', 'editable': is_grid_editable},
        {'field': 'gauge', 'headerName': "G", 'width': 50, 'headerClass': 'ag-header-cell-center-aligned', 'editable': is_grid_editable},
        {'headerName': 'ノズル打ち込み、ムシねじ', 'headerClass': 'ag-header-cell-center-aligned', 'children': [{'headerName': 'ピース面取り量、取付ボルト確認', 'headerClass': 'ag-header-cell-center-aligned', 'children': [{**base_date_column, 'field': 'task1_date', 'editable': is_grid_editable}, {'field': 'task1_worker', 'headerName': '作業者', 'width': 130, 'editable': is_grid_editable, 'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {'values': [""] + worker_names}, 'headerClass': 'ag-header-cell-center-aligned'}]}]},
        {'headerName': 'カムの品番、隙間、キズ', 'headerClass': 'ag-header-cell-center-aligned', 'children': [{'headerName': '指定柄、１セグメント取付確認', 'headerClass': 'ag-header-cell-center-aligned', 'children': [{**base_date_column, 'field': 'task2_date', 'editable': is_grid_editable}, {'field': 'task2_worker', 'headerName': '作業者', 'width': 120, 'editable': is_grid_editable, 'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {'values': [""] + worker_names}, 'headerClass': 'ag-header-cell-center-aligned'}]}]},
        {'headerName': task3_header, 'headerClass': 'ag-header-cell-center-aligned', 'children': [{'headerName': '高さ調整、文字盤合わせ', 'headerClass': 'ag-header-cell-center-aligned', 'children': [{**base_date_column, 'field': 'task3_date', 'editable': is_grid_editable}, {'field': 'task3_worker', 'headerName': '作業確認者', 'width': 135, 'editable': is_grid_editable, 'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {'values': [""] + worker_names}, 'headerClass': 'ag-header-cell-center-aligned'}]}]},
        {'field': 'instrument_no', 'headerName': '計測器No', 'width': 90, 'editable': is_grid_editable, 'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {'values': [""] + instrument_names}, 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'completion_status', 'headerName': '完成品', 'width': 70, 'editable': is_grid_editable, 'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {'values': ["", "合", "否", "不要"]}, 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'remarks', 'headerName': '備考', 'width': 150, 'editable': is_grid_editable, 'wrapText': True, 'autoHeight': True, 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'delete_flag', 'headerName': '削除', 'width': 60, 'editable': is_grid_editable, 'cellRenderer': 'agCheckboxCellRenderer', 'headerClass': 'ag-header-cell-center-aligned'}
    ]
    grid_options = {"columnDefs": column_defs, "defaultColDef": {"wrapHeaderText": True, "autoHeaderHeight": True, "suppressMovable": True, "resizable": False}, "suppressRowClickSelection": True, "getRowStyle": getRowStyle_js}
    custom_css = {
        ".ag-header-cell-center-aligned .ag-header-cell-label": {
            "justify-content": "center"
        },
        ".ag-header-group-cell-center-aligned .ag-header-group-cell-label": {
            "justify-content": "center"
        },
        ".ag-header-cell:not(:last-child)": {"border-right": "1px solid #e2e2e2 !important"}, ".ag-header-group-cell:not(:last-child)": {"border-right": "1px solid #e2e2e2 !important"}}
    
    grid_response = AgGrid(df_display, gridOptions=grid_options, custom_css=custom_css, data_return_mode=DataReturnMode.AS_INPUT, update_mode=GridUpdateMode.MODEL_CHANGED, height=400,
                           width='100%', key=f"{prefix}grid_{selected_year}_{selected_month}_{st.session_state.session_count}", allow_unsafe_jscode=True, enable_enterprise_modules=False, theme='streamlit')

    # --- グリッド編集内容の反映 ---
    updated_df = pd.DataFrame(grid_response['data'])
    if not updated_df.empty and len(df_display) == len(updated_df):
        current_display_str = df_display.fillna("").astype(str)
        updated_display_str = updated_df.set_index(df_display.index).fillna("").astype(str)
        if not current_display_str.equals(updated_display_str):
            working_copy = st.session_state[session_key_current_data].copy()
            working_copy.update(updated_df.set_index(df_display.index))
            st.session_state[session_key_current_data] = working_copy

    # --- 更新ボタンとそれに伴う処理 ---
    if not st.session_state[f"{prefix}update_in_progress"] and not st.session_state[f"{prefix}confirming_deletion"]:
        if st.button("更新", type="primary", key=f"{prefix}update_button"):
            latest_df, original_df = st.session_state[session_key_current_data], st.session_state[session_key_original_df]
            machine_nos_to_delete = latest_df[latest_df['delete_flag'] == True]['machine_no'].tolist()
            
            def normalize_value(val):
                if pd.isna(val):
                    return '___EMPTY_OR_NAN___'
                return str(val)

            original_comp = original_df.drop(columns=['delete_flag'], errors='ignore').applymap(normalize_value)
            latest_comp = latest_df.drop(columns=['delete_flag'], errors='ignore').applymap(normalize_value)
            common_indices = original_comp.index.intersection(latest_comp.index)
            changed_mask = (original_comp.loc[common_indices] != latest_comp.loc[common_indices]).any(axis=1)
            indices_to_update = original_comp.loc[common_indices][changed_mask].index.tolist()
            indices_to_update = [idx for idx in indices_to_update if original_df.loc[idx, 'machine_no'] not in machine_nos_to_delete]

            if not machine_nos_to_delete and not indices_to_update:
                st.warning("変更された項目がありません。")
            else:
                st.session_state[f'{prefix}df_to_process'] = latest_df
                st.session_state[f'{prefix}machine_nos_to_delete'] = machine_nos_to_delete
                st.session_state[f'{prefix}indices_to_update'] = indices_to_update
                st.session_state[f"{prefix}confirming_deletion"] = bool(machine_nos_to_delete)
                st.session_state[f"{prefix}update_in_progress"] = not bool(machine_nos_to_delete)
                st.rerun()

    if st.session_state[f"{prefix}confirming_deletion"]:
        st.warning(f"**削除対象が{len(st.session_state[f'{prefix}machine_nos_to_delete'])}件あります。**\n\n本当に実行してもよろしいですか？この操作は元に戻せません。")
        confirm_cols = st.columns(8)
        if confirm_cols[0].button("はい", type="primary", key=f"{prefix}confirm_yes"):
            st.session_state[f"{prefix}confirming_deletion"], st.session_state[f"{prefix}update_in_progress"] = False, True
            st.rerun()
        if confirm_cols[1].button("いいえ", key=f"{prefix}confirm_no"):
            st.session_state[f"{prefix}confirming_deletion"], st.session_state[f'{prefix}machine_nos_to_delete'], st.session_state[f'{prefix}indices_to_update'] = False, [], []
            st.rerun()

    if st.session_state[f"{prefix}update_in_progress"]:
        deleted_count, succeeded_rows, failed_rows = 0, [], []
        machine_nos_to_delete = st.session_state.get(f'{prefix}machine_nos_to_delete', [])
        indices_to_update = st.session_state.get(f'{prefix}indices_to_update', [])
        
        if machine_nos_to_delete:
            with st.spinner("選択された行を削除中..."):
                deleted_count = database.delete_rows(selected_year, selected_month, machine_nos_to_delete, table_name)
        
        if indices_to_update:
            df_to_process, original_df = st.session_state[f'{prefix}df_to_process'], st.session_state[session_key_original_df]
            with st.spinner("データベースを更新中..."):
                for idx in indices_to_update:
                    if idx in df_to_process.index and idx in original_df.index:
                        row_to_update = df_to_process.loc[idx]
                        if database.update_row_with_lock(row_to_update, selected_year, selected_month, original_df.loc[idx, 'last_modified_timestamp'], table_name):
                            succeeded_rows.append(row_to_update['machine_no'])
                        else:
                            failed_rows.append(row_to_update['machine_no'])
        
        if deleted_count > 0: st.success(f"{deleted_count}件のデータを削除しました。")
        if succeeded_rows: st.success(f"以下の機番の更新に成功しました: {', '.join(succeeded_rows)}")
        if failed_rows: st.error(f"以下の機番は他のユーザーによって先に更新されたため、更新できませんでした: {', '.join(failed_rows)}")

        placeholder = st.empty()
        for i in range(5, 0, -1):
            placeholder.info(f"{i} 秒後に画面を更新します...")
            time.sleep(1)
        placeholder.empty()

        st.session_state.session_count += 1
        keys_to_delete = [
            f'{prefix}df_to_process', f'{prefix}machine_nos_to_delete', f'{prefix}indices_to_update', 
            f'{prefix}update_in_progress', f'{prefix}confirming_deletion', 
            session_key_original_df, session_key_current_data
        ]
        for key in keys_to_delete:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

    st.markdown("---")

    # --- 手動データ追加 ---
    def handle_add_submission():
        if not st.session_state[f"{prefix}new_machine_no"] or not st.session_state[f"{prefix}new_model_name"]:
            st.session_state[f"{prefix}add_message"] = ('warning', "「機番」と「機種名」は必須です。")
            return
        nengetsu = f"{str(selected_year)[-2:]}{selected_month:02d}"
        new_data = {
            'machine_no': st.session_state[f"{prefix}new_machine_no"], 'model_name': st.session_state[f"{prefix}new_model_name"],
            'size_inch': st.session_state[f"{prefix}new_size_inch"], 'gauge': st.session_state[f"{prefix}new_gauge"],
            'production_plan_month_full': f"{nengetsu}{st.session_state[f'{prefix}new_suffix']}"
        }
        success, message = database.add_manual_row(selected_year, selected_month, new_data, table_name)
        if success:
            st.session_state[f"{prefix}add_message"] = ('success', f"機番: {new_data['machine_no']} を追加しました。")
            for k_suffix in ['new_machine_no', 'new_model_name', 'new_size_inch', 'new_gauge']: st.session_state[f"{prefix}{k_suffix}"] = ""
            st.session_state[f"{prefix}new_suffix"] = 1
            # データ追加成功後、セッション中のデータフレームを削除して次回アクセス時に再読み込みさせる
            keys_to_del = [session_key_original_df, session_key_current_data]
            for k in keys_to_del:
                if k in st.session_state: del st.session_state[k]
        else:
            st.session_state[f"{prefix}add_message"] = ('error', message)

    st.write("**手動データ追加**")
    add_cols = st.columns([2, 3, 0.75, 0.75, 1.2, 1])
    add_cols[0].text_input("機番", key=f"{prefix}new_machine_no")
    add_cols[1].text_input("機種名", key=f"{prefix}new_model_name")
    add_cols[2].text_input("吋", key=f"{prefix}new_size_inch")
    add_cols[3].text_input("G", key=f"{prefix}new_gauge")
    add_cols[4].selectbox("生産計画次", options=list(range(1, 9)), key=f"{prefix}new_suffix")
    add_cols[5].button("追加", on_click=handle_add_submission, key=f"{prefix}add_button")

    message_placeholder = st.empty()
    if st.session_state[f"{prefix}add_message"]:
        msg_type, msg_text = st.session_state[f"{prefix}add_message"]
        getattr(message_placeholder, msg_type)(msg_text)
        if msg_type == 'success':
            time.sleep(3)
            st.session_state[f"{prefix}add_message"] = None
            st.rerun()
        else:
            st.session_state[f"{prefix}add_message"] = None
