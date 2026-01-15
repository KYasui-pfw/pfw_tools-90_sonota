"""
rBOM API → SQLite 同期スクリプト

rBOM APIからデータを取得し、SQLiteに保存します。
15分ごとにcronで実行されることを想定。

同期対象:
    - rBOM M0430 (SGNCD, SGNNM) → _rBOM_MSTR_RES (CODE, NAME + ダミー値)
    - rBOM M0840 (HMCD, SEQ, KTCD, SGNCD) → _rBOM_DATA_RES_CAPA (FINAL_ITEM_CODE, PROCESS_ORDER, PROCESS_CODE, RES_CODE1 + ダミー値)

実行方法:
    python krd_sync_rbom.py

仕様:
    - 同期方向: rBOM API → SQLite（一方向、読み取り専用）
    - _rBOM_MSTR_RES: 全件置き換え（DELETE & INSERT）
    - _rBOM_DATA_RES_CAPA: UPSERT（INSERT or UPDATE、DELETEなし）
    - エラー処理: ログ記録のみ（処理継続）
    - ログ: 日次ローテーション、7日間保持
"""

import sqlite3
import httpx
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone, timedelta
import os
import re
import sys
import time

# ========== 設定 ==========

# rBOM API設定（環境変数から読み取り）
API_BASE_URL = os.getenv('API_BASE_URL', 'http://fastapi:8000')
READ_API_KEY = os.getenv('READ_API_KEY', '')

# SQLite設定
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'krd_machine.db')

# ログ設定
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 対象テーブル名
RBOM_MSTR_RES_TABLE = '_rBOM_MSTR_RES'
RBOM_DATA_RES_CAPA_TABLE = '_rBOM_DATA_RES_CAPA'

# ========== ロギング設定 ==========

