"""
mapping_resultsテーブルからej_order_no毎のej_quantity合計を抽出
"""
import sqlite3
import pandas as pd
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "db", "mapping.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "db", "01_ej_quantity_sum.csv")


def main():
    print("=" * 60)
    print("ej_order_no毎のej_quantity合計抽出")
    print("=" * 60)

    # DB接続
    conn = sqlite3.connect(DB_PATH)

    # データ取得（ej_order_noが空欄でないもの）
    query = """
    SELECT ej_order_no, ej_quantity, rbom_quantity, rbom_order_no, rbom_line_no
    FROM mapping_results
    WHERE ej_order_no IS NOT NULL AND ej_order_no != ''
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"抽出件数: {len(df):,}件")

    # 重複行を削除（ej_order_no + rbom_order_no + rbom_line_noが同じ行）
    # ej_quantityが小さい方を残す
    df = df.sort_values(['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_quantity'])
    df = df.drop_duplicates(subset=['ej_order_no', 'rbom_order_no', 'rbom_line_no'], keep='first')
    print(f"重複削除後: {len(df):,}件")

    # 空欄の場合は0として扱う
    df['ej_quantity'] = df['ej_quantity'].fillna(0)
    df['rbom_quantity'] = df['rbom_quantity'].fillna(0)

    # ej_order_no毎に集計
    df_grouped = df.groupby('ej_order_no', as_index=False).agg({
        'ej_quantity': 'sum',
        'rbom_quantity': 'sum'
    })
    df_grouped.columns = ['ej_order_no', 'ej_quantity_sum', 'rbom_quantity_sum']

    print(f"ユニークej_order_no数: {len(df_grouped):,}件")

    # CSV出力
    df_grouped.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n出力完了: {OUTPUT_PATH}")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")

    # プレビュー
    print("\n--- データプレビュー (先頭10件) ---")
    print(df_grouped.head(10))


if __name__ == "__main__":
    main()
