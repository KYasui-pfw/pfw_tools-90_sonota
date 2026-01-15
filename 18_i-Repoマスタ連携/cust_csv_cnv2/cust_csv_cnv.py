############################################################################
# i-Reporter
# 客先マスタの変換処理（rBOMシステムからの取得版）
# 作成 20251205
#
# データソース: rBOM API経由
#   - M0610（販売取引先マスタ）: HTRCD, HTRNM1, AREACD
#   - M0030（地区マスタ）: AREACD, AREANM
############################################################################
import httpx
import csv
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


# API設定
API_BASE_URL = "http://pfw-api"
QUERY_ENDPOINT = "/query"
READ_API_KEY = "oG5^Ls%#20yq"

# 出力先
CSV_UPLOAD_PATH = r"D:\CustomMaster\CSV_UPLOAD"

# テスト用：出力先が存在しない場合はスクリプトと同じディレクトリに出力
def get_output_path() -> str:
    if os.path.exists(CSV_UPLOAD_PATH):
        return CSV_UPLOAD_PATH
    else:
        return os.path.dirname(__file__)


def fetch_data(table: str, columns: list[str], limit: int = 10000, offset: int = 0) -> dict:
    """APIからデータを取得"""
    headers = {"X-API-KEY": READ_API_KEY, "Content-Type": "application/json"}

    request_body = {
        "table": table,
        "columns": columns,
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


def fetch_all_data(table: str, columns: list[str]) -> list[dict]:
    """全データをページネーションで取得"""
    all_rows = []
    offset = 0
    limit = 10000

    while True:
        result = fetch_data(table, columns, limit, offset)
        rows = result.get("rows", [])

        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < limit:
            break

        offset += limit

    return all_rows


def get_area_master() -> dict:
    """M0030地区マスタを取得し、AREACD→AREANM の辞書を返す"""
    rows = fetch_all_data("M0030", ["AREACD", "AREANM"])
    return {row["AREACD"]: row["AREANM"] for row in rows if row.get("AREACD")}


def is_valid_htrcd(htrcd: str) -> bool:
    """HTRCDが「アルファベット1文字＋数字」のパターンかチェック"""
    if not htrcd:
        return False
    # アルファベット1文字 + 数字1文字以上
    pattern = r'^[A-Za-z][0-9]+$'
    return bool(re.match(pattern, htrcd))


def get_customer_master() -> list[dict]:
    """M0610販売取引先マスタを取得（アルファベット1文字＋数字のHTRCDのみ）"""
    all_data = fetch_all_data("M0610", ["HTRCD", "HTRNM1", "AREACD"])
    # HTRCDがアルファベット1文字＋数字のパターンのみフィルタリング
    filtered_data = [row for row in all_data if is_valid_htrcd(row.get("HTRCD", ""))]
    return filtered_data


def create_ireporter_csv(customers: list[dict], area_dict: dict) -> str:
    """i-Reporter取込用CSVを作成"""

    # データ行を作成（国コード→客先コードでソート）
    data_rows = []
    for cust in customers:
        htrcd = cust.get("HTRCD", "")
        htrnm1 = cust.get("HTRNM1", "")
        areacd = cust.get("AREACD", "")
        areanm = area_dict.get(areacd, "")

        data_rows.append({
            "htrcd": htrcd,
            "htrnm1": htrnm1,
            "areacd": areacd,
            "areanm": areanm
        })

    # 国コード→客先コードでソート
    data_rows.sort(key=lambda x: (x["areacd"], x["htrcd"]))

    # 表示順を付与（1から連番）
    for i, row in enumerate(data_rows, start=1):
        row["display_order"] = i

    # ヘッダー部を作成（111列）
    header_row1 = ["H", "アクション区分", "マスターキー", "マスター名称", "マスター種別", "フィールド型配列", "フィールド名称配列", "画像フィールド名称配列", "本体保存可否", "ダウンロード区分", "保持期間", "有効期限", "表示順", "備考", "レコードキーヘッダ名称", "レコーバリューヘッダ名称", "権限グループ", "ラベルモード", "ラベル", "帳票定義ＩＤ", "入力帳票ＩＤ"]
    header_row1.extend([""] * (111 - len(header_row1)))

    # フィールド型配列とフィールド名称配列（100個のtext;と国名;国コード;;...）
    field_types = "text;text;;" + ";" * 97
    field_names = "国名;国コード;;" + ";" * 97

    header_row2 = ["M", "M", "M_CUSTOMER", "客先マスタ", "0", field_types, field_names, ";;;;", "1", "0", "0", "", "1000", "客先管理を行うマスタです", "客先コード", "客先名称", "4;6;9;11", "", "チェックシートマスタ", "", ""]
    header_row2.extend([""] * (111 - len(header_row2)))

    header_row3 = ["H", "アクション区分", "客先コード", "客先名称", "権限グループ", "表示順", "国名", "国コード"]
    for i in range(3, 101):
        header_row3.append(f"フィールド{i:04d}")
    header_row3.extend(["フィールド1001", "フィールド1002", "フィールド1003", "フィールド1004", "フィールド1005"])

    # 出力ファイル名
    dt_now = datetime.now(timezone(timedelta(hours=9)))
    csv_name = os.path.join(get_output_path(), dt_now.strftime('%Y%m%d%H%M%S') + "_客先マスタデータ.csv")

    # CSV出力
    with open(csv_name, 'w', newline='', encoding='CP932') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)

        # ヘッダー3行
        writer.writerow(header_row1)
        writer.writerow(header_row2)
        writer.writerow(header_row3)

        # データ行
        for row in data_rows:
            data_line = [
                "R",                    # 固定
                "M",                    # アクション区分
                row["htrcd"],           # 客先コード
                row["htrnm1"],          # 客先名称
                "",                     # 権限グループ（空欄）
                str(row["display_order"]),  # 表示順
                row["areanm"],          # 国名
                row["areacd"]           # 国コード
            ]
            # 残りの列は空欄
            data_line.extend([""] * (111 - len(data_line)))
            writer.writerow(data_line)

    return csv_name


def main():
    try:
        print("客先マスタ変換処理開始")

        # M0030地区マスタを取得
        print("M0030地区マスタを取得中...")
        area_dict = get_area_master()
        print(f"  取得件数: {len(area_dict)}件")

        # M0610販売取引先マスタを取得
        print("M0610販売取引先マスタを取得中...")
        all_customers = fetch_all_data("M0610", ["HTRCD", "HTRNM1", "AREACD"])
        print(f"  全件数: {len(all_customers)}件")
        # フィルタリング（アルファベット1文字＋数字のみ）
        customers = [row for row in all_customers if is_valid_htrcd(row.get("HTRCD", ""))]
        print(f"  対象件数（アルファベット1文字＋数字）: {len(customers)}件")

        # i-Reporter用CSVを作成
        print("CSV作成中...")
        csv_name = create_ireporter_csv(customers, area_dict)
        print(f"CSV出力完了: {csv_name}")

        print("処理完了")

    except Exception as e:
        print(f"エラー発生: {e}")
        dt_now = datetime.now(timezone(timedelta(hours=9)))
        err_file = os.path.join(os.path.dirname(__file__), dt_now.strftime('%Y%m%d%H%M%S') + "_err.txt")
        with open(err_file, mode='w') as f:
            f.write(str(e))
        raise


if __name__ == "__main__":
    main()
