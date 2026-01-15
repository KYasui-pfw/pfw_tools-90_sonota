"""
mapping_resultsテーブルのis_fixed=1のデータをfixed_mappingsテーブルに同期する
"""
import sqlite3

DB_PATH = r"C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\mapping.db"

def sync_fixed_mappings():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 現状確認
    cur.execute("SELECT COUNT(*) FROM mapping_results WHERE is_fixed = 1")
    mr_fixed_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM fixed_mappings")
    fm_count = cur.fetchone()[0]

    print(f"同期前:")
    print(f"  mapping_results (is_fixed=1): {mr_fixed_count}件")
    print(f"  fixed_mappings: {fm_count}件")

    # fixed_mappingsを一旦クリア
    cur.execute("DELETE FROM fixed_mappings")
    print(f"\nfixed_mappingsをクリアしました")

    # mapping_resultsのis_fixed=1のデータをfixed_mappingsに挿入
    cur.execute("""
        INSERT INTO fixed_mappings (
            ej_order_no, ej_item_code, ej_item_name, ej_quantity,
            ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
            rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
            rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd, mk020_note,
            ej_m_sequence, rbom_m_sequence, status
        )
        SELECT
            ej_order_no, ej_item_code, ej_item_name, ej_quantity,
            ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
            rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
            rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd, mk020_note,
            ej_m_sequence, rbom_m_sequence, status
        FROM mapping_results
        WHERE is_fixed = 1
    """)

    inserted_count = cur.rowcount
    print(f"fixed_mappingsに{inserted_count}件挿入しました")

    conn.commit()

    # 確認
    cur.execute("SELECT COUNT(*) FROM fixed_mappings")
    fm_count_after = cur.fetchone()[0]

    print(f"\n同期後:")
    print(f"  fixed_mappings: {fm_count_after}件")

    conn.close()
    print("\n同期完了")

if __name__ == "__main__":
    sync_fixed_mappings()
