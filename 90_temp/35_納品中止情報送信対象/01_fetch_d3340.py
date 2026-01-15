# -*- coding: utf-8 -*-
"""
納品中止情報送信対象のD3340データ取得スクリプト

入力: rBOM発注番号+行番号.csv（PONO+LINENOの形式）
出力: D3340テーブルの該当データ全項目をCSV出力
"""

import httpx
import csv
from datetime import datetime
from pathlib import Path

# API設定
API_BASE_URL = "http://pfw-api"
QUERY_ENDPOINT = "/query"
READ_API_KEY = "oG5^Ls%#20yq"

# パス設定
BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "rBOM発注番号+行番号.csv"
OUTPUT_DIR = BASE_DIR / "output"

# D3340の全カラム
D3340_COLUMNS = [
    "PONO", "LINENO", "TRKBN", "SRTNO", "JUNO", "JULINENO", "SEINO", "LISTNO",
    "VERNO", "STATUS", "RCVTSTKBN", "RCVCHKKBN", "RSNCD", "HMCNGKBN", "PARTSKBN",
    "HMCD", "HMNM", "HMWNM", "MODEL", "MODELW", "MAKER", "MATERIAL", "PROCESS",
    "SHAPEKBN", "SIZEX", "SIZEY", "SIZEZ", "SHAPEQTY", "KTCD", "DRVDT", "RECDT",
    "THQTY", "THUNIT", "INQTY", "QTY", "UNIT", "WEIGHT", "TWEIGHT", "KPKBN",
    "KPRSNCD", "PCMMTDT", "PKBN", "PRICE", "AMOUNT", "TAXKBN", "TAX", "PRNKBN",
    "PRNDT", "NKFLG", "NNKBN", "NNCD", "NNBASHO", "SEIBUCD", "SBCD", "CSBCD",
    "PRNO", "PRLINENO", "NOTE", "POSTRECDTM", "POSTRECTAN", "POSTRECNOTE",
    "NOTAXAMT", "TAXRATE", "KGZEIFLG", "INSTID", "INSTDT", "UPDTID", "UPDTDT"
]


def load_input_file() -> list[tuple[str, int]]:
    """入力ファイルを読み込み、PONO+LINENOのリストを返す"""
    keys = []
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # ヘッダーをスキップ
        for row in reader:
            if not row or not row[0]:
                continue
            value = row[0].strip()
            if "+" in value:
                parts = value.split("+")
                pono = parts[0]  # 左9桁
                lineno = int(parts[1])  # 右3桁
                keys.append((pono, lineno))
    return keys


def fetch_all_d3340() -> list[dict]:
    """D3340テーブル全体をページネーションで取得する"""
    headers = {"X-API-KEY": READ_API_KEY, "Content-Type": "application/json"}
    all_rows = []
    offset = 0
    limit = 10000

    print("D3340テーブル全体を取得中...")

    while True:
        print(f"  取得中: offset={offset}")

        request_body = {
            "table": "D3340",
            "columns": D3340_COLUMNS,
            "limit": limit,
            "offset": offset
        }

        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{API_BASE_URL}{QUERY_ENDPOINT}",
                headers=headers,
                json=request_body
            )
            response.raise_for_status()
            result = response.json()
            rows = result.get("rows", [])

        if not rows:
            break

        all_rows.extend(rows)
        print(f"  取得済み: {len(all_rows)}件")

        if len(rows) < limit:
            break

        offset += limit

    print(f"D3340取得完了: 合計 {len(all_rows)}件")
    return all_rows


def fetch_d3340_by_keys(keys: list[tuple[str, int]]) -> tuple[list[dict], list[dict]]:
    """PONO+LINENOのリストでD3340からデータを取得する

    Returns:
        tuple: (PONO+LINENOで検索した結果, PONOのみで検索した結果)
    """
    # 重複を除去してセット化
    unique_keys = set(keys)
    unique_ponos = set(pono for pono, lineno in unique_keys)
    print(f"入力データ:")
    print(f"  PONO+LINENO: {len(unique_keys)}件（重複除去後）")
    print(f"  PONOのみ: {len(unique_ponos)}件（重複除去後）")

    # D3340全体を取得
    all_d3340 = fetch_all_d3340()

    # フィルタリング（PONO+LINENO）
    print("対象データをフィルタリング中...")
    result_pono_lineno = []
    seen_pono_lineno = set()
    for row in all_d3340:
        pono = row.get("PONO")
        lineno = row.get("LINENO")
        key = (pono, lineno)
        if key in unique_keys and key not in seen_pono_lineno:
            result_pono_lineno.append(row)
            seen_pono_lineno.add(key)

    # フィルタリング（PONOのみ）
    result_pono_only = []
    seen_pono_only = set()
    for row in all_d3340:
        pono = row.get("PONO")
        lineno = row.get("LINENO")
        key = (pono, lineno)
        if pono in unique_ponos and key not in seen_pono_only:
            result_pono_only.append(row)
            seen_pono_only.add(key)

    print(f"フィルタリング完了:")
    print(f"  PONO+LINENOで検索: {len(result_pono_lineno)}件")
    print(f"  PONOのみで検索: {len(result_pono_only)}件")
    print(f"  差分: {len(result_pono_only) - len(result_pono_lineno)}件")

    return result_pono_lineno, result_pono_only


def save_to_csv(rows: list[dict], output_path: Path):
    """結果をCSVファイルに出力する"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=D3340_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSVファイル出力完了: {output_path}")


def main():
    """メイン処理"""
    # 出力ディレクトリ作成
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 入力ファイル読み込み
    print("入力ファイル読み込み中...")
    keys = load_input_file()
    print(f"入力件数: {len(keys)}件")

    if not keys:
        print("対象データがありません。")
        return

    # D3340からデータ取得
    print("\nD3340テーブルからデータ取得中...")
    rows_pono_lineno, rows_pono_only = fetch_d3340_by_keys(keys)

    # CSV出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if rows_pono_lineno:
        output_path1 = OUTPUT_DIR / f"01_D3340_PONO_LINENO_{timestamp}.csv"
        save_to_csv(rows_pono_lineno, output_path1)

    if rows_pono_only:
        output_path2 = OUTPUT_DIR / f"02_D3340_PONO_ONLY_{timestamp}.csv"
        save_to_csv(rows_pono_only, output_path2)

    # 差分抽出: PONO_ONLYにあってPONO_LINENOにないもの
    # PONO_LINENOのキーセットを作成
    pono_lineno_keys = set((row.get("PONO"), row.get("LINENO")) for row in rows_pono_lineno)

    # PONO_ONLYからPONO_LINENOにないものを抽出
    rows_diff = []
    for row in rows_pono_only:
        key = (row.get("PONO"), row.get("LINENO"))
        if key not in pono_lineno_keys:
            rows_diff.append(row)

    if rows_diff:
        output_path3 = OUTPUT_DIR / f"03_D3340_PONO_ONLYのみ_{timestamp}.csv"
        save_to_csv(rows_diff, output_path3)

    print(f"\n===== 処理完了 =====")
    print(f"01_PONO+LINENOで検索: {len(rows_pono_lineno)}件")
    print(f"02_PONOのみで検索: {len(rows_pono_only)}件")
    print(f"03_PONO_ONLYにのみ存在: {len(rows_diff)}件")


if __name__ == "__main__":
    main()
