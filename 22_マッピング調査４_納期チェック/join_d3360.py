"""
join_d3360.py

CSVのrBOM発注番号+行番号とD3360をLEFT JOINするスクリプト

入力: rBOM_PONO+LINENO.csv
出力: joined_d3360.csv
"""
import os
import pandas as pd
import httpx
from dotenv import load_dotenv

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(SCRIPT_DIR, "rBOM_PONO+LINENO.csv")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "joined_d3360.csv")

# API設定
ENV_PATH = r"C:\Dev\01_Back_APIServer\fastapi_app\.env"
API_BASE_URL = "http://pfw-api/query"


def load_api_key():
    """APIキーを読み込み"""
    load_dotenv(ENV_PATH)
    return os.getenv("READ_API_KEY")


def parse_rbom_key(val):
    """rBOM発注番号+行番号をPONOとPOLINENOに分解"""
    if pd.isna(val):
        return None, None
    s = str(val)
    pono = s[:9]
    if '+' in s:
        polineno = int(s.split('+')[1])
    else:
        polineno = None
    return pono, polineno


def fetch_d3360_data(api_key, pono_list):
    """
    D3360からPONO, POLINENO, NOTEを一括取得

    Args:
        api_key: READ_API_KEY
        pono_list: PONOのリスト

    Returns:
        dict: {(PONO, POLINENO): NOTE, ...}
    """
    result = {}
    unique_ponos = list(set(pono_list))

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    print(f"D3360からデータ取得中... (対象PONO数: {len(unique_ponos)})")

    # バッチで取得（100件ずつ）
    batch_size = 100
    total_fetched = 0

    with httpx.Client(timeout=60.0) as client:
        for i in range(0, len(unique_ponos), batch_size):
            batch_ponos = unique_ponos[i:i+batch_size]

            payload = {
                "table": "D3360",
                "columns": ["PONO", "POLINENO", "NOTE"],
                "where": {
                    "and": [
                        {"PONO": {"in": batch_ponos}}
                    ]
                },
                "limit": 10000
            }

            try:
                response = client.post(API_BASE_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                rows = data.get("rows", [])
                for row in rows:
                    pono = row.get("PONO")
                    polineno = row.get("POLINENO")
                    note = row.get("NOTE")
                    if pono and polineno is not None:
                        result[(pono, int(polineno))] = note

                total_fetched += len(rows)
                print(f"  バッチ {i//batch_size + 1}/{(len(unique_ponos)-1)//batch_size + 1}: {len(rows)}件取得")

            except Exception as e:
                print(f"  バッチ {i//batch_size + 1}: エラー - {e}")

    print(f"D3360から合計 {total_fetched} 件取得完了")
    return result


def main():
    print("=" * 60)
    print("CSV と D3360 LEFT JOIN 処理")
    print("=" * 60)
    print()

    # APIキー読み込み
    api_key = load_api_key()
    if not api_key:
        print("エラー: READ_API_KEYが見つかりません")
        return 1

    # CSV読み込み
    print(f"入力ファイル: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, encoding='cp932')
    print(f"読み込み行数: {len(df)}")
    print()

    # PONO, POLINENOを分解
    df['PONO'] = df['rBOM発注番号+行番号'].apply(lambda x: parse_rbom_key(x)[0])
    df['POLINENO'] = df['rBOM発注番号+行番号'].apply(lambda x: parse_rbom_key(x)[1])

    # D3360からデータ取得
    pono_list = df['PONO'].dropna().tolist()
    d3360_dict = fetch_d3360_data(api_key, pono_list)
    print()

    # LEFT JOIN（NOTEをマッピング）
    # D3360にデータがあるがNOTEが空/NULLの場合は「注意」と出力
    # D3360にデータがない場合は空欄のまま
    def get_note_with_warning(row):
        if pd.isna(row['POLINENO']):
            return None
        key = (row['PONO'], int(row['POLINENO']))
        if key in d3360_dict:
            note = d3360_dict[key]
            if note is None or note == '' or (isinstance(note, str) and note.strip() == ''):
                return '注意'
            return note
        return None  # D3360にデータなしの場合は空欄

    df['NOTE'] = df.apply(get_note_with_warning, axis=1)

    # 結果サマリー
    print("=" * 60)
    print("結果サマリー")
    print("=" * 60)

    total = len(df)
    # NOTEがNoneでもD3360にデータがあるケースがあるので、別途カウント
    has_d3360 = sum(1 for _, row in df.iterrows() if (row['PONO'], int(row['POLINENO']) if pd.notna(row['POLINENO']) else None) in d3360_dict)
    note_warning = (df['NOTE'] == '注意').sum()
    note_has_value = df['NOTE'].notna().sum() - note_warning

    print(f"総件数: {total}")
    print(f"D3360にデータあり: {has_d3360}")
    print(f"D3360にデータなし: {total - has_d3360}")
    print(f"NOTEあり（値あり）: {note_has_value}")
    print(f"NOTEなし（注意）: {note_warning}")
    print()

    # CSV出力
    output_df = df[['rBOM発注番号+行番号', 'PONO', 'POLINENO', 'NOTE']]
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='cp932')
    print(f"結果出力: {OUTPUT_CSV}")

    # NOTEありの例を表示
    note_rows = df[df['NOTE'].notna()].head(10)
    if len(note_rows) > 0:
        print()
        print("=== NOTEありの例（上位10件）===")
        for _, row in note_rows.iterrows():
            print(f"  {row['rBOM発注番号+行番号']}: NOTE={row['NOTE']}")

    return 0


if __name__ == "__main__":
    exit(main())
