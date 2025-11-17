"""
UI コンポーネント
"""
import streamlit as st
import pandas as pd

# render_sidebar関数は削除（Streamlit Pagesを使用するため）

def render_main_grid(data: pd.DataFrame, stats: dict = None):
    """
    Streamlit標準テーブルを表示

    Args:
        data: 表示するDataFrame
        stats: 統計情報の辞書 (optional)
            - ej_source_count: EJ抽出件数
            - rbom_source_count: rBOM抽出件数
            - ej_after_diff_count: 差引処理後のEJ件数
            - rbom_after_diff_count: 差引処理後のrBOM件数
            - ej_conditions: EJ抽出条件テキスト
            - rbom_conditions: rBOM抽出条件テキスト
    """

    # データのコピーを作成
    data = data.copy()

    # 結果列を作成（手動/自動/未マッピングの判定）
    def determine_result(row):
        # statusフィールドを優先チェック（"済2"などの特殊ステータス）
        status = row.get('status')
        if pd.notna(status) and status != '':
            return status  # statusが設定されている場合はそのまま返す（"済2"など）

        # is_manual_mappingフラグをチェック（Trueまたは1の場合）
        manual_flag = row.get('is_manual_mapping')

        # デバッグ: 最初の10行だけログ出力
        import logging
        logger = logging.getLogger(__name__)
        if hasattr(determine_result, 'debug_count'):
            determine_result.debug_count += 1
        else:
            determine_result.debug_count = 1

        if determine_result.debug_count <= 10:
            logger.debug(f"[結果判定] ej_order_no={row.get('ej_order_no')}, rbom_order_no={row.get('rbom_order_no')}, status={status}, is_manual_mapping={manual_flag} (型: {type(manual_flag)})")

        # SQLiteはBOOLEANを0/1として保存するため、1またはTrueをチェック
        if pd.notna(manual_flag) and manual_flag in [True, 1, '1', 1.0]:
            return '手'
        elif pd.notna(row.get('ej_order_no')) and pd.notna(row.get('rbom_order_no')):
            return '済'  # 自動マッピング成功は「済」
        else:
            return '未'  # 未マッピング

    data['result'] = data.apply(determine_result, axis=1)

    # 固定データを保存（表示変換前）
    fixed_data_original = data[data['is_fixed'].isin([True, 1, '1', 1.0])].copy() if 'is_fixed' in data.columns else pd.DataFrame()

    # is_fixed列を○/空欄に変換
    if 'is_fixed' in data.columns:
        data['is_fixed'] = data['is_fixed'].apply(lambda x: '○' if x in [True, 1, '1', 1.0] else '')

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
    
    # カラムの順序を指定（品目コード→EJ発注番号→EJ連番、rBOM発注番号→rBOM連番の順序）
    column_order = []
    display_columns = {}

    # 統一品目コード（最優先）
    if 'item_code' in data.columns:
        column_order.append('item_code')
        display_columns['item_code'] = '共通品目コード'

    # 結果列（手動/自動/未マッピング）
    if 'result' in data.columns:
        column_order.append('result')
        display_columns['result'] = '結果'

    # 固定列
    if 'is_fixed' in data.columns:
        column_order.append('is_fixed')
        display_columns['is_fixed'] = '固定'

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
    # EJステータスとEJ発注種別は非表示（データは保持）
    # if 'ej_status' in data.columns:
    #     column_order.append('ej_status')
    #     display_columns['ej_status'] = 'EJステータス'
    # if 'ej_purch_odr_typ' in data.columns:
    #     column_order.append('ej_purch_odr_typ')
    #     display_columns['ej_purch_odr_typ'] = 'EJ発注種別'
    if 'ej_delivery_date' in data.columns:
        column_order.append('ej_delivery_date')
        display_columns['ej_delivery_date'] = 'EJ納期'
    if 'ej_vend_cd' in data.columns:
        column_order.append('ej_vend_cd')
        display_columns['ej_vend_cd'] = 'EJ仕入先コード'
    
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
    if 'rbom_ktcd' in data.columns:
        column_order.append('rbom_ktcd')
        display_columns['rbom_ktcd'] = 'rBOM工程コード'
    if 'rbom_srcd' in data.columns:
        column_order.append('rbom_srcd')
        display_columns['rbom_srcd'] = 'rBOM仕入先コード'
    if 'mk020_note' in data.columns:
        column_order.append('mk020_note')
        display_columns['mk020_note'] = 'rBOM備考'

    # データをソート：品目コード→EJ発注番号→EJ連番→rBOM発注番号+行番号→rBOM連番の順
    sort_columns = []

    if 'item_code' in data.columns:
        sort_columns.append('item_code')
    if 'ej_order_no' in data.columns:
        sort_columns.append('ej_order_no')
    if 'ej_m_sequence' in data.columns:
        sort_columns.append('ej_m_sequence')
    if 'rbom_order_line' in data.columns:
        sort_columns.append('rbom_order_line')
    if 'rbom_m_sequence' in data.columns:
        sort_columns.append('rbom_m_sequence')

    if sort_columns:
        data = data.sort_values(by=sort_columns, ascending=True, na_position='last')

    # カラムの順序を調整
    data_reordered = data[column_order]

    # データフレームのカラム名を変更
    display_data = data_reordered.rename(columns=display_columns)

    # Streamlit dataframe（読み取り専用）- パフォーマンス最適化
    st.dataframe(
        display_data,
        use_container_width=True,
        height=400,
        hide_index=True,
    )

    # 固定マッピング管理セクション
    if not fixed_data_original.empty:
        st.markdown("---")
        st.subheader(f"📌 固定マッピング管理 ({len(fixed_data_original)}件)")

        # 検索とボタンのレイアウト
        search_col, btn_col1 = st.columns([3, 1])

        with search_col:
            search_ej_order = st.text_input(
                "EJ発注番号で検索",
                key="search_ej_order",
                placeholder="EJ発注番号を入力してください",
                help="部分一致検索に対応しています"
            )

        with btn_col1:
            st.write("")  # スペース調整
            if st.button("全固定解除", type="secondary", key="unfix_all_btn"):
                # 全固定解除の確認
                if 'confirm_unfix_all' not in st.session_state:
                    st.session_state.confirm_unfix_all = True
                    st.rerun()

        # 全固定解除の確認ダイアログ
        if st.session_state.get('confirm_unfix_all', False):
            st.warning(f"⚠️ 固定されている全{len(fixed_data_original)}件のマッピングを解除しますか？")
            confirm_col1, confirm_col2, confirm_col3 = st.columns([1, 1, 4])
            with confirm_col1:
                if st.button("はい、解除する", key="confirm_yes", type="primary"):
                    # 全件解除
                    if 'unfix_target' not in st.session_state:
                        st.session_state.unfix_target = []
                    for _, row in fixed_data_original.iterrows():
                        st.session_state.unfix_target.append({
                            'ej_order_no': row.get('ej_order_no', ''),
                            'rbom_order_no': row.get('rbom_order_no', ''),
                            'rbom_line_no': row.get('rbom_line_no', '')
                        })
                    del st.session_state.confirm_unfix_all
                    st.rerun()
            with confirm_col2:
                if st.button("キャンセル", key="confirm_no"):
                    del st.session_state.confirm_unfix_all
                    st.rerun()

        # 検索フィルタリング（検索欄が空の場合は何も表示しない）
        if search_ej_order:
            filtered_fixed = fixed_data_original[
                fixed_data_original['ej_order_no'].astype(str).str.contains(search_ej_order, case=False, na=False)
            ]

            st.caption(f"表示件数: {len(filtered_fixed)}件")

            # 検索結果を表示
            if not filtered_fixed.empty:
                for idx, row in filtered_fixed.iterrows():
                    ej_order_no = row.get('ej_order_no', '')
                    rbom_order_no = row.get('rbom_order_no', '')
                    rbom_line_no = row.get('rbom_line_no', '')
                    item_code = row.get('item_code', '')
                    status = row.get('status', '')

                    # rBOM発注番号+行番号の表示
                    if pd.notna(rbom_order_no) and pd.notna(rbom_line_no):
                        rbom_display = f"{str(rbom_order_no).zfill(9)}+{str(int(rbom_line_no)).zfill(3)}"
                    else:
                        rbom_display = "N/A"

                    # 行ごとに情報と解除ボタンを表示
                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        st.text(f"品目: {item_code} | EJ: {ej_order_no} | rBOM: {rbom_display} | 状態: {status}")
                    with col_btn:
                        # 一意なキーを生成
                        button_key = f"unfix_{ej_order_no}_{rbom_order_no}_{rbom_line_no}_{idx}"
                        if st.button("解除", key=button_key, type="secondary"):
                            # セッション状態に解除対象を保存
                            if 'unfix_target' not in st.session_state:
                                st.session_state.unfix_target = []
                            st.session_state.unfix_target.append({
                                'ej_order_no': ej_order_no,
                                'rbom_order_no': rbom_order_no,
                                'rbom_line_no': rbom_line_no
                            })
                            st.rerun()
            else:
                st.info("検索条件に一致する固定マッピングがありません。")

    # データ統計情報とCSV出力
    col1, col2, col3 = st.columns([1, 1, 5])

    with col1:
        total_count = len(data)
        st.metric("総件数", total_count)

    with col2:
        # マッピングしたデータ（EJとrBOM両方に値があるデータ）
        if len(data) > 0:
            matched_count = len(data.dropna(subset=['ej_order_no', 'rbom_order_no']))
            st.metric("マッピング済", matched_count)

    with col3:
        # CSV出力
        if st.button("CSV出力"):
            from datetime import datetime
            import io

            # CSV用のカラム順序と項目名（画面表示＋非表示項目を含む）
            csv_column_order = []
            csv_display_columns = {}

            # 統一品目コード
            if 'item_code' in data.columns:
                csv_column_order.append('item_code')
                csv_display_columns['item_code'] = '共通品目コード'

            # 結果列
            if 'result' in data.columns:
                csv_column_order.append('result')
                csv_display_columns['result'] = '結果'

            # 固定列
            if 'is_fixed' in data.columns:
                csv_column_order.append('is_fixed')
                csv_display_columns['is_fixed'] = '固定'

            # EJグループ（全項目を含む）
            if 'ej_order_no' in data.columns:
                csv_column_order.append('ej_order_no')
                csv_display_columns['ej_order_no'] = 'EJ発注番号'
            if 'ej_m_sequence' in data.columns:
                csv_column_order.append('ej_m_sequence')
                csv_display_columns['ej_m_sequence'] = 'EJ連番'
            if 'ej_item_code' in data.columns:
                csv_column_order.append('ej_item_code')
                csv_display_columns['ej_item_code'] = 'EJ品目コード'
            if 'ej_item_name' in data.columns:
                csv_column_order.append('ej_item_name')
                csv_display_columns['ej_item_name'] = 'EJ品目名'
            if 'ej_quantity' in data.columns:
                csv_column_order.append('ej_quantity')
                csv_display_columns['ej_quantity'] = 'EJ数'
            if 'ej_status' in data.columns:
                csv_column_order.append('ej_status')
                csv_display_columns['ej_status'] = 'EJステータス'
            if 'ej_purch_odr_typ' in data.columns:
                csv_column_order.append('ej_purch_odr_typ')
                csv_display_columns['ej_purch_odr_typ'] = 'EJ発注種別'
            if 'ej_delivery_date' in data.columns:
                csv_column_order.append('ej_delivery_date')
                csv_display_columns['ej_delivery_date'] = 'EJ納期'
            if 'ej_vend_cd' in data.columns:
                csv_column_order.append('ej_vend_cd')
                csv_display_columns['ej_vend_cd'] = 'EJ仕入先コード'

            # rBOMグループ（全項目を含む）
            if 'rbom_order_line' in data.columns:
                csv_column_order.append('rbom_order_line')
                csv_display_columns['rbom_order_line'] = 'rBOM発注番号+行番号'
            if 'rbom_m_sequence' in data.columns:
                csv_column_order.append('rbom_m_sequence')
                csv_display_columns['rbom_m_sequence'] = 'rBOM連番'
            if 'rbom_item_code' in data.columns:
                csv_column_order.append('rbom_item_code')
                csv_display_columns['rbom_item_code'] = 'rBOM品目コード'
            if 'rbom_item_name' in data.columns:
                csv_column_order.append('rbom_item_name')
                csv_display_columns['rbom_item_name'] = 'rBOM品目名'
            if 'rbom_quantity' in data.columns:
                csv_column_order.append('rbom_quantity')
                csv_display_columns['rbom_quantity'] = 'rBOM数'
            if 'rbom_delivery_date' in data.columns:
                csv_column_order.append('rbom_delivery_date')
                csv_display_columns['rbom_delivery_date'] = 'rBOM納期'
            if 'rbom_ktcd' in data.columns:
                csv_column_order.append('rbom_ktcd')
                csv_display_columns['rbom_ktcd'] = 'rBOM工程コード'
            if 'rbom_srcd' in data.columns:
                csv_column_order.append('rbom_srcd')
                csv_display_columns['rbom_srcd'] = 'rBOM仕入先コード'
            if 'mk020_note' in data.columns:
                csv_column_order.append('mk020_note')
                csv_display_columns['mk020_note'] = 'rBOM備考'

            # CSV用データを準備
            csv_data_reordered = data[csv_column_order]
            csv_data_prepared = csv_data_reordered.rename(columns=csv_display_columns)

            # BOM付きUTF-8でCSVを生成（Excelでの文字化け防止）
            output = io.StringIO()
            csv_data_prepared.to_csv(output, index=False, encoding='utf-8')
            csv_string = output.getvalue()

            # UTF-8 BOM付きでエンコード
            csv_bytes = '\ufeff' + csv_string
            csv_data_bytes = csv_bytes.encode('utf-8')

            st.download_button(
                label="CSVダウンロード",
                data=csv_data_bytes,
                file_name=f"mapping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # 水平線
    st.markdown("---")

    # 詳細統計情報（小さく表示）
    if stats:
        st.markdown("""
        <style>
        .small-text {
            font-size: 0.85em;
            color: #666;
            line-height: 1.6;
        }
        .small-text strong {
            color: #333;
        }
        </style>
        """, unsafe_allow_html=True)

        info_col1, info_col2 = st.columns([1, 3])

        with info_col1:
            st.markdown('<div class="small-text">', unsafe_allow_html=True)
            st.markdown(f"**📊 データ抽出件数**")
            st.markdown(f"- EJ抽出件数: **{stats.get('ej_source_count', 'N/A')}** 件")
            st.markdown(f"- rBOM抽出件数: **{stats.get('rbom_source_count', 'N/A')}** 件")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="small-text">', unsafe_allow_html=True)
            st.markdown(f"**🔢 差引処理後の件数**")
            st.markdown(f"- EJ側: **{stats.get('ej_source_count', 'N/A')}** → **{stats.get('ej_after_diff_count', 'N/A')}** 件")
            st.markdown(f"- rBOM側: **{stats.get('rbom_source_count', 'N/A')}** → **{stats.get('rbom_after_diff_count', 'N/A')}** 件")
            st.markdown("</div>", unsafe_allow_html=True)

        with info_col2:
            # 3カラムレイアウト（EJ条件、rBOM条件、手動マッピング）
            sub_col1, sub_col2, sub_col3 = st.columns(3)

            with sub_col1:
                st.markdown('<div class="small-text">', unsafe_allow_html=True)
                st.markdown(f"**📋 EJ抽出条件**")
                st.markdown(f"{stats.get('ej_conditions', 'N/A')}")
                st.markdown("</div>", unsafe_allow_html=True)

            with sub_col2:
                st.markdown('<div class="small-text">', unsafe_allow_html=True)
                st.markdown(f"**📋 rBOM抽出条件**")
                st.markdown(f"{stats.get('rbom_conditions', 'N/A')}")
                st.markdown("</div>", unsafe_allow_html=True)

            with sub_col3:
                st.markdown('<div class="small-text">', unsafe_allow_html=True)
                st.markdown(f"**🔧 手動マッピング**")
                manual_registered = stats.get('manual_mapping_registered_count', 0)
                manual_success = stats.get('manual_mapping_success_count', 0)
                manual_failed = stats.get('manual_mapping_failed_count', 0)
                st.markdown(f"- 登録件数: **{manual_registered}** 件")
                st.markdown(f"- マッピング成功: **{manual_success}** 件")
                st.markdown(f"- マッピング失敗: **{manual_failed}** 件")
                st.markdown("</div>", unsafe_allow_html=True)

            # マッピング失敗の詳細情報を表示
            manual_failed_details = stats.get('manual_mapping_failed_details', [])
            if manual_failed_details:
                st.markdown("---")
                st.markdown('<div class="small-text">', unsafe_allow_html=True)
                st.markdown(f"**⚠️ 手動マッピング失敗の詳細**")
                for detail in manual_failed_details:
                    ej_no = detail.get('ej_order_no', 'N/A')
                    rbom_no = detail.get('rbom_order_no', 'N/A')
                    rbom_line = str(detail.get('rbom_line_no', 'N/A')).zfill(3) if detail.get('rbom_line_no') else 'N/A'
                    reason = detail.get('reason', '不明')
                    st.markdown(f"- EJ={ej_no} ↔ rBOM={rbom_no}+{rbom_line}: {reason}")
                st.markdown("</div>", unsafe_allow_html=True)