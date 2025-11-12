import pandas as pd

def check_zenkatei_0():
    """PEFINソートの前工程=0の行と品目工程マスタの対応を確認"""

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

        # 前工程=0の行を抽出
        zenkatei_0_rows = pefin_df[pefin_df[zenkatei_col] == 0]
        print(f"\n前工程=0の行数: {len(zenkatei_0_rows)}行")

        if len(zenkatei_0_rows) > 0:
            print("\n前工程=0の完成部番一覧:")
            for idx, row in zenkatei_0_rows.iterrows():
                kansei_bango = str(row[kansei_col]) if pd.notna(row[kansei_col]) else ''
                print(f"  {kansei_bango}")

            # 各完成部番について品目工程マスタでの行数を確認
            print(f"\n=== 品目工程マスタでの対応確認 ===")
            total_matching_rows = 0

            for idx, row in zenkatei_0_rows.iterrows():
                kansei_bango = str(row[kansei_col]) if pd.notna(row[kansei_col]) else ''

                # 該当するHMCDの行を取得
                matching_rows = master_df[master_df['HMCD'] == kansei_bango]
                row_count = len(matching_rows)
                total_matching_rows += row_count

                print(f"{kansei_bango}: {row_count}行")

                if row_count > 0:
                    # 詳細表示
                    print("  詳細:")
                    for _, master_row in matching_rows.iterrows():
                        print(f"    SEQ={master_row['SEQ']}, KTSEQ={master_row['KTSEQ']}, KTCD={master_row['KTCD']}")

                    # PEFIN行があるかチェック
                    pefin_rows = matching_rows[matching_rows['KTCD'] == 'PEFIN']
                    print(f"    PEFIN行数: {len(pefin_rows)}行")

            print(f"\n=== 集計結果 ===")
            print(f"前工程=0の完成部番数: {len(zenkatei_0_rows)}件")
            print(f"品目工程マスタでの総該当行数: {total_matching_rows}行")

            # 前工程=0以外の参考データ
            print(f"\n=== 参考: 他の前工程値の分布 ===")
            zenkatei_counts = pefin_df[zenkatei_col].value_counts().sort_index()
            for zenkatei_val, count in zenkatei_counts.items():
                print(f"前工程={zenkatei_val}: {count}件")

        else:
            print("前工程=0の行が見つかりませんでした")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_zenkatei_0()