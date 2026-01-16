# -*- coding: utf-8 -*-
"""
01_3_受入件数比較.py
EJ受入とrBOM受入のCSVを結合し、差分を計算する

処理内容:
  1. 01_1_受入件数比較_EJ受入_YYYYMM.csv を読み込む
  2. 01_2_受入件数比較_rBOM受入_YYYYMM.csv を読み込む
  3. ITEM_CD = HMCD で結合（FULL OUTER JOIN相当）
  4. 差分（ACPT_QTY_SUM - RCVQTY_SUM）を計算
  5. 月ごとにCSV出力

出力CSV項目:
  - ITEM_CD: 品目コード（EJ側のITEM_CDまたはrBOM側のHMCD）
  - EJ_ACPT_QTY_SUM: EJ側受入数量合計
  - EJ_PUCH_ODR_CD_LIST: EJ側発注番号一覧
  - RBOM_RCVQTY_SUM: rBOM側受入数量合計
  - RBOM_PONO_LIST: rBOM側発注番号一覧
  - RBOM_NOTE_LIST: rBOM側NOTE一覧
  - DIFF: 差分（EJ_ACPT_QTY_SUM - RBOM_RCVQTY_SUM）
"""

import sys
import os
import csv
import glob
import re
from datetime import datetime
from pathlib import Path

# =============================================================================
# 設定
# =============================================================================
# 入力ファイルパターン
EJ_CSV_PATTERN = "01_1_受入件数比較_EJ受入_*.csv"
RBOM_CSV_PATTERN = "01_2_受入件数比較_rBOM受入_*.csv"

# 出力ファイル名プレフィックス
OUTPUT_PREFIX = "01_3_受入件数比較"


# =============================================================================
# ロギング
# =============================================================================
def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# CSV読み込み
# =============================================================================
def read_ej_csv(file_path: Path) -> dict:
    """
    EJ受入CSVを読み込み、ITEM_CDをキーとした辞書で返す

    Returns:
        dict: {ITEM_CD: {"qty": 数量, "orders": 発注番号リスト}}
    """
    result = {}
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_cd = row.get("ITEM_CD", "").strip()
            if item_cd:
                result[item_cd] = {
                    "qty": float(row.get("ACPT_QTY_SUM", 0) or 0),
                    "orders": row.get("PUCH_ODR_CD_LIST", "")
                }
    return result


def read_rbom_csv(file_path: Path) -> dict:
    """
    rBOM受入CSVを読み込み、HMCDをキーとした辞書で返す

    Returns:
        dict: {HMCD: {"qty": 数量, "ponos": PONO一覧, "notes": NOTE一覧}}
    """
    result = {}
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hmcd = row.get("HMCD", "").strip()
            if hmcd:
                result[hmcd] = {
                    "qty": float(row.get("RCVQTY_SUM", 0) or 0),
                    "ponos": row.get("PONO_LIST", ""),
                    "notes": row.get("NOTE_LIST", "")
                }
    return result


# =============================================================================
# 結合処理
# =============================================================================
def merge_data(ej_data: dict, rbom_data: dict) -> list:
    """
    EJデータとrBOMデータをFULL OUTER JOIN相当で結合

    Args:
        ej_data: EJ側データ {ITEM_CD: {...}}
        rbom_data: rBOM側データ {HMCD: {...}}

    Returns:
        list: 結合結果のリスト
    """
    result = []

    # 全てのキーを取得（ITEM_CD = HMCD）
    all_keys = set(ej_data.keys()) | set(rbom_data.keys())

    for key in sorted(all_keys):
        ej = ej_data.get(key)
        rbom = rbom_data.get(key)

        ej_qty = ej["qty"] if ej else ""
        ej_orders = ej["orders"] if ej else ""
        rbom_qty = rbom["qty"] if rbom else ""
        rbom_ponos = rbom["ponos"] if rbom else ""
        rbom_notes = rbom["notes"] if rbom else ""

        # 差分計算（両方に存在する場合のみ）
        if ej is not None and rbom is not None:
            diff = ej["qty"] - rbom["qty"]
        else:
            diff = ""

        result.append({
            "ITEM_CD": key,
            "EJ_ACPT_QTY_SUM": ej_qty,
            "EJ_PUCH_ODR_CD_LIST": ej_orders,
            "RBOM_RCVQTY_SUM": rbom_qty,
            "RBOM_PONO_LIST": rbom_ponos,
            "RBOM_NOTE_LIST": rbom_notes,
            "DIFF": diff
        })

    return result


# =============================================================================
# CSV出力
# =============================================================================
def write_merged_csv(data: list, output_path: Path):
    """
    結合結果をCSV出力

    Args:
        data: 結合結果のリスト
        output_path: 出力ファイルパス
    """
    output_columns = [
        "ITEM_CD",
        "EJ_ACPT_QTY_SUM",
        "EJ_PUCH_ODR_CD_LIST",
        "RBOM_RCVQTY_SUM",
        "RBOM_PONO_LIST",
        "RBOM_NOTE_LIST",
        "DIFF"
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(data)

    log(f"出力: {output_path} ({len(data)}件)")


# =============================================================================
# メイン処理
# =============================================================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # カレントディレクトリをスクリプトの場所に変更
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # workディレクトリ
    work_dir = script_dir / "work"

    print("=" * 60)
    print("01_3_受入件数比較")
    print("=" * 60)

    # EJ側CSVファイルを検索
    ej_files = sorted(glob.glob(str(work_dir / EJ_CSV_PATTERN)))
    if not ej_files:
        log(f"EJ側CSVファイルが見つかりません: {EJ_CSV_PATTERN}")
        return

    # 月ごとに処理
    for ej_file in ej_files:
        ej_path = Path(ej_file)

        # ファイル名からYYYYMMを抽出
        match = re.search(r'_(\d{6})\.csv$', ej_path.name)
        if not match:
            log(f"ファイル名からYYYYMMを抽出できません: {ej_path.name}")
            continue

        yyyymm = match.group(1)

        # 対応するrBOM側CSVを検索
        rbom_path = work_dir / f"01_2_受入件数比較_rBOM受入_{yyyymm}.csv"
        if not rbom_path.exists():
            log(f"rBOM側CSVが見つかりません: {rbom_path.name}")
            continue

        log(f"処理中: {yyyymm}")

        # CSV読み込み
        ej_data = read_ej_csv(ej_path)
        rbom_data = read_rbom_csv(rbom_path)

        log(f"  EJ側: {len(ej_data)}件, rBOM側: {len(rbom_data)}件")

        # 結合
        merged = merge_data(ej_data, rbom_data)

        # 統計
        both_count = sum(1 for r in merged if r["EJ_ACPT_QTY_SUM"] != "" and r["RBOM_RCVQTY_SUM"] != "")
        ej_only = sum(1 for r in merged if r["EJ_ACPT_QTY_SUM"] != "" and r["RBOM_RCVQTY_SUM"] == "")
        rbom_only = sum(1 for r in merged if r["EJ_ACPT_QTY_SUM"] == "" and r["RBOM_RCVQTY_SUM"] != "")

        log(f"  結合結果: 両方={both_count}, EJのみ={ej_only}, rBOMのみ={rbom_only}")

        # CSV出力
        output_path = work_dir / f"{OUTPUT_PREFIX}_{yyyymm}.csv"
        write_merged_csv(merged, output_path)

    print("=" * 60)
    print("完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
