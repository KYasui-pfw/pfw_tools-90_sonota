"""
D3340とD3420の比較調査
なぜD3420は15000件あるのにD3340は2151件しかないのか？
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
    print("D3340 vs D3420 Comparison Investigation")
    print("=" * 80)

    # 1. D3340の全件数を確認（offsetで取得）
    print("\n[1] D3340 Total Count Check")
    print("-" * 60)

    all_d3340 = []
    offset = 0
    while True:
        result = query_generic(
            "D3340",
            columns=["PONO", "LINENO", "SEINO", "DRVDT", "STATUS"],
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

    print(f"  D3340 Total: {len(all_d3340):,} rows")

    # 2. D3420の全件数を確認
    print("\n[2] D3420 Total Count Check")
    print("-" * 60)

    all_d3420 = []
    offset = 0
    while True:
        result = query_generic(
            "D3420",
            columns=["INDNO", "LINENO", "SEINO", "DRVDT", "STATUS"],
            limit=10000,
            offset=offset
        )
        if not result or not result.get('rows'):
            break
        all_d3420.extend(result['rows'])
        print(f"  Offset {offset}: {len(result['rows'])} rows fetched")
        if result.get('row_count', 0) < 10000:
            break
        offset += 10000

    print(f"  D3420 Total: {len(all_d3420):,} rows")

    # 3. DRVDT範囲別の分布
    print("\n[3] DRVDT Range Distribution")
    print("-" * 60)

    def analyze_drvdt(data, table_name):
        drvdt_year = defaultdict(int)
        null_count = 0
        for row in data:
            drvdt = row.get('DRVDT')
            if drvdt:
                year = str(drvdt)[:4]
                drvdt_year[year] += 1
            else:
                null_count += 1
        print(f"  {table_name}:")
        for year in sorted(drvdt_year.keys()):
            print(f"    {year}: {drvdt_year[year]:,} rows")
        if null_count:
            print(f"    NULL: {null_count:,} rows")

    analyze_drvdt(all_d3340, "D3340")
    analyze_drvdt(all_d3420, "D3420")

    # 4. STATUS分布
    print("\n[4] STATUS Distribution")
    print("-" * 60)

    def analyze_status(data, table_name):
        status_counts = defaultdict(int)
        for row in data:
            status = row.get('STATUS')
            status_counts[str(status) if status else 'NULL'] += 1
        print(f"  {table_name}:")
        for status in sorted(status_counts.keys()):
            print(f"    STATUS={status}: {status_counts[status]:,} rows")

    analyze_status(all_d3340, "D3340")
    analyze_status(all_d3420, "D3420")

    # 5. D3340とD3420のSEINOの重複確認
    print("\n[5] SEINO Overlap Check")
    print("-" * 60)

    d3340_seinos = set(row.get('SEINO') for row in all_d3340 if row.get('SEINO'))
    d3420_seinos = set(row.get('SEINO') for row in all_d3420 if row.get('SEINO'))

    print(f"  D3340 unique SEINOs: {len(d3340_seinos):,}")
    print(f"  D3420 unique SEINOs: {len(d3420_seinos):,}")
    print(f"  Common SEINOs: {len(d3340_seinos & d3420_seinos):,}")
    print(f"  D3340 only: {len(d3340_seinos - d3420_seinos):,}")
    print(f"  D3420 only: {len(d3420_seinos - d3340_seinos):,}")

    # 6. D3340のDRVDT >= 2025-11-01の件数
    print("\n[6] D3340 with DRVDT >= 2025-11-01")
    print("-" * 60)

    d3340_2025_11 = [r for r in all_d3340 if r.get('DRVDT') and str(r.get('DRVDT')) >= '2025-11-01']
    print(f"  Count: {len(d3340_2025_11):,} rows")

    # STATUS分布
    status_2025_11 = defaultdict(int)
    for row in d3340_2025_11:
        status = row.get('STATUS')
        status_2025_11[str(status) if status else 'NULL'] += 1
    print("  STATUS distribution:")
    for status in sorted(status_2025_11.keys()):
        print(f"    STATUS={status}: {status_2025_11[status]:,} rows")

    # 7. D3420のDRVDT >= 2025-11-01の件数
    print("\n[7] D3420 with DRVDT >= 2025-11-01")
    print("-" * 60)

    d3420_2025_11 = [r for r in all_d3420 if r.get('DRVDT') and str(r.get('DRVDT')) >= '2025-11-01']
    print(f"  Count: {len(d3420_2025_11):,} rows")

    # STATUS分布
    status_2025_11_420 = defaultdict(int)
    for row in d3420_2025_11:
        status = row.get('STATUS')
        status_2025_11_420[str(status) if status else 'NULL'] += 1
    print("  STATUS distribution:")
    for status in sorted(status_2025_11_420.keys()):
        print(f"    STATUS={status}: {status_2025_11_420[status]:,} rows")

    # 8. 結論
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"""
  D3340: Total {len(all_d3340):,} rows (DRVDT >= 2025-11-01: {len(d3340_2025_11):,} rows)
  D3420: Total {len(all_d3420):,} rows (DRVDT >= 2025-11-01: {len(d3420_2025_11):,} rows)

  Note: D3340 is 発注明細 (Purchase Order Details)
        D3420 is 社内指示明細 (Internal Instruction Details)

  These are DIFFERENT tables with different purposes!

  The /orders/ API queries D3340, NOT D3420.
  If you need D3420 data, use /instructions/ API or /query endpoint.
""")

    # JSONに保存
    output_file = "C:/Dev/90_tools/09_EJ_rBOM_マッピング２/tyousa/table_comparison.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'd3340_total': len(all_d3340),
            'd3340_2025_11': len(d3340_2025_11),
            'd3420_total': len(all_d3420),
            'd3420_2025_11': len(d3420_2025_11),
            'd3340_status': dict(analyze_status_dict(all_d3340)),
            'd3420_status': dict(analyze_status_dict(all_d3420))
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")

def analyze_status_dict(data):
    status_counts = defaultdict(int)
    for row in data:
        status = row.get('STATUS')
        status_counts[str(status) if status else 'NULL'] += 1
    return status_counts

if __name__ == "__main__":
    main()
