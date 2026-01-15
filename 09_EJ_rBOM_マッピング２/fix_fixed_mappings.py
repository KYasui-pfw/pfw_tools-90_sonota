# -*- coding: utf-8 -*-
"""
fixed_mappingsテーブルにitem_codeカラムを追加し、
mapping_resultsから★マーク付きitem_codeをコピーする
"""
import sqlite3

db_path = r'C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\mapping.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== fixed_mappingsテーブル修正 ===\n")

# 1. item_codeカラムがあるか確認
cursor.execute("PRAGMA table_info(fixed_mappings)")
columns = [col[1] for col in cursor.fetchall()]
print(f"現在のカラム: {columns}")

if 'item_code' not in columns:
    print("\nitem_codeカラムを追加...")
    cursor.execute("ALTER TABLE fixed_mappings ADD COLUMN item_code TEXT")
    conn.commit()
    print("item_codeカラム追加完了")
else:
    print("\nitem_codeカラムは既に存在します")

# 2. mapping_resultsのis_fixed=1かつ★マーク付きのitem_codeをfixed_mappingsに反映
# ej_order_no + rbom_order_no + rbom_line_no でマッチング
cursor.execute("""
    UPDATE fixed_mappings
    SET item_code = (
        SELECT mr.item_code
        FROM mapping_results mr
        WHERE mr.ej_order_no = fixed_mappings.ej_order_no
          AND mr.rbom_order_no = fixed_mappings.rbom_order_no
          AND mr.rbom_line_no = fixed_mappings.rbom_line_no
          AND mr.is_fixed = 1
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1
        FROM mapping_results mr
        WHERE mr.ej_order_no = fixed_mappings.ej_order_no
          AND mr.rbom_order_no = fixed_mappings.rbom_order_no
          AND mr.rbom_line_no = fixed_mappings.rbom_line_no
          AND mr.is_fixed = 1
    )
""")
updated = cursor.rowcount
conn.commit()
print(f"\nitem_code更新: {updated}件")

# 3. 確認
cursor.execute("SELECT COUNT(*) FROM fixed_mappings WHERE item_code LIKE '★%'")
star_count = cursor.fetchone()[0]
print(f"fixed_mappings内の★マーク付き: {star_count}件")

cursor.execute("SELECT item_code, ej_order_no, rbom_order_no FROM fixed_mappings WHERE item_code LIKE '★%' LIMIT 5")
print("\n★マーク付きサンプル:")
for row in cursor.fetchall():
    print(f"  item_code={row[0]}, EJ={row[1]}, rBOM={row[2]}")

conn.close()
print("\n=== 完了 ===")
