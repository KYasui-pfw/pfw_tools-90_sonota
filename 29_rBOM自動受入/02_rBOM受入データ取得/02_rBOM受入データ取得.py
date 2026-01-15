"""
rBOM受入データ取得スクリプト

pfw-api の /query エンドポイントを使用して
D3350（受入ファイル）とD3360（受入明細ファイル）を取得し、
RCVNOをキーに結合して出力する。

対象: INSTDT >= 2025/12/01
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import httpx
from dotenv import load_dotenv

# 設定
SCRIPT_DIR = Path(__file__).parent
WORK_DIR = SCRIPT_DIR / "work"
LOG_DIR = SCRIPT_DIR / "log"

# API設定
ENV_PATH = Path(r"C:\Dev\01_Back_APIServer\fastapi_app\.env")
API_BASE_URL = "http://pfw-api/query"

# 取得対象の開始日
TARGET_START_DATE = "2025-12-01"


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
    """7日以上前のログファイルを削除"""
    if not LOG_DIR.exists():
        return

    threshold = datetime.now() - timedelta(days=7)

    for log_file in LOG_DIR.glob("log_*.txt"):
        try:
            # ファイル名から日付を抽出
            date_str = log_file.stem.replace("log_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < threshold:
                log_file.unlink()
        except (ValueError, OSError):
            pass


# print関数をオーバーライドしてログに出力
original_print = print
def print(*args, **kwargs):
    message = " ".join(str(arg) for arg in args)
    logging.info(message)
    original_print(*args, **kwargs)


def load_api_key():
    """APIキーを読み込み"""
    load_dotenv(ENV_PATH)
    return os.getenv("READ_API_KEY")


def fetch_d3350(api_key):
    """
    D3350（受入ファイル）を取得
    INSTDT >= TARGET_START_DATE
    """
    print("")
    print("=" * 50)
    print("D3350（受入ファイル）取得")
    print("=" * 50)

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # D3350のカラム
    columns = [
        "RCVNO",      # 受入番号 (PK)
        "RCVDT",      # 受入日
        "PONO",       # 発注番号
        "RCVCNT",     # 受入回数
        "SRCD",       # 仕入先コード
        "SRTANNM",    # 仕入先担当者
        "SHCD",       # 支払先コード
        "SHBUCD",     # 支払事業部コード
        "DEPTCD",     # 受入部門コード
        "TANCD",      # 受入担当者コード
        "IPTANCD",    # 入力担当者コード
        "TAXKBN",     # 消費税計算区分
        "AMOUNT",     # 伝票金額合計
        "TAX",        # 伝票消費税合計
        "NOTE",       # 摘要
        "INSTDT",     # 登録日時
        "UPDTDT",     # 更新日時
    ]

    all_rows = []
    offset = 0
    batch_size = 10000

    with httpx.Client(timeout=120.0) as client:
        while True:
            payload = {
                "table": "D3350",
                "columns": columns,
                "where": {
                    "and": [
                        {"INSTDT": {"gte": TARGET_START_DATE}}
                    ]
                },
                "limit": batch_size,
                "offset": offset
            }

            try:
                response = client.post(API_BASE_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                rows = data.get("rows", [])
                if not rows:
                    break

                all_rows.extend(rows)
                print(f"  取得: {len(rows)}件 (累計: {len(all_rows)}件)")

                if len(rows) < batch_size:
                    break

                offset += batch_size

            except Exception as e:
                print(f"[ERROR] D3350取得エラー: {e}")
                import traceback
                print(traceback.format_exc())
                break

    df = pd.DataFrame(all_rows)
    print(f"D3350 取得完了: {len(df)}件")
    return df


def fetch_d3360(api_key):
    """
    D3360（受入明細ファイル）を取得
    INSTDT >= TARGET_START_DATE
    """
    print("")
    print("=" * 50)
    print("D3360（受入明細ファイル）取得")
    print("=" * 50)

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # D3360のカラム
    columns = [
        "RCVNO",      # 受入番号 (PK)
        "LINENO",     # 行番号 (PK)
        "TRKBN",      # 取引区分
        "PONO",       # 発注番号
        "POLINENO",   # 発注行番号
        "STATUS",     # 状態
        "RCVTSTKBN",  # 受入検査区分
        "RCVCHKKBN",  # 受入検収区分
        "EDKBN",      # 完納区分
        "RCVDT",      # 受入日
        "RCVTANCD",   # 受入担当者コード
        "TSTDT",      # 検査日
        "TSTTANCD",   # 検査担当者コード
        "CHKDT",      # 検収日
        "CHKTANCD",   # 検収担当者コード
        "RCVQTY",     # 受入数
        "RCVUNIT",    # 受入単位コード
        "INQTY",      # 入数
        "OKQTY",      # 良品数
        "NGQTY",      # 不良数
        "NGRSNCD",    # 不良理由コード
        "QTY",        # 検収量
        "UNIT",       # 単位コード
        "WEIGHT",     # 品目重量
        "TWEIGHT",    # 品目総重量
        "KPKBN",      # 仮単価区分
        "PKBN",       # 単価区分
        "PRICE",      # 単価
        "AMOUNT",     # 金額
        "TAXKBN",     # 消費税区分
        "TAX",        # 消費税
        "SEIBUCD",    # 製造事業部コード
        "SBCD",       # 勘定科目コード
        "CSBCD",      # 原価科目コード
        "ZILOTNO",    # 在庫ロット番号
        "NOTE",       # 備考
        "NOTAXAMT",   # 税抜金額
        "TAXRATE",    # 消費税率
        "KGZEIFLG",   # 軽減税率対象フラグ
        "INSTDT",     # 登録日時
        "UPDTDT",     # 更新日時
    ]

    all_rows = []
    offset = 0
    batch_size = 10000

    with httpx.Client(timeout=120.0) as client:
        while True:
            payload = {
                "table": "D3360",
                "columns": columns,
                "where": {
                    "and": [
                        {"INSTDT": {"gte": TARGET_START_DATE}}
                    ]
                },
                "limit": batch_size,
                "offset": offset
            }

            try:
                response = client.post(API_BASE_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                rows = data.get("rows", [])
                if not rows:
                    break

                all_rows.extend(rows)
                print(f"  取得: {len(rows)}件 (累計: {len(all_rows)}件)")

                if len(rows) < batch_size:
                    break

                offset += batch_size

            except Exception as e:
                print(f"[ERROR] D3360取得エラー: {e}")
                import traceback
                print(traceback.format_exc())
                break

    df = pd.DataFrame(all_rows)
    print(f"D3360 取得完了: {len(df)}件")
    return df


def join_and_export(df_d3350, df_d3360):
    """
    D3350とD3360をRCVNOで結合してCSV出力
    """
    print("")
    print("=" * 50)
    print("D3350・D3360結合・CSV出力")
    print("=" * 50)

    # workディレクトリを作成
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    if df_d3350.empty and df_d3360.empty:
        print("[WARN] D3350・D3360 両方が空です")
        return

    # 各テーブルを個別に出力
    if not df_d3350.empty:
        output_path = WORK_DIR / "02_D3350.csv"
        df_d3350.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] D3350: {len(df_d3350)}件 -> {output_path}")

    if not df_d3360.empty:
        output_path = WORK_DIR / "02_D3360.csv"
        df_d3360.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] D3360: {len(df_d3360)}件 -> {output_path}")

    # RCVNOで結合（INNER JOIN）
    if not df_d3350.empty and not df_d3360.empty:
        # D3350のカラムにサフィックスを付けて区別（NOTEなど重複するカラムがあるため）
        df_d3350_renamed = df_d3350.add_suffix('_H')
        df_d3350_renamed = df_d3350_renamed.rename(columns={'RCVNO_H': 'RCVNO'})

        # D3360のカラムにサフィックスを付けて区別
        df_d3360_renamed = df_d3360.add_suffix('_D')
        df_d3360_renamed = df_d3360_renamed.rename(columns={'RCVNO_D': 'RCVNO'})

        # INNER JOIN
        df_joined = df_d3360_renamed.merge(
            df_d3350_renamed,
            on='RCVNO',
            how='inner'
        )

        output_path = WORK_DIR / "02_D3350_D3360_結合.csv"
        df_joined.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[OK] 結合データ: {len(df_joined)}件 -> {output_path}")

        # サマリー
        print("")
        print("--- サマリー ---")
        print(f"D3350 RCVNO数: {df_d3350['RCVNO'].nunique()}")
        print(f"D3360 RCVNO数: {df_d3360['RCVNO'].nunique()}")
        print(f"結合後 RCVNO数: {df_joined['RCVNO'].nunique()}")
        print(f"結合後 行数: {len(df_joined)}")


def main():
    """メイン処理"""
    # ログ設定
    setup_logging()

    start_time = datetime.now()
    print("")
    print("=" * 50)
    print(f"rBOM受入データ取得 開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象: INSTDT >= {TARGET_START_DATE}")
    print("=" * 50)

    try:
        # APIキー読み込み
        api_key = load_api_key()
        if not api_key:
            print("[ERROR] READ_API_KEYが見つかりません")
            return 1

        # 1. D3350取得
        df_d3350 = fetch_d3350(api_key)

        # 2. D3360取得
        df_d3360 = fetch_d3360(api_key)

        # 3. 結合・CSV出力
        join_and_export(df_d3350, df_d3360)

    except Exception as e:
        print(f"[ERROR] 処理中にエラーが発生: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    print("")
    print("=" * 50)
    print(f"処理完了: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (所要時間: {elapsed:.1f}秒)")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
