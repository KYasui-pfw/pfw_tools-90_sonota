import pandas as pd
import os
from datetime import datetime

def main():
    """
    品目構成work.csvを読み込んで、M0850品目構成マスタのレイアウトでCSV出力する
    """
    # ディレクトリパスの設定
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\output"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== 品目構成マスタ(M0850)出力処理 ===")
    
    # 入力ファイルのパス
    input_file = os.path.join(input_dir, "品目構成work.csv")
    
    # ファイル存在確認
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません - {input_file}")
        return
    
    # CSVファイルを読み込み
    print(f"読み込み中: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"入力データ: {len(df)}行")
    
    # M0850のレイアウトに従ってデータを変換
    output_data = []
    
    for index, row in df.iterrows():
        # 指示5に従って各フィールドをマッピング
        record = {
            'OYAHMCD': str(row['完成部番']) if pd.notna(row['完成部番']) else '',  # インプットの「完成部番」
            'SEQ': 1,  # 固定で1
            'STRNO': 1,  # 固定で1
            'OYAREVNO': 1,  # 固定で1
            'STRSEQ': 1,  # 固定で1
            'KOHMCD': str(row['前工程']) if pd.notna(row['前工程']) else '',  # インプットの「前工程」
            'SIZEX': '',  # 空欄
            'SIZEY': '',  # 空欄
            'SIZEZ': '',  # 空欄
            'SHAPEQTY': 1,  # 固定で1
            'OYAQTYKBN': 1,  # 固定で1
            'OYAQTY': 1,  # 固定で1
            'OYAUNIT': 'PC',  # 固定で"PC"
            'KOQTY': float(row['単位数分子']) if pd.notna(row['単位数分子']) else 1.0,  # 単位数分子を使用
            'KOUNIT': 'PC',  # 固定で"PC"（子品目単位も同じと仮定）
            'VALDEC': 0,  # 固定で0
            'HASUKBN': 1,  # 固定で1
            'NOTE': '',  # 空欄
            'REVNOTE': '',  # 空欄
            'REVDT': '',  # 空欄
            'REVTANCD': '',  # 空欄
            'VALFLG': 1,  # 固定で1
            'INSTID': '',  # 空欄
            'INSTDT': '',  # 空欄
            'UPDTID': '',  # 空欄
            'UPDTDT': ''  # 空欄
        }
        
        output_data.append(record)
    
    # DataFrameを作成
    output_df = pd.DataFrame(output_data)
    
    # 出力ファイルのパス
    output_file = os.path.join(output_dir, "M0850_品目構成マスタ.csv")
    
    # CSVファイルに出力（ヘッダー付き）
    output_df.to_csv(output_file, encoding='utf-8-sig', index=False)
    
    print(f"出力完了: {output_file}")
    print(f"出力データ: {len(output_df)}行")
    
    # 出力内容のサンプルを表示
    print("\n=== 出力データサンプル（最初の5行） ===")
    print(output_df.head().to_string(index=False))
    
    print("\n=== フィールドマッピング確認 ===")
    print("OYAHMCD (親品目コード) ← 完成部番")
    print("KOHMCD (子品目コード) ← 前工程")
    print("KOQTY (子品目数量) ← 単位数分子")
    print("固定値: SEQ=1, STRNO=1, OYAREVNO=1, STRSEQ=1, SHAPEQTY=1")
    print("固定値: OYAQTYKBN=1, OYAQTY=1, HASUKBN=1, VALFLG=1")
    print("固定値: VALDEC=0, OYAUNIT='PC', KOUNIT='PC'")
    print("空欄: SIZEX, SIZEY, SIZEZ, NOTE, REVNOTE, REVDT, REVTANCD")

if __name__ == "__main__":
    main()