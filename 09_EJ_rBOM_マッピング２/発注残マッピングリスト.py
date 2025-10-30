"""
EJ-rBOM マッピングツール メインアプリケーション
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.db_manager import DatabaseManager
from data_sources.ej_connector import EJConnector
from data_sources.rbom_connector import RBOMConnector
from data_sources.mk020_connector import MK020Connector
from mapping.mapper import MappingEngine
from ui.components import render_main_grid
import os
import logging
from pathlib import Path
import zipfile
import shutil

# デバッグログ設定
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"debug_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def backup_database():
    """
    データベースをバックアップする

    Returns:
        bool: バックアップが成功した場合True、失敗した場合False
    """
    try:
        # データベースファイルのパス
        db_path = Path("./database/mapping.db")

        # データベースファイルが存在しない場合はバックアップ不要
        if not db_path.exists():
            logger.info("データベースファイルが存在しないため、バックアップをスキップします。")
            return True

        # バックアップディレクトリの作成
        backup_dir = Path("./database/DB_backup")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # タイムスタンプ付きのファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"{timestamp}_mapping.db.zip"
        backup_path = backup_dir / backup_filename

        # zipファイルに圧縮
        logger.info(f"データベースバックアップ開始: {backup_filename}")
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(db_path, arcname="mapping.db")

        logger.info(f"データベースバックアップ完了: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"データベースバックアップ中にエラーが発生しました: {str(e)}", exc_info=True)
        return False

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

    # 固定の日付範囲
    start_date = date(2025, 7, 1)
    end_date = date(2027, 1, 31)

    # 納期許容日数の入力と自動マッピングボタン
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.5])

    with col1:
        ej_after_rbom_days = st.number_input(
            "EJ≧rBOM納期許容日数",
            min_value=0,
            max_value=730,
            value=None,
            step=1,
            help="EJ納期がrBOM納期よりこの日数以内に遅い場合にマッピング対象とします（空欄=制限なし）"
        )

    with col2:
        ej_before_rbom_days = st.number_input(
            "EJ≦rBOM納期許容日数",
            min_value=0,
            max_value=730,
            value=None,
            step=1,
            help="EJ納期がrBOM納期よりこの日数以内に早い場合にマッピング対象とします（空欄=制限なし）"
        )

    with col3:
        st.write("")  # スペース調整
        enable_quantity_diff = st.checkbox(
            "差引処理",
            value=True,
            help="チェックすると、EJ数とrBOM数の差分を連番を増やして追加します"
        )

    with col4:
        st.write("")  # スペース調整
        auto_mapping_btn = st.button("自動マッピング", type="primary")

    with col5:
        # 前回実行時刻を2段表示
        if 'last_mapping_time' in st.session_state:
            last_time = st.session_state.last_mapping_time
            st.caption("前回実行:")
            st.caption(last_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            st.caption("前回実行:")
            st.caption("なし")
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.db_manager.initialize_database()

        # 最終実行時刻を取得（データベースまたはバックアップから）
        last_time = st.session_state.db_manager.get_last_execution_time()
        if last_time:
            st.session_state.last_mapping_time = last_time
            logger.info(f"前回実行時刻を復元: {last_time}")
    
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
            logger.info("=" * 80)
            logger.info("自動マッピング処理開始")
            logger.info(f"納期範囲: {start_date} 〜 {end_date}")
            print(f"[DEBUG] 確認完了 - 実際の処理を開始")

            # データベースバックアップ（処理開始前）
            logger.info("【ステップ0】データベースバックアップ開始")
            backup_start_time = datetime.now()
            backup_success = backup_database()
            backup_elapsed = (datetime.now() - backup_start_time).total_seconds()

            if not backup_success:
                st.warning("データベースのバックアップに失敗しましたが、処理を続行します。")
                logger.warning(f"データベースバックアップ失敗 ({backup_elapsed:.2f}秒)")
            else:
                logger.info(f"データベースバックアップ完了 ({backup_elapsed:.2f}秒)")

            # 確認後の実際の処理
            with st.spinner("データを取得中..."):
                try:
                    # 1. EJデータ取得
                    logger.info("【ステップ1】EJデータ取得開始")
                    start_time = datetime.now()
                    ej_connector = EJConnector()
                    ej_data = ej_connector.get_order_backlog(start_date, end_date)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"EJデータ取得完了: {len(ej_data)}件 ({elapsed:.2f}秒)")

                    # 2. rBOMデータ取得
                    logger.info("【ステップ2】rBOMデータ取得開始")
                    start_time = datetime.now()
                    rbom_connector = RBOMConnector()
                    rbom_data = rbom_connector.get_orders_by_date_range(start_date, end_date)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"rBOMデータ取得完了: {len(rbom_data)}件 ({elapsed:.2f}秒)")

                    # 3. 手動マッピング取得
                    logger.info("【ステップ3】手動マッピング取得開始")
                    start_time = datetime.now()
                    manual_mappings_df = st.session_state.db_manager.get_manual_mappings()
                    manual_mappings = manual_mappings_df.to_dict('records') if not manual_mappings_df.empty else []
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"手動マッピング取得完了: {len(manual_mappings)}件 ({elapsed:.2f}秒)")

                    # 4. 固定マッピング取得
                    logger.info("【ステップ4】固定マッピング取得開始")
                    start_time = datetime.now()
                    fixed_mappings_df = st.session_state.db_manager.get_fixed_mappings()
                    fixed_mappings = fixed_mappings_df.to_dict('records') if not fixed_mappings_df.empty else []
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"固定マッピング取得完了: {len(fixed_mappings)}件 ({elapsed:.2f}秒)")

                    # 5. MK020マスタ取得
                    logger.info("【ステップ5】MK020マスタ取得開始")
                    start_time = datetime.now()
                    mk020_connector = MK020Connector()
                    mk020_data = mk020_connector.get_mk020_data()
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"MK020マスタ取得完了: {len(mk020_data)}件 ({elapsed:.2f}秒)")

                    # 6. マッピング実行
                    logger.info("【ステップ6】マッピング実行開始")
                    start_time = datetime.now()
                    mapper = MappingEngine()
                    mapping_result = mapper.execute_mapping(
                        ej_data,
                        rbom_data,
                        manual_mappings=manual_mappings,
                        fixed_mappings=fixed_mappings,
                        ej_after_rbom_days=ej_after_rbom_days,
                        ej_before_rbom_days=ej_before_rbom_days,
                        enable_quantity_diff=enable_quantity_diff,
                        mk020_data=mk020_data
                    )
                    # マッピング結果と統計情報を展開
                    mapping_results = mapping_result['mapping_results']
                    manual_mapping_success_count = mapping_result['manual_mapping_success_count']
                    manual_mapping_failed_count = mapping_result['manual_mapping_failed_count']
                    manual_mapping_failed_details = mapping_result['manual_mapping_failed_details']
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"マッピング実行完了: {len(mapping_results)}件 ({elapsed:.2f}秒)")

                    # 統計情報を収集
                    ej_after_count = len([r for r in mapping_results if r.get('ej_order_no') is not None])
                    rbom_after_count = len([r for r in mapping_results if r.get('rbom_order_no') is not None])

                    # 抽出条件テキストを作成
                    ej_cond_text = (
                        f"- テーブル: T_RLSD_PUCH_ODR, M_ITEM\n"
                        f"- 納期: {start_date} 〜 {end_date}\n"
                        f"- ステータス: PUCH_ODR_STS_TYP = 2\n"
                        f"- 発注種別: PUCH_ODR_TYP ≠ 4"
                    )
                    rbom_cond_text = (
                        f"- テーブル: D3340, D3010, D3360, DK020\n"
                        f"- 納期: {start_date} 〜 {end_date}"
                    )
                    if ej_after_rbom_days is not None or ej_before_rbom_days is not None:
                        ej_cond_text += f"\n- 納期許容条件: EJ≧rBOM {ej_after_rbom_days if ej_after_rbom_days is not None else '制限なし'}日, EJ≦rBOM {ej_before_rbom_days if ej_before_rbom_days is not None else '制限なし'}日"

                    # 統計情報をセッションに保存
                    st.session_state.mapping_stats = {
                        'ej_source_count': len(ej_data),
                        'rbom_source_count': len(rbom_data),
                        'ej_after_diff_count': ej_after_count,
                        'rbom_after_diff_count': rbom_after_count,
                        'ej_conditions': ej_cond_text,
                        'rbom_conditions': rbom_cond_text,
                        'manual_mapping_success_count': manual_mapping_success_count,
                        'manual_mapping_failed_count': manual_mapping_failed_count,
                        'manual_mapping_registered_count': len(manual_mappings),
                        'manual_mapping_failed_details': manual_mapping_failed_details
                    }

                    # 6. 結果保存
                    logger.info("【ステップ6】結果保存開始")
                    start_time = datetime.now()
                    st.session_state.db_manager.save_mapping_results(mapping_results)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"結果保存完了 ({elapsed:.2f}秒)")

                    # 前回実行時刻を記録（セッションとデータベースの両方）
                    execution_time = datetime.now()
                    st.session_state.last_mapping_time = execution_time
                    st.session_state.db_manager.save_last_execution_time(execution_time)
                    logger.info(f"前回実行時刻を記録: {execution_time}")

                    logger.info("自動マッピング処理完了")
                    logger.info("=" * 80)
                    st.success("自動マッピングが完了しました。")
                    print(f"[DEBUG] 処理完了 - 確認状態を削除")
                    # 確認状態を削除（次回は再度確認ダイアログを表示）
                    if 'auto_mapping_confirmed' in st.session_state:
                        del st.session_state.auto_mapping_confirmed
                    st.rerun()

                except Exception as e:
                    logger.error(f"エラー発生: {str(e)}", exc_info=True)
                    st.error(f"エラーが発生しました: {str(e)}")
                    print(f"[DEBUG] エラー発生 - 確認状態を削除: {str(e)}")
                    # エラー時も確認状態を削除
                    if 'auto_mapping_confirmed' in st.session_state:
                        del st.session_state.auto_mapping_confirmed
    
    if 'db_manager' in st.session_state and st.session_state.db_manager:
        mapping_data_raw = st.session_state.db_manager.get_mapping_results()

        if not mapping_data_raw.empty:
            mapping_data = _ensure_and_prepare_data(mapping_data_raw)

            # データ表示のみ（編集機能なし）
            display_data = prepare_display_data(mapping_data)

            # 統計情報を取得（存在する場合）
            stats = st.session_state.get('mapping_stats', None)

            render_main_grid(display_data, stats=stats)
        else:
            st.info("マッピングデータがありません。「自動マッピング」を実行してください。")

def prepare_display_data(mapping_data: pd.DataFrame) -> pd.DataFrame:
    """グリッド表示用のデータを準備（セッション状態の固定状態を反映）"""
    logger.debug(f"prepare_display_data開始: {len(mapping_data)}件")
    start_time = datetime.now()

    display_data = mapping_data.copy()

    # データ型をデバッグ出力（根本原因調査）
    numeric_fields = ['ej_status', 'ej_purch_odr_typ', 'rbom_line_no']
    for field in numeric_fields:
        if field in display_data.columns:
            sample_values = display_data[field].head(5)
            logger.info(f"【データ型調査】{field}:")
            for idx, val in sample_values.items():
                logger.info(f"  行{idx}: 値={repr(val)}, 型={type(val).__name__}, isna={pd.isna(val)}")

    # 数値フィールドを文字列に変換（文字化け対策）
    # データベースから取得した値をそのまま文字列化（バイナリデータ対策）
    for field in numeric_fields:
        if field in display_data.columns:
            def safe_to_string(value):
                """安全に文字列変換する関数"""
                if pd.isna(value) or value is None:
                    return None

                # 数値型の場合
                if isinstance(value, (int, float)):
                    if pd.isna(value):  # NaNチェック
                        return None
                    return str(int(value))

                # バイト列の場合
                if isinstance(value, bytes):
                    try:
                        # バイト列をデコードせずに、直接整数として解釈
                        # SQLiteから取得したバイナリ整数データの可能性
                        decoded = value.decode('latin-1')  # latin-1で1バイト=1文字として扱う
                        # 最初の文字のord値を取得（整数値）
                        if len(decoded) > 0:
                            return str(ord(decoded[0]))
                    except Exception:
                        pass
                    return None

                # 文字列の場合
                if isinstance(value, str):
                    # すでに数値文字列の場合
                    if value.isdigit():
                        return value
                    # 数値変換を試みる
                    try:
                        return str(int(float(value)))
                    except (ValueError, TypeError):
                        pass
                    return None

                # その他の型は文字列化を試みる
                try:
                    return str(int(value))
                except (ValueError, TypeError):
                    return None

            display_data[field] = display_data[field].apply(safe_to_string)

    # 品目コード順にソート（昇順）
    if 'item_code' in display_data.columns:
        sort_start = datetime.now()
        display_data = display_data.sort_values('item_code', ascending=True, na_position='last')
        logger.debug(f"  品目コードソート完了 ({(datetime.now() - sort_start).total_seconds():.3f}秒)")

    # rBOM発注番号+行番号の連結列を作成（ベクトル化で高速化、エンコーディングエラー対策）
    if 'rbom_order_no' in display_data.columns and 'rbom_line_no' in display_data.columns:
        def create_order_line(row):
            """発注番号+行番号を作成"""
            try:
                order_no = row['rbom_order_no']
                line_no = row['rbom_line_no']

                # 両方がNoneでない場合のみ処理
                if pd.notna(order_no) and pd.notna(line_no) and line_no is not None:
                    # order_noを数値化（9桁ゼロ埋め）
                    if isinstance(order_no, (int, float)):
                        order_str = str(int(order_no)).zfill(9)
                    elif isinstance(order_no, str):
                        if order_no.isdigit():
                            order_str = order_no.zfill(9)
                        else:
                            order_str = str(int(float(order_no))).zfill(9)
                    else:
                        return None

                    # line_noを数値化（3桁ゼロ埋め）
                    # line_noは既にsafe_to_stringで文字列化済みなので、そのまま使用
                    if isinstance(line_no, str):
                        if line_no.isdigit():
                            line_str = line_no.zfill(3)
                        else:
                            line_str = str(int(float(line_no))).zfill(3)
                    elif isinstance(line_no, (int, float)):
                        line_str = str(int(line_no)).zfill(3)
                    else:
                        return None

                    return f"{order_str}+{line_str}"
            except Exception as e:
                # エラーログは出さない（大量になるため）
                pass

            return None

        display_data['rbom_order_line'] = display_data.apply(create_order_line, axis=1)
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.debug(f"prepare_display_data完了 ({elapsed:.2f}秒)")
    return display_data

if __name__ == "__main__":
    main()