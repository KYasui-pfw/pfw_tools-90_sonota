import pandas as pd
import os
from datetime import datetime
import cx_Oracle

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

def main():
    """
    14_品目工程work.csvを読み込んで、M0840品目工程マスタのレイアウトでCSV出力する
    """
    # ディレクトリパスの設定
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\output"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== 品目工程マスタ(M0840)出力処理 ===")
    
    # 入力ファイルのパス
    input_file = os.path.join(input_dir, "14_品目工程work.csv")
    
    # ファイル存在確認
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません - {input_file}")
        return
    
    # CSVファイルを読み込み
    print(f"読み込み中: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"入力データ: {len(df)}行")
    
    # M0410工程マスタを読み込み
    print("\n=== M0410工程マスタ読み込み ===")
    m0410_file = os.path.join(r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input", "M0410_工程マスタ.csv")
    try:
        m0410_df = pd.read_csv(m0410_file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        m0410_df = pd.read_csv(m0410_file, encoding='shift_jis')
    valid_ktcd_set = set(m0410_df['KTCD'].astype(str))
    print(f"有効KTCD数: {len(valid_ktcd_set)}件")
    
    # EJシステムからSRCD用データを取得
    print("\n=== EJシステム（M_PUCH_UNIT_COST）データ取得 ===")
    try:
        srcd_sql = """
        SELECT ITEM_CD, VEND_CD, EFF_PHASE_IN_DATE
        FROM EXPJ2.M_PUCH_UNIT_COST
        ORDER BY ITEM_CD, EFF_PHASE_IN_DATE DESC
        """
        srcd_df = ej_data_get(srcd_sql)
        print(f"SRCD用データ取得: {len(srcd_df)}行")
        
        # 最新日付のレコードのみを抽出
        srcd_latest = srcd_df.groupby('ITEM_CD').first().reset_index()
        srcd_dict = dict(zip(srcd_latest['ITEM_CD'], srcd_latest['VEND_CD']))
        print(f"SRCD辞書作成: {len(srcd_dict)}件")
    except Exception as e:
        print(f"SRCD用データ取得エラー: {e}")
        srcd_dict = {}
    
    # EJシステムからLDTIME用データを取得
    print("\n=== EJシステム（M_ITEM）データ取得 ===")
    try:
        ldtime_sql = """
        SELECT ITEM_CD, PUCH_FIXED_LT
        FROM EXPJ2.M_ITEM
        """
        ldtime_df = ej_data_get(ldtime_sql)
        print(f"LDTIME用データ取得: {len(ldtime_df)}行")
        
        ldtime_dict = dict(zip(ldtime_df['ITEM_CD'], ldtime_df['PUCH_FIXED_LT']))
        print(f"LDTIME辞書作成: {len(ldtime_dict)}件")
    except Exception as e:
        print(f"LDTIME用データ取得エラー: {e}")
        ldtime_dict = {}
    
    # 完成部番でグループ化してSEQとKTSEQを計算
    output_data = []
    
    # 完成部番でグループ化
    grouped = df.groupby('完成部番')
    
    for hmcd, group in grouped:
        # 同一HMCDに対して連番を付与
        for idx, (_, row) in enumerate(group.iterrows(), 1):
            # 前工程からKTCDを抽出（最初のハイフンまでの文字列）
            zenkatei = str(row['前工程']) if pd.notna(row['前工程']) else ''
            if '-' in zenkatei:
                ktcd = zenkatei.split('-')[0]
            else:
                ktcd = zenkatei  # ハイフンがない場合はそのまま
            
            # KTCDの存在チェック
            if ktcd not in valid_ktcd_set:
                ktcd = ktcd + "（無）"
            
            # 前工程をキーにしてSRCDを取得、完成部番をキーにしてLDTIMEを取得
            zenkatei_key = str(row['前工程']) if pd.notna(row['前工程']) else ''
            srcd_value = srcd_dict.get(zenkatei_key, "無し")
            kansei_bango = str(hmcd) if pd.notna(hmcd) else ''
            ldtime_value = ldtime_dict.get(kansei_bango, 0)
            
            # M0840のレイアウトに従ってデータを変換
            record = {
                'HMCD': str(hmcd) if pd.notna(hmcd) else '',  # 完成部番
                'SEQ': idx,  # 同じHMCDの場合、1単位で連番
                'KTSEQ': idx * 10,  # 同じHMCDの場合、10単位で連番
                'KTCD': ktcd,  # 前工程の最初のハイフンまでの文字列（存在チェック済）
                'SRCD': str(srcd_value),  # EJ M_PUCH_UNIT_COSTから取得
                'SGNCD': '仮',  # 固定文字列"仮"
                'DDTIME': 0,  # 固定値"0"
                'SGTIME': 0,  # 固定値"0"
                'LDTIME': int(ldtime_value) if ldtime_value is not None else 0,  # EJ M_ITEMから取得
                'SRPRICE': 0,  # 固定値"0"
                'CSBCD': '10',  # 固定値"10"
                'SUPCLSCD': '',  # 空欄
                'SUPCD': '',  # 空欄
                'RCVTSTKBN': '2',  # 固定値"2"
                'RCVCHKKBN': '2',  # 固定値"2"
                'INSTID': '',  # 空欄
                'INSTDT': '',  # 空欄
                'UPDTID': '',  # 空欄
                'UPDTDT': ''  # 空欄
            }
            
            output_data.append(record)
    
    # DataFrameを作成
    output_df = pd.DataFrame(output_data)
    
    # 出力ファイルのパス
    output_file = os.path.join(output_dir, "M0840_品目工程マスタ.csv")
    
    # CSVファイルに出力（ヘッダー付き）
    output_df.to_csv(output_file, encoding='utf-8-sig', index=False)
    
    print(f"出力完了: {output_file}")
    print(f"出力データ: {len(output_df)}行")
    
    # 出力内容のサンプルを表示
    print("\n=== 出力データサンプル（最初の10行） ===")
    print(output_df.head(10).to_string(index=False))
    
    print("\n=== フィールドマッピング確認 ===")
    print("HMCD (品目コード) ← 14_品目工程work.csvの「完成部番」")
    print("SEQ (番号) ← 同じHMCDの場合、1単位で連番")
    print("KTSEQ (工順) ← 同じHMCDの場合、10単位で連番") 
    print("KTCD (工程コード) ← 14_品目工程work.csvの「前工程」の最初のハイフンまでの文字列（存在チェック済）")
    print("SRCD (仕入先コード) ← EJ M_PUCH_UNIT_COSTテーブルのVEND_CD（前工程をキーとして、最新日付優先）")
    print("LDTIME (リードタイム) ← EJ M_ITEMテーブルのPUCH_FIXED_LT")
    print("固定値: SGNCD='仮', DDTIME=0, SGTIME=0, SRPRICE=0, CSBCD='10', RCVTSTKBN='2', RCVCHKKBN='2'")
    print("空欄: SUPCLSCD, SUPCD, INSTID, INSTDT, UPDTID, UPDTDT")
    
    # 処理統計を表示
    print(f"\n=== 処理統計 ===")
    print(f"処理対象の品目数（HMCD）: {output_df['HMCD'].nunique()}件")
    print(f"総工程数: {len(output_df)}件")
    
    # HMCDごとの工程数を表示（上位10件）
    hmcd_counts = output_df['HMCD'].value_counts().head(10)
    print(f"\n=== HMCDごとの工程数（上位10件） ===")
    for hmcd, count in hmcd_counts.items():
        print(f"  {hmcd}: {count}工程")

if __name__ == "__main__":
    main()