"""
処理1: rBOM CSVファイルコピー・加工処理

機能:
- 4つのCSVファイルをコピー
- 2ファイルは項目削除・重複削除を実施
- KakouDenpyoディレクトリに出力
"""
import os
import shutil
import pandas as pd
from dotenv import load_dotenv
from logger_config import setup_logger, cleanup_old_logs

# 環境変数を読み込み
load_dotenv()

# ロガー設定
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '7'))
logger = setup_logger('process1', LOG_DIR, LOG_RETENTION_DAYS)


def set_file_permissions(file_path):
    """
    ファイルのパーミッションを666に設定（全ユーザー読み書き可能）

    Args:
        file_path (str): ファイルパス
    """
    try:
        os.chmod(file_path, 0o666)
        logger.debug(f"パーミッション設定完了: {file_path} (666)")
    except Exception as e:
        logger.warning(f"パーミッション設定に失敗しました: {file_path} - {e}")


def read_csv_files():
    """環境変数からCSVファイルパスを読み込む"""
    csv_files = {
        'csv1': os.getenv('CSV1_PATH'),  # CAMKakouDenpyou.csv
        'csv2': os.getenv('CSV2_PATH'),  # CONV.csv
        'csv3': os.getenv('CSV3_PATH'),  # SEISANKI.csv
        'csv4': os.getenv('CSV4_PATH'),  # ASPKakouDenpyo.csv
    }

    # パスの存在確認
    for key, path in csv_files.items():
        if not path:
            logger.error(f"環境変数が設定されていません: {key.upper()}_PATH")
            return None

    return csv_files


def copy_simple_file(source_path, output_dir, output_filename=None):
    """
    CSVファイルをそのままコピー

    Args:
        source_path (str): ソースファイルパス
        output_dir (str): 出力先ディレクトリ
        output_filename (str, optional): 出力ファイル名（指定しない場合は元のファイル名）

    Returns:
        bool: 成功したらTrue
    """
    source_filename = os.path.basename(source_path)
    filename = output_filename if output_filename else source_filename

    try:
        if not os.path.exists(source_path):
            logger.error(f"ファイルが見つかりません: {source_path}")
            return False

        # 出力先ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        # ファイルをコピー
        dest_path = os.path.join(output_dir, filename)
        shutil.copy2(source_path, dest_path)

        # パーミッションを666に設定
        set_file_permissions(dest_path)

        file_size = os.path.getsize(dest_path)
        logger.info(f"✓ コピー完了: {filename} ({file_size:,} bytes)")
        return True

    except Exception as e:
        logger.error(f"✗ コピー失敗: {filename} - {e}")
        return False


