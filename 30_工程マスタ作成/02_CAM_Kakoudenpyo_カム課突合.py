# -*- coding: utf-8 -*-
"""
02_CAM_Kakoudenpyo_カム課突合.py
CAMKakouDenpyo.csvの伝票Noをキーに、全カム課加工検討データから項目を追記

カム課_伝票データ有無:
- 有り: 伝票Noで一致し、子部番が5文字以上
- 子部番無し: 伝票Noで一致したが、子部番が4文字以下 → 部品名で5文字以上を再検索
- 無し: 伝票No不一致 → 部品名で検索（子部番5文字以上を優先）
"""

import pandas as pd
from pathlib import Path
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# 入力ファイル
INPUT_CSV = Path(r"C:\Dev\90_tools\30_工程マスタ作成\01_KakouDenpyo\4-01 CAMKakouDenpyo.csv")
MASTER_XLSX = Path(r"C:\Dev\90_tools\30_工程マスタ作成\02_カム課\全カム課加工検討データ.xlsx")

# 出力先
OUTPUT_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work")
OUTPUT_CSV = OUTPUT_DIR / "4-01 CAMKakouDenpyo_カム課付き.csv"

# 突合キー
KEY_CSV = "伝票Ｎｏ"
KEY_MASTER = "ロットコード"

# 追記する項目
APPEND_COLS = ["月次", "子部番", "孫部番", "部品名", "工程"]

# 子部番の有効判定（5文字以上）
MIN_KOBUBAN_LENGTH = 5


def is_valid_kobuban(kobuban) -> bool:
    """子部番が有効か判定
    無効パターン:
    - 4文字以下
    - * で始まる（*、*【数字】など）
    - キャンセル待ち
    - 数字/数字次纏めて（例: 6/7次纏めて）
    - 数字月部品と纏めて（例: 3月部品と纏めて）
    - ﾃﾞｰﾀ納期 で始まる
    - 内作-PT依頼 で始まる
    - ﾌﾗｲｽは1Fﾄﾗｯｸﾔｰﾄﾞのﾊﾟﾚｯﾄの上へお願いします で始まる
    """
    if kobuban is None:
        return False
    s = str(kobuban).strip()
    if s == '' or s == 'nan':
        return False

    # 4文字以下は無効
    if len(s) < MIN_KOBUBAN_LENGTH:
        return False

    # * で始まるパターン（半角・全角両方）
    if s.startswith('*') or s.startswith('＊'):
        return False

    # 【】で始まるパターン（【22】、【28】など）
    if s.startswith('【'):
        return False

    # キャンセル待ち
    if s == 'キャンセル待ち':
        return False

    # 数字/数字次纏めて パターン（例: 6/7次纏めて, 1/2/3次纏めて, 1/3次纏めて【24】）
    if re.match(r'^\d+([/／]\d+)+次纏めて', s):
        return False

    # 数字月部品と纏めて パターン（例: 3月部品と纏めて）
    if re.match(r'^\d+月部品と纏めて$', s):
        return False

    # 特定の文言で始まる場合
    invalid_prefixes = [
        'ﾃﾞｰﾀ納期',
        '内作-PT依頼',
        'ﾌﾗｲｽは1Fﾄﾗｯｸﾔｰﾄﾞのﾊﾟﾚｯﾄの上へお願いします',
    ]
    for prefix in invalid_prefixes:
        if s.startswith(prefix):
            return False

    return True


def find_valid_kobuban_data(buhinmei: str, master_by_buhinmei: dict, exclude_zaiko: bool = False) -> dict | None:
    """部品名で検索し、子部番が有効なデータを返す（月次降順で最初に見つかったもの）

    Args:
        buhinmei: 部品名
        master_by_buhinmei: 部品名→データリストの辞書
        exclude_zaiko: Trueの場合、工程が「在庫」のデータを除外
    """
    if buhinmei not in master_by_buhinmei:
        return None

    for data in master_by_buhinmei[buhinmei]:
        if is_valid_kobuban(data["子部番"]):
            if exclude_zaiko:
                kotei = str(data["工程"]).strip() if data["工程"] is not None else ""
                if kotei == "在庫":
                    continue
            return data

    # 有効なデータがなければNone
    return None


