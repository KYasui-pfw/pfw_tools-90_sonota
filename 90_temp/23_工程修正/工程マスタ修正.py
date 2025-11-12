"""
工程マスタ修正スクリプト

機能:
- CSVファイルのKTCDを修正して新しい列を追加
- 行の順番を変更せずに処理
- HMCDごとにKTSEQの最大行を判定（PL/PA始まりは除外）
- 最大行未満で9を含むKTCDを修正（9とその右側を削除）
- PL/PA始まりの行は修正対象外
"""
import pandas as pd
import os
from datetime import datetime
import sys

# エンコーディング自動判定用
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
    return 'utf-8'  # デフォルト


def process_ktcd_correction(input_file, output_file, log_file):
    """
    工程マスタのKTCD修正処理

    Args:
        input_file (str): 入力CSVファイルパス
        output_file (str): 出力CSVファイルパス
        log_file (str): ログファイルパス
    """
    log_messages = []
    log_messages.append("=" * 60)
    log_messages.append("工程マスタ修正処理 開始")
    log_messages.append("=" * 60)
    log_messages.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_messages.append(f"入力ファイル: {input_file}")
    log_messages.append(f"出力ファイル: {output_file}")
    log_messages.append("")

    try:
        # エンコーディング判定
        encoding = detect_encoding(input_file)
        log_messages.append(f"検出されたエンコーディング: {encoding}")

        # CSVファイル読み込み
        df = pd.read_csv(input_file, encoding=encoding)
        total_rows = len(df)
        log_messages.append(f"総行数: {total_rows:,}行")
        log_messages.append("")

        # KTCD修正後の列を追加（初期値は空文字）
        df['KTCD修正後'] = ''

        # HMCDでグループ化して処理
        modified_count = 0
        modified_groups = set()
        excluded_pl_pa_count = 0

        for hmcd, group in df.groupby('HMCD', sort=False):
            group_indices = group.index

            # PL/PA始まりを除外して最大KTSEQ行を判定
            non_pl_pa_group = group[~group['KTCD'].str.startswith(('PL', 'PA'))]

            if len(non_pl_pa_group) == 0:
                # すべてPL/PAの場合は処理しない
                continue

            # 最大KTSEQ行を取得
            max_ktseq_row = non_pl_pa_group.loc[non_pl_pa_group['KTSEQ'].idxmax()]
            max_ktseq = max_ktseq_row['KTSEQ']

            # 最大行未満の行を対象に処理
            target_rows = group[group['KTSEQ'] < max_ktseq]

            for idx in target_rows.index:
                ktcd = df.at[idx, 'KTCD']

                # PL/PA始まりは修正対象外
                if ktcd.startswith('PL') or ktcd.startswith('PA'):
                    if '9' in ktcd:
                        excluded_pl_pa_count += 1
                    continue

                # 9が含まれるKTCDを修正
                if '9' in ktcd:
                    # 9の位置を見つけて、9とその右側を削除
                    pos = ktcd.index('9')
                    corrected_ktcd = ktcd[:pos]

                    df.at[idx, 'KTCD修正後'] = corrected_ktcd
                    modified_count += 1
                    modified_groups.add(hmcd)

        # 出力ディレクトリを作成
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # CSVファイル出力（同じエンコーディングで）
        df.to_csv(output_file, index=False, encoding=encoding)

        # 処理結果サマリー
        log_messages.append("=" * 60)
        log_messages.append("処理結果サマリー")
        log_messages.append("=" * 60)
        log_messages.append(f"修正対象HMCDグループ数: {len(modified_groups):,}グループ")
        log_messages.append(f"修正された行数: {modified_count:,}行")
        log_messages.append(f"PL/PA始まりで除外された行数: {excluded_pl_pa_count:,}行")
        log_messages.append("")

        # 修正例をいくつか表示
        log_messages.append("=" * 60)
        log_messages.append("修正例（最初の10件）")
        log_messages.append("=" * 60)
        modified_samples = df[df['KTCD修正後'] != ''].head(10)
        for _, row in modified_samples.iterrows():
            log_messages.append(f"HMCD={row['HMCD']}, KTSEQ={row['KTSEQ']}, KTCD={row['KTCD']} → {row['KTCD修正後']}")

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
    input_file = os.path.join(base_dir, "input", "工程マスタ修正前.csv")
    output_file = os.path.join(base_dir, "output", "工程マスタ修正後.csv")
    log_file = os.path.join(base_dir, f"処理ログ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    # 入力ファイルの存在確認
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        return 1

    # 処理実行
    success = process_ktcd_correction(input_file, output_file, log_file)

    if success:
        print(f"\n出力ファイル: {output_file}")
        print(f"ログファイル: {log_file}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
