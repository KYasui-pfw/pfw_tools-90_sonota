"""
KRD MySQL → SQLite 高頻度同期スクリプト

genpinhyoシステムで使用されているテーブルのみを同期します。
5分ごとにWindows Task Schedulerで実行されることを想定。

同期対象テーブル（6個）:
    - DATA_ASP2_PUT
    - MSTR_PROCODESTR
    - DATA_KOUTEIZUKAN
    - MSTR_METAL
    - DATA_RES_CAPA
    - MSTR_RES

実行方法:
    python krd_sync_frequent.py

仕様:
    - 同期方向: MySQL → SQLite（一方向、読み取り専用）
    - 更新戦略: 全件置き換え（DELETE & INSERT）
    - エラー処理: ログ記録のみ（処理継続）
    - ログ: 日次ローテーション、7日間保持
"""

import sqlite3
import pymysql
from sqlalchemy import create_engine, text
import pandas as pd
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone, timedelta
import os
import re
import sys
import time

# ========== 設定 ==========

# MySQL接続設定（環境変数から読み取り）
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'krd'),
    'database': os.getenv('MYSQL_DATABASE', 'machin'),
    'user': os.getenv('MYSQL_USER', 'pfw'),
    'password': os.getenv('MYSQL_PASSWORD', 'mejiriHoo'),
    'charset': os.getenv('MYSQL_CHARSET', 'utf8')
}

# SQLite設定
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'krd_machine.db')

# ログ設定
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 同期対象テーブル（genpinhyo使用テーブルのみ）
INCLUDE_TABLES = [
    'DATA_ASP2_PUT',
    'MSTR_PROCODESTR',
    'MSTR_METAL',
    'DATA_RES_CAPA',
    'MSTR_RES'
]

# ========== ロギング設定 ==========

def setup_logging():
    """ロギングを設定"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # 日次ローテーションハンドラ（log_frequent_YYYYMMDD.txt形式）
    log_file = os.path.join(LOG_DIR, 'log_frequent.txt')
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
    handler.namer = lambda name: name.replace('log_frequent.txt.', 'log_frequent')

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

def get_mysql_connection():
    """MySQL接続を取得"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        logger.info("MySQL接続成功")
        return conn
    except Exception as e:
        logger.error(f"MySQL接続失敗: {e}")
        raise

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

# ========== テーブル情報取得 ==========

def get_all_tables(mysql_conn):
    """MySQL上の指定テーブル一覧を取得"""
    try:
        cursor = mysql_conn.cursor()

        placeholders = ','.join(['%s'] * len(INCLUDE_TABLES))
        sql = f"""
            SELECT TABLE_NAME, TABLE_TYPE
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            AND TABLE_TYPE = 'BASE TABLE'
            AND TABLE_NAME IN ({placeholders})
            ORDER BY TABLE_NAME
        """
        cursor.execute(sql, [MYSQL_CONFIG['database']] + INCLUDE_TABLES)

        tables = cursor.fetchall()
        cursor.close()

        logger.info(f"取得したテーブル数: {len(tables)}")
        return tables
    except Exception as e:
        logger.error(f"テーブル一覧取得失敗: {e}")
        raise

def get_table_columns(mysql_conn, table_name):
    """テーブルのカラム情報を取得"""
    try:
        cursor = mysql_conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        logger.error(f"テーブル {table_name} のカラム情報取得失敗: {e}")
        raise

# ========== データ型変換 ==========

def mysql_to_sqlite_type(mysql_type):
    """MySQLデータ型をSQLiteデータ型に変換"""
    mysql_type = mysql_type.lower()

    # 数値型
    if any(x in mysql_type for x in ['int', 'integer', 'tinyint', 'smallint', 'mediumint', 'bigint']):
        return 'INTEGER'
    if any(x in mysql_type for x in ['decimal', 'numeric', 'float', 'double', 'real']):
        return 'REAL'

    # 日付・時刻型
    if any(x in mysql_type for x in ['date', 'time', 'year', 'datetime', 'timestamp']):
        return 'TEXT'

    # 文字列型
    if any(x in mysql_type for x in ['char', 'varchar', 'text', 'blob', 'enum', 'set']):
        return 'TEXT'

    # デフォルト
    return 'TEXT'

