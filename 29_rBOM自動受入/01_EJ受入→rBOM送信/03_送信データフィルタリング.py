# -*- coding: utf-8 -*-
"""
03_送信データフィルタリング.py
02_送信データ全件.csvを読み込み、rBOMに既に登録済みのデータを除外する

処理内容:
  1. 02_送信データ全件.csvを読み込む
  2. フィルタリング1: D3350.NOTEとCSV.NOTEが一致 → 除外（受入済み）
  3. フィルタリング2: D3340でPONO+LINENO一致かつSTATUS=4or8 → 除外（完納/強制完納）
  4. 出力:
     - 03_送信データ.csv: フィルタリング後の送信対象データ
     - 03_除外データ.csv: 除外されたデータ（除外理由付き）
"""

import sys
import os
import csv
import re
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

# 入力ファイル
INPUT_CSV = "02_送信データ全件.csv"

# 出力ファイル
OUTPUT_CSV = "03_送信データ.csv"
OUTPUT_EXCLUDED_CSV = "03_除外データ.csv"
OUTPUT_CHECK_CSV = "03_除外データ（要チェック）.csv"

# 除外理由カラム名
EXCLUDE_REASON_COLUMN = "除外理由"


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

    Args:
        table_name: テーブル名（D3350, D3340など）
        columns: 取得カラム（オプション）
        where: WHERE条件（オプション）
        limit: 取得件数上限
        offset: オフセット

    Returns:
        データのリスト
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


def fetch_all_data(table_name: str, columns: list) -> list:
    """
    テーブルから全データを取得（ページネーション対応）

    Args:
        table_name: テーブル名
        columns: 取得カラム

    Returns:
        全データのリスト
    """
    log(f"{table_name}データ取得中...")

    all_data = []
    offset = 0
    limit = 10000

    while True:
        data = query_api(table_name, columns=columns, limit=limit, offset=offset)
        if not data:
            break
        all_data.extend(data)
        log(f"  取得中: offset={offset}, 件数={len(all_data)}")
        if len(data) < limit:
            break
        offset += limit

    log(f"{table_name}取得完了: {len(all_data)}件")
    return all_data


def fetch_d3350_notes() -> set:
    """
    D3350からNOTE一覧を取得

    Returns:
        set: NOTEの集合
    """
    all_data = fetch_all_data("D3350", columns=["NOTE"])

    # NOTEの集合を作成
    note_set = set()
    for row in all_data:
        note = row.get("NOTE", "")
        if note:
            note_set.add(note)

    log(f"D3350のユニークNOTE数: {len(note_set)}")
    return note_set


def fetch_d3340_status() -> tuple:
    """
    D3340からSTATUS別のPONO+LINENO一覧を取得

    Returns:
        tuple: (completed_set, partial_set)
            - completed_set: STATUS=4or8（完納/強制完納）の{(PONO, LINENO), ...}
            - partial_set: STATUS=3（一部完納）の{(PONO, LINENO), ...}
    """
    all_data = fetch_all_data("D3340", columns=["PONO", "LINENO", "STATUS"])

    # STATUS別にPONO+LINENOの集合を作成
    completed_set = set()  # STATUS=4or8
    partial_set = set()    # STATUS=3

    for row in all_data:
        status = str(row.get("STATUS", "")).strip()
        pono = row.get("PONO", "")
        lineno = str(row.get("LINENO", ""))
        if pono and lineno:
            if status in ("4", "8"):
                completed_set.add((pono, lineno))
            elif status == "3":
                partial_set.add((pono, lineno))

    log(f"D3340の完納/強制完納件数: {len(completed_set)}")
    log(f"D3340の一部完納件数: {len(partial_set)}")
    return completed_set, partial_set


def extract_note_number(note: str) -> int:
    """
    NOTEから数値部分を抽出

    Args:
        note: NOTE値（例: "E90580141"）

    Returns:
        数値部分（抽出できない場合は0）
    """
    match = re.match(r'E(\d+)', note)
    if match:
        return int(match.group(1))
    return 0


