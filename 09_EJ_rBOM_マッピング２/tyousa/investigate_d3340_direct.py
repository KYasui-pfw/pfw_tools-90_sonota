"""
D3340テーブルの全データ件数とGETSUJI分布を直接確認するスクリプト
Generic Query APIを使用してD3340を直接クエリ
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

def query_generic(table_name, columns="*", where_clause=None, limit=None):
    """Generic Query APIを使用"""
    payload = {
        "table_name": table_name,
        "columns": columns
    }
    if where_clause:
        payload["where_clause"] = where_clause
    if limit:
        payload["limit"] = limit

    try:
        response = requests.post(
            f"{BASE_URL}/generic-query/",
            headers=HEADERS,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  エラー: {e}")
        return None

def main():
    print("=" * 80)
    print("D3340テーブル直接調査")
    print("=" * 80)

    # 1. D3340の全件数（DRVDT >= 2025-11-01）
    print("\n【1】D3340テーブルの件数確認（DRVDT >= 2025-11-01）")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns="COUNT(*) AS CNT",
        where_clause="DRVDT >= DATE '2025-11-01'"
    )
    if result:
        print(f"  D3340件数（DRVDT >= 2025-11-01）: {result}")

    # 2. D3340の全件数（条件なし）
    print("\n【2】D3340テーブルの全件数")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns="COUNT(*) AS CNT"
    )
    if result:
        print(f"  D3340全件数: {result}")

    # 3. DRVDTの月別分布（2025年以降）
    print("\n【3】D3340 DRVDT月別分布")
    print("-" * 60)

    result = query_generic(
        "D3340",
        columns="TO_CHAR(DRVDT, 'YYYY-MM') AS DRVDT_MONTH, COUNT(*) AS CNT",
        where_clause="DRVDT >= DATE '2025-01-01' GROUP BY TO_CHAR(DRVDT, 'YYYY-MM') ORDER BY DRVDT_MONTH"
    )
    if result:
        for row in result:
            print(f"  {row}")

    # 4. D3010.GETSUJIの分布確認
    print("\n【4】D3010 GETSUJI分布（D3340とJOIN）")
    print("-" * 60)

    # D3340とD3010をJOINしてGETSUJI分布を確認
    result = query_generic(
        "D3340 d3340 LEFT JOIN D3010 d3010 ON d3340.SEINO = d3010.SEINO",
        columns="COALESCE(TO_CHAR(d3010.GETSUJI), 'NULL') AS GETSUJI, COUNT(*) AS CNT",
        where_clause="d3340.DRVDT >= DATE '2025-11-01' GROUP BY COALESCE(TO_CHAR(d3010.GETSUJI), 'NULL') ORDER BY GETSUJI"
    )
    if result:
        for row in result:
            print(f"  {row}")

    # 5. GETSUJIがNULLのレコード数
    print("\n【5】D3010.GETSUJIがNULLのレコード")
    print("-" * 60)

    result = query_generic(
        "D3340 d3340 LEFT JOIN D3010 d3010 ON d3340.SEINO = d3010.SEINO",
        columns="COUNT(*) AS CNT",
        where_clause="d3340.DRVDT >= DATE '2025-11-01' AND d3010.GETSUJI IS NULL"
    )
    if result:
        print(f"  GETSUJIがNULLの件数: {result}")

    # 6. SEINOがD3010に存在しないレコード
    print("\n【6】D3340.SEINOがD3010に存在しないレコード")
    print("-" * 60)

    result = query_generic(
        "D3340 d3340 LEFT JOIN D3010 d3010 ON d3340.SEINO = d3010.SEINO",
        columns="COUNT(*) AS CNT",
        where_clause="d3340.DRVDT >= DATE '2025-11-01' AND d3010.SEINO IS NULL"
    )
    if result:
        print(f"  D3010に存在しないSEINOの件数: {result}")

    # 7. APIクエリ条件の再現
    print("\n【7】APIクエリ条件の再現（GETSUJI LIKE '202511%' OR DRVDT月='202511'）")
    print("-" * 60)

    result = query_generic(
        "D3340 d3340 LEFT JOIN D3010 d3010 ON d3340.SEINO = d3010.SEINO",
        columns="COUNT(*) AS CNT",
        where_clause="COALESCE(TO_CHAR(d3010.GETSUJI), TO_CHAR(d3340.DRVDT, 'YYYYMM')) LIKE '202511%'"
    )
    if result:
        print(f"  2025年11月条件での件数: {result}")

    # 8. 各月のAPIクエリ条件での件数
    print("\n【8】各月のAPIクエリ条件での件数")
    print("-" * 60)

    for year_month in ['202511', '202512', '202601', '202602', '202603', '202604', '202605', '202606']:
        result = query_generic(
            "D3340 d3340 LEFT JOIN D3010 d3010 ON d3340.SEINO = d3010.SEINO",
            columns="COUNT(*) AS CNT",
            where_clause=f"COALESCE(TO_CHAR(d3010.GETSUJI), TO_CHAR(d3340.DRVDT, 'YYYYMM')) LIKE '{year_month}%'"
        )
        if result:
            cnt = result[0].get('CNT', 0) if result else 0
            print(f"  GETSUJI/DRVDT LIKE '{year_month}%': {cnt}件")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
