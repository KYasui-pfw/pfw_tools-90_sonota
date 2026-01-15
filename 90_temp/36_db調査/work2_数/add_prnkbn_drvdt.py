# -*- coding: utf-8 -*-
"""
add_prnkbn_drvdt.py

02_両方あり_同一rBOM.csvに以下を取得して追加する:
- D3330テーブルからPRNKBN（発注区分）
- D3340テーブルからDRVDT（希望納期）

キー:
- D3330: PONO（rBOM発注番号）
- D3340: PONO + LINENO（rBOM発注番号 + 行番号）
"""

import os
import pandas as pd
import requests

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "02_両方あり_同一rBOM.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "02_両方あり_同一rBOM_PRNKBN_DRVDT.csv")

# API設定
API_BASE_URL = "http://pfw-api"
API_KEY = "oG5^Ls%#20yq"  # READ_API_KEY

# カラムインデックス（0始まり）
COL_RBOM_ORDER = 10   # rBOM発注番号+行番号


def query_d3330(pono_list):
    """
    D3330テーブルからPONO, PRNKBNを取得
    """
    url = f"{API_BASE_URL}/query"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "table": "D3330",
        "columns": ["PONO", "PRNKBN"],
        "where": {
            "or": [{"PONO": {"eq": pono}} for pono in pono_list]
        },
        "limit": 10000
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


def query_d3340(pono_lineno_list):
    """
    D3340テーブルからPONO, LINENO, DRVDTを取得
    """
    url = f"{API_BASE_URL}/query"
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "table": "D3340",
        "columns": ["PONO", "LINENO", "DRVDT"],
        "where": {
            "or": [
                {"and": [{"PONO": {"eq": pono}}, {"LINENO": {"eq": lineno}}]}
                for pono, lineno in pono_lineno_list
            ]
        },
        "limit": 10000
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


