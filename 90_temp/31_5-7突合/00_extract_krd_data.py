"""
KRDデータベースからDATA_RES_CAPAデータを取得して処理する

処理フロー:
1. krd.machineのDATA_RES_CAPAから全件データを取得 → 01_krd全件データ.csv
2. krd.machineのDATA_RES_CAPAから編集後データを取得 → 02_krd桁数修正データ.csv (5.5を055にする等)
3. 01_krd全件データ.csvと02_krd桁数修正データ.csvを縦結合 → 03_マシニング課管理工程.csv
4. 例外処理: 特定の品番を変換
   - 5156-405AA7 → 5156-405AA07
   - 5156-409AA7 → 5156-406AA07
5. 03_マシニング課管理工程.csvとEXPJ2.M_ITEMをINNER JOIN → 04_EJ突合結果.csv
"""

# NLS_LANG環境変数を設定（database_utilsをimportする前に設定する必要がある）
import os
os.environ['NLS_LANG'] = 'JAPANESE_JAPAN.AL32UTF8'

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_utils import ej_data_get

def krd_data_get(sql):
    """
    krdのmachinDBに接続してSQLを実行する

    Args:
        sql (str): 実行するSQL文

    Returns:
        pd.DataFrame: クエリ結果のDataFrame
    """
    # DB接続定義
    db_url = 'mysql+pymysql://pfw:mejiriHoo@krd/machin?charset=utf8'
    # エンジンを作成
    engine = create_engine(db_url, echo=True)
    # セッションを作成するためのSessionクラスを生成
    Session = sessionmaker(bind=engine)
    session = Session()
    # コネクションを取得
    with engine.connect() as connection:
        # SQLクエリの実行
        df = pd.read_sql(sql, connection)
    # セッションを閉じる
    session.close()
    return df

def process_final_item_code_format(final_item_code):
    """
    FINAL_ITEM_CODEの桁数修正処理
    - 下2桁が数字の場合: 最後に0を追加
    - 下2桁が小数点1桁の場合: 100を掛けた値に変換

    例:
        5.5 → 055 (小数点パターン)
        100-501NA55 → 100-501NA550 (数字2桁パターン)

    Args:
        final_item_code: 品番コード

    Returns:
        str: 修正後の品番コード
    """
    code = str(final_item_code).strip()

    # 最後の2文字を取得
    if len(code) >= 2:
        last_two = code[-2:]

        # 下2桁が数字かチェック
        if last_two.isdigit():
            # 最後に0を追加
            return code + "0"

        # 小数点1桁のパターンをチェック (例: 5.5)
        if '.' in code:
            parts = code.split('.')
            if len(parts) == 2 and len(parts[1]) == 1 and parts[1].isdigit():
                # 小数点以下1桁の場合、100を掛けた値に変換し、末尾の0を先頭に移動
                base_part = parts[0]  # 小数点より前の部分
                decimal_part = parts[1]  # 小数点以下の数字
                # 100を掛けた値（例: 5.5 -> 550）
                multiplied_value = base_part + decimal_part + "0"

                # 最後の3桁の末尾の0を先頭に移動
                # 例: 100-501NA550 -> 100-501NA055
                if len(multiplied_value) >= 3:
                    # 最後の3文字を取得
                    last_three = multiplied_value[-3:]
                    if last_three.endswith('0'):
                        # 末尾の0を取り除いて先頭に配置
                        middle_part = last_three[:-1]  # 末尾の0を除いた2文字
                        new_last_three = '0' + middle_part
                        return multiplied_value[:-3] + new_last_three

                return multiplied_value

    # 変更不要な場合はそのまま返す
    return code

