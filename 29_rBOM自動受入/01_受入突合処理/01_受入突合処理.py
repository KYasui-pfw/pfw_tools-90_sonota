"""
rBOM自動受入処理スクリプト

タスクスケジューラで15分ごとに実行される前提

処理フロー:
1. EJシステム（T_ACPT_RSLT）からCREATED_DATE >= 2025/01/01の受入実績データを取得
2. mapping.dbのmapping_resultsテーブルとPUCH_ODR_CD=ej_order_noで突合
3. マッチあり/なしに分けてCSV出力
4. rBOM APIに受入実績を登録（TODO）
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import oracledb
from dotenv import load_dotenv

# 設定
SCRIPT_DIR = Path(__file__).parent
FILES_DIR = SCRIPT_DIR / "Files"
WORK_DIR = SCRIPT_DIR / "work"
LOG_DIR = SCRIPT_DIR / "log"

# mapping.dbのパス
MAPPING_DB_PATH = FILES_DIR / "mapping.db"

# .env読み込み
load_dotenv(SCRIPT_DIR / ".env")

# EJデータベース接続情報
EJ_DB_HOST = "172.17.107.102"
EJ_DB_PORT = "1521"
EJ_DB_SERVICE = "EXPJ"
EJ_DB_USER = "EXPJ2"
EJ_DB_PASSWORD = "EXPJ2"

# Oracle client初期化フラグ
_ej_thick_mode_initialized = False


def setup_logging():
    """ログ設定（日次ファイル、7日間保持）"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 古いログファイルを削除
    cleanup_old_logs()

    # ログファイル名（日付付き）
    log_filename = LOG_DIR / f"log_{datetime.now().strftime('%Y%m%d')}.txt"

    # ロガー設定
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # ファイルハンドラ（追記モード）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def cleanup_old_logs():
    """7日より古いログファイルを削除"""
    if not LOG_DIR.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=7)

    for log_file in LOG_DIR.glob("log_*.txt"):
        try:
            date_str = log_file.stem.replace("log_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")

            if file_date < cutoff_date:
                log_file.unlink()
                logging.info(f"[LOG] 古いログを削除: {log_file.name}")
        except (ValueError, OSError):
            pass


# printをオーバーライド（ログにも出力）
original_print = print


def print(*args, **kwargs):
    """printをオーバーライドしてログにも出力"""
    message = ' '.join(str(arg) for arg in args)
    logging.info(message)


def init_oracle_client():
    """Oracle clientの初期化（初回のみ）"""
    global _ej_thick_mode_initialized
    if not _ej_thick_mode_initialized:
        try:
            oracledb.init_oracle_client()
            _ej_thick_mode_initialized = True
        except Exception:
            pass  # 既に初期化済みの場合


