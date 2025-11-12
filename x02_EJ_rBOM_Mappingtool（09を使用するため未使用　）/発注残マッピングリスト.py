"""
EJ-rBOM マッピングツール メインアプリケーション
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.db_manager import DatabaseManager
from data_sources.ej_connector import EJConnector
from data_sources.rbom_connector import RBOMConnector
from mapping.mapper import MappingEngine
from ui.components import render_main_grid
import os

# ページ設定
st.set_page_config(
    page_title="発注残マッピングリスト",
    page_icon="🔗",
    layout="wide"
)

# CSS設定（サイドバーを表示）
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
    .appview-container .main .block-container{
                        padding-top: 1rem;
                        padding-right: 3rem;
                        padding-left: 3rem;
                        padding-bottom: 1rem;
                    }  
                    .reportview-container {
                        padding-top: 0rem;
                        padding-right: 3rem;
                        padding-left: 3rem;
                        padding-bottom: 0rem;
                    }
                    header[data-testid="stHeader"] {
                        z-index: -1;
                    }
                    div[data-testid="stToolbar"] {
                    z-index: 100;
                    }
                    div[data-testid="stDecoration"] {
                    z-index: 100;
                    }
    .block-container {
                    padding-top: 0rem !important;
                    padding-bottom: 0rem !important;
                    }        
</style>
""", unsafe_allow_html=True)

def _ensure_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameを整形し、処理に必要な列を準備するヘルパー関数。
    - 'rbom_order_line'から'rbom_order_no'と'rbom_line_no'を生成
    - 'is_fixed'列の存在と型を保証
    - キー列のデータ型を統一
    """
    # copy()を避けてメモリ使用量を減らす
    # df = df.copy()

    # rBOM注文番号と行番号を分割（'+'で分割） - ベクトル化で高速化
    if 'rbom_order_line' in df.columns:
        mask = df['rbom_order_line'].notna() & (df['rbom_order_line'] != 'None') & (df['rbom_order_line'] != '')
        if mask.any():
            split_data = df.loc[mask, 'rbom_order_line'].str.split('+', n=1, expand=True)
            if len(split_data.columns) >= 2:
                df.loc[mask, 'rbom_order_no'] = split_data.iloc[:, 0]
                df.loc[mask, 'rbom_line_no'] = pd.to_numeric(split_data.iloc[:, 1], errors='coerce')

    # 'is_fixed'列を準備 - ベクトル化で高速化
    if 'is_fixed' not in df.columns:
        df['is_fixed'] = False
    else:
        # ベクトル化でfillnaを使用
        df['is_fixed'] = df['is_fixed'].fillna(False).astype(bool)

    # キー列のデータ型を統一 - ベクトル化で高速化
    for col in ['ej_order_no', 'rbom_order_no']:
        if col in df.columns:
            df[col] = df[col].replace(['nan', 'None'], None)
    if 'rbom_line_no' in df.columns:
        df['rbom_line_no'] = df['rbom_line_no'].where(df['rbom_line_no'].notna(), None)

    return df

def main():
    """メイン処理"""
    render_mapping_list_page()

def render_mapping_list_page():
    """発注残マッピングリスト画面"""
    
    col_condition, col_auto_btn = st.columns([6, 1])
    
    with col_condition:
        with st.expander("抽出条件", expanded=False):
            col1, col2 = st.columns([1, 1])
            with col1:
                start_date = st.date_input("納期開始日", value=date(2025, 7, 1))
            with col2:
                end_date = st.date_input("納期終了日", value=date(2025, 12, 31))
    
    with col_auto_btn:
        auto_mapping_btn = st.button("自動マッピング", type="primary")
    
    if start_date < date(2025, 7, 1):
        st.warning("⚠️ EJシステムのデータ量を考慮し、納期は2025年7月1日以降を指定してください。")
        return
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.db_manager.initialize_database()
    
    if 'grid_fixed_states' not in st.session_state:
        st.session_state.grid_fixed_states = {}
    
    # データキャッシュでパフォーマンス改善（カウンターベース）
    if 'cached_display_data' not in st.session_state:
        st.session_state.cached_display_data = None
    if 'data_cache_counter' not in st.session_state:
        st.session_state.data_cache_counter = 0
    if 'cached_counter' not in st.session_state:
        st.session_state.cached_counter = -1
    
    if auto_mapping_btn:
        print(f"[DEBUG] 自動マッピングボタンがクリックされました")
        print(f"[DEBUG] 現在のセッション状態: {st.session_state.get('auto_mapping_confirmed', '未設定')}")
        
        # 新しいクリックでは確認プロセスを開始
        if 'auto_mapping_confirmed' not in st.session_state:
            st.session_state.auto_mapping_confirmed = None  # 確認待ち状態
            print(f"[DEBUG] 確認待ち状態に設定")
    
    # 確認プロセスの管理を分離
    if 'auto_mapping_confirmed' in st.session_state:
        if st.session_state.auto_mapping_confirmed is None:
            # ポップアップ風の確認ダイアログ
            with st.container():
                st.markdown("""
