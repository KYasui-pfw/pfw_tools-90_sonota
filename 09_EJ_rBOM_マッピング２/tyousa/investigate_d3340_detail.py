"""
D3340テーブルの詳細調査
直接見ると8802件あるのに、APIからは2151件しか取れない原因を調査
"""
import requests
import json
from collections import defaultdict

# API設定
BASE_URL = 'http://pfw-api'
API_KEY = r'oG5^Ls%#20yq'
HEADERS = {
    'X-API-KEY': API_KEY,
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

def query_generic(table_name, columns=None, where=None, order_by=None, limit=None, offset=None):
    """Generic Query APIを使用"""
    payload = {"table": table_name}
    if columns:
        payload["columns"] = columns
    if where:
        payload["where"] = where
    if order_by:
        payload["order_by"] = order_by
    if limit:
        payload["limit"] = limit
    if offset:
        payload["offset"] = offset

    try:
        response = requests.post(
            f"{BASE_URL}/query",
            headers=HEADERS,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("=" * 80)
    print("D3340 Detail Investigation")
    print("=" * 80)

    # 1. D3340の全件数を取得（条件なし）
    print("\n[1] D3340 Total Count (No Filter)")
    print("-" * 60)

    all_d3340 = []
    offset = 0
    while True:
        result = query_generic(
            "D3340",
            columns=["PONO", "LINENO", "SEINO", "DRVDT", "STATUS", "HMCD"],
            limit=10000,
            offset=offset
        )
        if not result or not result.get('rows'):
            break
        all_d3340.extend(result['rows'])
        print(f"  Offset {offset}: {len(result['rows'])} rows fetched")
        if result.get('row_count', 0) < 10000:
            break
        offset += 10000

    print(f"  Total from API: {len(all_d3340):,} rows")

    # 2. DRVDT分布（全期間）
    print("\n[2] DRVDT Distribution (All)")
    print("-" * 60)

    drvdt_counts = defaultdict(int)
    null_count = 0
    for row in all_d3340:
        drvdt = row.get('DRVDT')
        if drvdt:
            month = str(drvdt)[:7]
            drvdt_counts[month] += 1
        else:
            null_count += 1

    for month in sorted(drvdt_counts.keys()):
        print(f"  {month}: {drvdt_counts[month]:,} rows")
    if null_count:
        print(f"  NULL: {null_count:,} rows")

    # 3. STATUS分布
    print("\n[3] STATUS Distribution")
    print("-" * 60)

    status_counts = defaultdict(int)
    for row in all_d3340:
        status = row.get('STATUS')
        status_counts[str(status) if status else 'NULL'] += 1

    for status in sorted(status_counts.keys()):
        print(f"  STATUS={status}: {status_counts[status]:,} rows")

    # 4. 異なるDRVDT範囲でテスト
    print("\n[4] Different DRVDT Range Tests")
    print("-" * 60)

    test_ranges = [
        ("No Filter", None),
        ("DRVDT >= 2024-01-01", {"DRVDT": {"gte": "2024-01-01"}}),
        ("DRVDT >= 2025-01-01", {"DRVDT": {"gte": "2025-01-01"}}),
        ("DRVDT >= 2025-11-01", {"DRVDT": {"gte": "2025-11-01"}}),
        ("DRVDT < 2025-11-01", {"DRVDT": {"lt": "2025-11-01"}}),
        ("DRVDT IS NULL", {"DRVDT": {"is_null": True}}),
    ]

    for desc, where in test_ranges:
        result = query_generic(
            "D3340",
            columns=["PONO"],
            where=where,
            limit=10000
        )
        if result:
            print(f"  {desc}: {result.get('row_count', 0):,} rows")

    # 5. PONOの分布を確認
    print("\n[5] PONO Sample")
    print("-" * 60)

    pono_set = set(row.get('PONO') for row in all_d3340)
    print(f"  Unique PONOs: {len(pono_set):,}")

    # 最初と最後のPONOを表示
    sorted_ponos = sorted(pono_set)
    print(f"  First 5 PONOs: {sorted_ponos[:5]}")
    print(f"  Last 5 PONOs: {sorted_ponos[-5:]}")

    # 6. APIのスキーマを確認
    print("\n[6] Check if Schema affects results")
    print("-" * 60)
    print("  Note: API may be querying a specific schema (PFW_IT2 or PFW_SW)")
    print("  The .env DB_SCHEMA setting determines which schema is used")

    # 7. 追加調査：D3340以外のテーブルとの比較
    print("\n[7] Compare with D3330 (Parent Table)")
    print("-" * 60)

    d3330_all = []
    offset = 0
    while True:
        result = query_generic(
            "D3330",
            columns=["PONO", "STATUS"],
            limit=10000,
            offset=offset
        )
        if not result or not result.get('rows'):
            break
        d3330_all.extend(result['rows'])
        if result.get('row_count', 0) < 10000:
            break
        offset += 10000

    print(f"  D3330 Total: {len(d3330_all):,} rows")

    d3330_ponos = set(row.get('PONO') for row in d3330_all)
    print(f"  D3330 Unique PONOs: {len(d3330_ponos):,}")

    # D3340にあってD3330にないPONO
    d3340_ponos = set(row.get('PONO') for row in all_d3340)
    missing_in_d3330 = d3340_ponos - d3330_ponos
    print(f"  D3340 PONOs not in D3330: {len(missing_in_d3330):,}")

    print("\n" + "=" * 80)
    print("Investigation Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()
