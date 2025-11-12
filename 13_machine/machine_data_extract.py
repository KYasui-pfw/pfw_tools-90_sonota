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

# ディレクトリ作成
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=9))


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


def filter_by_top_remarks3(df):
    """
    top_remarks3 で当月・翌月・翌々月のデータをフィルタリング

    Args:
        df (pd.DataFrame): CSVデータ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    try:
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
        logger.info(f"対象月フィルタリング: {', '.join(target_months)}")

        # top_remarks3 の先頭6文字を抽出
        df['top_remarks3_ym'] = df['top_remarks3'].astype(str).str[:6]

        # 対象月のデータのみ抽出
        df_filtered = df[df['top_remarks3_ym'].isin(target_months)]

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"top_remarks3フィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

        return df_filtered

    except Exception as e:
        logger.error(f"top_remarks3フィルタリングに失敗しました: {e}")
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

    Args:
        df (pd.DataFrame): 入力データ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    try:
        # cluster_1_641_t が 2 または 4 の行を抽出（浮動小数点数も考慮）
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

        mask = df['cluster_1_641_t'].apply(is_2_or_4)
        df_filtered = df[mask].copy()

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"cluster_1_641_tフィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

        return df_filtered

    except Exception as e:
        logger.error(f"cluster_1_641_tフィルタリングに失敗しました: {e}")
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


async def process_dataframe_data(df, api_base_url, read_api_key, insert_api_key):
    """
    DataFrameデータを処理してAPIに送信

    Args:
        df (pd.DataFrame): 処理対象データ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー

    Returns:
        dict: 処理結果サマリー
    """
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    blocked_count = 0

    logger.info(f"データ処理を開始します: 全{total_rows}件\n")

    # 日本時間の今日の日付（YYYY-MM-DD形式）
    kteddt = datetime.now(JST).strftime('%Y-%m-%d')
    logger.info(f"KTEDDT（日本時間システム日付）: {kteddt}\n")

    async with httpx.AsyncClient() as client:
        # ステップ1: 事前処理 - 全INDNOリストを作成
        slip_keys = []
        valid_rows = []

        for index, row in df.iterrows():
            # INDNO取得（cluster_1_2_t）
            indno = str(row.get('cluster_1_2_t', '')).strip()
            if not indno or pd.isna(row.get('cluster_1_2_t')):
                skip_count += 1
                continue

            # lineno は固定値 1
            lineno = 1

            slip_keys.append({"indno": indno, "lineno": lineno})
            valid_rows.append((index + 1, row, indno, lineno))

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
        logger.info(f"データ送信を開始します: {len(valid_rows)}件\n")

        for row_number, row, indno, lineno in valid_rows:
            key = (indno, lineno)

            # キャッシュから指示データを取得
            if key not in instruction_cache:
                logger.error(f"  [{row_number}/{total_rows}] ✗ エラー: 指示データ取得失敗 (INDNO={indno}, lineno={lineno})")
                skip_count += 1
                continue

            instruction = instruction_cache[key]

            # 送信可否判定
            if not is_sendable_status(instruction):
                logger.info(f"  [{row_number}/{total_rows}] 除外: 送信不可状態（完了/中止/実績登録中） (INDNO={indno})")
                blocked_count += 1
                continue

            # prdqty を取得（THQTY）
            prdqty = instruction.get('THQTY')
            if prdqty is None or pd.isna(prdqty):
                logger.warning(f"  [{row_number}/{total_rows}] スキップ: THQTY が空 (INDNO={indno})")
                skip_count += 1
                continue

            # float型に変換
            try:
                prdqty_value = float(prdqty)
            except (ValueError, TypeError):
                logger.warning(f"  [{row_number}/{total_rows}] スキップ: THQTY が数値変換不可 (INDNO={indno}, THQTY={prdqty})")
                skip_count += 1
                continue

            # ペイロード作成
            payload = {
                "KTEDDT": kteddt,
                "INDNO": indno,
                "lineno": lineno,
                "IPTANCD": "SECT1557",
                "prdqty": prdqty_value,
                "ktedqty": prdqty_value
            }

            # API送信
            row_info = f"{row_number}/{total_rows}"
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
        'blocked': blocked_count
    }


async def process_dataframe_data_pattern3(df, api_base_url, read_api_key, insert_api_key):
    """
    DataFrameデータを処理してAPIに送信（パターン3: cluster_1_641_t='2'/'4'、全LINENO送信）

    Args:
        df (pd.DataFrame): 処理対象データ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー

    Returns:
        dict: 処理結果サマリー
    """
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    blocked_count = 0

    logger.info(f"データ処理を開始します（パターン3）: 全{total_rows}件\n")

    # 日本時間の今日の日付（YYYY-MM-DD形式）
    kteddt = datetime.now(JST).strftime('%Y-%m-%d')
    logger.info(f"KTEDDT（日本時間システム日付）: {kteddt}\n")

    async with httpx.AsyncClient() as client:
        # ステップ1: 対象月のリストを作成
        target_months = set()
        for index, row in df.iterrows():
            top_remarks3 = str(row.get('top_remarks3', '')).strip()
            # 6桁以上の場合は先頭6文字を取得
            if len(top_remarks3) >= 6:
                year_month = top_remarks3[:6]
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
                'blocked': blocked_count
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
        for index, row in df.iterrows():
            row_number = index + 1

            # INDNO取得（cluster_1_2_t）
            indno = str(row.get('cluster_1_2_t', '')).strip()
            if not indno or pd.isna(row.get('cluster_1_2_t')):
                logger.warning(f"  [{row_number}/{total_rows}] スキップ: INDNOが空")
                skip_count += 1
                continue

            # 該当INDNOの指示データを取得
            if indno not in indno_instructions:
                logger.error(f"  [{row_number}/{total_rows}] ✗ エラー: 指示データ取得失敗 (INDNO={indno})")
                skip_count += 1
                continue

            # 全LINENOに対して送信
            instructions_for_indno = indno_instructions[indno]
            logger.info(f"  [{row_number}/{total_rows}] INDNO={indno}: {len(instructions_for_indno)}件のLINENOを処理")

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

                # ペイロード作成
                payload = {
                    "KTEDDT": kteddt,
                    "INDNO": indno,
                    "lineno": lineno,
                    "IPTANCD": "SECT1557",
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
        'blocked': blocked_count
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

    result_pattern1 = {'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0}
    if not df_pattern1.empty:
        # データを処理してAPI送信（パターン1）
        result_pattern1 = await process_dataframe_data(df_pattern1, FASTAPI_BASE_URL, READ_API_KEY, INSERT_API_KEY)

        # パターン1処理結果サマリー
        logger.info("")
        logger.info("=" * 60)
        logger.info("【パターン1】処理完了")
        logger.info(f"総件数: {result_pattern1['total']}件")
        logger.info(f"成功: {result_pattern1['success']}件")
        logger.info(f"スキップ（バリデーションエラー・指示データ取得失敗）: {result_pattern1['skip']}件")
        logger.info(f"除外（送信不可状態）: {result_pattern1['blocked']}件")
        logger.info(f"エラー（送信失敗）: {result_pattern1['error']}件")
        logger.info("=" * 60)
    else:
        logger.warning("【パターン1】clusterフラグフィルタリング後のデータが0件です。パターン1をスキップします。")

    # ==================== パターン3処理 ====================
    logger.info("")
    logger.info("=" * 60)
    logger.info("【パターン3】cluster_1_641_t='2'/'4' の処理")
    logger.info("=" * 60)

    # cluster_1_641_t が '2' または '4' の行を抽出
    df_pattern3 = filter_by_cluster_641t(df_filtered)

    result_pattern3 = {'total': 0, 'success': 0, 'skip': 0, 'error': 0, 'blocked': 0}
    if not df_pattern3.empty:
        # データを処理してAPI送信（パターン3）
        result_pattern3 = await process_dataframe_data_pattern3(df_pattern3, FASTAPI_BASE_URL, READ_API_KEY, INSERT_API_KEY)

        # パターン3処理結果サマリー
        logger.info("")
        logger.info("=" * 60)
        logger.info("【パターン3】処理完了")
        logger.info(f"総件数: {result_pattern3['total']}件")
        logger.info(f"成功: {result_pattern3['success']}件")
        logger.info(f"スキップ（バリデーションエラー・指示データ取得失敗）: {result_pattern3['skip']}件")
        logger.info(f"除外（送信不可状態）: {result_pattern3['blocked']}件")
        logger.info(f"エラー（送信失敗）: {result_pattern3['error']}件")
        logger.info("=" * 60)
    else:
        logger.warning("【パターン3】cluster_1_641_tフィルタリング後のデータが0件です。パターン3をスキップします。")

    # ==================== 全体サマリー ====================
    logger.info("")
    logger.info("=" * 60)
    logger.info("全処理完了")
    logger.info("=" * 60)
    logger.info(f"【パターン1】成功: {result_pattern1['success']}件 / エラー: {result_pattern1['error']}件")
    logger.info(f"【パターン3】成功: {result_pattern3['success']}件 / エラー: {result_pattern3['error']}件")
    logger.info(f"【合計】成功: {result_pattern1['success'] + result_pattern3['success']}件 / エラー: {result_pattern1['error'] + result_pattern3['error']}件")
    logger.info("=" * 60)

    total_errors = result_pattern1['error'] + result_pattern3['error']
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
