"""
CSV差分比較スクリプト
3つのマスタファイルペアを比較し、差分結果を出力する
"""

import pandas as pd
import os
import sys
from datetime import datetime

# コンソール出力をUTF-8に設定
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 比較対象ファイルの定義
FILE_PAIRS = {
    'M0840': {
        'old': 'M0840_品目工程マスタ.csv',
        'new': 'M0840_品目工程マスタ_1112最終.csv',
        'output': 'M0840_差分比較結果.csv',
        'key_columns': ['HMCD', 'SEQ', 'KTSEQ']  # 主キー列
    },
    'M0850': {
        'old': 'M0850_品目構成マスタ.csv',
        'new': 'M0850_品目構成マスタ_1112最終.csv',
        'output': 'M0850_差分比較結果.csv',
        'key_columns': ['OYAHMCD', 'SEQ', 'STRNO', 'OYAREVNO', 'STRSEQ']  # 主キー列
    },
    'MK020': {
        'old': 'MK020_品目仕入工程単価マスタ.csv',
        'new': 'MK020_品目仕入工程単価マスタ_1112最終.csv',
        'output': 'MK020_差分比較結果.csv',
        'key_columns': ['OYAHMCD', 'KTCD', 'BUCD', 'SRCD', 'VALDTF']  # 主キー列
    }
}

def read_csv_with_encoding(file_path):
    """
    複数のエンコーディングを試してCSVファイルを読み込む
    """
    encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis']
    last_error = None

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, dtype=str)
            # NaN値を空文字列に変換
            df = df.fillna('')
            print(f"[OK] {os.path.basename(file_path)} を {encoding} で読み込みました (行数: {len(df)})")
            return df
        except Exception as e:
            last_error = e
            continue

    error_msg = f"ファイル {file_path} の読み込みに失敗しました: {str(last_error)}"
    raise Exception(error_msg)

def compare_dataframes(df_old, df_new, key_columns, master_name):
    """
    2つのDataFrameを比較し、差分を抽出する
    """
    print(f"\n{'='*60}")
    print(f"{master_name} の比較処理を開始")
    print(f"{'='*60}")

    # 主キーが存在するか確認
    for col in key_columns:
        if col not in df_old.columns:
            print(f"警告: 旧ファイルに列 '{col}' が見つかりません")
        if col not in df_new.columns:
            print(f"警告: 新ファイルに列 '{col}' が見つかりません")

    # 主キーで重複を除去（コピーを作成）
    df_old = df_old.drop_duplicates(subset=key_columns, keep='first').copy()
    df_new = df_new.drop_duplicates(subset=key_columns, keep='first').copy()

    # 主キーを組み合わせた文字列を作成
    df_old['_key'] = df_old[key_columns].apply(lambda x: '||'.join(x.astype(str)), axis=1)
    df_new['_key'] = df_new[key_columns].apply(lambda x: '||'.join(x.astype(str)), axis=1)

    # 行全体を文字列化（主キー以外の列）
    value_columns_old = [col for col in df_old.columns if col != '_key']
    value_columns_new = [col for col in df_new.columns if col != '_key']

    df_old['_value'] = df_old[value_columns_old].apply(lambda x: '||'.join(x.astype(str)), axis=1)
    df_new['_value'] = df_new[value_columns_new].apply(lambda x: '||'.join(x.astype(str)), axis=1)

    # 差分の分類
    keys_old = set(df_old['_key'])
    keys_new = set(df_new['_key'])

    only_in_old = keys_old - keys_new
    only_in_new = keys_new - keys_old
    common_keys = keys_old & keys_new

    # 結果格納用リスト
    results = []

    # 旧ファイルにのみ存在するデータ
    for key in only_in_old:
        row = df_old[df_old['_key'] == key].iloc[0].to_dict()
        row['差分状態'] = '旧ファイルのみ'
        row['差分詳細'] = '新ファイルには存在しません'
        # _key, _valueを削除
        row.pop('_key', None)
        row.pop('_value', None)
        results.append(row)

    # 新ファイルにのみ存在するデータ
    for key in only_in_new:
        row = df_new[df_new['_key'] == key].iloc[0].to_dict()
        row['差分状態'] = '新ファイルのみ'
        row['差分詳細'] = '旧ファイルには存在しません'
        row.pop('_key', None)
        row.pop('_value', None)
        results.append(row)

    # 両方に存在するが値が異なるデータ
    modified_count = 0
    for key in common_keys:
        old_row = df_old[df_old['_key'] == key].iloc[0]
        new_row = df_new[df_new['_key'] == key].iloc[0]

        if old_row['_value'] != new_row['_value']:
            modified_count += 1
            # 差分の詳細を作成
            diff_details = []
            for col in df_old.columns:
                if col not in ['_key', '_value']:
                    old_val = str(old_row.get(col, ''))
                    new_val = str(new_row.get(col, ''))
                    if old_val != new_val:
                        diff_details.append(f"{col}: [{old_val}] → [{new_val}]")

            row = new_row.to_dict()
            row['差分状態'] = '値が変更'
            row['差分詳細'] = ' | '.join(diff_details) if diff_details else '差分検出'
            row.pop('_key', None)
            row.pop('_value', None)
            results.append(row)

    # 統計情報を表示
    print(f"\n【比較結果】")
    print(f"  旧ファイル総行数: {len(df_old):,}")
    print(f"  新ファイル総行数: {len(df_new):,}")
    print(f"  旧ファイルのみ: {len(only_in_old):,} 件")
    print(f"  新ファイルのみ: {len(only_in_new):,} 件")
    print(f"  値が変更: {modified_count:,} 件")
    print(f"  一致（出力対象外）: {len(common_keys) - modified_count:,} 件")
    print(f"  差分合計: {len(results):,} 件")

    return pd.DataFrame(results)

def main():
    """
    メイン処理
    """
    print(f"\n{'#'*60}")
    print(f"# CSV差分比較処理開始")
    print(f"# 処理時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")

    # 各ファイルペアの比較処理
    for master_name, config in FILE_PAIRS.items():
        try:
            # ファイル読み込み
            print(f"\n[{master_name}] ファイル読み込み中...")
            df_old = read_csv_with_encoding(config['old'])
            df_new = read_csv_with_encoding(config['new'])

            # 比較処理
            df_result = compare_dataframes(df_old, df_new, config['key_columns'], master_name)

            # 結果が空の場合
            if len(df_result) == 0:
                print(f"\n[OK] [{master_name}] 差分はありません（すべて一致）")
                # 空のCSVファイルを作成
                df_empty = pd.DataFrame(columns=['差分状態', '差分詳細'])
                df_empty.to_csv(config['output'], index=False, encoding='utf-8-sig')
                print(f"  出力ファイル: {config['output']} (空ファイル)")
            else:
                # 列の順序を調整（差分状態、差分詳細を先頭に）
                cols = df_result.columns.tolist()
                if '差分状態' in cols and '差分詳細' in cols:
                    cols.remove('差分状態')
                    cols.remove('差分詳細')
                    cols = ['差分状態', '差分詳細'] + cols
                    df_result = df_result[cols]

                # CSV出力
                df_result.to_csv(config['output'], index=False, encoding='utf-8-sig')
                print(f"\n[OK] [{master_name}] 比較結果を出力しました")
                print(f"  出力ファイル: {config['output']}")
                print(f"  出力行数: {len(df_result):,} 件")

        except Exception as e:
            print(f"\n[ERROR] [{master_name}] エラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()

    print(f"\n{'#'*60}")
    print(f"# すべての処理が完了しました")
    print(f"{'#'*60}\n")

if __name__ == '__main__':
    main()
