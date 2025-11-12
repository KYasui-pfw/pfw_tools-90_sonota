import jaydebeapi
import pandas as pd
import os

# --- 設定 ---
# コンテナ内のデータパス (docker runコマンドでマウントする)
INPUT_DIR = "/app/data"
OUTPUT_DIR = "/app/output"

# 抽出対象のデータベースとテーブルの定義
TARGET_DATABASES = [
    {
        "db_file": "Cyl_pfw_table.accdb",
        "table_name": "KaLstCyl_All",
        "output_prefix": "Cyl_pfw_table"
    },
    {
        "db_file": "EJデータマスター.accdb",
        "table_name": "CAMFIN_LOG_ALL",
        "output_prefix": "EJデータマスター"
    }
]

# --- UCanAccess 接続情報 ---
# コンテナ内のjarファイルのパス
ucanaccess_dir = "/app/ucanaccess_lib"
jars = [
    os.path.join(ucanaccess_dir, jar_file) for jar_file in os.listdir(ucanaccess_dir)
]
classpath = ":".join(jars)
driver = 'net.ucanaccess.jdbc.UcanaccessDriver'

# --- メイン処理 ---
# outputフォルダが存在しない場合は作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

success_count = 0
error_count = 0

print("=== Access データベース抽出処理を開始します ===\n")

for idx, target in enumerate(TARGET_DATABASES, 1):
    db_file = target["db_file"]
    table_name = target["table_name"]
    output_prefix = target["output_prefix"]

    db_file_path = os.path.join(INPUT_DIR, db_file)
    conn_str = f"jdbc:ucanaccess://{db_file_path}"
    conn = None

    try:
        print(f"[{idx}/{len(TARGET_DATABASES)}] データベースに接続しています: {db_file}")
        conn = jaydebeapi.connect(driver, conn_str, {}, jars=classpath)
        print(f"  ✓ 接続に成功しました。")

        print(f"  テーブル '{table_name}' を処理中...")

        # テーブルからデータを取得（Access/UCanAccessでは角カッコを使用）
        query = f'SELECT * FROM [{table_name}]'
        df = pd.read_sql_query(query, conn)

        # CSVファイルとして出力（項目名付き）
        output_filename = f"{output_prefix}_{table_name}.csv"
        output_file = os.path.join(OUTPUT_DIR, output_filename)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"  ✓ {len(df)}件のデータを出力しました: {output_filename}\n")
        success_count += 1

    except Exception as e:
        print(f"  ✗ エラー: {e}\n")
        error_count += 1
        import traceback
        traceback.print_exc()

    finally:
        if conn:
            conn.close()

print(f"=== 処理完了 ===")
print(f"成功: {success_count}テーブル")
print(f"失敗: {error_count}テーブル")
print(f"出力先: {OUTPUT_DIR}")
