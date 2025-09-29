import pandas as pd
import os

def main():
    """
    前工程横展開CSVファイル3つを縦結合する
    - 前工程横展開.csv
    - 前工程横展開(I).csv
    - 前工程横展開(C).csv
    """
    # ディレクトリパス設定
    input_dir = r"C:\Dev\90_tools\90_temp\03_小数点調査\input"
    output_dir = r"C:\Dev\90_tools\90_temp\03_小数点調査"

    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)

    print("=== 前工程横展開CSVファイル縦結合処理 ===")

    # 読み込むファイルのリスト（順序重要）
    files_to_combine = [
        "前工程横展開.csv",
        "前工程横展開(I).csv",
        "前工程横展開(C).csv"
    ]

    # まず全ファイルを読み込んで最大列数を確認
    print("=== ファイル列数確認 ===")
    file_info = []
    max_columns = 0

    for filename in files_to_combine:
        file_path = os.path.join(input_dir, filename)
        if not os.path.exists(file_path):
            print(f"エラー: ファイルが見つかりません - {file_path}")
            return

        # ヘッダー行を読み込んで列数確認
        temp_df = pd.read_csv(file_path, encoding='shift_jis', nrows=0)
        col_count = len(temp_df.columns)
        file_info.append((filename, file_path, col_count))
        max_columns = max(max_columns, col_count)
        print(f"{filename}: {col_count}列")

    print(f"最大列数: {max_columns}列")

    # 全ファイルを最大列数に合わせて読み込み
    combined_data = []

    for i, (filename, file_path, col_count) in enumerate(file_info):
        print(f"\n読み込み中: {filename}")

        if i == 0:
            # 最初のファイル: ヘッダー付きで読み込み
            df = pd.read_csv(file_path, encoding='shift_jis')
            base_columns = df.columns.tolist()

            # 列数が足りない場合は空列を追加
            while len(df.columns) < max_columns:
                new_col_name = f"追加列_{len(df.columns) + 1}"
                df[new_col_name] = ''
                base_columns.append(new_col_name)

            print(f"  {filename}: {len(df)}行 {len(df.columns)}列 (ヘッダー含む)")
        else:
            # 2番目以降: ヘッダーをスキップして読み込み
            df = pd.read_csv(file_path, encoding='shift_jis', skiprows=1, header=None)

            # 列数を最大列数に合わせる
            while len(df.columns) < max_columns:
                df[len(df.columns)] = ''

            # 列名を最初のファイルに合わせる
            df.columns = base_columns
            print(f"  {filename}: {len(df)}行 {len(df.columns)}列 (ヘッダー除く)")

        combined_data.append(df)

    # 縦結合実行
    print("\n=== 縦結合実行 ===")
    result_df = pd.concat(combined_data, ignore_index=True)

    print(f"結合結果: {len(result_df)}行 {len(result_df.columns)}列")

    # 出力ファイル保存
    output_file = os.path.join(output_dir, "前工程横展開_縦結合.csv")
    result_df.to_csv(output_file, encoding='shift_jis', index=False)

    print(f"出力完了: {output_file}")
    print(f"出力データ: {len(result_df)}行")

    # 各ファイルの行数確認
    print("\n=== ファイル別行数確認 ===")
    start_idx = 0
    for i, filename in enumerate(files_to_combine):
        end_idx = start_idx + len(combined_data[i])
        print(f"{filename}: {len(combined_data[i])}行 (結合後行番号: {start_idx+1}～{end_idx})")
        start_idx = end_idx

    # 結合結果のサンプル表示
    print("\n=== 結合結果サンプル（最初の3行） ===")
    print(result_df.head(3).to_string(max_cols=10))

if __name__ == "__main__":
    main()