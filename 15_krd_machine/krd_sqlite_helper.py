"""
KRD SQLiteヘルパーモジュール

既存のkrd_data_get()関数をSQLiteベースに置き換えるためのヘルパー。
既存コードへの影響を最小限にするため、同じインターフェースを提供します。

使い方:
    既存コード:
        from module import krd_data_get
        df = krd_data_get("SELECT * FROM DATA_ASP2_PUT")

    新しいコード:
        import sys
        sys.path.append('C:/Dev/90_tools/50_tools/genpin_check/krd')
        from krd_sqlite_helper import krd_data_get
        df = krd_data_get("SELECT * FROM DATA_ASP2_PUT")
"""

import sqlite3
import pandas as pd
import os

# SQLiteデータベースのパス
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'krd_machine.db')

def krd_data_get(sql):
    """
    KRD SQLiteデータベースからデータを取得

    Parameters:
        sql (str): 実行するSQL文

    Returns:
        pd.DataFrame: クエリ結果のDataFrame

    Notes:
        - 既存のkrd_data_get()関数と同じインターフェース
        - MySQLではなくSQLiteから取得
    """
    try:
        # SQLite接続
        conn = sqlite3.connect(SQLITE_DB_PATH)

        # SQLを実行してDataFrameで取得
        df = pd.read_sql(sql, conn)

        # 接続を閉じる
        conn.close()

        return df

    except Exception as e:
        print(f"KRD SQLiteデータ取得エラー: {e}")
        print(f"SQL: {sql}")
        raise

def check_krd_sqlite_status():
    """
    KRD SQLiteデータベースの状態を確認

    Returns:
        dict: データベース情報
            - exists (bool): データベースファイルが存在するか
            - path (str): データベースファイルのパス
            - table_count (int): テーブル数
            - tables (list): テーブル一覧
    """
    status = {
        'exists': False,
        'path': SQLITE_DB_PATH,
        'table_count': 0,
        'tables': []
    }

    if not os.path.exists(SQLITE_DB_PATH):
        return status

    status['exists'] = True

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # テーブル一覧を取得
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        status['tables'] = tables
        status['table_count'] = len(tables)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"データベース状態確認エラー: {e}")

    return status

# ========== テスト用 ==========

if __name__ == "__main__":
    print("=" * 80)
    print("KRD SQLite 接続テスト")
    print("=" * 80)

    # データベース状態確認
    status = check_krd_sqlite_status()

    print(f"データベース存在: {status['exists']}")
    print(f"データベースパス: {status['path']}")
    print(f"テーブル数: {status['table_count']}")

    if status['exists']:
        print("\nテーブル一覧（先頭10件）:")
        for table in status['tables'][:10]:
            print(f"  - {table}")

        if status['table_count'] > 10:
            print(f"  ... 他 {status['table_count'] - 10} 件")

        # サンプルクエリ実行
        print("\n" + "=" * 80)
        print("サンプルクエリ実行: SELECT * FROM DATA_ASP2_PUT LIMIT 5")
        print("=" * 80)

        try:
            df = krd_data_get("SELECT * FROM DATA_ASP2_PUT LIMIT 5")
            print(f"\n取得件数: {len(df)} 件")
            print("\nカラム一覧:")
            print(df.columns.tolist())
            print("\nデータサンプル:")
            print(df)

        except Exception as e:
            print(f"\nクエリ実行エラー: {e}")

    else:
        print("\n⚠ データベースが存在しません")
        print("以下のコマンドで初回同期を実行してください:")
        print(f"  cd {os.path.dirname(__file__)}")
        print("  python krd_sync.py")
