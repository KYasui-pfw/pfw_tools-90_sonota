"""
未登録品目コードを既存マスタと比較して振り分けるスクリプト

入力:
  - 01_input/01_未登録813件.csv (品目コード列)
  - 01_input/02_M0840.csv (HMCD列)
  - 01_input/03_M0850.csv (OYAHMCD列)

出力:
  - 03_work/01_存在する.csv (M0840またはM0850に存在する品目コード)
  - 03_work/01_存在しない.csv (M0840とM0850のどちらにも存在しない品目コード)
"""

import pandas as pd
from pathlib import Path

# ========================================
# ディレクトリとファイルパス設定
# ========================================
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / '01_input'
WORK_DIR = BASE_DIR / '03_work'

# 入力ファイル
INPUT_CSV = INPUT_DIR / '01_未登録813件.csv'
M0840_CSV = INPUT_DIR / '02_M0840.csv'
M0850_CSV = INPUT_DIR / '03_M0850.csv'

# 出力ファイル
OUTPUT_EXIST = WORK_DIR / '01_存在する.csv'
OUTPUT_NOT_EXIST = WORK_DIR / '01_存在しない.csv'

# ワークディレクトリ作成
WORK_DIR.mkdir(exist_ok=True)


def main():
    """メイン処理"""
    print("=" * 60)
    print("品目コード存在チェック・振り分け処理")
    print("=" * 60)

    # 1. 未登録品目コードを読み込み
    print(f"読み込み中: {INPUT_CSV.name}")
    df_input = pd.read_csv(INPUT_CSV, dtype=str)

    # 列名確認（品目コード列）
    if '品目コード' not in df_input.columns:
        raise ValueError(f"'品目コード'列が見つかりません: {INPUT_CSV}")

    # 品目コードをセットに変換（前後の空白をtrim）
    input_codes = set(df_input['品目コード'].str.strip())
    print(f"  → 未登録品目コード件数: {len(input_codes)}")

    # 2. M0840のHMCDを読み込み（trim処理）
    print(f"読み込み中: {M0840_CSV.name}")
    df_m0840 = pd.read_csv(M0840_CSV, dtype=str, encoding='shift-jis')

    if 'HMCD' not in df_m0840.columns:
        raise ValueError(f"'HMCD'列が見つかりません: {M0840_CSV}")

    # HMCDをtrimしてセットに変換
    m0840_codes = set(df_m0840['HMCD'].str.strip())
    print(f"  → M0840のHMCD件数: {len(m0840_codes)}")

    # 3. M0850のOYAHMCDを読み込み（trim処理）
    print(f"読み込み中: {M0850_CSV.name}")
    df_m0850 = pd.read_csv(M0850_CSV, dtype=str, encoding='shift-jis')

    if 'OYAHMCD' not in df_m0850.columns:
        raise ValueError(f"'OYAHMCD'列が見つかりません: {M0850_CSV}")

    # OYAHMCDをtrimしてセットに変換
    m0850_codes = set(df_m0850['OYAHMCD'].str.strip())
    print(f"  → M0850のOYAHMCD件数: {len(m0850_codes)}")

    # 4. M0840とM0850の品目コードを統合
    existing_codes = m0840_codes | m0850_codes
    print(f"  → M0840/M0850の統合品目コード件数: {len(existing_codes)}")

    # 5. 存在チェック
    exist_codes = input_codes & existing_codes
    not_exist_codes = input_codes - existing_codes

    print()
    print(f"存在する品目コード件数: {len(exist_codes)}")
    print(f"存在しない品目コード件数: {len(not_exist_codes)}")

    # 6. 結果をCSVに出力
    print()
    # 存在する品目コード
    if exist_codes:
        df_exist = pd.DataFrame({'品目コード': sorted(exist_codes)})
        df_exist.to_csv(OUTPUT_EXIST, index=False, encoding='utf-8-sig')
        print(f"  → 出力完了: {OUTPUT_EXIST.name} ({len(exist_codes)}件)")
    else:
        print(f"  → 存在する品目コードなし")

    # 存在しない品目コード
    if not_exist_codes:
        df_not_exist = pd.DataFrame({'品目コード': sorted(not_exist_codes)})
        df_not_exist.to_csv(OUTPUT_NOT_EXIST, index=False, encoding='utf-8-sig')
        print(f"  → 出力完了: {OUTPUT_NOT_EXIST.name} ({len(not_exist_codes)}件)")
    else:
        print(f"  → 存在しない品目コードなし")

    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)


if __name__ == '__main__':
    main()
