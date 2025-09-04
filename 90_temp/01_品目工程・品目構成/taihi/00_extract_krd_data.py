import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def filter_latest_pack_date(df):
    """
    同じFINAL_ITEM_CODEの行が複数ある場合、PACK_DATEが最も新しい1行のみを抽出
    """
    if 'PACK_DATE' not in df.columns:
        print("PACK_DATE列が見つかりません。フィルタリングをスキップします。")
        return df
    
    # PACK_DATEを日付型に変換（変換できない場合は元の値を保持）
    df_copy = df.copy()
    df_copy['PACK_DATE_converted'] = pd.to_datetime(df_copy['PACK_DATE'], errors='coerce', format='%Y-%m-%d')
    
    # FINAL_ITEM_CODEでグループ化し、PACK_DATEが最新の行のみ抽出
    def get_latest_row(group):
        # NaNでないPACK_DATEがある場合は、最新の日付を選択
        valid_dates = group.dropna(subset=['PACK_DATE_converted'])
        if len(valid_dates) > 0:
            latest_idx = valid_dates['PACK_DATE_converted'].idxmax()
            return group.loc[[latest_idx]]
        else:
            # 全てNaNの場合は最初の行を返す
            return group.iloc[[0]]
    
    # グループごとに最新行を抽出
    result_df = df_copy.groupby('FINAL_ITEM_CODE', group_keys=False).apply(get_latest_row)
    
    # 一時的な変換用列を削除
    result_df = result_df.drop('PACK_DATE_converted', axis=1)
    
    return result_df.reset_index(drop=True)

def filter_by_group_conditions(df):
    """
    FINAL_ITEM_CODE+VERSIONのグループごとに条件チェックを行い、
    条件を満たす行のみで構成されたグループのデータを抽出
    
    条件:
    - PROCESS_CODE = 'GAI' または
    - RES_CODE1 IN ('000', '002', '003', '004', '005', '006', '007', '008', '009', '010', '011', '012', '013', '014', '015')
    """
    valid_res_codes = ['000', '002', '003', '004', '005', '006', '007', '008', '009', '010', '011', '012', '013', '014', '015']
    
    # グループごとに処理
    valid_groups = []
    
    for (final_item_code, version), group in df.groupby(['FINAL_ITEM_CODE', 'VERSION']):
        # グループ内の全行が条件を満たすかチェック
        all_valid = True
        
        for _, row in group.iterrows():
            process_code = str(row.get('PROCESS_CODE', '')).strip()
            res_code1 = str(row.get('RES_CODE1', '')).strip()
            
            # 条件チェック
            condition1 = process_code == 'GAI'
            condition2 = res_code1 in valid_res_codes
            
            if not (condition1 or condition2):
                all_valid = False
                break
        
        # グループ内の全行が条件を満たす場合のみ追加
        if all_valid:
            valid_groups.append(group)
            print(f"有効グループ: {final_item_code}, VERSION={version} ({len(group)}行)")
    
    # 有効なグループを結合
    if valid_groups:
        result_df = pd.concat(valid_groups, ignore_index=True)
        return result_df
    else:
        return pd.DataFrame()

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

def main():
    # 出力ディレクトリの設定
    work_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(work_dir, exist_ok=True)
    
    print("=== krdデータベースからDATA_RES_CAPAテーブルの抽出開始 ===")
    
    # SQLクエリ - 全データを取得してPython側でフィルタリング
    sql = """
    SELECT *
    FROM DATA_RES_CAPA
    ORDER BY FINAL_ITEM_CODE, VERSION, PROCESS_ORDER, RES_CODE1
    """
    
    try:
        # データベースからデータを取得
        print("データベースに接続中...")
        df = krd_data_get(sql)
        
        print(f"取得したデータ件数: {len(df)}行")
        
        if len(df) > 0:
            print(f"全データ取得: {len(df)}行")
            
            # 条件フィルタリング - グループ単位で条件チェック
            print("条件フィルタリング実行中...")
            filtered_df = filter_by_group_conditions(df)
            
            print(f"フィルタリング後: {len(filtered_df)}行")
            
            if len(filtered_df) > 0:
                # カラム情報を表示
                print(f"カラム数: {len(filtered_df.columns)}")
                
                # データの先頭数行を表示
                print("\n先頭5行のデータ:")
                print(filtered_df.head())
                
                
                # 全データも出力 - 指示9: ファイル名変更
                all_output_path = os.path.join(work_dir, '01_外注のみ工程（マシニング課、シリンダ課）.csv')
                filtered_df.to_csv(all_output_path, encoding='utf-8-sig', index=False)
                print(f"フィルタリング済み全データ出力: {all_output_path} ({len(filtered_df)}行)")
                
            else:
                print("条件を満たすデータが見つかりませんでした。")
            
        else:
            print("該当するデータが見つかりませんでした。")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("データベース接続情報やテーブル名を確認してください。")
    
    print("=== 処理完了 ===")
    
    # 指示7: 結合処理を追加
    print("\n=== 指示7: 結合処理開始 ===")
    join_with_asp_tables(work_dir)
    
    # 指示9: 追加処理
    print("\n=== 指示9: VERSIONマッチング処理開始 ===")
    process_version_matching(work_dir)

