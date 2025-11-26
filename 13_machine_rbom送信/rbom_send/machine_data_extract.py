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

        configs.append({
            'table': table,
            'source_table': source_table,
            'indno_col': indno_col,
            'seino_col': seino_col,
            'ktcd_col': ktcd_col,
            'judge_col': judge_col,
            'date_col': date_col,
            'iptancd': iptancd
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
        logger.info(f"INDNOマッピング読み込み完了: {len(mapping)}件")

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
                    logger.info(f"古いログファイルを削除しました: {filename}")
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
    logger.info("=" * 60)
    logger.info("PostgreSQL データ取得処理を開始")
    logger.info("=" * 60)

    try:
        # カラムリスト生成
        columns = generate_column_list()
        logger.info(f"取得対象カラム数: {len(columns)}列")

        # SQL文生成
        column_str = ', '.join(columns)
        sql = f"SELECT {column_str} FROM view_report_405"

        # PostgreSQL接続
        logger.info(f"データベースに接続中: {DB_URL.split('@')[1]}")  # パスワード部分は非表示
        engine = create_engine(DB_URL, echo=False)

        # データ取得
        logger.info("view_report_405 からデータ取得中...")
        with engine.connect() as connection:
            df = pd.read_sql(sql, connection)

        logger.info(f"データ取得完了: {len(df):,}行 × {len(df.columns)}列")

        # デバッグ用: CSV出力（ENABLE_CSV_OUTPUT=true の場合のみ）
        if ENABLE_CSV_OUTPUT:
            logger.info("")
            logger.info("--- デバッグモード: CSV出力 ---")
            timestamp = datetime.now(JST).strftime('%Y%m%d_%H%M%S')
            output_filename = f"machine_data_{timestamp}.csv"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            df.to_csv(output_path, index=False, encoding='utf-8-sig')

            file_size = os.path.getsize(output_path)
            logger.info(f"✓ CSV出力完了: {output_filename} ({file_size:,} bytes)")
            logger.info(f"  出力先: {os.path.abspath(output_path)}")
            logger.info("--- デバッグモード終了 ---")
            logger.info("")

        return df

    except Exception as e:
        logger.error(f"✗ エラーが発生しました: {e}")
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
        logger.info(f"{table_name} からデータ取得中...")
        with engine.connect() as connection:
            df = pd.read_sql(sql, connection)

        logger.info(f"✓ データ取得完了: {len(df):,}行 × {len(df.columns)}列")
        return df

    except Exception as e:
        logger.error(f"✗ {table_name} からのデータ取得エラー: {e}")
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
        logger.error(f"✗ API経由でのINDNO取得エラー (SEINO={seino}, KTCD={ktcd}): {e}")
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

            logger.info(f"年月分離モード: 年={year_column}, 月={month_column}")

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
            logger.info(f"対象月フィルタリング ({display_name}): {', '.join(target_months)}")

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
            logger.info(f"対象月フィルタリング ({display_name}): {', '.join(target_months)}")

            # 日付カラムの先頭6文字を抽出（一時カラム名を動的に生成）
            temp_col_name = f'{date_column}_ym'
            df[temp_col_name] = df[date_column].astype(str).str[:6]

            # 対象月のデータのみ抽出
            df_filtered = df[df[temp_col_name].isin(target_months)].copy()

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"{display_name}フィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

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
        logger.info(f"チェック対象カラム数: {len(existing_columns)}")

        if not existing_columns:
            logger.warning("cluster_1_*_n カラムが見つかりません")
            return pd.DataFrame()

        # いずれかのカラムが 1.0 の行を抽出
        mask = df[existing_columns].eq(1.0).any(axis=1)
        df_filtered = df[mask]

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"clusterフラグフィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

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

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"{display_name}フィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

        return df_filtered

    except Exception as e:
        logger.error(f"{display_name}フィルタリングに失敗しました: {e}")
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


async def get_instructions_by_month(client, api_base_url, read_api_key, year, month):
    """
    指定月の指示データを全件取得

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        year (int): 年
        month (int): 月

    Returns:
        list: 指示データのリスト
    """
    api_url = f"{api_base_url}/instructions/"
    headers = {
        "X-API-KEY": read_api_key
    }
    params = {
        "year": year,
        "month": month
    }

    try:
        logger.info(f"月次データ取得開始: {year}年{month}月")

        response = await client.get(
            api_url,
            headers=headers,
            params=params,
            timeout=60.0
        )
        response.raise_for_status()

        instructions = response.json()
        logger.info(f"月次データ取得完了: {year}年{month}月 - {len(instructions)}件")

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


async def get_instructions_batch(client, api_base_url, read_api_key, slip_keys):
    """
    複数の指示データを一括取得

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

    try:
        logger.info(f"指示データ一括取得開始: {len(slip_keys)}件")

        response = await client.post(
            api_url,
            headers=headers,
            json=slip_keys,
            timeout=30.0
        )
        response.raise_for_status()

        instructions = response.json()
        logger.info(f"指示データ一括取得完了: {len(instructions)}件")

        # 必要な4項目のみをキャッシュ
        instruction_cache = {}
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

        return instruction_cache

    except httpx.HTTPStatusError as e:
        logger.error(f"指示データ一括取得エラー: HTTP {e.response.status_code} - {e.response.text}")
        return {}
    except httpx.RequestError as e:
        logger.error(f"指示データ一括取得接続エラー: {e}")
        return {}
    except Exception as e:
        logger.error(f"指示データ一括取得予期しないエラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


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
        logger.info(f"  [{row_info}] ✓ 送信成功: INDNO={payload['INDNO']}, DATE={payload['KTEDDT']}, QTY={payload['ktedqty']}")
        return True, message

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"  [{row_info}] ✗ 送信失敗: INDNO={payload['INDNO']} - {error_msg}")
        return False, error_msg

    except httpx.RequestError as e:
        error_msg = f"接続エラー: {e}"
        logger.error(f"  [{row_info}] ✗ 送信失敗: INDNO={payload['INDNO']} - {error_msg}")
        return False, error_msg

    except Exception as e:
        error_msg = f"予期しないエラー: {e}"
        logger.error(f"  [{row_info}] ✗ 送信失敗: INDNO={payload['INDNO']} - {error_msg}")
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

    logger.info(f"データ処理を開始します: 全{total_rows}件\n")
    if indno_mapping:
        logger.info(f"INDNOマッピング: {len(indno_mapping)}件のマッピング適用可能\n")

    # 日本時間の今日の日付（YYYY-MM-DD形式）
    kteddt = datetime.now(JST).strftime('%Y-%m-%d')
    logger.info(f"KTEDDT（日本時間システム日付）: {kteddt}\n")

    async with httpx.AsyncClient() as client:
        # ステップ1: 事前処理 - 全INDNOリストを作成（INDNO変換もここで行う）
        slip_keys = []
        valid_rows = []

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
                logger.info(f"  INDNO変換: {original_indno} → {send_indno}")

            slip_keys.append({"indno": send_indno, "lineno": lineno})
            valid_rows.append((row, original_indno, send_indno, lineno))

        if not slip_keys:
            logger.warning("バリデーション通過データが0件です。処理を終了します。")
            return {
                'total': total_rows,
                'success': success_count,
                'skip': skip_count,
                'error': error_count,
                'blocked': blocked_count
            }

        # ステップ2: 指示データを一括取得
        logger.info("")
        instruction_cache = await get_instructions_batch(
            client, api_base_url, read_api_key, slip_keys
        )
        logger.info("")

        # ステップ3: 送信処理
        completion_url = f"{api_base_url}/completion/"
        valid_count = len(valid_rows)
        logger.info(f"データ送信を開始します: {valid_count}件\n")

        for row_number, (row, original_indno, send_indno, lineno) in enumerate(valid_rows, 1):
            key = (send_indno, lineno)  # 変換後のINDNOでキャッシュを検索

            # キャッシュから指示データを取得
            if key not in instruction_cache:
                logger.error(f"  [{row_number}/{valid_count}] ✗ エラー: 指示データ取得失敗 (元INDNO={original_indno}, 変換後INDNO={send_indno}, lineno={lineno})")
                skip_count += 1
                continue

            instruction = instruction_cache[key]

            # 送信可否判定
            if not is_sendable_status(instruction):
                logger.info(f"  [{row_number}/{valid_count}] 除外: 送信不可状態（完了/中止/実績登録中） (INDNO={send_indno})")
                blocked_count += 1
                continue

            # prdqty を取得（THQTY）
            prdqty = instruction.get('THQTY')
            if prdqty is None or pd.isna(prdqty):
                logger.warning(f"  [{row_number}/{valid_count}] スキップ: THQTY が空 (INDNO={send_indno})")
                skip_count += 1
                continue

            # float型に変換
            try:
                prdqty_value = float(prdqty)
            except (ValueError, TypeError):
                logger.warning(f"  [{row_number}/{valid_count}] スキップ: THQTY が数値変換不可 (INDNO={send_indno}, THQTY={prdqty})")
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

    return {
        'total': total_rows,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'blocked': blocked_count,
        'converted': converted_count  # INDNO変換件数
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


async def process_pattern3_table(df, api_base_url, read_api_key, insert_api_key, indno_column, date_column, iptancd, table_name='unknown', seino_column=None, ktcd_column=None, indno_mapping=None):
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

    logger.info(f"データ処理を開始します（パターン3: {table_name}）: 全{total_rows}件\n")
    if indno_mapping:
        logger.info(f"INDNOマッピング: {len(indno_mapping)}件のマッピング適用可能\n")

    # 日本時間の今日の日付（YYYY-MM-DD形式）
    kteddt = datetime.now(JST).strftime('%Y-%m-%d')
    logger.info(f"KTEDDT（日本時間システム日付）: {kteddt}\n")
    logger.info(f"IPTANCD: {iptancd}\n")
    logger.info(f"INDNOカラム: {indno_column}\n")
    logger.info(f"日付カラム: {date_column}\n")

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
            logger.warning("対象月が見つかりません。処理を終了します。")
            return {
                'total': total_rows,
                'success': success_count,
                'skip': skip_count,
                'error': error_count,
                'blocked': blocked_count,
                'converted': converted_count
            }

        target_months = sorted(target_months)
        logger.info(f"対象月: {', '.join([f'{y}年{m}月' for y, m in target_months])}\n")

        # ステップ2: 各月の指示データを取得してキャッシュ
        all_instructions = []
        for year, month in target_months:
            instructions = await get_instructions_by_month(client, api_base_url, read_api_key, year, month)
            all_instructions.extend(instructions)

        logger.info(f"\n全月次データ取得完了: 合計{len(all_instructions)}件\n")

        # INDNOをキーとした辞書を作成（全LINENOを含む）
        # {INDNO: [{instruction1}, {instruction2}, ...]}
        indno_instructions = {}
        for instruction in all_instructions:
            indno = instruction.get('INDNO', '')
            if indno:
                if indno not in indno_instructions:
                    indno_instructions[indno] = []
                indno_instructions[indno].append(instruction)

        logger.info(f"指示データINDNO数: {len(indno_instructions)}件\n")

        # ステップ3: 送信処理
        completion_url = f"{api_base_url}/completion/"
        logger.info(f"データ送信を開始します: {total_rows}件のINDNO\n")

        processed_count = 0
        for row_number, (index, row) in enumerate(df.iterrows(), 1):
            # INDNO取得（指定されたカラムから、またはAPI経由）
            if indno_column == "FROM_API":
                # SEINOとKTCDからAPI経由でINDNOを取得
                if not seino_column or not ktcd_column:
                    logger.error(f"  [{row_number}/{total_rows}] スキップ: seino_columnまたはktcd_columnが指定されていません")
                    skip_count += 1
                    continue

                seino = str(row.get(seino_column, '')).strip()

                # KTCDの取得: カラムとして存在する場合はカラムから、存在しない場合は固定値として扱う
                if ktcd_column in df.columns:
                    ktcd = str(row.get(ktcd_column, '')).strip()
                    if not ktcd or pd.isna(row.get(ktcd_column)):
                        logger.warning(f"  [{row_number}/{total_rows}] スキップ: KTCDが空 ({ktcd_column})")
                        skip_count += 1
                        continue
                else:
                    # 固定値として使用
                    ktcd = ktcd_column.strip()

                if not seino or pd.isna(row.get(seino_column)):
                    logger.warning(f"  [{row_number}/{total_rows}] スキップ: SEINOが空 ({seino_column})")
                    skip_count += 1
                    continue

                # API経由でINDNOを取得
                original_indno = await fetch_indno_from_api(seino, ktcd, api_base_url, read_api_key)
                if not original_indno:
                    logger.error(f"  [{row_number}/{total_rows}] ✗ エラー: INDNO取得失敗 (SEINO={seino}, KTCD={ktcd})")
                    error_count += 1
                    continue

                logger.info(f"  [{row_number}/{total_rows}] API経由でINDNO取得: SEINO={seino}, KTCD={ktcd} → INDNO={original_indno}")
            else:
                # 指定カラムから直接INDNO取得
                original_indno = str(row.get(indno_column, '')).strip()
                if not original_indno or pd.isna(row.get(indno_column)):
                    logger.warning(f"  [{row_number}/{total_rows}] スキップ: INDNOが空 ({indno_column})")
                    skip_count += 1
                    continue

            # INDNO変換処理（マッピング辞書に存在する場合は変換）
            # 指示データ検索の前に変換を行う
            send_indno = original_indno
            if original_indno in indno_mapping:
                send_indno = indno_mapping[original_indno]
                converted_count += 1
                logger.info(f"  [{row_number}/{total_rows}] INDNO変換: {original_indno} → {send_indno}")

            # 該当INDNOの指示データを取得（変換後のINDNOで検索）
            if send_indno not in indno_instructions:
                logger.error(f"  [{row_number}/{total_rows}] ✗ エラー: 指示データ取得失敗 (元INDNO={original_indno}, 変換後INDNO={send_indno})")
                skip_count += 1
                continue

            # 全LINENOに対して送信
            instructions_for_indno = indno_instructions[send_indno]
            logger.info(f"  [{row_number}/{total_rows}] INDNO={send_indno}: {len(instructions_for_indno)}件のLINENOを処理")

            for instruction in instructions_for_indno:
                lineno = instruction.get('LINENO', 0)
                processed_count += 1

                # 送信可否判定
                if not is_sendable_status(instruction):
                    logger.info(f"    └ LINENO={lineno}: 除外（送信不可状態）")
                    blocked_count += 1
                    continue

                # prdqty を取得（THQTY）
                prdqty = instruction.get('THQTY')
                if prdqty is None or pd.isna(prdqty):
                    logger.warning(f"    └ LINENO={lineno}: スキップ（THQTYが空）")
                    skip_count += 1
                    continue

                # float型に変換
                try:
                    prdqty_value = float(prdqty)
                except (ValueError, TypeError):
                    logger.warning(f"    └ LINENO={lineno}: スキップ（THQTY数値変換不可: {prdqty}）")
                    skip_count += 1
                    continue

                # ペイロード作成（send_indnoは既に変換済み）
                payload = {
                    "KTEDDT": kteddt,
                    "INDNO": send_indno,  # 変換後のINDNOを使用
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

    return {
        'total': total_rows,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'blocked': blocked_count,
        'converted': converted_count  # INDNO変換件数
    }


async def main_async():
    """メイン処理（非同期）"""
    logger.info("=" * 60)
    logger.info("機械データ取得 → FastAPI 送信 統合処理を開始")
    logger.info("=" * 60)

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # API設定チェック
    if not READ_API_KEY:
        logger.error("READ_API_KEY が設定されていません")
        return 1

    if not INSERT_API_KEY:
        logger.error("INSERT_API_KEY が設定されていません")
        return 1

    logger.info(f"API送信先: {FASTAPI_BASE_URL}")
    logger.info(f"CSV出力モード: {'有効' if ENABLE_CSV_OUTPUT else '無効（デバッグ用）'}\n")

    # INDNOマッピング辞書を読み込み
    indno_mapping = load_indno_mapping()

    # PostgreSQLからデータを取得
    df = extract_data_from_postgres()
    if df is None or df.empty:
        logger.error("データ取得に失敗したか、データが空です")
        return 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("FastAPI 送信処理を開始")
    logger.info("=" * 60)

    # top_remarks3 で当月・翌月・翌々月のデータをフィルタリング
    df_filtered = filter_by_top_remarks3(df)
    if df_filtered.empty:
        logger.warning("top_remarks3フィルタリング後のデータが0件です。処理を終了します。")
        return 0

    # ==================== パターン1処理 ====================
    logger.info("")
    logger.info("=" * 60)
    logger.info("【パターン1】cluster_1_24_n～cluster_1_636_n のフラグチェック処理")
    logger.info("=" * 60)

    # cluster_1_24_n～cluster_1_636_n のいずれかが 1.0 の行を抽出
    df_pattern1 = filter_by_cluster_flags(df_filtered)

    result_pattern1 = {'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0}
    if not df_pattern1.empty:
        # データを処理してAPI送信（パターン1）
        result_pattern1 = await process_dataframe_data(df_pattern1, FASTAPI_BASE_URL, READ_API_KEY, INSERT_API_KEY, indno_mapping)

        # パターン1処理結果サマリー
        logger.info("")
        logger.info("=" * 60)
        logger.info("【パターン1】処理完了")
        logger.info(f"総件数: {result_pattern1['total']}件")
        logger.info(f"成功: {result_pattern1['success']}件")
        logger.info(f"INDNO変換: {result_pattern1['converted']}件")
        logger.info(f"スキップ（バリデーションエラー・指示データ取得失敗）: {result_pattern1['skip']}件")
        logger.info(f"除外（送信不可状態）: {result_pattern1['blocked']}件")
        logger.info(f"エラー（送信失敗）: {result_pattern1['error']}件")
        logger.info("=" * 60)
    else:
        logger.warning("【パターン1】clusterフラグフィルタリング後のデータが0件です。パターン1をスキップします。")

    # ==================== パターン3処理（設定ベース複数テーブル対応） ====================
    logger.info("")
    logger.info("=" * 60)
    logger.info("【パターン3】設定ベース複数テーブル処理")
    logger.info("=" * 60)

    # .envから設定を読み込み
    pattern3_configs = load_pattern3_configs()

    if not pattern3_configs:
        logger.warning("【パターン3】設定が見つかりません。パターン3をスキップします。")
        result_pattern3_list = []
    else:
        logger.info(f"パターン3対象テーブル数: {len(pattern3_configs)}件\n")
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

            logger.info("")
            logger.info("-" * 60)
            logger.info(f"【パターン3-{idx}】テーブル: {table_name}")
            logger.info(f"  ソーステーブル: {source_table}")
            logger.info(f"  INDNOカラム: {indno_col}")
            if indno_col == "FROM_API":
                logger.info(f"  SEINOカラム: {seino_col}")
                logger.info(f"  KTCDカラム: {ktcd_col}")
            logger.info(f"  判定カラム: {judge_col}")
            logger.info(f"  日付カラム: {date_col}")
            logger.info(f"  IPTANCD: {iptancd}")
            logger.info("-" * 60)

            # ソーステーブルからデータを取得
            df_source = fetch_data_from_table(source_table)
            if df_source is None or df_source.empty:
                logger.error(f"【パターン3-{idx}】{source_table} からのデータ取得に失敗しました。このテーブルをスキップします。")
                result_pattern3_list.append({'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0})
                continue

            # 日付カラムで当月・翌月・翌々月のデータをフィルタリング
            df_date_filtered = filter_by_date_column(df_source, date_col, f"{source_table}.{date_col}")
            if df_date_filtered.empty:
                logger.warning(f"【パターン3-{idx}】日付フィルタリング後のデータが0件です。このテーブルをスキップします。")
                result_pattern3_list.append({'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0, 'converted': 0})
                continue

            # 判定カラムが '2' または '4' の行を抽出
            df_pattern3_table = filter_by_judge_column(df_date_filtered, judge_col, f"{source_table}.{judge_col}")

            if df_pattern3_table.empty:
                logger.warning(f"【パターン3-{idx}】フィルタリング後のデータが0件です。このテーブルをスキップします。")
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
                indno_mapping=indno_mapping
            )
            result_pattern3_list.append(result)

            # このテーブルの処理結果サマリー
            logger.info("")
            logger.info(f"【パターン3-{idx}】{table_name} 処理完了")
            logger.info(f"総件数: {result['total']}件")
            logger.info(f"成功: {result['success']}件")
            logger.info(f"INDNO変換: {result['converted']}件")
            logger.info(f"スキップ（バリデーションエラー・指示データ取得失敗）: {result['skip']}件")
            logger.info(f"除外（送信不可状態）: {result['blocked']}件")
            logger.info(f"エラー（送信失敗）: {result['error']}件")

    # パターン3全体のサマリー
    if result_pattern3_list:
        pattern3_total_success = sum(r['success'] for r in result_pattern3_list)
        pattern3_total_error = sum(r['error'] for r in result_pattern3_list)
        pattern3_total_converted = sum(r['converted'] for r in result_pattern3_list)
        logger.info("")
        logger.info("=" * 60)
        logger.info("【パターン3】全テーブル処理完了")
        logger.info(f"合計成功: {pattern3_total_success}件")
        logger.info(f"合計INDNO変換: {pattern3_total_converted}件")
        logger.info(f"合計エラー: {pattern3_total_error}件")
        logger.info("=" * 60)
    else:
        pattern3_total_success = 0
        pattern3_total_error = 0
        pattern3_total_converted = 0

    # ==================== 全体サマリー ====================
    total_converted = result_pattern1['converted'] + pattern3_total_converted
    logger.info("")
    logger.info("=" * 60)
    logger.info("全処理完了")
    logger.info("=" * 60)
    logger.info(f"【パターン1】成功: {result_pattern1['success']}件 / INDNO変換: {result_pattern1['converted']}件 / エラー: {result_pattern1['error']}件")
    logger.info(f"【パターン3】成功: {pattern3_total_success}件 / INDNO変換: {pattern3_total_converted}件 / エラー: {pattern3_total_error}件")
    logger.info(f"【合計】成功: {result_pattern1['success'] + pattern3_total_success}件 / INDNO変換: {total_converted}件 / エラー: {result_pattern1['error'] + pattern3_total_error}件")
    logger.info("=" * 60)

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