def main():
    print("=" * 60)
    print("02_CAM_Kakoudenpyo_カム課突合")
    print(f"入力CSV: {INPUT_CSV}")
    print(f"マスタ: {MASTER_XLSX}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # 入力CSV読み込み
    print("\n入力CSV読み込み...")
    df_input = pd.read_csv(INPUT_CSV, encoding='cp932')
    print(f"  行数: {len(df_input)}")
    print(f"  伝票Ｎｏユニーク数: {df_input[KEY_CSV].nunique()}")

    # マスタ読み込み
    print("\nマスタ読み込み...")
    df_master = pd.read_excel(MASTER_XLSX)
    print(f"  行数: {len(df_master)}")
    print(f"  ロットコードユニーク数: {df_master[KEY_MASTER].nunique()}")

    # マスタを辞書化（ロットコード → 項目）
    master_by_lotcode = {}
    for _, row in df_master.iterrows():
        key = str(row[KEY_MASTER]).strip()
        if key and key != 'nan':
            if key not in master_by_lotcode:
                master_by_lotcode[key] = {col: row[col] for col in APPEND_COLS}

    print(f"  ロットコード辞書件数: {len(master_by_lotcode)}")

    # 部品名でグループ化（月次降順でソート）
    print("\n部品名インデックス作成...")
    df_master_sorted = df_master.sort_values("月次", ascending=False)
    master_by_buhinmei = {}
    for _, row in df_master_sorted.iterrows():
        buhinmei = str(row["部品名"]).strip()
        if buhinmei and buhinmei != 'nan':
            if buhinmei not in master_by_buhinmei:
                master_by_buhinmei[buhinmei] = []
            master_by_buhinmei[buhinmei].append({col: row[col] for col in APPEND_COLS})

    print(f"  部品名ユニーク数: {len(master_by_buhinmei)}")

    # 突合
    print("\n突合処理...")
    result_df = df_input.copy()

    # 追記列を初期化
    result_df["カム課_伝票データ有無"] = None
    result_df["カム課_月次"] = None
    for col in ["子部番", "孫部番", "部品名", "工程"]:
        result_df[f"カム課_{col}"] = None

    count_ari = 0
    count_kobuban_nashi = 0
    count_zaiko = 0
    count_nashi = 0
    count_no_match = 0

    for idx, row in result_df.iterrows():
        denpyo_no = str(row[KEY_CSV]).strip()
        buhinmei = str(row["部品名"]).strip()

        if denpyo_no in master_by_lotcode:
            # 伝票Noで一致
            master_row = master_by_lotcode[denpyo_no]

            # 工程が「在庫」の場合は過去を検索
            kotei = str(master_row["工程"]).strip() if master_row["工程"] is not None else ""
            if kotei == "在庫":
                result_df.at[idx, "カム課_伝票データ有無"] = "在庫のため過去を検索"

                valid_data = find_valid_kobuban_data(buhinmei, master_by_buhinmei, exclude_zaiko=True)
                if valid_data:
                    result_df.at[idx, "カム課_月次"] = valid_data["月次"]
                    for col in ["子部番", "孫部番", "部品名", "工程"]:
                        result_df.at[idx, f"カム課_{col}"] = valid_data[col]
                else:
                    # 有効なデータが見つからない場合は元のデータをセット + 子部番に追記
                    result_df.at[idx, "カム課_月次"] = master_row["月次"]
                    for col in ["孫部番", "部品名", "工程"]:
                        result_df.at[idx, f"カム課_{col}"] = master_row[col]
                    kobuban_val = str(master_row["子部番"]).strip() if master_row["子部番"] is not None and str(master_row["子部番"]).strip() != 'nan' else ""
                    result_df.at[idx, "カム課_子部番"] = f"{kobuban_val}【過去に同様の部番無し】"
                count_zaiko += 1
            elif is_valid_kobuban(master_row["子部番"]):
                # 子部番が5文字以上 → 有り
                result_df.at[idx, "カム課_伝票データ有無"] = "有り"
                result_df.at[idx, "カム課_月次"] = master_row["月次"]
                for col in ["子部番", "孫部番", "部品名", "工程"]:
                    result_df.at[idx, f"カム課_{col}"] = master_row[col]
                count_ari += 1
            else:
                # 子部番が4文字以下 → 子部番無し、部品名で再検索
                result_df.at[idx, "カム課_伝票データ有無"] = "子部番無し"

                valid_data = find_valid_kobuban_data(buhinmei, master_by_buhinmei)
                if valid_data:
                    result_df.at[idx, "カム課_月次"] = valid_data["月次"]
                    for col in ["子部番", "孫部番", "部品名", "工程"]:
                        result_df.at[idx, f"カム課_{col}"] = valid_data[col]
                else:
                    # 有効なデータが見つからない場合は元のデータをセット + 子部番に追記
                    result_df.at[idx, "カム課_月次"] = master_row["月次"]
                    for col in ["孫部番", "部品名", "工程"]:
                        result_df.at[idx, f"カム課_{col}"] = master_row[col]
                    kobuban_val = str(master_row["子部番"]).strip() if master_row["子部番"] is not None and str(master_row["子部番"]).strip() != 'nan' else ""
                    result_df.at[idx, "カム課_子部番"] = f"{kobuban_val}【過去に同様の部番無し】"
                count_kobuban_nashi += 1
        else:
            # 伝票Noで不一致 → 無し、部品名で検索
            result_df.at[idx, "カム課_伝票データ有無"] = "無し"

            # 有効な子部番を持つデータを探す（在庫は除外）
            valid_data = find_valid_kobuban_data(buhinmei, master_by_buhinmei, exclude_zaiko=True)
            if valid_data:
                result_df.at[idx, "カム課_月次"] = valid_data["月次"]
                for col in ["子部番", "孫部番", "部品名", "工程"]:
                    result_df.at[idx, f"カム課_{col}"] = valid_data[col]
                count_nashi += 1
            elif buhinmei in master_by_buhinmei:
                # 有効なデータがない場合は最新のデータをセット + 子部番に追記
                first_data = master_by_buhinmei[buhinmei][0]
                result_df.at[idx, "カム課_月次"] = first_data["月次"]
                for col in ["孫部番", "部品名", "工程"]:
                    result_df.at[idx, f"カム課_{col}"] = first_data[col]
                kobuban_val = str(first_data["子部番"]).strip() if first_data["子部番"] is not None and str(first_data["子部番"]).strip() != 'nan' else ""
                result_df.at[idx, "カム課_子部番"] = f"{kobuban_val}【過去に同様の部番無し】"
                count_nashi += 1
            else:
                count_no_match += 1

    print(f"  有り: {count_ari}件")
    print(f"  子部番無し: {count_kobuban_nashi}件")
    print(f"  在庫のため過去を検索: {count_zaiko}件")
    print(f"  無し: {count_nashi}件")
    print(f"  不一致: {count_no_match}件")

    # 不一致の部品名サンプル
    no_match_rows = result_df[result_df["カム課_月次"].isna()]
    if len(no_match_rows) > 0:
        no_match_buhinmei = no_match_rows["部品名"].unique()
        print(f"  不一致の部品名ユニーク数: {len(no_match_buhinmei)}")
        print(f"  不一致サンプル: {list(no_match_buhinmei[:5])}")

    # 出力
    result_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n出力: {OUTPUT_CSV}")
    print(f"  行数: {len(result_df)}")

    print("=" * 60)


if __name__ == "__main__":
    main()
