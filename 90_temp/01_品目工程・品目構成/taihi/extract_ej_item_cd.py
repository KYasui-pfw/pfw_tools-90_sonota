import pandas as pd
import cx_Oracle
import os
from datetime import datetime

def ej_data_get(sql):
    """
    EJシステム（Oracle）への接続とSQL実行
    """
    try:
        # Oracle接続設定
        dsn = cx_Oracle.makedsn("172.17.107.102", 1521, service_name="EXPJ")
        connection = cx_Oracle.connect("EXPJ2", "EXPJ2", dsn, encoding="UTF-8")
        
        # SQLクエリ実行
        df = pd.read_sql_query(sql, connection)
        connection.close()
        
        print(f"EJデータベースから {len(df)}行 取得しました")
        return df
        
    except Exception as e:
        print(f"EJデータベース接続エラー: {e}")
        return None

def main():
    """
    EJシステムのM_ITEMテーブルからITEM_CDを取得し、
    加工実績部番.csvの部番と突合して一致データのみ抽出
    """
    print("=== EJ M_ITEM ITEM_CD突合データ取得 ===")
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ディレクトリの設定
    work_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input"
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. 加工実績部番.csvの読み込み
    print("\n=== 加工実績部番.csv読み込み ===")
    kakou_file = os.path.join(input_dir, "加工実績部番.csv")
    
    if not os.path.exists(kakou_file):
        print(f"エラー: ファイルが見つかりません - {kakou_file}")
        return
    
    # 複数のエンコーディングを試す
    kakou_df = None
    for encoding in ['utf-8-sig', 'shift_jis', 'cp932']:
        try:
            kakou_df = pd.read_csv(kakou_file, encoding=encoding)
            print(f"加工実績部番.csv読み込み成功 (encoding: {encoding}): {len(kakou_df)}行")
            break
        except UnicodeDecodeError:
            continue
    
    if kakou_df is None:
        print("エラー: 加工実績部番.csvの読み込みに失敗しました")
        return
    
    # 部番列の存在確認
    if '部番' not in kakou_df.columns:
        print(f"エラー: '部番'列が見つかりません。利用可能な列: {list(kakou_df.columns)}")
        return
    
    # 部番データを取得（重複除去、空白除去）
    buban_set = set(kakou_df['部番'].dropna().astype(str).str.strip())
    print(f"加工実績部番データ件数（重複除去後）: {len(buban_set)}件")
    
    # 2. EJデータベースからデータ取得
    print("\n=== EJデータベース接続・データ取得 ===")
    sql = """
    SELECT ITEM_CD
    FROM EXPJ2.M_ITEM
    WHERE ITEM_CD NOT LIKE '!%'
    ORDER BY ITEM_CD
    """
    
    print("実行SQL:")
    print(sql)
    
    ej_df = ej_data_get(sql)
    
    if ej_df is None:
        print("EJデータ取得に失敗しました")
        return
    
    print(f"EJ M_ITEM取得件数: {len(ej_df):,}件")
    
    # 3. 突合処理
    print("\n=== 突合処理実行 ===")
    
    # EJデータのITEM_CDと加工実績部番の部番を突合
    matched_items = []
    for item_cd in ej_df['ITEM_CD']:
        if str(item_cd).strip() in buban_set:
            matched_items.append(item_cd)
    
    # 突合結果をDataFrameに変換
    matched_df = pd.DataFrame({'ITEM_CD': matched_items})
    
    print(f"突合結果: {len(matched_df)}件が一致")
    print(f"一致率: {len(matched_df)/len(ej_df)*100:.2f}%")
    
    # 4. 統計情報・サンプル表示
    print(f"\n=== 突合結果統計 ===")
    print(f"EJ M_ITEM総件数: {len(ej_df):,}件")
    print(f"加工実績部番件数: {len(buban_set):,}件")
    print(f"突合一致件数: {len(matched_df):,}件")
    
    if len(matched_df) > 0:
        print(f"\n=== 突合一致データサンプル（最初の10件） ===")
        print(matched_df.head(10).to_string(index=False))
        
        if len(matched_df) > 10:
            print(f"\n=== 突合一致データサンプル（最後の10件） ===")
            print(matched_df.tail(10).to_string(index=False))
    
    # 5. CSV出力
    output_file = os.path.join(work_dir, "EJ_M_ITEM_突合一致ITEM_CD.csv")
    matched_df.to_csv(output_file, encoding='utf-8-sig', index=False)
    
    print(f"\n=== CSV出力完了 ===")
    print(f"出力ファイル: {output_file}")
    print(f"出力件数: {len(matched_df):,}件")
    print(f"実行完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()