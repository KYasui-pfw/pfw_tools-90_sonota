"""
machine_data_extract.py

PostgreSQL (irepodb) の view_report_405 からデータを取得し、
FastAPI completion エンドポイントに送信する統合処理

処理フロー:
1. PostgreSQL から DataFrame 取得（107列）
2. (デバッグ用: CSV出力 - ENABLE_CSV_OUTPUT=true の場合のみ)
3. top_remarks3 で当月・翌月・翌々月のデータをフィルタリング
4. パターン分岐:
   - パターン1: cluster_1_24_n～cluster_1_636_n のいずれかが 1.0 の行を抽出 → LINENO=1のみ送信
   - パターン3: cluster_1_641_t が '2' または '4' の行を抽出 → 全LINENO送信
5. FastAPI 経由で指示データを取得（パターン1はバッチ、パターン3は月次取得）
6. 状態チェックして送信可能なデータのみ completion エンドポイントに送信

実行: python machine_data_extract.py
"""
import os
import sys
import httpx
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd

# 環境変数読み込み
load_dotenv()

# 設定値取得
DB_URL = os.getenv('DB_URL', 'postgresql://postgres:cimtops@ESRV10/irepodb')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
LOG_DIR = os.getenv('LOG_DIR', './logs')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '7'))
FASTAPI_BASE_URL = os.getenv('FASTAPI_BASE_URL', 'http://127.0.0.1:8000')
READ_API_KEY = os.getenv('READ_API_KEY', '')
INSERT_API_KEY = os.getenv('INSERT_API_KEY', '')
ENABLE_CSV_OUTPUT = os.getenv('ENABLE_CSV_OUTPUT', 'false').lower() == 'true'
LOT_MAPPING_DB_PATH = os.getenv('LOT_MAPPING_DB_PATH', './db/lot_mapping.db')

# ディレクトリ作成
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=9))

# ========== 特定5部品の実績返却先リダイレクト ==========
# 現品票発行（90_tools/50_tools/genpin_check/1_現品票発行.py の時限処理 20260115追加）が
# この5部品だけ「払出先40を除外・60を通過」させているため、40側の伝票には現品票が出ず、
# i-Reporter のチェックシートは払出先60の伝票にしか作られない。
# その結果、実績は60側にしか返らず40側の指示がSTATUS='1'のまま残り続ける。
#
# そこで5部品に限り、i-Reporter が持つINDNO（＝60側）ではなく、
# 「同一SEINO・同一OYALISTNO で 払出先(D3410.SRCD)=40」のINDNOへ実績を返す。
# OYALISTNO は D3420.LISTNO を D3110 で引いた親LISTNOで、/instructions/ の応答に含まれる。
# ※60側へは送信しない（差し替え）。LINENOの範囲は現行どおり
#   （パターン1=LINENO=1のみ / パターン3=リダイレクト先の全LINENO）。
SPECIAL_PART_NAMES = frozenset({
    'SINKER REST RING',
    'NEEDLE DIAL',
    'NEEDLE CYLINDER',
    'SINKER DIAL',
    'WRAP DIAL',
})
SPECIAL_PART_TARGET_SRCD = '40'

# ========== SEINO+HMCD による返却先INDNOの解決 ==========
# INDNO は作業開始後に再発行されることがある（旧INDNOは rBOM 側で消える／完了扱いになる）ため、
# i-Reporter が持つINDNOではなく「同一SEINO・同一HMCD で 払出先(SRCD)=40」の現行INDNOへ実績を返す。
# .env の PATTERN3_<ID>_MODE=seino_hmcd で有効化（現状は405＝マシニング課のみ）。
#   - 旧INDNOが月次指示データにある → rBOM側のSEINO・HMCDを使う（SEINOは完全一致）
#   - 無い（rBOM側で消えた）        → i-Reporter 側の SEINO末尾(SEINO_COLUMN)・HMCD(HMCD_COLUMN) を使う
#                                     （SEINOは短縮されているため末尾一致）
# 解決した全INDNOの全LINENOへ送る。SEINO先頭2桁が数字なら年（26=2026年）とみなし、前年以前は送らない。
RESOLVE_MODE_SEINO_HMCD = 'seino_hmcd'
SEINO_HMCD_TARGET_SRCD = '40'


def load_pattern3_configs():
    """
    .envファイルからパターン3のテーブル設定を読み込む

    Returns:
        list: [{"table": "view_report_405", "source_table": "view_report_405", "indno_col": "...", "judge_col": "...", "date_col": "...", "iptancd": "..."}, ...]
    """
    configs = []

    # PATTERN3_TABLES から対象テーブルリストを取得
    tables_str = os.getenv('PATTERN3_TABLES', '')
    if not tables_str:
        return configs

    tables = [t.strip() for t in tables_str.split(',') if t.strip()]

    for table in tables:
        # テーブル名から数字部分を抽出（例: view_report_405 → 405）
        table_id = table.replace('view_report_', '')

        # 各テーブルの設定を取得
        source_table = os.getenv(f'PATTERN3_{table_id}_SOURCE_TABLE', '')
        indno_col = os.getenv(f'PATTERN3_{table_id}_INDNO_COLUMN', '')
        seino_col = os.getenv(f'PATTERN3_{table_id}_SEINO_COLUMN', '')
        ktcd_col = os.getenv(f'PATTERN3_{table_id}_KTCD_COLUMN', '')
        judge_col = os.getenv(f'PATTERN3_{table_id}_JUDGE_COLUMN', '')
        date_col = os.getenv(f'PATTERN3_{table_id}_DATE_COLUMN', '')
        iptancd = os.getenv(f'PATTERN3_{table_id}_IPTANCD', '')
        # 334専用: SEINO+HMNMマッチングモード / seino_hmcd: SEINO+HMCDで返却先INDNOを解決（405）
        mode = os.getenv(f'PATTERN3_{table_id}_MODE', '')
        hmnm_filter = os.getenv(f'PATTERN3_{table_id}_HMNM_FILTER', '')
        hmcd_col = os.getenv(f'PATTERN3_{table_id}_HMCD_COLUMN', '')

        # 必須項目チェック: source_table, judge_col, date_col, iptancd は必須
        # indno_col は "FROM_API" の場合、seino_col と ktcd_col も必須
        if not (source_table and judge_col and date_col and iptancd):
            logger.warning(f"パターン3設定不完全: {table} (source_table={source_table}, judge_col={judge_col}, date_col={date_col}, iptancd={iptancd})")
            continue

        # INDNO_COLUMN のチェック
        if not indno_col:
            logger.warning(f"パターン3設定不完全: {table} (indno_col が設定されていません)")
            continue

        # FROM_API の場合は SEINO_COLUMN と KTCD_COLUMN が必須
        if indno_col == "FROM_API":
            if not (seino_col and ktcd_col):
                logger.warning(f"パターン3設定不完全: {table} (indno_col=FROM_API の場合、seino_col と ktcd_col が必須です)")
                continue

        # seino_hmcd モードは SEINO_COLUMN（末尾）と HMCD_COLUMN が必須
        if mode == RESOLVE_MODE_SEINO_HMCD:
            if not (seino_col and hmcd_col):
                logger.warning(f"パターン3設定不完全: {table} (mode={RESOLVE_MODE_SEINO_HMCD} の場合、seino_col と hmcd_col が必須です)")
                continue

        configs.append({
            'table': table,
            'source_table': source_table,
            'indno_col': indno_col,
            'seino_col': seino_col,
            'ktcd_col': ktcd_col,
            'judge_col': judge_col,
            'date_col': date_col,
            'iptancd': iptancd,
            'mode': mode,
            'hmnm_filter': hmnm_filter,
            'hmcd_col': hmcd_col
        })

    return configs


