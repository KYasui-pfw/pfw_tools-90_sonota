"""
処理2: Access DB → CSV抽出処理

機能:
- ネットワークドライブからAccess DBファイルをコピー
- UCanAccessで各テーブルを抽出
- KakouJissekiディレクトリにCSV出力
"""
import os
import shutil
import warnings
import jaydebeapi
import pandas as pd
from dotenv import load_dotenv
from logger_config import setup_logger, cleanup_old_logs

# pandasのUserWarningを抑制
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

# 環境変数を読み込み
load_dotenv()

# ロガー設定
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '7'))
logger = setup_logger('process2', LOG_DIR, LOG_RETENTION_DAYS)


def copy_accdb_file(source_path, dest_dir):
    """
    Access DBファイルをコピー

    Args:
        source_path (str): ソースファイルパス
        dest_dir (str): コピー先ディレクトリ

    Returns:
        str: コピー先ファイルパス、失敗時はNone
    """
    filename = os.path.basename(source_path)

    try:
        if not os.path.exists(source_path):
            logger.error(f"ファイルが見つかりません: {source_path}")
            return None

        # コピー先ディレクトリが存在しない場合は作成
        os.makedirs(dest_dir, exist_ok=True)

        # ファイルをコピー
        dest_path = os.path.join(dest_dir, filename)
        shutil.copy2(source_path, dest_path)

        file_size = os.path.getsize(dest_path)
        logger.info(f"  ✓ コピー完了: {filename} ({file_size:,} bytes)")
        return dest_path

    except Exception as e:
        logger.error(f"  ✗ コピー失敗: {filename} - {e}")
        return None


