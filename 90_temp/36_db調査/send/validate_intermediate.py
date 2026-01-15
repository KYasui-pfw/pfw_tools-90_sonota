# -*- coding: utf-8 -*-
"""
intermediate.csv の検証スクリプト
"""

import os
import csv
import requests
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "intermediate.csv")

API_BASE_URL = "http://pfw-api"
API_KEY = "oG5^Ls%#20yq"


def query_d3340_by_pono(pono_list):
    """D3340テーブルからPONOでデータ取得"""
    url = f"{API_BASE_URL}/query"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "table": "D3340",
        "columns": ["PONO", "LINENO", "HMCD", "QTY"],
        "where": {
            "or": [{"PONO": {"eq": pono}} for pono in pono_list]
        },
        "limit": 10000
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("intermediate.csv 検証")
    print("=" * 60)
    print()

    # CSV読み込み
    rows = []
    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"総行数: {len(rows)}")
    print()

    # ========================================
    # 1. 空白チェック
    # ========================================
    print("【1. 空白チェック】")
    whitespace_issues = []
    for i, row in enumerate(rows, start=2):
        for key, val in row.items():
            if val != val.strip():
                whitespace_issues.append((i, key, repr(val)))

    if whitespace_issues:
        print(f"  ⚠ 空白を含むセル: {len(whitespace_issues)}件")
        for line, col, val in whitespace_issues[:10]:
            print(f"    行{line}: {col}={val}")
        if len(whitespace_issues) > 10:
            print(f"    ... 他 {len(whitespace_issues) - 10}件")
    else:
        print("  ✓ 空白問題なし")
    print()

    # ========================================
    # 2. RCVQTYチェック
    # ========================================
    print("【2. RCVQTY（受入数）チェック】")
    rcvqty_values = [float(row["RCVQTY"].strip()) for row in rows]
    rcvqty_counter = Counter(rcvqty_values)

    print(f"  RCVQTY分布:")
    for val, cnt in sorted(rcvqty_counter.items()):
        print(f"    {val}: {cnt}件")

    zero_count = rcvqty_counter.get(0, 0) + rcvqty_counter.get(0.0, 0)
    if zero_count == len(rows):
        print(f"  ⚠ 全行RCVQTY=0 です！受入数0で登録してよいですか？")
    print()

    # ========================================
    # 3. EJNO重複チェック
    # ========================================
    print("【3. EJNO重複チェック】")
    ejno_list = [row["EJNO"].strip() for row in rows]
    ejno_counter = Counter(ejno_list)
    duplicates = [(ejno, cnt) for ejno, cnt in ejno_counter.items() if cnt > 1]

    if duplicates:
        print(f"  ⚠ 重複EJNO: {len(duplicates)}件")
        for ejno, cnt in duplicates:
            print(f"    {ejno}: {cnt}回")
            # 該当行を表示
            for i, row in enumerate(rows, start=2):
                if row["EJNO"].strip() == ejno:
                    print(f"      行{i}: PONO={row['PONO'].strip()}, LINENO={row['POLINENO'].strip()}")
    else:
        print("  ✓ EJNO重複なし")
    print()

    # ========================================
    # 4. PONO+LINENO重複チェック
    # ========================================
    print("【4. PONO+LINENO重複チェック】")
    pono_lineno_list = [(row["PONO"].strip().zfill(9), int(row["POLINENO"].strip())) for row in rows]
    pono_lineno_counter = Counter(pono_lineno_list)
    pl_duplicates = [(pl, cnt) for pl, cnt in pono_lineno_counter.items() if cnt > 1]

    if pl_duplicates:
        print(f"  ⚠ 重複PONO+LINENO: {len(pl_duplicates)}件")
        for (pono, lineno), cnt in pl_duplicates:
            print(f"    PONO={pono}, LINENO={lineno}: {cnt}回")
    else:
        print("  ✓ PONO+LINENO重複なし")
    print()

    # ========================================
    # 5. D3340存在チェック（API）
    # ========================================
    print("【5. D3340存在チェック】")
    unique_pono_lineno = list(set(pono_lineno_list))
    print(f"  ユニークPONO+LINENO数: {len(unique_pono_lineno)}")

    # ユニークなPONOリストを取得
    unique_pono = list(set([p for p, l in unique_pono_lineno]))
    print(f"  ユニークPONO数: {len(unique_pono)}")

    print("  D3340からデータ取得中...")
    all_d3340 = []
    batch_size = 100

    for i in range(0, len(unique_pono), batch_size):
        batch = unique_pono[i:i+batch_size]
        try:
            result = query_d3340_by_pono(batch)
            if "rows" in result:
                all_d3340.extend(result["rows"])
        except Exception as e:
            print(f"    エラー: {e}")

    print(f"  D3340取得件数: {len(all_d3340)}")

    # 存在するPONO+LINENOのセット
    d3340_set = set()
    d3340_info = {}
    for row in all_d3340:
        key = (str(row["PONO"]), int(row["LINENO"]))
        d3340_set.add(key)
        d3340_info[key] = row

    # 存在しないものを検出
    not_found = []
    for pono, lineno in unique_pono_lineno:
        if (pono, lineno) not in d3340_set:
            not_found.append((pono, lineno))

    if not_found:
        print(f"  ⚠ D3340に存在しない: {len(not_found)}件")
        for pono, lineno in not_found[:10]:
            print(f"    PONO={pono}, LINENO={lineno}")
        if len(not_found) > 10:
            print(f"    ... 他 {len(not_found) - 10}件")
    else:
        print("  ✓ 全てD3340に存在")
    print()

    # ========================================
    # 6. D3340のSURYO（発注数）確認
    # ========================================
    print("【6. D3340発注数との比較】")
    print("  サンプル（先頭10件）:")
    for i, row in enumerate(rows[:10], start=2):
        pono = row["PONO"].strip().zfill(9)
        lineno = int(row["POLINENO"].strip())
        rcvqty = float(row["RCVQTY"].strip())
        ejno = row["EJNO"].strip()

        key = (pono, lineno)
        if key in d3340_info:
            qty = d3340_info[key].get("QTY", "?")
            hmcd = d3340_info[key].get("HMCD", "?")
            print(f"    {ejno}: PONO={pono}+{lineno}, RCVQTY={rcvqty}, D3340.QTY={qty}, HMCD={hmcd}")
        else:
            print(f"    {ejno}: PONO={pono}+{lineno}, RCVQTY={rcvqty}, D3340に存在しない")
    print()

    # ========================================
    # サマリー
    # ========================================
    print("=" * 60)
    print("検証サマリー")
    print("=" * 60)
    issues = []
    if whitespace_issues:
        issues.append(f"空白問題: {len(whitespace_issues)}件（処理時にstrip()されるので問題なし）")
    if zero_count == len(rows):
        issues.append("全行RCVQTY=0 ← 要確認")
    if duplicates:
        issues.append(f"EJNO重複: {len(duplicates)}件 ← 要確認")
    if pl_duplicates:
        issues.append(f"PONO+LINENO重複: {len(pl_duplicates)}件 ← 要確認")
    if not_found:
        issues.append(f"D3340不存在: {len(not_found)}件 ← 要確認")

    if issues:
        print("⚠ 確認が必要な項目:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ 問題なし")

    return 0


if __name__ == "__main__":
    exit(main())