def setup_logging():
    """ロギングを設定"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # 日次ローテーションハンドラ（log_rbom_YYYYMMDD.txt形式）
    log_file = os.path.join(LOG_DIR, 'log_rbom.txt')
    handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )

    # ファイル名形式をカスタマイズ
    handler.suffix = "_%Y%m%d.txt"
    handler.extMatch = re.compile(r"^_\d{8}\.txt$")
    handler.namer = lambda name: name.replace('log_rbom.txt.', 'log_rbom')

    # フォーマット設定
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # コンソール出力も追加
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

# ========== データベース接続 ==========

def get_sqlite_connection():
    """SQLite接続を取得"""
    try:
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        logger.info(f"SQLite接続成功: {SQLITE_DB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"SQLite接続失敗: {e}")
        raise

# ========== rBOM API呼び出し ==========

def fetch_m0430_data():
    """
    rBOM APIからM0430（資源マスタ）のデータを取得

    Returns:
        list: 資源データのリスト [{SGNCD: ..., SGNNM: ...}, ...]
    """
    try:
        headers = {"X-API-KEY": READ_API_KEY}

        # /query エンドポイントへPOSTリクエスト
        request_body = {
            "table": "M0430",
            "columns": ["SGNCD", "SGNNM"],
            "order_by": ["SGNCD"]
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_BASE_URL}/query",
                headers=headers,
                json=request_body
            )
            response.raise_for_status()

            result = response.json()
            rows = result.get('rows', [])

            logger.info(f"rBOM API取得成功: M0430 {len(rows)}件")
            return rows

    except httpx.RequestError as e:
        logger.error(f"rBOM APIへの接続に失敗: {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"rBOM APIがエラーを返しました: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"rBOM APIからのデータ取得中にエラー: {e}")
        return []

# ========== テーブル作成・同期 ==========

def create_rbom_mstr_res_table(sqlite_conn):
    """
    _rBOM_MSTR_RES テーブルを作成
    MSTR_RESと同じ構造で作成
    """
    try:
        cursor = sqlite_conn.cursor()

        # 既存テーブルを削除
        cursor.execute(f"DROP TABLE IF EXISTS {RBOM_MSTR_RES_TABLE}")

        # MSTR_RESと同じ構造でテーブル作成
        create_sql = f"""
        CREATE TABLE {RBOM_MSTR_RES_TABLE} (
            NO INTEGER NOT NULL,
            CODE TEXT NOT NULL,
            NAME TEXT NOT NULL,
            GROUP_NO INTEGER NOT NULL,
            PALETTE_NUM INTEGER NOT NULL,
            SHIFT_NO INTEGER NOT NULL,
            WORKING INTEGER NOT NULL,
            COLOR INTEGER NOT NULL,
            VIEW_NO INTEGER NOT NULL,
            TYPE TEXT NOT NULL,
            QRY TEXT NOT NULL,
            FACTOR_NUM INTEGER NOT NULL,
            DISABLED_RES TEXT NOT NULL,
            OLD_CODE TEXT,
            HOURS_PER_DAY INTEGER
        )
        """
        cursor.execute(create_sql)
        sqlite_conn.commit()
        cursor.close()

        logger.info(f"テーブル {RBOM_MSTR_RES_TABLE} を作成しました")
        return True

    except Exception as e:
        logger.error(f"テーブル {RBOM_MSTR_RES_TABLE} の作成失敗: {e}")
        return False

def sync_rbom_mstr_res_data(sqlite_conn, api_data):
    """
    rBOM APIから取得したM0430データをSQLiteに同期

    Args:
        sqlite_conn: SQLite接続
        api_data: rBOM APIから取得したデータ [{SGNCD: ..., SGNNM: ...}, ...]

    Returns:
        tuple: (成功フラグ, レコード数)
    """
    try:
        if not api_data:
            logger.info(f"  データ: 0件")
            return True, 0

        cursor = sqlite_conn.cursor()

        # 全件削除
        cursor.execute(f"DELETE FROM {RBOM_MSTR_RES_TABLE}")

        # データ挿入（ダミー値を設定）
        insert_sql = f"""
        INSERT INTO {RBOM_MSTR_RES_TABLE}
        (NO, CODE, NAME, GROUP_NO, PALETTE_NUM, SHIFT_NO, WORKING, COLOR,
         VIEW_NO, TYPE, QRY, FACTOR_NUM, DISABLED_RES, OLD_CODE, HOURS_PER_DAY)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for i, row in enumerate(api_data, start=1):
            # CODE = SGNCD, NAME = SGNNM, その他はダミー値
            values = (
                i,                          # NO: 連番
                row.get('SGNCD', ''),       # CODE: 資源コード
                row.get('SGNNM', ''),       # NAME: 資源名
                1,                          # GROUP_NO: ダミー
                1,                          # PALETTE_NUM: ダミー
                1,                          # SHIFT_NO: ダミー
                1,                          # WORKING: ダミー
                1,                          # COLOR: ダミー
                i,                          # VIEW_NO: 連番
                '1',                        # TYPE: ダミー
                '1',                        # QRY: ダミー
                1,                          # FACTOR_NUM: ダミー
                '0',                        # DISABLED_RES: ダミー（有効）
                None,                       # OLD_CODE: NULL
                8                           # HOURS_PER_DAY: ダミー（8時間）
            )
            cursor.execute(insert_sql, values)

        sqlite_conn.commit()
        cursor.close()

        record_count = len(api_data)
        logger.info(f"  データ: {record_count:,}件")
        return True, record_count

    except Exception as e:
        logger.error(f"  データ同期失敗: {e}")
        return False, 0


# ========== _rBOM_DATA_RES_CAPA 関連 ==========

def fetch_m0840_data():
    """
    rBOM APIからM0840（品目工程マスタ）のデータを取得

    Returns:
        list: 品目工程データのリスト [{HMCD: ..., SEQ: ..., KTCD: ..., SGNCD: ...}, ...]
    """
    try:
        headers = {"X-API-KEY": READ_API_KEY}

        # /query エンドポイントへPOSTリクエスト
        request_body = {
            "table": "M0840",
            "columns": ["HMCD", "SEQ", "KTCD", "SGNCD"],
            "order_by": ["HMCD", "SEQ"]
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{API_BASE_URL}/query",
                headers=headers,
                json=request_body
            )
            response.raise_for_status()

            result = response.json()
            rows = result.get('rows', [])

            logger.info(f"rBOM API取得成功: M0840 {len(rows)}件")
            return rows

    except httpx.RequestError as e:
        logger.error(f"rBOM APIへの接続に失敗: {e}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"rBOM APIがエラーを返しました: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"rBOM APIからのデータ取得中にエラー: {e}")
        return []