def extract_table_to_csv(db_path, table_name, output_dir, output_prefix, job_table_name=None):
    """
    Access DBからテーブルを抽出してCSV出力
    job_table_nameが指定されている場合、LEFT JOINを実行

    Args:
        db_path (str): Access DBファイルパス
        table_name (str): 抽出するテーブル名
        output_dir (str): 出力先ディレクトリ
        output_prefix (str): 出力ファイル名プレフィックス
        job_table_name (str, optional): ジョブテーブル名（指定時はLEFT JOIN実行）

    Returns:
        bool: 成功したらTrue
    """
    conn = None

    try:
        logger.info(f"  テーブル '{table_name}' を処理中...")

        # UCanAccess接続情報
        ucanaccess_dir = "/app/ucanaccess_lib"
        jars = [
            os.path.join(ucanaccess_dir, jar_file)
            for jar_file in os.listdir(ucanaccess_dir)
            if jar_file.endswith('.jar')
        ]
        classpath = ":".join(jars)
        driver = 'net.ucanaccess.jdbc.UcanaccessDriver'
        conn_str = f"jdbc:ucanaccess://{db_path}"

        # データベースに接続
        conn = jaydebeapi.connect(driver, conn_str, {}, jars=classpath)

        # テーブルからデータを取得
        if job_table_name:
            # LEFT JOINを実行（KaLstCyl_All.KUMITATENO_Job = ジョブ.lotCode）
            query = f'''
                SELECT t1.*, t2.*
                FROM [{table_name}] AS t1
                LEFT JOIN [{job_table_name}] AS t2
                ON t1.KUMITATENO_Job = t2.lotCode
            '''
            logger.info(f"  ジョブテーブル '{job_table_name}' とLEFT JOINを実行中...")
        else:
            query = f'SELECT * FROM [{table_name}]'

        df = pd.read_sql_query(query, conn)

        # 出力先ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        # CSVファイルとして出力
        output_filename = f"{output_prefix}_{table_name}.csv"
        output_path = os.path.join(output_dir, output_filename)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        file_size = os.path.getsize(output_path)
        logger.info(f"  ✓ {len(df):,}件のデータを出力しました: {output_filename} ({file_size:,} bytes)")
        return True

    except Exception as e:
        logger.error(f"  ✗ エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        if conn:
            conn.close()


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("処理2: Access DB → CSV抽出処理を開始")
    logger.info("=" * 60)

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # 環境変数から設定を読み込み
    accdb_source1 = os.getenv('ACCDB_SOURCE1')
    accdb_source2 = os.getenv('ACCDB_SOURCE2')
    table1_name = os.getenv('TABLE1_NAME', 'KaLstCyl_All')
    table2_name = os.getenv('TABLE2_NAME', 'CAMFIN_LOG_ALL')
    job_table_name = os.getenv('JOB_TABLE_NAME', 'ジョブ')  # LEFT JOIN用のジョブテーブル名
    output_prefix1 = os.getenv('OUTPUT_PREFIX1', 'Cyl_pfw_table')
    output_prefix2 = os.getenv('OUTPUT_PREFIX2', 'EJデータマスター')
    output_dir = os.getenv('OUTPUT_DIR_JISSEKI', '/app/output/KakouJisseki')
    data_dir = '/app/data'

    if not accdb_source1 or not accdb_source2:
        logger.error("環境変数ACCDB_SOURCE1またはACCDB_SOURCE2が設定されていません")
        return 1

    logger.info(f"出力先: {output_dir}\n")

    # 処理対象DB定義
    databases = [
        {
            'source': accdb_source1,
            'table_name': table1_name,
            'output_prefix': output_prefix1,
            'job_table_name': job_table_name  # KaLstCyl_AllとジョブテーブルをLEFT JOIN
        },
        {
            'source': accdb_source2,
            'table_name': table2_name,
            'output_prefix': output_prefix2,
            'job_table_name': None  # CAMFIN_LOG_ALLはJOINなし
        }
    ]

    success_count = 0
    error_count = 0

    # 各データベースを処理
    for idx, db_info in enumerate(databases, 1):
        source_path = db_info['source']
        table_name = db_info['table_name']
        output_prefix = db_info['output_prefix']
        job_table_name = db_info.get('job_table_name', None)  # ジョブテーブル名を取得

        logger.info(f"[{idx}/{len(databases)}] データベースに接続しています: {os.path.basename(source_path)}")

        # ステップ1: Access DBファイルをコピー（★テスト用ファイル使用時はスキップ★）
        source_filename = os.path.basename(source_path)

        # ★テスト用: 対象のaccdbファイルに対応する_test.accdbが存在する場合は優先使用★
        if source_filename == 'Cyl_pfw_table.accdb':
            test_file = os.path.join(data_dir, 'Cyl_pfw_table_test.accdb')
            if os.path.exists(test_file):
                logger.info(f"  ★ テストモード: 既存のテストファイルを使用します: {os.path.basename(test_file)}")
                db_path = test_file
            else:
                logger.warning(f"  テストファイルが見つかりません: {test_file}")
                logger.info(f"  通常モード: ソースファイルをコピーします")
                db_path = copy_accdb_file(source_path, data_dir)
                if not db_path:
                    error_count += 1
                    logger.info("")
                    continue
        elif source_filename == 'EJデータマスター.accdb':
            test_file = os.path.join(data_dir, 'EJデータマスター_test.accdb')
            if os.path.exists(test_file):
                logger.info(f"  ★ テストモード: 既存のテストファイルを使用します: {os.path.basename(test_file)}")
                db_path = test_file
            else:
                logger.warning(f"  テストファイルが見つかりません: {test_file}")
                logger.info(f"  通常モード: ソースファイルをコピーします")
                db_path = copy_accdb_file(source_path, data_dir)
                if not db_path:
                    error_count += 1
                    logger.info("")
                    continue
        else:
            db_path = copy_accdb_file(source_path, data_dir)
            if not db_path:
                error_count += 1
                logger.info("")
                continue

        # ステップ2: テーブルを抽出してCSV出力（job_table_nameが指定されている場合はLEFT JOIN）
        result = extract_table_to_csv(db_path, table_name, output_dir, output_prefix, job_table_name)

        if result:
            success_count += 1
        else:
            error_count += 1

        logger.info("")

    # 処理結果サマリー
    logger.info("=" * 60)
    logger.info("処理2完了")
    logger.info(f"成功: {success_count}テーブル")
    logger.info(f"失敗: {error_count}テーブル")
    logger.info("=" * 60)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    exit(main())
