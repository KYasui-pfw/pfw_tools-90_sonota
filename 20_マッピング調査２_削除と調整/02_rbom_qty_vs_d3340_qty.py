"""
済/済2/手のデータについて、rbom_order_no + rbom_line_noでD3340と突合
rbom_quantityの合計とD3340のQTYの差を確認
差がある/差がないの2ファイルを出力
"""
import sqlite3
import pandas as pd
import requests
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "db", "mapping.db")
OUTPUT_DIFF_PATH = os.path.join(SCRIPT_DIR, "db", "02_rbom_qty_diff.csv")
OUTPUT_MATCH_PATH = os.path.join(SCRIPT_DIR, "db", "02_rbom_qty_match.csv")

# API設定
API_BASE_URL = "http://pfw-api"
API_KEY = "oG5^Ls%#20yq"
HEADERS = {
    'X-API-KEY': API_KEY,
    'accept': 'application/json',
    'Content-Type': 'application/json'
}


def query_d3340(order_no_list):
    """D3340テーブルからデータを取得"""
    payload = {
        "table": "D3340",
        "columns": ["PONO", "LINENO", "QTY"],
        "where": {
            "and": [
                {"PONO": {"in": order_no_list}}
            ]
        },
        "limit": 10000
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            headers=HEADERS,
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and 'rows' in result:
                return result['rows']
            return result
        else:
            print(f"  APIエラー: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  接続エラー: {e}")
        return None


def main():
    print("=" * 60)
    print("済/済2/手のrbom_quantity合計 vs D3340のQTY 比較")
    print("=" * 60)

    # DB接続
    conn = sqlite3.connect(DB_PATH)

    # 済/済2/手のデータを取得
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
      AND rbom_line_no IS NOT NULL
      AND status IN ('済', '済2', '手')
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"済/済2/手の件数: {len(df):,}件")

    # status別件数
    print("\nstatus別件数:")
    status_counts = df['status'].value_counts(dropna=False)
    for status, count in status_counts.items():
        print(f"  {status}: {count:,}件")

    # rbom_order_no + rbom_line_no毎にrbom_quantityを合計
    df_grouped = df.groupby(['rbom_order_no', 'rbom_line_no']).agg({
        'rbom_quantity': 'sum',
        'ej_order_no': 'count'  # マッピング行数
    }).reset_index()
    df_grouped.columns = ['rbom_order_no', 'rbom_line_no', 'rbom_qty_sum', 'mapping_count']

    print(f"\nユニークなrbom_order_no + rbom_line_no組み合わせ数: {len(df_grouped):,}件")

    # ユニークなrbom_order_noを取得
    unique_order_nos = df_grouped['rbom_order_no'].unique().tolist()
    print(f"ユニークなrbom_order_no数: {len(unique_order_nos):,}件")

    # バッチ処理でD3340からデータを取得
    print("\n--- D3340取得 ---")
    all_d3340_results = []
    batch_size = 100
    for i in range(0, len(unique_order_nos), batch_size):
        batch = unique_order_nos[i:i+batch_size]
        print(f"  D3340取得中... {i+1}-{min(i+batch_size, len(unique_order_nos))} / {len(unique_order_nos)}")
        results = query_d3340(batch)
        if results:
            all_d3340_results.extend(results)

    print(f"D3340取得件数: {len(all_d3340_results):,}件")

    if len(all_d3340_results) == 0:
        print("D3340データが取得できませんでした")
        return

    # D3340のDataFrame作成
    df_d3340 = pd.DataFrame(all_d3340_results)
    df_d3340.columns = [col.lower() for col in df_d3340.columns]
    df_d3340 = df_d3340.rename(columns={
        'pono': 'rbom_order_no',
        'lineno': 'rbom_line_no',
        'qty': 'd3340_qty'
    })

    # 型を統一
    df_grouped['rbom_order_no'] = df_grouped['rbom_order_no'].astype(str)
    df_grouped['rbom_line_no'] = pd.to_numeric(df_grouped['rbom_line_no'], errors='coerce')
    df_d3340['rbom_order_no'] = df_d3340['rbom_order_no'].astype(str)
    df_d3340['rbom_line_no'] = pd.to_numeric(df_d3340['rbom_line_no'], errors='coerce')

    # マージ
    df_compare = df_grouped.merge(
        df_d3340,
        on=['rbom_order_no', 'rbom_line_no'],
        how='left'
    )

    print(f"\n比較対象件数: {len(df_compare):,}件")
    print(f"D3340にマッチした件数: {df_compare['d3340_qty'].notna().sum():,}件")
    print(f"D3340にマッチしなかった件数: {df_compare['d3340_qty'].isna().sum():,}件")

    # 差分計算
    df_compare['qty_diff'] = df_compare['rbom_qty_sum'] - df_compare['d3340_qty']

    # 差があるもの / 差がないもの に分離
    df_diff = df_compare[df_compare['qty_diff'] != 0].copy()
    df_match = df_compare[df_compare['qty_diff'] == 0].copy()

    print(f"\n差がある件数: {len(df_diff):,}件")
    print(f"差がない件数: {len(df_match):,}件")

    # 元データの詳細情報を付与するため、再度マージ
    # 差がある方
    if len(df_diff) > 0:
        df_diff_detail = df.merge(
            df_diff[['rbom_order_no', 'rbom_line_no', 'rbom_qty_sum', 'd3340_qty', 'qty_diff', 'mapping_count']],
            on=['rbom_order_no', 'rbom_line_no'],
            how='inner'
        )
        df_diff_detail = df_diff_detail.sort_values(['rbom_order_no', 'rbom_line_no', 'ej_order_no'])
        df_diff_detail.to_csv(OUTPUT_DIFF_PATH, index=False, encoding='utf-8-sig')
        print(f"\n差あり出力完了: {OUTPUT_DIFF_PATH}")
        print(f"ファイルサイズ: {os.path.getsize(OUTPUT_DIFF_PATH) / 1024:.2f} KB")
        print(f"出力行数: {len(df_diff_detail):,}件")
    else:
        print("\n差があるデータはありません")

    # 差がない方
    if len(df_match) > 0:
        df_match_detail = df.merge(
            df_match[['rbom_order_no', 'rbom_line_no', 'rbom_qty_sum', 'd3340_qty', 'qty_diff', 'mapping_count']],
            on=['rbom_order_no', 'rbom_line_no'],
            how='inner'
        )
        df_match_detail = df_match_detail.sort_values(['rbom_order_no', 'rbom_line_no', 'ej_order_no'])
        df_match_detail.to_csv(OUTPUT_MATCH_PATH, index=False, encoding='utf-8-sig')
        print(f"\n差なし出力完了: {OUTPUT_MATCH_PATH}")
        print(f"ファイルサイズ: {os.path.getsize(OUTPUT_MATCH_PATH) / 1024:.2f} KB")
        print(f"出力行数: {len(df_match_detail):,}件")
    else:
        print("\n差がないデータはありません")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)

    if len(df_diff) > 0:
        print("\n--- 差があるデータの統計 ---")
        print(f"  rbom_qty_sum > d3340_qty: {len(df_diff[df_diff['qty_diff'] > 0]):,}件")
        print(f"  rbom_qty_sum < d3340_qty: {len(df_diff[df_diff['qty_diff'] < 0]):,}件")
        print(f"  最小差分: {df_diff['qty_diff'].min():.1f}")
        print(f"  最大差分: {df_diff['qty_diff'].max():.1f}")

        # プレビュー（差がある方）
        print("\n--- 差があるデータプレビュー (先頭10件) ---")
        preview_cols = ['rbom_order_no', 'rbom_line_no', 'rbom_qty_sum', 'd3340_qty', 'qty_diff', 'mapping_count']
        print(df_diff[preview_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
