# -*- coding: utf-8 -*-
"""
02_受入単価修正
01_status追加.csvからSTATUS=3,4,8のデータを抽出し、
D3360からRCVNO, LINENOを取得して追加する
"""

import pandas as pd
import requests
from pathlib import Path

# 設定
API_URL = 'http://pfw-api/query'
API_HEADERS = {
    'Content-Type': 'application/json',
    'X-API-KEY': 'oG5^Ls%#20yq'
}

SCRIPT_DIR = Path(__file__).parent
INPUT_FILE = SCRIPT_DIR / '01_status追加.csv'
OUTPUT_FILE = SCRIPT_DIR / '02_受入単価修正.csv'

# 対象STATUS
TARGET_STATUS = [3, 4, 8]


def get_rcvno_lineno_from_d3360(pono_polineno_list: list[tuple[str, int]]) -> tuple[dict, dict]:
    """
    D3360からPONO+POLINENOでRCVNO, LINENO, LINENO_2を取得

    Args:
        pono_polineno_list: [(PONO, POLINENO), ...] のリスト

    Returns:
        (rcvno_dict, lineno2_dict) のタプル
        - rcvno_dict: {(PONO, POLINENO): [(RCVNO, LINENO), ...], ...}
        - lineno2_dict: {(RCVNO, LINENO): LINENO_2, ...}
    """
    from collections import defaultdict

    # PONOのユニークリストを作成
    pono_list = list(set([p[0] for p in pono_polineno_list]))

    # D3360から全データ取得
    all_rows = []
    batch_size = 500
    for i in range(0, len(pono_list), batch_size):
        batch_ponos = pono_list[i:i + batch_size]

        payload = {
            'table': 'D3360',
            'columns': ['PONO', 'POLINENO', 'RCVNO', 'LINENO'],
            'where': {'PONO': {'in': batch_ponos}},
            'limit': 10000
        }

        try:
            response = requests.post(API_URL, headers=API_HEADERS, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            if 'rows' in data:
                all_rows.extend(data['rows'])

            print(f"  取得完了: {i + len(batch_ponos)}/{len(pono_list)} PONOs")

        except Exception as e:
            print(f"  エラー: {e}")

    # PONO+POLINENO毎のRCVNO, LINENOリスト
    rcvno_dict = {}
    for row in all_rows:
        key = (row['PONO'], row['POLINENO'])
        if key not in rcvno_dict:
            rcvno_dict[key] = []
        rcvno_dict[key].append((row['RCVNO'], row['LINENO']))

    # RCVNO毎にLINENO昇順で連番を振る（LINENO_2）
    lineno2_dict = {}
    rcvno_linenos = defaultdict(list)
    for row in all_rows:
        rcvno_linenos[row['RCVNO']].append(row['LINENO'])

    for rcvno, linenos in rcvno_linenos.items():
        sorted_linenos = sorted(set(linenos))
        for idx, lineno in enumerate(sorted_linenos, start=1):
            lineno2_dict[(rcvno, lineno)] = idx

    return rcvno_dict, lineno2_dict


def main():
    print("=== 受入単価修正データ作成 開始 ===")

    # CSV読み込み
    print(f"\n1. CSV読み込み: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"   全レコード数: {len(df)}")

    # STATUS=3,4,8のみ抽出
    print(f"\n2. STATUS={TARGET_STATUS}のデータを抽出...")
    df_target = df[df['STATUS'].isin(TARGET_STATUS)].copy()
    print(f"   対象レコード数: {len(df_target)}")

    # STATUS分布
    status_counts = df_target['STATUS'].value_counts().sort_index()
    for status, count in status_counts.items():
        print(f"     STATUS={status}: {count}件")

    # PONO+POLINENOのリスト作成（PONOは9桁ゼロ埋め）
    pono_polineno_list = list(zip(
        df_target['rBOM発注番号'].apply(lambda x: str(x).zfill(9)),
        df_target['rBOM行番号'].astype(int)
    ))

    # D3360からRCVNO, LINENO, LINENO_2取得
    print(f"\n3. D3360からRCVNO, LINENO, LINENO_2取得中...")
    rcvno_dict, lineno2_dict = get_rcvno_lineno_from_d3360(pono_polineno_list)
    print(f"   取得キー数: {len(rcvno_dict)}")
    print(f"   LINENO_2取得数: {len(lineno2_dict)}")

    # RCVNO, LINENO列を追加（LEFT JOIN：複数ヒット時は行を展開）
    print(f"\n4. RCVNO, LINENO列を追加中（LEFT JOIN）...")

    rows_expanded = []
    for _, row in df_target.iterrows():
        key = (str(row['rBOM発注番号']).zfill(9), int(row['rBOM行番号']))
        values = rcvno_dict.get(key, [])

        if values:
            # 複数ヒット時は行を展開
            for rcvno, lineno in values:
                new_row = row.copy()
                new_row['RCVNO'] = rcvno
                new_row['D3360_LINENO'] = lineno
                new_row['D3360_LINENO_2'] = lineno2_dict.get((rcvno, lineno))
                rows_expanded.append(new_row)
        else:
            # ヒットなしの場合はNULL
            new_row = row.copy()
            new_row['RCVNO'] = None
            new_row['D3360_LINENO'] = None
            new_row['D3360_LINENO_2'] = None
            rows_expanded.append(new_row)

    df_result = pd.DataFrame(rows_expanded)

    # 結果サマリ
    print(f"   展開前: {len(df_target)}件")
    print(f"   展開後: {len(df_result)}件")
    rcvno_found = df_result['RCVNO'].notna().sum()
    rcvno_not_found = df_result['RCVNO'].isna().sum()
    print(f"   RCVNO取得成功: {rcvno_found}件")
    print(f"   RCVNO取得失敗: {rcvno_not_found}件")

    # CSV出力
    print(f"\n5. CSV出力: {OUTPUT_FILE}")
    df_result.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    print("\n=== 処理完了 ===")


if __name__ == '__main__':
    main()