def main():
    print("=" * 60)
    print("D3330 PRNKBN + D3340 DRVDT 取得処理")
    print("=" * 60)
    print()

    # CSV読み込み
    print(f"入力ファイル: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding="cp932", dtype=str)
    print(f"読み込み行数: {len(df)}")

    # カラム名取得
    cols = df.columns.tolist()
    rbom_col = cols[COL_RBOM_ORDER]
    print(f"rBOM発注番号+行番号カラム: {rbom_col}")
    print()

    # rBOM発注番号と行番号を抽出
    def extract_pono_lineno(val):
        """rBOM発注番号+行番号から(PONO, LINENO)を抽出"""
        if pd.isna(val) or str(val).strip() == "":
            return "", ""
        parts = str(val).split("+")
        if len(parts) >= 2:
            pono = parts[0]
            lineno = int(parts[1])  # 行番号は整数
            return pono, lineno
        return parts[0], ""

    df["_rbom_pono"] = df[rbom_col].apply(lambda x: extract_pono_lineno(x)[0])
    df["_rbom_lineno"] = df[rbom_col].apply(lambda x: extract_pono_lineno(x)[1])

    # ========================================
    # D3330からPRNKBN取得
    # ========================================
    pono_list = df[df["_rbom_pono"] != ""]["_rbom_pono"].unique().tolist()
    print(f"ユニークrBOM発注番号数: {len(pono_list)}")

    print("D3330からPRNKBN取得中...")
    d3330_data = []
    batch_size = 100

    for i in range(0, len(pono_list), batch_size):
        batch = pono_list[i:i+batch_size]
        print(f"  バッチ {i//batch_size + 1}/{(len(pono_list)-1)//batch_size + 1}: {len(batch)}件...")

        try:
            result = query_d3330(batch)
            if "rows" in result:
                d3330_data.extend(result["rows"])
                print(f"    -> {len(result['rows'])}行取得")
            else:
                print(f"    -> データなし")
        except Exception as e:
            print(f"    -> エラー: {e}")

    print(f"D3330合計取得行数: {len(d3330_data)}")
    print()

    # D3330データをDataFrameに変換
    if d3330_data:
        d3330_df = pd.DataFrame(d3330_data)
        d3330_df["PONO"] = d3330_df["PONO"].astype(str)
        d3330_df = d3330_df.drop_duplicates(subset=["PONO"], keep="first")
        print(f"D3330ユニークPONO数: {len(d3330_df)}")
    else:
        d3330_df = pd.DataFrame(columns=["PONO", "PRNKBN"])

    # ========================================
    # D3340からDRVDT取得
    # ========================================
    # PONO+LINENOのペアリストを作成（空欄除く）
    pono_lineno_list = []
    for _, row in df.iterrows():
        pono = row["_rbom_pono"]
        lineno = row["_rbom_lineno"]
        if pono != "" and lineno != "":
            pono_lineno_list.append((pono, lineno))

    # 重複除去
    pono_lineno_list = list(set(pono_lineno_list))
    print(f"ユニークPONO+LINENO組み合わせ数: {len(pono_lineno_list)}")

    print("D3340からDRVDT取得中...")
    d3340_data = []
    batch_size = 100

    for i in range(0, len(pono_lineno_list), batch_size):
        batch = pono_lineno_list[i:i+batch_size]
        print(f"  バッチ {i//batch_size + 1}/{(len(pono_lineno_list)-1)//batch_size + 1}: {len(batch)}件...")

        try:
            result = query_d3340(batch)
            if "rows" in result:
                d3340_data.extend(result["rows"])
                print(f"    -> {len(result['rows'])}行取得")
            else:
                print(f"    -> データなし")
        except Exception as e:
            print(f"    -> エラー: {e}")

    print(f"D3340合計取得行数: {len(d3340_data)}")
    print()

    # D3340データをDataFrameに変換
    if d3340_data:
        d3340_df = pd.DataFrame(d3340_data)
        d3340_df["PONO"] = d3340_df["PONO"].astype(str)
        d3340_df["LINENO"] = d3340_df["LINENO"].astype(int)
        d3340_df = d3340_df.drop_duplicates(subset=["PONO", "LINENO"], keep="first")
        print(f"D3340ユニークPONO+LINENO数: {len(d3340_df)}")
    else:
        d3340_df = pd.DataFrame(columns=["PONO", "LINENO", "DRVDT"])

    # ========================================
    # マージ
    # ========================================
    # D3330マージ（PRNKBNを追加）
    df = df.merge(
        d3330_df[["PONO", "PRNKBN"]],
        left_on="_rbom_pono",
        right_on="PONO",
        how="left"
    )
    df.drop(columns=["PONO"], inplace=True)

    # D3340マージ（DRVDTを追加）
    # _rbom_linenoを数値に変換（空文字はNaNに）
    df["_rbom_lineno_int"] = pd.to_numeric(df["_rbom_lineno"], errors="coerce")

    df = df.merge(
        d3340_df[["PONO", "LINENO", "DRVDT"]],
        left_on=["_rbom_pono", "_rbom_lineno_int"],
        right_on=["PONO", "LINENO"],
        how="left"
    )

    # 不要カラム削除
    df.drop(columns=["_rbom_pono", "_rbom_lineno", "_rbom_lineno_int", "PONO", "LINENO"], inplace=True)

    # 出力
    df.to_csv(OUTPUT_FILE, index=False, encoding="cp932")
    print()
    print(f"出力ファイル: {OUTPUT_FILE}")
    print(f"出力行数: {len(df)}")

    # 結果サマリー
    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)

    print()
    print("PRNKBN分布:")
    prnkbn_counts = df["PRNKBN"].value_counts(dropna=False)
    for val, cnt in prnkbn_counts.items():
        print(f"  {val}: {cnt}件")

    print()
    print("DRVDT分布（上位10件）:")
    drvdt_counts = df["DRVDT"].value_counts(dropna=False).head(10)
    for val, cnt in drvdt_counts.items():
        print(f"  {val}: {cnt}件")

    return 0


if __name__ == "__main__":
    exit(main())
