"""
mapping_resultsテーブルのstatus列を確認するスクリプト
"""
import sqlite3
import pandas as pd

db_path = "./Database/mapping.db"

try:
    conn = sqlite3.connect(db_path)

    # ステータス別の件数を確認
    print("=" * 80)
    print("【ステータス別件数】")
    print("=" * 80)
    df_status = pd.read_sql_query(
        "SELECT status, COUNT(*) as count FROM mapping_results GROUP BY status ORDER BY status",
        conn
    )
    print(df_status.to_string(index=False))
    print()

    # 各ステータスのサンプルデータを確認（各5件）
    print("=" * 80)
    print("【ステータス='済' のサンプル（5件）】")
    print("=" * 80)
    df_done = pd.read_sql_query(
        """
        SELECT status, ej_order_no, rbom_order_no, rbom_line_no,
               ej_item_code, rbom_item_code, ej_quantity, rbom_quantity
        FROM mapping_results
        WHERE status = '済'
        LIMIT 5
        """,
        conn
    )
    print(df_done.to_string(index=False))
    print()

    print("=" * 80)
    print("【ステータス='済2' のサンプル（5件）】")
    print("=" * 80)
    df_done2 = pd.read_sql_query(
        """
        SELECT status, ej_order_no, rbom_order_no, rbom_line_no,
               ej_item_code, rbom_item_code, ej_quantity, rbom_quantity, mk020_note
        FROM mapping_results
        WHERE status = '済2'
        LIMIT 5
        """,
        conn
    )
    print(df_done2.to_string(index=False))
    print()

    print("=" * 80)
    print("【ステータス='未' のサンプル（5件）】")
    print("=" * 80)
    df_not_done = pd.read_sql_query(
        """
        SELECT status, ej_order_no, rbom_order_no, rbom_line_no,
               ej_item_code, rbom_item_code
        FROM mapping_results
        WHERE status = '未'
        LIMIT 5
        """,
        conn
    )
    print(df_not_done.to_string(index=False))
    print()

    # 空文字列やNULLのステータスをチェック
    print("=" * 80)
    print("【ステータスが空またはNULLの件数】")
    print("=" * 80)
    df_empty = pd.read_sql_query(
        """
        SELECT
            SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) as null_count,
            SUM(CASE WHEN status = '' THEN 1 ELSE 0 END) as empty_count,
            SUM(CASE WHEN status IS NULL OR status = '' THEN 1 ELSE 0 END) as total_invalid
        FROM mapping_results
        """,
        conn
    )
    print(df_empty.to_string(index=False))
    print()

    # 全レコード数
    print("=" * 80)
    print("【全レコード数】")
    print("=" * 80)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mapping_results")
    total_count = cursor.fetchone()[0]
    print(f"合計: {total_count}件")

    conn.close()
    print("\n確認完了！")

except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()
