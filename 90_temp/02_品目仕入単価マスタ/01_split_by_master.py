import pandas as pd
import os

# ファイルパス設定
BASE_DIR = r"C:\Dev\90_tools\90_temp\02_品目仕入単価マスタ"
INPUT_DIR = os.path.join(BASE_DIR, "00_input")
M0840_FILE = os.path.join(INPUT_DIR, "M0840_品目工程マスタ.csv")
MASTER_FILE = os.path.join(INPUT_DIR, "品目仕入単価マスタ.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "01_振り分け")

# 出力ディレクトリ作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CSVファイル読み込み
print("M0840_品目工程マスタ.csv を読み込んでいます...")
m0840_df = pd.read_csv(M0840_FILE, encoding='utf-8-sig')
print(f"M0840データ件数: {len(m0840_df)}")

print("品目仕入単価マスタ.csv を読み込んでいます...")
master_df = pd.read_csv(MASTER_FILE, encoding='shift_jis')
print(f"品目仕入単価マスタデータ件数: {len(master_df)}")

# M0840側で複合キー（KTCD-HMCD）を作成
m0840_df['COMPOSITE_KEY'] = m0840_df['KTCD'].astype(str) + '-' + m0840_df['HMCD'].astype(str)
print(f"M0840複合キー作成完了")

# 品目仕入単価マスタのHMCDセットを取得（重複除去）
master_hmcd_set = set(master_df['HMCD'].unique())
print(f"品目仕入単価マスタの一意なHMCD件数: {len(master_hmcd_set)}")

# M0840データを存在/非存在で振り分け（複合キーで照合）
exists_df = m0840_df[m0840_df['COMPOSITE_KEY'].isin(master_hmcd_set)].copy()
not_exists_df = m0840_df[~m0840_df['COMPOSITE_KEY'].isin(master_hmcd_set)].copy()

# 出力時は複合キー列を削除
exists_df = exists_df.drop(columns=['COMPOSITE_KEY'])
not_exists_df = not_exists_df.drop(columns=['COMPOSITE_KEY'])

print(f"\n品目仕入単価マスタに存在するデータ: {len(exists_df)}件")
print(f"品目仕入単価マスタに存在しないデータ: {len(not_exists_df)}件")

# ファイル出力
exists_file = os.path.join(OUTPUT_DIR, "品目仕入単価マスタに存在.csv")
not_exists_file = os.path.join(OUTPUT_DIR, "品目仕入単価マスタに存在しない.csv")

exists_df.to_csv(exists_file, index=False, encoding='utf-8-sig')
print(f"\n[OK] {exists_file} に出力しました")

not_exists_df.to_csv(not_exists_file, index=False, encoding='utf-8-sig')
print(f"[OK] {not_exists_file} に出力しました")

print("\n処理完了")