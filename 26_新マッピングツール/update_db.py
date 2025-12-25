"""
発注情報SQLiteデータベース更新スクリプト

データソース: .envファイルで定義
mapping_resultsテーブルに統合、period列で期間区分

処理フロー（12月ファイル）:
1. サーバーからExcelをコピー
2. excel_processor で D3340/D3330/MK020/M0820 APIクエリ実行
3. Excel自動追記（rBOM発注番号、行番号、工程コード等）
4. 色分け処理（水色=NOTE突合成功、黄色=MK020一致、ピンク=前工程一致、赤=取引先不一致）
5. 自動インプット除外判定
6. 処理済みExcelをデータベースにインポート
"""

import shutil
import sqlite3
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv

# Excel処理モジュール
import excel_processor

# 設定
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "mapping.db"
OUTPUT_DIR = SCRIPT_DIR / "01_excel_rBOM比較"  # Excel処理の出力先
LOG_DIR = SCRIPT_DIR / "log"


def setup_logging():
    """ログ設定（日次ファイル、1週間分保持）"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 古いログファイルを削除（7日より古いもの）
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
            # ファイル名から日付を抽出（log_YYYYMMDD.txt）
            date_str = log_file.stem.replace("log_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")

            if file_date < cutoff_date:
                log_file.unlink()
                print(f"[LOG] 古いログを削除: {log_file.name}")
        except (ValueError, OSError):
            pass  # 日付解析エラーや削除エラーは無視


def log_print(message):
    """printとログ両方に出力"""
    logging.info(message)


# printをlog_printに置き換えるためのラッパー
original_print = print


def print(*args, **kwargs):
    """printをオーバーライドしてログにも出力"""
    message = ' '.join(str(arg) for arg in args)
    logging.info(message)
    # 元のprintも呼ぶ（コンソール出力はloggingのStreamHandlerで行うため不要）
    # original_print(*args, **kwargs)

# サーバー環境でのコピー先（D:\py\EJ_rBOM_mapping\database\mapping.db）
COPY_DEST_DIR = Path(r"D:\py\EJ_rBOM_mapping\database")
COPY_DEST_DB = COPY_DEST_DIR / "mapping.db"

# .env読み込み
load_dotenv(SCRIPT_DIR / ".env")

# 期間区分
PERIOD_DEC = "2025年12月15日以降の発注マッピング"
PERIOD_NOV = "2025年11月以前の発注残マッピング"

# サーバーファイルパス（.envから取得）
SERVER_FILES = {
    PERIOD_DEC: os.getenv("FILE_DEC"),
    PERIOD_NOV: os.getenv("FILE_NOV"),
}

# ローカルコピー先（元ファイル）
LOCAL_FILES = {
    PERIOD_DEC: SCRIPT_DIR / "発注情報12月EJとrBOM.xlsx",
    PERIOD_NOV: SCRIPT_DIR / "発注情報EJとrBOM.xlsx",
}


def split_rbom(val):
    """rBOM発注番号+行番号を分割"""
    if pd.isna(val):
        return None, None
    parts = str(val).split('+')
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return str(val), None


def copy_from_server():
    """サーバーからファイルをコピーし、12月ファイルはExcel処理を実行後サーバーに書き戻し"""
    print("=" * 50)
    print("サーバーからファイルをコピー")
    print("=" * 50)

    for key, server_path in SERVER_FILES.items():
        local_path = LOCAL_FILES[key]
        server_mtime_before = None

        # 1. サーバーファイルのタイムスタンプを取得（書き戻し判定用）
        try:
            server_mtime_before = os.path.getmtime(server_path)
        except (FileNotFoundError, PermissionError, OSError):
            pass  # タイムスタンプ取得失敗は無視

        # 2. サーバーからファイルをコピー（エラーでも続行）
        try:
            shutil.copy2(server_path, local_path)
            print(f"[OK] {key}: {server_path}")
        except FileNotFoundError:
            print(f"[WARN] ファイルが見つかりません: {server_path}")
            if local_path.exists():
                print(f"       ローカルファイルを使用: {local_path}")
            else:
                print(f"[SKIP] ローカルファイルもありません")
                continue
        except PermissionError:
            print(f"[WARN] サーバーファイルが使用中のためコピーできません: {server_path}")
            if local_path.exists():
                print(f"       ローカルファイルを使用: {local_path}")
            else:
                print(f"[SKIP] ローカルファイルもありません")
                continue

        # 12月ファイルの場合、Excel処理を実行
        if key == PERIOD_DEC:
            print("\n" + "=" * 50)
            print("12月ファイルのExcel処理を実行")
            print("=" * 50)
            processed_file = excel_processor.process_december_excel(local_path, OUTPUT_DIR)

            # 処理済みファイルを発注情報12月EJとrBOM.xlsxにリネーム（上書き）
            print(f"\n処理済みファイルをリネーム: {processed_file.name} → {local_path.name}")
            shutil.copy2(processed_file, local_path)

            # サーバーに書き戻し（タイムスタンプチェック付き）
            # タイムスタンプが取得できた場合のみ書き戻しを試行
            if server_mtime_before is not None:
                copy_to_server(local_path, server_path, server_mtime_before)
            else:
                print("\n[SKIP] サーバーへの書き戻しをスキップ（タイムスタンプ取得不可）")


def copy_to_server(local_path: Path, server_path: str, original_mtime: float):
    """処理済みExcelをサーバーに書き戻し（タイムスタンプチェック付き）

    Args:
        local_path: ローカルの処理済みファイル
        server_path: サーバーのファイルパス
        original_mtime: コピー前に記録したサーバーファイルのタイムスタンプ
    """
    print("\n" + "=" * 50)
    print("サーバーへExcel書き戻し")
    print("=" * 50)

    try:
        # 現在のサーバーファイルのタイムスタンプを確認
        current_mtime = os.path.getmtime(server_path)

        if current_mtime != original_mtime:
            # タイムスタンプが変更されている = 誰かが更新した
            original_time = datetime.fromtimestamp(original_mtime).strftime('%Y-%m-%d %H:%M:%S')
            current_time = datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[SKIP] サーバーファイルが更新されています（上書きしません）")
            print(f"       コピー時: {original_time}")
            print(f"       現在:     {current_time}")
            return

        # 上書きコピー
        shutil.copy2(local_path, server_path)
        print(f"[OK] サーバーに書き戻し完了: {server_path}")

    except PermissionError:
        print(f"[SKIP] ファイルが編集中のため上書きできません: {server_path}")
    except Exception as e:
        print(f"[ERROR] サーバーへの書き戻しに失敗しました: {e}")


def load_and_transform_normal(file_path: Path, period: str) -> pd.DataFrame:
    """通常ファイル(Sheet1)を読み込みmapping_resultsレイアウトに変換"""
    print(f"\n読み込み中: {file_path.name} (Sheet1)")
    df = pd.read_excel(file_path, sheet_name="Sheet1")
    print(f"  元データ行数: {len(df)}")

    # カラムインデックス
    # [0] EJ発注番号, [3] EJ品目コード, [5] EJ数, [10] rBOM発注番号+行番号
    cols = df.columns.tolist()

    ej_order_no = df[cols[0]]  # EJ発注番号
    hmcd = df[cols[3]]  # EJ品目コード -> HMCD
    ej_quantity = df[cols[5]]  # EJ数 -> rBOM数として使用
    rbom_combined = df[cols[10]]  # rBOM発注番号+行番号

    # rBOM発注番号+行番号を分割
    rbom_order_no = []
    rbom_line_no = []
    for val in rbom_combined:
        order, line = split_rbom(val)
        rbom_order_no.append(order)
        rbom_line_no.append(line)

    # mapping_resultsと同じレイアウトで作成 + period列追加
    new_df = pd.DataFrame({
        'ej_order_no': ej_order_no,
        'rbom_order_no': rbom_order_no,
        'rbom_line_no': rbom_line_no,
        'rbom_quantity': ej_quantity,  # EJ数をrBOM数として使用
        'rbom_m_sequence': 1,  # 全て1
        'status': '済',  # 全て「済」
        'period': period,  # 期間区分
        'hmcd': hmcd  # 品目コード
    })

    print(f"  変換後行数: {len(new_df)}")
    return new_df


def load_and_transform_december(file_path: Path, period: str) -> pd.DataFrame:
    """12月ファイル(T_RLSD_PUCH_ODR)を読み込みmapping_resultsレイアウトに変換"""
    print(f"\n読み込み中: {file_path.name} (T_RLSD_PUCH_ODR)")
    df = pd.read_excel(file_path, sheet_name="T_RLSD_PUCH_ODR")
    print(f"  元データ行数: {len(df)}")

    # カラムインデックス
    # [7] 連番号 = EJ発注番号
    # [5] rBOM発注番号（必須）
    # [6] 行番号
    # [11] 品目番号 (L列)
    # [12] 発注数 (M列)
    # [89] rBOM品目CD
    # [90] rBOM発注数
    cols = df.columns.tolist()

    ej_order_no = df[cols[7]]  # 連番号 = EJ発注番号
    rbom_order_no = df[cols[5]]  # rBOM発注番号（必須）
    rbom_line_no = df[cols[6]]  # 行番号
    rbom_quantity = df[cols[90]]  # rBOM発注数
    order_quantity = df[cols[12]]  # 発注数 (M列)
    rbom_hmcd = df[cols[89]]  # rBOM品目CD
    item_no = df[cols[11]]  # 品目番号 (L列)

    # rBOM発注数がNaNの場合は発注数(M列)を使用
    rbom_quantity = rbom_quantity.fillna(order_quantity)

    # rBOM品目CDがNaNの場合は品目番号(L列)を使用
    hmcd = rbom_hmcd.fillna(item_no)

    # mapping_resultsと同じレイアウトで作成 + period列追加
    new_df = pd.DataFrame({
        'ej_order_no': ej_order_no,
        'rbom_order_no': rbom_order_no,
        'rbom_line_no': rbom_line_no,
        'rbom_quantity': rbom_quantity,
        'rbom_m_sequence': 1,  # 全て1
        'status': '済',  # 全て「済」
        'period': period,  # 期間区分
        'hmcd': hmcd  # 品目コード
    })

    print(f"  変換後行数: {len(new_df)}")
    return new_df


def update_database():
    """SQLiteデータベースを更新"""
    print("\n" + "=" * 50)
    print("データベース更新")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    # 既存テーブルがあれば削除して再作成
    conn.execute('DROP TABLE IF EXISTS mapping_results')
    conn.execute('DROP INDEX IF EXISTS idx_ej_order_no')
    conn.execute('DROP INDEX IF EXISTS idx_rbom_order_no')
    conn.execute('DROP INDEX IF EXISTS idx_period')
    print("既存テーブルを削除しました")

    # mapping_resultsテーブル作成（period, hmcd列追加）
    conn.execute('''
        CREATE TABLE mapping_results (
            ej_order_no TEXT,
            rbom_order_no TEXT,
            rbom_line_no INTEGER,
            rbom_quantity REAL,
            rbom_m_sequence INTEGER,
            status TEXT,
            period TEXT,
            hmcd TEXT
        )
    ''')

    total_rows = 0
    for period, local_path in LOCAL_FILES.items():
        if not local_path.exists():
            print(f"[SKIP] ファイルが存在しません: {local_path}")
            continue

        # ファイルタイプに応じて変換関数を選択
        if period == PERIOD_DEC:
            df = load_and_transform_december(local_path, period)
        else:
            df = load_and_transform_normal(local_path, period)

        # 一時テーブルに挿入
        df.to_sql('temp_data', conn, if_exists='replace', index=False)

        # データを変換して挿入
        conn.execute('''
            INSERT INTO mapping_results (ej_order_no, rbom_order_no, rbom_line_no, rbom_quantity, rbom_m_sequence, status, period, hmcd)
            SELECT
                ej_order_no,
                rbom_order_no,
                CAST(rbom_line_no AS INTEGER),
                rbom_quantity,
                CAST(rbom_m_sequence AS INTEGER),
                status,
                period,
                hmcd
            FROM temp_data
        ''')

        # 一時テーブル削除
        conn.execute('DROP TABLE temp_data')

        print(f"[OK] {period}: {len(df)}行")
        total_rows += len(df)

    # インデックス作成
    conn.execute('CREATE INDEX idx_ej_order_no ON mapping_results(ej_order_no)')
    conn.execute('CREATE INDEX idx_rbom_order_no ON mapping_results(rbom_order_no)')
    conn.execute('CREATE INDEX idx_period ON mapping_results(period)')

    # 更新履歴テーブル
    conn.execute('''
        CREATE TABLE IF NOT EXISTS update_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            updated_at TEXT
        )
    ''')
    conn.execute('INSERT INTO update_history (updated_at) VALUES (?)',
                 (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

    print(f"\n[完了] データベース: {DB_PATH}")
    print(f"総レコード数: {total_rows:,}")
    print(f"ファイルサイズ: {DB_PATH.stat().st_size:,} bytes")


def copy_db_to_destination():
    """データベースを別ディレクトリにコピー（サーバー環境のみ）"""
    print("\n" + "=" * 50)
    print("データベースコピー")
    print("=" * 50)

    # コピー先ディレクトリが存在しない場合はスキップ（開発環境）
    if not COPY_DEST_DIR.exists():
        print(f"[SKIP] コピー先ディレクトリが存在しません: {COPY_DEST_DIR}")
        print("       （サーバー環境でのみコピーが実行されます）")
        return

    try:
        shutil.copy2(DB_PATH, COPY_DEST_DB)
        print(f"[OK] コピー完了: {COPY_DEST_DB}")
        print(f"     ファイルサイズ: {COPY_DEST_DB.stat().st_size:,} bytes")
    except PermissionError:
        print(f"[ERROR] アクセス権限がありません: {COPY_DEST_DB}")
        raise
    except Exception as e:
        print(f"[ERROR] コピーに失敗しました: {e}")
        raise


def main():
    """メイン処理"""
    # ログ設定
    setup_logging()

    print(f"\n実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        copy_from_server()
        update_database()
        copy_db_to_destination()
        print("\n" + "=" * 50)
        print("更新完了")
        print("=" * 50)
    except Exception as e:
        print(f"\n[ERROR] 処理中にエラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    main()
