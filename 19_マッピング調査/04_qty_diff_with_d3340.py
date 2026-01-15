"""
02_quantity_diff.csv（qty_diff!=0）と03_d3340_status_qty.csvを結合
1. 02のqty_diff!=0の行を抽出
2. order_noをキーにmapping_resultsからej_order_noとrbom情報を取得
3. rbom_order_no + rbom_line_noをキーに03とLEFT JOIN
4. rbom_order_no + rbom_line_noをキーにD3360とLEFT JOIN
"""
import sqlite3
import pandas as pd
import requests
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "mapping.db")

INPUT_02_PATH = os.path.join(DB_DIR, "02_quantity_diff.csv")
INPUT_03_PATH = os.path.join(DB_DIR, "03_d3340_status_qty.csv")
OUTPUT_PATH = os.path.join(DB_DIR, "04_qty_diff_with_d3340.csv")

# API設定
API_BASE_URL = "http://pfw-api"
API_KEY = "oG5^Ls%#20yq"
HEADERS = {
    'X-API-KEY': API_KEY,
    'accept': 'application/json',
    'Content-Type': 'application/json'
}


def query_d3360(order_no_list):
    """D3360テーブルからデータを取得"""
    payload = {
        "table": "D3360",
        "columns": ["PONO", "POLINENO", "STATUS", "RCVQTY", "NOTE"],
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
    print("02(qty_diff!=0) + mapping_results + 03 結合")
    print("=" * 60)

    # 02_quantity_diff.csv 読み込み
    df_02 = pd.read_csv(INPUT_02_PATH)
    print(f"02_quantity_diff.csv 全件: {len(df_02):,}件")

    # qty_diff != 0 の行を抽出
    df_02_diff = df_02[df_02['qty_diff'] != 0].copy()
    print(f"02_quantity_diff.csv (qty_diff!=0): {len(df_02_diff):,}件")

    # mapping_resultsからrbom情報を取得（ej_order_noでマッチ）
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT ej_order_no, rbom_order_no, rbom_line_no
    FROM mapping_results
    WHERE ej_order_no IS NOT NULL AND ej_order_no != ''
    """
    df_mapping = pd.read_sql_query(query, conn)
    conn.close()
    print(f"mapping_results (ej_order_no有効): {len(df_mapping):,}件")

    # 02とmapping_resultsをLEFT JOIN (order_no = ej_order_no)
    df_merged = df_02_diff.merge(
        df_mapping,
        left_on='order_no',
        right_on='ej_order_no',
        how='left'
    )
    print(f"02 + mapping_results 結合後: {len(df_merged):,}件")

    # 03_d3340_status_qty.csv 読み込み（rbom_order_noを文字列として読み込み）
    df_03 = pd.read_csv(INPUT_03_PATH, dtype={'rbom_order_no': str})
    # rbom_order_noを9桁ゼロパディング
    df_03['rbom_order_no'] = df_03['rbom_order_no'].apply(lambda x: str(x).zfill(9) if pd.notna(x) else x)
    print(f"03_d3340_status_qty.csv: {len(df_03):,}件")

    # 型を統一
    df_merged['rbom_order_no'] = df_merged['rbom_order_no'].astype(str)
    df_merged['rbom_line_no'] = pd.to_numeric(df_merged['rbom_line_no'], errors='coerce')
    df_03['rbom_order_no'] = df_03['rbom_order_no'].astype(str)
    df_03['rbom_line_no'] = pd.to_numeric(df_03['rbom_line_no'], errors='coerce')

    # 03とLEFT JOIN (rbom_order_no + rbom_line_no) - ej_quantityも取得
    df_result = df_merged.merge(
        df_03[['rbom_order_no', 'rbom_line_no', 'ej_quantity', 'd3340_status', 'd3340_qty', 'd3340_nouki']],
        on=['rbom_order_no', 'rbom_line_no'],
        how='left'
    )
    print(f"最終結合後: {len(df_result):,}件")

    # 不要カラムを削除（重複するej_order_no）
    if 'ej_order_no' in df_result.columns:
        df_result = df_result.drop(columns=['ej_order_no'])

    # D3360からデータを取得
    print("\n--- D3360取得 ---")
    unique_rbom_order_nos = df_result['rbom_order_no'].dropna().unique().tolist()
    # 'nan'文字列を除外
    unique_rbom_order_nos = [x for x in unique_rbom_order_nos if x != 'nan']
    print(f"対象rbom_order_no数: {len(unique_rbom_order_nos):,}件")

    # バッチ処理でD3360からデータを取得
    all_d3360_results = []
    batch_size = 100
    for i in range(0, len(unique_rbom_order_nos), batch_size):
        batch = unique_rbom_order_nos[i:i+batch_size]
        print(f"  D3360取得中... {i+1}-{min(i+batch_size, len(unique_rbom_order_nos))} / {len(unique_rbom_order_nos)}")
        results = query_d3360(batch)
        if results:
            all_d3360_results.extend(results)

    print(f"D3360取得件数: {len(all_d3360_results):,}件")

    if all_d3360_results:
        df_d3360 = pd.DataFrame(all_d3360_results)
        df_d3360.columns = [col.lower() for col in df_d3360.columns]
        df_d3360 = df_d3360.rename(columns={
            'pono': 'rbom_order_no',
            'polineno': 'rbom_line_no',
            'status': 'd3360_status',
            'rcvqty': 'd3360_rcvqty',
            'note': 'd3360_note'
        })

        # 型を統一
        df_d3360['rbom_order_no'] = df_d3360['rbom_order_no'].astype(str)
        df_d3360['rbom_line_no'] = pd.to_numeric(df_d3360['rbom_line_no'], errors='coerce')

        # D3360とLEFT JOIN
        df_result = df_result.merge(
            df_d3360[['rbom_order_no', 'rbom_line_no', 'd3360_status', 'd3360_rcvqty', 'd3360_note']],
            on=['rbom_order_no', 'rbom_line_no'],
            how='left'
        )
        print(f"D3360結合後: {len(df_result):,}件")

    # ソート
    df_result = df_result.sort_values(['order_no', 'rbom_order_no', 'rbom_line_no'])

    # puch_odr_typ列を削除
    if 'puch_odr_typ' in df_result.columns:
        df_result = df_result.drop(columns=['puch_odr_typ'])

    # 重複行を削除（ej_order_no(=order_no) + rbom_order_no + rbom_line_noが同じ行）
    # ej_quantityが小さい方を残す
    print(f"\n重複削除前: {len(df_result):,}件")
    df_result = df_result.sort_values(['order_no', 'rbom_order_no', 'rbom_line_no', 'ej_quantity'])
    df_result = df_result.drop_duplicates(subset=['order_no', 'rbom_order_no', 'rbom_line_no'], keep='first')
    print(f"重複削除後: {len(df_result):,}件")

    # order_noが一行上と同じ場合、mapping_qty, rbom_qty, expj_qty, qty_diffを空欄にする
    # ※ej_quantityは空欄にしない
    df_result = df_result.reset_index(drop=True)
    prev_order_no = None
    for idx in range(len(df_result)):
        current_order_no = df_result.loc[idx, 'order_no']
        if current_order_no == prev_order_no:
            df_result.loc[idx, 'mapping_qty'] = None
            df_result.loc[idx, 'rbom_qty'] = None
            df_result.loc[idx, 'expj_qty'] = None
            df_result.loc[idx, 'qty_diff'] = None
        prev_order_no = current_order_no

    # カラム順序を調整（ej_quantityをrbom_order_noの左に配置）
    cols = df_result.columns.tolist()
    if 'ej_quantity' in cols and 'rbom_order_no' in cols:
        cols.remove('ej_quantity')
        rbom_order_no_idx = cols.index('rbom_order_no')
        cols.insert(rbom_order_no_idx, 'ej_quantity')
        df_result = df_result[cols]

    # CSV出力
    df_result.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n出力完了: {OUTPUT_PATH}")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")
    print(f"出力行数: {len(df_result):,}件")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"rbom_order_noが紐付いた件数: {df_result['rbom_order_no'].notna().sum():,}件")
    print(f"rbom_order_noが紐付かなかった件数: {df_result['rbom_order_no'].isna().sum():,}件")
    print(f"d3340_statusが紐付いた件数: {df_result['d3340_status'].notna().sum():,}件")
    print(f"d3340_statusが紐付かなかった件数: {df_result['d3340_status'].isna().sum():,}件")

    # d3340_status別件数
    print("\nd3340_status別件数:")
    status_counts = df_result['d3340_status'].value_counts(dropna=False)
    for status, count in status_counts.items():
        print(f"  {status}: {count:,}件")

    # d3360_status別件数
    if 'd3360_status' in df_result.columns:
        print(f"\nd3360_statusが紐付いた件数: {df_result['d3360_status'].notna().sum():,}件")
        print("\nd3360_status別件数:")
        status_counts_3360 = df_result['d3360_status'].value_counts(dropna=False)
        for status, count in status_counts_3360.items():
            print(f"  {status}: {count:,}件")

    # プレビュー
    print("\n--- データプレビュー (先頭15件) ---")
    print(df_result.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
