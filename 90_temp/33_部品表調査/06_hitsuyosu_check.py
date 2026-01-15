"""
必要数一覧と品目工程・品目構成マスタのチェック

処理内容:
1. 4つの必要数一覧CSVファイルを縦結合
2. Z列（26列目）が空欄の行を削除
3. A列で重複している行は1行目のみ取り出す
4. B列を挿入し、M840/M850とLEFT JOINして工程・構成情報を追加
   - M840: HMCDが一致する行のKTCDを「工程：」+KTCDとしてB列に追加
   - M850: HMCDが一致する行のKOHMCDを「構成：」+KOHMCDとしてB列に追加
   - 複数マッチ時は行を展開（SEQ昇順）
"""

import httpx
import csv
import pandas as pd
from pathlib import Path
from collections import defaultdict


# API設定
API_BASE_URL = "http://pfw-api"
QUERY_ENDPOINT = "/query"
READ_API_KEY = "oG5^Ls%#20yq"

# 入力ファイル設定
INPUT_DIR = Path(r"\\172.17.107.102\PrintOutCsv\3.購買")
INPUT_FILES = [
    "3-22 必要数一覧12月_20251217.csv",
    "3-22 必要数一覧01月_20251217.csv",
    "3-22 必要数一覧02月_20251217.csv",
    "3-22 必要数一覧03月_20251217.csv",
]


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


def load_and_merge_csv_files() -> pd.DataFrame:
    """4つのCSVファイルを読み込み、縦結合"""
    print("\n===== CSVファイル読み込み・結合 =====")

    dfs = []
    for i, filename in enumerate(INPUT_FILES):
        filepath = INPUT_DIR / filename
        print(f"読み込み中: {filepath}")

        # CP932で読み込み
        df = pd.read_csv(filepath, encoding="cp932", dtype=str)

        if i == 0:
            # 1ファイル目はヘッダー込みでそのまま
            header = df.columns.tolist()
            print(f"  ヘッダー取得: {len(header)}列")

        dfs.append(df)
        print(f"  行数: {len(df)}件")

    # 縦結合
    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"\n結合後の総行数: {len(merged_df)}件")

    return merged_df


