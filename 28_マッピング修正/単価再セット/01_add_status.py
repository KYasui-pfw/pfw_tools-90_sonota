# -*- coding: utf-8 -*-
"""
仕入単価確認.csvにD3340のSTATUSを追加するスクリプト
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
INPUT_FILE = SCRIPT_DIR / '仕入単価確認.csv'
OUTPUT_FILE = SCRIPT_DIR / '01_status追加.csv'


def get_status_and_lineno2_from_d3340(pono_lineno_list: list[tuple[str, int]]) -> tuple[dict, dict]:
    """
    D3340からPONO+LINENOでSTATUSとLINENO_2を取得

    Args:
        pono_lineno_list: [(PONO, LINENO), ...] のリスト

    Returns:
        (status_dict, lineno2_dict) のタプル
        - status_dict: {(PONO, LINENO): STATUS, ...}
        - lineno2_dict: {(PONO, LINENO): LINENO_2, ...}
    """
    # PONOのユニークリストを作成
    pono_list = list(set([p[0] for p in pono_lineno_list]))

    # D3340から全データ取得（PONO毎の全LINENO）
    all_rows = []
    batch_size = 500
    for i in range(0, len(pono_list), batch_size):
        batch_ponos = pono_list[i:i + batch_size]

        payload = {
            'table': 'D3340',
            'columns': ['PONO', 'LINENO', 'STATUS'],
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

    # STATUS辞書を作成
    status_dict = {}
    for row in all_rows:
        key = (row['PONO'], row['LINENO'])
        status_dict[key] = row.get('STATUS')

    # LINENO_2辞書を作成（PONO毎にLINENO昇順で連番）
    lineno2_dict = {}
    # PONO毎にグループ化
    from collections import defaultdict
    pono_linenos = defaultdict(list)
    for row in all_rows:
        pono_linenos[row['PONO']].append(row['LINENO'])

    # 各PONOについて、LINENO昇順でソートしてLINENO_2を割り当て
    for pono, linenos in pono_linenos.items():
        sorted_linenos = sorted(set(linenos))  # 重複を除いてソート
        for idx, lineno in enumerate(sorted_linenos, start=1):
            lineno2_dict[(pono, lineno)] = idx

    return status_dict, lineno2_dict


def main():
    print("=== STATUS追加処理 開始 ===")

    # CSV読み込み
    print(f"\n1. CSV読み込み: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"   レコード数: {len(df)}")

    # PONO+LINENOのリスト作成（PONOは9桁ゼロ埋め）
    pono_lineno_list = list(zip(
        df['rBOM発注番号'].apply(lambda x: str(x).zfill(9)),
        df['rBOM行番号'].astype(int)
    ))

    # D3340からSTATUSとLINENO_2取得
    print(f"\n2. D3340からSTATUS・LINENO_2取得中...")
    status_dict, lineno2_dict = get_status_and_lineno2_from_d3340(pono_lineno_list)
    print(f"   STATUS取得件数: {len(status_dict)}")
    print(f"   LINENO_2取得件数: {len(lineno2_dict)}")

    # STATUS列を追加（PONOは9桁ゼロ埋め）
    print(f"\n3. STATUS列を追加中...")
    df['STATUS'] = df.apply(
        lambda row: status_dict.get((str(row['rBOM発注番号']).zfill(9), int(row['rBOM行番号']))),
        axis=1
    )

    # 結果サマリ
    status_counts = df['STATUS'].value_counts(dropna=False)
    print(f"\n   STATUS分布:")
    for status, count in status_counts.items():
        status_label = status if pd.notna(status) else '(NULL)'
        print(f"     {status_label}: {count}件")

    # LINENO_2を追加（D3340の全行ベースで算出済み）
    print(f"\n4. LINENO_2を追加中...")
    df['LINENO_2'] = df.apply(
        lambda row: lineno2_dict.get((str(row['rBOM発注番号']).zfill(9), int(row['rBOM行番号']))),
        axis=1
    )
    print(f"   LINENO_2追加完了")

    # CSV出力
    print(f"\n5. CSV出力: {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    print("\n=== 処理完了 ===")


if __name__ == '__main__':
    main()
