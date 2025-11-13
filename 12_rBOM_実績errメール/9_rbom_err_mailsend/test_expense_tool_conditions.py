# test_expense_tool_conditions.py
# 経費工具受入メールの発信条件を検証するスクリプト

import sys
import io
import requests
import json
from datetime import datetime, timedelta
from app.config import config

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# FastAPI接続設定
# Dockerネットワーク内では http://fastapi:8000
# ローカル/本番では http://pfw-api または http://127.0.0.1:8000
API_URL = "http://pfw-api/query"
HEADERS = {"X-API-KEY": config.READ_API_KEY}

print("=" * 80)
print("経費工具受入メール発信条件の検証")
print("=" * 80)
print()

# ========================================
# 【検証1】DK020でSYORIZUMIKBN='2'のレコード数を確認
# ========================================
print("【検証1】DK020で正常終了(SYORIZUMIKBN='2')のレコード数を確認")
print("-" * 80)

payload_dk020_all = {
    "table": "DK020",
    "columns": ["PONO", "POLINENO", "INSTDT", "IPTANCD", "SYORIZUMIKBN"],
    "where": {
        "SYORIZUMIKBN": "2"
    }
}

try:
    response = requests.post(API_URL, json=payload_dk020_all, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    dk020_records = data.get("rows", [])

    print(f"✅ DK020正常終了レコード数: {len(dk020_records)}件")
    print()

    # 最新5件を表示
    if dk020_records:
        print("📋 最新5件のサンプル:")
        for i, rec in enumerate(dk020_records[:5], 1):
            print(f"  {i}. PONO={rec.get('PONO')}, LINENO={rec.get('POLINENO')}, "
                  f"INSTDT={rec.get('INSTDT')}, IPTANCD={rec.get('IPTANCD')}")
        print()

except requests.exceptions.RequestException as e:
    print(f"❌ エラー: {e}")
    print()
    dk020_records = []

# ========================================
# 【検証2】各DK020レコードについてD3340を照会（monitor.pyと同じロジック）
# ========================================
print("【検証2】各DK020レコードについてD3340を照会してSEINOを確認")
print("-" * 80)

keihi_count = 0
non_keihi_count = 0
error_count = 0
d3340_keihi_records = []
seino_values = {}  # SEINOの値の分布を記録

print(f"※ {len(dk020_records)}件について1件ずつD3340を照会します（最大10件表示）")
print()

for i, dk_rec in enumerate(dk020_records[:10], 1):  # 最初の10件のみ処理
    pono = dk_rec.get("PONO")
    polineno = dk_rec.get("POLINENO")

    # D3340から詳細情報を取得（monitor.pyと同じクエリ）
    detail_payload = {
        "table": "D3340",
        "columns": ["SEINO", "HMNM", "SRCD"],
        "where": {
            "and": [
                {"PONO": pono},
                {"LINENO": polineno}
            ]
        }
    }

    try:
        detail_response = requests.post(API_URL, json=detail_payload, headers=HEADERS, timeout=30)
        detail_response.raise_for_status()
        detail_data = detail_response.json()
        detail_rows = detail_data.get("rows", [])

        if not detail_rows:
            print(f"  {i}. PONO={pono}, LINENO={polineno} → D3340にデータなし")
            error_count += 1
            continue

        detail = detail_rows[0]
        seino = detail.get("SEINO", "")

        # SEINOの値を集計
        seino_values[seino] = seino_values.get(seino, 0) + 1

        if seino == "KEIHI":
            keihi_count += 1
            d3340_keihi_records.append({
                "PONO": pono,
                "LINENO": polineno,
                "INSTDT": dk_rec.get("INSTDT"),
                "IPTANCD": dk_rec.get("IPTANCD"),
                "SEINO": seino,
                "HMNM": detail.get("HMNM"),
                "SRCD": detail.get("SRCD")
            })
            print(f"  {i}. PONO={pono}, LINENO={polineno} → SEINO='{seino}' ★[経費工具]")
            print(f"      HMNM={detail.get('HMNM')}, SRCD={detail.get('SRCD')}")
        else:
            non_keihi_count += 1
            if i <= 3:  # 最初の3件のみ詳細表示
                print(f"  {i}. PONO={pono}, LINENO={polineno} → SEINO='{seino}'")

    except requests.exceptions.RequestException as e:
        print(f"  {i}. PONO={pono}, LINENO={polineno} → エラー: {e}")
        error_count += 1

print()
print(f"✅ 集計結果（最初の10件中）:")
print(f"   SEINO='KEIHI' (経費工具): {keihi_count}件")
print(f"   SEINO!='KEIHI' (非経費工具): {non_keihi_count}件")
print(f"   D3340データなし/エラー: {error_count}件")
print()
print(f"📊 SEINOの値の分布:")
for seino_val, count in sorted(seino_values.items(), key=lambda x: x[1], reverse=True):
    print(f"   '{seino_val}': {count}件")
print()

# ========================================
# 【検証3】経費工具レコードの詳細確認
# ========================================
print("【検証3】経費工具レコードの詳細確認")
print("-" * 80)

matched_records = d3340_keihi_records

if matched_records:
    print(f"✅ 経費工具レコード数: {len(matched_records)}件")
    print()

    print("📋 詳細情報（全件）:")
    for i, rec in enumerate(matched_records, 1):
        print(f"  {i}. PONO={rec['PONO']}, LINENO={rec['LINENO']}")
        print(f"      INSTDT={rec['INSTDT']}")
        print(f"      IPTANCD（受入者）={rec['IPTANCD']}")
        print(f"      SEINO={rec['SEINO']}")
        print(f"      SRCD（仕入先）={rec['SRCD']}")
        print(f"      HMNM={rec['HMNM']}")
        print()
else:
    print("⚠️  経費工具レコードが見つかりませんでした")
    print()

# ========================================
# 【検証4】D3330から発注担当者情報を確認
# ========================================
print("【検証4】D3330から発注担当者情報を確認（サンプル）")
print("-" * 80)

if matched_records:
    sample_pono = matched_records[0].get("PONO")

    payload_d3330 = {
        "table": "D3330",
        "columns": ["PONO", "TANCD", "IPTANCD", "SRCD", "PODT"],
        "where": {
            "PONO": sample_pono
        }
    }

    try:
        response = requests.post(API_URL, json=payload_d3330, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        d3330_records = data.get("rows", [])

        if d3330_records:
            d3330_rec = d3330_records[0]
            print(f"✅ サンプルPONO={sample_pono}の発注情報:")
            print(f"   TANCD（発注担当）={d3330_rec.get('TANCD')}")
            print(f"   IPTANCD（入力担当）={d3330_rec.get('IPTANCD')}")
            print(f"   SRCD（仕入先）={d3330_rec.get('SRCD')}")
            print(f"   PODT（発注日）={d3330_rec.get('PODT')}")
            print()
        else:
            print(f"⚠️  D3330にPONO={sample_pono}のデータが見つかりません")
            print()

    except requests.exceptions.RequestException as e:
        print(f"❌ エラー: {e}")
        print()

# ========================================
# 【検証5】現在の実装での処理フロー確認
# ========================================
print("【検証5】現在の実装での処理効率の分析")
print("-" * 80)

total_dk020 = len(dk020_records)
total_keihi = keihi_count
total_non_keihi = non_keihi_count

print("現在の実装:")
print(f"  ステップ1: DK020でSYORIZUMIKBN='2'を全件取得")
print(f"             → {total_dk020}件")
print()
print(f"  ステップ2: 各レコードについてD3340を個別照会（N+1問題）")
print(f"             → 最大{total_dk020}回のAPI呼び出し")
print()
print(f"  ステップ3: SEINO='KEIHI'のみメール送信処理")
print(f"             → 実際に処理される件数: {total_keihi}件（サンプル10件中）")
print()
print(f"💡 処理効率:")
if total_dk020 > 0:
    efficiency = (total_keihi / min(10, total_dk020)) * 100
    waste = (total_non_keihi / min(10, total_dk020)) * 100
    print(f"   有効な処理: {efficiency:.1f}% ({total_keihi}/{min(10, total_dk020)}件)")
    print(f"   無駄な処理: {waste:.1f}% ({total_non_keihi}/{min(10, total_dk020)}件)")
print()

# ========================================
# 【推奨】改善案
# ========================================
print("=" * 80)
print("【推奨】改善案")
print("=" * 80)
print()
print("問題点:")
print("  ❌ DK020の全正常終了データを毎回取得（過去データも含む）")
print("  ❌ D3340を1件ずつ照会（N+1問題でパフォーマンス悪化）")
print("  ❌ 大部分のレコードがSEINO!='KEIHI'で無駄なAPI呼び出し")
print()
print("改善案1: 日付フィルタを追加")
print("  ✅ DK020のINSTDTで直近7日間などに絞る")
print("  ✅ 過去データの再チェックを防止")
print()
print("改善案2: JOINクエリまたはバッチ取得")
print("  ✅ D3340でSEINO='KEIHI'のPONO一覧を先に取得")
print("  ✅ DK020をIN句でフィルタリング")
print("  ✅ API呼び出しを2回に削減")
print()
print("改善案3: 送信済みチェックの最適化")
print("  ✅ 現状: 毎回全件チェック後に送信済み確認")
print("  ✅ 改善: 未送信レコードのみを最初から絞り込む")
print()

print("=" * 80)
print("検証完了")
print("=" * 80)
