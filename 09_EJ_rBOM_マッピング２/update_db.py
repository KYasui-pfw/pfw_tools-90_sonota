# -*- coding: utf-8 -*-
"""
データベース更新スクリプト
1. 済3 → 済 に変更（D3360マッピング）
2. 済3だったレコードのitem_codeに★マークを付与
3. is_fixed=1のレコードをfixed_mappingsにコピー
"""
import sqlite3

db_path = r'C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\mapping.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== データベース更新開始 ===\n")

# 1. 済3のレコード数を確認
cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE status = '済3'")
sumi3_count = cursor.fetchone()[0]
print(f"済3のレコード数: {sumi3_count}件")

# 2. 済3のitem_codeに★マークを付与（まだ付いていないもの）
cursor.execute("""
    UPDATE mapping_results
    SET item_code = '★' || item_code
    WHERE status = '済3' AND item_code NOT LIKE '★%'
""")
star_added = cursor.rowcount
print(f"★マーク付与: {star_added}件")

# 3. 済3 → 済 に変更
cursor.execute("""
    UPDATE mapping_results
    SET status = '済'
    WHERE status = '済3'
""")
status_updated = cursor.rowcount
print(f"済3→済 更新: {status_updated}件")

# 4. fixed_mappingsを空にする
cursor.execute("DELETE FROM fixed_mappings")
print(f"\nfixed_mappingsをクリア")

# 5. is_fixed=1のレコードをfixed_mappingsにコピー
cursor.execute("""
    INSERT INTO fixed_mappings (
        ej_order_no, ej_item_code, ej_item_name, ej_quantity,
        ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
        rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
        rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd,
        mk020_note, ej_m_sequence, rbom_m_sequence, status,
        created_at, updated_at
    )
    SELECT
        ej_order_no, ej_item_code, ej_item_name, ej_quantity,
        ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
        rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
        rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd,
        mk020_note, ej_m_sequence, rbom_m_sequence, status,
        created_at, updated_at
    FROM mapping_results
    WHERE is_fixed = 1
""")
fixed_copied = cursor.rowcount
print(f"fixed_mappingsにコピー: {fixed_copied}件")

conn.commit()

# 確認
print("\n=== 更新後の状態 ===")
cursor.execute("SELECT COUNT(*) FROM fixed_mappings")
print(f"fixed_mappings件数: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE is_fixed = 1")
print(f"is_fixed=1件数: {cursor.fetchone()[0]}")

cursor.execute("SELECT status, COUNT(*) FROM mapping_results GROUP BY status ORDER BY status")
print("\nstatus別件数:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE item_code LIKE '★%'")
print(f"\n★マーク付きitem_code: {cursor.fetchone()[0]}件")

conn.close()
print("\n=== 完了 ===")
