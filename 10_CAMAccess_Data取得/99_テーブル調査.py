import pypyodbc
import csv
from pathlib import Path

# データベースファイルのパス
db_path = r"C:\Dev\90_tools\10_CAMAccess_Data取得\99_材料\EJデータマスター.accdb"

# 出力ディレクトリ
output_dir = Path(r"C:\Dev\90_tools\10_CAMAccess_Data取得\90_テーブル調査")

# 出力ディレクトリが存在しない場合は作成
output_dir.mkdir(parents=True, exist_ok=True)

# Accessデータベースに接続
conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};'

try:
    conn = pypyodbc.connect(conn_str)
    cursor = conn.cursor()

    # 全テーブルのリストを取得（システムテーブルを除く）
    tables = []
    for table_info in cursor.tables(tableType='TABLE'):
        table_name = table_info.table_name
        # システムテーブル（MSys で始まるもの）を除外
        if not table_name.startswith('MSys'):
            tables.append(table_name)

    print(f"検出されたテーブル数: {len(tables)}")
    print("=" * 50)

    # 各テーブルをCSVに出力
    for table_name in tables:
        try:
            print(f"処理中: {table_name}")

            # テーブルのデータを読み取り
            query = f"SELECT * FROM [{table_name}]"
            cursor.execute(query)

            # カラム名を取得
            columns = [desc[0] for desc in cursor.description]

            # CSVファイルとして保存
            csv_filename = output_dir / f"{table_name}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # ヘッダー行を書き込み
                writer.writerow(columns)

                # データ行を書き込み
                record_count = 0
                for row in cursor.fetchall():
                    writer.writerow(row)
                    record_count += 1

            print(f"  → 出力完了: {csv_filename} (レコード数: {record_count})")

        except Exception as e:
            print(f"  → エラー: {table_name} - {str(e)}")

    print("=" * 50)
    print("全テーブルの出力が完了しました。")

except Exception as e:
    print(f"データベース接続エラー: {str(e)}")

finally:
    if 'conn' in locals():
        conn.close()
