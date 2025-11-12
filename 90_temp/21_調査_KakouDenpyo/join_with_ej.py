import pandas as pd
import cx_Oracle
import os

def ej_data_get(sql):
    """EJシステム（Oracle Database）に接続してSQLを実行する"""
    try:
        # EJシステム接続情報
        host = '172.17.107.102'
        port = '1521'
        service_name = 'EXPJ'
        username = 'EXPJ2'
        password = 'EXPJ2'

        # 接続文字列
        connection_string = f"{username}/{password}@{host}:{port}/{service_name}"

        # データベース接続
        connection = cx_Oracle.connect(connection_string)

        # SQLを実行してDataFrameに変換
        df = pd.read_sql(sql, connection)

        # 接続を閉じる
        connection.close()

        return df

    except Exception as e:
        print(f"EJシステムへの接続でエラーが発生しました: {str(e)}")
        raise

# ファイルパス設定
BASE_DIR = r"C:\Dev\90_tools\90_temp\21_調査_KakouDenpyo"
INPUT_FILE = os.path.join(BASE_DIR, "4-03 ASPKakouDenpyo.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "4-03 ASPKakouDenpyo_with_PRODUCT_TYP_and_ISSUE_SPACE.csv") # <<< 変更点: 出力ファイル名を変更

print("=== 加工部番とEJ M_ITEMテーブルの結合処理 ===")
print(f"入力ファイル: {INPUT_FILE}")

# CSVファイルの読み込み（Shift-JIS / CP932エンコーディング）
print("\n1. CSVファイルを読み込んでいます...")
try:
    # エンコーディングを試行
    encodings = ['shift_jis', 'cp932', 'utf-8-sig']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(INPUT_FILE, encoding=enc)
            print(f"   エンコーディング '{enc}' で読み込みました")
            break
        except:
            continue

    if df is None:
        raise Exception("CSVファイルの読み込みに失敗しました")

    print(f"   データ件数: {len(df)}")
    print(f"   カラム数: {len(df.columns)}")
    print(f"   カラム名: {df.columns.tolist()[:5]}...")  # 最初の5列のみ表示

    # 加工部番のカラムを特定（6列目が加工部番の可能性が高い）
    # カラム名が文字化けしている場合は、インデックスで指定
    kakou_buban_col = df.columns[5]  # 6列目（0-indexed）
    print(f"\n   加工部番カラム: {kakou_buban_col}")
    print(f"   加工部番サンプル:\n{df[kakou_buban_col].head()}")

except Exception as e:
    print(f"エラー: {str(e)}")
    raise

# EJデータベースからM_ITEMテーブルのデータを取得
print("\n2. EJ M_ITEMテーブルからPRODUCT_TYPとISSUE_SPACEを取得しています...") # <<< 変更点: メッセージを修正
try:
    # 加工部番の一意なリストを取得
    unique_kakou_buban = df[kakou_buban_col].dropna().unique()
    print(f"   ユニークな加工部番の数: {len(unique_kakou_buban)}")

    # SQLクエリ作成（LIKE前方一致検索）
    # 大量のデータの場合はバッチ処理が必要
    batch_size = 900
    all_ej_data = []

    for i in range(0, len(unique_kakou_buban), batch_size):
        batch = unique_kakou_buban[i:i+batch_size]

        # LIKE条件を作成（前方一致）
        like_conditions = []
        for item in batch:
            escaped_item = str(item).replace("'", "''")
            like_conditions.append(f"ITEM_CD LIKE '{escaped_item}%'")

        where_clause = " OR ".join(like_conditions)

        # <<< 変更点: SQLクエリに ISSUE_SPACE を追加
        sql = f"""
        SELECT
            ITEM_CD,
            PRODUCT_TYP,
            ISSUE_SPACE
        FROM
            EXPJ2.M_ITEM
        WHERE
            {where_clause}
        """

        batch_result = ej_data_get(sql)
        all_ej_data.append(batch_result)
        print(f"   バッチ {i//batch_size + 1}/{(len(unique_kakou_buban)-1)//batch_size + 1} 取得完了 ({len(batch_result)}件)")

    # 全バッチを結合
    ej_df = pd.concat(all_ej_data, ignore_index=True)
    print(f"\n   EJデータ取得完了: {len(ej_df)}件")
    print(f"   サンプル:\n{ej_df.head()}")

except Exception as e:
    print(f"エラー: {str(e)}")
    raise

# データの結合（前方一致・最新の1件のみ）
print("\n3. データを結合しています（前方一致・複数マッチ時は最新の1件を使用）...")
try:
    # 結果を格納するリスト
    all_results = []
    multiple_match_count = 0
    multiple_match_details = []

    for idx, row in df.iterrows():
        kakou_buban = str(row[kakou_buban_col])

        # EJデータから前方一致するものを検索
        matches = ej_df[ej_df['ITEM_CD'].str.startswith(kakou_buban, na=False)]

        if len(matches) > 0:
            # 複数マッチの場合、最後の行（最も新しい行）を使用
            if len(matches) > 1:
                multiple_match_count += 1
                multiple_match_details.append({
                    '加工部番': kakou_buban,
                    'マッチ件数': len(matches),
                    '選択されたITEM_CD': matches.iloc[-1]['ITEM_CD']
                })

            # 最後の行を取得
            match_row = matches.iloc[-1]
            new_row = row.copy()
            new_row['MATCHED_ITEM_CD'] = match_row['ITEM_CD']
            new_row['PRODUCT_TYP'] = match_row['PRODUCT_TYP']
            new_row['ISSUE_SPACE'] = match_row['ISSUE_SPACE'] # <<< 変更点: ISSUE_SPACE を追加
            all_results.append(new_row)
        else:
            # マッチしない場合は元の行をそのまま追加
            new_row = row.copy()
            new_row['MATCHED_ITEM_CD'] = None
            new_row['PRODUCT_TYP'] = None
            new_row['ISSUE_SPACE'] = None # <<< 変更点: ISSUE_SPACE をNoneで追加
            all_results.append(new_row)

        # 進捗表示（100行ごと）
        if (idx + 1) % 100 == 0:
            print(f"   処理中... {idx + 1}/{len(df)} 行")

    # DataFrameに変換
    result_df = pd.DataFrame(all_results)

    print(f"\n   結合完了:")
    print(f"   元のデータ: {len(df)}件")
    print(f"   出力データ: {len(result_df)}件")
    print(f"   複数マッチした加工部番: {multiple_match_count}件")

    # 複数マッチの詳細を表示（最初の10件）
    if multiple_match_count > 0:
        print(f"\n   複数マッチの詳細（最初の10件）:")
        for detail in multiple_match_details[:10]:
            print(f"     - {detail['加工部番']}: {detail['マッチ件数']}件マッチ → {detail['選択されたITEM_CD']}を選択")

    # PRODUCT_TYPが取得できなかった件数を確認
    missing_count = result_df['PRODUCT_TYP'].isna().sum()
    print(f"\n   PRODUCT_TYPが取得できなかった件数: {missing_count}件")

    if missing_count > 0:
        print(f"   該当する加工部番:\n{result_df[result_df['PRODUCT_TYP'].isna()][kakou_buban_col].unique()[:10]}")

except Exception as e:
    print(f"エラー: {str(e)}")
    raise

# CSVファイルに出力
print(f"\n4. 結果をCSVファイルに出力しています...")
try:
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"   出力完了: {OUTPUT_FILE}")
    print(f"   ファイルサイズ: {os.path.getsize(OUTPUT_FILE):,} bytes")

except Exception as e:
    print(f"エラー: {str(e)}")
    raise

print("\n=== 処理完了 ===")
print(f"\n最終データ:")
print(f"  総件数: {len(result_df)}")
print(f"  カラム数: {len(result_df.columns)}")
print(f"  PRODUCT_TYP取得率: {(1 - missing_count/len(result_df))*100:.2f}%")