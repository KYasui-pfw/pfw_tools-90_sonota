import pandas as pd

def check_specific_cases():
    """指示33の具体的なケースを詳しく確認"""

    # 修正前後の比較用に先ほど作った比較ファイルを確認
    output_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\output\M0840_品目工程マスタ.csv"

    try:
        master_df = pd.read_csv(output_file, encoding='utf-8-sig')

        # 具体的なケースを確認
        test_cases = [
            ("2172-205AA", 2),  # 前工程=2: SEQ1↔2入れ替え期待
            ("KA65-00101AA", 3)  # 前工程=3: 順繰り入れ替え期待
        ]

        for hmcd, expected_zenkatei in test_cases:
            print(f"\n=== {hmcd} (前工程={expected_zenkatei}) ===")

            hmcd_data = master_df[master_df['HMCD'] == hmcd].sort_values('SEQ')
            if len(hmcd_data) == 0:
                print("データなし")
                continue

            # 現在の状態を表示
            print("現在の状態:")
            for _, row in hmcd_data.iterrows():
                print(f"  SEQ={row['SEQ']}, KTSEQ={row['KTSEQ']}, KTCD={row['KTCD']}")

            if expected_zenkatei == 2:
                print("\n期待される結果（前工程=2の場合）:")
                print("  元のSEQ=1の内容がSEQ=2の位置に")
                print("  元のSEQ=2の内容がSEQ=1の位置に")
                print("  つまり、SEQ1とSEQ2のKTCDが入れ替わっているはず")

                if len(hmcd_data) >= 2:
                    seq1_ktcd = hmcd_data[hmcd_data['SEQ'] == 1]['KTCD'].iloc[0]
                    seq2_ktcd = hmcd_data[hmcd_data['SEQ'] == 2]['KTCD'].iloc[0]
                    print(f"\n実際: SEQ1={seq1_ktcd}, SEQ2={seq2_ktcd}")

                    # 元々のデータでは何だったか推測（これは推測なので参考程度）
                    print("推測: 元々はSEQ1=PA, SEQ2=MCだったが、入れ替えでSEQ1=MC, SEQ2=PAになるべき")

            elif expected_zenkatei == 3:
                print("\n期待される結果（前工程=3の場合）:")
                print("  2→1: 元のSEQ=2の内容がSEQ=1の位置に")
                print("  3→2: 元のSEQ=3の内容がSEQ=2の位置に")
                print("  1→3: 元のSEQ=1の内容がSEQ=3の位置に")

                if len(hmcd_data) >= 3:
                    seq1_ktcd = hmcd_data[hmcd_data['SEQ'] == 1]['KTCD'].iloc[0]
                    seq2_ktcd = hmcd_data[hmcd_data['SEQ'] == 2]['KTCD'].iloc[0]
                    seq3_ktcd = hmcd_data[hmcd_data['SEQ'] == 3]['KTCD'].iloc[0]
                    print(f"\n実際: SEQ1={seq1_ktcd}, SEQ2={seq2_ktcd}, SEQ3={seq3_ktcd}")

                    # 期待される順序
                    print("期待: 元々のSEQ順序が変更されているはず")

        # 別のアプローチ：PEFINソートcsv確認
        print(f"\n=== PEFINソート.csvの該当行確認 ===")
        pefin_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input\PEFINソート.csv"

        for encoding in ['utf-8', 'shift_jis', 'cp932']:
            try:
                pefin_df = pd.read_csv(pefin_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        for hmcd, _ in test_cases:
            kansei_col = pefin_df.columns[0]
            zenkatei_col = pefin_df.columns[1]

            pefin_row = pefin_df[pefin_df[kansei_col] == hmcd]
            if len(pefin_row) > 0:
                zenkatei_value = pefin_row[zenkatei_col].iloc[0]
                print(f"{hmcd}: PEFINソート.csvでの前工程値 = {zenkatei_value}")
            else:
                print(f"{hmcd}: PEFINソート.csvに該当なし")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_specific_cases()