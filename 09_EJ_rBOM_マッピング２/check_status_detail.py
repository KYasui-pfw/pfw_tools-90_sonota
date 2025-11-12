"""
空のstatusレコードの詳細を確認するスクリプト
"""
import sqlite3
import pandas as pd

db_path = "./Database/mapping.db"

try:
    conn = sqlite3.connect(db_path)

    # 空のstatusレコードのマッピング状態を確認
    print("=" * 80)
    print("【空のstatusレコードの分析】")
    print("=" * 80)

    df_empty_detail = pd.read_sql_query(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN ej_order_no IS NOT NULL AND rbom_order_no IS NOT NULL THEN 1 ELSE 0 END) as both_exist,
            SUM(CASE WHEN ej_order_no IS NOT NULL AND rbom_order_no IS NULL THEN 1 ELSE 0 END) as ej_only,
            SUM(CASE WHEN ej_order_no IS NULL AND rbom_order_no IS NOT NULL THEN 1 ELSE 0 END) as rbom_only
        FROM mapping_results
        WHERE status = ''
        """,
        conn
    )
    print("空のstatusレコードの内訳:")
    print(df_empty_detail.to_string(index=False))
    print()

    # 空のstatusで両方存在するレコード（本来は'済'または'済2'のはず）のサンプル
    print("=" * 80)
    print("【status='' かつ EJ/rBOM両方存在（本来マッチしているはず）】")
    print("=" * 80)
    df_both = pd.read_sql_query(
        """
        SELECT status, ej_order_no, rbom_order_no, rbom_line_no,
               ej_item_code, rbom_item_code, ej_quantity, rbom_quantity,
               mapping_type, is_fixed, mk020_note
        FROM mapping_results
        WHERE status = ''
          AND ej_order_no IS NOT NULL
          AND rbom_order_no IS NOT NULL
        LIMIT 10
        """,
        conn
    )
    print(df_both.to_string(index=False))
    print(f"\n該当件数: {len(pd.read_sql_query('SELECT * FROM mapping_results WHERE status = \"\" AND ej_order_no IS NOT NULL AND rbom_order_no IS NOT NULL', conn))}件")
    print()

    # EJのみのサンプル
    print("=" * 80)
    print("【status='' かつ EJのみ存在（本来'未'のはず）】")
    print("=" * 80)
    df_ej = pd.read_sql_query(
        """
        SELECT status, ej_order_no, ej_item_code, ej_quantity
        FROM mapping_results
        WHERE status = ''
          AND ej_order_no IS NOT NULL
          AND rbom_order_no IS NULL
        LIMIT 10
        """,
        conn
    )
    print(df_ej.to_string(index=False))
    print(f"\n該当件数: {len(pd.read_sql_query('SELECT * FROM mapping_results WHERE status = \"\" AND ej_order_no IS NOT NULL AND rbom_order_no IS NULL', conn))}件")
    print()

    # rBOMのみのサンプル
    print("=" * 80)
    print("【status='' かつ rBOMのみ存在（本来'未'のはず）】")
    print("=" * 80)
    df_rbom = pd.read_sql_query(
        """
        SELECT status, rbom_order_no, rbom_line_no, rbom_item_code, rbom_quantity
        FROM mapping_results
        WHERE status = ''
          AND ej_order_no IS NULL
          AND rbom_order_no IS NOT NULL
        LIMIT 10
        """,
        conn
    )
    print(df_rbom.to_string(index=False))
    print(f"\n該当件数: {len(pd.read_sql_query('SELECT * FROM mapping_results WHERE status = \"\" AND ej_order_no IS NULL AND rbom_order_no IS NOT NULL', conn))}件")

    conn.close()
    print("\n確認完了！")

except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()
