"""
mapping_resultsのrbom_order_no + rbom_line_noをキーに
D3340テーブルからstatus(SYORIZUMIKB)とqty(HATYUSU)を取得
"""
import sqlite3
import pandas as pd
import requests
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "db", "mapping.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "db", "03_d3340_status_qty.csv")

# API設定
API_BASE_URL = "http://pfw-api"
API_KEY = r"oG5^Ls%#20yq"
HEADERS = {
    'X-API-KEY': API_KEY,
    'accept': 'application/json',
    'Content-Type': 'application/json'
}


def query_d3340(order_no_list):
    """D3340テーブルからデータを取得（/query API使用）"""
    payload = {
        "table": "D3340",
        "columns": ["PONO", "LINENO", "STATUS", "QTY", "DRVDT"],
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
            # 新しいレスポンス形式の場合はrowsを返す
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
    print("D3340からstatus(SYORIZUMIKB)とqty(HATYUSU)を取得")
    print("=" * 60)

    # DB接続してej_order_no, ej_quantity, rbom_order_no, rbom_line_noを取得
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT DISTINCT ej_order_no, ej_quantity, rbom_order_no, rbom_line_no
    FROM mapping_results
    WHERE rbom_order_no IS NOT NULL AND rbom_order_no != ''
      AND rbom_line_no IS NOT NULL
    """
    df_keys = pd.read_sql_query(query, conn)
    conn.close()

    print(f"抽出件数: {len(df_keys):,}件")

    # 重複行を削除（ej_order_no + rbom_order_no + rbom_line_noが同じ行）
    # ej_quantityが小さい方を残す
    df_keys = df_keys.sort_values(['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_quantity'])
    df_keys = df_keys.drop_duplicates(subset=['ej_order_no', 'rbom_order_no', 'rbom_line_no'], keep='first')
    print(f"重複削除後: {len(df_keys):,}件")

    # ユニークなrbom_order_noを取得
    unique_order_nos = df_keys['rbom_order_no'].unique().tolist()
    print(f"ユニークrbom_order_no数: {len(unique_order_nos):,}件")

    # バッチ処理でD3340からデータを取得（100件ずつ）
    all_results = []
    batch_size = 100
    for i in range(0, len(unique_order_nos), batch_size):
        batch = unique_order_nos[i:i+batch_size]
        print(f"  取得中... {i+1}-{min(i+batch_size, len(unique_order_nos))} / {len(unique_order_nos)}")

        results = query_d3340(batch)
        if results:
            all_results.extend(results)

    print(f"\nD3340取得件数: {len(all_results):,}件")

    if len(all_results) == 0:
        print("データが取得できませんでした")
        return

    # DataFrameに変換
    df_d3340 = pd.DataFrame(all_results)
    # カラム名を小文字に変換
    df_d3340.columns = [col.lower() for col in df_d3340.columns]
    df_d3340 = df_d3340.rename(columns={
        'pono': 'rbom_order_no',
        'lineno': 'rbom_line_no',
        'status': 'd3340_status',
        'qty': 'd3340_qty',
        'drvdt': 'd3340_nouki'
    })

    # rbom_line_noを数値型に変換
    df_d3340['rbom_line_no'] = pd.to_numeric(df_d3340['rbom_line_no'], errors='coerce')
    df_keys['rbom_line_no'] = pd.to_numeric(df_keys['rbom_line_no'], errors='coerce')

    # mapping_resultsのキーとマージ
    df_result = df_keys.merge(df_d3340, on=['rbom_order_no', 'rbom_line_no'], how='left')

    # ソート
    df_result = df_result.sort_values(['rbom_order_no', 'rbom_line_no'])

    # CSV出力
    df_result.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n出力完了: {OUTPUT_PATH}")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")
    print(f"出力行数: {len(df_result):,}件")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"D3340にマッチした件数: {df_result['d3340_status'].notna().sum():,}件")
    print(f"D3340にマッチしなかった件数: {df_result['d3340_status'].isna().sum():,}件")

    # ステータス別件数
    print("\nステータス別件数:")
    status_counts = df_result['d3340_status'].value_counts(dropna=False)
    for status, count in status_counts.items():
        print(f"  {status}: {count:,}件")

    # プレビュー
    print("\n--- データプレビュー (先頭10件) ---")
    print(df_result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
