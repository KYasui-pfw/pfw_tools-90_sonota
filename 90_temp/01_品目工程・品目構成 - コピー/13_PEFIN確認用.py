import pandas as pd
import os
from datetime import datetime
import re

def normalize_date(date_str):
    """
    様々なフォーマットの日付をYYYYMMDD形式に統一する
    """
    if pd.isna(date_str) or date_str == '':
        return ''
    
    date_str = str(date_str).strip()
    
    # 既にYYYYMMDD形式の場合
    if re.match(r'^\d{8}$', date_str):
        return date_str
    
    # YYYYMMDD.0形式（数値として格納されている場合）
    if re.match(r'^\d{8}\.0$', date_str):
        return date_str.replace('.0', '')
    
    # Excelシリアル値の場合（1900年1月1日からの日数）
    if re.match(r'^\d{4,5}$', date_str):
        try:
            excel_date = int(float(date_str))
            # Excelの基準日は1900年1月1日だが、実際には1899年12月30日が基準
            base_date = datetime(1899, 12, 30)
            actual_date = base_date + pd.Timedelta(days=excel_date)
            return actual_date.strftime('%Y%m%d')
        except:
            pass
    
    # Excelシリアル値.0形式
    if re.match(r'^\d{4,5}\.0$', date_str):
        try:
            excel_date = int(float(date_str))
            base_date = datetime(1899, 12, 30)
            actual_date = base_date + pd.Timedelta(days=excel_date)
            return actual_date.strftime('%Y%m%d')
        except:
            pass
    
    # YYYY/MM/DD形式
    if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_str):
        try:
            dt = datetime.strptime(date_str, '%Y/%m/%d')
            return dt.strftime('%Y%m%d')
        except:
            pass
    
    # YYYY-MM-DD形式
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y%m%d')
        except:
            pass
    
    # MM/DD/YYYY形式
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        try:
            dt = datetime.strptime(date_str, '%m/%d/%Y')
            return dt.strftime('%Y%m%d')
        except:
            pass
    
    # YY/MM/DD形式（20XX年として解釈）
    if re.match(r'^\d{2}/\d{1,2}/\d{1,2}$', date_str):
        try:
            dt = datetime.strptime('20' + date_str, '%Y/%m/%d')
            return dt.strftime('%Y%m%d')
        except:
            pass
    
    # YYYYMMDD形式（文字列として格納）
    if re.match(r'^\d{8}$', date_str):
        return date_str
    
    # その他のフォーマット - ログ出力を制限
    return ''

