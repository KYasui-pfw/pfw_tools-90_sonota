"""
mapping_resultsテーブルから
rbom_order_noとrbom_line_noが同じにもかかわらず、rbom_delivery_dateが異なる行を抽出
"""
import sqlite3
import pandas as pd
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "db", "mapping.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "db", "01_2_rbom_delivery_date_diff.csv")


def main():
    print("=" * 60)
    print("rbom_order_no+rbom_line_no同一でrbom_delivery_date異なる行抽出")
    print("=" * 60)

    # DB接続
    conn = sqlite3.connect(DB_PATH)

    # rbom_order_noとrbom_line_noが空欄でないデータを取得
    query = """
    SELECT
        rbom_order_no,
        rbom_line_no,
        rbom_delivery_date,
        ej_order_no,
        ej_quantity,
        rbom_quantity,
        rbom_item_code,
        rbom_item_name,
        rbom_seino
    FROM mapping_results
    WHERE rbom_order_no IS NOT NULL AND rbom_order_no != ''
      AND rbom_line_no IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"抽出件数（rbom_order_no有効）: {len(df):,}件")

    # rbom_order_no + rbom_line_no でグループ化し、rbom_delivery_dateのユニーク数をカウント
    df_grouped = df.groupby(['rbom_order_no', 'rbom_line_no']).agg({
        'rbom_delivery_date': 'nunique'
    }).reset_index()
    df_grouped.columns = ['rbom_order_no', 'rbom_line_no', 'delivery_date_count']

    # rbom_delivery_dateが2種類以上あるものを抽出
    df_diff = df_grouped[df_grouped['delivery_date_count'] > 1]
    print(f"納期が異なる組み合わせ数: {len(df_diff):,}件")

    if len(df_diff) == 0:
        print("\n該当データなし")
        return

    # 該当するrbom_order_no + rbom_line_noの詳細データを取得
    df_result = df.merge(df_diff[['rbom_order_no', 'rbom_line_no']], on=['rbom_order_no', 'rbom_line_no'])

    # ソート
    df_result = df_result.sort_values(['rbom_order_no', 'rbom_line_no', 'rbom_delivery_date'])

    # CSV出力
    df_result.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n出力完了: {OUTPUT_PATH}")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")
    print(f"出力行数: {len(df_result):,}件")

    # プレビュー
    print("\n--- データプレビュー (先頭20件) ---")
    print(df_result.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