def filter_and_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Z列空欄削除、A列重複削除"""
    print("\n===== フィルタリング・重複削除 =====")

    original_count = len(df)

    # Z列（26列目、インデックス25）が空欄の行を削除
    col_z = df.columns[25] if len(df.columns) > 25 else None
    if col_z:
        print(f"Z列（{col_z}）が空欄の行を削除")
        df = df[df[col_z].notna() & (df[col_z] != "")]
        print(f"  削除後: {len(df)}件（{original_count - len(df)}件削除）")
    else:
        print("警告: Z列が見つかりません")

    # A列で重複している行は1行目のみ取り出す
    col_a = df.columns[0]
    before_dedup = len(df)
    df = df.drop_duplicates(subset=[col_a], keep="first")
    print(f"A列（{col_a}）重複削除後: {len(df)}件（{before_dedup - len(df)}件削除）")

    return df


def get_m840_data() -> dict:
    """M840（品目工程マスタ）からHMCD, SEQ, KTCD, SRCDを取得し、HMCDでグループ化"""
    print("\n===== M840品目工程マスタ取得 =====")

    rows = fetch_all_data(
        table="M0840",
        columns=["HMCD", "SEQ", "KTCD", "SRCD"]
    )

    # HMCDでグループ化（SEQ昇順でソート）
    m840_dict = defaultdict(list)
    for row in rows:
        hmcd = row.get("HMCD")
        if hmcd:
            m840_dict[hmcd].append({
                "SEQ": row.get("SEQ", ""),
                "KTCD": row.get("KTCD", ""),
                "SRCD": row.get("SRCD", "")
            })

    # 各HMCDのリストをSEQ昇順でソート
    for hmcd in m840_dict:
        m840_dict[hmcd].sort(key=lambda x: x["SEQ"] if x["SEQ"] else "")

    print(f"ユニークHMCD数: {len(m840_dict)}件")
    return m840_dict


def get_m850_data() -> dict:
    """M850（品目構成マスタ）からOYAHMCD, SEQ, KOHMCDを取得し、OYAHMCDでグループ化"""
    print("\n===== M850品目構成マスタ取得 =====")

    rows = fetch_all_data(
        table="M0850",
        columns=["OYAHMCD", "SEQ", "KOHMCD"]
    )

    # OYAHMCDでグループ化（SEQ昇順でソート）
    m850_dict = defaultdict(list)
    for row in rows:
        oyahmcd = row.get("OYAHMCD")
        if oyahmcd:
            m850_dict[oyahmcd].append({
                "SEQ": row.get("SEQ", ""),
                "KOHMCD": row.get("KOHMCD", "")
            })

    # 各OYAHMCDのリストをSEQ昇順でソート
    for oyahmcd in m850_dict:
        m850_dict[oyahmcd].sort(key=lambda x: x["SEQ"] if x["SEQ"] else "")

    print(f"ユニークHMCD数: {len(m850_dict)}件")
    return m850_dict


def expand_rows_with_masters(df: pd.DataFrame, m840_dict: dict, m850_dict: dict) -> pd.DataFrame:
    """B列、C列を挿入し、M840/M850とJOINして行を展開"""
    print("\n===== B列・C列挿入・マスタ結合・行展開 =====")

    col_a = df.columns[0]
    original_columns = df.columns.tolist()

    # 新しいB列（工程・構成）、C列（SRCD）を挿入した列リスト
    new_columns = [original_columns[0], "工程・構成", "SRCD"] + original_columns[1:]

    expanded_rows = []
    match_m840_count = 0
    match_m850_count = 0
    no_match_count = 0

    for _, row in df.iterrows():
        hmcd = row[col_a]
        row_data = row.tolist()

        # A列の値でM840、M850を検索
        m840_matches = m840_dict.get(hmcd, [])
        m850_matches = m850_dict.get(hmcd, [])

        if not m840_matches and not m850_matches:
            # マッチなし：B列・C列空欄で1行追加
            new_row = [row_data[0], "", ""] + row_data[1:]
            expanded_rows.append(new_row)
            no_match_count += 1
        else:
            # M850のマッチ行を追加（SEQ昇順）※構成を先に、SRCDは空欄
            for m850 in m850_matches:
                kohmcd = m850.get("KOHMCD", "")
                b_value = f"構成：{kohmcd}" if kohmcd else ""
                new_row = [row_data[0], b_value, ""] + row_data[1:]
                expanded_rows.append(new_row)
                match_m850_count += 1

            # M840のマッチ行を追加（SEQ昇順）※工程は後、SRCDあり
            for m840 in m840_matches:
                ktcd = m840.get("KTCD", "")
                srcd = m840.get("SRCD", "")
                b_value = f"工程：{ktcd}" if ktcd else ""
                new_row = [row_data[0], b_value, srcd] + row_data[1:]
                expanded_rows.append(new_row)
                match_m840_count += 1

    print(f"M840マッチ行数: {match_m840_count}件")
    print(f"M850マッチ行数: {match_m850_count}件")
    print(f"マッチなし行数: {no_match_count}件")
    print(f"展開後の総行数: {len(expanded_rows)}件")

    result_df = pd.DataFrame(expanded_rows, columns=new_columns)
    return result_df


def save_to_csv(df: pd.DataFrame, output_path: Path):
    """結果をCSVファイルに出力"""
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\nCSVファイル出力完了: {output_path}")
    print(f"  出力行数: {len(df)}件")


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # 1. CSVファイル読み込み・結合
    df = load_and_merge_csv_files()

    # 2. Z列空欄削除、A列重複削除
    df = filter_and_deduplicate(df)

    if len(df) == 0:
        print("フィルタリング後のデータがありません。")
        return

    # 3. M840、M850データ取得
    m840_dict = get_m840_data()
    m850_dict = get_m850_data()

    # 4. B列挿入・マスタ結合・行展開
    result_df = expand_rows_with_masters(df, m840_dict, m850_dict)

    # 5. CSV出力
    output_path = output_dir / "06_必要数一覧チェック.csv"
    save_to_csv(result_df, output_path)

    # サマリー表示
    print("\n========== 処理結果サマリー ==========")
    print(f"入力ファイル数: {len(INPUT_FILES)}件")
    print(f"出力行数: {len(result_df)}件")


if __name__ == "__main__":
    main()
