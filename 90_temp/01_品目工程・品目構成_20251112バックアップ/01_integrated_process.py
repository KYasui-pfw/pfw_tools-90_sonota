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

        print("\n=== 例外処理: KF22-002プレフィックス前工程2削除 ===")

        # 完成部番が"KF22-002"で始まり、前工程2が"MC-"で始まるデータの前工程2を空欄にする
        kf22_exception_count = 0
        for idx, row in combined_df.iterrows():
            kansei_buban = str(row['完成部番']) if pd.notna(row['完成部番']) else ""
            zenkou2 = str(row['前工程2']) if pd.notna(row['前工程2']) else ""

            if kansei_buban.startswith("KF22-002") and zenkou2.startswith("MC-"):
                # 前工程2を空欄にする
                combined_df.at[idx, '前工程2'] = ""
                combined_df.at[idx, '単位数分子2'] = ""
                combined_df.at[idx, '単位数分母2'] = ""
                kf22_exception_count += 1

        print(f"KF22-002例外処理完了: {kf22_exception_count}行の前工程2を削除")

        print("\n=== 例外処理: 02_購買課_MA変換.csv処理 ===")

        # 02_購買課_MA変換.csvを読み込み
        ma_henkan_file = os.path.join(input_dir, "02_購買課_MA変換.csv")
        ma_henkan_codes = set()

        if os.path.exists(ma_henkan_file):
            print(f"読み込み中: 02_購買課_MA変換.csv")
            try:
                ma_henkan_df = pd.read_csv(ma_henkan_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                ma_henkan_df = pd.read_csv(ma_henkan_file, encoding='shift_jis')

            # カラム名を確認して完成部番を取得（最初のカラムが完成部番と仮定）
            if len(ma_henkan_df.columns) > 0:
                kansei_col = ma_henkan_df.columns[0]  # 最初のカラムを完成部番として使用
                ma_henkan_codes.update(ma_henkan_df[kansei_col].dropna().astype(str))
                print(f"02_購買課_MA変換.csv: {len(ma_henkan_df[kansei_col].dropna())}件の完成部番")
        else:
            print(f"02_購買課_MA変換.csvが見つかりません: {ma_henkan_file}")

        # 02_購買課_MA変換.csvと一致した完成部番の処理
        ma_henkan_count = 0
        zenkou_columns = ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6']
        bunshi_columns = ['単位数分子1', '単位数分子2', '単位数分子3', '単位数分子4', '単位数分子5', '単位数分子6']
        bunbo_columns = ['単位数分母1', '単位数分母2', '単位数分母3', '単位数分母4', '単位数分母5', '単位数分母6']

        for idx, row in combined_df.iterrows():
            kansei_buban = str(row['完成部番']) if pd.notna(row['完成部番']) else ""

            if kansei_buban in ma_henkan_codes:
                # 空欄でない一番右の前工程を見つける
                rightmost_index = -1
                for i in range(5, -1, -1):  # 前工程6から前工程1まで逆順でチェック
                    zenkou_value = str(row[zenkou_columns[i]]) if pd.notna(row[zenkou_columns[i]]) else ""
                    if zenkou_value.strip():  # 空欄でない場合
                        rightmost_index = i
                        break

                if rightmost_index >= 0:
                    # 一番右の前工程をMA-{完成部番}に変更
                    combined_df.at[idx, zenkou_columns[rightmost_index]] = f"MA-{kansei_buban}"
                    # 単位数分子、単位数分母は変更なし（ユーザー確認済み）
                    ma_henkan_count += 1

        print(f"02_購買課_MA変換処理完了: {ma_henkan_count}行の前工程をMA-変換")

        print("\n=== 指示27: 05_EJ_M_ITEM_生技実績突合.csvとの突合処理 ===")
        
        # 05_EJ_M_ITEM_生技実績突合.csvを読み込み
        ej_seigijisseki_file = os.path.join(work_dir, "05_EJ_M_ITEM_生技実績突合.csv")
        
        if os.path.exists(ej_seigijisseki_file):
            print(f"読み込み中: 05_EJ_M_ITEM_生技実績突合.csv")
            try:
                ej_seigijisseki_df = pd.read_csv(ej_seigijisseki_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                ej_seigijisseki_df = pd.read_csv(ej_seigijisseki_file, encoding='shift_jis')
            
            # ITEM_CDのセットを作成
            if 'ITEM_CD' in ej_seigijisseki_df.columns:
                seigijisseki_codes = set(ej_seigijisseki_df['ITEM_CD'].dropna().astype(str))
                print(f"05_EJ_M_ITEM_生技実績突合.csv: {len(seigijisseki_codes)}件のITEM_CD")
                
                # 指示27の処理：完成部番と一致するデータの変換
                matched_count = 0
                for idx, row in combined_df.iterrows():
                    kansei_buban = str(row['完成部番']) if pd.notna(row['完成部番']) else ""
                    
                    if kansei_buban and kansei_buban in seigijisseki_codes:
                        matched_count += 1
                        
                        # 既存データを右にシフト（6→5→4→3→2→1の順で処理）
                        for n in range(6, 1, -1):  # 6から2まで
                            bunshi_col = f'単位数分子{n-1}'
                            bunbo_col = f'単位数分母{n-1}'
                            zenkou_col = f'前工程{n-1}'
                            
                            new_bunshi_col = f'単位数分子{n}'
                            new_bunbo_col = f'単位数分母{n}'
                            new_zenkou_col = f'前工程{n}'
                            
                            # データを右にシフト
                            combined_df.at[idx, new_bunshi_col] = row[bunshi_col]
                            combined_df.at[idx, new_bunbo_col] = row[bunbo_col]
                            combined_df.at[idx, new_zenkou_col] = row[zenkou_col]
                        
                        # 新しい1列目のデータを設定
                        combined_df.at[idx, '単位数分子1'] = 1
                        combined_df.at[idx, '単位数分母1'] = 1
                        combined_df.at[idx, '前工程1'] = f"PEFIN-{kansei_buban}"
                
                print(f"指示27処理完了: {matched_count}行を変換")
            else:
                print("エラー: 05_EJ_M_ITEM_生技実績突合.csvに'ITEM_CD'列が見つかりません")
        else:
            print(f"05_EJ_M_ITEM_生技実績突合.csvが見つかりません: {ej_seigijisseki_file}")
        
        combined_file = os.path.join(output_dir, "06_combined_前工程横展開.csv")
        combined_df.to_csv(combined_file, encoding='utf-8-sig', index=False, header=True)
        print(f"結合ファイル出力完了: {combined_file}")
        
        print("\n=== ステップ1.5: 04_EJ678.csv、03_マシニング課管理工程.csv、01_購買課_対象外.csvとの突合 ===")

        # 04_EJ678.csv、03_マシニング課管理工程.csv、01_購買課_対象外.csv、03_購買課_そのまま.csvを読み込み
        ej_file = os.path.join(work_dir, "04_EJ678.csv")
        gaichu_file = os.path.join(work_dir, "03_マシニング課管理工程.csv")
        koubai_file = os.path.join(input_dir, "01_購買課_対象外.csv")
        koubai_sonomama_file = os.path.join(input_dir, "03_購買課_そのまま.csv")

        ej_data = {}  # ITEM_CD -> PRODUCT_TYP のマッピング
        gaichu_codes = set()
        koubai_codes = set()
        koubai_sonomama_codes = set()
        
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

        # 01_購買課_対象外.csvから完成部番を取得
        if os.path.exists(koubai_file):
            print(f"読み込み中: 01_購買課_対象外.csv")
            try:
                koubai_df = pd.read_csv(koubai_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                # UTF-8で読めない場合はShift_JISを試す
                koubai_df = pd.read_csv(koubai_file, encoding='shift_jis')

            # カラム名を確認して完成部番を取得（最初のカラムが完成部番と仮定）
            if len(koubai_df.columns) > 0:
                kansei_col = koubai_df.columns[0]  # 最初のカラムを完成部番として使用
                koubai_codes.update(koubai_df[kansei_col].dropna().astype(str))
                print(f"01_購買課_対象外.csv: {len(koubai_df[kansei_col].dropna())}件の完成部番")

        # 03_購買課_そのまま.csvから完成部番を取得
        if os.path.exists(koubai_sonomama_file):
            print(f"読み込み中: 03_購買課_そのまま.csv")
            try:
                koubai_sonomama_df = pd.read_csv(koubai_sonomama_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                # UTF-8で読めない場合はShift_JISを試す
                koubai_sonomama_df = pd.read_csv(koubai_sonomama_file, encoding='shift_jis')

            # カラム名を確認して完成部番を取得（最初のカラムが完成部番と仮定）
            if len(koubai_sonomama_df.columns) > 0:
                kansei_col = koubai_sonomama_df.columns[0]  # 最初のカラムを完成部番として使用
                koubai_sonomama_codes.update(koubai_sonomama_df[kansei_col].dropna().astype(str))
                print(f"03_購買課_そのまま.csv: {len(koubai_sonomama_df[kansei_col].dropna())}件の完成部番")

        print(f"EJコード: {len(ej_data)}件")
        print(f"マシニング課管理工程コード: {len(gaichu_codes)}件")
        print(f"購買課対象外コード: {len(koubai_codes)}件")
        print(f"購買課そのままコード: {len(koubai_sonomama_codes)}件")
        
        # ヘッダー付きでDataFrameを再読み込み
        df = pd.read_csv(combined_file, encoding='utf-8-sig')
        
        # 完成部番列で突合
        if '完成部番' in df.columns:
            df['完成部番_str'] = df['完成部番'].astype(str)
            
            # 全ての行がデータ行（ヘッダーなしファイル）
            data_rows = df.copy()
            
            # 指示18の条件: 04_EJ678.csvの「ITEM_CD」または03_マシニング課管理工程.csvの「FINAL_ITEM_CODE」が一致する行を対象外とする
            # 追加: 01_購買課_対象外.csvの完成部番と一致する行も対象外とする
            ej_matched = data_rows['完成部番_str'].isin(ej_data.keys())
            gaichu_matched = data_rows['完成部番_str'].isin(gaichu_codes)
            koubai_matched = data_rows['完成部番_str'].isin(koubai_codes)
            
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
            
            # 指示28の条件: 完成部番が"TS-"で始まるデータは例外的に全て07_matched_前工程横展開.csvに振り分ける
            ts_prefix_mask = data_rows['完成部番_str'].str.startswith('TS-', na=False)

            # 追加除外リスト: 特定の完成部番13項目を除外対象に追加
            exclude_list = [
                'SK5-4.0X40X97', 'SK5-6.0X40X97', 'K-22210', 'K-29610AA',
                'SK5-3.5X40X97', 'SK5-4.5X40X97', 'SK5-5.0X40X97', 'SK5-4.0X75X330',
                'SK5-T6XH40XL97-CUT-ONLY', 'SK5-3.2X40X97', 'SK5-3.0X40X300',
                'SK5-T4XH40XL97-CUT-ONLY', 'SK5-T4XH40XL65-CUT-ONLY'
            ]
            exclude_specific_mask = data_rows['完成部番_str'].isin(exclude_list)
            
            # 条件: 04_EJ678.csv、03_マシニング課管理工程.csv、01_購買課_対象外.csv、SKD/SUJ、TS-プレフィックス、または特定除外リストいずれかと一致する（対象外）
            matched_mask = ej_matched | gaichu_matched | koubai_matched | skd_suj_mask | ts_prefix_mask | exclude_specific_mask
            
            matched_rows = data_rows[matched_mask]
            unmatched_rows = data_rows[~matched_mask]
            
            print(f"一致した行: {len(matched_rows)}行")
            print(f"  - EJ678一致: {ej_matched.sum()}行")
            print(f"  - マシニング課管理工程一致: {gaichu_matched.sum()}行")
            print(f"  - 購買課対象外一致: {koubai_matched.sum()}行")
            print(f"  - SKD/SUJ最大前工程: {skd_suj_mask.sum()}行")
            print(f"  - TS-プレフィックス: {ts_prefix_mask.sum()}行")
            print(f"  - 特定除外リスト一致: {exclude_specific_mask.sum()}行")
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
                    elif item_code in koubai_codes:
                        # 01_購買課_対象外.csvとマッチした場合："koubai_excluded"
                        matched_values.append("koubai_excluded")
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
                # 指示28の条件: 前工程1が"AO-"で始まり、前工程2が空欄のものは例外的に09_MA_prefix_data.csvに振り分ける
                zenkou1 = str(row.iloc[4]).strip() if 4 < len(row) and pd.notna(row.iloc[4]) else ""
                zenkou2 = str(row.iloc[7]).strip() if 7 < len(row) and pd.notna(row.iloc[7]) else ""
                zenkou3 = str(row.iloc[10]).strip() if 10 < len(row) and pd.notna(row.iloc[10]) else ""
                
                ao_exception = (zenkou1.startswith("AO-") and (zenkou2 == "" or zenkou2 == "nan"))
                
                # 指示30の例外処理: 特定の4つの完成部番は強制的に10_non_MA_prefix_data.csvに振り分ける
                kansei_buban = str(row.iloc[1]).strip() if 1 < len(row) and pd.notna(row.iloc[1]) else ""
                force_non_ma_items = {"K-18405B", "KS64-00504DA", "KS64-02404EA", "SPL-2721AA"}
                force_non_ma = kansei_buban in force_non_ma_items
                
                # 指示29の条件: 前工程1が"PEFIN-"で始まり、前工程2が空欄ではなく、前工程3が空欄のものは例外的に09_MA_prefix_data.csvに振り分ける
                pefin_exception = (zenkou1.startswith("PEFIN-") and
                                 zenkou2 != "" and zenkou2 != "nan" and pd.notna(row.iloc[7]) and
                                 (zenkou3 == "" or zenkou3 == "nan")) and not force_non_ma  # 指示30が優先

                # 03_購買課_そのまま.csv例外処理: 指定された完成部番は強制的に09_MA_prefix_data.csvに振り分ける
                koubai_sonomama_exception = kansei_buban in koubai_sonomama_codes and not force_non_ma  # 指示30が優先

                if force_non_ma:
                    non_ma_rows.append(row)
                elif rightmost_zenkou.startswith("MA-") or ao_exception or pefin_exception or koubai_sonomama_exception:
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
    
    # 03_購買課_そのまま.csvを読み込み
    # output_dir = "work" なので、親ディレクトリの "input" を取得
    parent_dir = os.path.dirname(output_dir)  # 01_品目工程・品目構成ディレクトリ
    input_dir = os.path.join(parent_dir, "input")
    koubai_sonomama_file = os.path.join(input_dir, "03_購買課_そのまま.csv")
    koubai_sonomama_codes = set()

    if os.path.exists(koubai_sonomama_file):
        try:
            koubai_sonomama_df = pd.read_csv(koubai_sonomama_file, encoding='utf-8-sig')
        except UnicodeDecodeError:
            koubai_sonomama_df = pd.read_csv(koubai_sonomama_file, encoding='shift_jis')

        if len(koubai_sonomama_df.columns) > 0:
            kansei_col = koubai_sonomama_df.columns[0]
            koubai_sonomama_codes.update(koubai_sonomama_df[kansei_col].dropna().astype(str))

    # 指示29の条件: 同じ完成部番でNo6が"PEFIN-"で始まり、No5が空欄ではなく、No4が空欄の条件を満たすデータについて、No5を品目構成に振り分け
    pefin_kousei_rows = []
    pefin_condition_items = set()

    # 03_購買課_そのまま.csv条件: 完成部番が一致する行で、空欄を除いた行のうち最も番号が小さい行
    koubai_sonomama_kousei_rows = []
    koubai_sonomama_condition_items = set()
    
    # PEFIN-条件と03_購買課_そのまま.csv条件を特定
    for completion_code, group in non_empty_df.groupby('完成部番'):
        group_sorted = group.sort_values('No')

        # PEFIN-条件をチェック
        # No6(最後の工程)がPEFIN-で始まるかチェック
        no6_rows = group_sorted[group_sorted['No'] == 6]
        if len(no6_rows) > 0:
            no6_zenkou = str(no6_rows.iloc[0]['前工程']).strip()
            if no6_zenkou.startswith("PEFIN-"):
                # No5が空欄ではなく、No4が空欄かチェック
                no5_rows = group_sorted[group_sorted['No'] == 5]
                no4_rows = group_sorted[group_sorted['No'] == 4]

                has_no5 = len(no5_rows) > 0 and str(no5_rows.iloc[0]['前工程']).strip() not in ["", "nan"]
                has_no4 = len(no4_rows) > 0 and str(no4_rows.iloc[0]['前工程']).strip() not in ["", "nan"]

                if has_no5 and not has_no4:
                    # 条件を満たす：No5を品目構成に振り分け
                    pefin_condition_items.add(completion_code)
                    pefin_kousei_rows.extend(no5_rows.index.tolist())

        # 03_購買課_そのまま.csv条件をチェック
        if completion_code in koubai_sonomama_codes:
            # 空欄を除いた行のうち最も番号が小さい行を取得
            non_empty_group = group_sorted[group_sorted['前工程'].notna() & (group_sorted['前工程'].astype(str).str.strip() != "")]
            if len(non_empty_group) > 0:
                smallest_no_row = non_empty_group.iloc[0]  # group_sortedなので最初の行が最小番号
                koubai_sonomama_condition_items.add(completion_code)
                koubai_sonomama_kousei_rows.append(smallest_no_row.name)
    
    # MA-で始まる行 + PEFIN条件でNo5の行 + 03_購買課_そのまま.csv条件
    ma_condition = non_empty_df['前工程'].astype(str).str.startswith("MA-")
    pefin_no5_condition = non_empty_df.index.isin(pefin_kousei_rows)
    koubai_sonomama_condition = non_empty_df.index.isin(koubai_sonomama_kousei_rows)

    ma_rows = non_empty_df[ma_condition | pefin_no5_condition | koubai_sonomama_condition]
    non_ma_rows = non_empty_df[~(ma_condition | pefin_no5_condition | koubai_sonomama_condition)]
    
    if len(pefin_condition_items) > 0:
        print(f"指示29条件適用: {len(pefin_condition_items)}件の完成部番でNo5を品目構成に移動")

    if len(koubai_sonomama_condition_items) > 0:
        print(f"03_購買課_そのまま.csv条件適用: {len(koubai_sonomama_condition_items)}件の完成部番で最小番号行を品目構成に移動")

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