def process_and_copy_file(source_path, output_dir, delete_columns=None, output_filename=None, rename_columns=None):
    """
    CSVファイルを加工してコピー（項目削除・重複削除・カラム名変更）

    Args:
        source_path (str): ソースファイルパス
        output_dir (str): 出力先ディレクトリ
        delete_columns (list): 削除対象カラムのリスト
        output_filename (str, optional): 出力ファイル名（指定しない場合は元のファイル名）
        rename_columns (dict, optional): カラム名変更マッピング（旧名: 新名）

    Returns:
        bool: 成功したらTrue
    """
    source_filename = os.path.basename(source_path)
    filename = output_filename if output_filename else source_filename

    try:
        if not os.path.exists(source_path):
            logger.error(f"ファイルが見つかりません: {source_path}")
            return False

        # CSVファイルを読み込み（エンコーディング自動検出）
        logger.info(f"読み込み中: {filename}")

        # 複数のエンコーディングを試行
        encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis', 'latin1']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(source_path, encoding=encoding)
                logger.info(f"  エンコーディング: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            logger.error(f"  ✗ エンコーディングの検出に失敗しました")
            return False

        original_rows = len(df)
        logger.info(f"  元データ: {original_rows:,}行, {len(df.columns)}列")

        # 項目削除
        if delete_columns:
            existing_columns = [col for col in delete_columns if col in df.columns]
            if existing_columns:
                df = df.drop(columns=existing_columns)
                logger.info(f"  項目削除: {len(existing_columns)}列削除 → {len(df.columns)}列")

        # カラム名変更
        if rename_columns:
            existing_renames = {old: new for old, new in rename_columns.items() if old in df.columns}
            if existing_renames:
                df = df.rename(columns=existing_renames)
                logger.info(f"  カラム名変更: {len(existing_renames)}列変更")
                for old, new in existing_renames.items():
                    logger.info(f"    '{old}' → '{new}'")

        # 重複行削除
        df_deduplicated = df.drop_duplicates()
        duplicates_removed = original_rows - len(df_deduplicated)
        if duplicates_removed > 0:
            logger.info(f"  重複削除: {duplicates_removed:,}行削除 → {len(df_deduplicated):,}行")
            df = df_deduplicated

        # 出力先ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        # CSVとして出力（Shift_JIS）
        dest_path = os.path.join(output_dir, filename)
        df.to_csv(dest_path, index=False, encoding='cp932')

        # パーミッションを666に設定
        set_file_permissions(dest_path)

        file_size = os.path.getsize(dest_path)
        logger.info(f"✓ 加工完了: {filename} ({file_size:,} bytes, encoding=cp932)")
        return True

    except Exception as e:
        logger.error(f"✗ 加工失敗: {filename} - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("処理1: rBOM CSVファイルコピー・加工処理を開始")
    logger.info("=" * 60)

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # 環境変数からパスを取得
    csv_files = read_csv_files()
    if not csv_files:
        logger.error("環境変数の読み込みに失敗しました")
        return 1

    output_dir = os.getenv('OUTPUT_DIR_DENPYO', '/app/output/KakouDenpyo')
    logger.info(f"出力先: {output_dir}\n")

    # 加工対象ファイル名と削除カラム設定
    process_file1 = os.getenv('PROCESS_FILE1', 'CAMKakouDenpyou.csv')
    process_file2 = os.getenv('PROCESS_FILE2', 'ASPKakouDenpyo.csv')

    # 出力ファイル名の設定（半角スペースを含む名前に対応）
    output_file1 = os.getenv('OUTPUT_FILE1', '4-01 CAMKakouDenpyo.csv')
    output_file2 = os.getenv('OUTPUT_FILE2', '4-03 ASPKakouDenpyo.csv')

    # 削除カラムの取得（カンマ区切り）
    delete_columns_file1_str = os.getenv('DELETE_COLUMNS_FILE1', '')
    delete_columns_file2_str = os.getenv('DELETE_COLUMNS_FILE2', '')

    delete_columns_file1 = [col.strip() for col in delete_columns_file1_str.split(',') if col.strip()]
    delete_columns_file2 = [col.strip() for col in delete_columns_file2_str.split(',') if col.strip()]

    # カラム名変更マッピングの取得（形式: "旧名1:新名1,旧名2:新名2"）
    rename_columns_file1_str = os.getenv('RENAME_COLUMNS_FILE1', '')
    rename_columns_file2_str = os.getenv('RENAME_COLUMNS_FILE2', '')

    rename_columns_file1 = {}
    if rename_columns_file1_str:
        for pair in rename_columns_file1_str.split(','):
            if ':' in pair:
                old, new = pair.split(':', 1)
                rename_columns_file1[old.strip()] = new.strip()

    rename_columns_file2 = {}
    if rename_columns_file2_str:
        for pair in rename_columns_file2_str.split(','):
            if ':' in pair:
                old, new = pair.split(':', 1)
                rename_columns_file2[old.strip()] = new.strip()

    success_count = 0
    error_count = 0

    # 各ファイルを処理
    for key, source_path in csv_files.items():
        filename = os.path.basename(source_path)

        logger.info(f"[{success_count + error_count + 1}/{len(csv_files)}] 処理中: {filename}")

        # 加工対象ファイルかどうか判定
        if filename == process_file1:
            # CAMKakouDenpyou.csv - 項目削除・重複削除・カラム名変更
            if delete_columns_file1:
                logger.info(f"  削除対象カラム: {', '.join(delete_columns_file1)}")
            logger.info(f"  出力ファイル名: {output_file1}")
            result = process_and_copy_file(source_path, output_dir, delete_columns_file1, output_file1, rename_columns_file1)
        elif filename == process_file2:
            # ASPKakouDenpyo.csv - 項目削除・重複削除・カラム名変更
            if delete_columns_file2:
                logger.info(f"  削除対象カラム: {', '.join(delete_columns_file2)}")
            logger.info(f"  出力ファイル名: {output_file2}")
            result = process_and_copy_file(source_path, output_dir, delete_columns_file2, output_file2, rename_columns_file2)
        else:
            # CONV.csv, SEISANKI.csv - そのままコピー
            result = copy_simple_file(source_path, output_dir)

        if result:
            success_count += 1
        else:
            error_count += 1

        logger.info("")

    # 処理結果サマリー
    logger.info("=" * 60)
    logger.info("処理1完了")
    logger.info(f"成功: {success_count}ファイル")
    logger.info(f"失敗: {error_count}ファイル")
    logger.info("=" * 60)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    exit(main())