def create_rbom_data_res_capa_table(sqlite_conn):
    """
    _rBOM_DATA_RES_CAPA テーブルを作成（存在しない場合のみ）
    DATA_RES_CAPAと同じ構造で作成
    """
    try:
        cursor = sqlite_conn.cursor()

        # テーブルが存在しない場合のみ作成
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {RBOM_DATA_RES_CAPA_TABLE} (
            FINAL_ITEM_CODE TEXT,
            PROCESS_ORDER INTEGER,
            PROCESS_CODE TEXT,
            RES_CODE1 TEXT,
            CAPACITY1 TEXT,
            INF_CHANGE1 TEXT,
            RES_CODE2 TEXT,
            CAPACITY2 TEXT,
            INF_CHANGE2 TEXT,
            RES_CODE3 TEXT,
            CAPACITY3 TEXT,
            INF_CHANGE3 TEXT,
            VERSION INTEGER DEFAULT 1,
            OPE_NAME TEXT,
            UP_DATE TEXT,
            CHK_VAL_FLG INTEGER DEFAULT 0,
            PRIMARY KEY (FINAL_ITEM_CODE, PROCESS_ORDER, VERSION)
        )
        """
        cursor.execute(create_sql)
        sqlite_conn.commit()
        cursor.close()

        logger.info(f"テーブル {RBOM_DATA_RES_CAPA_TABLE} を確認/作成しました")
        return True

    except Exception as e:
        logger.error(f"テーブル {RBOM_DATA_RES_CAPA_TABLE} の作成失敗: {e}")
        return False


def sync_rbom_data_res_capa(sqlite_conn, api_data):
    """
    rBOM APIから取得したM0840データをSQLiteに同期（UPSERT）

    Args:
        sqlite_conn: SQLite接続
        api_data: rBOM APIから取得したデータ [{HMCD: ..., SEQ: ..., KTCD: ..., SGNCD: ...}, ...]

    Returns:
        tuple: (成功フラグ, 挿入数, 更新数)
    """
    try:
        if not api_data:
            logger.info(f"  データ: 0件")
            return True, 0, 0

        cursor = sqlite_conn.cursor()

        # UPSERT用SQL（SQLite 3.24+）
        upsert_sql = f"""
        INSERT INTO {RBOM_DATA_RES_CAPA_TABLE}
        (FINAL_ITEM_CODE, PROCESS_ORDER, PROCESS_CODE, RES_CODE1,
         CAPACITY1, INF_CHANGE1, RES_CODE2, CAPACITY2, INF_CHANGE2,
         RES_CODE3, CAPACITY3, INF_CHANGE3, VERSION, OPE_NAME, UP_DATE, CHK_VAL_FLG)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(FINAL_ITEM_CODE, PROCESS_ORDER, VERSION) DO UPDATE SET
            PROCESS_CODE = excluded.PROCESS_CODE,
            RES_CODE1 = excluded.RES_CODE1,
            UP_DATE = excluded.UP_DATE
        """

        insert_count = 0
        update_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d')

        for row in api_data:
            # M0840 → DATA_RES_CAPA マッピング
            values = (
                row.get('HMCD', ''),        # FINAL_ITEM_CODE ← HMCD
                row.get('SEQ', 0),          # PROCESS_ORDER ← SEQ
                row.get('KTCD', ''),        # PROCESS_CODE ← KTCD
                row.get('SGNCD', ''),       # RES_CODE1 ← SGNCD
                '1',                        # CAPACITY1: ダミー
                '1',                        # INF_CHANGE1: ダミー
                '',                         # RES_CODE2: 空
                '1',                        # CAPACITY2: ダミー
                '1',                        # INF_CHANGE2: ダミー
                '',                         # RES_CODE3: 空
                '1',                        # CAPACITY3: ダミー
                '1',                        # INF_CHANGE3: ダミー
                1,                          # VERSION: 固定値1
                '',                         # OPE_NAME: 空
                current_date,               # UP_DATE: 現在日付
                0                           # CHK_VAL_FLG: 0
            )

            # 既存レコードをチェック
            cursor.execute(
                f"SELECT 1 FROM {RBOM_DATA_RES_CAPA_TABLE} WHERE FINAL_ITEM_CODE = ? AND PROCESS_ORDER = ? AND VERSION = ?",
                (row.get('HMCD', ''), row.get('SEQ', 0), 1)
            )
            exists = cursor.fetchone() is not None

            cursor.execute(upsert_sql, values)

            if exists:
                update_count += 1
            else:
                insert_count += 1

        sqlite_conn.commit()
        cursor.close()

        logger.info(f"  データ: 挿入 {insert_count:,}件, 更新 {update_count:,}件")
        return True, insert_count, update_count

    except Exception as e:
        logger.error(f"  データ同期失敗: {e}")
        return False, 0, 0

# ========== メイン処理 ==========

def format_time(seconds):
    """秒数を読みやすい形式に変換"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.1f}秒"

