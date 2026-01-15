"""
スキーマとテーブルの詳細調査
直接見ると8802件あるのにAPIからは2151件しか取れない原因を特定
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
    print("Schema Investigation")
    print("=" * 80)

    print("""
    Note: You mentioned D3340 has 8802 rows when viewed directly.
    API returns only 2151 rows.

    Possible causes:
    1. Different schema (PFW_IT2 vs PFW_SW vs other)
    2. View filtering
    3. Different database instance

    Let's check what the API actually sees...
    """)

    # 1. D3340のPONO範囲を確認
    print("\n[1] D3340 PONO Range Check")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns=["PONO", "LINENO", "DRVDT"],
        order_by=["PONO ASC"],
        limit=10
    )
    if result:
        print(f"  First 10 rows (sorted by PONO ASC):")
        for row in result.get('rows', []):
            print(f"    PONO={row.get('PONO')}, LINENO={row.get('LINENO')}, DRVDT={row.get('DRVDT')}")

    result = query_generic(
        "D3340",
        columns=["PONO", "LINENO", "DRVDT"],
        order_by=["PONO DESC"],
        limit=10
    )
    if result:
        print(f"\n  Last 10 rows (sorted by PONO DESC):")
        for row in result.get('rows', []):
            print(f"    PONO={row.get('PONO')}, LINENO={row.get('LINENO')}, DRVDT={row.get('DRVDT')}")

    # 2. D3340のDRVDT範囲を確認
    print("\n[2] D3340 DRVDT Range Check")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns=["PONO", "LINENO", "DRVDT"],
        order_by=["DRVDT ASC"],
        limit=10
    )
    if result:
        print(f"  Earliest DRVDT:")
        for row in result.get('rows', []):
            print(f"    PONO={row.get('PONO')}, DRVDT={row.get('DRVDT')}")

    result = query_generic(
        "D3340",
        columns=["PONO", "LINENO", "DRVDT"],
        order_by=["DRVDT DESC"],
        limit=10
    )
    if result:
        print(f"\n  Latest DRVDT:")
        for row in result.get('rows', []):
            print(f"    PONO={row.get('PONO')}, DRVDT={row.get('DRVDT')}")

    # 3. 特定のPONOで確認（直接見ているテーブルにあるPONOを指定して確認）
    print("\n[3] Specific PONO Check")
    print("-" * 60)

    test_ponos = ["000000001", "000001000", "000003945", "000010000", "000017951"]
    for pono in test_ponos:
        result = query_generic(
            "D3340",
            columns=["PONO", "LINENO", "DRVDT", "STATUS"],
            where={"PONO": pono},
            limit=100
        )
        if result:
            count = result.get('row_count', 0)
            print(f"  PONO={pono}: {count} rows")
            if count > 0:
                for row in result.get('rows', [])[:3]:
                    print(f"    LINENO={row.get('LINENO')}, DRVDT={row.get('DRVDT')}, STATUS={row.get('STATUS')}")

    # 4. D3340の古いデータ（2025年11月より前）があるか確認
    print("\n[4] D3340 Data Before 2025-11-01")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns=["PONO", "LINENO", "DRVDT"],
        where={"DRVDT": {"lt": "2025-11-01"}},
        limit=100
    )
    if result:
        print(f"  Count (DRVDT < 2025-11-01): {result.get('row_count', 0)}")
        if result.get('rows'):
            print("  Sample rows:")
            for row in result.get('rows', [])[:5]:
                print(f"    PONO={row.get('PONO')}, DRVDT={row.get('DRVDT')}")

    # 5. 環境情報の確認（APIのルート情報）
    print("\n[5] API Root Info")
    print("-" * 60)

    try:
        response = requests.get(
            f"{BASE_URL}/",
            headers=HEADERS,
            timeout=10
        )
        print(f"  API Root Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 80)
    print("""
    CONCLUSION:

    If D3340 only has data with DRVDT >= 2025-11-01 through the API,
    but you see 8802 rows directly, this suggests:

    1. The API is connected to a DIFFERENT schema/database
       - API uses PFW_IT2 schema by default
       - You might be looking at a different schema (PFW_SW, etc.)

    2. Or the API is connected to a filtered VIEW
       - Not the actual D3340 table

    3. Or the database has been cleaned/truncated
       - Old data removed from PFW_IT2.D3340

    To verify:
    - Check which schema you're viewing directly (SELECT * FROM ALL_TABLES WHERE TABLE_NAME='D3340')
    - Check API server's .env file for DB_SCHEMA setting
    - Compare the PONO values between direct view and API
    """)
    print("=" * 80)

if __name__ == "__main__":
    main()
