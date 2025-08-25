###
# アッセンブリー課チェックシート
# ADD_20250626 ギアボックス追加
###
import streamlit as st
import pandas as pd
import datetime
import time

import database
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode


def render(checksheet_type: str, table_name: str):
    """
    ギアボックスGrのチェックシートタブUIを描画する関数。

    Args:
        checksheet_type (str): 'ギアボックスGr'。UIのタイトルやマスターデータの取得に使用。
        table_name (str): データベース操作の対象となるテーブル名。
    """
    # st.session_state のキーを動的に生成するためのプレフィックス
    prefix = 'gearbox_gr_'

    # --- ヘッダーとセレクター ---
    header_cols = st.columns(2)
    with header_cols[0]:
        st.subheader(f"{checksheet_type}チェックシート")
    with header_cols[1]:
        now = datetime.datetime.now()
        year_options, month_options = [
            now.year - 1, now.year, now.year + 1], list(range(1, 13))
        suffix_options = [""] + list(range(1, 9))

        selector_cols = st.columns(3)
        selected_year = selector_cols[0].selectbox(
            "生産計画年", year_options, index=year_options.index(now.year), key=f"{prefix}main_year")
        selected_month = selector_cols[1].selectbox(
            "生産計画月", month_options, index=now.month - 1, format_func=lambda x: f"{x:02d}", key=f"{prefix}main_month")
        selected_suffix = selector_cols[2].selectbox(
            "生産計画次", suffix_options, index=0, key=f"{prefix}main_suffix")

    # --- データ取得・更新 ---
    if st.session_state[f"{prefix}last_fetched_year_month"] != (selected_year, selected_month):
        with st.spinner(f"{selected_year}年{selected_month}月の{checksheet_type}生産機情報を取得・更新中..."):
            product_type = 'gearbox_gr'
            fetched_data = database.fetch_production_machine_info(
                selected_year, selected_month, product_type)
            if not fetched_data.empty:
                database.upsert_production_machine_data(
                    fetched_data, selected_year, selected_month, table_name)

        st.session_state[f"{prefix}last_fetched_year_month"] = (
            selected_year, selected_month)
        for key in list(st.session_state.keys()):
            if key.startswith(f"original_df_{prefix}") or key.startswith(f"current_data_{prefix}"):
                del st.session_state[key]
        st.rerun()

    # --- データ準備 for AgGrid ---
    session_key_original_df = f"original_df_{prefix}{selected_year}_{selected_month}"
    session_key_current_data = f"current_data_{prefix}{selected_year}_{selected_month}"

    if session_key_current_data not in st.session_state:
        fresh_df = database.get_checksheet_data(
            selected_year, selected_month, table_name).reset_index(drop=True)
        fresh_df['delete_flag'] = False
        st.session_state[session_key_original_df] = fresh_df.copy()
        st.session_state[session_key_current_data] = fresh_df.copy()

    full_data = st.session_state[session_key_current_data]
    df_filtered = full_data[full_data['production_plan_month_full'].astype(str).str.endswith(
        str(selected_suffix))] if selected_suffix != "" and not full_data.empty else full_data

    df_display = df_filtered.drop(columns=['production_year', 'production_month', 'size_inch', 'gauge',
                                  'last_modified_timestamp', 'production_plan_month_full'], errors='ignore')

    # --- AgGridの定義 ---
    date_value_parser = JsCode(
        """ function(params) { if (params.newValue instanceof Date && !isNaN(params.newValue)) { const d = params.newValue; return `${d.getFullYear()}-${('0' + (d.getMonth() + 1)).slice(-2)}-${('0' + d.getDate()).slice(-2)}`; } return params.newValue; } """)
    date_display_formatter = JsCode(
        """ function(params) { if (!params.value) { return ''; } let dateObj; if (params.value instanceof Date && !isNaN(params.value)) { dateObj = params.value; } else if (typeof params.value === 'string') { dateObj = new Date(params.value); if (isNaN(dateObj.getTime())) { return params.value.split(' ')[0]; } } else { return ''; } return `${('0' + (dateObj.getMonth() + 1)).slice(-2)}/${('0' + dateObj.getDate()).slice(-2)}`; } """)
    getRowStyle_js = JsCode(
        """ function(params) { if (params.data.completion_status === '不要') { return { 'background-color': '#A9A9A9' }; } return null; } """)

    worker_names = database.get_workers_for_checksheet(checksheet_type)[
        'worker_name'].tolist()

    # [新規] ヘッダーに適用するカスタムCSSクラス名を定義
    CUSTOM_HEADER_CLASS = "gearbox-custom-header"

    # [修正] 共通の列定義を更新し、中央揃え用の 'ag-header-cell-center-aligned' クラスを追加
    worker_column_def = {
        'width': 56,  # 75 * 0.75 = 56.25
        'editable': True,
        'cellEditor': 'agSelectCellEditor',
        'cellEditorParams': {'values': [""] + worker_names},
        'cellClass': 'small-font-cell center-align',
        'headerClass': f"{CUSTOM_HEADER_CLASS} ag-header-cell-center-aligned"
    }
    date_column_def = {
        'width': 50,
        'editable': True,
        'cellEditor': 'agDateCellEditor',
        'valueParser': date_value_parser,
        'valueFormatter': date_display_formatter,
        'cellClass': 'center-align',
        'headerClass': f"{CUSTOM_HEADER_CLASS} ag-header-cell-center-aligned"
    }

    is_grid_editable = not st.session_state.get(f"{prefix}update_in_progress", False)

    # [修正] headerNameに改行コード(\n)を挿入し、縦書き表示に対応
    column_defs = [
        {'field': 'machine_no', 'headerName': "機番", 'width': 90,
            'pinned': 'left', 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'model_name', 'headerName': "機種名", 'width': 130,
            'headerClass': 'ag-header-cell-center-aligned'},
        {**worker_column_def, 'headerName': 'ギ\nヤ\nボ\nッ\nク\nス\n準\n備',
            'field': 'gearbox_prep_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'ギ\nヤ\nボ\nッ\nク\nス\n内\n部\n製\n作',
            'field': 'gearbox_internal_mfg_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'ギ\nヤ\nボ\nッ\nク\nス\n組\n込\nみ',
            'field': 'gearbox_assy_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'ハ\nン\nド\nホ\nイ\n｜\nル\n準\n備',
            'field': 'handwheel_prep_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'ハ\nン\nド\nホ\nイ\n｜\nル\n部\n品\n製\n作',
            'field': 'handwheel_parts_mfg_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'ワ\nン\nウ\nェ\nイ\n\nコ\nロ\n確\n認',
            'field': 'oneway_clutch_check_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'ハ\nン\nド\nホ\nイ\n｜\nル\n組\n込\nみ',
            'field': 'handwheel_assy_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'カ\nウ\nン\nタ\n｜\nギ\nア\n準\n備',
            'field': 'counter_gear_prep_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'カ\nウ\nン\nタ\n｜\nギ\nア\n組\n込\nみ',
            'field': 'counter_gear_assy_worker', 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': 'サ\nイ\nド\n組\n込\nみ',
            'field': 'side_assy_worker', 'editable': is_grid_editable},
        # 予備項目
        {**worker_column_def, 'headerName': '予備1', 'field': 'spare_1_worker', 'hide': True, 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': '予備2', 'field': 'spare_2_worker', 'hide': True, 'editable': is_grid_editable},
        {**worker_column_def, 'headerName': '予備3', 'field': 'spare_3_worker', 'hide': True, 'editable': is_grid_editable},
        {
            'headerName': '完\n成\n品', 'field': 'completion_status', 'width': 56,  # 75 * 0.75 = 56.25
            'editable': is_grid_editable, 'cellEditor': 'agSelectCellEditor',
            'cellEditorParams': {'values': ["", "合", "否", "不要"]},
            'cellClass': 'center-align',
            'headerClass': f"{CUSTOM_HEADER_CLASS} ag-header-cell-center-aligned"
        },
        {**date_column_def, 'headerName': '完\n成\n日\n付', 'field': 'completion_date', 'width': 75, 'editable': is_grid_editable},
        {'field': 'remarks', 'headerName': '備考欄', 'width': 150, 'editable': is_grid_editable,
            'wrapText': True, 'autoHeight': True, 'headerClass': 'ag-header-cell-center-aligned'},
        {'field': 'delete_flag', 'headerName': '削除', 'width': 60, 'editable': is_grid_editable,
            'cellRenderer': 'agCheckboxCellRenderer', 'headerClass': 'ag-header-cell-center-aligned'}
    ]

    grid_options = {
        "columnDefs": column_defs,
        "defaultColDef": {
            "wrapHeaderText": True,
            "autoHeaderHeight": True,
            "suppressMovable": True,
            "resizable": False
        },
        "suppressRowClickSelection": True,
        "getRowStyle": getRowStyle_js,
        "headerHeight": 160,  # 縦書きのためヘッダー高さを確保
    }

    # [修正] custom_cssにヘッダー中央揃え用の定義を追加
    custom_css = {
        ".ag-header-cell-center-aligned .ag-header-cell-label": {
            "justify-content": "center"
        },
        ".ag-header-cell:not(:last-child)": {"border-right": "1px solid #e2e2e2 !important"},
        ".ag-header-group-cell:not(:last-child)": {"border-right": "1px solid #e2e2e2 !important"},
        ".small-font-cell": {
            "font-size": "smaller !important"
        },
        ".center-align": {
            "text-align": "center !important",
        },
        f".{CUSTOM_HEADER_CLASS} .ag-header-cell-label": {
            "font-size": "smaller !important",
            "white-space": "pre-wrap !important",
            "line-height": "1.2em !important",
        }
    }

    grid_response = AgGrid(df_display, gridOptions=grid_options, custom_css=custom_css, data_return_mode=DataReturnMode.AS_INPUT, update_mode=GridUpdateMode.MODEL_CHANGED, height=480,
                           width='100%', key=f"{prefix}grid_{selected_year}_{selected_month}_{st.session_state.session_count}", allow_unsafe_jscode=True, enable_enterprise_modules=False, theme='streamlit')

    # --- グリッド編集内容の反映 ---
    updated_df = pd.DataFrame(grid_response['data'])
    if not updated_df.empty and len(df_display) == len(updated_df):
        current_display_str = df_display.fillna("").astype(str)
        updated_display_str = updated_df.set_index(
            df_display.index).fillna("").astype(str)
        if not current_display_str.equals(updated_display_str):
            working_copy = st.session_state[session_key_current_data].copy()
            working_copy.update(updated_df.set_index(df_display.index))
            st.session_state[session_key_current_data] = working_copy

    # --- 更新ボタンとそれに伴う処理 ---
    if not st.session_state[f"{prefix}update_in_progress"] and not st.session_state[f"{prefix}confirming_deletion"]:
        if st.button("更新", type="primary", key=f"{prefix}update_button"):
            latest_df, original_df = st.session_state[
                session_key_current_data], st.session_state[session_key_original_df]
            machine_nos_to_delete = latest_df[latest_df['delete_flag']
                                              == True]['machine_no'].tolist()

            def normalize_value(val):
                if pd.isna(val):
                    return '___EMPTY_OR_NAN___'
                return str(val)

            original_comp = original_df.drop(
                columns=['delete_flag'], errors='ignore').applymap(normalize_value)
            latest_comp = latest_df.drop(
                columns=['delete_flag'], errors='ignore').applymap(normalize_value)
            common_indices = original_comp.index.intersection(
                latest_comp.index)
            changed_mask = (
                original_comp.loc[common_indices] != latest_comp.loc[common_indices]).any(axis=1)
            indices_to_update = original_comp.loc[common_indices][changed_mask].index.tolist(
            )
            indices_to_update = [
                idx for idx in indices_to_update if original_df.loc[idx, 'machine_no'] not in machine_nos_to_delete]

            if not machine_nos_to_delete and not indices_to_update:
                st.warning("変更された項目がありません。")
            else:
                st.session_state[f'{prefix}df_to_process'] = latest_df
                st.session_state[f'{prefix}machine_nos_to_delete'] = machine_nos_to_delete
                st.session_state[f'{prefix}indices_to_update'] = indices_to_update
                st.session_state[f"{prefix}confirming_deletion"] = bool(
                    machine_nos_to_delete)
                st.session_state[f"{prefix}update_in_progress"] = not bool(
                    machine_nos_to_delete)
                st.rerun()

    if st.session_state[f"{prefix}confirming_deletion"]:
        delete_key = f'{prefix}machine_nos_to_delete'
        num_to_delete = len(st.session_state.get(delete_key, []))
        st.warning(
            f"**削除対象が{num_to_delete}件あります。**\n\n本当に実行してもよろしいですか？この操作は元に戻せません。")
        confirm_cols = st.columns(8)
        if confirm_cols[0].button("はい", type="primary", key=f"{prefix}confirm_yes"):
            st.session_state[f"{prefix}confirming_deletion"], st.session_state[f"{prefix}update_in_progress"] = False, True
            st.rerun()
        if confirm_cols[1].button("いいえ", key=f"{prefix}confirm_no"):
            st.session_state[f"{prefix}confirming_deletion"], st.session_state[
                f'{prefix}machine_nos_to_delete'], st.session_state[f'{prefix}indices_to_update'] = False, [], []
            st.rerun()

    if st.session_state[f"{prefix}update_in_progress"]:
        deleted_count, succeeded_rows, failed_rows = 0, [], []
        machine_nos_to_delete = st.session_state.get(
            f'{prefix}machine_nos_to_delete', [])
        indices_to_update = st.session_state.get(
            f'{prefix}indices_to_update', [])

        if machine_nos_to_delete:
            with st.spinner("選択された行を削除中..."):
                deleted_count = database.delete_rows(
                    selected_year, selected_month, machine_nos_to_delete, table_name)

        if indices_to_update:
            df_to_process, original_df = st.session_state[
                f'{prefix}df_to_process'], st.session_state[session_key_original_df]
            with st.spinner("データベースを更新中..."):
                for idx in indices_to_update:
                    if idx in df_to_process.index and idx in original_df.index:
                        row_to_update = df_to_process.loc[idx]
                        if database.update_row_with_lock(row_to_update, selected_year, selected_month, original_df.loc[idx, 'last_modified_timestamp'], table_name):
                            succeeded_rows.append(row_to_update['machine_no'])
                        else:
                            failed_rows.append(row_to_update['machine_no'])

        if deleted_count > 0:
            st.success(f"{deleted_count}件のデータを削除しました。")
        if succeeded_rows:
            st.success(f"以下の機番の更新に成功しました: {', '.join(succeeded_rows)}")
        if failed_rows:
            st.error(
                f"以下の機番は他のユーザーによって先に更新されたため、更新できませんでした: {', '.join(failed_rows)}")

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
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.markdown("---")

    # --- 手動データ追加 ---
    def handle_add_submission():
        if not st.session_state[f"{prefix}new_machine_no"] or not st.session_state[f"{prefix}new_model_name"]:
            st.session_state[f"{prefix}add_message"] = (
                'warning', "「機番」と「機種名」は必須です。")
            return

        nengetsu = f"{str(selected_year)[-2:]}{selected_month:02d}"
        suffix_key = f"{prefix}new_suffix"
        suffix_val = st.session_state[suffix_key]

        new_data = {
            'machine_no': st.session_state[f"{prefix}new_machine_no"],
            'model_name': st.session_state[f"{prefix}new_model_name"],
            'production_plan_month_full': f"{nengetsu}{suffix_val}"
        }

        success, message = database.add_manual_row(
            selected_year, selected_month, new_data, table_name)

        if success:
            st.session_state[f"{prefix}add_message"] = (
                'success', f"機番: {new_data['machine_no']} を追加しました。")
            for k_suffix in ['new_machine_no', 'new_model_name']:
                st.session_state[f"{prefix}{k_suffix}"] = ""
            st.session_state[suffix_key] = 1

            keys_to_del = [session_key_original_df, session_key_current_data]
            for k in keys_to_del:
                if k in st.session_state:
                    del st.session_state[k]
        else:
            st.session_state[f"{prefix}add_message"] = ('error', message)

    st.write("**手動データ追加**")
    add_cols = st.columns([2, 3, 1.2, 1])
    add_cols[0].text_input("機番", key=f"{prefix}new_machine_no")
    add_cols[1].text_input("機種名", key=f"{prefix}new_model_name")
    add_cols[2].selectbox("生産計画次", options=list(
        range(1, 9)), key=f"{prefix}new_suffix")
    add_cols[3].button("追加", on_click=handle_add_submission,
                       key=f"{prefix}add_button")

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
