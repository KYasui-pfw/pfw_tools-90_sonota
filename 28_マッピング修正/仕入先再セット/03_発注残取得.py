# -*- coding: utf-8 -*-
"""
03_発注残取得.csvのPUCH_ODR_CDをキーにして、T_RLSD_PUCH_ODRの全項目を取得
"""

import pandas as pd
import oracledb
from pathlib import Path

# パス設定
BASE_DIR = Path(__file__).parent
INPUT_CSV = BASE_DIR / "03_発注残取得.csv"
KANNO_CSV = BASE_DIR / "02_完納対象調査.csv"
OUTPUT_CSV = BASE_DIR / "03_発注残取得_結果.csv"

# EJデータベース接続情報
EJ_HOST = '172.17.107.102'
EJ_PORT = '1521'
EJ_SERVICE = 'EXPJ'
EJ_USER = 'EXPJ2'
EJ_PASSWORD = 'EXPJ2'


def main():
    # thick mode初期化
    try:
        oracledb.init_oracle_client()
    except Exception:
        pass  # 既に初期化済みの場合

    # 入力ファイル読み込み
    input_df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
    print(f"03_発注残取得.csv 読み込み: {len(input_df)}行")

    # 重複削除
    input_df = input_df.drop_duplicates(subset=['PUCH_ODR_CD'])
    print(f"重複削除後: {len(input_df)}行")

    # PUCH_ODR_CDリスト取得
    puch_odr_cds = input_df['PUCH_ODR_CD'].tolist()
    print(f"取得対象: {len(puch_odr_cds)}件")

    # Oracle接続
    connection_string = f"{EJ_USER}/{EJ_PASSWORD}@{EJ_HOST}:{EJ_PORT}/{EJ_SERVICE}"

    try:
        conn = oracledb.connect(connection_string)
        cursor = conn.cursor()
        print("EJデータベース接続成功")

        # IN句用のプレースホルダー作成（Oracle IN句は1000件制限があるため分割）
        all_results = []
        chunk_size = 900

        for i in range(0, len(puch_odr_cds), chunk_size):
            chunk = puch_odr_cds[i:i + chunk_size]
            placeholders = ','.join([f':p{j}' for j in range(len(chunk))])

            query = f"""
                SELECT *
                FROM EXPJ2.T_RLSD_PUCH_ODR
                WHERE PUCH_ODR_CD IN ({placeholders})
            """

            # パラメータ辞書作成
            params = {f'p{j}': cd for j, cd in enumerate(chunk)}

            cursor.execute(query, params)

            # 列名取得
            columns = [desc[0] for desc in cursor.description]

            # 結果取得
            rows = cursor.fetchall()

            for row in rows:
                all_results.append(dict(zip(columns, row)))

            print(f"  チャンク {i//chunk_size + 1}: {len(rows)}件取得")

        conn.close()
        print(f"\n合計取得件数: {len(all_results)}件")

        # DataFrame化
        if all_results:
            result_df = pd.DataFrame(all_results)

            # 入力CSVをベースにLEFT JOIN（取得できなかったものは空欄）
            input_df_base = input_df[['PUCH_ODR_CD']].copy()
            merged_df = input_df_base.merge(
                result_df,
                on='PUCH_ODR_CD',
                how='left'
            )

            # 02_完納対象調査.csvからEJ数合計を取得
            kanno_df = pd.read_csv(KANNO_CSV, encoding='utf-8-sig')
            print(f"\n02_完納対象調査.csv 読み込み: {len(kanno_df)}行")

            # EJ発注番号でグループ化してEJ数を合計
            ej_sum = kanno_df.groupby('EJ発注番号')['EJ数'].sum().reset_index()
            ej_sum.columns = ['PUCH_ODR_CD', 'EJ数合計']

            # マージ
            merged_df = merged_df.merge(
                ej_sum,
                on='PUCH_ODR_CD',
                how='left'
            )

            merged_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
            print(f"\n出力: {OUTPUT_CSV}")
            print(f"出力件数: {len(merged_df)}件")
            print(f"EJ数合計あり: {merged_df['EJ数合計'].notna().sum()}件")
        else:
            # 結果が0件の場合は入力CSVのPUCH_ODR_CDのみ出力
            input_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
            print(f"出力: {OUTPUT_CSV}")
            print("取得結果が0件のため、PUCH_ODR_CDのみ出力")

    except oracledb.DatabaseError as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    main()
