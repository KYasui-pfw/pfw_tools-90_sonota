# -*- coding: utf-8 -*-
"""
EJシステムで特定のカラムを含むテーブルを検索するスクリプト

Usage:
    python search_column.py [カラム名]

Example:
    python search_column.py PUCH_ODR_STS_TYP
"""

import oracledb
import sys

def search_column_in_tables(column_name: str):
    """
    EJシステム(Oracle)で指定カラムを含むテーブルを検索

    Args:
        column_name: 検索するカラム名
    """
    # EJシステム接続情報
    host = '172.17.107.102'
    port = '1521'
    service_name = 'EXPJ'
    username = 'EXPJ2'
    password = 'EXPJ2'
    connection_string = f"{username}/{password}@{host}:{port}/{service_name}"

    # thick mode初期化
    try:
        oracledb.init_oracle_client()
        print("oracledb thick mode初期化完了")
    except Exception as e:
        print(f"thick mode初期化スキップ: {e}")

    try:
        with oracledb.connect(connection_string) as conn:
            cursor = conn.cursor()

            # ALL_TAB_COLUMNSから検索（EXPJ2スキーマのみ）
            query = """
                SELECT
                    OWNER,
                    TABLE_NAME,
                    COLUMN_NAME,
                    DATA_TYPE,
                    DATA_LENGTH,
                    NULLABLE
                FROM ALL_TAB_COLUMNS
                WHERE OWNER = 'EXPJ2'
                  AND UPPER(COLUMN_NAME) LIKE UPPER(:col_pattern)
                ORDER BY TABLE_NAME, COLUMN_NAME
            """

            # 完全一致検索
            cursor.execute(query, {'col_pattern': column_name})
            results = cursor.fetchall()

            if results:
                print(f"\n=== '{column_name}' を含むテーブル（完全一致）===")
                print(f"{'OWNER':<15} {'TABLE_NAME':<40} {'COLUMN_NAME':<30} {'DATA_TYPE':<15} {'LENGTH':<10} {'NULLABLE':<8}")
                print("-" * 120)
                for row in results:
                    owner, table_name, col_name, data_type, data_length, nullable = row
                    print(f"{owner:<15} {table_name:<40} {col_name:<30} {data_type:<15} {str(data_length):<10} {nullable:<8}")
                print(f"\n合計: {len(results)}件")
            else:
                print(f"\n'{column_name}' に完全一致するカラムは見つかりませんでした")

            # 部分一致検索
            cursor.execute(query, {'col_pattern': f'%{column_name}%'})
            partial_results = cursor.fetchall()

            # 完全一致以外のものを抽出
            partial_only = [r for r in partial_results if r[2].upper() != column_name.upper()]

            if partial_only:
                print(f"\n=== '{column_name}' を含むカラム（部分一致）===")
                print(f"{'OWNER':<15} {'TABLE_NAME':<40} {'COLUMN_NAME':<30} {'DATA_TYPE':<15} {'LENGTH':<10} {'NULLABLE':<8}")
                print("-" * 120)
                for row in partial_only:
                    owner, table_name, col_name, data_type, data_length, nullable = row
                    print(f"{owner:<15} {table_name:<40} {col_name:<30} {data_type:<15} {str(data_length):<10} {nullable:<8}")
                print(f"\n部分一致: {len(partial_only)}件")

    except oracledb.DatabaseError as e:
        print(f"データベースエラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # デフォルトで PUCH_ODR_STS_TYP を検索
        column_name = "PUCH_ODR_STS_TYP"
        print(f"引数なし: デフォルトで '{column_name}' を検索します")
    else:
        column_name = sys.argv[1]

    print(f"EJシステムで '{column_name}' カラムを検索中...")
    search_column_in_tables(column_name)
