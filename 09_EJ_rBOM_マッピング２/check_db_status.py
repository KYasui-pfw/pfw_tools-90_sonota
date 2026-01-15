# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect(r'C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\mapping.db')
cursor = conn.cursor()

# fixed_mappings件数
cursor.execute('SELECT COUNT(*) FROM fixed_mappings')
print(f'fixed_mappings件数: {cursor.fetchone()[0]}')

# is_fixed=1件数
cursor.execute('SELECT COUNT(*) FROM mapping_results WHERE is_fixed = 1')
print(f'is_fixed=1件数: {cursor.fetchone()[0]}')

# status別件数
print('\nstatus別件数:')
cursor.execute('SELECT status, COUNT(*) FROM mapping_results GROUP BY status ORDER BY status')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# ★マーク付きitem_code確認
cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE item_code LIKE '★%'")
print(f'\n★マーク付きitem_code: {cursor.fetchone()[0]}件')

conn.close()
