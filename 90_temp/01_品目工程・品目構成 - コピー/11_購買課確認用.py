import pandas as pd
import os

def main():
    """
    購買課確認用のデータ処理を行う
    - 10_non_MA_prefix_data.csvに担当者名を追加
    - 最大前工程番号の工程コードを抽出
    - M0410工程マスタとの突合により振り分け
    """
    
    # ディレクトリパスの設定
    work_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input"
    kensyou_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\kensyou"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(kensyou_dir, exist_ok=True)
    
    print("=== 購買課確認用データ処理 ===")
    
    # 1. 入力ファイルの読み込み
    print("\n=== ファイル読み込み ===")
    
    # 10_non_MA_prefix_data.csvの読み込み
    non_ma_file = os.path.join(work_dir, "10_non_MA_prefix_data.csv")
    if not os.path.exists(non_ma_file):
        print(f"エラー: ファイルが見つかりません - {non_ma_file}")
        return
    
    df = pd.read_csv(non_ma_file, encoding='utf-8-sig')
    print(f"10_non_MA_prefix_data.csv読み込み: {len(df)}行")
    
    # 担当者.csvの読み込み
    tanto_file = os.path.join(input_dir, "担当者.csv")
    if not os.path.exists(tanto_file):
        print(f"エラー: ファイルが見つかりません - {tanto_file}")
        return
    
    # 担当者.csvは文字化けの可能性があるため、複数のエンコーディングを試す
    tanto_df = None
    for encoding in ['utf-8-sig', 'shift_jis', 'cp932']:
        try:
            tanto_df = pd.read_csv(tanto_file, encoding=encoding)
            print(f"担当者.csv読み込み成功 (encoding: {encoding}): {len(tanto_df)}行")
            break
        except UnicodeDecodeError:
            continue
    
    if tanto_df is None:
        print("エラー: 担当者.csvの読み込みに失敗しました")
        return
    
    # M0410_工程マスタ.csvの読み込み
    m0410_file = os.path.join(input_dir, "M0410_工程マスタ.csv")
    if not os.path.exists(m0410_file):
        print(f"エラー: ファイルが見つかりません - {m0410_file}")
        return
    
    m0410_df = pd.read_csv(m0410_file, encoding='utf-8-sig')
    print(f"M0410_工程マスタ.csv読み込み: {len(m0410_df)}行")
    
    # 2. 担当者名の項目追加
    print("\n=== 担当者名項目追加処理 ===")
    
    # 担当者辞書を作成
    tanto_dict = dict(zip(tanto_df['SUPCD'].astype(str), tanto_df['SUPNM']))
    
    # 担当者名列を追加（区分コードの右に挿入）
    df.insert(1, '担当者名', '')
    
    # 区分コードと担当者.csvのSUPCDを突合
    for idx, row in df.iterrows():
        kubun_code = str(row['区分コード']) if pd.notna(row['区分コード']) else ''
        tanto_name = tanto_dict.get(kubun_code, '')
        df.at[idx, '担当者名'] = tanto_name
    
    print(f"担当者名マッピング完了")
    
    # 3. 最大前工程番号の特定と工程コード抽出
    print("\n=== 最大前工程項目特定・工程コード抽出 ===")
    
    # 前工程列名を定義
    zenkatei_columns = ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6']
    
    # 各行について最大前工程番号の工程コードを抽出
    df['最大前工程項目'] = ''
    df['工程コード'] = ''
    
    for idx, row in df.iterrows():
        max_zenkatei = ''
        max_zenkatei_num = 0
        
        # 前工程1～6の中で空欄でない最も番号が大きい項目を特定
        for i, col in enumerate(zenkatei_columns, 1):
            zenkatei_value = str(row[col]) if pd.notna(row[col]) and str(row[col]).strip() != '' else ''
            if zenkatei_value:
                max_zenkatei = zenkatei_value
                max_zenkatei_num = i
        
        df.at[idx, '最大前工程項目'] = max_zenkatei
        
        # 工程コードを抽出（最初のハイフンまでの文字列）
        if max_zenkatei:
            if '-' in max_zenkatei:
                kotei_code = max_zenkatei.split('-')[0]
            else:
                kotei_code = max_zenkatei
            df.at[idx, '工程コード'] = kotei_code
    
    print(f"工程コード抽出完了")
    
    # 4. M0410工程マスタとの突合による振り分け
    print("\n=== M0410工程マスタ突合・振り分け処理 ===")
    
    # 有効なKTCDセットを作成
    valid_ktcd_set = set(m0410_df['KTCD'].astype(str))
    
    # 一致・不一致で振り分け
    matched_df = df[df['工程コード'].isin(valid_ktcd_set)].copy()
    unmatched_df = df[~df['工程コード'].isin(valid_ktcd_set)].copy()
    
    print(f"M0410工程マスタと一致: {len(matched_df)}行")
    print(f"M0410工程マスタと不一致: {len(unmatched_df)}行")
    
    # 5. 結果の出力
    print("\n=== 結果出力 ===")
    
    # 区分コード順でソート
    matched_df_sorted = matched_df.sort_values('区分コード')
    unmatched_df_sorted = unmatched_df.sort_values('区分コード')
    
    # 出力用に不要な列を除外
    output_matched = matched_df_sorted.drop(['最大前工程項目', '工程コード'], axis=1)
    output_unmatched = unmatched_df_sorted.drop(['最大前工程項目', '工程コード'], axis=1)
    
    # 一致データの出力
    matched_file = os.path.join(kensyou_dir, "購買課確認用_工程マスタ一致.csv")
    output_matched.to_csv(matched_file, encoding='utf-8-sig', index=False)
    print(f"工程マスタ一致データ出力: {matched_file}")
    
    # 不一致データの出力
    unmatched_file = os.path.join(kensyou_dir, "購買課確認用_工程マスタ不一致.csv")
    output_unmatched.to_csv(unmatched_file, encoding='utf-8-sig', index=False)
    print(f"工程マスタ不一致データ出力: {unmatched_file}")
    
    # 統計情報の表示
    print("\n=== 処理統計 ===")
    print(f"総データ数: {len(df)}行")
    print(f"工程マスタ一致: {len(matched_df)}行 ({len(matched_df)/len(df)*100:.1f}%)")
    print(f"工程マスタ不一致: {len(unmatched_df)}行 ({len(unmatched_df)/len(df)*100:.1f}%)")
    
    # 工程コード別の統計
    kotei_stats = df['工程コード'].value_counts().head(10)
    print(f"\n=== 工程コード出現頻度（上位10件） ===")
    for kotei, count in kotei_stats.items():
        match_status = "一致" if kotei in valid_ktcd_set else "不一致"
        print(f"  {kotei}: {count}件 ({match_status})")
    
    # サンプルデータの表示
    print(f"\n=== 出力データサンプル（工程マスタ一致・最初の5行） ===")
    if len(output_matched) > 0:
        sample_cols = ['区分コード', '担当者名', '完成部番']
        available_cols = [col for col in sample_cols if col in output_matched.columns]
        print(output_matched[available_cols].head().to_string(index=False))
    
    print(f"\n=== 出力データサンプル（工程マスタ不一致・最初の5行） ===")
    if len(output_unmatched) > 0:
        sample_cols = ['区分コード', '担当者名', '完成部番']
        available_cols = [col for col in sample_cols if col in output_unmatched.columns]
        print(output_unmatched[available_cols].head().to_string(index=False))

if __name__ == "__main__":
    main()