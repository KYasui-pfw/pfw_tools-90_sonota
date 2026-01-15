"""
compare_rbom_qty.py

CSVのrBOM数合計とD3340のQTYを比較するスクリプト

入力: mapping_rbom_qty.csv
出力: comparison_result.csv
"""
import os
import pandas as pd
import httpx
from dotenv import load_dotenv

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(SCRIPT_DIR, "mapping_rbom_qty.csv")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "comparison_result.csv")

# API設定
ENV_PATH = r"C:\Dev\01_Back_APIServer\fastapi_app\.env"
API_BASE_URL = "http://pfw-api/query"


def load_api_key():
    """APIキーを読み込み"""
    load_dotenv(ENV_PATH)
    return os.getenv("READ_API_KEY")


def parse_rbom_key(val):
    """rBOM発注番号+行番号をPONOとLINENOに分解"""
    if pd.isna(val):
        return None, None
    s = str(val)
    pono = s[:9]
    if '+' in s:
        lineno_str = s.split('+')[1]
        lineno = int(lineno_str)
    else:
        lineno = None
    return pono, lineno


def fetch_d3340_qty(api_key, pono_lineno_list):
    """
    D3340からQTYを一括取得

    Args:
        api_key: READ_API_KEY
        pono_lineno_list: [(PONO, LINENO), ...] のリスト

    Returns:
        dict: {(PONO, LINENO): QTY, ...}
    """
    result = {}

    # PONOのユニークリストを取得
    unique_ponos = list(set([p for p, l in pono_lineno_list]))

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    print(f"D3340からデータ取得中... (対象PONO数: {len(unique_ponos)})")

    # バッチで取得（100件ずつ）
    batch_size = 100
    total_fetched = 0

    with httpx.Client(timeout=60.0) as client:
        for i in range(0, len(unique_ponos), batch_size):
            batch_ponos = unique_ponos[i:i+batch_size]

            payload = {
                "table": "D3340",
                "columns": ["PONO", "LINENO", "QTY"],
                "where": {
                    "and": [
                        {"PONO": {"in": batch_ponos}}
                    ]
                },
                "limit": 10000
            }

            try:
                response = client.post(API_BASE_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                rows = data.get("rows", [])
                for row in rows:
                    pono = row.get("PONO")
                    lineno = row.get("LINENO")
                    qty = row.get("QTY")
                    if pono and lineno is not None:
                        result[(pono, int(lineno))] = qty

                total_fetched += len(rows)
                print(f"  バッチ {i//batch_size + 1}: {len(rows)}件取得")

            except Exception as e:
                print(f"  バッチ {i//batch_size + 1}: エラー - {e}")

    print(f"D3340から合計 {total_fetched} 件取得完了")
    return result


def main():
    print("=" * 60)
    print("rBOM数 vs D3340 QTY 比較処理")
    print("=" * 60)
    print()

    # APIキー読み込み
    api_key = load_api_key()
    if not api_key:
        print("エラー: READ_API_KEYが見つかりません")
        return 1

    # CSV読み込み
    print(f"入力ファイル: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, encoding='cp932')
    print(f"読み込み行数: {len(df)}")
    print()

    # rBOM発注番号+行番号を分解
    df['PONO'] = df['rBOM発注番号+行番号'].apply(lambda x: parse_rbom_key(x)[0])
    df['LINENO'] = df['rBOM発注番号+行番号'].apply(lambda x: parse_rbom_key(x)[1])

    # rBOM発注番号+行番号単位でrBOM数を合計
    grouped = df.groupby('rBOM発注番号+行番号').agg({
        'rBOM数': 'sum',
        'PONO': 'first',
        'LINENO': 'first'
    }).reset_index()
    grouped.columns = ['rBOM発注番号+行番号', 'rBOM数合計', 'PONO', 'LINENO']

    print(f"ユニークなrBOM発注番号+行番号: {len(grouped)}")
    print()

    # D3340からQTYを取得
    pono_lineno_list = [(row['PONO'], int(row['LINENO'])) for _, row in grouped.iterrows() if pd.notna(row['LINENO'])]
    d3340_qty_dict = fetch_d3340_qty(api_key, pono_lineno_list)
    print()

    # D3340のQTYをマッピング
    grouped['D3340_QTY'] = grouped.apply(
        lambda row: d3340_qty_dict.get((row['PONO'], int(row['LINENO']))) if pd.notna(row['LINENO']) else None,
        axis=1
    )

    # 差異計算
    grouped['差異'] = grouped['rBOM数合計'] - grouped['D3340_QTY']
    grouped['差異あり'] = grouped['差異'].apply(lambda x: '○' if pd.notna(x) and x != 0 else '')

    # 結果サマリー
    print("=" * 60)
    print("結果サマリー")
    print("=" * 60)

    total = len(grouped)
    d3340_found = grouped['D3340_QTY'].notna().sum()
    d3340_not_found = grouped['D3340_QTY'].isna().sum()
    diff_count = (grouped['差異'] != 0).sum()
    match_count = ((grouped['差異'] == 0) & (grouped['D3340_QTY'].notna())).sum()

    print(f"総件数: {total}")
    print(f"D3340にデータあり: {d3340_found}")
    print(f"D3340にデータなし: {d3340_not_found}")
    print(f"一致: {match_count}")
    print(f"差異あり: {diff_count}")
    print()

    # CSV出力
    output_df = grouped[['rBOM発注番号+行番号', 'PONO', 'LINENO', 'rBOM数合計', 'D3340_QTY', '差異', '差異あり']]
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='cp932')
    print(f"結果出力: {OUTPUT_CSV}")

    # 差異ありの上位10件を表示
    diff_rows = grouped[grouped['差異'] != 0].head(10)
    if len(diff_rows) > 0:
        print()
        print("=== 差異ありの例（上位10件）===")
        for _, row in diff_rows.iterrows():
            print(f"  {row['rBOM発注番号+行番号']}: rBOM数合計={row['rBOM数合計']}, D3340_QTY={row['D3340_QTY']}, 差異={row['差異']}")

    return 0


if __name__ == "__main__":
    exit(main())
