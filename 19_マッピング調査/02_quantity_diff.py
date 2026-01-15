"""
01_ej_quantity_sum.csv と EXPJ2.T_RLSD_PUCH_ODR.csv を比較
同じorder_no毎のquantity差分を計算
"""
import pandas as pd
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "db")

EJ_SUM_PATH = os.path.join(DB_DIR, "01_ej_quantity_sum.csv")
EXPJ_PATH = os.path.join(DB_DIR, "EXPJ2.T_RLSD_PUCH_ODR.csv")
OUTPUT_PATH = os.path.join(DB_DIR, "02_quantity_diff.csv")
OUTPUT_EXPJ_ONLY_PATH = os.path.join(DB_DIR, "02_expj_only.csv")


def main():
    print("=" * 60)
    print("01_ej_quantity_sum.csv と EXPJ2.T_RLSD_PUCH_ODR.csv 比較")
    print("=" * 60)

    # 01_ej_quantity_sum.csv 読み込み
    df_mapping = pd.read_csv(EJ_SUM_PATH)
    print(f"01_ej_quantity_sum.csv: {len(df_mapping):,}件")

    # EXPJ2.T_RLSD_PUCH_ODR.csv 読み込み（必要カラム、cp932エンコーディング）
    df_expj = pd.read_csv(EXPJ_PATH, usecols=['PUCH_ODR_CD', 'PUCH_ODR_QTY', 'PUCH_ODR_DLV_DATE', 'PUCH_ODR_TYP'], encoding='cp932')
    print(f"EXPJ2.T_RLSD_PUCH_ODR.csv（全件）: {len(df_expj):,}件")

    # 納期を日付型に変換
    df_expj['PUCH_ODR_DLV_DATE'] = pd.to_datetime(df_expj['PUCH_ODR_DLV_DATE'], errors='coerce')

    # 2025/11/1以降のデータのみ抽出
    filter_date = pd.Timestamp('2025-11-01')
    df_expj = df_expj[df_expj['PUCH_ODR_DLV_DATE'] >= filter_date]
    print(f"EXPJ2.T_RLSD_PUCH_ODR.csv（2025/11/1以降）: {len(df_expj):,}件")

    # 不要カラムを削除
    df_expj = df_expj[['PUCH_ODR_CD', 'PUCH_ODR_QTY', 'PUCH_ODR_TYP']]

    # カラム名を統一
    df_mapping.columns = ['order_no', 'mapping_qty', 'rbom_qty']
    df_expj.columns = ['order_no', 'expj_qty', 'puch_odr_typ']

    # EXPJの数量を数値型に変換
    df_expj['expj_qty'] = pd.to_numeric(df_expj['expj_qty'], errors='coerce')

    # quantityがnullまたは0のものを除外
    df_expj = df_expj[(df_expj['expj_qty'].notna()) & (df_expj['expj_qty'] != 0)]
    print(f"EXPJ2.T_RLSD_PUCH_ODR.csv（quantity有効）: {len(df_expj):,}件")

    # マージ（両方に存在するもの、片方のみのものも含む）
    df_merged = pd.merge(df_mapping, df_expj, on='order_no', how='outer')

    # 空欄を0で埋める
    df_merged['mapping_qty'] = df_merged['mapping_qty'].fillna(0)
    df_merged['rbom_qty'] = df_merged['rbom_qty'].fillna(0)
    df_merged['expj_qty'] = df_merged['expj_qty'].fillna(0)

    # mapping側の数量がNULLまたは0のものを除外
    df_merged = df_merged[df_merged['mapping_qty'] != 0]
    print(f"マージ後（mapping_qty有効）: {len(df_merged):,}件")

    # 差分計算 (mapping_qty - expj_qty)
    df_merged['qty_diff'] = df_merged['mapping_qty'] - df_merged['expj_qty']

    # ソート（order_no昇順）
    df_merged = df_merged.sort_values('order_no')

    # CSV出力
    df_merged.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n出力完了: {OUTPUT_PATH}")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"総レコード数: {len(df_merged):,}件")
    print(f"  - 両方に存在: {len(df_merged[(df_merged['mapping_qty'] != 0) & (df_merged['expj_qty'] != 0)]):,}件")
    print(f"  - mappingのみ: {len(df_merged[(df_merged['mapping_qty'] != 0) & (df_merged['expj_qty'] == 0)]):,}件")
    print(f"  - EXPJのみ: {len(df_merged[(df_merged['mapping_qty'] == 0) & (df_merged['expj_qty'] != 0)]):,}件")

    print(f"\n差分がある件数: {len(df_merged[df_merged['qty_diff'] != 0]):,}件")
    print(f"  - mapping > expj: {len(df_merged[df_merged['qty_diff'] > 0]):,}件")
    print(f"  - mapping < expj: {len(df_merged[df_merged['qty_diff'] < 0]):,}件")
    print(f"  - 差分なし: {len(df_merged[df_merged['qty_diff'] == 0]):,}件")

    # 差分サマリー
    print(f"\n差分の統計:")
    print(f"  - 最小差分: {df_merged['qty_diff'].min():.1f}")
    print(f"  - 最大差分: {df_merged['qty_diff'].max():.1f}")
    print(f"  - 平均差分: {df_merged['qty_diff'].mean():.2f}")

    # プレビュー（差分があるもの上位10件）
    df_diff_only = df_merged[df_merged['qty_diff'] != 0].copy()
    df_diff_only = df_diff_only.sort_values('qty_diff', key=abs, ascending=False)
    print("\n--- 差分が大きいもの (上位10件) ---")
    print(df_diff_only.head(10).to_string(index=False))

    # EXPJのみに存在するデータを別途出力
    df_expj_only = df_merged[(df_merged['mapping_qty'] == 0) & (df_merged['expj_qty'] != 0)].copy()
    if len(df_expj_only) > 0:
        df_expj_only.to_csv(OUTPUT_EXPJ_ONLY_PATH, index=False, encoding='utf-8-sig')
        print(f"\n--- EXPJのみ出力 ---")
        print(f"出力完了: {OUTPUT_EXPJ_ONLY_PATH}")
        print(f"件数: {len(df_expj_only):,}件")


if __name__ == "__main__":
    main()