def get_ej_acpt_rslt():
    """EJシステムからT_ACPT_RSLT（受入実績）を取得（CREATED_DATE >= 2025/01/01）"""
    print("=" * 50)
    print("EJシステムから受入実績データを取得")
    print("=" * 50)

    init_oracle_client()

    connection_string = f"{EJ_DB_USER}/{EJ_DB_PASSWORD}@{EJ_DB_HOST}:{EJ_DB_PORT}/{EJ_DB_SERVICE}"

    try:
        conn = oracledb.connect(connection_string)
        cursor = conn.cursor()

        query = """
            SELECT
                PUCH_ODR_CD,
                ACPT_NO,
                ACPT_QTY,
                ACPT_DATE,
                UNIT_COST,
                WH_CD,
                VEND_LOT_NO,
                ACPT_STS_TYP,
                CREATED_DATE
            FROM EXPJ2.T_ACPT_RSLT
            WHERE CREATED_DATE >= TO_DATE('2025/01/01', 'YYYY/MM/DD')
            ORDER BY CREATED_DATE DESC
        """

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()

        df = pd.DataFrame(rows, columns=columns)
        print(f"取得件数: {len(df)}件")

        # 日付変換
        if 'ACPT_DATE' in df.columns:
            df['ACPT_DATE'] = pd.to_datetime(df['ACPT_DATE']).dt.strftime("%Y-%m-%d")
        if 'CREATED_DATE' in df.columns:
            df['CREATED_DATE'] = pd.to_datetime(df['CREATED_DATE']).dt.strftime("%Y-%m-%d %H:%M:%S")

        return df

    except Exception as e:
        print(f"[ERROR] EJデータ取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame()


def get_mapping_results():
    """mapping.dbからmapping_resultsテーブルを取得"""
    print("")
    print("=" * 50)
    print("mapping.dbからマッピング結果を取得")
    print("=" * 50)

    if not MAPPING_DB_PATH.exists():
        print(f"[ERROR] mapping.dbが見つかりません: {MAPPING_DB_PATH}")
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(MAPPING_DB_PATH)
        df = pd.read_sql_query("SELECT ej_order_no, period FROM mapping_results", conn)
        conn.close()

        print(f"取得件数: {len(df)}件")
        return df

    except Exception as e:
        print(f"[ERROR] mapping.db読み込みエラー: {e}")
        return pd.DataFrame()


def match_and_export(df_ej, df_mapping):
    """EJデータとmapping_resultsを突合し、CSV出力
    
    出力ファイル:
    - 01_マッチあり.csv: 両方に存在するデータ
    - 01_EJのみ.csv: EJ側にあるがmapping.dbにないデータ
    - 01_mappingのみ.csv: mapping.dbにあるがEJ側にないデータ
    """
    print("")
    print("=" * 50)
    print("突合処理・CSV出力")
    print("=" * 50)

    # workディレクトリを作成
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    if df_ej.empty and df_mapping.empty:
        print("[WARN] EJデータ・マッピングデータ両方が空です")
        return

    if df_ej.empty:
        print("[WARN] EJデータが空です。mapping側のみ出力します")
        output_path = WORK_DIR / "01_mappingのみ.csv"
        df_mapping.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] mappingのみ: {len(df_mapping)}件 -> {output_path}")
        return

    if df_mapping.empty:
        print("[WARN] マッピングデータが空です。EJ側のみ出力します")
        output_path = WORK_DIR / "01_EJのみ.csv"
        df_ej.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] EJのみ: {len(df_ej)}件 -> {output_path}")
        return

    # mapping_resultsのej_order_noをユニーク化（重複がある場合は最初の1件を使用）
    df_mapping_unique = df_mapping.drop_duplicates(subset=['ej_order_no'], keep='first')

    # EJ側のPUCH_ODR_CDのセット
    ej_orders = set(df_ej['PUCH_ODR_CD'].astype(str))
    # mapping側のej_order_noのセット
    mapping_orders = set(df_mapping_unique['ej_order_no'].astype(str))

    # 1. マッチあり（両方に存在）
    matched_orders = ej_orders & mapping_orders
    
    # 2. EJのみ（mapping.dbにない）
    ej_only_orders = ej_orders - mapping_orders
    
    # 3. mappingのみ（EJ側にない）
    mapping_only_orders = mapping_orders - ej_orders

    print(f"マッチあり: {len(matched_orders)}件")
    print(f"EJのみ: {len(ej_only_orders)}件")
    print(f"mappingのみ: {len(mapping_only_orders)}件")

    # マッチありデータを作成（EJデータにmapping情報をJOIN）
    if matched_orders:
        df_match = df_ej[df_ej['PUCH_ODR_CD'].astype(str).isin(matched_orders)].merge(
            df_mapping_unique,
            left_on='PUCH_ODR_CD',
            right_on='ej_order_no',
            how='left'
        )
        output_path = WORK_DIR / "01_マッチあり.csv"
        df_match.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] -> {output_path}")

    # EJのみデータを出力
    if ej_only_orders:
        df_ej_only = df_ej[df_ej['PUCH_ODR_CD'].astype(str).isin(ej_only_orders)].copy()
        output_path = WORK_DIR / "01_EJのみ.csv"
        df_ej_only.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] -> {output_path}")

    # mappingのみデータを出力
    if mapping_only_orders:
        df_mapping_only = df_mapping_unique[df_mapping_unique['ej_order_no'].astype(str).isin(mapping_only_orders)].copy()
        output_path = WORK_DIR / "01_mappingのみ.csv"
        df_mapping_only.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] -> {output_path}")


def main():
    """メイン処理"""
    # ログ設定
    setup_logging()

    start_time = datetime.now()
    print("")
    print("=" * 50)
    print(f"rBOM自動受入処理 開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # 1. EJシステムから受入実績データを取得
        df_ej = get_ej_acpt_rslt()

        # 2. mapping.dbからマッピング結果を取得
        df_mapping = get_mapping_results()

        # 3. 突合してCSV出力
        match_and_export(df_ej, df_mapping)

        # TODO: 4. rBOM APIに受入実績を登録

    except Exception as e:
        print(f"[ERROR] 処理中にエラーが発生: {e}")
        import traceback
        print(traceback.format_exc())

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    print("")
    print("=" * 50)
    print(f"処理完了: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (所要時間: {elapsed:.1f}秒)")
    print("=" * 50)


if __name__ == "__main__":
    main()