def join_with_asp_tables(work_dir):
    """
    指示7: DATA_RES_CAPA_extracted.csvとDATA_ASP2_PUT/DATA_ASP_PUTテーブルを結合
    """
    # 指示9: ファイル名変更
    extracted_file = os.path.join(work_dir, '01_外注のみ工程（マシニング課、シリンダ課）.csv')
    
    if not os.path.exists(extracted_file):
        print("01_外注のみ工程（マシニング課、シリンダ課）.csvが見つかりません。")
        return
    
    # 抽出済みデータを読み込み
    print("01_外注のみ工程（マシニング課、シリンダ課）.csvを読み込み中...")
    df_extracted = pd.read_csv(extracted_file, encoding='utf-8-sig')
    print(f"抽出済みデータ: {len(df_extracted)}行")
    
    # FINAL_ITEM_CODEの重複を排除（最初の行のみ残す）
    df_unique = df_extracted.drop_duplicates(subset=['FINAL_ITEM_CODE'], keep='first')
    print(f"重複除去後: {len(df_unique)}行 (FINAL_ITEM_CODEがユニーク)")
    
    try:
        # 指示8: まずDATA_ASP_PUTとDATA_ASP2_PUTを縦結合
        print("DATA_ASP_PUTとDATA_ASP2_PUTの縦結合処理開始...")
        
        # DATA_ASP2_PUT から必要な3列のみ取得
        print("DATA_ASP2_PUTテーブルから3列取得中...")
        sql_asp2_simple = """
        SELECT SETU_F, PACK_DATE, VERSION
        FROM DATA_ASP2_PUT
        WHERE SETU_F IS NOT NULL AND SETU_F != ''
        """
        df_asp2_simple = krd_data_get(sql_asp2_simple)
        print(f"DATA_ASP2_PUT取得: {len(df_asp2_simple)}行")
        
        # DATA_ASP_PUT から必要な3列のみ取得
        print("DATA_ASP_PUTテーブルから3列取得中...")
        sql_asp_simple = """
        SELECT SETU_F, PACK_DATE, VERSION
        FROM DATA_ASP_PUT
        WHERE SETU_F IS NOT NULL AND SETU_F != ''
        """
        df_asp_simple = krd_data_get(sql_asp_simple)
        print(f"DATA_ASP_PUT取得: {len(df_asp_simple)}行")
        
        # 2つのテーブルを縦結合
        df_asp_combined = pd.concat([df_asp2_simple, df_asp_simple], ignore_index=True)
        print(f"縦結合後: {len(df_asp_combined)}行")
        
        # FINAL_ITEM_CODE と SETU_F で結合（重複除去済みデータを使用）
        df_joined_combined = pd.merge(
            df_unique, df_asp_combined, 
            left_on='FINAL_ITEM_CODE', right_on='SETU_F', 
            how='left', suffixes=('', '_ASP')
        )
        
        # 同じFINAL_ITEM_CODEに対して、PACK_DATEが最も新しい1行のみ抽出
        print(f"結合後: {len(df_joined_combined)}行")
        df_joined_latest = filter_latest_pack_date(df_joined_combined)
        print(f"PACK_DATE最新行抽出後: {len(df_joined_latest)}行")
        
        # 最終結果を出力 - 指示9: ファイル名変更
        latest_version_path = os.path.join(work_dir, '02_最新使用VERSION.csv')
        df_joined_latest.to_csv(latest_version_path, encoding='utf-8-sig', index=False)
        print(f"02_最新使用VERSION.csv出力完了: {latest_version_path} ({len(df_joined_latest)}行)")
        
    except Exception as e:
        print(f"結合処理でエラーが発生しました: {e}")

def process_version_matching(work_dir):
    """
    指示9: 02_最新使用VERSION.csvを編集し、VERSIONとVERSION_ASPが一致する行のみを抽出
    """
    latest_version_file = os.path.join(work_dir, '02_最新使用VERSION.csv')
    
    if not os.path.exists(latest_version_file):
        print("02_最新使用VERSION.csvが見つかりません。")
        return
    
    try:
        # CSVファイルを読み込み
        print("02_最新使用VERSION.csvを読み込み中...")
        df = pd.read_csv(latest_version_file, encoding='utf-8-sig')
        print(f"読み込みデータ: {len(df)}行")
        
        # VERSIONとVERSION_ASPの列が存在するかチェック
        if 'VERSION' not in df.columns or 'VERSION_ASP' not in df.columns:
            print("必要な列（VERSION, VERSION_ASP）が見つかりません。")
            print(f"利用可能な列: {list(df.columns)}")
            return
        
        # VERSIONとVERSION_ASPが一致する行のみ抽出
        matched_df = df[df['VERSION'] == df['VERSION_ASP']]
        print(f"VERSIONマッチング後: {len(matched_df)}行")
        
        # 結果を03_外注対象.csvとして出力
        output_file = os.path.join(work_dir, '03_外注対象.csv')
        matched_df.to_csv(output_file, encoding='utf-8-sig', index=False)
        print(f"03_外注対象.csv出力完了: {output_file} ({len(matched_df)}行)")
        
    except Exception as e:
        print(f"VERSIONマッチング処理でエラーが発生しました: {e}")

if __name__ == "__main__":
    main()