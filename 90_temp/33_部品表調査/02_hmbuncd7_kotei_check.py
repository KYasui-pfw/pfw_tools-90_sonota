"""
D3110テーブル（製番部品表ファイル）のHMBUNCD=7品目の工程登録チェック

処理内容:
1. M0810品目マスタからHMBUNCD='7'の品目コード(HMCD)リストを取得
2. D3110からSEINO, OYALISTNO, LISTNO, HMCD, HMNM, KTCDを取得
3. HMBUNCD=7の品目を持つ行（親行）を特定
4. その親行のLISTNOをOYALISTNOとして持つ子行を検索
5. 子行が1行もない場合、親行のKTCDに"工程登録無"を設定
6. 親行と子行をCSV出力
"""

import httpx
import csv
from pathlib import Path
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


def get_hmbuncd7_hmcd_set() -> set:
    """M0810からHMBUNCD='7'の品目コード(HMCD)セットを取得"""
    print("\n===== M0810品目マスタからHMBUNCD=7の品目を取得 =====")

    rows = fetch_all_data(
        table="M0810",
        columns=["HMCD"],
        where={"HMBUNCD": "7"}
    )

    hmcd_set = {row["HMCD"] for row in rows if row.get("HMCD")}
    print(f"HMBUNCD=7の品目数: {len(hmcd_set)}件")
    return hmcd_set


def get_d3110_data() -> list[dict]:
    """D3110から必要な6項目を取得"""
    print("\n===== D3110製番部品表からデータを取得 =====")

    return fetch_all_data(
        table="D3110",
        columns=["SEINO", "OYALISTNO", "LISTNO", "HMCD", "HMNM", "KTCD"]
    )


def process_data(d3110_rows: list[dict], hmbuncd7_hmcd_set: set) -> list[dict]:
    """
    HMBUNCD=7の行（親）とその子行を抽出し、工程行がない場合はKTCDに"工程登録無"を設定

    判定ロジック:
    - 子行が1行もない → 工程登録無
    - 子行はあるがKTCD値ありの行が1つもない → 工程登録無
    - 子行にKTCD値ありの行が1つ以上ある → 工程登録あり（出力しない）
    """
    print("\n===== データ処理中 =====")

    # OYALISTNOをキーにした辞書を作成（親のLISTNOから子を検索）
    # キー: OYALISTNO, 値: その行のリスト
    oyalistno_to_rows = defaultdict(list)
    for row in d3110_rows:
        oyalistno = row.get("OYALISTNO")
        if oyalistno:
            oyalistno_to_rows[oyalistno].append(row)

    # HMBUNCD=7の親行を特定（KTCDが空欄の行のみ対象）
    parent_rows = []
    for row in d3110_rows:
        hmcd = row.get("HMCD")
        ktcd = row.get("KTCD")
        # HMBUNCD=7かつKTCDが空欄（工程行ではない）の行のみ親行として扱う
        if hmcd and hmcd in hmbuncd7_hmcd_set and not ktcd:
            parent_rows.append(row)

    print(f"HMBUNCD=7を持つ親行数（KTCD空欄のみ）: {len(parent_rows)}件")

    # 結果を格納するリスト
    result_rows = []
    no_child_count = 0
    no_process_count = 0

    for parent in parent_rows:
        parent_listno = parent.get("LISTNO")

        # この親のLISTNOをOYALISTNOとして持つ子行を検索
        child_rows = oyalistno_to_rows.get(parent_listno, [])

        # 子行の中にKTCD値ありの行（工程行）があるかチェック
        has_process_row = any(row.get("KTCD") for row in child_rows)

        if not child_rows:
            # 子行がない場合 → 工程登録無
            parent_output = {
                "SEINO": parent.get("SEINO", ""),
                "OYALISTNO": parent.get("OYALISTNO", ""),
                "LISTNO": parent.get("LISTNO", ""),
                "HMCD": parent.get("HMCD", ""),
                "HMNM": parent.get("HMNM", ""),
                "KTCD": "工程登録無（子行なし）"
            }
            result_rows.append(parent_output)
            no_child_count += 1
        elif not has_process_row:
            # 子行はあるがKTCD値ありの行がない場合 → 工程登録無
            parent_output = {
                "SEINO": parent.get("SEINO", ""),
                "OYALISTNO": parent.get("OYALISTNO", ""),
                "LISTNO": parent.get("LISTNO", ""),
                "HMCD": parent.get("HMCD", ""),
                "HMNM": parent.get("HMNM", ""),
                "KTCD": "工程登録無（工程行なし）"
            }
            result_rows.append(parent_output)
            no_process_count += 1

    print(f"工程登録無（子行なし）: {no_child_count}件")
    print(f"工程登録無（工程行なし）: {no_process_count}件")
    print(f"出力対象行数: {len(result_rows)}件")

    return result_rows


