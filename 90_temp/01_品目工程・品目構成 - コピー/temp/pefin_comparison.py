import pandas as pd
import os

def main():
    # ファイルパスの定義
    base_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成"
    pefin_file = os.path.join(base_dir, "input", "PEFINソート.csv")
    master_file = os.path.join(base_dir, "output", "M0840_品目工程マスタ.csv")
    output_file = os.path.join(base_dir, "temp", "PEFIN一致_品目工程マスタ.csv")

    try:
        # PEFINソート.csvを読み込み（文字エンコーディングの問題を考慮）
        print("PEFINソート.csvを読み込み中...")
        try:
            pefin_df = pd.read_csv(pefin_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                pefin_df = pd.read_csv(pefin_file, encoding='shift_jis')
            except UnicodeDecodeError:
                pefin_df = pd.read_csv(pefin_file, encoding='cp932')

        # 品目工程マスタを読み込み
        print("品目工程マスタを読み込み中...")
        try:
            master_df = pd.read_csv(master_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                master_df = pd.read_csv(master_file, encoding='shift_jis')
            except UnicodeDecodeError:
                master_df = pd.read_csv(master_file, encoding='cp932')

        # カラム名を確認・修正
        print("PEFINソート.csvのカラム:")
        print(pefin_df.columns.tolist())
        print("\n品目工程マスタのカラム:")
        print(master_df.columns.tolist())

        # PEFINソート.csvの最初のカラムを完成部番として扱う
        pefin_column = pefin_df.columns[0]
        pefin_items = pefin_df[pefin_column].dropna().unique()

        print(f"\nPEFINソート.csvの完成部番数: {len(pefin_items)}")
        print(f"品目工程マスタの総行数: {len(master_df)}")

        # HMCDと完成部番を比較して一致する行を抽出
        matched_df = master_df[master_df['HMCD'].isin(pefin_items)]

        print(f"一致した行数: {len(matched_df)}")

        # 結果を出力
        matched_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n結果を出力しました: {output_file}")

        # 統計情報を表示
        print("\n=== 統計情報 ===")
        print(f"PEFIN対象完成部番数: {len(pefin_items)}")
        print(f"品目工程マスタ一致行数: {len(matched_df)}")
        print(f"一致した完成部番数: {matched_df['HMCD'].nunique()}")

        # 一致した完成部番の一覧（最初の10件）
        matched_items = matched_df['HMCD'].unique()
        print(f"\n一致した完成部番（最初の10件）:")
        for i, item in enumerate(matched_items[:10]):
            print(f"  {i+1}. {item}")

        if len(matched_items) > 10:
            print(f"  ... 他 {len(matched_items) - 10} 件")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()