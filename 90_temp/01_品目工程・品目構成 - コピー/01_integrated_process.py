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
    
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input"
    
    print("=== ステップ1: CSVファイルの結合 ===")
    
    # CSVファイルのリスト（前工程横展開(C).csvを直接使用）
    csv_files = [
        "前工程横展開.csv",
        "前工程横展開(I).csv", 
        "前工程横展開(C).csv"
    ]
    
    
    # データフレームのリスト
    dataframes = []
    
    # 各CSVファイルを読み込み
    for i, file in enumerate(csv_files):
        # 全てのファイルをinputディレクトリから読み込み
        file_path = os.path.join(input_dir, file)
            
        if os.path.exists(file_path):
            print(f"読み込み中: {file}")
            # エンコーディングを指定してCSVを読み込み
            try:
                df = pd.read_csv(file_path, encoding='shift_jis', header=None)
                
                # 全てのファイルでヘッダー行（1行目）を削除
                df = df.iloc[1:]  # 1行目（ヘッダー）をスキップ
                print(f"  {file}: {df.shape[0]}行 {df.shape[1]}列 (ヘッダー削除後)")
                
                dataframes.append(df)
                
            except UnicodeDecodeError:
                # Shift_JISで読めない場合はUTF-8を試す
                df = pd.read_csv(file_path, encoding='utf-8', header=None)
                
                # 全てのファイルでヘッダー行（1行目）を削除
                df = df.iloc[1:]  # 1行目（ヘッダー）をスキップ
                print(f"  {file}: {df.shape[0]}行 {df.shape[1]}列 (ヘッダー削除後)")
                
                dataframes.append(df)
        else:
            print(f"ファイルが見つかりません: {file}")
    
    # データフレームを縦に結合
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"結合後: {combined_df.shape[0]}行 {combined_df.shape[1]}列")
        
        # 1列目（区分コード）は保持（指示16対応）
        # combined_df = combined_df.iloc[:, 1:]  # この処理を削除
        print(f"区分コード保持: {combined_df.shape[0]}行 {combined_df.shape[1]}列")
        
        # 21列目（インデックス20）以降の列を削除（20列目=前工程6まで残す、区分コード保持のため+1）
        if combined_df.shape[1] > 20:
            combined_df = combined_df.iloc[:, :20]
            print(f"21列目以降削除後: {combined_df.shape[0]}行 {combined_df.shape[1]}列")
        
        # 中間結果をCSVファイルに出力（ヘッダー付与）
        column_names = ['区分コード', '完成部番', '単位数分子1', '単位数分母1', '前工程1', '単位数分子2', '単位数分母2', '前工程2', 
                       '単位数分子3', '単位数分母3', '前工程3', '単位数分子4', '単位数分母4', '前工程4', 
                       '単位数分子5', '単位数分母5', '前工程5', '単位数分子6', '単位数分母6', '前工程6']
        combined_df.columns = column_names
        combined_file = os.path.join(output_dir, "06_combined_前工程横展開.csv")
        combined_df.to_csv(combined_file, encoding='utf-8-sig', index=False, header=True)
        print(f"結合ファイル出力完了: {combined_file}")
        
        print("\n=== ステップ1.5: 04_EJ678.csvと03_マシニング課管理工程.csvとの突合 ===")
        
        # 04_EJ678.csvと03_マシニング課管理工程.csvを読み込み
        ej_file = os.path.join(work_dir, "04_EJ678.csv")
        gaichu_file = os.path.join(work_dir, "03_マシニング課管理工程.csv")
        
        ej_data = {}  # ITEM_CD -> PRODUCT_TYP のマッピング
        gaichu_codes = set()
        
        # 04_EJ678.csvからITEM_CDとPRODUCT_TYPを取得
        if os.path.exists(ej_file):
            print(f"読み込み中: 04_EJ678.csv")
            try:
                ej_df = pd.read_csv(ej_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                ej_df = pd.read_csv(ej_file, encoding='shift_jis')
            
            if 'ITEM_CD' in ej_df.columns and 'PRODUCT_TYP' in ej_df.columns:
                for _, row in ej_df.iterrows():
                    item_cd = str(row['ITEM_CD']) if pd.notna(row['ITEM_CD']) else ""
                    product_typ = row['PRODUCT_TYP'] if pd.notna(row['PRODUCT_TYP']) else ""
                    if item_cd:
                        ej_data[item_cd] = product_typ
                print(f"04_EJ678.csv: {len(ej_data)}件のITEM_CD")
        
        # 03_マシニング課管理工程.csvからFINAL_ITEM_CODEを取得
        if os.path.exists(gaichu_file):
            print(f"読み込み中: 03_マシニング課管理工程.csv")
            try:
                gaichu_df = pd.read_csv(gaichu_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                # UTF-8で読めない場合はShift_JISを試す
                gaichu_df = pd.read_csv(gaichu_file, encoding='shift_jis')
            
            if 'FINAL_ITEM_CODE' in gaichu_df.columns:
                gaichu_codes.update(gaichu_df['FINAL_ITEM_CODE'].dropna().astype(str))
                print(f"03_マシニング課管理工程.csv: {len(gaichu_df['FINAL_ITEM_CODE'].dropna())}件のFINAL_ITEM_CODE")
        
        print(f"EJコード: {len(ej_data)}件")
        print(f"マシニング課管理工程コード: {len(gaichu_codes)}件")
        
        # ヘッダー付きでDataFrameを再読み込み
        df = pd.read_csv(combined_file, encoding='utf-8-sig')
        
        # 完成部番列で突合
        if '完成部番' in df.columns:
            df['完成部番_str'] = df['完成部番'].astype(str)
            
            # 全ての行がデータ行（ヘッダーなしファイル）
            data_rows = df.copy()
            
            # 指示18の条件: 04_EJ678.csvの「ITEM_CD」または03_マシニング課管理工程.csvの「FINAL_ITEM_CODE」が一致する行を対象外とする
            ej_matched = data_rows['完成部番_str'].isin(ej_data.keys())
            gaichu_matched = data_rows['完成部番_str'].isin(gaichu_codes)
            
            # 指示26の条件: 最大前工程番号がSKD/SUJで始まる行も対象外とする
            skd_suj_matched = []
            zenkou_columns = ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6']
            
            for _, row in data_rows.iterrows():
                rightmost_zenkou = ''
                # 右から左へ（前工程6→前工程1）順番に空欄でない項目を探す
                for col in reversed(zenkou_columns):
                    if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
                        rightmost_zenkou = str(row[col]).strip()
                        break
                
                # 最大前工程番号がSKDまたはSUJで始まるかチェック
                is_skd_suj = rightmost_zenkou.startswith("SKD") or rightmost_zenkou.startswith("SUJ")
                skd_suj_matched.append(is_skd_suj)
            
            # SKD/SUJマスクを作成
            skd_suj_mask = pd.Series(skd_suj_matched, index=data_rows.index)
            
            # 条件: 04_EJ678.csv、03_マシニング課管理工程.csv、またはSKD/SUJいずれかと一致する（対象外）
            matched_mask = ej_matched | gaichu_matched | skd_suj_mask
            
            matched_rows = data_rows[matched_mask]
            unmatched_rows = data_rows[~matched_mask]
            
            print(f"一致した行: {len(matched_rows)}行")
            print(f"  - EJ678一致: {ej_matched.sum()}行")
            print(f"  - マシニング課管理工程一致: {gaichu_matched.sum()}行")
            print(f"  - SKD/SUJ最大前工程: {skd_suj_mask.sum()}行")
            print(f"一致しなかった行: {len(unmatched_rows)}行")
            
            # ヘッダー行を作成（列名を設定、matchedカラムを追加）
            column_names = ['区分コード', '完成部番', '単位数分子1', '単位数分母1', '前工程1', '単位数分子2', '単位数分母2', '前工程2', 
                           '単位数分子3', '単位数分母3', '前工程3', '単位数分子4', '単位数分母4', '前工程4', 
                           '単位数分子5', '単位数分母5', '前工程5', '単位数分子6', '単位数分母6', '前工程6', 'matched']
            
            # 一致したデータ（ヘッダー付き）を出力
            matched_file = os.path.join(output_dir, "07_matched_前工程横展開.csv")
            if len(matched_rows) > 0:
                matched_rows_clean = matched_rows.drop('完成部番_str', axis=1, inplace=False)
                
                # matchedカラムの値を設定
                matched_values = []
                for idx, row in matched_rows_clean.iterrows():
                    item_code = str(row['完成部番']) if pd.notna(row['完成部番']) else ""
                    
                    if item_code in ej_data:
                        # 04_EJ678.csvとマッチした場合：PRODUCT_TYPの値
                        matched_values.append(ej_data[item_code])
                    elif item_code in gaichu_codes:
                        # 03_マシニング課管理工程.csvとマッチした場合："machine"
                        matched_values.append("machine")
                    elif idx in data_rows.index and skd_suj_mask.loc[idx]:
                        # SKD/SUJ最大前工程とマッチした場合："skd_suj"
                        matched_values.append("skd_suj")
                    else:
                        matched_values.append("")
                
                matched_rows_clean['matched'] = matched_values
                matched_rows_clean.columns = column_names
                matched_rows_clean.to_csv(matched_file, encoding='utf-8-sig', index=False, header=True)
                print(f"一致データ出力完了: {matched_file}")
            else:
                # 一致データがない場合でもヘッダーのみのファイルを作成
                empty_df = pd.DataFrame(columns=column_names)
                empty_df.to_csv(matched_file, encoding='utf-8-sig', index=False, header=True)
                print(f"一致データなし（ヘッダーのみ）: {matched_file}")
            
            # 一致しなかったデータ（ヘッダー付き）を出力（matchedカラムなし）
            unmatched_column_names = ['区分コード', '完成部番', '単位数分子1', '単位数分母1', '前工程1', '単位数分子2', '単位数分母2', '前工程2', 
                                     '単位数分子3', '単位数分母3', '前工程3', '単位数分子4', '単位数分母4', '前工程4', 
                                     '単位数分子5', '単位数分母5', '前工程5', '単位数分子6', '単位数分母6', '前工程6']
            unmatched_file = os.path.join(output_dir, "08_unmatched_前工程横展開.csv")
            if len(unmatched_rows) > 0:
                unmatched_rows_clean = unmatched_rows.drop('完成部番_str', axis=1, inplace=False)
                unmatched_rows_clean.columns = unmatched_column_names
                unmatched_rows_clean.to_csv(unmatched_file, encoding='utf-8-sig', index=False, header=True)
                print(f"不一致データ出力完了: {unmatched_file}")
        
        # ステップ1の中間ファイルは削除しない（全て保存）
        # cleanup_file(combined_file)
        
        print("\n=== ステップ2: MA-プレフィックス分離 ===")
        
        # 一致しなかったデータを使用してステップ2以降を実行（指示15対応）
        df = pd.read_csv(unmatched_file, encoding='utf-8-sig')
        # ヘッダー行を除いてデータ行のみを処理
        df = df.iloc[1:].reset_index(drop=True)
        print(f"データサイズ: {df.shape[0]}行 {df.shape[1]}列")
        
        # 前工程列のインデックス（0ベース、区分コード保持のため+1）
        # 前工程1=4, 前工程2=7, 前工程3=10, 前工程4=13, 前工程5=16, 前工程6=19
        zenkou_columns = [4, 7, 10, 13, 16, 19]
        
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
        
        # MA-で始まるデータを出力（ヘッダー付与）
        ma_output_file = os.path.join(output_dir, "09_MA_prefix_data.csv")
        if ma_rows:
            ma_df = pd.concat([row.to_frame().T for row in ma_rows], ignore_index=True)
            column_names_ma = ['区分コード', '完成部番', '単位数分子1', '単位数分母1', '前工程1', '単位数分子2', '単位数分母2', '前工程2', 
                              '単位数分子3', '単位数分母3', '前工程3', '単位数分子4', '単位数分母4', '前工程4', 
                              '単位数分子5', '単位数分母5', '前工程5', '単位数分子6', '単位数分母6', '前工程6']
            ma_df.columns = column_names_ma
            ma_df.to_csv(ma_output_file, encoding='utf-8-sig', index=False, header=True)
            print(f"MA-データ出力完了: {ma_output_file}")
        
        # MA-で始まらないデータを出力（ヘッダー付与）
        non_ma_output_file = os.path.join(output_dir, "10_non_MA_prefix_data.csv")
        if non_ma_rows:
            non_ma_df = pd.concat([row.to_frame().T for row in non_ma_rows], ignore_index=True)
            column_names_non_ma = ['区分コード', '完成部番', '単位数分子1', '単位数分母1', '前工程1', '単位数分子2', '単位数分母2', '前工程2', 
                                  '単位数分子3', '単位数分母3', '前工程3', '単位数分子4', '単位数分母4', '前工程4', 
                                  '単位数分子5', '単位数分母5', '前工程5', '単位数分子6', '単位数分母6', '前工程6']
            non_ma_df.columns = column_names_non_ma
            non_ma_df.to_csv(non_ma_output_file, encoding='utf-8-sig', index=False, header=True)
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
        print(f"  - 08_unmatched_前工程横展開.csv: {os.path.join(output_dir, '08_unmatched_前工程横展開.csv')}")
        print(f"  - 07_matched_前工程横展開.csv: {os.path.join(output_dir, '07_matched_前工程横展開.csv')}")
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
    
    # CSVファイルを読み込み（ヘッダー付き）
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    # 展開後のデータを格納するリスト
    expanded_rows = []
    
    # 各行を処理（全行がデータ行）
    for idx, row in df.iterrows():
            
        completion_code = row['完成部番']  # 完成部番
        
        # 6セットのデータを逆順で処理（No=1が単位数分子6になるように）
        # セット6 → No=1, セット5 → No=2, ..., セット1 → No=6
        for set_num in range(6, 0, -1):  # 6から1へ
            no = 7 - set_num  # No値：6→1, 5→2, 4→3, 3→4, 2→5, 1→6
            
            # 列名を計算
            bunshi_col = f'単位数分子{set_num}'
            bunbo_col = f'単位数分母{set_num}'
            zenkou_col = f'前工程{set_num}'
            
            # 値を取得（列が存在しない場合は空文字）
            bunshi = row[bunshi_col] if bunshi_col in row.index else ""
            bunbo = row[bunbo_col] if bunbo_col in row.index else ""
            zenkou = row[zenkou_col] if zenkou_col in row.index else ""
            
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