def create_sqlite_table(sqlite_conn, table_name, columns):
    """SQLiteにテーブルを作成"""
    try:
        cursor = sqlite_conn.cursor()

        # 既存テーブルを削除
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # カラム定義を作成
        column_defs = []
        for col in columns:
            col_name = col[0]
            col_type = mysql_to_sqlite_type(col[1])
            null_constraint = "" if col[2] == 'YES' else " NOT NULL"

            # デフォルト値の処理（簡略化）
            default_val = col[4]
            default_constraint = ""
            if default_val is not None and default_val != 'NULL':
                # NULLや式は除外
                if not any(x in str(default_val).upper() for x in ['CURRENT_TIMESTAMP', 'NULL']):
                    if col_type == 'TEXT':
                        default_constraint = f" DEFAULT '{default_val}'"
                    else:
                        default_constraint = f" DEFAULT {default_val}"

            column_defs.append(f"{col_name} {col_type}{null_constraint}{default_constraint}")

        create_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        cursor.execute(create_sql)
        sqlite_conn.commit()
        cursor.close()

        return True
    except Exception as e:
        logger.error(f"テーブル {table_name} の作成失敗: {e}")
        return False

# ========== データ同期 ==========

def sync_table_data(mysql_conn, sqlite_conn, table_name):
    """テーブルデータを同期（全件置き換え）"""
    try:
        # MySQLからデータを全件取得
        mysql_engine = create_engine(
            f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@"
            f"{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}?charset={MYSQL_CONFIG['charset']}"
        )

        df = pd.read_sql(f"SELECT * FROM {table_name}", mysql_engine)

        if len(df) == 0:
            logger.info(f"  データ: 0件")
            return True, 0

        # SQLiteに全件削除＆挿入
        cursor = sqlite_conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")

        # DataFrameをSQLiteに挿入
        df.to_sql(table_name, sqlite_conn, if_exists='append', index=False)

        sqlite_conn.commit()
        cursor.close()

        record_count = len(df)
        logger.info(f"  データ: {record_count:,}件")
        return True, record_count

    except Exception as e:
        logger.error(f"  データ同期失敗: {e}")
        return False, 0

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

def sync_all_tables():
    """全テーブルを同期"""
    logger.info("=" * 80)
    logger.info("KRD MySQL → SQLite 高頻度同期開始（genpinhyo使用テーブル）")
    logger.info("=" * 80)

    overall_start_time = time.time()
    mysql_conn = None
    sqlite_conn = None

    try:
        # データベース接続
        mysql_conn = get_mysql_connection()
        sqlite_conn = get_sqlite_connection()

        # 全テーブル取得
        tables = get_all_tables(mysql_conn)

        success_count = 0
        error_count = 0
        total_records = 0
        table_times = []

        # 各テーブルを処理
        for table_name, table_type in tables:
            table_start_time = time.time()

            logger.info(f"処理開始: {table_name} ({table_type})")

            try:
                # カラム情報取得
                columns = get_table_columns(mysql_conn, table_name)

                # SQLiteテーブル作成
                if not create_sqlite_table(sqlite_conn, table_name, columns):
                    error_count += 1
                    table_elapsed = time.time() - table_start_time
                    logger.info(f"  処理時間: {format_time(table_elapsed)} [失敗]")
                    continue

                # データ同期
                sync_success, record_count = sync_table_data(mysql_conn, sqlite_conn, table_name)

                table_elapsed = time.time() - table_start_time

                if sync_success:
                    success_count += 1
                    total_records += record_count
                    table_times.append((table_name, record_count, table_elapsed))
                    logger.info(f"  処理時間: {format_time(table_elapsed)} [成功]")
                else:
                    error_count += 1
                    logger.info(f"  処理時間: {format_time(table_elapsed)} [失敗]")

            except Exception as e:
                error_count += 1
                table_elapsed = time.time() - table_start_time
                logger.error(f"テーブル {table_name} の処理中にエラー: {e}")
                logger.info(f"  処理時間: {format_time(table_elapsed)} [エラー]")
                continue

        overall_elapsed = time.time() - overall_start_time

        # サマリー
        logger.info("=" * 80)
        logger.info("同期完了サマリー")
        logger.info(f"成功: {success_count} テーブル")
        logger.info(f"失敗: {error_count} テーブル")
        logger.info(f"総レコード数: {total_records:,} 件")
        logger.info(f"総処理時間: {format_time(overall_elapsed)}")
        logger.info("=" * 80)

        # 処理時間が長いテーブルTOP5
        if table_times:
            logger.info("")
            logger.info("処理時間TOP5:")
            sorted_times = sorted(table_times, key=lambda x: x[2], reverse=True)[:5]
            for i, (tname, rcount, telapsed) in enumerate(sorted_times, 1):
                logger.info(f"  {i:2d}. {tname:30s} {rcount:8,}件 {format_time(telapsed):>12s}")
            logger.info("=" * 80)

    except Exception as e:
        logger.error(f"同期処理中に致命的エラー: {e}")
        sys.exit(1)

    finally:
        # 接続を閉じる
        if mysql_conn:
            mysql_conn.close()
            logger.info("MySQL接続をクローズしました")
        if sqlite_conn:
            sqlite_conn.close()
            logger.info("SQLite接続をクローズしました")

# ========== エントリポイント ==========

if __name__ == "__main__":
    try:
        sync_all_tables()
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)