def save_to_csv(rows: list[dict], output_path: Path):
    """結果をCSVファイルに出力"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["SEINO", "OYALISTNO", "LISTNO", "HMCD", "HMNM", "KTCD"])

        for row in rows:
            writer.writerow([
                row["SEINO"],
                row["OYALISTNO"],
                row["LISTNO"],
                row["HMCD"],
                row["HMNM"],
                row["KTCD"]
            ])

    print(f"\nCSVファイル出力完了: {output_path}")


def count_hmbuncd7_in_d3110(d3110_rows: list[dict], hmbuncd7_hmcd_set: set, output_dir: Path) -> dict:
    """D3110内のHMBUNCD=7品目の件数をカウントし、SEINOごとの件数をCSV出力"""
    print("\n===== HMBUNCD=7データ件数カウント =====")

    # HMBUNCD=7の品目を持つ行をカウント
    matched_rows = [row for row in d3110_rows if row.get("HMCD") in hmbuncd7_hmcd_set]

    # KTCDが空欄の行（品目行）とKTCDがある行（工程行）を分ける
    item_rows = [row for row in matched_rows if not row.get("KTCD")]
    process_rows = [row for row in matched_rows if row.get("KTCD")]

    # ユニークな品目コード数
    unique_hmcd = set(row.get("HMCD") for row in matched_rows if row.get("HMCD"))

    # ユニークな製番数
    unique_seino = set(row.get("SEINO") for row in matched_rows if row.get("SEINO"))

    # SEINOごとの件数をカウント
    seino_count = defaultdict(lambda: {"total": 0, "item_rows": 0, "process_rows": 0, "unique_hmcd": set()})
    for row in matched_rows:
        seino = row.get("SEINO", "")
        hmcd = row.get("HMCD", "")
        ktcd = row.get("KTCD")

        seino_count[seino]["total"] += 1
        if ktcd:
            seino_count[seino]["process_rows"] += 1
        else:
            seino_count[seino]["item_rows"] += 1
        if hmcd:
            seino_count[seino]["unique_hmcd"].add(hmcd)

    # SEINOごとの件数をCSV出力
    seino_output_path = output_dir / "02_HMBUNCD7_SEINOごと件数.csv"
    with open(seino_output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["SEINO", "総行数", "品目行数", "工程行数", "ユニーク品目数"])

        for seino in sorted(seino_count.keys()):
            data = seino_count[seino]
            writer.writerow([
                seino,
                data["total"],
                data["item_rows"],
                data["process_rows"],
                len(data["unique_hmcd"])
            ])

    print(f"SEINOごと件数CSV出力完了: {seino_output_path}")
    print(f"  出力製番数: {len(seino_count)}件")

    result = {
        "total_matched": len(matched_rows),
        "item_rows": len(item_rows),
        "process_rows": len(process_rows),
        "unique_hmcd": len(unique_hmcd),
        "unique_seino": len(unique_seino)
    }

    print(f"\nHMBUNCD=7品目を含む総行数: {result['total_matched']}件")
    print(f"  - 品目行（KTCD空欄）: {result['item_rows']}件")
    print(f"  - 工程行（KTCDあり）: {result['process_rows']}件")
    print(f"ユニーク品目コード数: {result['unique_hmcd']}件")
    print(f"ユニーク製番数: {result['unique_seino']}件")

    return result


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # 1. M0810からHMBUNCD=7の品目コードセットを取得
    hmbuncd7_hmcd_set = get_hmbuncd7_hmcd_set()

    if not hmbuncd7_hmcd_set:
        print("HMBUNCD=7の品目が見つかりませんでした。")
        return

    # 2. D3110からデータを取得
    d3110_rows = get_d3110_data()

    if not d3110_rows:
        print("D3110データが取得できませんでした。")
        return

    # 3. HMBUNCD=7データの件数カウント（SEINOごとCSV出力含む）
    count_result = count_hmbuncd7_in_d3110(d3110_rows, hmbuncd7_hmcd_set, output_dir)

    # 4. データ処理（親行と子行の抽出、工程登録無の判定）
    result_rows = process_data(d3110_rows, hmbuncd7_hmcd_set)

    if not result_rows:
        print("抽出対象データがありませんでした。")
        # カウント結果のみ表示して終了
        print("\n========== 処理結果サマリー ==========")
        print(f"HMBUNCD=7品目数（M0810マスタ）: {len(hmbuncd7_hmcd_set)}件")
        print(f"D3110総行数: {len(d3110_rows)}件")
        print(f"D3110内HMBUNCD=7マッチ行数: {count_result['total_matched']}件")
        return

    # 5. CSV出力
    output_path = output_dir / "02_HMBUNCD7工程登録チェック.csv"
    save_to_csv(result_rows, output_path)

    # サマリー表示
    print("\n========== 処理結果サマリー ==========")
    print(f"HMBUNCD=7品目数（M0810マスタ）: {len(hmbuncd7_hmcd_set)}件")
    print(f"D3110総行数: {len(d3110_rows)}件")
    print(f"D3110内HMBUNCD=7マッチ行数: {count_result['total_matched']}件")
    print(f"  - ユニーク品目コード数: {count_result['unique_hmcd']}件")
    print(f"  - ユニーク製番数: {count_result['unique_seino']}件")
    print(f"工程登録無の出力行数: {len(result_rows)}件")


if __name__ == "__main__":
    main()
