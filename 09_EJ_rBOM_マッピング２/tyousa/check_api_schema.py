"""
APIサーバーが接続しているスキーマを確認
PFW vs PFW_IT2 の違いを検証
"""
import requests
import json

# API設定
BASE_URL = 'http://pfw-api'
API_KEY = r'oG5^Ls%#20yq'
HEADERS = {
    'X-API-KEY': API_KEY,
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

def query_generic(table_name, columns=None, where=None, limit=None):
    """Generic Query APIを使用"""
    payload = {"table": table_name}
    if columns:
        payload["columns"] = columns
    if where:
        payload["where"] = where
    if limit:
        payload["limit"] = limit

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
    print("API Server Schema Check")
    print("=" * 80)

    print("""
    Local .env shows: DB_SCHEMA="PFW"
    But API server (http://pfw-api) may have different config.

    Let's check what data the API actually sees...
    """)

    # 1. D3340の件数確認
    print("\n[1] D3340 Count from API")
    print("-" * 60)

    result = query_generic("D3340", columns=["PONO"], limit=10000)
    if result:
        print(f"  D3340 rows: {result.get('row_count', 0):,}")

    # 2. PONOの最小値・最大値
    print("\n[2] D3340 PONO Range")
    print("-" * 60)

    result = query_generic("D3340", columns=["PONO"], limit=10000)
    if result and result.get('rows'):
        ponos = [r.get('PONO') for r in result['rows']]
        print(f"  Min PONO: {min(ponos)}")
        print(f"  Max PONO: {max(ponos)}")

    # 3. 本番環境(PFW)に8802件あるはずのD3340を確認
    #    PONOの若い番号（古いデータ）が存在するか
    print("\n[3] Check for older PONOs (should exist in PFW schema)")
    print("-" * 60)

    # 古いPONO番号を検索
    old_ponos = ["000000001", "000000100", "000000500", "000001000", "000002000", "000003000"]
    for pono in old_ponos:
        result = query_generic(
            "D3340",
            columns=["PONO", "LINENO", "DRVDT"],
            where={"PONO": {"lte": pono}},
            limit=5
        )
        if result:
            count = result.get('row_count', 0)
            if count > 0:
                print(f"  PONO <= {pono}: {count} rows found")
                break
            else:
                print(f"  PONO <= {pono}: No data")

    # 4. DRVDTの範囲確認
    print("\n[4] D3340 DRVDT Range Check")
    print("-" * 60)

    # 2025年11月より前のデータ
    result = query_generic(
        "D3340",
        columns=["PONO", "DRVDT"],
        where={"DRVDT": {"lt": "2025-11-01"}},
        limit=10
    )
    if result:
        count = result.get('row_count', 0)
        print(f"  DRVDT < 2025-11-01: {count} rows")
        if count > 0:
            print("  Sample:")
            for row in result['rows'][:5]:
                print(f"    PONO={row.get('PONO')}, DRVDT={row.get('DRVDT')}")

    # 2024年のデータ
    result = query_generic(
        "D3340",
        columns=["PONO", "DRVDT"],
        where={"and": [
            {"DRVDT": {"gte": "2024-01-01"}},
            {"DRVDT": {"lt": "2025-01-01"}}
        ]},
        limit=10
    )
    if result:
        count = result.get('row_count', 0)
        print(f"  DRVDT in 2024: {count} rows")

    print("\n" + "=" * 80)
    print("""
    CONCLUSION:

    If API shows:
    - Only ~2151 rows in D3340
    - PONO starting from 000003945
    - DRVDT starting from 2025-11-22
    - No data before 2025-11

    Then the API server (http://pfw-api) is connected to a DIFFERENT
    schema than your direct connection (PFW with 8802 rows).

    The API is likely connected to:
    - PFW_IT2 (development/test schema)
    - Or a newly migrated schema with limited data

    To fix this, check the API server's .env file:
    - If running in Docker: check docker-compose.yml or container env
    - If running on server: check the .env file on that server
    - Ensure DB_SCHEMA="PFW" on the API server
    """)
    print("=" * 80)

if __name__ == "__main__":
    main()