def get_indno_numeric_value(indno):
    """
    INDNOの数値部分を抽出（先頭1文字を除く）

    Args:
        indno: INDNO文字列（例: 'H00001111'）

    Returns:
        int: 数値部分。変換失敗時はfloat('inf')
    """
    try:
        if indno and len(indno) > 1:
            return int(indno[1:])
        return float('inf')
    except (ValueError, TypeError):
        return float('inf')


def load_indno_mapping():
    """
    lot_mapping.db の mapping_results テーブルからINDNOマッピング辞書を作成

    同一lot_numberに複数のindnoが存在する場合、
    indnoの数値部分（先頭1文字を除く）が最小のものを優先する。
    例: H00001, H00002, H00003 → H00001を採用

    Returns:
        dict: {lot_number: indno} の辞書。読み込み失敗時は空辞書
    """
    mapping = {}

    if not os.path.exists(LOT_MAPPING_DB_PATH):
        logger.warning(f"INDNOマッピングDBが見つかりません: {LOT_MAPPING_DB_PATH}")
        return mapping

    try:
        import sqlite3
        conn = sqlite3.connect(LOT_MAPPING_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT lot_number, indno FROM mapping_results")
        rows = cursor.fetchall()

        for lot_number, indno in rows:
            if lot_number and indno:
                if lot_number not in mapping:
                    # 初回登録
                    mapping[lot_number] = indno
                else:
                    # 既存エントリと比較し、数値が小さい方を採用
                    existing_value = get_indno_numeric_value(mapping[lot_number])
                    new_value = get_indno_numeric_value(indno)
                    if new_value < existing_value:
                        mapping[lot_number] = indno

        conn.close()

    except Exception as e:
        logger.error(f"INDNOマッピング読み込みエラー: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return mapping


def setup_logger():
    """ロガー設定（日次ローテーション、7日保持）"""
    logger = logging.getLogger('machine_extract')
    logger.setLevel(logging.INFO)

    # 既存ハンドラーをクリア
    logger.handlers.clear()

    # ファイルハンドラー（日次ローテーション）
    log_filename = os.path.join(LOG_DIR, f"machine_extract_{datetime.now(JST).strftime('%Y%m%d')}.log")
    file_handler = TimedRotatingFileHandler(
        filename=log_filename,
        when='midnight',
        interval=1,
        backupCount=LOG_RETENTION_DAYS,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def cleanup_old_logs(log_dir, retention_days):
    """古いログファイルを削除"""
    try:
        current_time = datetime.now(JST)
        for filename in os.listdir(log_dir):
            if filename.startswith('machine_extract_') and filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path), tz=JST)
                age_days = (current_time - file_time).days

                if age_days > retention_days:
                    os.remove(file_path)
    except Exception as e:
        logger.warning(f"ログクリーンアップ中にエラー: {e}")


def generate_column_list():
    """取得対象の107列リストを生成"""
    columns = ['cluster_1_2_t']

    # cluster_1_24_n ～ cluster_1_636_n (12刻み)
    for i in range(24, 637, 12):
        columns.append(f'cluster_1_{i}_n')

    # cluster_1_14_t ～ cluster_1_626_t (12刻み+2)
    for i in range(14, 627, 12):
        columns.append(f'cluster_1_{i}_t')

    # cluster_1_641_t を追加
    columns.append('cluster_1_641_t')

    # top_remarks3 (実際のDBカラム名)
    columns.append('top_remarks3')

    return columns


def extract_data_from_postgres():
    """
    PostgreSQLからデータを取得

    Returns:
        pd.DataFrame or None: 取得したデータ、失敗時はNone
    """
    try:
        # カラムリスト生成
        columns = generate_column_list()

        # SQL文生成
        column_str = ', '.join(columns)
        sql = f"SELECT {column_str} FROM view_report_405"

        # PostgreSQL接続
        engine = create_engine(DB_URL, echo=False)

        # データ取得
        with engine.connect() as connection:
            df = pd.read_sql(sql, connection)

        # デバッグ用: CSV出力（ENABLE_CSV_OUTPUT=true の場合のみ）
        if ENABLE_CSV_OUTPUT:
            timestamp = datetime.now(JST).strftime('%Y%m%d_%H%M%S')
            output_filename = f"machine_data_{timestamp}.csv"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

        return df

    except Exception as e:
        logger.error(f"PostgreSQLデータ取得エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def fetch_data_from_table(table_name):
    """
    指定されたテーブルから全カラムを取得（パターン3用）

    Args:
        table_name (str): 取得対象のテーブル名（例: view_report_334）

    Returns:
        pd.DataFrame: 取得したデータ、エラー時はNone
    """
    try:
        # SQL文生成（全カラム取得）
        sql = f"SELECT * FROM {table_name}"

        # PostgreSQL接続
        engine = create_engine(DB_URL, echo=False)

        # データ取得
        with engine.connect() as connection:
            df = pd.read_sql(sql, connection)

        return df

    except Exception as e:
        logger.error(f"{table_name} からのデータ取得エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


async def fetch_indno_from_api(seino, ktcd, api_base_url, read_api_key):
    """
    SEINO と KTCD から INDNO を API 経由で取得

    Args:
        seino (str): 製番
        ktcd (str): 工程コード
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー

    Returns:
        str: 取得したINDNO、エラー時はNone
    """
    try:
        url = f"{api_base_url}/query"
        headers = {
            "X-API-Key": read_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "table": "D3420",
            "columns": ["INDNO", "LINENO"],
            "where": {
                "and": [
                    {"SEINO": seino},
                    {"KTCD": ktcd}
                ]
            },
            "limit": 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            # レスポンスから INDNO を取得
            rows = data.get('rows', [])
            if rows and len(rows) > 0:
                indno = rows[0].get('INDNO', '')
                if indno:
                    return str(indno).strip()

            return None

    except Exception as e:
        logger.error(f"API経由でのINDNO取得エラー (SEINO={seino}, KTCD={ktcd}): {e}")
        return None


def filter_by_top_remarks3(df):
    """
    top_remarks3 で当月・翌月・翌々月のデータをフィルタリング
    ※この関数は後方互換性のため残していますが、新しいコードでは filter_by_date_column() を使用してください

    Args:
        df (pd.DataFrame): CSVデータ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    return filter_by_date_column(df, 'top_remarks3', 'top_remarks3')


def filter_by_date_column(df, date_column, display_name=None):
    """
    指定されたカラムで当月・翌月・翌々月のデータをフィルタリング（汎用版）

    Args:
        df (pd.DataFrame): CSVデータ
        date_column (str): 日付カラム名（カンマ区切りで年・月を別々に指定可能: "year_col,month_col"）
        display_name (str): ログ表示用名称（省略時は date_column を使用）

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    if display_name is None:
        display_name = date_column

    try:
        # カンマで分割されているかチェック（年と月が別カラム）
        if ',' in date_column:
            columns = [col.strip() for col in date_column.split(',')]
            if len(columns) != 2:
                logger.error(f"DATE_COLUMNの形式が不正です: {date_column} (年カラム,月カラム の2つが必要)")
                return pd.DataFrame()

            year_column = columns[0]
            month_column = columns[1]

            # カラムが存在するかチェック
            if year_column not in df.columns:
                logger.error(f"年カラム '{year_column}' が存在しません")
                return pd.DataFrame()
            if month_column not in df.columns:
                logger.error(f"月カラム '{month_column}' が存在しません")
                return pd.DataFrame()

            # 現在の日本時間
            now = datetime.now(JST)
            current_year_month = now.strftime('%Y%m')

            # 翌月
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            next_month_str = next_month.strftime('%Y%m')

            # 翌々月
            next_next_month = (next_month.replace(day=1) + timedelta(days=32)).replace(day=1)
            next_next_month_str = next_next_month.strftime('%Y%m')

            target_months = [current_year_month, next_month_str, next_next_month_str]

            # 年と月を結合してYYYYMM形式にする（月は0埋め）
            temp_col_name = f'{year_column}_{month_column}_ym'
            df[temp_col_name] = df.apply(
                lambda row: f"{str(row[year_column]).strip()}{str(int(row[month_column])).zfill(2)}"
                if pd.notna(row[year_column]) and pd.notna(row[month_column]) and str(row[year_column]).strip().isdigit() and str(row[month_column]).strip().replace('.', '').isdigit()
                else '',
                axis=1
            )

            # 対象月のデータのみ抽出
            df_filtered = df[df[temp_col_name].isin(target_months)].copy()

        else:
            # 単一カラムの場合（既存ロジック）
            # カラムが存在するかチェック
            if date_column not in df.columns:
                logger.error(f"カラム '{date_column}' が存在しません")
                return pd.DataFrame()

            # 現在の日本時間
            now = datetime.now(JST)
            current_year_month = now.strftime('%Y%m')

            # 翌月
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            next_month_str = next_month.strftime('%Y%m')

            # 翌々月
            next_next_month = (next_month.replace(day=1) + timedelta(days=32)).replace(day=1)
            next_next_month_str = next_next_month.strftime('%Y%m')

            target_months = [current_year_month, next_month_str, next_next_month_str]

            # 日付カラムの先頭6文字を抽出（一時カラム名を動的に生成）
            temp_col_name = f'{date_column}_ym'
            df[temp_col_name] = df[date_column].astype(str).str[:6]

            # 対象月のデータのみ抽出
            df_filtered = df[df[temp_col_name].isin(target_months)].copy()

        return df_filtered

    except Exception as e:
        logger.error(f"{display_name}フィルタリングに失敗しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


def filter_by_cluster_flags(df):
    """
    cluster_1_24_n～cluster_1_636_n のいずれかが 1.0 の行を抽出

    Args:
        df (pd.DataFrame): CSVデータ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    try:
        # cluster_1_24_n～cluster_1_636_n のカラム名リスト生成（12刻み、52個）
        cluster_columns = [f'cluster_1_{i}_n' for i in range(24, 637, 12)]

        # 存在するカラムのみ対象
        existing_columns = [col for col in cluster_columns if col in df.columns]

        if not existing_columns:
            logger.warning("cluster_1_*_n カラムが見つかりません")
            return pd.DataFrame()

        # いずれかのカラムが 1.0 の行を抽出
        mask = df[existing_columns].eq(1.0).any(axis=1)
        df_filtered = df[mask]

        return df_filtered

    except Exception as e:
        logger.error(f"clusterフラグフィルタリングに失敗しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


def filter_by_cluster_641t(df):
    """
    cluster_1_641_t が '2' または '4' である行を抽出（パターン3用）
    ※この関数は後方互換性のため残していますが、新しいコードでは filter_by_judge_column() を使用してください

    Args:
        df (pd.DataFrame): 入力データ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    return filter_by_judge_column(df, 'cluster_1_641_t', 'cluster_1_641_t')


def filter_by_judge_column(df, judge_column, display_name=None):
    """
    指定されたカラムが '2' または '4' である行を抽出（汎用パターン3用）

    Args:
        df (pd.DataFrame): 入力データ
        judge_column (str): 判定用カラム名
        display_name (str): ログ表示用名称（省略時は judge_column を使用）

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    if display_name is None:
        display_name = judge_column

    try:
        # カラムが存在するかチェック
        if judge_column not in df.columns:
            logger.error(f"カラム '{judge_column}' が存在しません")
            return pd.DataFrame()

        # 判定カラムが 2 または 4 の行を抽出（浮動小数点数も考慮）
        # 文字列型と数値型の両方に対応
        def is_2_or_4(val):
            if pd.isna(val):
                return False
            # 数値型の場合
            try:
                num_val = float(val)
                return num_val == 2.0 or num_val == 4.0
            except (ValueError, TypeError):
                pass
            # 文字列型の場合
            str_val = str(val).strip()
            return str_val in ['2', '4', '2.0', '4.0']

        mask = df[judge_column].apply(is_2_or_4)
        df_filtered = df[mask].copy()

        return df_filtered

    except Exception as e:
        logger.error(f"{display_name}フィルタリングに失敗しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


def filter_out_202603_and_later(df, date_column='top_remarks3', display_name=None):
    """
    202603以降のデータを除外する時限処理

    ※この処理が不要になったら、呼び出し箇所をコメントアウトしてください

    Args:
        df (pd.DataFrame): 入力データ
        date_column (str): 日付カラム名（YYYYMMDD形式、先頭6桁をYYYYMMとして使用）
        display_name (str): ログ表示用名称（省略時は date_column を使用）

    Returns:
        pd.DataFrame: フィルタリング後のデータ（202602以前のみ）
    """
    if display_name is None:
        display_name = date_column

    try:
        # カラムが存在するかチェック
        if date_column not in df.columns:
            logger.warning(f"カラム '{date_column}' が存在しません。202603以降除外フィルタをスキップします。")
            return df

        # 日付カラムの先頭6文字を取得（YYYYMM）
        temp_col_name = f'{date_column}_yyyymm_temp'
        df[temp_col_name] = df[date_column].astype(str).str[:6]

        # 202602以前のデータのみ抽出（202603以降を除外）
        df_filtered = df[df[temp_col_name] <= '202602'].copy()

        # 一時カラムを削除
        df_filtered = df_filtered.drop(columns=[temp_col_name], errors='ignore')

        return df_filtered

    except Exception as e:
        logger.error(f"202603以降除外処理に失敗しました ({display_name}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


def is_sendable_status(instruction):
    """
    指示データの状態が送信可能かどうかを判定

    判定ルール:
    - 完了（EDKKBN='1'/'2', STATUS='3'/'4'/'8'）→ 送信不可
    - 中止（STATUS='9'）→ 送信不可
    - 実績登録中（SYORIZUMIKB='1'）→ 送信不可
    - 登録エラー（SYORIZUMIKB='3'）→ 送信可能
    - 未完了（その他）→ 送信可能

    Args:
        instruction (dict): 指示データ

    Returns:
        bool: 送信可能な場合True
    """
    status = str(instruction.get('STATUS', '')).strip()
    syorizumi = str(instruction.get('SYORIZUMIKB', '')).strip()
    edkkbn = str(instruction.get('EDKKBN', '')).strip()  # API側はEDKKBN

    # 完納区分がある場合は送信不可（完了済み）
    if edkkbn in ('1', '2'):
        return False

    # STATUS が完了条件に該当する場合は送信不可
    if status in ('3', '4', '8'):
        return False

    # STATUS が中止の場合は送信不可
    if status == '9':
        return False

    # 処理済区分が「実績登録中」の場合は送信不可
    if syorizumi == '1':
        return False

    # 上記以外（未完了 or 登録エラー）は送信可能
    return True


# 月次指示データの実行中キャッシュ {(year, month): [instruction, ...]}
# 同じ月を複数のテーブル・パターンで参照するため、1回の実行では取得を1度に抑える。
_MONTHLY_INSTRUCTIONS_CACHE = {}


async def get_instructions_by_month(client, api_base_url, read_api_key, year, month):
    """
    指定月の指示データを全件取得（同一実行中はキャッシュを再利用）

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        year (int): 年
        month (int): 月

    Returns:
        list: 指示データのリスト
    """
    cache_key = (year, month)
    if cache_key in _MONTHLY_INSTRUCTIONS_CACHE:
        return _MONTHLY_INSTRUCTIONS_CACHE[cache_key]

    api_url = f"{api_base_url}/instructions/"
    headers = {
        "X-API-KEY": read_api_key
    }
    params = {
        "year": year,
        "month": month
    }

    try:
        response = await client.get(
            api_url,
            headers=headers,
            params=params,
            timeout=60.0
        )
        response.raise_for_status()

        instructions = response.json()
        _MONTHLY_INSTRUCTIONS_CACHE[cache_key] = instructions
        return instructions

    except httpx.HTTPStatusError as e:
        logger.error(f"月次データ取得エラー ({year}年{month}月): HTTP {e.response.status_code} - {e.response.text}")
        return []
    except httpx.RequestError as e:
        logger.error(f"月次データ取得接続エラー ({year}年{month}月): {e}")
        return []
    except Exception as e:
        logger.error(f"月次データ取得予期しないエラー ({year}年{month}月): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def get_target_year_months():
    """
    対象月（当月・翌月・翌々月）を (year, month) のリストで返す

    filter_by_date_column() が抽出する月と同一。リダイレクト用インデックスの
    構築範囲を決めるために使用する。
    """
    now = datetime.now(JST)
    months = [(now.year, now.month)]
    for _ in range(2):
        year, month = months[-1]
        months.append((year + 1, 1) if month == 12 else (year, month + 1))
    return months


def build_special_part_redirect_index(instructions):
    """
    月次指示データから、特定5部品のリダイレクト解決用インデックスを構築

    Args:
        instructions (list): /instructions/ の応答（INDNO, SEINO, HMNM, SRCD, OYALISTNO を含む）

    Returns:
        dict: {'by_indno': {INDNO: {...}}, 'by_oya': {(SEINO, OYALISTNO): {INDNO, ...}}}
    """
    by_indno = {}
    by_oya = {}

    for instruction in instructions:
        indno = str(instruction.get('INDNO') or '').strip()
        if not indno:
            continue

        info = by_indno.get(indno)
        if info is None:
            info = {
                'hmnm': str(instruction.get('HMNM') or '').strip(),
                'srcd': str(instruction.get('SRCD') or '').strip(),
                'oya_keys': set(),
            }
            by_indno[indno] = info

        seino = str(instruction.get('SEINO') or '').strip()
        oyalistno = str(instruction.get('OYALISTNO') or '').strip()
        if seino and oyalistno:
            oya_key = (seino, oyalistno)
            info['oya_keys'].add(oya_key)
            by_oya.setdefault(oya_key, set()).add(indno)

    return {'by_indno': by_indno, 'by_oya': by_oya}


def resolve_special_part_targets(indno, redirect_index):
    """
    特定5部品の実績返却先INDNOを解決

    D3420.LISTNO を D3110 で引いた OYALISTNO（/instructions/ の応答に含まれる）が
    同一かつ同一SEINOの指示のうち、払出先(SRCD)=40 のINDNOを返す。

    Args:
        indno (str): i-Reporter 由来のINDNO（INDNO変換済み）
        redirect_index (dict): build_special_part_redirect_index() の戻り値

    Returns:
        tuple: (特定5部品か, 返却先INDNOのリスト)
               特定5部品でない場合は (False, [])。
               特定5部品だが40側が見つからない場合は (True, [])。
    """
    if not redirect_index:
        return False, []

    info = redirect_index['by_indno'].get(indno)
    if info is None or info['hmnm'] not in SPECIAL_PART_NAMES:
        return False, []

    # 既に払出先40の伝票（チェックシートが40側に作られたケース）はそのまま返す
    if info['srcd'] == SPECIAL_PART_TARGET_SRCD:
        return True, [indno]

    targets = set()
    for oya_key in info['oya_keys']:
        for candidate in redirect_index['by_oya'].get(oya_key, ()):
            if candidate == indno:
                continue
            candidate_info = redirect_index['by_indno'].get(candidate)
            if candidate_info and candidate_info['srcd'] == SPECIAL_PART_TARGET_SRCD:
                targets.add(candidate)

    return True, sorted(targets)


def get_cell_text(row, column):
    """行のセル値を前後空白除去した文字列で返す（欠損は空文字）"""
    value = row.get(column)
    if value is None or pd.isna(value):
        return ''
    return str(value).strip()


def get_seino_year(seino):
    """SEINO先頭2桁が数字ならその値（西暦下2桁。26=2026年）、数字でなければ None"""
    head = str(seino or '')[:2]
    return int(head) if len(head) == 2 and head.isdigit() else None


def build_seino_hmcd_index(instructions):
    """
    月次指示データから、払出先40の {HMCD: {(SEINO, INDNO), ...}} を構築

    Args:
        instructions (list): /instructions/ の応答（INDNO, SEINO, HMCD, SRCD を含む）
    """
    index = {}
    for instruction in instructions:
        if str(instruction.get('SRCD') or '').strip() != SEINO_HMCD_TARGET_SRCD:
            continue
        indno = str(instruction.get('INDNO') or '').strip()
        seino = str(instruction.get('SEINO') or '').strip()
        hmcd = str(instruction.get('HMCD') or '').strip()
        if indno and seino and hmcd:
            index.setdefault(hmcd, set()).add((seino, indno))
    return index


def resolve_targets_by_seino_hmcd(send_indno, row, seino_column, hmcd_column, indno_instructions, seino_hmcd_index, current_yy):
    """
    SEINO+HMCD（払出先40）で実績の返却先INDNOを解決

    Args:
        send_indno (str): i-Reporter 由来のINDNO（INDNO変換済み）
        row (pd.Series): 405等の行（SEINO末尾・HMCDの取得元）
        seino_column (str): SEINO末尾カラム名
        hmcd_column (str): HMCDカラム名
        indno_instructions (dict): {INDNO: [指示データ, ...]}（月次）
        seino_hmcd_index (dict): build_seino_hmcd_index() の戻り値
        current_yy (int): 今年（西暦下2桁）。これより小さい年のSEINOは対象外

    Returns:
        tuple: (理由, 返却先INDNOのリスト)
               理由は None=解決 / 'no_key'=SEINO・HMCD取得不可 / 'not_found'=払出先40に該当なし /
               'past_year'=前年以前の製番のみ / 'ambiguous'=SEINO末尾一致が複数
    """
    # (SEINO, HMCD, 完全一致か)。旧INDNOが rBOM にあれば rBOM の値、無ければ i-Reporter の値を使う
    keys = []
    old_instructions = indno_instructions.get(send_indno)
    if old_instructions:
        pairs = {
            (str(i.get('SEINO') or '').strip(), str(i.get('HMCD') or '').strip())
            for i in old_instructions
        }
        keys = [(seino, hmcd, True) for seino, hmcd in pairs if seino and hmcd]
    else:
        seino = get_cell_text(row, seino_column)
        hmcd = get_cell_text(row, hmcd_column)
        if seino and hmcd:
            keys = [(seino, hmcd, False)]
    if not keys:
        return 'no_key', []

    matches = set()
    suffix_match = False
    for seino, hmcd, exact in keys:
        for candidate_seino, candidate_indno in seino_hmcd_index.get(hmcd, ()):
            if exact:
                if candidate_seino == seino:
                    matches.add((candidate_seino, candidate_indno))
            elif candidate_seino.endswith(seino):
                suffix_match = True
                matches.add((candidate_seino, candidate_indno))
    if not matches:
        return 'not_found', []

    # 前年以前の製番は対象外（先頭が数字でないSEINOは年を判定できないので除外しない）
    current = set()
    for seino, indno in matches:
        year = get_seino_year(seino)
        if year is None or year >= current_yy:
            current.add((seino, indno))
    if not current:
        return 'past_year', []

    # 末尾一致で別SEINOが混ざった場合は特定できないので送らない
    if suffix_match and len({seino for seino, _ in current}) > 1:
        return 'ambiguous', []

    return None, sorted({indno for _, indno in current})


# 指示データ一括取得の1リクエストあたり件数上限。
# 大量のslip_keysを1回で投げると、バックエンドのOracle呼び出しが
# call timeout (30秒, DPY-4024/ORA-03156) を超えてHTTP 500になるため分割する。
INSTRUCTIONS_BATCH_CHUNK_SIZE = 100


async def get_instructions_batch(client, api_base_url, read_api_key, slip_keys):
    """
    複数の指示データを一括取得

    slip_keys を INSTRUCTIONS_BATCH_CHUNK_SIZE 件ずつに分割して複数回POSTし、
    結果のキャッシュをマージして返す（Oracle call timeout 回避のため）。

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        slip_keys (list): [{"indno": "...", "lineno": 1}, ...] のリスト

    Returns:
        dict: {(indno, lineno): {必要な4項目のみ}, ...} の辞書
    """
    if not slip_keys:
        return {}

    api_url = f"{api_base_url}/instructions/slip/batch"
    headers = {
        "X-API-KEY": read_api_key,
        "Content-Type": "application/json"
    }

    instruction_cache = {}
    total_chunks = (len(slip_keys) + INSTRUCTIONS_BATCH_CHUNK_SIZE - 1) // INSTRUCTIONS_BATCH_CHUNK_SIZE

    for chunk_index in range(total_chunks):
        start = chunk_index * INSTRUCTIONS_BATCH_CHUNK_SIZE
        chunk = slip_keys[start:start + INSTRUCTIONS_BATCH_CHUNK_SIZE]

        try:
            response = await client.post(
                api_url,
                headers=headers,
                json=chunk,
                timeout=60.0
            )
            response.raise_for_status()

            instructions = response.json()

            # 必要な4項目のみをキャッシュ
            for instruction in instructions:
                indno = instruction.get('INDNO', '')
                lineno = instruction.get('LINENO', 0)
                key = (indno, lineno)

                instruction_cache[key] = {
                    'STATUS': instruction.get('STATUS', ''),
                    'SYORIZUMIKB': instruction.get('SYORIZUMIKB', ''),
                    'EDKKBN': instruction.get('EDKKBN', ''),
                    'THQTY': instruction.get('THQTY')
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"指示データ一括取得エラー (チャンク {chunk_index + 1}/{total_chunks}): HTTP {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"指示データ一括取得接続エラー (チャンク {chunk_index + 1}/{total_chunks}): {e}")
        except Exception as e:
            logger.error(f"指示データ一括取得予期しないエラー (チャンク {chunk_index + 1}/{total_chunks}): {e}")
            import traceback
            logger.error(traceback.format_exc())

    return instruction_cache


async def send_completion_record(client, api_url, api_key, payload, row_info):
    """
    completion エンドポイントにデータを送信

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_url (str): API URL
        api_key (str): API KEY
        payload (dict): 送信データ
        row_info (str): 行情報（ログ用）

    Returns:
        tuple: (bool, str) - (成功フラグ, レスポンスメッセージ)
    """
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = await client.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=10.0
        )
        response.raise_for_status()

        response_data = response.json()
        message = response_data.get('message', 'Success')
        return True, message

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"送信失敗 [{row_info}]: INDNO={payload['INDNO']} - {error_msg}")
        return False, error_msg

    except httpx.RequestError as e:
        error_msg = f"接続エラー: {e}"
        logger.error(f"送信失敗 [{row_info}]: INDNO={payload['INDNO']} - {error_msg}")
        return False, error_msg

    except Exception as e:
        error_msg = f"予期しないエラー: {e}"
        logger.error(f"送信失敗 [{row_info}]: INDNO={payload['INDNO']} - {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        return False, error_msg


async def process_dataframe_data(df, api_base_url, read_api_key, insert_api_key, indno_mapping=None):
    """
    DataFrameデータを処理してAPIに送信

    Args:
        df (pd.DataFrame): 処理対象データ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー
        indno_mapping (dict): {lot_number: indno} マッピング辞書（省略可）

    Returns:
        dict: 処理結果サマリー
    """
    if indno_mapping is None:
        indno_mapping = {}
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    blocked_count = 0
    converted_count = 0  # INDNO変換カウント
    redirected_count = 0  # 特定5部品のリダイレクトカウント

    # 日本時間の今日の日付（YYYY-MM-DD形式）
    kteddt = datetime.now(JST).strftime('%Y-%m-%d')

    async with httpx.AsyncClient() as client:
        # 特定5部品のリダイレクト用インデックスを構築（対象月＝当月・翌月・翌々月）
        redirect_instructions = []
        for year, month in get_target_year_months():
            redirect_instructions.extend(
                await get_instructions_by_month(client, api_base_url, read_api_key, year, month)
            )
        redirect_index = build_special_part_redirect_index(redirect_instructions)

        # ステップ1: 事前処理 - 全INDNOリストを作成（INDNO変換もここで行う）
        slip_keys = []
        valid_rows = []
        special_unresolved = []  # 特定5部品だが払出先40の指示が見つからなかったINDNO

        for index, row in df.iterrows():
            # INDNO取得（cluster_1_2_t）
            original_indno = str(row.get('cluster_1_2_t', '')).strip()
            if not original_indno or pd.isna(row.get('cluster_1_2_t')):
                skip_count += 1
                continue

            # lineno は固定値 1
            lineno = 1

            # INDNO変換処理（マッピング辞書に存在する場合は変換）
            # 指示データ取得の前に変換を行う
            send_indno = original_indno
            if original_indno in indno_mapping:
                send_indno = indno_mapping[original_indno]
                converted_count += 1

            # 特定5部品は払出先40の指示へ返却先を差し替える
            is_special, resolved_indnos = resolve_special_part_targets(send_indno, redirect_index)
            if is_special:
                if not resolved_indnos:
                    special_unresolved.append(send_indno)
                    skip_count += 1
                    continue
                if resolved_indnos != [send_indno]:
                    redirected_count += 1
                target_indnos = resolved_indnos
            else:
                target_indnos = [send_indno]

            for target_indno in target_indnos:
                slip_keys.append({"indno": target_indno, "lineno": lineno})
                valid_rows.append((row, original_indno, target_indno, lineno))

        if special_unresolved:
            logger.error(
                f"特定5部品リダイレクト先(払出先40)なし: {len(special_unresolved)}件 - "
                + ", ".join(special_unresolved)
            )

        if not slip_keys:
            logger.warning("バリデーション通過データが0件です。処理を終了します。")
            return {
                'total': total_rows,
                'success': success_count,
                'skip': skip_count,
                'error': error_count,
                'blocked': blocked_count,
                'converted': converted_count,
                'redirected': redirected_count
            }

        # ステップ2: 指示データを一括取得
        instruction_cache = await get_instructions_batch(
            client, api_base_url, read_api_key, slip_keys
        )

        # ステップ3: 送信処理
        completion_url = f"{api_base_url}/completion/"
        valid_count = len(valid_rows)
        missing_instructions = []  # 指示データが見つからなかった (元INDNO, 変換後INDNO, lineno) を集約用に蓄積

        for row_number, (row, original_indno, send_indno, lineno) in enumerate(valid_rows, 1):
            key = (send_indno, lineno)  # 変換後のINDNOでキャッシュを検索

            # キャッシュから指示データを取得
            if key not in instruction_cache:
                missing_instructions.append((original_indno, send_indno, lineno))
                skip_count += 1
                continue

            instruction = instruction_cache[key]

            # 送信可否判定
            if not is_sendable_status(instruction):
                blocked_count += 1
                continue

            # prdqty を取得（THQTY）
            prdqty = instruction.get('THQTY')
            if prdqty is None or pd.isna(prdqty):
                logger.warning(f"THQTY が空: INDNO={send_indno}")
                skip_count += 1
                continue

            # float型に変換
            try:
                prdqty_value = float(prdqty)
            except (ValueError, TypeError):
                logger.warning(f"THQTY が数値変換不可: INDNO={send_indno}, THQTY={prdqty}")
                skip_count += 1
                continue

            # ペイロード作成（send_indnoは既に変換済み）
            payload = {
                "KTEDDT": kteddt,
                "INDNO": send_indno,  # 変換後のINDNOを使用
                "lineno": lineno,
                "IPTANCD": "SECT1557",
                "prdqty": prdqty_value,
                "ktedqty": prdqty_value
            }

            # API送信
            row_info = f"{row_number}/{valid_count}"
            success, message = await send_completion_record(
                client, completion_url, insert_api_key, payload, row_info
            )

            if success:
                success_count += 1
            else:
                error_count += 1

        # 指示データが見つからなかった分をまとめて1行でログ出力（ログ肥大化防止のため個別出力はしない）
        if missing_instructions:
            detail = ", ".join(
                f"{o}(lineno={l})" if o == s else f"{o}→{s}(lineno={l})"
                for o, s, l in missing_instructions
            )
            logger.error(f"指示データ取得失敗: {len(missing_instructions)}件 - {detail}")

    return {
        'total': total_rows,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'blocked': blocked_count,
        'converted': converted_count,  # INDNO変換件数
        'redirected': redirected_count  # 特定5部品リダイレクト件数
    }


async def process_dataframe_data_pattern3(df, api_base_url, read_api_key, insert_api_key):
    """
    DataFrameデータを処理してAPIに送信（パターン3: cluster_1_641_t='2'/'4'、全LINENO送信）
    ※この関数は後方互換性のため残していますが、新しいコードでは process_pattern3_table() を使用してください

    Args:
        df (pd.DataFrame): 処理対象データ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー

    Returns:
        dict: 処理結果サマリー
    """
    return await process_pattern3_table(
        df, api_base_url, read_api_key, insert_api_key,
        indno_column='cluster_1_2_t',
        date_column='top_remarks3',
        iptancd='SECT1557',
        table_name='view_report_405'
    )


async def process_pattern3_table(df, api_base_url, read_api_key, insert_api_key, indno_column, date_column, iptancd, table_name='unknown', seino_column=None, ktcd_column=None, indno_mapping=None, resolve_mode='', hmcd_column=None):
    """
    DataFrameデータを処理してAPIに送信（汎用パターン3: 全LINENO送信）

    Args:
        df (pd.DataFrame): 処理対象データ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー
        indno_column (str): INDNO取得用カラム名（"FROM_API"の場合はAPI経由で取得）
        date_column (str): 日付カラム名（対象月の判定に使用）
        iptancd (str): IPTANCD固定値
        table_name (str): テーブル名（ログ表示用）
        seino_column (str): SEINOカラム名（indno_column="FROM_API"の場合に使用）
        ktcd_column (str): KTCDカラム名（indno_column="FROM_API"の場合に使用）
        indno_mapping (dict): {lot_number: indno} マッピング辞書（省略可）
        resolve_mode (str): 'seino_hmcd' の場合、SEINO+HMCD（払出先40）で返却先INDNOを解決する
        hmcd_column (str): HMCDカラム名（resolve_mode='seino_hmcd' の場合に使用。seino_column はSEINO末尾）

    Returns:
        dict: 処理結果サマリー
    """
    if indno_mapping is None:
        indno_mapping = {}
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    blocked_count = 0
    converted_count = 0  # INDNO変換カウント
    redirected_count = 0  # 特定5部品のリダイレクトカウント

    # 日本時間の今日の日付（YYYY-MM-DD形式）
    kteddt = datetime.now(JST).strftime('%Y-%m-%d')

    async with httpx.AsyncClient() as client:
        # ステップ1: 対象月のリストを作成
        target_months = set()

        # カンマで分割されているかチェック（年と月が別カラム）
        if ',' in date_column:
            columns = [col.strip() for col in date_column.split(',')]
            if len(columns) == 2:
                year_column = columns[0]
                month_column = columns[1]

                for index, row in df.iterrows():
                    year_value = str(row.get(year_column, '')).strip()
                    month_value = str(row.get(month_column, '')).strip()

                    # 年と月が両方有効な数値の場合
                    if year_value.isdigit() and month_value.replace('.', '').isdigit():
                        try:
                            year = int(year_value)
                            month = int(float(month_value))  # 7.0 のような場合にも対応
                            if 1 <= month <= 12:
                                target_months.add((year, month))
                        except ValueError:
                            continue
            else:
                logger.error(f"DATE_COLUMNの形式が不正です: {date_column}")
        else:
            # 単一カラムの場合（既存ロジック）
            for index, row in df.iterrows():
                date_value = str(row.get(date_column, '')).strip()
                # 6桁以上の場合は先頭6文字を取得
                if len(date_value) >= 6:
                    year_month = date_value[:6]
                    if year_month.isdigit():
                        year = int(year_month[:4])
                        month = int(year_month[4:6])
                        target_months.add((year, month))

        if not target_months:
            logger.warning(f"対象月が見つかりません ({table_name})。処理を終了します。")
            return {
                'total': total_rows,
                'success': success_count,
                'skip': skip_count,
                'error': error_count,
                'blocked': blocked_count,
                'converted': converted_count,
                'redirected': redirected_count
            }

        target_months = sorted(target_months)

        # ステップ2: 各月の指示データを取得してキャッシュ
        all_instructions = []
        for year, month in target_months:
            instructions = await get_instructions_by_month(client, api_base_url, read_api_key, year, month)
            all_instructions.extend(instructions)

        # INDNOをキーとした辞書を作成（全LINENOを含む）
        # {INDNO: [{instruction1}, {instruction2}, ...]}
        indno_instructions = {}
        for instruction in all_instructions:
            indno = instruction.get('INDNO', '')
            if indno:
                if indno not in indno_instructions:
                    indno_instructions[indno] = []
                indno_instructions[indno].append(instruction)

        # 特定5部品のリダイレクト用インデックス（月次データから構築＝追加のAPI呼び出しは不要）
        redirect_index = build_special_part_redirect_index(all_instructions)

        # SEINO+HMCD解決用インデックス（払出先40。月次データから構築）
        use_seino_hmcd = resolve_mode == RESOLVE_MODE_SEINO_HMCD
        seino_hmcd_index = build_seino_hmcd_index(all_instructions) if use_seino_hmcd else {}
        current_yy = datetime.now(JST).year % 100
        resolved_targets = set()  # 解決済みの返却先INDNO（複数行が同じINDNOに解決される場合の二重送信防止）
        resolve_failures = {}  # {理由: [ラベル, ...]} をログ集約用に蓄積

        # ステップ3: 送信処理
        completion_url = f"{api_base_url}/completion/"

        processed_count = 0
        missing_instructions = []  # 指示データが見つからなかった (元INDNO, 変換後INDNO) を集約用に蓄積
        special_unresolved = []  # 特定5部品だが払出先40の指示が見つからなかったINDNO
        for row_number, (index, row) in enumerate(df.iterrows(), 1):
            # INDNO取得（指定されたカラムから、またはAPI経由）
            if indno_column == "FROM_API":
                # SEINOとKTCDからAPI経由でINDNOを取得
                if not seino_column or not ktcd_column:
                    logger.error(f"seino_columnまたはktcd_columnが指定されていません ({table_name})")
                    skip_count += 1
                    continue

                seino = str(row.get(seino_column, '')).strip()

                # KTCDの取得: カラムとして存在する場合はカラムから、存在しない場合は固定値として扱う
                if ktcd_column in df.columns:
                    ktcd = str(row.get(ktcd_column, '')).strip()
                    if not ktcd or pd.isna(row.get(ktcd_column)):
                        logger.warning(f"KTCDが空 ({ktcd_column}) [{row_number}/{total_rows}]")
                        skip_count += 1
                        continue
                else:
                    # 固定値として使用
                    ktcd = ktcd_column.strip()

                if not seino or pd.isna(row.get(seino_column)):
                    logger.warning(f"SEINOが空 ({seino_column}) [{row_number}/{total_rows}]")
                    skip_count += 1
                    continue

                # API経由でINDNOを取得
                original_indno = await fetch_indno_from_api(seino, ktcd, api_base_url, read_api_key)
                if not original_indno:
                    logger.error(f"INDNO取得失敗: SEINO={seino}, KTCD={ktcd} [{row_number}/{total_rows}]")
                    error_count += 1
                    continue

            else:
                # 指定カラムから直接INDNO取得
                original_indno = str(row.get(indno_column, '')).strip()
                if not original_indno or pd.isna(row.get(indno_column)):
                    logger.warning(f"INDNOが空 ({indno_column}) [{row_number}/{total_rows}]")
                    skip_count += 1
                    continue

            # INDNO変換処理（マッピング辞書に存在する場合は変換）
            # 指示データ検索の前に変換を行う
            send_indno = original_indno
            if original_indno in indno_mapping:
                send_indno = indno_mapping[original_indno]
                converted_count += 1

            if use_seino_hmcd:
                # SEINO+HMCD（払出先40）で現行INDNOを解決（特定5部品リダイレクトは不要）
                reason, target_indnos = resolve_targets_by_seino_hmcd(
                    send_indno, row, seino_column, hmcd_column,
                    indno_instructions, seino_hmcd_index, current_yy
                )
                if reason:
                    label = f"{send_indno}({get_cell_text(row, seino_column)}/{get_cell_text(row, hmcd_column)})"
                    resolve_failures.setdefault(reason, []).append(label)
                    skip_count += 1
                    continue
                target_indnos = [t for t in target_indnos if t not in resolved_targets]
                resolved_targets.update(target_indnos)
                if not target_indnos:
                    continue  # 他の行で解決済み（二重送信しない）
            else:
                # 特定5部品は払出先40の指示へ返却先を差し替える
                is_special, resolved_indnos = resolve_special_part_targets(send_indno, redirect_index)
                if is_special:
                    if not resolved_indnos:
                        special_unresolved.append(send_indno)
                        skip_count += 1
                        continue
                    if resolved_indnos != [send_indno]:
                        redirected_count += 1
                    target_indnos = resolved_indnos
                else:
                    target_indnos = [send_indno]

            for target_indno in target_indnos:
                # 該当INDNOの指示データを取得（変換・リダイレクト後のINDNOで検索）
                if target_indno not in indno_instructions:
                    missing_instructions.append((original_indno, target_indno))
                    skip_count += 1
                    continue

                # 全LINENOに対して送信
                instructions_for_indno = indno_instructions[target_indno]

                for instruction in instructions_for_indno:
                    lineno = instruction.get('LINENO', 0)
                    processed_count += 1

                    # 送信可否判定
                    if not is_sendable_status(instruction):
                        blocked_count += 1
                        continue

                    # prdqty を取得（THQTY）
                    prdqty = instruction.get('THQTY')
                    if prdqty is None or pd.isna(prdqty):
                        logger.warning(f"THQTYが空: INDNO={target_indno}, LINENO={lineno}")
                        skip_count += 1
                        continue

                    # float型に変換
                    try:
                        prdqty_value = float(prdqty)
                    except (ValueError, TypeError):
                        logger.warning(f"THQTY数値変換不可: INDNO={target_indno}, LINENO={lineno}, THQTY={prdqty}")
                        skip_count += 1
                        continue

                    # ペイロード作成（target_indnoは変換・リダイレクト適用済み）
                    payload = {
                        "KTEDDT": kteddt,
                        "INDNO": target_indno,
                        "lineno": lineno,
                        "IPTANCD": iptancd,
                        "prdqty": prdqty_value,
                        "ktedqty": prdqty_value
                    }

                    # API送信
                    row_info = f"{row_number}/{total_rows}, LINENO={lineno}"
                    success, message = await send_completion_record(
                        client, completion_url, insert_api_key, payload, row_info
                    )

                    if success:
                        success_count += 1
                    else:
                        error_count += 1

        # 指示データが見つからなかった分をまとめて1行でログ出力（ログ肥大化防止のため個別出力はしない）
        if missing_instructions:
            detail = ", ".join(
                o if o == s else f"{o}→{s}"
                for o, s in missing_instructions
            )
            logger.error(f"指示データ取得失敗: {len(missing_instructions)}件 ({table_name}) - {detail}")

        # 特定5部品でリダイレクト先が見つからなかった分をまとめて1行でログ出力
        if special_unresolved:
            logger.error(
                f"特定5部品リダイレクト先(払出先40)なし: {len(special_unresolved)}件 ({table_name}) - "
                + ", ".join(special_unresolved)
            )

        # SEINO+HMCDで解決できなかった分を理由別に1行ずつログ出力
        resolve_failure_messages = (
            ('no_key', logger.error, 'SEINO・HMCD取得不可'),
            ('not_found', logger.error, '払出先40のSEINO+HMCD該当なし'),
            ('ambiguous', logger.error, 'SEINO末尾一致が複数（特定不可）'),
            ('past_year', logger.warning, '前年以前の製番のため対象外'),
        )
        for reason, log, message in resolve_failure_messages:
            labels = resolve_failures.get(reason)
            if labels:
                log(f"{message}: {len(labels)}件 ({table_name}) - " + ", ".join(labels))

    return {
        'total': total_rows,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'blocked': blocked_count,
        'converted': converted_count,  # INDNO変換件数
        'redirected': redirected_count  # 特定5部品リダイレクト件数
    }


async def main_async():
    """メイン処理（非同期）"""
    logger.info("処理開始")

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # API設定チェック
    if not READ_API_KEY:
        logger.error("READ_API_KEY が設定されていません")
        return 1

    if not INSERT_API_KEY:
        logger.error("INSERT_API_KEY が設定されていません")
        return 1

    # INDNOマッピング辞書を読み込み
    indno_mapping = load_indno_mapping()

    # PostgreSQLからデータを取得
    df = extract_data_from_postgres()
    if df is None or df.empty:
        logger.error("データ取得に失敗したか、データが空です")
        return 1

    # top_remarks3 で当月・翌月・翌々月のデータをフィルタリング
    df_filtered = filter_by_top_remarks3(df)
    if df_filtered.empty:
        logger.warning("top_remarks3フィルタリング後のデータが0件です。処理を終了します。")
        return 0

    # ========== 時限処理：202603以降除外（不要になったら下記1行をコメントアウト） ==========
    # df_filtered = filter_out_202603_and_later(df_filtered, 'top_remarks3')
    # ========== 時限処理ここまで ==========
    if df_filtered.empty:
        logger.warning("202603以降除外フィルタリング後のデータが0件です。処理を終了します。")
        return 0

    # ==================== パターン1処理 ====================
    df_pattern1 = filter_by_cluster_flags(df_filtered)

    result_pattern1 = {'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0, 'redirected': 0}
    if not df_pattern1.empty:
        result_pattern1 = await process_dataframe_data(df_pattern1, FASTAPI_BASE_URL, READ_API_KEY, INSERT_API_KEY, indno_mapping)
    else:
        logger.warning("パターン1: clusterフラグフィルタリング後のデータが0件です。スキップします。")

    # ==================== パターン3処理（設定ベース複数テーブル対応） ====================
    pattern3_configs = load_pattern3_configs()

    if not pattern3_configs:
        logger.warning("パターン3: 設定が見つかりません。スキップします。")
        result_pattern3_list = []
    else:
        result_pattern3_list = []

        # 各テーブル設定に対してループ処理
        for idx, config in enumerate(pattern3_configs, 1):
            table_name = config['table']
            source_table = config['source_table']
            indno_col = config['indno_col']
            seino_col = config['seino_col']
            ktcd_col = config['ktcd_col']
            judge_col = config['judge_col']
            date_col = config['date_col']
            iptancd = config['iptancd']

            # ソーステーブルからデータを取得
            df_source = fetch_data_from_table(source_table)
            if df_source is None or df_source.empty:
                logger.error(f"パターン3-{idx}: {source_table} からのデータ取得失敗。スキップします。")
                result_pattern3_list.append({'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0})
                continue

            # 日付カラムで当月・翌月・翌々月のデータをフィルタリング
            df_date_filtered = filter_by_date_column(df_source, date_col, f"{source_table}.{date_col}")
            if df_date_filtered.empty:
                logger.warning(f"パターン3-{idx}: {source_table} 日付フィルタリング後0件。スキップします。")
                result_pattern3_list.append({'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0})
                continue

            # ========== 時限処理：202603以降除外（不要になったら下記1行をコメントアウト） ==========
            # df_date_filtered = filter_out_202603_and_later(df_date_filtered, date_col.split(',')[0] if ',' in date_col else date_col, f"{source_table}.{date_col}")
            # ========== 時限処理ここまで ==========
            if df_date_filtered.empty:
                logger.warning(f"パターン3-{idx}: {source_table} 202603以降除外後0件。スキップします。")
                result_pattern3_list.append({'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0})
                continue

            # 判定カラムが '2' または '4' の行を抽出
            df_pattern3_table = filter_by_judge_column(df_date_filtered, judge_col, f"{source_table}.{judge_col}")

            if df_pattern3_table.empty:
                logger.warning(f"パターン3-{idx}: {source_table} 判定フィルタリング後0件。スキップします。")
                result_pattern3_list.append({'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0})
                continue

            # データを処理してAPI送信（パターン3）
            result = await process_pattern3_table(
                df_pattern3_table,
                FASTAPI_BASE_URL,
                READ_API_KEY,
                INSERT_API_KEY,
                indno_column=indno_col,
                date_column=date_col,
                iptancd=iptancd,
                table_name=table_name,
                seino_column=seino_col,
                ktcd_column=ktcd_col,
                indno_mapping=indno_mapping,
                resolve_mode=config['mode'],
                hmcd_column=config['hmcd_col']
            )
            result_pattern3_list.append(result)

    # ==================== 全体サマリー ====================
    pattern3_total_success = sum(r['success'] for r in result_pattern3_list) if result_pattern3_list else 0
    pattern3_total_error = sum(r['error'] for r in result_pattern3_list) if result_pattern3_list else 0
    pattern3_total_converted = sum(r['converted'] for r in result_pattern3_list) if result_pattern3_list else 0
    pattern3_total_redirected = sum(r.get('redirected', 0) for r in result_pattern3_list) if result_pattern3_list else 0

    logger.info(
        f"完了: P1成功={result_pattern1['success']}件/エラー={result_pattern1['error']}件, "
        f"P3成功={pattern3_total_success}件/エラー={pattern3_total_error}件, "
        f"特定5部品リダイレクト=P1:{result_pattern1.get('redirected', 0)}件/P3:{pattern3_total_redirected}件"
    )

    total_errors = result_pattern1['error'] + pattern3_total_error
    return 0 if total_errors == 0 else 1


def main():
    """メイン処理"""
    global logger
    logger = setup_logger()

    # 非同期処理を実行
    import asyncio
    exit_code = asyncio.run(main_async())

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