def adjust_edkbn(rows: list) -> tuple:
    """
    同じPONO+POLINENOでEDKBN=2が複数ある場合、
    NOTEの数値部分が最大のもののみ2を維持し、他は1に変更

    Args:
        rows: 対象データのリスト

    Returns:
        tuple: (調整後のリスト, 調整件数)
    """
    # PONO+POLINENOでグループ化
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        pono = row.get("PONO", "").strip()
        polineno = row.get("POLINENO", "").strip()
        key = (pono, polineno)
        groups[key].append(i)

    adjusted_count = 0

    for key, indices in groups.items():
        # このグループ内でEDKBN=2のインデックスを抽出
        edkbn2_indices = [i for i in indices if rows[i].get("EDKBN", "").strip() == "2"]

        if len(edkbn2_indices) <= 1:
            # EDKBN=2が0または1件なら調整不要
            continue

        # NOTEの数値部分が最大のものを特定
        max_note_num = -1
        max_index = None
        for i in edkbn2_indices:
            note = rows[i].get("NOTE", "").strip()
            note_num = extract_note_number(note)
            if note_num > max_note_num:
                max_note_num = note_num
                max_index = i

        # 最大以外のEDKBN=2を1に変更
        for i in edkbn2_indices:
            if i != max_index:
                pono = rows[i].get("PONO", "")
                polineno = rows[i].get("POLINENO", "")
                note = rows[i].get("NOTE", "")
                log(f"  EDKBN調整: PONO={pono}, POLINENO={polineno}, NOTE={note} → 2を1に変更")
                rows[i]["EDKBN"] = "1"
                adjusted_count += 1

    return rows, adjusted_count


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
    print("03_送信データフィルタリング")
    print("=" * 60)

    # 入力ファイル確認
    input_csv_path = work_dir / INPUT_CSV
    if not input_csv_path.exists():
        log(f"エラー: 入力ファイルが見つかりません: {input_csv_path}")
        return

    # ==========================================================================
    # APIデータ取得
    # ==========================================================================
    # D3350のNOTEデータ取得
    d3350_notes = fetch_d3350_notes()

    # D3340のSTATUS別データ取得
    d3340_completed, d3340_partial = fetch_d3340_status()

    # ==========================================================================
    # 入力CSV読み込み
    # ==========================================================================
    log(f"入力CSV読み込み中: {input_csv_path}")
    input_rows = []
    with open(input_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        for row in reader:
            input_rows.append(row)

    log(f"入力CSV読み込み完了: {len(input_rows)}件")

    # ==========================================================================
    # フィルタリング処理
    # ==========================================================================
    output_rows = []      # 送信対象
    excluded_rows = []    # 除外データ
    check_rows = []       # 要チェックデータ（一部完納）

    for row in input_rows:
        exclude_reason = None
        check_reason = None

        # フィルタ0: EJ_CREATED_DATE >= 2026/01/01（一時的な除外条件）
        ej_created_date = row.get("EJ_CREATED_DATE", "").strip()
        if ej_created_date >= "2026-01-01":
            exclude_reason = "EJ_CREATED_DATE>=2026/01/01(一時除外)"

        # フィルタ1: D3350.NOTEと一致（受入済み）
        if exclude_reason is None:
            note = row.get("NOTE", "").strip()
            if note in d3350_notes:
                exclude_reason = "受入済み(D3350.NOTE一致)"

        # フィルタ2: D3340で完納/強制完納
        if exclude_reason is None:
            pono = row.get("PONO", "").strip()
            polineno = row.get("POLINENO", "").strip()
            if (pono, polineno) in d3340_completed:
                exclude_reason = "完納/強制完納(D3340.STATUS=4or8)"

        # フィルタ3: D3340で一部完納（要チェック）
        if exclude_reason is None:
            pono = row.get("PONO", "").strip()
            polineno = row.get("POLINENO", "").strip()
            if (pono, polineno) in d3340_partial:
                check_reason = "一部完納(D3340.STATUS=3)"

        # 振り分け
        if exclude_reason:
            row[EXCLUDE_REASON_COLUMN] = exclude_reason
            excluded_rows.append(row)
        elif check_reason:
            row[EXCLUDE_REASON_COLUMN] = check_reason
            check_rows.append(row)
        else:
            output_rows.append(row)

    log(f"フィルタリング完了: 送信対象={len(output_rows)}, 除外={len(excluded_rows)}, 要チェック={len(check_rows)}")

    # ==========================================================================
    # EDKBN調整処理
    # ==========================================================================
    # 同じPONO+POLINENOでEDKBN=2が複数ある場合、NOTEの数値が最大のもののみ2を維持
    output_rows, edkbn_adjusted_count = adjust_edkbn(output_rows)
    log(f"EDKBN調整完了: {edkbn_adjusted_count}件を2→1に変更")

    # ==========================================================================
    # 出力
    # ==========================================================================
    # 03_送信データ.csv
    output_csv_path = work_dir / OUTPUT_CSV
    with open(output_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    log(f"出力: {output_csv_path} ({len(output_rows)}件)")

    # 03_除外データ.csv（除外理由カラム追加）
    excluded_fieldnames = fieldnames + [EXCLUDE_REASON_COLUMN]
    if excluded_rows:
        excluded_csv_path = work_dir / OUTPUT_EXCLUDED_CSV
        with open(excluded_csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=excluded_fieldnames)
            writer.writeheader()
            writer.writerows(excluded_rows)
        log(f"出力: {excluded_csv_path} ({len(excluded_rows)}件)")

    # 03_除外データ（要チェック）.csv（一部完納）
    if check_rows:
        check_csv_path = work_dir / OUTPUT_CHECK_CSV
        with open(check_csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=excluded_fieldnames)
            writer.writeheader()
            writer.writerows(check_rows)
        log(f"出力: {check_csv_path} ({len(check_rows)}件)")

    print("=" * 60)
    print(f"完了:")
    print(f"  送信対象:   {len(output_rows)}件 → {OUTPUT_CSV}")
    print(f"  除外:       {len(excluded_rows)}件 → {OUTPUT_EXCLUDED_CSV}")
    print(f"  要チェック: {len(check_rows)}件 → {OUTPUT_CHECK_CSV}")
    print("=" * 60)


if __name__ == "__main__":
    main()
