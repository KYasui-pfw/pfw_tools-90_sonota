# test_d3340_access.py
# D3340テーブルへのアクセステスト

import sys
import io
import requests
import json

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "http://pfw-api/query"
API_KEY = "oG5^Ls%#20yq"
HEADERS = {"X-API-KEY": API_KEY}

print("=" * 80)
print("D3340テーブルアクセステスト")
print("=" * 80)
print()

# テスト1: D3340の全カラムを1件取得
print("[テスト1] D3340から1件取得（カラム指定なし）")
print("-" * 80)

payload1 = {
    "table": "D3340",
    "limit": 1
}

try:
    response = requests.post(API_URL, json=payload1, headers=HEADERS, timeout=30)
    print(f"ステータスコード: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功: {data.get('row_count')}件取得")
        if data.get('rows'):
            print(f"カラム一覧: {', '.join(data.get('columns', []))}")
            print()
            print("サンプルデータ:")
            for key, value in data['rows'][0].items():
                print(f"  {key}: {value}")
    else:
        print(f"❌ エラー: {response.status_code}")
        print(f"レスポンス: {response.text}")

except Exception as e:
    print(f"❌ 例外: {e}")

print()
print()

# テスト2: 特定のPONO+LINENOで取得
print("[テスト2] 特定のPONO+LINENOで取得")
print("-" * 80)

payload2 = {
    "table": "D3340",
    "columns": ["PONO", "LINENO", "SEINO", "HMNM"],  # SRCDを削除してテスト
    "where": {
        "and": [
            {"PONO": "000008133"},
            {"LINENO": 58}  # 数値型に変更
        ]
    }
}

try:
    response = requests.post(API_URL, json=payload2, headers=HEADERS, timeout=30)
    print(f"ステータスコード: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功: {data.get('row_count')}件取得")
        if data.get('rows'):
            for row in data['rows']:
                print(f"データ: {row}")
    else:
        print(f"❌ エラー: {response.status_code}")
        print(f"レスポンス: {response.text}")

except Exception as e:
    print(f"❌ 例外: {e}")

print()
print("=" * 80)
print("テスト完了")
print("=" * 80)
