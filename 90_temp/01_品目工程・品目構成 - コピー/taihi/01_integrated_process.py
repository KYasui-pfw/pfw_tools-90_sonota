import pandas as pd
import os

def cleanup_file(file_path):
    """ファイルを削除する"""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"削除: {os.path.basename(file_path)}")

def main():
    # ディレクトリパスの設定
    work_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== ステップ0: 前工程横展開(C).csvとCAFIN.csvの突合 ===")
    
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input"
    
    # 前工程横展開(C).csvとCAFIN.csvを読み込み
    zenkoutei_c_file = os.path.join(input_dir, "前工程横展開(C).csv")
    cafin_file = os.path.join(input_dir, "CAFIN.csv")
    
    cafin_codes = set()
    
    # CAFIN.csvから品目コードを取得
    if os.path.exists(cafin_file):
        print(f"読み込み中: CAFIN.csv")
        try:
            cafin_df = pd.read_csv(cafin_file, encoding='utf-8-sig')
        except UnicodeDecodeError:
            cafin_df = pd.read_csv(cafin_file, encoding='shift_jis')
        
        if '品目コード' in cafin_df.columns:
            cafin_codes.update(cafin_df['品目コード'].dropna().astype(str))
            print(f"CAFIN.csv: {len(cafin_df['品目コード'].dropna())}件の品目コード")
    
    # 前工程横展開(C).csvを読み込み
    if os.path.exists(zenkoutei_c_file):
        print(f"読み込み中: 前工程横展開(C).csv")
        try:
            zenkoutei_c_df = pd.read_csv(zenkoutei_c_file, encoding='shift_jis', header=None)
        except UnicodeDecodeError:
            zenkoutei_c_df = pd.read_csv(zenkoutei_c_file, encoding='utf-8', header=None)
        
        print(f"前工程横展開(C).csv: {zenkoutei_c_df.shape[0]}行 {zenkoutei_c_df.shape[1]}列")
        
        # 完成部番列（2列目、インデックス1）で突合
        zenkoutei_c_df['完成部番_str'] = zenkoutei_c_df.iloc[:, 1].astype(str)
        
        # ヘッダー行を除いてデータ行のみで判定
        header_row = zenkoutei_c_df.iloc[0:1].copy()
        data_rows = zenkoutei_c_df.iloc[1:].copy()
        
        # CAFIN.csvと突合
        matched_mask = data_rows['完成部番_str'].isin(cafin_codes)
        
        matched_rows = data_rows[matched_mask]  # 一致（対象外）
        unmatched_rows = data_rows[~matched_mask]  # 不一致（対象）
        
        print(f"CAFIN.csvと一致した行（対象外）: {len(matched_rows)}行")
        print(f"CAFIN.csvと一致しなかった行（対象）: {len(unmatched_rows)}行")
        
        # 対象外データ（一致したデータ）を出力
        taishogai_file = os.path.join(work_dir, "04_前工程横展開(C)_対象外.csv")
        if len(matched_rows) > 0:
            taishogai_df = pd.concat([header_row, matched_rows], ignore_index=True)
            taishogai_df.drop('完成部番_str', axis=1, inplace=True)
            taishogai_df.to_csv(taishogai_file, encoding='utf-8-sig', index=False, header=False)
            print(f"対象外データ出力完了: {taishogai_file}")
        else:
            # 対象外データがない場合でもヘッダーのみのファイルを作成
            header_only = header_row.copy()
            header_only.drop('完成部番_str', axis=1, inplace=True)
            header_only.to_csv(taishogai_file, encoding='utf-8-sig', index=False, header=False)
            print(f"対象外データなし（ヘッダーのみ）: {taishogai_file}")
        
        # 対象データ（不一致データ）を出力
        taisho_file = os.path.join(work_dir, "05_前工程横展開(C)_対象.csv")
        if len(unmatched_rows) > 0:
            taisho_df = pd.concat([header_row, unmatched_rows], ignore_index=True)
            taisho_df.drop('完成部番_str', axis=1, inplace=True)
            taisho_df.to_csv(taisho_file, encoding='utf-8-sig', index=False, header=False)
            print(f"対象データ出力完了: {taisho_file}")
        else:
            # 対象データがない場合でもヘッダーのみのファイルを作成
            header_only = header_row.copy()
            header_only.drop('完成部番_str', axis=1, inplace=True)
            header_only.to_csv(taisho_file, encoding='utf-8-sig', index=False, header=False)
            print(f"対象データなし（ヘッダーのみ）: {taisho_file}")
    
    print("\n=== ステップ1: CSVファイルの結合 ===")
    
    # CSVファイルのリスト（前工程横展開(C)_対象.csvを使用）
    csv_files = [
        "前工程横展開.csv",
        "前工程横展開(I).csv", 
        "05_前工程横展開(C)_対象.csv"
    ]
    
    
    # データフレームのリスト
    dataframes = []
    
    # 各CSVファイルを読み込み
    for i, file in enumerate(csv_files):
        # 05_前工程横展開(C)_対象.csvはworkディレクトリから読み込み
        if file == "05_前工程横展開(C)_対象.csv":
            file_path = os.path.join(work_dir, file)
        else:
            file_path = os.path.join(input_dir, file)
            
        if os.path.exists(file_path):
            print(f"読み込み中: {file}")
            # エンコーディングを指定してCSVを読み込み
            try:
                df = pd.read_csv(file_path, encoding='shift_jis', header=None)
                
                # 2つ目以降のファイルはヘッダー行（1行目）を削除
                if i > 0:
                    df = df.iloc[1:]  # 1行目（ヘッダー）をスキップ
                    print(f"  {file}: {df.shape[0]}行 {df.shape[1]}列 (ヘッダー削除後)")
                else:
                    print(f"  {file}: {df.shape[0]}行 {df.shape[1]}列")
                
                dataframes.append(df)
                
            except UnicodeDecodeError:
                # Shift_JISで読めない場合はUTF-8を試す
                df = pd.read_csv(file_path, encoding='utf-8', header=None)
                
                # 2つ目以降のファイルはヘッダー行（1行目）を削除
                if i > 0:
                    df = df.iloc[1:]  # 1行目（ヘッダー）をスキップ
                    print(f"  {file}: {df.shape[0]}行 {df.shape[1]}列 (ヘッダー削除後)")
                else:
                    print(f"  {file}: {df.shape[0]}行 {df.shape[1]}列")
                
                dataframes.append(df)
        else:
            print(f"ファイルが見つかりません: {file}")
    
    # データフレームを縦に結合
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"結合後: {combined_df.shape[0]}行 {combined_df.shape[1]}列")
        
        # 1列目（インデックス0）を削除
        if combined_df.shape[1] > 0:
            combined_df = combined_df.iloc[:, 1:]
            print(f"1列目削除後: {combined_df.shape[0]}行 {combined_df.shape[1]}列")
        
        # 20列目（インデックス19）以降の列を削除（19列目=前工程6まで残す）
        if combined_df.shape[1] > 19:
            combined_df = combined_df.iloc[:, :19]
            print(f"20列目以降削除後: {combined_df.shape[0]}行 {combined_df.shape[1]}列")
        
        # 中間結果をCSVファイルに出力
        combined_file = os.path.join(output_dir, "06_combined_前工程横展開.csv")
        combined_df.to_csv(combined_file, encoding='utf-8-sig', index=False, header=False)
        print(f"結合ファイル出力完了: {combined_file}")
        
        print("\n=== ステップ1.5: 前工程横展開(C)_対象.csvと03_外注対象.csvとの突合 ===")
        
        # 05_前工程横展開(C)_対象.csvと03_外注対象.csvを読み込み
        zenkoutei_c_taisho_file = os.path.join(work_dir, "05_前工程横展開(C)_対象.csv")
        gaichu_file = os.path.join(input_dir, "03_外注対象.csv")
        
        zenkoutei_c_codes = set()
        gaichu_codes = set()
        
        # 前工程横展開(C)_対象.csvから完成部番を取得
        if os.path.exists(zenkoutei_c_taisho_file):
            print(f"読み込み中: 05_前工程横展開(C)_対象.csv")
            try:
                zenkoutei_c_df = pd.read_csv(zenkoutei_c_taisho_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                zenkoutei_c_df = pd.read_csv(zenkoutei_c_taisho_file, encoding='shift_jis')
            
            # 完成部番列（2列目、インデックス1）から取得
            if zenkoutei_c_df.shape[1] > 1:
                # ヘッダー行を除いてデータ行のみから完成部番を取得
                zenkoutei_c_codes.update(zenkoutei_c_df.iloc[1:, 1].dropna().astype(str))
                print(f"05_前工程横展開(C)_対象.csv: {len(zenkoutei_c_df.iloc[1:, 1].dropna())}件の完成部番")
        
        # 03_外注対象.csvからFINAL_ITEM_CODEを取得
        if os.path.exists(gaichu_file):
            print(f"読み込み中: 03_外注対象.csv")
            try:
                gaichu_df = pd.read_csv(gaichu_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                # UTF-8で読めない場合はShift_JISを試す
                gaichu_df = pd.read_csv(gaichu_file, encoding='shift_jis')
            
            if 'FINAL_ITEM_CODE' in gaichu_df.columns:
                gaichu_codes.update(gaichu_df['FINAL_ITEM_CODE'].dropna().astype(str))
                print(f"03_外注対象.csv: {len(gaichu_df['FINAL_ITEM_CODE'].dropna())}件のFINAL_ITEM_CODE")
        
        print(f"05_前工程横展開(C)_対象完成部番: {len(zenkoutei_c_codes)}件")
        print(f"外注対象コード: {len(gaichu_codes)}件")
        
        # ヘッダーありでDataFrameを再読み込み
        df = pd.read_csv(combined_file, encoding='utf-8-sig')
        
        # 完成部番列（1列目、インデックス0）で突合（結合処理で区分コードは削除済み）
        if df.shape[1] > 0:
            df['完成部番_str'] = df.iloc[:, 0].astype(str)
            
            # ヘッダー行を除いてデータ行のみで判定
            data_rows = df.iloc[1:].copy()
            
            # 指示11の条件: 05_前工程横展開(C)_対象.csvの「完成部番」または03_外注対象.csvの「FINAL_ITEM_CODE」が一致する行を対象とする
            zenkoutei_c_matched = data_rows['完成部番_str'].isin(zenkoutei_c_codes)
            gaichu_matched = data_rows['完成部番_str'].isin(gaichu_codes)
            
            # 条件: 05_前工程横展開(C)_対象.csvまたは03_外注対象.csvと一致する
            matched_mask = zenkoutei_c_matched | gaichu_matched
            
            matched_rows = data_rows[matched_mask]
            unmatched_rows = data_rows[~matched_mask]
            
            print(f"一致した行: {len(matched_rows)}行")
            print(f"一致しなかった行: {len(unmatched_rows)}行")
            
            # ヘッダー行を取得
            header_row = df.iloc[0:1]
            
            # 一致したデータ（ヘッダー付き）を出力
            matched_file = os.path.join(output_dir, "07_matched_前工程横展開.csv")
            if len(matched_rows) > 0:
                matched_df = pd.concat([header_row, matched_rows], ignore_index=True)
                matched_df.drop('完成部番_str', axis=1, inplace=True)
                matched_df.to_csv(matched_file, encoding='utf-8-sig', index=False, header=False)
                print(f"一致データ出力完了: {matched_file}")
            else:
                # 一致データがない場合でもヘッダーのみのファイルを作成
                header_row.drop('完成部番_str', axis=1, inplace=True)
                header_row.to_csv(matched_file, encoding='utf-8-sig', index=False, header=False)
                print(f"一致データなし（ヘッダーのみ）: {matched_file}")
            
            # 一致しなかったデータ（ヘッダー付き）を出力
            unmatched_file = os.path.join(output_dir, "08_unmatched_前工程横展開.csv")
            if len(unmatched_rows) > 0:
                unmatched_df = pd.concat([header_row, unmatched_rows], ignore_index=True)
                unmatched_df.drop('完成部番_str', axis=1, inplace=True)
                unmatched_df.to_csv(unmatched_file, encoding='utf-8-sig', index=False, header=False)
                print(f"不一致データ出力完了: {unmatched_file}")
        
        # ステップ1の中間ファイルは削除しない（全て保存）
        # cleanup_file(combined_file)
        
        print("\n=== ステップ2: MA-プレフィックス分離 ===")
        
        # 一致したデータを使用してステップ2以降を実行
        df = pd.read_csv(matched_file, encoding='utf-8-sig', header=None)
        print(f"データサイズ: {df.shape[0]}行 {df.shape[1]}列")
        
        # 前工程列のインデックス（0ベース）
        # 前工程1=3, 前工程2=6, 前工程3=9, 前工程4=12, 前工程5=15, 前工程6=18
        zenkou_columns = [3, 6, 9, 12, 15, 18]
        
        # MA-で始まる行とそうでない行を分離
        ma_rows = []
        non_ma_rows = []
        
        # 全ての行をデータ行として処理（ヘッダーなし）
        for idx, row in df.iterrows():
            
            # 各行で前工程が空欄でないセットの中で最も右にある前工程を見つける
            rightmost_zenkou = ""
            rightmost_index = -1
            
            for col_idx in zenkou_columns:
                if col_idx < len(row) and pd.notna(row.iloc[col_idx]) and str(row.iloc[col_idx]).strip() != "":
                    rightmost_zenkou = str(row.iloc[col_idx]).strip()
                    rightmost_index = col_idx
            
            # 最も右の前工程が存在する場合のみ処理
            if rightmost_zenkou:
                if rightmost_zenkou.startswith("MA-"):
                    ma_rows.append(row)
                else:
                    non_ma_rows.append(row)
        
        print(f"MA-で始まる行: {len(ma_rows)}行")
        print(f"MA-で始まらない行: {len(non_ma_rows)}行")
        
        # MA-で始まるデータを出力
        ma_output_file = os.path.join(output_dir, "09_MA_prefix_data.csv")
        if ma_rows:
            ma_df = pd.concat([row.to_frame().T for row in ma_rows], ignore_index=True)
            ma_df.to_csv(ma_output_file, encoding='utf-8-sig', index=False, header=False)
            print(f"MA-データ出力完了: {ma_output_file}")
        
        # MA-で始まらないデータを出力
        non_ma_output_file = os.path.join(output_dir, "10_non_MA_prefix_data.csv")
        if non_ma_rows:
            non_ma_df = pd.concat([row.to_frame().T for row in non_ma_rows], ignore_index=True)
            non_ma_df.to_csv(non_ma_output_file, encoding='utf-8-sig', index=False, header=False)
            print(f"非MA-データ出力完了: {non_ma_output_file}")
        
        # ステップ1の中間ファイルは削除しない（全て保存）
        # cleanup_file(combined_file)
        
        print("\n=== ステップ3: データ展開処理 ===")
        
        # ステップ3: 09_MA_prefix_data.csv と 10_non_MA_prefix_data.csv を展開
        ma_expanded_file = os.path.join(output_dir, "11_MA_expanded_data.csv")
        non_ma_expanded_file = os.path.join(output_dir, "12_non_MA_expanded_data.csv")
        
        expand_data(output_dir, "09_MA_prefix_data.csv", "11_MA_expanded_data.csv")
        expand_data(output_dir, "10_non_MA_prefix_data.csv", "12_non_MA_expanded_data.csv")
        
        # ステップ2の中間ファイルは削除しない（全て保存）
        # cleanup_file(ma_output_file)
        # cleanup_file(non_ma_output_file)
        
        print("\n=== ステップ4: 前工程空白削除と最終分離 ===")
        
        # ステップ4: 11_MA_expanded_data.csv を処理
        process_step4_ma_data(output_dir, "11_MA_expanded_data.csv")
        
        # 12_non_MA_expanded_data.csv から前工程空白行を削除
        process_step4_non_ma_data(output_dir, "12_non_MA_expanded_data.csv")
        
        # ステップ3の中間ファイルは削除しない（全て保存）
        # cleanup_file(ma_expanded_file)  # 11_MA_expanded_data.csvを保存するためコメントアウト
        # 12_non_MA_expanded_data.csvと11_MA_expanded_data.csvは最終出力として残すため削除しない
        
        print("\n=== 処理完了 ===")
        print("最終出力ファイル:")
        print(f"  - 13_品目構成work.csv: {os.path.join(output_dir, '13_品目構成work.csv')}")
        print(f"  - 14_品目工程work.csv: {os.path.join(output_dir, '14_品目工程work.csv')}")
        print(f"  - 11_MA_expanded_data.csv: {os.path.join(output_dir, '11_MA_expanded_data.csv')}")
        print(f"  - 12_non_MA_expanded_data.csv (空白行削除済): {os.path.join(output_dir, '12_non_MA_expanded_data.csv')}")
        print(f"  - 07_matched_前工程横展開.csv: {os.path.join(output_dir, '07_matched_前工程横展開.csv')}")
        print(f"  - 08_unmatched_前工程横展開.csv: {os.path.join(output_dir, '08_unmatched_前工程横展開.csv')}")
        print(f"  - 06_combined_前工程横展開.csv: {os.path.join(output_dir, '06_combined_前工程横展開.csv')}")
        print(f"  - 09_MA_prefix_data.csv: {os.path.join(output_dir, '09_MA_prefix_data.csv')}")
        print(f"  - 10_non_MA_prefix_data.csv: {os.path.join(output_dir, '10_non_MA_prefix_data.csv')}")
        
    else:
        print("結合するデータがありません。")

def expand_data(output_dir, input_filename, output_filename):
    """
    CSVファイルを読み込み、各行を6行に展開する
    """
    input_file = os.path.join(output_dir, input_filename)
    output_file = os.path.join(output_dir, output_filename)
    
    if not os.path.exists(input_file):
        print(f"ファイルが見つかりません: {input_file}")
        return
    
    print(f"展開処理中: {input_filename}")
    
    # CSVファイルを読み込み（ヘッダーなし）
    df = pd.read_csv(input_file, encoding='utf-8-sig', header=None)
    
    # 展開後のデータを格納するリスト
    expanded_rows = []
    
    # 各行を処理（全行がデータ行）
    for idx, row in df.iterrows():
            
        completion_code = row.iloc[0]  # 完成部番（結合処理で区分コードは削除済み）
        
        # 6セットのデータを逆順で処理（No=1が単位数分子6になるように）
        # セット6 → No=1, セット5 → No=2, ..., セット1 → No=6
        for set_num in range(6, 0, -1):  # 6から1へ
            no = 7 - set_num  # No値：6→1, 5→2, 4→3, 3→4, 2→5, 1→6
            
            # 列インデックスを計算
            # セット1: 単位数分子1(1), 単位数分母1(2), 前工程1(3)
            # セット2: 単位数分子2(4), 単位数分母2(5), 前工程2(6)
            # ...
            # セットN: 単位数分子N(3*N-2), 単位数分母N(3*N-1), 前工程N(3*N)
            bunshi_idx = 3 * set_num - 2
            bunbo_idx = 3 * set_num - 1
            zenkou_idx = 3 * set_num
            
            # 値を取得（範囲外や空の場合は空文字）
            bunshi = row.iloc[bunshi_idx] if bunshi_idx < len(row) else ""
            bunbo = row.iloc[bunbo_idx] if bunbo_idx < len(row) else ""
            zenkou = row.iloc[zenkou_idx] if zenkou_idx < len(row) else ""
            
            # NaNを空文字に変換
            if pd.isna(bunshi):
                bunshi = ""
            if pd.isna(bunbo):
                bunbo = ""
            if pd.isna(zenkou):
                zenkou = ""
            
            # 展開行を作成
            expanded_rows.append([no, completion_code, bunshi, bunbo, zenkou])
    
    # 展開後のDataFrameを作成
    expanded_df = pd.DataFrame(expanded_rows, columns=['No', '完成部番', '単位数分子', '単位数分母', '前工程'])
    
    # CSVファイルに出力
    expanded_df.to_csv(output_file, encoding='utf-8-sig', index=False)
    print(f"展開データ出力完了: {output_file} ({len(expanded_rows)}行)")

def process_step4_ma_data(output_dir, input_filename):
    """
    MA_expanded_data.csvを処理してMA-で始まる行と始まらない行に分離
    前工程が空白の行は除外
    """
    input_file = os.path.join(output_dir, input_filename)
    
    if not os.path.exists(input_file):
        print(f"ファイルが見つかりません: {input_file}")
        return
    
    print(f"ステップ4処理中: {input_filename}")
    
    # CSVファイルを読み込み
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    # 前工程が空白でない行のみ抽出
    non_empty_df = df[df['前工程'].notna() & (df['前工程'].astype(str).str.strip() != "")]
    
    # MA-で始まる行と始まらない行に分離
    ma_rows = non_empty_df[non_empty_df['前工程'].astype(str).str.startswith("MA-")]
    non_ma_rows = non_empty_df[~non_empty_df['前工程'].astype(str).str.startswith("MA-")]
    
    print(f"前工程空白削除後: {len(non_empty_df)}行")
    print(f"MA-で始まる行: {len(ma_rows)}行 → 13_品目構成work.csv")
    print(f"MA-で始まらない行: {len(non_ma_rows)}行 → 14_品目工程work.csv")
    
    # 13_品目構成work.csv（MA-で始まる行）
    if len(ma_rows) > 0:
        kousei_file = os.path.join(output_dir, "13_品目構成work.csv")
        ma_rows.to_csv(kousei_file, encoding='utf-8-sig', index=False)
        print(f"13_品目構成work.csv出力完了: {kousei_file} ({len(ma_rows)}行)")
    
    # 14_品目工程work.csv（MA-で始まらない行）
    if len(non_ma_rows) > 0:
        koutei_file = os.path.join(output_dir, "14_品目工程work.csv")
        non_ma_rows.to_csv(koutei_file, encoding='utf-8-sig', index=False)
        print(f"14_品目工程work.csv出力完了: {koutei_file} ({len(non_ma_rows)}行)")

def process_step4_non_ma_data(output_dir, input_filename):
    """
    non_MA_expanded_data.csvから前工程が空白の行を削除
    """
    input_file = os.path.join(output_dir, input_filename)
    
    if not os.path.exists(input_file):
        print(f"ファイルが見つかりません: {input_file}")
        return
    
    print(f"12_non_MA_expanded_data.csv前工程空白削除中...")
    
    # CSVファイルを読み込み
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    # 前工程が空白でない行のみ抽出
    non_empty_df = df[df['前工程'].notna() & (df['前工程'].astype(str).str.strip() != "")]
    
    print(f"12_non_MA_expanded_data.csv: {len(df)}行 → {len(non_empty_df)}行 (空白削除後)")
    
    # 元ファイルを上書き
    non_empty_df.to_csv(input_file, encoding='utf-8-sig', index=False)
    print(f"12_non_MA_expanded_data.csv更新完了: {input_file}")

if __name__ == "__main__":
    main()