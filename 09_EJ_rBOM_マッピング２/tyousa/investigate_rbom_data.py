"""
rBOM APIデータ取得調査スクリプト
D3340テーブルのデータがなぜ少なく取得されるか調査
"""
import requests
import json
from datetime import date, datetime
from collections import defaultdict

# API設定
BASE_URL = 'http://pfw-api'
API_KEY = r'oG5^Ls%#20yq'
HEADERS = {
    'X-API-KEY': API_KEY,
    'accept': 'application/json'
}

def get_orders(year: int, month: int):
    """指定年月のデータを取得"""
    params = {'year': year, 'month': month}
    try:
        response = requests.get(
            f"{BASE_URL}/orders/",
            params=params,
            headers=HEADERS,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  エラー: {e}")
        return []

def main():
    print("=" * 80)
    print("rBOM API データ取得調査")
    print("=" * 80)

    # 調査対象期間: 2025年11月 ～ 2026年6月
    months_to_check = [
        (2025, 11), (2025, 12),
        (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5), (2026, 6),
        (2026, 7), (2026, 8), (2026, 9), (2026, 10), (2026, 11), (2026, 12),
        (2027, 1)
    ]

    total_records = 0
    monthly_stats = {}
    all_data = []

    print("\n【1】月別データ取得件数")
    print("-" * 60)

    for year, month in months_to_check:
        data = get_orders(year, month)
        count = len(data)
        total_records += count
        monthly_stats[(year, month)] = count
        all_data.extend(data)
        print(f"  {year}年{month:02d}月: {count:,}件")

    print(f"\n  合計: {total_records:,}件")

    if not all_data:
        print("\nデータが取得できませんでした。")
        return

    # GETSUJIとDRVDTの分析
    print("\n【2】GETSUJI（月次）の分布")
    print("-" * 60)

    getsuji_counts = defaultdict(int)
    for item in all_data:
        getsuji = item.get('GETSUJI') or 'NULL'
        getsuji_counts[getsuji] += 1

    for getsuji in sorted(getsuji_counts.keys()):
        print(f"  GETSUJI={getsuji}: {getsuji_counts[getsuji]:,}件")

    # DRVDTの分析
    print("\n【3】DRVDT（納期）の月別分布")
    print("-" * 60)

    drvdt_counts = defaultdict(int)
    drvdt_null_count = 0

    for item in all_data:
        drvdt = item.get('DRVDT')
        if drvdt:
            try:
                drvdt_month = drvdt[:7]  # YYYY-MM
                drvdt_counts[drvdt_month] += 1
            except:
                drvdt_counts['INVALID'] += 1
        else:
            drvdt_null_count += 1

    for drvdt_month in sorted(drvdt_counts.keys()):
        print(f"  DRVDT月={drvdt_month}: {drvdt_counts[drvdt_month]:,}件")

    if drvdt_null_count > 0:
        print(f"  DRVDT=NULL: {drvdt_null_count:,}件")

    # GETSUJIとDRVDT月のクロス分析
    print("\n【4】GETSUJIとDRVDT月のクロス分析（乖離確認）")
    print("-" * 60)

    cross_analysis = defaultdict(int)
    mismatch_examples = []

    for item in all_data:
        getsuji = item.get('GETSUJI') or 'NULL'
        drvdt = item.get('DRVDT')

        if drvdt:
            drvdt_month = drvdt[:7].replace('-', '')  # YYYYMM形式
        else:
            drvdt_month = 'NULL'

        # GETSUJIの先頭6桁とDRVDT月を比較
        getsuji_prefix = str(getsuji)[:6] if getsuji != 'NULL' else 'NULL'

        cross_analysis[(getsuji_prefix, drvdt_month)] += 1

        # 乖離例を収集（GETSUJIとDRVDT月が異なるケース）
        if getsuji_prefix != 'NULL' and drvdt_month != 'NULL' and getsuji_prefix != drvdt_month:
            if len(mismatch_examples) < 10:
                mismatch_examples.append({
                    'PONO': item.get('PONO'),
                    'LINENO': item.get('LINENO'),
                    'GETSUJI': getsuji,
                    'DRVDT': drvdt,
                    'HMCD': item.get('HMCD')
                })

    print("\n  GETSUJI(先頭6桁) | DRVDT月 | 件数")
    print("  " + "-" * 40)
    for (getsuji_prefix, drvdt_month), count in sorted(cross_analysis.items()):
        match_mark = "○" if getsuji_prefix == drvdt_month else "×"
        print(f"  {getsuji_prefix:>14} | {drvdt_month:>7} | {count:>6,}件 {match_mark}")

    if mismatch_examples:
        print("\n【5】GETSUJI≠DRVDT月のデータ例（最大10件）")
        print("-" * 60)
        for ex in mismatch_examples:
            print(f"  PONO={ex['PONO']}, LINENO={ex['LINENO']}")
            print(f"    GETSUJI={ex['GETSUJI']}, DRVDT={ex['DRVDT']}, HMCD={ex['HMCD']}")

    # D3010とのJOIN状況
    print("\n【6】D3010_SEINO（製番JOIN）の状況")
    print("-" * 60)

    d3010_joined = sum(1 for item in all_data if item.get('D3010_SEINO'))
    d3010_null = sum(1 for item in all_data if not item.get('D3010_SEINO'))

    print(f"  D3010とJOIN成功: {d3010_joined:,}件")
    print(f"  D3010とJOIN失敗（NULL）: {d3010_null:,}件")

    # 結果をJSONファイルに保存
    output_file = "C:/Dev/90_tools/09_EJ_rBOM_マッピング２/tyousa/rbom_data_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_records': total_records,
            'monthly_stats': {f"{y}-{m:02d}": c for (y, m), c in monthly_stats.items()},
            'getsuji_distribution': dict(getsuji_counts),
            'drvdt_distribution': dict(drvdt_counts),
            'mismatch_examples': mismatch_examples
        }, f, ensure_ascii=False, indent=2)

    print(f"\n詳細データを保存: {output_file}")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
