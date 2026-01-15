# -*- coding: utf-8 -*-
"""
D3920発注明細履歴からQTYが11→9に変更されたレコードを検索
"""
import requests
from collections import defaultdict

def main():
    url = 'http://pfw-api/query'
    headers = {'Content-Type': 'application/json', 'X-API-KEY': 'oG5^Ls%#20yq'}

    all_records = []
    offset = 0
    limit = 1000

    print("D3920からデータ取得中...")
    while True:
        payload = {
            'table': 'D3920',
            'columns': ['PONO', 'LINENO', 'QTY', 'UPDTTM', 'UPDTKBN', 'HMCD', 'HMNM'],
            'where': {'or': [{'QTY': 11}, {'QTY': 9}]},
            'order_by': ['PONO', 'LINENO', 'UPDTTM'],
            'limit': limit,
            'offset': offset
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if 'rows' not in data or len(data['rows']) == 0:
            break

        all_records.extend(data['rows'])

        if len(data['rows']) < limit:
            break
        offset += limit

    print(f'総レコード数: {len(all_records)}')

    # PONO+LINENOでグループ化
    grouped = defaultdict(list)
    for r in all_records:
        key = (r['PONO'], r['LINENO'])
        grouped[key].append(r)

    # 11→9に変更されたケースを探す
    changes = []
    for key, records in grouped.items():
        records_sorted = sorted(records, key=lambda x: x['UPDTTM'])

        for i in range(len(records_sorted) - 1):
            if records_sorted[i]['QTY'] == 11 and records_sorted[i+1]['QTY'] == 9:
                changes.append({
                    'PONO': key[0],
                    'LINENO': key[1],
                    'HMCD': records_sorted[i]['HMCD'],
                    'before_qty': records_sorted[i]['QTY'],
                    'before_time': records_sorted[i]['UPDTTM'],
                    'after_qty': records_sorted[i+1]['QTY'],
                    'after_time': records_sorted[i+1]['UPDTTM']
                })

    print(f'QTY 11→9 に変更されたレコード数: {len(changes)}')
    print()
    print('=' * 80)
    for c in changes:
        print(f'発注番号: {c["PONO"]}, 行番号: {c["LINENO"]}')
        print(f'  品目コード: {c["HMCD"]}')
        print(f'  変更前: QTY={int(c["before_qty"])} ({c["before_time"]})')
        print(f'  変更後: QTY={int(c["after_qty"])} ({c["after_time"]})')
        print()

if __name__ == '__main__':
    main()
