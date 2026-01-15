"""
taisyou.csv と D3340/D3360 をマッピングするスクリプト

入力: taisyou.csv (引当番号, 行番号)
出力: taisyou_with_status.csv (引当番号, 行番号, STATUS, RCVQTY合計)
マッピング条件:
  - D3340: 引当番号=PONO, 行番号=LINENO → STATUS
  - D3360: 引当番号=PONO, 行番号=POLINENO → RCVQTY合計
"""
import csv
import httpx
import os
from collections import defaultdict

# API設定
API_BASE_URL = "http://pfw-api"
QUERY_ENDPOINT = "/query"
READ_API_KEY = "oG5^Ls%#20yq"


def fetch_data(table: str, columns: list[str], where: dict = None, limit: int = 10000, offset: int = 0) -> dict:
    """汎用データ取得関数"""
    headers = {"X-API-KEY": READ_API_KEY, "Content-Type": "application/json"}

    request_body = {
        "table": table,
        "columns": columns,
        "limit": limit,
        "offset": offset
    }
    if where:
        request_body["where"] = where

    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            f"{API_BASE_URL}{QUERY_ENDPOINT}",
            headers=headers,
            json=request_body
        )
        response.raise_for_status()
        return response.json()


def fetch_all_data(table: str, columns: list[str], where: dict = None) -> list[dict]:
    """全データをページネーションで取得"""
    all_rows = []
    offset = 0
    limit = 10000

    print(f"{table}テーブルからデータを取得中...")

    while True:
        print(f"  取得中: offset={offset}, limit={limit}")
        result = fetch_data(table, columns, where, limit, offset)
        rows = result.get("rows", [])

        if not rows:
            break

        all_rows.extend(rows)
        print(f"  取得済み: {len(all_rows)}件")

        if len(rows) < limit:
            break

        offset += limit

    print(f"データ取得完了: 合計 {len(all_rows)}件")
    return all_rows


def main():
    print("=" * 60)
    print("taisyou.csv × D3340 マッピング処理")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "taisyou.csv")
    output_file = os.path.join(script_dir, "taisyou_with_status.csv")

    # 1. taisyou.csv読み込み
    print("\n===== taisyou.csv読み込み =====")
    input_rows = []
    with open(input_file, "r", encoding="cp932") as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダー読み飛ばし
        print(f"ヘッダー: {header}")
        for row in reader:
            if len(row) >= 2:
                input_rows.append({
                    "引当番号": row[0],
                    "行番号": row[1]
                })
    print(f"読み込み行数: {len(input_rows)}件")

    # 2. D3340からデータ取得（入力の発注番号リストでWHERE IN検索）
    print("\n===== D3340発注明細ファイルからデータを取得 =====")

    # 入力からユニークな発注番号を取得
    unique_pono_set = set(row["引当番号"] for row in input_rows)
    unique_pono_list = list(unique_pono_set)
    print(f"検索対象の発注番号数: {len(unique_pono_list)}件")

    # チャンクに分けてWHERE IN検索
    d3340_rows = []
    chunk_size = 500
    for i in range(0, len(unique_pono_list), chunk_size):
        chunk = unique_pono_list[i:i+chunk_size]
        print(f"  取得中: {i+1}～{min(i+chunk_size, len(unique_pono_list))}件目")
        result = fetch_data(
            table="D3340",
            columns=["PONO", "LINENO", "STATUS"],
            where={"PONO": {"in": chunk}},
            limit=10000
        )
        d3340_rows.extend(result.get("rows", []))

    print(f"D3340取得件数: {len(d3340_rows)}件")

    # PONO+LINENOをキーにした辞書作成
    d3340_dict = {}
    for row in d3340_rows:
        pono = str(row.get("PONO", "")).strip()
        lineno = str(row.get("LINENO", "")).strip()
        status = row.get("STATUS", "")
        key = f"{pono}_{lineno}"
        d3340_dict[key] = status

    print(f"D3340ユニークキー数: {len(d3340_dict)}件")

    # 3. D3360からデータ取得（入力の発注番号リストでWHERE IN検索）
    print("\n===== D3360受入明細ファイルからデータを取得 =====")

    # チャンクに分けてWHERE IN検索
    d3360_rows = []
    for i in range(0, len(unique_pono_list), chunk_size):
        chunk = unique_pono_list[i:i+chunk_size]
        print(f"  取得中: {i+1}～{min(i+chunk_size, len(unique_pono_list))}件目")
        result = fetch_data(
            table="D3360",
            columns=["PONO", "POLINENO", "RCVQTY"],
            where={"PONO": {"in": chunk}},
            limit=10000
        )
        d3360_rows.extend(result.get("rows", []))

    print(f"D3360取得件数: {len(d3360_rows)}件")

    # PONO+POLINENOをキーにしてRCVQTYを合計
    d3360_dict = defaultdict(float)
    for row in d3360_rows:
        pono = str(row.get("PONO", "")).strip()
        polineno = str(row.get("POLINENO", "")).strip()
        rcvqty = row.get("RCVQTY") or 0
        try:
            rcvqty = float(rcvqty)
        except (ValueError, TypeError):
            rcvqty = 0
        key = f"{pono}_{polineno}"
        d3360_dict[key] += rcvqty

    print(f"D3360ユニークキー数: {len(d3360_dict)}件")

    # 4. マッピング処理
    print("\n===== マッピング処理 =====")
    output_rows = []
    d3340_matched = 0
    d3340_unmatched = 0
    d3360_matched = 0
    d3360_unmatched = 0

    for row in input_rows:
        ateno = row["引当番号"]
        gyono = row["行番号"]
        key = f"{ateno}_{gyono}"

        # D3340マッピング
        if key in d3340_dict:
            status = d3340_dict[key]
            d3340_matched += 1
        else:
            status = ""
            d3340_unmatched += 1

        # D3360マッピング
        if key in d3360_dict:
            rcvqty_sum = d3360_dict[key]
            d3360_matched += 1
        else:
            rcvqty_sum = ""
            d3360_unmatched += 1

        output_rows.append({
            "引当番号": ateno,
            "行番号": gyono,
            "D3340.STATUS": status,
            "D3360.RCVQTY合計": rcvqty_sum
        })

    print(f"D3340マッチ: {d3340_matched}件 / 非マッチ: {d3340_unmatched}件")
    print(f"D3360マッチ: {d3360_matched}件 / 非マッチ: {d3360_unmatched}件")

    # 5. CSV出力
    print("\n===== CSV出力 =====")
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["引当番号", "行番号", "D3340.STATUS", "D3360.RCVQTY合計"])
        for row in output_rows:
            writer.writerow([row["引当番号"], row["行番号"], row["D3340.STATUS"], row["D3360.RCVQTY合計"]])

    print(f"出力完了: {output_file}")
    print(f"出力行数: {len(output_rows)}件")

    # サマリー
    print("\n========== 処理結果サマリー ==========")
    print(f"入力行数: {len(input_rows)}件")
    print(f"ユニーク発注番号数: {len(unique_pono_list)}件")
    print(f"D3340取得件数: {len(d3340_rows)}件（ユニークキー: {len(d3340_dict)}件）")
    print(f"D3360取得件数: {len(d3360_rows)}件（ユニークキー: {len(d3360_dict)}件）")
    print(f"D3340マッチ: {d3340_matched}件 / 非マッチ: {d3340_unmatched}件")
    print(f"D3360マッチ: {d3360_matched}件 / 非マッチ: {d3360_unmatched}件")


if __name__ == "__main__":
    main()
