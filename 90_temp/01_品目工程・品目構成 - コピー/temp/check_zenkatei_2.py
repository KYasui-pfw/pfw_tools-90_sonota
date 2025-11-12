import pandas as pd

def check_zenkatei_2():
    """PEFINソートの前工程=2の行と品目工程マスタの対応を確認"""

    # ファイルパス
    pefin_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input\PEFINソート.csv"
    master_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\output\M0840_品目工程マスタ.csv"

    try:
        # PEFINソート.csvを読み込み
        for encoding in ['utf-8', 'shift_jis', 'cp932']:
            try:
                pefin_df = pd.read_csv(pefin_file, encoding=encoding)
                print(f"PEFINソート.csv読み込み成功 (エンコーディング: {encoding})")
                break
            except UnicodeDecodeError:
                continue

        # 品目工程マスタを読み込み
        master_df = pd.read_csv(master_file, encoding='utf-8-sig')
        print(f"品目工程マスタ読み込み成功: {len(master_df)}行")

        # カラム名を取得
        kansei_col = pefin_df.columns[0]  # 完成部番
        zenkatei_col = pefin_df.columns[1]  # 前工程

        print(f"\nPEFINソート.csvのカラム: {kansei_col}, {zenkatei_col}")

        # 前工程=2の行を抽出
        zenkatei_2_rows = pefin_df[pefin_df[zenkatei_col] == 2]
        print(f"\n前工程=2の行数: {len(zenkatei_2_rows)}行")

        if len(zenkatei_2_rows) > 0:
            print("\n前工程=2の完成部番一覧（最初の10件）:")
            for i, (idx, row) in enumerate(zenkatei_2_rows.iterrows()):
                if i < 10:  # 最初の10件のみ表示
                    kansei_bango = str(row[kansei_col]) if pd.notna(row[kansei_col]) else ''
                    print(f"  {kansei_bango}")
                elif i == 10:
                    print(f"  ... 他 {len(zenkatei_2_rows) - 10} 件")
                    break

            # 各完成部番について品目工程マスタでの行数を確認
            print(f"\n=== 品目工程マスタでの対応確認 ===")
            total_matching_rows = 0
            existing_count = 0
            pefin_seq_list = []

            for idx, row in zenkatei_2_rows.iterrows():
                kansei_bango = str(row[kansei_col]) if pd.notna(row[kansei_col]) else ''

                # 該当するHMCDの行を取得
                matching_rows = master_df[master_df['HMCD'] == kansei_bango]
                row_count = len(matching_rows)
                total_matching_rows += row_count

                if row_count > 0:
                    existing_count += 1

                    # PEFIN行のSEQを確認
                    pefin_rows = matching_rows[matching_rows['KTCD'] == 'PEFIN']
                    if len(pefin_rows) > 0:
                        for _, pefin_row in pefin_rows.iterrows():
                            pefin_seq_list.append({
                                'HMCD': kansei_bango,
                                'SEQ': pefin_row['SEQ'],
                                'KTSEQ': pefin_row['KTSEQ'],
                                'total_rows': row_count
                            })

            print(f"前工程=2の完成部番数: {len(zenkatei_2_rows)}件")
            print(f"品目工程マスタに存在する完成部番数: {existing_count}件")
            print(f"品目工程マスタでの総該当行数: {total_matching_rows}行")

            # PEFIN行の詳細分析
            if pefin_seq_list:
                print(f"\n=== PEFIN行のSEQ分析 ===")
                print(f"PEFIN行を持つ完成部番数: {len(pefin_seq_list)}件")

                # SEQ値の分布を確認
                seq_counts = {}
                for item in pefin_seq_list:
                    seq_val = item['SEQ']
                    if seq_val not in seq_counts:
                        seq_counts[seq_val] = 0
                    seq_counts[seq_val] += 1

                print(f"\nPEFIN行のSEQ値分布:")
                for seq_val in sorted(seq_counts.keys()):
                    print(f"  SEQ={seq_val}: {seq_counts[seq_val]}件")

                # 代表例を表示
                print(f"\n代表例（最初の5件）:")
                for i, item in enumerate(pefin_seq_list[:5]):
                    print(f"  {item['HMCD']}: PEFIN行のSEQ={item['SEQ']} (全{item['total_rows']}行中)")

                # 詳細な内容確認（最初の3件）
                print(f"\n詳細内容確認（最初の3件）:")
                for i, item in enumerate(pefin_seq_list[:3]):
                    hmcd = item['HMCD']
                    matching_rows = master_df[master_df['HMCD'] == hmcd].sort_values('SEQ')
                    print(f"\n{hmcd}:")
                    for _, row in matching_rows.iterrows():
                        marker = "★" if row['KTCD'] == 'PEFIN' else "  "
                        print(f"  {marker}SEQ={row['SEQ']}, KTSEQ={row['KTSEQ']}, KTCD={row['KTCD']}")

            else:
                print(f"\nPEFIN行を持つ完成部番はありませんでした")

        else:
            print("前工程=2の行が見つかりませんでした")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_zenkatei_2()