import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import cx_Oracle

def krd_data_get(sql):
    """krdのmachinDBに接続してSQLを実行する"""
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

def process_final_item_code_format(final_item_code):
    """
    FINAL_ITEM_CODEの桁数修正処理
    - 下2桁が数字の場合：最後に0を追加
    - 下2桁が小数点1桁の場合：100を掛けた値に変換
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

def process_digit_correction(work_dir):
    """
    指示13: 01_krd全件データ.csvを読み込んで桁数修正処理を実行
    """
    input_file = os.path.join(work_dir, '01_krd全件データ.csv')
    output_file = os.path.join(work_dir, '02_krd桁数修正データ.csv')
    
    try:
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

def combine_csv_files(work_dir):
    """
    指示14: 01_krd全件データ.csvと02_krd桁数修正データ.csvを縦結合して重複を除去
    """
    input_file1 = os.path.join(work_dir, '01_krd全件データ.csv')
    input_file2 = os.path.join(work_dir, '02_krd桁数修正データ.csv')
    output_file = os.path.join(work_dir, '03_マシニング課管理工程.csv')
    
    try:
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
        
        # 03_マシニング課管理工程.csvとして出力
        combined_df.to_csv(output_file, encoding='utf-8-sig', index=False)
        print(f"\n03_マシニング課管理工程.csv出力完了: {output_file} ({len(combined_df)}行)")
        
    except Exception as e:
        print(f"縦結合処理でエラーが発生しました: {e}")

def extract_ej_data(work_dir):
    """
    指示17: EJシステムからM_ITEMテーブルのデータを取得
    """
    output_file = os.path.join(work_dir, '04_EJ678.csv')
    
    # SQLクエリ - ITEM_CDとPRODUCT_TYPを取得
    sql = """
    SELECT ITEM_CD, PRODUCT_TYP
    FROM EXPJ2.M_ITEM
    WHERE ITEM_CD NOT LIKE '!%'
      AND PRODUCT_TYP IN (6, 7, 8)
    ORDER BY ITEM_CD
    """
    
    try:
        # EJシステムからデータを取得
        print("EJシステムに接続中...")
        df = ej_data_get(sql)
        
        print(f"EJシステムから取得したデータ件数: {len(df)}行")
        
        if len(df) > 0:
            # データの先頭数行を表示
            print("\n先頭10行のデータ:")
            print(df.head(10))
            
            # 04_EJ678.csvとして出力
            df.to_csv(output_file, encoding='utf-8-sig', index=False)
            print(f"\n04_EJ678.csv出力完了: {output_file} ({len(df)}行)")
            
        else:
            print("該当するデータが見つかりませんでした。")
            
    except Exception as e:
        print(f"EJデータ抽出でエラーが発生しました: {e}")

def main():
    # 出力ディレクトリの設定
    work_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(work_dir, exist_ok=True)
    
    print("=== 指示12: シンプルな外注対象データ抽出 ===")
    
    # SQLクエリ - FINAL_ITEM_CODEのみを重複なしで取得
    sql = """
    SELECT DISTINCT FINAL_ITEM_CODE
    FROM DATA_RES_CAPA
    WHERE FINAL_ITEM_CODE IS NOT NULL 
      AND FINAL_ITEM_CODE != ''
    ORDER BY FINAL_ITEM_CODE
    """
    
    try:
        # データベースからデータを取得
        print("データベースに接続中...")
        df = krd_data_get(sql)
        
        print(f"取得したデータ件数: {len(df)}行")
        
        if len(df) > 0:
            # データの先頭数行を表示
            print("\n先頭10行のデータ:")
            print(df.head(10))
            
            # 01_krd全件データ.csvとして出力
            output_path = os.path.join(work_dir, '01_krd全件データ.csv')
            df.to_csv(output_path, encoding='utf-8-sig', index=False)
            print(f"\n01_krd全件データ.csv出力完了: {output_path} ({len(df)}行)")
            
            # 指示13: 桁数修正処理
            print("\n=== 指示13: FINAL_ITEM_CODE桁数修正処理 ===")
            process_digit_correction(work_dir)
            
            # 指示14: 縦結合と重複除去
            print("\n=== 指示14: データ結合と重複除去 ===")
            combine_csv_files(work_dir)
            
        else:
            print("該当するデータが見つかりませんでした。")
            
        # 指示17: EJシステムからデータ取得
        print("\n=== 指示17: EJシステムからデータ取得 ===")
        extract_ej_data(work_dir)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("データベース接続情報やテーブル名を確認してください。")
    
    print("=== 処理完了 ===")

if __name__ == "__main__":
    main()