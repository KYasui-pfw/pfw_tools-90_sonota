"""
D3340/D3420テーブルの件数とGETSUJI分布を直接確認するスクリプト
Generic Query API (/query) を使用
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
    payload = {
        "table": table_name
    }
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
    except requests.exceptions.HTTPError as e:
        print(f"  HTTPエラー: {e}")
        print(f"  レスポンス: {e.response.text[:500] if e.response else 'なし'}")
        return None
    except Exception as e:
        print(f"  エラー: {e}")
        return None

def main():
    print("=" * 80)
    print("D3340/D3420テーブル直接調査 (Generic Query API)")
    print("=" * 80)

    # 1. D3340の件数（DRVDT >= 2025-11-01）
    print("\n【1】D3340テーブルの件数")
    print("-" * 60)

    # DRVDT >= 2025-11-01 の件数
    result = query_generic(
        "D3340",
        columns=["PONO"],
        where={"DRVDT": {"gte": "2025-11-01"}},
        limit=10000
    )
    if result:
        print(f"  D3340件数（DRVDT >= 2025-11-01）: {result.get('row_count', 0):,}件")

    # 2. D3340の全件数（条件なし、最大10000件）
    result = query_generic(
        "D3340",
        columns=["PONO"],
        limit=10000
    )
    if result:
        print(f"  D3340件数（上限10000件）: {result.get('row_count', 0):,}件")

    # 3. D3420の件数（DRVDT >= 2025-11-01）
    print("\n【2】D3420テーブルの件数")
    print("-" * 60)

    result = query_generic(
        "D3420",
        columns=["INDNO"],
        where={"DRVDT": {"gte": "2025-11-01"}},
        limit=10000
    )
    if result:
        print(f"  D3420件数（DRVDT >= 2025-11-01）: {result.get('row_count', 0):,}件")

    result = query_generic(
        "D3420",
        columns=["INDNO"],
        limit=10000
    )
    if result:
        print(f"  D3420件数（上限10000件）: {result.get('row_count', 0):,}件")

    # 4. D3340のDRVDT月別分布
    print("\n【3】D3340 DRVDT月別分布（2025年以降）")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns=["DRVDT"],
        where={"DRVDT": {"gte": "2025-01-01"}},
        limit=10000
    )
    if result:
        drvdt_counts = defaultdict(int)
        for row in result.get('rows', []):
            drvdt = row.get('DRVDT')
            if drvdt:
                drvdt_month = str(drvdt)[:7]  # YYYY-MM
                drvdt_counts[drvdt_month] += 1
            else:
                drvdt_counts['NULL'] += 1

        for month in sorted(drvdt_counts.keys()):
            print(f"  {month}: {drvdt_counts[month]:,}件")

    # 5. D3010テーブルのGETSUJI分布
    print("\n【4】D3010 GETSUJI分布")
    print("-" * 60)

    result = query_generic(
        "D3010",
        columns=["GETSUJI"],
        limit=10000
    )
    if result:
        getsuji_counts = defaultdict(int)
        for row in result.get('rows', []):
            getsuji = row.get('GETSUJI')
            if getsuji:
                # 先頭6桁（YYYYMM）で集計
                getsuji_prefix = str(getsuji)[:6]
                getsuji_counts[getsuji_prefix] += 1
            else:
                getsuji_counts['NULL'] += 1

        print(f"  取得件数: {result.get('row_count', 0):,}件")
        print("\n  GETSUJI（先頭6桁）分布:")
        for getsuji in sorted(getsuji_counts.keys()):
            print(f"    {getsuji}: {getsuji_counts[getsuji]:,}件")

    # 6. D3340のSTATUSの分布
    print("\n【5】D3340 STATUSの分布")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns=["STATUS"],
        where={"DRVDT": {"gte": "2025-11-01"}},
        limit=10000
    )
    if result:
        status_counts = defaultdict(int)
        for row in result.get('rows', []):
            status = row.get('STATUS')
            status_counts[str(status) if status else 'NULL'] += 1

        for status in sorted(status_counts.keys()):
            print(f"  STATUS={status}: {status_counts[status]:,}件")

    # 7. D3340でSEINOがD3010に存在するか確認（サンプル）
    print("\n【6】D3340 SEINOサンプル確認")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns=["PONO", "LINENO", "SEINO", "HMCD", "DRVDT"],
        where={"DRVDT": {"gte": "2025-11-01"}},
        order_by=["PONO", "LINENO"],
        limit=20
    )
    if result:
        print(f"  取得件数: {result.get('row_count', 0):,}件")
        print("\n  サンプルデータ:")
        for row in result.get('rows', [])[:10]:
            print(f"    PONO={row.get('PONO')}, LINENO={row.get('LINENO')}, SEINO={row.get('SEINO')}, DRVDT={row.get('DRVDT')}")

    # 8. D3010のサンプル確認（SEINOとGETSUJI）
    print("\n【7】D3010 サンプル確認")
    print("-" * 60)

    result = query_generic(
        "D3010",
        columns=["SEINO", "GETSUJI", "HMNM"],
        limit=20
    )
    if result:
        print(f"  取得件数: {result.get('row_count', 0):,}件")
        print("\n  サンプルデータ:")
        for row in result.get('rows', [])[:10]:
            print(f"    SEINO={row.get('SEINO')}, GETSUJI={row.get('GETSUJI')}")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