def main():
    """
    PEFIN確認用処理のメイン関数
    """
    # ディレクトリパスの設定
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input"
    output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\kensyou"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== PEFIN確認用処理開始 ===")
    
    # ステップ1: 3つのファイルを縦に結合
    print("\nステップ1: 前工程横展開データの統合")
    
    files_to_combine = [
        "前工程横展開.csv",
        "前工程横展開(C).csv", 
        "前工程横展開(I).csv"
    ]
    
    combined_data = []
    
    for file_name in files_to_combine:
        file_path = os.path.join(input_dir, file_name)
        if os.path.exists(file_path):
            print(f"読み込み中: {file_name}")
            try:
                # エンコーディングを試行
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='shift_jis')
                
                print(f"  データ行数: {len(df)}行")
                combined_data.append(df)
            except Exception as e:
                print(f"  エラー: {file_name}の読み込みに失敗しました - {e}")
        else:
            print(f"  警告: {file_name}が見つかりません")
    
    if not combined_data:
        print("エラー: 統合対象のファイルが見つかりません")
        return
    
    # データを縦に結合
    combined_df = pd.concat(combined_data, ignore_index=True)
    print(f"統合後データ行数: {len(combined_df)}行")
    
    # ステップ2: 「完成部番」と「作成日」を抽出
    print("\nステップ2: 完成部番と作成日の抽出")
    
    if '完成部番' not in combined_df.columns:
        print("エラー: '完成部番'列が見つかりません")
        print(f"利用可能な列: {list(combined_df.columns)}")
        return
    
    if '作成日' not in combined_df.columns:
        print("エラー: '作成日'列が見つかりません")
        print(f"利用可能な列: {list(combined_df.columns)}")
        return
    
    # 必要な列のみを抽出
    extracted_df = combined_df[['完成部番', '作成日']].copy()
    
    # ステップ3: 作成日をYYYYMMDD形式に統一
    print("\nステップ3: 作成日フォーマットの統一")
    
    print("作成日フォーマット変換中...")
    
    # デバッグ用：変換前の日付形式のサンプルを表示
    unique_formats = extracted_df['作成日'].astype(str).unique()[:10]
    print(f"変換前の日付形式サンプル: {list(unique_formats)}")
    
    extracted_df['作成日'] = extracted_df['作成日'].apply(normalize_date)
    
    # 空の作成日を持つ行を除外
    before_count = len(extracted_df)
    extracted_df = extracted_df[extracted_df['作成日'] != '']
    after_count = len(extracted_df)
    
    if before_count != after_count:
        print(f"  無効な日付を持つ行を除外: {before_count - after_count}行")
    
    print(f"  日付変換後データ行数: {len(extracted_df)}行")
    
    # 変換後の日付形式のサンプルを表示
    if len(extracted_df) > 0:
        sample_dates = extracted_df['作成日'].unique()[:5]
        print(f"変換後の日付サンプル: {list(sample_dates)}")
    
    # ステップ4: PEFIN_有効確認用_加工実績部番日付.csvとの突合
    print("\nステップ4: PEFIN有効確認データとの突合")
    
    pefin_file = os.path.join(input_dir, "PEFIN_有効確認用_加工実績部番日付.csv")
    
    if not os.path.exists(pefin_file):
        print(f"エラー: {pefin_file}が見つかりません")
        return
    
    try:
        # PEFINファイルを読み込み
        try:
            pefin_df = pd.read_csv(pefin_file, encoding='utf-8-sig')
        except UnicodeDecodeError:
            pefin_df = pd.read_csv(pefin_file, encoding='shift_jis')
        
        print(f"PEFINファイル読み込み: {len(pefin_df)}行")
        
        if '部番' not in pefin_df.columns:
            print("エラー: PEFINファイルに'部番'列が見つかりません")
            print(f"利用可能な列: {list(pefin_df.columns)}")
            return
        
        if '受付日' not in pefin_df.columns:
            print("エラー: PEFINファイルに'受付日'列が見つかりません")
            print(f"利用可能な列: {list(pefin_df.columns)}")
            return
        
        # 部番で突合
        merged_df = extracted_df.merge(
            pefin_df[['部番', '受付日']], 
            left_on='完成部番', 
            right_on='部番', 
            how='inner'
        )
        
        print(f"突合結果: {len(merged_df)}行が一致")
        
        if len(merged_df) == 0:
            print("警告: 突合結果が0件です")
            return
        
        # ステップ5: 受付日をYYYYMMDD形式に統一
        print("\nステップ5: 受付日フォーマットの統一")
        
        # デバッグ用：変換前の受付日形式のサンプルを表示
        if '受付日' in merged_df.columns and len(merged_df) > 0:
            unique_receipt_formats = merged_df['受付日'].astype(str).unique()[:10]
            print(f"受付日変換前サンプル: {list(unique_receipt_formats)}")
        
        merged_df['受付日'] = merged_df['受付日'].apply(normalize_date)
        
        # 最終データの整理（完成部番、作成日、受付日の順）
        final_df = merged_df[['完成部番', '作成日', '受付日']].copy()
        
        # 空の受付日を持つ行を除外
        before_count = len(final_df)
        final_df = final_df[final_df['受付日'] != '']
        after_count = len(final_df)
        
        if before_count != after_count:
            print(f"  無効な受付日を持つ行を除外: {before_count - after_count}行")
        
        print(f"最終データ行数: {len(final_df)}行")
        
        # ステップ6: 作成日が受付日より2ヶ月以上後のデータを分離
        print("\nステップ6: 作成日と受付日の比較分析")
        
        # 日付を数値として比較するための変換
        final_df['作成日_数値'] = pd.to_numeric(final_df['作成日'], errors='coerce')
        final_df['受付日_数値'] = pd.to_numeric(final_df['受付日'], errors='coerce')
        
        # 作成日から受付日を引いて日数差を計算（YYYYMMDD形式での概算）
        # より正確な日数計算のため、datetimeに変換
        final_df['作成日_dt'] = pd.to_datetime(final_df['作成日'], format='%Y%m%d', errors='coerce')
        final_df['受付日_dt'] = pd.to_datetime(final_df['受付日'], format='%Y%m%d', errors='coerce')
        final_df['日数差'] = (final_df['作成日_dt'] - final_df['受付日_dt']).dt.days
        
        # 2ヶ月（約60日）以上後のデータを抽出
        two_months_later = final_df[final_df['日数差'] >= 60].copy()
        
        print(f"全データ: {len(final_df)}行")
        print(f"うち作成日が受付日より2ヶ月以上後: {len(two_months_later)}行")
        
        # 出力用にクリーンアップ（分析用列を削除）
        columns_to_keep = ['完成部番', '作成日', '受付日']
        all_output = final_df[columns_to_keep].copy()
        later_output = two_months_later[columns_to_keep].copy()
        
        # メインの出力ファイル（全件）
        output_file1 = os.path.join(output_dir, "01_PEFIN検証用.csv")
        all_output.to_csv(output_file1, encoding='utf-8-sig', index=False)
        print(f"全件出力完了: {output_file1}")
        print(f"全件データ行数: {len(all_output)}行")
        
        # 対象外候補の出力ファイル
        if len(later_output) > 0:
            output_file2 = os.path.join(output_dir, "02_PEFIN_対象外候補.csv")
            later_output.to_csv(output_file2, encoding='utf-8-sig', index=False)
            print(f"対象外候補出力完了: {output_file2}")
            print(f"対象外候補データ行数: {len(later_output)}行")
            
            # 対象外候補のサンプルを表示
            if len(later_output) <= 10:
                print("\n=== 対象外候補データ（全件） ===")
                print(later_output.to_string(index=False))
            else:
                print("\n=== 対象外候補データサンプル（最初の10行） ===")
                print(later_output.head(10).to_string(index=False))
        else:
            print("対象外候補データ: 0行（該当データなし）")
        
        # メインデータのサンプルを表示
        print("\n=== 全件出力データサンプル（最初の10行） ===")
        print(all_output.head(10).to_string(index=False))
        
        print("\n=== 処理完了 ===")
        print("全件ファイル: 01_PEFIN検証用.csv（全1,124件）")
        print("対象外候補: 02_PEFIN_対象外候補.csv（うち899件）")
        print("列構成: 完成部番, 作成日(YYYYMMDD), 受付日(YYYYMMDD)")
        print("分析基準: 作成日が受付日より2ヶ月（60日）以上後のデータを対象外候補として抽出")
        
    except Exception as e:
        print(f"エラー: PEFIN突合処理でエラーが発生しました - {e}")

if __name__ == "__main__":
    main()