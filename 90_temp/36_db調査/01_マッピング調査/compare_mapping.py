"""
マッピングデータ比較スクリプト

比較対象:
- mapping_results.xlsx [マッピングデータ] シート
- 発注情報EJとrBOM.xlsx [Sheet1] シート

比較項目: EJ発注番号 + rBOM発注番号+行番号 の組み合わせ
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 設定
BASE_DIR = Path(__file__).parent
MAPPING_RESULTS = BASE_DIR / "mapping_results.xlsx"
HACCHU_INFO = BASE_DIR / "発注情報EJとrBOM.xlsx"
OUTPUT_DIR = BASE_DIR

# 列名
COL_EJ_ORDER = "EJ発注番号"
COL_RBOM_ORDER_LINE = "rBOM発注番号+行番号"


def load_mapping_results():
    """mapping_results.xlsx [マッピングデータ] を読み込み"""
    df = pd.read_excel(MAPPING_RESULTS, sheet_name="マッピングデータ")
    print(f"mapping_results.xlsx 読み込み完了: {len(df)}行")
    return df


def load_hacchu_info():
    """発注情報EJとrBOM.xlsx [Sheet1] を読み込み"""
    df = pd.read_excel(HACCHU_INFO, sheet_name="Sheet1")
    print(f"発注情報EJとrBOM.xlsx 読み込み完了: {len(df)}行")
    return df


def create_key(row):
    """EJ発注番号 + rBOM発注番号+行番号 の組み合わせキーを作成"""
    ej = str(row[COL_EJ_ORDER]).strip() if pd.notna(row[COL_EJ_ORDER]) else ""
    rbom = str(row[COL_RBOM_ORDER_LINE]).strip() if pd.notna(row[COL_RBOM_ORDER_LINE]) else ""
    return f"{ej}|{rbom}"


def compare_mappings():
    """マッピングデータを比較"""
    print("=" * 60)
    print("マッピングデータ比較")
    print("=" * 60)

    # データ読み込み
    df_mapping = load_mapping_results()
    df_hacchu = load_hacchu_info()

    # キー列の存在確認
    print(f"\n[mapping_results] 列: {COL_EJ_ORDER}, {COL_RBOM_ORDER_LINE}")
    print(f"[発注情報] 列: {COL_EJ_ORDER}, {COL_RBOM_ORDER_LINE}")

    # キー作成
    df_mapping["_key"] = df_mapping.apply(create_key, axis=1)
    df_hacchu["_key"] = df_hacchu.apply(create_key, axis=1)

    # 片方でも空欄の場合は除外（両方に値がある組み合わせのみ比較）
    def is_valid_key(key):
        parts = key.split("|")
        return len(parts) == 2 and parts[0] != "" and parts[1] != ""

    df_mapping_valid = df_mapping[df_mapping["_key"].apply(is_valid_key)]
    df_hacchu_valid = df_hacchu[df_hacchu["_key"].apply(is_valid_key)]

    # mapping_results: EJ数が0の行を除外
    if "EJ数" in df_mapping_valid.columns:
        before_count = len(df_mapping_valid)
        df_mapping_valid = df_mapping_valid[df_mapping_valid["EJ数"] != 0]
        print(f"[mapping_results] EJ数=0 を除外: {before_count} → {len(df_mapping_valid)}")

    print(f"\n[mapping_results] 有効キー数: {len(df_mapping_valid)}")
    print(f"[発注情報] 有効キー数: {len(df_hacchu_valid)}")

    # セット化して比較
    set_mapping = set(df_mapping_valid["_key"])
    set_hacchu = set(df_hacchu_valid["_key"])

    # 差異計算
    only_in_mapping = set_mapping - set_hacchu  # mapping_resultsにのみ存在
    only_in_hacchu = set_hacchu - set_mapping   # 発注情報にのみ存在
    common = set_mapping & set_hacchu           # 両方に存在

    print("\n" + "-" * 40)
    print("比較結果")
    print("-" * 40)
    print(f"両方に存在: {len(common)}件")
    print(f"mapping_resultsにのみ存在: {len(only_in_mapping)}件")
    print(f"発注情報にのみ存在: {len(only_in_hacchu)}件")

    # 結果をDataFrameに変換
    results = {
        "only_in_mapping": df_mapping_valid[df_mapping_valid["_key"].isin(only_in_mapping)],
        "only_in_hacchu": df_hacchu_valid[df_hacchu_valid["_key"].isin(only_in_hacchu)],
        "common": df_mapping_valid[df_mapping_valid["_key"].isin(common)]
    }

    return results, only_in_mapping, only_in_hacchu, common


def compare_same_ej_different_rbom(results):
    """同じEJ発注番号で、rBOM発注番号+行番号が異なるデータを比較"""
    print("\n" + "-" * 40)
    print("同一EJ発注番号の差異分析")
    print("-" * 40)

    df_only_mapping = results["only_in_mapping"].copy()
    df_only_hacchu = results["only_in_hacchu"].copy()

    if df_only_mapping.empty or df_only_hacchu.empty:
        print("比較対象データがありません")
        return pd.DataFrame()

    # EJ発注番号でマージ
    df_only_mapping_subset = df_only_mapping[[COL_EJ_ORDER, COL_RBOM_ORDER_LINE]].copy()
    df_only_mapping_subset.columns = [COL_EJ_ORDER, "rBOM_mapping"]

    df_only_hacchu_subset = df_only_hacchu[[COL_EJ_ORDER, COL_RBOM_ORDER_LINE]].copy()
    df_only_hacchu_subset.columns = [COL_EJ_ORDER, "rBOM_発注情報"]

    # 同じEJ発注番号でマージ
    merged = pd.merge(
        df_only_mapping_subset,
        df_only_hacchu_subset,
        on=COL_EJ_ORDER,
        how="inner"
    )

    print(f"同一EJ発注番号で異なるrBOM: {len(merged)}件")

    if not merged.empty:
        print("\n【サンプル（最大10件）】")
        print(merged.head(10).to_string(index=False))

    return merged


def export_results(results, only_in_mapping, only_in_hacchu, common):
    """結果をExcelに出力"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"比較結果_{timestamp}.xlsx"

    # 同一EJ発注番号の差異分析
    same_ej_diff = compare_same_ej_different_rbom(results)

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # サマリーシート
        summary_data = {
            "項目": [
                "両方に存在",
                "mapping_resultsにのみ存在",
                "発注情報にのみ存在",
                "同一EJ発注番号で異なるrBOM"
            ],
            "件数": [
                len(common),
                len(only_in_mapping),
                len(only_in_hacchu),
                len(same_ej_diff)
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="サマリー", index=False)

        # 同一EJ発注番号で異なるrBOM
        if not same_ej_diff.empty:
            same_ej_diff.to_excel(writer, sheet_name="同一EJで異なるrBOM", index=False)

        # mapping_resultsにのみ存在
        if not results["only_in_mapping"].empty:
            results["only_in_mapping"].drop(columns=["_key"]).to_excel(
                writer, sheet_name="mapping_resultsのみ", index=False
            )

        # 発注情報にのみ存在
        if not results["only_in_hacchu"].empty:
            results["only_in_hacchu"].drop(columns=["_key"]).to_excel(
                writer, sheet_name="発注情報のみ", index=False
            )

        # 両方に存在（参考）
        if not results["common"].empty:
            common_df = results["common"].drop(columns=["_key"])
            common_df.to_excel(writer, sheet_name="両方に存在", index=False)

    print(f"\n出力完了: {output_file}")
    return output_file


def main():
    results, only_in_mapping, only_in_hacchu, common = compare_mappings()
    export_results(results, only_in_mapping, only_in_hacchu, common)
    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
