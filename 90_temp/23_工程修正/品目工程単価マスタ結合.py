"""
品目工程単価マスタと品目工程マスタ修正後の結合処理

機能:
- 品目工程単価マスタ.csvに、品目工程マスタ修正後.csvから9KTCDを追加
- OYAHMCD + KTCDをキーにLEFT JOINを実行
- 複数マッチする場合はカンマ区切りで連結
"""
import pandas as pd
import os
from datetime import datetime
import sys


def detect_encoding(file_path):
    """ファイルのエンコーディングを判定"""
    encodings = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8'


def process_join(master_file, modified_file, output_file, log_file):
    """
    品目工程単価マスタと品目工程マスタ修正後を結合

    Args:
        master_file (str): 品目工程単価マスタのパス
        modified_file (str): 品目工程マスタ修正後のパス
        output_file (str): 出力CSVファイルパス
        log_file (str): ログファイルパス
    """
    log_messages = []
    log_messages.append("=" * 60)
    log_messages.append("品目工程単価マスタ結合処理 開始")
    log_messages.append("=" * 60)
    log_messages.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append(f"品目工程単価マスタ: {master_file}")
    log_messages.append(f"品目工程マスタ修正後: {modified_file}")
    log_messages.append(f"出力ファイル: {output_file}")
    log_messages.append("")

    try:
        # エンコーディング判定
        master_enc = detect_encoding(master_file)
        modified_enc = detect_encoding(modified_file)
        log_messages.append(f"品目工程単価マスタのエンコーディング: {master_enc}")
        log_messages.append(f"品目工程マスタ修正後のエンコーディング: {modified_enc}")
        log_messages.append("")

        # ファイル読み込み
        df_master = pd.read_csv(master_file, encoding=master_enc)
        df_modified = pd.read_csv(modified_file, encoding=modified_enc)

        log_messages.append(f"品目工程単価マスタ行数: {len(df_master):,}行")
        log_messages.append(f"品目工程マスタ修正後行数: {len(df_modified):,}行")
        log_messages.append("")

        # 品目工程マスタ修正後から、KTCDに"9"を含む行のみを抽出
        df_modified_with_9 = df_modified[df_modified['KTCD'].str.contains('9', na=False)].copy()
        log_messages.append(f"KTCDに9を含む行数: {len(df_modified_with_9):,}行")

        # KTCDから"9"とその右側を削除した列を作成（結合キー用）
        def remove_after_9(ktcd):
            """KTCDから9とその右側を削除"""
            if pd.isna(ktcd):
                return ktcd
            if '9' in ktcd:
                pos = ktcd.index('9')
                return ktcd[:pos]
            return ktcd

        df_modified_with_9['KTCD_KEY'] = df_modified_with_9['KTCD'].apply(remove_after_9)

        # 複数マッチを処理: HMCD + KTCD_KEYでグループ化し、元のKTCDをカンマ区切りで連結
        df_grouped = df_modified_with_9.groupby(['HMCD', 'KTCD_KEY'])['KTCD'].apply(
            lambda x: ','.join(sorted(set(x)))
        ).reset_index()
        df_grouped.columns = ['HMCD', 'KTCD_KEY', '9KTCD']

        log_messages.append(f"結合用レコード数（重複削除後）: {len(df_grouped):,}行")
        log_messages.append("")

        # LEFT JOIN: 品目工程単価マスタ（左） + 品目工程マスタ修正後（右）
        # 結合キー: OYAHMCD = HMCD, KTCD = KTCD_KEY
        df_result = df_master.merge(
            df_grouped,
            left_on=['OYAHMCD', 'KTCD'],
            right_on=['HMCD', 'KTCD_KEY'],
            how='left'
        )

        # 結合に使った一時カラム（HMCD, KTCD_KEY）を削除
        df_result = df_result.drop(columns=['HMCD', 'KTCD_KEY'], errors='ignore')

        # 9KTCDがNaNの場合は空文字に変換
        df_result['9KTCD'] = df_result['9KTCD'].fillna('')

        # カラム順序を調整: SYOKAIHINKBNの右に9KTCDを配置
        original_cols = list(df_master.columns)
        syokaihinkbn_index = original_cols.index('SYOKAIHINKBN')
        new_cols = original_cols[:syokaihinkbn_index + 1] + ['9KTCD'] + original_cols[syokaihinkbn_index + 1:]
        df_result = df_result[new_cols]

        # 出力ディレクトリを作成
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # CSV出力
        df_result.to_csv(output_file, index=False, encoding=master_enc)

        # 統計情報
        matched_count = len(df_result[df_result['9KTCD'] != ''])
        unmatched_count = len(df_result[df_result['9KTCD'] == ''])

        log_messages.append("=" * 60)
        log_messages.append("処理結果サマリー")
        log_messages.append("=" * 60)
        log_messages.append(f"出力総行数: {len(df_result):,}行")
        log_messages.append(f"9KTCD追加された行数: {matched_count:,}行")
        log_messages.append(f"9KTCDが空欄の行数: {unmatched_count:,}行")
        log_messages.append("")

        # マッチ例を表示
        log_messages.append("=" * 60)
        log_messages.append("9KTCD追加例（最初の10件）")
        log_messages.append("=" * 60)
        matched_samples = df_result[df_result['9KTCD'] != ''].head(10)
        for _, row in matched_samples.iterrows():
            log_messages.append(f"OYAHMCD={row['OYAHMCD']}, KTCD={row['KTCD']} → 9KTCD={row['9KTCD']}")

        # 複数マッチの例を表示
        multiple_matches = df_result[df_result['9KTCD'].str.contains(',', na=False)]
        if len(multiple_matches) > 0:
            log_messages.append("")
            log_messages.append("=" * 60)
            log_messages.append(f"複数マッチ例（カンマ区切り、{len(multiple_matches):,}件）")
            log_messages.append("=" * 60)
            for _, row in multiple_matches.head(10).iterrows():
                log_messages.append(f"OYAHMCD={row['OYAHMCD']}, KTCD={row['KTCD']} → 9KTCD={row['9KTCD']}")

        log_messages.append("")
        log_messages.append("=" * 60)
        log_messages.append("処理完了")
        log_messages.append("=" * 60)

        # ログをファイルとコンソールに出力
        log_content = "\n".join(log_messages)
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

        print(log_content)

        return True

    except Exception as e:
        error_msg = f"\nエラーが発生しました: {e}"
        log_messages.append(error_msg)
        log_content = "\n".join(log_messages)

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

        print(log_content)
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン処理"""
    # ファイルパス設定
    base_dir = r"C:\Dev\90_tools\90_temp\23_工程修正"
    master_file = os.path.join(base_dir, "input", "品目工程単価マスタ.csv")
    modified_file = os.path.join(base_dir, "input", "品目工程マスタ修正後.csv")
    output_file = os.path.join(base_dir, "output", "品目工程単価マスタ_9KTCD追加.csv")
    log_file = os.path.join(base_dir, f"処理ログ_結合_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    # 入力ファイルの存在確認
    if not os.path.exists(master_file):
        print(f"エラー: 入力ファイルが見つかりません: {master_file}")
        return 1

    if not os.path.exists(modified_file):
        print(f"エラー: 入力ファイルが見つかりません: {modified_file}")
        return 1

    # 処理実行
    success = process_join(master_file, modified_file, output_file, log_file)

    if success:
        print(f"\n出力ファイル: {output_file}")
        print(f"ログファイル: {log_file}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
