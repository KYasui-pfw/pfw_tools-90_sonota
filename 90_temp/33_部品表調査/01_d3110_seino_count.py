"""
D3110テーブル（製番部品表ファイル）のSEINO毎の行数を調査するスクリプト

rBOMシステムのFastAPI経由でD3110テーブルを取得し、
SEINO（製番）毎に何行のデータがあるかを集計してCSV出力します。
"""

import httpx
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


# API設定
API_BASE_URL = "http://pfw-api"
QUERY_ENDPOINT = "/query"
READ_API_KEY = "oG5^Ls%#20yq"


def fetch_d3110_data(limit: int = 50000, offset: int = 0) -> list[dict]:
    """D3110テーブルからデータを取得する（ページネーション対応）"""
    headers = {"X-API-KEY": READ_API_KEY, "Content-Type": "application/json"}

    request_body = {
        "table": "D3110",
        "columns": ["SEINO", "SEQ"],  # 集計に必要な最小限のカラムのみ取得
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
        return response.json()


def fetch_all_d3110_data() -> list[dict]:
    """D3110テーブルの全データを取得する（ページネーション対応）"""
    all_rows = []
    offset = 0
    limit = 10000  # API制限: 最大10000件

    print("D3110テーブルからデータを取得中...")

    while True:
        print(f"  取得中: offset={offset}, limit={limit}")
        result = fetch_d3110_data(limit=limit, offset=offset)
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


def count_by_seino(rows: list[dict]) -> Counter:
    """SEINO毎の行数をカウントする"""
    seino_counter = Counter()
    for row in rows:
        seino = row.get("SEINO")
        if seino:
            seino_counter[seino] += 1
    return seino_counter


def save_to_csv(seino_counts: Counter, output_path: Path):
    """結果をCSVファイルに出力する"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["SEINO", "行数"])

        # 行数の降順でソート
        for seino, count in seino_counts.most_common():
            writer.writerow([seino, count])

    print(f"CSVファイル出力完了: {output_path}")


def save_summary_to_csv(seino_counts: Counter, output_path: Path):
    """サマリー統計をCSVファイルに出力する"""
    total_seino = len(seino_counts)
    total_rows = sum(seino_counts.values())
    avg_rows = total_rows / total_seino if total_seino > 0 else 0
    max_rows = max(seino_counts.values()) if seino_counts else 0
    min_rows = min(seino_counts.values()) if seino_counts else 0

    # 行数の分布を計算
    distribution = Counter()
    for count in seino_counts.values():
        if count == 1:
            distribution["1行"] += 1
        elif count <= 10:
            distribution["2-10行"] += 1
        elif count <= 50:
            distribution["11-50行"] += 1
        elif count <= 100:
            distribution["51-100行"] += 1
        elif count <= 500:
            distribution["101-500行"] += 1
        elif count <= 1000:
            distribution["501-1000行"] += 1
        else:
            distribution["1000行超"] += 1

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # サマリー統計
        writer.writerow(["項目", "値"])
        writer.writerow(["調査日時", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["対象テーブル", "D3110（製番部品表ファイル）"])
        writer.writerow(["総SEINO数", total_seino])
        writer.writerow(["総行数", total_rows])
        writer.writerow(["平均行数/SEINO", f"{avg_rows:.2f}"])
        writer.writerow(["最大行数", max_rows])
        writer.writerow(["最小行数", min_rows])
        writer.writerow([])

        # 行数分布
        writer.writerow(["行数範囲", "SEINO数"])
        order = ["1行", "2-10行", "11-50行", "51-100行", "101-500行", "501-1000行", "1000行超"]
        for label in order:
            writer.writerow([label, distribution.get(label, 0)])

    print(f"サマリーCSVファイル出力完了: {output_path}")


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # データ取得
    rows = fetch_all_d3110_data()

    if not rows:
        print("データが取得できませんでした。")
        return

    # SEINO毎の行数カウント
    seino_counts = count_by_seino(rows)

    # 結果出力
    detail_path = output_dir / "01_製番部品表件数調査.csv"
    save_to_csv(seino_counts, detail_path)

    # コンソールにもサマリーを表示
    print("\n========== 調査結果サマリー ==========")
    print(f"総SEINO数: {len(seino_counts)}")
    print(f"総行数: {sum(seino_counts.values())}")
    print(f"平均行数/SEINO: {sum(seino_counts.values()) / len(seino_counts):.2f}")
    print(f"最大行数: {max(seino_counts.values())}")
    print(f"最小行数: {min(seino_counts.values())}")

    # 上位10件を表示
    print("\n========== 行数上位10件 ==========")
    for seino, count in seino_counts.most_common(10):
        print(f"  {seino}: {count}行")


if __name__ == "__main__":
    main()
