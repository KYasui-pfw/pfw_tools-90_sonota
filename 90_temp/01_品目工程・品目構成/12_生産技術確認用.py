import pandas as pd
import os
from datetime import datetime

def main():
    """
    生産技術確認用のデータ処理を行う
    - 06_combined_前工程横展開.csvから前工程1が"PEFIN-"で始まり、前工程3が空欄ではないデータを抽出
    - 工程順序が不明なデータとして出力
    """
    
    # ディレクトリパスの設定
    work_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    kensyou_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\kensyou"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(kensyou_dir, exist_ok=True)
    
    print("=== 生産技術確認用データ処理 ===")
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 入力ファイルの読み込み
    print("\n=== ファイル読み込み ===")
    
    # 06_combined_前工程横展開.csvの読み込み
    combined_file = os.path.join(work_dir, "06_combined_前工程横展開.csv")
    if not os.path.exists(combined_file):
        print(f"エラー: ファイルが見つかりません - {combined_file}")
        return
    
    df = pd.read_csv(combined_file, encoding='utf-8-sig')
    print(f"06_combined_前工程横展開.csv読み込み: {len(df)}行")
    
    # 2. 抽出条件の適用
    print("\n=== 抽出条件適用 ===")
    
    # 抽出対象データを格納するリスト
    target_rows = []
    
    for idx, row in df.iterrows():
        # 前工程1が"PEFIN-"で始まるかチェック
        zenkou1 = str(row['前工程1']).strip() if pd.notna(row['前工程1']) else ""
        
        if zenkou1.startswith("PEFIN-"):
            # 前工程3が空欄ではないかチェック
            zenkou3 = str(row['前工程3']).strip() if pd.notna(row['前工程3']) else ""
            
            if zenkou3 != "" and zenkou3 != "nan":
                # 条件を満たすデータを追加
                target_rows.append(row)
    
    print(f"抽出条件を満たすデータ: {len(target_rows)}行")
    
    if len(target_rows) == 0:
        print("抽出対象データがありません")
        return
    
    # 3. 結果DataFrameの作成
    result_df = pd.DataFrame(target_rows)
    
    # 4. 統計情報・サンプル表示
    print(f"\n=== 抽出結果統計 ===")
    print(f"総入力データ: {len(df):,}行")
    print(f"抽出データ: {len(result_df):,}行")
    print(f"抽出率: {len(result_df)/len(df)*100:.2f}%")
    
    # 完成部番の重複確認
    unique_items = result_df['完成部番'].nunique()
    print(f"ユニーク完成部番数: {unique_items}件")
    
    # サンプルデータ表示
    if len(result_df) > 0:
        print(f"\n=== 抽出データサンプル（最初の10行） ===")
        sample_cols = ['完成部番', '前工程1', '前工程2', '前工程3']
        available_cols = [col for col in sample_cols if col in result_df.columns]
        print(result_df[available_cols].head(10).to_string(index=False))
        
        # 前工程パターンの分析
        print(f"\n=== 前工程パターン分析 ===")
        
        # PEFIN-パターンの種類
        pefin_patterns = result_df['前工程1'].value_counts().head(10)
        print("前工程1パターン（上位10件）:")
        for pattern, count in pefin_patterns.items():
            print(f"  {pattern}: {count}件")
        
        # 前工程3のパターン
        zenkou3_patterns = result_df['前工程3'].value_counts().head(10)
        print("\n前工程3パターン（上位10件）:")
        for pattern, count in zenkou3_patterns.items():
            print(f"  {pattern}: {count}件")
    
    # 5. CSV出力
    output_file = os.path.join(kensyou_dir, "生産技術確認用_工程順不明.csv")
    result_df.to_csv(output_file, encoding='utf-8-sig', index=False)
    
    print(f"\n=== CSV出力完了 ===")
    print(f"出力ファイル: {output_file}")
    print(f"出力件数: {len(result_df):,}件")
    print(f"実行完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n=== 処理完了 ===")
    print("前工程1がPEFIN-で始まり、前工程3が空欄ではないデータを抽出しました。")
    print("これらは工程順序の確認が必要なデータです。")

if __name__ == "__main__":
    main()