"""
rbom_order_noが同じにもかかわらず、
（済、済2、手）のいずれかのstatusと、未のstatusの行が混在しているデータを抽出
"""
import sqlite3
import pandas as pd
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "db", "mapping.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "db", "01_rbom_order_status_mix.csv")


def main():
    print("=" * 60)
    print("rbom_order_no同一でstatus混在（済/済2/手 と 未）データ抽出")
    print("=" * 60)

    # DB接続
    conn = sqlite3.connect(DB_PATH)

    # rbom_order_noが有効なデータを取得
    query = """
    SELECT
        rbom_order_no,
        rbom_line_no,
        ej_order_no,
        ej_quantity,
        rbom_quantity,
        rbom_item_code,
        rbom_item_name,
        rbom_delivery_date,
        rbom_seino,
        status
    FROM mapping_results
    WHERE rbom_order_no IS NOT NULL AND rbom_order_no != ''
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"抽出件数（rbom_order_no有効）: {len(df):,}件")

    # status別件数
    print("\nstatus別件数:")
    status_counts = df['status'].value_counts(dropna=False)
    for status, count in status_counts.items():
        print(f"  {status}: {count:,}件")

    # rbom_order_no毎に、statusの種類を確認
    # 済/済2/手 のいずれかがあるか
    df['is_mapped'] = df['status'].isin(['済', '済2', '手'])
    # 未 があるか
    df['is_unmapped'] = df['status'] == '未'

    # rbom_order_no毎に集計
    df_grouped = df.groupby('rbom_order_no').agg({
        'is_mapped': 'any',
        'is_unmapped': 'any'
    }).reset_index()

    # 両方がTrueのrbom_order_noを抽出（混在）
    df_mixed = df_grouped[(df_grouped['is_mapped'] == True) & (df_grouped['is_unmapped'] == True)]
    print(f"\nstatus混在のrbom_order_no数: {len(df_mixed):,}件")

    if len(df_mixed) == 0:
        print("\n該当データなし")
        return

    # 該当するrbom_order_noの詳細データを取得
    df_result = df[df['rbom_order_no'].isin(df_mixed['rbom_order_no'])]

    # 不要なカラムを削除
    df_result = df_result.drop(columns=['is_mapped', 'is_unmapped'])

    # ソート
    df_result = df_result.sort_values(['rbom_order_no', 'rbom_line_no', 'status'])

    # CSV出力
    df_result.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n出力完了: {OUTPUT_PATH}")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")
    print(f"出力行数: {len(df_result):,}件")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"混在rbom_order_no数: {len(df_mixed):,}件")
    print(f"該当行数: {len(df_result):,}件")

    # 混在データ内のstatus別件数
    print("\n混在データ内のstatus別件数:")
    result_status_counts = df_result['status'].value_counts(dropna=False)
    for status, count in result_status_counts.items():
        print(f"  {status}: {count:,}件")

    # プレビュー
    print("\n--- データプレビュー (先頭20件) ---")
    print(df_result.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
