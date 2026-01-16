# -*- coding: utf-8 -*-
"""
01_受入件数比較_rBOM受入.py
rBOMシステムの受入実績をHMCD単位・月別に集計する

処理内容:
  1. D3350とD3360をRCVNOで結合
  2. D3340とPONO+POLINENO(=LINENO)で結合
  3. D3360.RCVDT >= 2025/12/01 のデータを抽出
  4. 月別・HMCD別にRCVQTYを集計
  5. 月ごとにCSV出力

出力CSV項目:
  - HMCD: 品目コード
  - RCVQTY_SUM: 受入数量合計
  - PONO_LIST: 集計対象の発注番号一覧（カンマ区切り）
  - NOTE_LIST: 集計対象のNOTE一覧（カンマ区切り）
"""

import sys
import os
import csv
import httpx
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# =============================================================================
# 設定
# =============================================================================
API_BASE_URL = "http://pfw-api"
READ_API_KEY = "oG5^Ls%#20yq"
TIMEOUT = 60.0

# 抽出開始日
EXTRACT_START_DATE = "2025-12-01"

# 出力ファイル名プレフィックス
OUTPUT_PREFIX = "01_2_受入件数比較_rBOM受入"


# =============================================================================
# ロギング
# =============================================================================
def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# API呼び出し
# =============================================================================
def query_api(table_name: str, columns: list = None, where: dict = None, limit: int = 10000, offset: int = 0) -> list:
    """
    汎用クエリAPIを呼び出す
    """
    headers = {
        "X-API-KEY": READ_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "table": table_name,
        "limit": limit,
        "offset": offset
    }
    if columns:
        data["columns"] = columns
    if where:
        data["where"] = where

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(
                f"{API_BASE_URL}/query",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result.get("rows", [])
    except httpx.HTTPStatusError as e:
        log(f"APIエラー ({table_name}): {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        log(f"APIエラー ({table_name}): {e}")
        return []


def fetch_all_data(table_name: str, columns: list, where: dict = None) -> list:
    """
    テーブルから全データを取得（ページネーション対応）
    """
    log(f"{table_name}データ取得中...")

    all_data = []
    offset = 0
    limit = 10000

    while True:
        data = query_api(table_name, columns=columns, where=where, limit=limit, offset=offset)
        if not data:
            break
        all_data.extend(data)
        log(f"  取得中: offset={offset}, 件数={len(all_data)}")
        if len(data) < limit:
            break
        offset += limit

    log(f"{table_name}取得完了: {len(all_data)}件")
    return all_data


# =============================================================================
# データ取得
# =============================================================================
def fetch_rbom_data() -> list:
    """
    rBOMからD3350、D3360、D3340を取得して結合

    Returns:
        list: 結合済みデータのリスト
    """
    # D3360（受入明細）を取得
    d3360_all = fetch_all_data(
        "D3360",
        columns=["RCVNO", "LINENO", "RCVDT", "RCVQTY", "PONO", "POLINENO"]
    )

    if not d3360_all:
        return []

    # RCVDT >= 2025/12/01 でフィルタリング
    d3360_data = []
    for row in d3360_all:
        rcvdt = row.get("RCVDT", "")
        if rcvdt and str(rcvdt)[:10] >= EXTRACT_START_DATE:
            d3360_data.append(row)

    log(f"D3360フィルタリング後: {len(d3360_data)}件 (RCVDT >= {EXTRACT_START_DATE})")

    # D3350（受入ファイル）を取得
    d3350_data = fetch_all_data(
        "D3350",
        columns=["RCVNO", "NOTE"]
    )

    # D3340（発注明細）を取得
    d3340_data = fetch_all_data(
        "D3340",
        columns=["PONO", "LINENO", "HMCD"]
    )

    # D3350をRCVNOでインデックス化
    d3350_dict = {}
    for row in d3350_data:
        rcvno = row.get("RCVNO", "")
        if rcvno:
            d3350_dict[rcvno] = row

    # D3340をPONO+LINENOでインデックス化
    d3340_dict = {}
    for row in d3340_data:
        pono = row.get("PONO", "")
        lineno = str(row.get("LINENO", ""))
        if pono and lineno:
            d3340_dict[(pono, lineno)] = row

    # 結合
    log("データ結合中...")
    joined_data = []
    for d3360_row in d3360_data:
        rcvno = d3360_row.get("RCVNO", "")
        pono = d3360_row.get("PONO", "")
        polineno = str(d3360_row.get("POLINENO", ""))

        # D3350と結合
        d3350_row = d3350_dict.get(rcvno, {})
        note = d3350_row.get("NOTE", "")

        # D3340と結合
        d3340_row = d3340_dict.get((pono, polineno), {})
        hmcd = d3340_row.get("HMCD", "")

        if hmcd:  # HMCDがある場合のみ
            joined_data.append({
                "RCVDT": d3360_row.get("RCVDT", ""),
                "RCVQTY": d3360_row.get("RCVQTY", 0),
                "PONO": pono,
                "POLINENO": polineno,
                "NOTE": note,
                "HMCD": hmcd
            })

    log(f"結合完了: {len(joined_data)}件")
    return joined_data


# =============================================================================
# データ集計
# =============================================================================
def aggregate_by_month_and_hmcd(data: list) -> dict:
    """
    月別・HMCD別にデータを集計

    Args:
        data: 結合済みデータ

    Returns:
        dict: {YYYYMM: {HMCD: {"qty": 合計数量, "ponos": set, "notes": set}}}
    """
    result = defaultdict(lambda: defaultdict(lambda: {"qty": 0, "ponos": set(), "notes": set()}))

    for row in data:
        rcvdt = row.get("RCVDT", "")
        hmcd = row.get("HMCD", "")
        rcvqty = row.get("RCVQTY", 0) or 0
        pono = row.get("PONO", "")
        polineno = row.get("POLINENO", "")
        note = row.get("NOTE", "")

        if not rcvdt or not hmcd:
            continue

        # YYYYMM形式の年月を取得
        if isinstance(rcvdt, datetime):
            yyyymm = rcvdt.strftime("%Y%m")
        else:
            yyyymm = str(rcvdt)[:7].replace("-", "")

        # 集計
        result[yyyymm][hmcd]["qty"] += float(rcvqty)
        if pono:
            # PONO+POLINENO の形式で追加
            pono_lineno = f"{pono}+{polineno}"
            result[yyyymm][hmcd]["ponos"].add(pono_lineno)
        if note:
            result[yyyymm][hmcd]["notes"].add(note)

    return result


# =============================================================================
# CSV出力
# =============================================================================
def write_monthly_csv(aggregated_data: dict, work_dir: Path):
    """
    月別CSVを出力

    Args:
        aggregated_data: 集計済みデータ
        work_dir: 出力先ディレクトリ
    """
    output_columns = ["HMCD", "RCVQTY_SUM", "PONO_LIST", "NOTE_LIST"]

    for yyyymm, items in sorted(aggregated_data.items()):
        output_path = work_dir / f"{OUTPUT_PREFIX}_{yyyymm}.csv"

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=output_columns)
            writer.writeheader()

            for hmcd in sorted(items.keys()):
                item_data = items[hmcd]
                writer.writerow({
                    "HMCD": hmcd,
                    "RCVQTY_SUM": item_data["qty"],
                    "PONO_LIST": ",".join(sorted(item_data["ponos"])),
                    "NOTE_LIST": ",".join(sorted(item_data["notes"]))
                })

        log(f"出力: {output_path} ({len(items)}件)")


# =============================================================================
# メイン処理
# =============================================================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # カレントディレクトリをスクリプトの場所に変更
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # workディレクトリ確認
    work_dir = script_dir / "work"
    if not work_dir.exists():
        work_dir.mkdir(parents=True)
        log(f"workディレクトリ作成: {work_dir}")

    print("=" * 60)
    print("01_受入件数比較_rBOM受入")
    print(f"抽出条件: D3360.RCVDT >= {EXTRACT_START_DATE}")
    print("=" * 60)

    try:
        # rBOMデータ取得・結合
        log("rBOMデータ取得中...")
        rbom_data = fetch_rbom_data()

        if not rbom_data:
            log("対象データがありません")
            print("=" * 60)
            print("完了: 対象データなし")
            print("=" * 60)
            return

        # 月別・HMCD別に集計
        log("データ集計中...")
        aggregated = aggregate_by_month_and_hmcd(rbom_data)

        # 月別CSV出力
        write_monthly_csv(aggregated, work_dir)

        print("=" * 60)
        print("完了:")
        for yyyymm in sorted(aggregated.keys()):
            print(f"  {yyyymm}: {len(aggregated[yyyymm])}品目")
        print("=" * 60)

    except Exception as e:
        log(f"エラー: {e}")
        raise


if __name__ == "__main__":
    main()