def extract_krd_all_data(work_dir):
    """
    処理1: krd.machineのDATA_RES_CAPAから全件データを取得
    """
    output_file = os.path.join(work_dir, '01_krd全件データ.csv')

    # SQLクエリ - DATA_RES_CAPAから全件取得
    sql = """
    SELECT FINAL_ITEM_CODE
    FROM DATA_RES_CAPA
    """

    try:
        print("=== 処理1: KRDデータベースから全件データ取得 ===")
        print("KRDシステムに接続中...")
        df = krd_data_get(sql)

        print(f"KRDシステムから取得したデータ件数: {len(df)}行")

        if len(df) > 0:
            # 重複を除去
            df = df.drop_duplicates()
            print(f"重複除去後: {len(df)}行")

            # データの先頭数行を表示
            print("\n先頭10行のデータ:")
            print(df.head(10))

            # 01_krd全件データ.csvとして出力
            df.to_csv(output_file, encoding='utf-8-sig', index=False)
            print(f"\n01_krd全件データ.csv出力完了: {output_file} ({len(df)}行)")

        else:
            print("該当するデータが見つかりませんでした。")

    except Exception as e:
        print(f"KRDデータ抽出でエラーが発生しました: {e}")
        raise

def process_digit_correction(work_dir):
    """
    処理2: 01_krd全件データ.csvを読み込んで桁数修正処理を実行
    """
    input_file = os.path.join(work_dir, '01_krd全件データ.csv')
    output_file = os.path.join(work_dir, '02_krd桁数修正データ.csv')

    try:
        print("\n=== 処理2: 桁数修正処理 ===")
        # 01_krd全件データ.csvを読み込み
        print(f"読み込み中: {input_file}")
        df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"読み込み完了: {len(df)}行")

        # FINAL_ITEM_CODEの桁数修正処理
        print("桁数修正処理実行中...")
        df['FINAL_ITEM_CODE_CORRECTED'] = df['FINAL_ITEM_CODE'].apply(process_final_item_code_format)

        # 修正例を表示
        print("\n修正例（最初の10行）:")
        for i in range(min(10, len(df))):
            original = df.iloc[i]['FINAL_ITEM_CODE']
            corrected = df.iloc[i]['FINAL_ITEM_CODE_CORRECTED']
            if original != corrected:
                print(f"  {original} → {corrected}")
            else:
                print(f"  {original} (変更なし)")

        # 修正されたデータのみを含むDataFrameを作成
        result_df = df[['FINAL_ITEM_CODE_CORRECTED']].rename(columns={'FINAL_ITEM_CODE_CORRECTED': 'FINAL_ITEM_CODE'})

        # 02_krd桁数修正データ.csvとして出力
        result_df.to_csv(output_file, encoding='utf-8-sig', index=False)
        print(f"\n02_krd桁数修正データ.csv出力完了: {output_file} ({len(result_df)}行)")

        # 修正統計を表示
        changes_count = (df['FINAL_ITEM_CODE'] != df['FINAL_ITEM_CODE_CORRECTED']).sum()
        print(f"修正された行数: {changes_count}行 / 全{len(df)}行")

    except Exception as e:
        print(f"桁数修正処理でエラーが発生しました: {e}")
        raise

def combine_csv_files(work_dir):
    """
    処理3-4: 01_krd全件データ.csvと02_krd桁数修正データ.csvを縦結合して重複を除去
            例外処理で特定の品番を変換
    """
    input_file1 = os.path.join(work_dir, '01_krd全件データ.csv')
    input_file2 = os.path.join(work_dir, '02_krd桁数修正データ.csv')
    output_file = os.path.join(work_dir, '03_マシニング課管理工程.csv')

    try:
        print("\n=== 処理3: 縦結合処理 ===")
        # 両ファイルを読み込み
        print(f"読み込み中: {input_file1}")
        df1 = pd.read_csv(input_file1, encoding='utf-8-sig')
        print(f"01_krd全件データ.csv: {len(df1)}行")

        print(f"読み込み中: {input_file2}")
        df2 = pd.read_csv(input_file2, encoding='utf-8-sig')
        print(f"02_krd桁数修正データ.csv: {len(df2)}行")

        # 縦に結合
        combined_df = pd.concat([df1, df2], ignore_index=True)
        print(f"結合後: {len(combined_df)}行")

        # 重複を除去
        combined_df = combined_df.drop_duplicates()
        print(f"重複除去後: {len(combined_df)}行")

        print("\n=== 処理4: 例外処理（特定品番の変換） ===")
        # FINAL_ITEM_CODEに対する例外処理
        if 'FINAL_ITEM_CODE' in combined_df.columns:
            # 5156-405AA7 → 5156-405AA07
            mask1 = combined_df['FINAL_ITEM_CODE'] == '5156-405AA7'
            combined_df.loc[mask1, 'FINAL_ITEM_CODE'] = '5156-405AA07'
            changed1 = mask1.sum()

            # 5156-409AA7 → 5156-406AA07
            mask2 = combined_df['FINAL_ITEM_CODE'] == '5156-409AA7'
            combined_df.loc[mask2, 'FINAL_ITEM_CODE'] = '5156-406AA07'
            changed2 = mask2.sum()

            print(f"  5156-405AA7 → 5156-405AA07: {changed1}件変換")
            print(f"  5156-409AA7 → 5156-406AA07: {changed2}件変換")

        # 03_マシニング課管理工程.csvとして出力
        combined_df.to_csv(output_file, encoding='utf-8-sig', index=False)
        print(f"\n03_マシニング課管理工程.csv出力完了: {output_file} ({len(combined_df)}行)")

    except Exception as e:
        print(f"縦結合処理でエラーが発生しました: {e}")
        raise

