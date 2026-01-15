# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect(r'C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\mapping.db')
cursor = conn.cursor()

# item_codeに★が付いているか確認（mapping_results）
cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE item_code LIKE ?", ('%★%',))
print(f"mapping_results item_code★付き: {cursor.fetchone()[0]}件")

cursor.execute("SELECT item_code FROM mapping_results WHERE item_code LIKE ? LIMIT 5", ('%★%',))
print("item_code★付きサンプル:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# ej_item_codeに★が付いているか確認
cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE ej_item_code LIKE ?", ('%★%',))
print(f"\nmapping_results ej_item_code★付き: {cursor.fetchone()[0]}件")

cursor.execute("SELECT ej_item_code FROM mapping_results WHERE ej_item_code LIKE ? LIMIT 5", ('%★%',))
print("ej_item_code★付きサンプル:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# is_fixed=1かつej_order_noがNone以外のもの（D3360マッピング候補）
cursor.execute("""
    SELECT COUNT(*) FROM mapping_results
    WHERE is_fixed = 1 AND ej_order_no IS NOT NULL AND rbom_order_no IS NOT NULL
""")
print(f"\nis_fixed=1かつEJ/rBOM両方あり: {cursor.fetchone()[0]}件")

# fixed_mappingsのej_order_noサンプル
cursor.execute("SELECT ej_order_no, rbom_order_no, rbom_line_no FROM fixed_mappings LIMIT 5")
print("\nfixed_mappingsサンプル:")
for row in cursor.fetchall():
    print(f"  EJ={row[0]}, rBOM={row[1]}+{row[2]}")

conn.close()