<style>
    /* ツールバーとデコレーションを非表示（サイドバーボタンは残す） */
    div[data-testid="stToolbar"] {
        display: none !important;
        height: 0px !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
        height: 0px !important;
    }
    #MainMenu {
        display: none !important;
        height: 0px !important;
    }
    
    /* ヘッダーとフッターを非表示 */
    header {
        visibility: hidden;
        height: 0%;
    }
    footer {
        visibility: hidden;
        height: 0%;
    }
    header[data-testid="stHeader"] {
        z-index: -1;
    }
    
    /* コンテナのパディング調整 */
    .appview-container .main .block-container {
        padding-top: 1rem;
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 1rem;
    }
    .reportview-container {
        padding-top: 0rem;
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 0rem;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* ボタンスタイル調整 */
    div[data-testid="stButton"] > button {
        height: 38.4px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)
                
                col_center = st.columns([2, 1, 1, 2])
                
                with col_center[1]:
                    yes_btn = st.button("✅ はい", key="auto_mapping_yes", use_container_width=True)
                with col_center[2]:
                    no_btn = st.button("❌ いいえ", key="auto_mapping_no", use_container_width=True)
            
            if yes_btn:
                print(f"[DEBUG] はいボタンがクリックされました")
                st.session_state.auto_mapping_confirmed = True
                print(f"[DEBUG] 確認状態をTrueに設定してrerun")
                st.rerun()
            elif no_btn:
                print(f"[DEBUG] いいえボタンがクリックされました")
                del st.session_state.auto_mapping_confirmed
                st.info("自動マッピングがキャンセルされました。")
        
        elif st.session_state.auto_mapping_confirmed is True:
            print(f"[DEBUG] 確認完了 - 実際の処理を開始")
            # 確認後の実際の処理
            with st.spinner("データを取得中..."):
                try:
                    ej_connector = EJConnector()
                    ej_data = ej_connector.get_order_backlog(start_date, end_date)
                    
                    rbom_connector = RBOMConnector()
                    rbom_data = rbom_connector.get_orders_by_date_range(start_date, end_date)
                    
                    manual_mappings = st.session_state.db_manager.get_manual_mappings().to_dict('records')
                    fixed_mappings = st.session_state.db_manager.get_fixed_mappings().to_dict('records')
                    
                    mapper = MappingEngine()
                    mapping_results = mapper.execute_mapping(ej_data, rbom_data, manual_mappings, fixed_mappings)
                    
                    st.session_state.db_manager.save_mapping_results(mapping_results)
                    st.session_state.grid_fixed_states = {}
                    # キャッシュカウンターをインクリメントして強制更新
                    st.session_state.data_cache_counter += 1
                    
                    st.success("自動マッピングが完了しました。")
                    print(f"[DEBUG] 処理完了 - 確認状態を削除")
                    # 確認状態を削除（次回は再度確認ダイアログを表示）
                    if 'auto_mapping_confirmed' in st.session_state:
                        del st.session_state.auto_mapping_confirmed
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                    print(f"[DEBUG] エラー発生 - 確認状態を削除: {str(e)}")
                    # エラー時も確認状態を削除
                    if 'auto_mapping_confirmed' in st.session_state:
                        del st.session_state.auto_mapping_confirmed
    
    if 'db_manager' in st.session_state and st.session_state.db_manager:
        mapping_data_raw = st.session_state.db_manager.get_mapping_results()
        
        if not mapping_data_raw.empty:
            mapping_data = _ensure_and_prepare_data(mapping_data_raw)
                        
            # 「手動」以外はすべて「自動」として扱う
            auto_mapping_count = len(mapping_data[mapping_data['mapping_type'] != '手動'])
            
            if auto_mapping_count > 0:
                # 全選択状態を判定
                all_selected = is_all_selected(mapping_data)
                
                col_fixed, col_message, col_spacer, col_toggle = st.columns([2, 2, 2, 1.5])
                with col_fixed:
                    fixed_registration_btn = st.button("マッピング確定情報更新", type="secondary", key="fixed_registration")
                with col_message:
                    # 固定登録メッセージ表示用のプレースホルダー
                    message_placeholder = st.empty()
                    # スピナー表示用のプレースホルダー
                    spinner_placeholder = st.empty()
                    # セッション状態からメッセージを表示
                    if 'fixed_update_message' in st.session_state:
                        msg_type, msg_text = st.session_state.fixed_update_message
                        if msg_type == "success":
                            message_placeholder.success(msg_text)
                        else:
                            message_placeholder.info(msg_text)
                        # メッセージ表示後に削除
                        del st.session_state.fixed_update_message
                with col_toggle:
                    # 状態に応じてボタンを切り替え
                    if all_selected:
                        toggle_btn = st.button("全解除", key="toggle_selection")
                        select_all_btn = False
                        deselect_all_btn = toggle_btn
                    else:
                        toggle_btn = st.button("全選択", key="toggle_selection")
                        select_all_btn = toggle_btn
                        deselect_all_btn = False
            else:
                col_fixed, col_message = st.columns([1.5, 4.5])
                with col_fixed:
                    fixed_registration_btn = st.button("マッピング確定情報更新", type="secondary", key="fixed_registration_only")
                with col_message:
                    # 固定登録メッセージ表示用のプレースホルダー
                    message_placeholder = st.empty()
                    # スピナー表示用のプレースホルダー
                    spinner_placeholder = st.empty()
                    # セッション状態からメッセージを表示
                    if 'fixed_update_message' in st.session_state:
                        msg_type, msg_text = st.session_state.fixed_update_message
                        if msg_type == "success":
                            message_placeholder.success(msg_text)
                        else:
                            message_placeholder.info(msg_text)
                        # メッセージ表示後に削除
                        del st.session_state.fixed_update_message
                select_all_btn = False
                deselect_all_btn = False
            
            # ボタン操作をバッチ処理でst.rerun()を最小化
            needs_rerun = False
            if select_all_btn:
                apply_select_all_to_grid(mapping_data)
                needs_rerun = True
            
            if deselect_all_btn:
                apply_deselect_all_to_grid(mapping_data)
                needs_rerun = True
                
            if needs_rerun:
                # 全選択/全解除時もキャッシュカウンターをインクリメント
                st.session_state.data_cache_counter += 1
                st.rerun()
            
            # データキャッシュでパフォーマンス改善（カウンターベース）
            # 固定登録ボタンが押された場合は必ずキャッシュを無効化
            cache_valid = (st.session_state.cached_counter == st.session_state.data_cache_counter and 
                          st.session_state.cached_counter >= 0 and
                          st.session_state.cached_display_data is not None)
            
            use_cache = cache_valid and not fixed_registration_btn
            
            if use_cache:
                display_data = st.session_state.cached_display_data
            else:
                # 新しいデータを取得
                display_data = prepare_display_data(mapping_data)
                # 固定登録処理時以外はキャッシュを更新
                if not fixed_registration_btn:
                    st.session_state.cached_display_data = display_data
                    st.session_state.cached_counter = st.session_state.data_cache_counter
                
            edited_data = render_main_grid(display_data)
            
            if fixed_registration_btn and edited_data is not None:
                with spinner_placeholder:
                    with st.spinner("マッピング確定情報更新処理中..."):
                        # 固定登録処理実行
                        process_fixed_registration(edited_data, mapping_data, message_placeholder)
                        
                        # キャッシュを無効化
                        st.session_state.data_cache_counter += 1
                        st.session_state.cached_display_data = None
                        st.session_state.cached_counter = -1
                
                # 処理完了後にrerun
                st.rerun()
        else:
            st.info("マッピングデータがありません。「自動マッピング」を実行してください。")

def prepare_display_data(mapping_data: pd.DataFrame) -> pd.DataFrame:
    """グリッド表示用のデータを準備（セッション状態の固定状態を反映）"""
    
    display_data = mapping_data.copy()
    
    # rBOM発注番号+行番号の連結列を作成（ベクトル化で高速化）
    if 'rbom_order_no' in display_data.columns and 'rbom_line_no' in display_data.columns:
        mask = display_data['rbom_order_no'].notna() & display_data['rbom_line_no'].notna()
        display_data['rbom_order_line'] = None
        if mask.any():
            display_data.loc[mask, 'rbom_order_line'] = (
                display_data.loc[mask, 'rbom_order_no'].astype(str).str.zfill(9) + '+' +
                display_data.loc[mask, 'rbom_line_no'].astype(str).str.zfill(3)
            )
    
    
    # セッション状態が存在し、かつ空でない場合のみセッション状態を優先
    # そうでなければデータベースの状態をそのまま使用（固定登録後の状態反映）
    if ('grid_fixed_states' in st.session_state and 
        st.session_state.grid_fixed_states and 
        len(st.session_state.grid_fixed_states) > 0):
        
        # ベクトル化で高速化：キーを一括生成
        ej_mask = display_data['ej_order_no'].notna()
        rbom_mask = display_data['rbom_order_no'].notna() & display_data['rbom_line_no'].notna()
        
        # MATCHEDデータ用キー
        matched_keys = (
            display_data.loc[ej_mask & rbom_mask, 'ej_order_no'].astype(str) + '-' +
            display_data.loc[ej_mask & rbom_mask, 'rbom_order_no'].astype(str) + '-' +
            display_data.loc[ej_mask & rbom_mask, 'rbom_line_no'].astype(int).astype(str)
        )
        
        # EJ_ONLYデータ用キー
        ej_only_keys = display_data.loc[ej_mask & ~rbom_mask, 'ej_order_no'].astype(str) + '-NULL-NULL'
        
        # セッション状態を一括更新
        for idx, key in matched_keys.items():
            if key in st.session_state.grid_fixed_states:
                display_data.loc[idx, 'is_fixed'] = st.session_state.grid_fixed_states[key]
        
        for idx, key in ej_only_keys.items():
            if key in st.session_state.grid_fixed_states:
                display_data.loc[idx, 'is_fixed'] = st.session_state.grid_fixed_states[key]
        
    
    return display_data

def apply_select_or_deselect_to_grid(mapping_data: pd.DataFrame, select: bool):
    """グリッドの全ての手動以外のマッピング行を選択または非選択状態にする"""
    # EJ_ONLYデータとMATCHEDデータの両方に対応するフィルター条件
    target_mask = (
        (mapping_data['mapping_type'] != '手動') &
        (mapping_data['ej_order_no'].notna())
        # rbom_order_no/rbom_line_noの条件を削除（EJ_ONLYデータではNULLのため）
    )
    
    # マスク適用後の件数
    matched_data = mapping_data[target_mask]
    
    # セッション状態の初期化
    if 'grid_fixed_states' not in st.session_state:
        st.session_state.grid_fixed_states = {}
    
    for _, row in matched_data.iterrows():
        # EJ_ONLYとMATCHEDデータの両方に対応するキー生成
        if pd.notna(row['rbom_order_no']) and pd.notna(row['rbom_line_no']):
            # MATCHEDデータの場合: 従来通りのキー
            key = f"{row['ej_order_no']}-{row['rbom_order_no']}-{int(row['rbom_line_no'])}"
        else:
            # EJ_ONLYデータの場合: EJ発注番号のみのキー
            key = f"{row['ej_order_no']}-NULL-NULL"
        
        st.session_state.grid_fixed_states[key] = select

def apply_select_all_to_grid(mapping_data: pd.DataFrame):
    """全選択を適用"""
    apply_select_or_deselect_to_grid(mapping_data, True)

def apply_deselect_all_to_grid(mapping_data: pd.DataFrame):
    """全解除を適用"""
    apply_select_or_deselect_to_grid(mapping_data, False)

def is_all_selected(mapping_data: pd.DataFrame) -> bool:
    """すべての手動以外のマッピング行が選択されているかチェック"""
    target_mask = (
        (mapping_data['mapping_type'] != '手動') &
        (mapping_data['ej_order_no'].notna())
    )
    
    if not target_mask.any():
        return False
    
    target_data = mapping_data[target_mask]
    
    # セッション状態が存在しない場合は未選択
    if 'grid_fixed_states' not in st.session_state or not st.session_state.grid_fixed_states:
        return False
    
    # すべての対象行がセッション状態でTrueになっているかチェック
    for _, row in target_data.iterrows():
        if pd.notna(row['rbom_order_no']) and pd.notna(row['rbom_line_no']):
            key = f"{row['ej_order_no']}-{row['rbom_order_no']}-{int(row['rbom_line_no'])}"
        else:
            key = f"{row['ej_order_no']}-NULL-NULL"
        
        # セッション状態にないか、Falseの場合は未選択
        if key not in st.session_state.grid_fixed_states or not st.session_state.grid_fixed_states[key]:
            return False
    
    return True

def process_fixed_registration(edited_data: pd.DataFrame, original_data: pd.DataFrame, message_placeholder):
    """固定登録処理を実行（一括更新で安定化）"""
    try:
        # 1. 編集されたグリッドのデータを準備
        reverse_column_mapping = {
            'EJ発注番号': 'ej_order_no', 'EJ連番': 'ej_m_sequence', 'EJ品目コード': 'ej_item_code', 'EJ品目名': 'ej_item_name',
            'EJ数': 'ej_quantity', 'EJ納期': 'ej_delivery_date', 'rBOM発注番号+行番号': 'rbom_order_line',
            'rBOM連番': 'rbom_m_sequence', 'rBOM品目コード': 'rbom_item_code', 'rBOM品目名': 'rbom_item_name', 'rBOM数': 'rbom_quantity',
            'rBOM納期': 'rbom_delivery_date', '状態': 'status', '種別': 'mapping_type', 'マッピング確定': 'is_fixed'
        }
        # 2. マージキーを定義
        merge_keys = ['ej_order_no', 'rbom_order_no', 'rbom_line_no']
        
        edited_df = edited_data.rename(columns=reverse_column_mapping)
        
        # rbom_order_line列がNULLの場合、original_dataから補完
        if 'rbom_order_line' in edited_df.columns and original_data is not None:
            # 元データに対応するインデックスでrbom_order_no, rbom_line_noを直接コピー
            if len(edited_df) == len(original_data):
                # 元データをコピーしてNoneに変換
                rbom_order_values = original_data['rbom_order_no'].values
                rbom_line_values = original_data['rbom_line_no'].values
                
                # 'None'文字列やpandas.NAをNoneに変換
                edited_df['rbom_order_no'] = [None if pd.isna(v) or str(v) == 'None' else v for v in rbom_order_values]
                edited_df['rbom_line_no'] = [None if pd.isna(v) else v for v in rbom_line_values]
                
        
        edited_df = _ensure_and_prepare_data(edited_df)
        
        # 根本的解決: すべてのpandas.NAをNoneに変換（ベクトル化で高速化）
        for col in edited_df.columns:
            if edited_df[col].isna().any():
                edited_df[col] = edited_df[col].where(edited_df[col].notna(), None)
        
        for col in original_data.columns:
            if original_data[col].isna().any():
                original_data[col] = original_data[col].where(original_data[col].notna(), None)
        
        
        # 3. 元データと編集後データで変更を比較
        # マージキーが存在するかチェック
        missing_keys_in_original = [key for key in merge_keys if key not in original_data.columns]
        missing_keys_in_edited = [key for key in merge_keys if key not in edited_df.columns]
        
        if missing_keys_in_original:
            st.error(f"original_dataに不足しているキー: {missing_keys_in_original}")
            return
        if missing_keys_in_edited:
            st.error(f"edited_dfに不足しているキー: {missing_keys_in_edited}")
            return
        
        comparison_df = pd.merge(
            original_data[merge_keys + ['is_fixed', 'mapping_type']],
            edited_df[merge_keys + ['is_fixed']],
            on=merge_keys,
            suffixes=('_orig', '_edited'),
            how='left' # 元データを基準に結合
        )
        
        # 変更があった行をフィルタリング (元の状態と編集後の状態が異なる)
        changed_rows = comparison_df[comparison_df['is_fixed_orig'] != comparison_df['is_fixed_edited']].copy()
        
        # 手動マッピングは固定変更不可のため除外
        changed_rows = changed_rows[changed_rows['mapping_type'] != '手動']

        if changed_rows.empty:
            st.info("マッピング確定状態の変更はありませんでした。")
            return

        # 4. 変更内容をDBに反映
        # 変更があった行の完全な情報を取得
        final_changes = pd.merge(original_data, changed_rows, on=merge_keys, how='inner')
        
        # 根本的解決: final_changesでもpandas.NAを除去（ベクトル化で高速化）
        for col in final_changes.columns:
            if final_changes[col].isna().any():
                final_changes[col] = final_changes[col].where(final_changes[col].notna(), None)

        added_count = 0
        removed_count = 0

        # pandas.NAをNoneに変換する関数を定義（シンプル化）
        def convert_na_to_none(value):
            return None if pd.isna(value) else value

        # 一括更新用のデータを準備
        bulk_updates = []
        
        for i, (_, row) in enumerate(final_changes.iterrows()):
            new_state = convert_na_to_none(row['is_fixed_edited'])
            
            # new_stateがNoneの場合はFalseとして扱う
            if new_state is None:
                new_state = False

            ej_order = convert_na_to_none(row.get('ej_order_no'))
            rbom_order = convert_na_to_none(row.get('rbom_order_no'))
            rbom_line = convert_na_to_none(row.get('rbom_line_no'))
            
            # マッピングデータを準備
            mapping_data = {key: convert_na_to_none(value) for key, value in row.to_dict().items()}
            
            bulk_updates.append((ej_order, rbom_order, rbom_line, new_state, mapping_data))
            
            if new_state:
                added_count += 1
            else:
                removed_count += 1

        # 一括更新を実行
        st.session_state.db_manager.bulk_update_fixed_and_save_mappings(bulk_updates)
        
        # データ更新後、即座にキャッシュを無効化
        st.session_state.data_cache_counter += 1
        st.session_state.cached_display_data = None  # 追加の安全策

        # 5. 結果を即座に表示し、セッション状態にも保存
        if added_count > 0 or removed_count > 0:
            # 詳細なメッセージを作成
            messages = []
            if added_count > 0:
                messages.append(f"登録: {added_count}件")
            if removed_count > 0:
                messages.append(f"削除: {removed_count}件")
            
            # 成功メッセージを即座に表示
            success_msg = f"マッピング確定更新完了 - {' / '.join(messages)}"
            message_placeholder.success(success_msg)
            # セッション状態にも保存（rerun後用）
            st.session_state.fixed_update_message = ("success", success_msg)
            st.session_state.grid_fixed_states = {} # 選択状態をリセット
        else:
            # 変更なしメッセージを即座に表示
            info_msg = "マッピング確定状態の変更はありませんでした。"
            message_placeholder.info(info_msg)
            # セッション状態にも保存（rerun後用）
            st.session_state.fixed_update_message = ("info", info_msg)

    except Exception as e:
        st.error(f"マッピング確定情報更新処理でエラーが発生しました: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

if __name__ == "__main__":
    main()