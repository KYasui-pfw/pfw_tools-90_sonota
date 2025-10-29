# test_error_check.py
# エラーデータの存在確認

import requests
import json

api_url = 'http://pfw-api/query'
headers = {'X-API-KEY': 'oG5^Ls%#20yq'}

# DK020のエラーデータ確認
print('=== DK020のエラーデータ確認 ===')
try:
    payload_dk020 = {
        'table': 'DK020',
        'where': {'SYORIZUMIKBN': '3'}
    }
    r1 = requests.post(api_url, json=payload_dk020, headers=headers, timeout=10)
    print(f'ステータス: {r1.status_code}')
    data1 = r1.json()
    rows1 = data1.get('rows', [])
    print(f'件数: {len(rows1)}件')
    if rows1:
        print('最初の1件:')
        print(json.dumps(rows1[0], ensure_ascii=False, indent=2))
except Exception as e:
    print(f'エラー: {e}')

print('\n=== DK040のエラーデータ確認 ===')
try:
    payload_dk040 = {
        'table': 'DK040',
        'where': {'SYORIZUMIKBN': '3'}
    }
    r2 = requests.post(api_url, json=payload_dk040, headers=headers, timeout=10)
    print(f'ステータス: {r2.status_code}')
    data2 = r2.json()
    rows2 = data2.get('rows', [])
    print(f'件数: {len(rows2)}件')
    if rows2:
        print('最初の1件:')
        print(json.dumps(rows2[0], ensure_ascii=False, indent=2))
except Exception as e:
    print(f'エラー: {e}')
