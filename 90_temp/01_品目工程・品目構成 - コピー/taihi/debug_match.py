import pandas as pd
import os

def debug_match():
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input"
    
    # CAFIN.csvを読み込み
    cafin_file = os.path.join(input_dir, "CAFIN.csv")
    try:
        cafin_df = pd.read_csv(cafin_file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        cafin_df = pd.read_csv(cafin_file, encoding='shift_jis')
    
    print("=== CAFIN.csv ===")
    print(f"列名: {list(cafin_df.columns)}")
    print(f"品目コード列の存在: {'品目コード' in cafin_df.columns}")
    if '品目コード' in cafin_df.columns:
        cafin_codes = cafin_df['品目コード'].dropna().astype(str)
        print(f"品目コード数: {len(cafin_codes)}")
        print("最初の10件:")
        for i, code in enumerate(cafin_codes.head(10)):
            print(f"  {i+1}: '{code}' (len={len(code)}, repr={repr(code)})")
    
    # 前工程横展開(C).csvを読み込み
    zenkoutei_c_file = os.path.join(input_dir, "前工程横展開(C).csv")
    try:
        zenkoutei_c_df = pd.read_csv(zenkoutei_c_file, encoding='shift_jis', header=None)
    except UnicodeDecodeError:
        zenkoutei_c_df = pd.read_csv(zenkoutei_c_file, encoding='utf-8', header=None)
    
    print(f"\n=== 前工程横展開(C).csv ===")
    print(f"行数: {len(zenkoutei_c_df)}, 列数: {len(zenkoutei_c_df.columns)}")
    
    # 完成部番（1列目）のサンプルを確認
    completion_codes = zenkoutei_c_df.iloc[1:11, 0].dropna().astype(str)  # ヘッダー除く10件
    print("完成部番の最初の10件:")
    for i, code in enumerate(completion_codes):
        print(f"  {i+2}: '{code}' (len={len(code)}, repr={repr(code)})")
    
    # 特定の値での突合テスト
    if '品目コード' in cafin_df.columns:
        cafin_codes_set = set(cafin_df['品目コード'].dropna().astype(str))
        
        print(f"\n=== 突合テスト ===")
        test_codes = ["00-1041G32", "00-1041E26", "105-420AB48"]
        for test_code in test_codes:
            in_cafin = test_code in cafin_codes_set
            print(f"'{test_code}' がCAFIN.csvにある: {in_cafin}")
        
        # 実際の完成部番での突合テスト
        print(f"\n=== 実際の完成部番での突合 ===")
        all_completion_codes = zenkoutei_c_df.iloc[1:, 0].dropna().astype(str)
        matched_count = 0
        sample_matches = []
        
        for code in all_completion_codes:
            if code in cafin_codes_set:
                matched_count += 1
                if len(sample_matches) < 10:
                    sample_matches.append(code)
        
        print(f"実際の一致件数: {matched_count}")
        print(f"一致したコードのサンプル:")
        for match in sample_matches:
            print(f"  '{match}'")

if __name__ == "__main__":
    debug_match()