def sync_rbom_to_sqlite():
    """rBOM APIからSQLiteへの同期メイン処理"""
    logger.info("=" * 80)
    logger.info("rBOM API → SQLite 同期開始")
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info("=" * 80)

    overall_start_time = time.time()
    sqlite_conn = None
    results = []

    try:
        # SQLite接続
        sqlite_conn = get_sqlite_connection()

        # ===== 1. _rBOM_MSTR_RES (M0430) =====
        logger.info("-" * 40)
        logger.info("1. _rBOM_MSTR_RES (M0430) 同期")
        logger.info("-" * 40)

        m0430_data = fetch_m0430_data()
        if m0430_data:
            if create_rbom_mstr_res_table(sqlite_conn):
                success, count = sync_rbom_mstr_res_data(sqlite_conn, m0430_data)
                results.append((RBOM_MSTR_RES_TABLE, success, count, 0))
            else:
                results.append((RBOM_MSTR_RES_TABLE, False, 0, 0))
        else:
            logger.warning("M0430データを取得できませんでした")
            results.append((RBOM_MSTR_RES_TABLE, False, 0, 0))

        # ===== 2. _rBOM_DATA_RES_CAPA (M0840) =====
        logger.info("-" * 40)
        logger.info("2. _rBOM_DATA_RES_CAPA (M0840) 同期")
        logger.info("-" * 40)

        m0840_data = fetch_m0840_data()
        if m0840_data:
            if create_rbom_data_res_capa_table(sqlite_conn):
                success, insert_count, update_count = sync_rbom_data_res_capa(sqlite_conn, m0840_data)
                results.append((RBOM_DATA_RES_CAPA_TABLE, success, insert_count, update_count))
            else:
                results.append((RBOM_DATA_RES_CAPA_TABLE, False, 0, 0))
        else:
            logger.warning("M0840データを取得できませんでした")
            results.append((RBOM_DATA_RES_CAPA_TABLE, False, 0, 0))

        overall_elapsed = time.time() - overall_start_time

        # サマリー
        logger.info("=" * 80)
        logger.info("同期完了サマリー")
        for table_name, success, count1, count2 in results:
            if table_name == RBOM_MSTR_RES_TABLE:
                logger.info(f"  {table_name}: {'成功' if success else '失敗'} ({count1:,}件)")
            else:
                logger.info(f"  {table_name}: {'成功' if success else '失敗'} (挿入:{count1:,}件, 更新:{count2:,}件)")
        logger.info(f"処理時間: {format_time(overall_elapsed)}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"同期処理中に致命的エラー: {e}")
        sys.exit(1)

    finally:
        if sqlite_conn:
            sqlite_conn.close()
            logger.info("SQLite接続をクローズしました")

# ========== エントリポイント ==========

if __name__ == "__main__":
    try:
        # API設定確認
        if not READ_API_KEY:
            logger.error("READ_API_KEY が設定されていません")
            logger.error(".env ファイルに READ_API_KEY を設定してください")
            sys.exit(1)

        sync_rbom_to_sqlite()

    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)
