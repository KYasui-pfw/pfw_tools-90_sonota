import pandas as pd
import os

def check_output_result():
    """指示33の処理結果を詳細確認"""

    # ファイルパス
    output_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\output\M0840_品目工程マスタ.csv"
    pefin_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input\PEFINソート.csv"

    try:
        # 品目工程マスタを読み込み
        master_df = pd.read_csv(output_file, encoding='utf-8-sig')
        print(f"品目工程マスタ読み込み: {len(master_df)}行")

        # PEFINソート.csvを読み込み
        for encoding in ['utf-8', 'shift_jis', 'cp932']:
            try:
                pefin_df = pd.read_csv(pefin_file, encoding=encoding)
                print(f"PEFINソート.csv読み込み成功 (エンコーディング: {encoding})")
                break
            except UnicodeDecodeError:
                continue

        if len(pefin_df.columns) >= 2:
            kansei_col = pefin_df.columns[0]  # 完成部番
            zenkatei_col = pefin_df.columns[1]  # 前工程

            print(f"\n=== 指示33処理結果詳細確認 ===")

            # 各処理パターンを確認
            for _, pefin_row in pefin_df.iterrows():
                kansei_bango = str(pefin_row[kansei_col]) if pd.notna(pefin_row[kansei_col]) else ''
                zenkatei_value = pefin_row[zenkatei_col] if pd.notna(pefin_row[zenkatei_col]) else 0

                # 該当するHMCDの行を取得
                hmcd_data = master_df[master_df['HMCD'] == kansei_bango]

                if len(hmcd_data) == 0:
                    continue

                print(f"\n--- {kansei_bango} (前工程={zenkatei_value}) ---")

                # SEQ順にソートして表示
                hmcd_sorted = hmcd_data.sort_values('SEQ')
                for _, row in hmcd_sorted.iterrows():
                    print(f"  SEQ={row['SEQ']}, KTSEQ={row['KTSEQ']}, KTCD={row['KTCD']}")

                # 期待値との比較
                if zenkatei_value == 0:
                    # PEFIN行が削除されているか確認
                    pefin_count = len(hmcd_data[hmcd_data['KTCD'] == 'PEFIN'])
                    print(f"  期待: PEFIN行削除, 実際: PEFIN行数={pefin_count} {'OK' if pefin_count == 0 else 'NG'}")

                elif zenkatei_value == 1:
                    # 何も変更されていないことを確認（ここでは基本的な連番チェック）
                    seq_values = sorted(hmcd_data['SEQ'].tolist())
                    expected_seq = list(range(1, len(hmcd_data) + 1))
                    print(f"  期待: 編集なし, 実際: SEQ={seq_values} {'OK' if seq_values == expected_seq else 'NG'}")

                elif zenkatei_value == 2:
                    # SEQ 1↔2が入れ替わっているか確認
                    if len(hmcd_data) >= 2:
                        seq1_row = hmcd_data[hmcd_data['SEQ'] == 1]
                        seq2_row = hmcd_data[hmcd_data['SEQ'] == 2]
                        if len(seq1_row) > 0 and len(seq2_row) > 0:
                            seq1_ktseq = seq1_row.iloc[0]['KTSEQ']
                            seq2_ktseq = seq2_row.iloc[0]['KTSEQ']
                            print(f"  期待: SEQ1<->2入れ替え, 実際: SEQ1のKTSEQ={seq1_ktseq}, SEQ2のKTSEQ={seq2_ktseq}")
                            print(f"  {'OK' if seq1_ktseq == 10 and seq2_ktseq == 20 else 'NG'}")

                elif zenkatei_value == 3:
                    # SEQ順繰り入れ替えを確認
                    if len(hmcd_data) >= 3:
                        seq_values = sorted(hmcd_data['SEQ'].tolist())
                        ktseq_mapping = {}
                        for _, row in hmcd_data.iterrows():
                            ktseq_mapping[row['SEQ']] = row['KTSEQ']
                        print(f"  期待: 順繰り入れ替え, 実際: SEQ-KTSEQ mapping: {ktseq_mapping}")
                        expected_mapping = {1: 10, 2: 20, 3: 30}
                        check_ok = all(ktseq_mapping.get(seq) == expected_mapping.get(seq) for seq in [1, 2, 3] if seq in ktseq_mapping)
                        print(f"  {'OK' if check_ok else 'NG'}")

            # 特定のサンプルケースを詳細表示
            print(f"\n=== 主要サンプルケース詳細 ===")

            sample_cases = [
                "KF43-00101AA",  # 前工程=0
                "00-1160AA",     # 前工程=1
                "2172-205AA",    # 前工程=2
                "KA65-00101AA"   # 前工程=3
            ]

            for case in sample_cases:
                case_data = master_df[master_df['HMCD'] == case].sort_values('SEQ')
                if len(case_data) > 0:
                    print(f"\n{case}:")
                    print(case_data[['HMCD', 'SEQ', 'KTSEQ', 'KTCD']].to_string(index=False))
                else:
                    print(f"\n{case}: データなし")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_output_result()