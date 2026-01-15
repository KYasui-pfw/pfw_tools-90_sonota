# -*- coding: utf-8 -*-
import sqlite3

db_path = r'C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\mapping.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# mapping_resultsの★マーク付きでis_fixed=1のレコード
cursor.execute("""
    SELECT item_code, ej_order_no, rbom_order_no, rbom_line_no, is_fixed
    FROM mapping_results
    WHERE item_code LIKE '★%'
    LIMIT 10
""")
print("mapping_results ★マーク付き:")
for row in cursor.fetchall():
    print(f"  item_code={row[0]}, EJ={row[1]}, rBOM={row[2]}+{row[3]}, is_fixed={row[4]}")

# fixed_mappingsの同じEJ発注番号があるか
cursor.execute("""
    SELECT fm.ej_order_no, fm.rbom_order_no, fm.rbom_line_no, fm.item_code
    FROM fixed_mappings fm
    WHERE fm.ej_order_no IN (
        SELECT ej_order_no FROM mapping_results WHERE item_code LIKE '★%' LIMIT 5
    )
""")
print("\nfixed_mappings 対応レコード:")
for row in cursor.fetchall():
    print(f"  EJ={row[0]}, rBOM={row[1]}+{row[2]}, item_code={row[3]}")

conn.close()
