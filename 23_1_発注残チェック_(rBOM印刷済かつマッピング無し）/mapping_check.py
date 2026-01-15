"""
発注残チェックスクリプト

mapping.dbのmapping_resultsテーブルと
rBOMデータベースのD3330/D3340テーブルをLEFT JOINしてCSV出力する

D3330: 発注ヘッダー (PONO)
D3340: 発注明細 (PONO + LINENO)
"""

import sqlite3
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# 設定
API_URL = 'http://pfw-api/query'
API_KEY = 'oG5^Ls%#20yq'
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / 'mapping.db'
CHUNK_SIZE = 500  # API呼び出し時のPONO数


def fetch_table_by_pono(table: str, pono_list: list, headers: dict) -> list:
    """PONOリストでフィルタしてテーブルデータを取得"""
    all_data = []
    for i in range(0, len(pono_list), CHUNK_SIZE):
        chunk = pono_list[i:i + CHUNK_SIZE]
        resp = requests.post(API_URL, headers=headers, json={
            'table': table,
            'where': {'PONO': {'in': chunk}},
            'limit': 10000
        })
        data = resp.json()
        if 'rows' in data:
            all_data.extend(data['rows'])
        print(f'  {table} chunk {i // CHUNK_SIZE + 1}: {len(data.get("rows", []))} rows')
    return all_data


def main():
    headers = {'Content-Type': 'application/json', 'X-API-KEY': API_KEY}

    # 1. mapping_resultsからデータ取得
    print('Loading mapping_results...')
    conn = sqlite3.connect(DB_PATH)
    df_mapping = pd.read_sql_query('SELECT * FROM mapping_results', conn)
    conn.close()
    print(f'  mapping_results: {len(df_mapping)} rows')

    # rbom_order_noの一意な値を取得（数字のみ）
    pono_list = df_mapping[df_mapping['rbom_order_no'].notna()]['rbom_order_no'].unique().tolist()
    pono_list = [p for p in pono_list if p and str(p).isdigit()]
    print(f'  Unique PONOs: {len(pono_list)}')

    # 2. D3330とD3340を取得
    print('Fetching D3330...')
    d3330_data = fetch_table_by_pono('D3330', pono_list, headers)
    print(f'  D3330 total: {len(d3330_data)} rows')

    print('Fetching D3340...')
    d3340_data = fetch_table_by_pono('D3340', pono_list, headers)
    print(f'  D3340 total: {len(d3340_data)} rows')

    # 3. DataFrameに変換
    df_d3330 = pd.DataFrame(d3330_data) if d3330_data else pd.DataFrame()
    df_d3340 = pd.DataFrame(d3340_data) if d3340_data else pd.DataFrame()

    # 4. D3330とD3340をPONOでJOIN
    if not df_d3330.empty and not df_d3340.empty:
        d3330_cols = ['PONO', 'PODT', 'SRCD', 'TANCD', 'NOTE', 'PRNKBN']
        d3340_cols = ['PONO', 'LINENO', 'HMCD', 'HMNM', 'QTY', 'DRVDT', 'STATUS', 'SEINO']

        df_d3330_sel = df_d3330[[c for c in d3330_cols if c in df_d3330.columns]]
        df_d3340_sel = df_d3340[[c for c in d3340_cols if c in df_d3340.columns]]

        df_rbom = pd.merge(df_d3340_sel, df_d3330_sel, on='PONO', how='left', suffixes=('', '_header'))
        print(f'  Joined D3330+D3340: {len(df_rbom)} rows')
    else:
        df_rbom = pd.DataFrame()
        print('  No rBOM data')

    # 5. mapping_resultsとLEFT JOIN
    df_mapping['rbom_order_no'] = df_mapping['rbom_order_no'].astype(str)
    df_mapping['rbom_line_no'] = pd.to_numeric(df_mapping['rbom_line_no'], errors='coerce')

    if not df_rbom.empty:
        df_rbom['PONO'] = df_rbom['PONO'].astype(str)
        df_rbom['LINENO'] = pd.to_numeric(df_rbom['LINENO'], errors='coerce')

        df_result = pd.merge(
            df_mapping,
            df_rbom,
            left_on=['rbom_order_no', 'rbom_line_no'],
            right_on=['PONO', 'LINENO'],
            how='left'
        )
    else:
        df_result = df_mapping.copy()

    print(f'  Final result: {len(df_result)} rows')

    # 6. CSV出力
    output_file = SCRIPT_DIR / f'mapping_check_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'Output: {output_file}')

    # 結果サマリー
    matched = df_result['PONO'].notna().sum() if 'PONO' in df_result.columns else 0
    print(f'\nSummary:')
    print(f'  Matched rows: {matched} / {len(df_result)}')
    print(f'  Unmatched rows: {len(df_result) - matched}')


if __name__ == '__main__':
    main()