def join_with_ej_m_item(work_dir):
    """
    処理5: 03_マシニング課管理工程.csvとEXPJ2.M_ITEMをINNER JOIN
    """
    input_file = os.path.join(work_dir, '03_マシニング課管理工程.csv')
    output_file = os.path.join(work_dir, '04_EJ突合結果.csv')

    try:
        print("\n=== 処理5: EXPJ2.M_ITEMとの突合 ===")

        # 03_マシニング課管理工程.csvを読み込み
        print(f"読み込み中: {input_file}")
        machining_df = pd.read_csv(input_file, encoding='utf-8-sig')
        print(f"マシニング課管理工程データ: {len(machining_df)}行")

        # EXPJ2.M_ITEMから必要なカラムを取得
        print("EXPJ2.M_ITEMからデータ取得中...")
        ej_sql = """
        SELECT ITEM_CD, PRODUCT_TYP
        FROM EXPJ2.M_ITEM
        """
        ej_df = ej_data_get(ej_sql)
        print(f"EXPJ2.M_ITEM取得データ: {len(ej_df)}行, {len(ej_df.columns)}列")

        # INNER JOINを実行
        print("\nINNER JOIN実行中...")
        joined_df = pd.merge(
            machining_df,
            ej_df,
            left_on='FINAL_ITEM_CODE',
            right_on='ITEM_CD',
            how='inner'
        )
        print(f"突合結果: {len(joined_df)}行")

        # ITEM_CD列を削除（FINAL_ITEM_CODEと重複するため）
        if 'ITEM_CD' in joined_df.columns:
            joined_df = joined_df.drop(columns=['ITEM_CD'])

        # 結果を出力
        joined_df.to_csv(output_file, encoding='utf-8-sig', index=False)
        print(f"\n04_EJ突合結果.csv出力完了: {output_file} ({len(joined_df)}行)")

        # 統計情報を表示
        print(f"\n突合統計:")
        print(f"  マシニング課管理工程: {len(machining_df)}行")
        print(f"  EXPJ2.M_ITEM: {len(ej_df)}行")
        print(f"  突合成功: {len(joined_df)}行")
        print(f"  突合失敗: {len(machining_df) - len(joined_df)}行")

    except Exception as e:
        print(f"EJ突合処理でエラーが発生しました: {e}")
        raise

def main():
    """
    メイン処理
    """
    # ディレクトリ設定
    base_dir = r"C:\Dev\90_tools\90_temp\31_5-7突合"
    work_dir = os.path.join(base_dir, "work")

    # workディレクトリが存在しない場合は作成
    os.makedirs(work_dir, exist_ok=True)

    print("=" * 80)
    print("KRDデータ抽出・加工処理")
    print("=" * 80)

    try:
        # 処理1: KRDから全件データ取得
        extract_krd_all_data(work_dir)

        # 処理2: 桁数修正処理
        process_digit_correction(work_dir)

        # 処理3-4: 縦結合と例外処理
        combine_csv_files(work_dir)

        # 処理5: EXPJ2.M_ITEMとの突合
        join_with_ej_m_item(work_dir)

        print("\n" + "=" * 80)
        print("全処理完了")
        print("=" * 80)

    except Exception as e:
        print(f"\n処理中にエラーが発生しました: {e}")
        raise

if __name__ == "__main__":
    main()
