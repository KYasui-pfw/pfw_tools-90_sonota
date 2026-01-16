# -*- coding: utf-8 -*-
"""
01_EJ受入データ変換.py
EJシステム（T_ACPT_RSLT）から受入実績データを取得し、rBOM送信用CSVを作成する

抽出条件:
  - T_ACPT_RSLT.CREATED_DATE >= 2025/12/01 00:00:00

出力CSV項目:
  - EDKBN: 空欄 (後工程で設定)
  - RCVDT: T_ACPT_RSLT.ACPT_DATE
  - PONO: 空欄 (後工程で設定)
  - POLINENO: 空欄 (後工程で設定)
  - IPTANCD: 空欄 (後工程で設定)
  - RCVQTY: T_ACPT_RSLT.ACPT_QTY
  - OKQTY: T_ACPT_RSLT.ACPT_QTY
  - NGQTY: 0 (固定)
  - MEINOTE: PUCH_ODR_CD
  - NOTE: 空欄
"""

import sys
import os
import csv
import oracledb
from datetime import datetime
from pathlib import Path

# =============================================================================
# 設定
# =============================================================================
# EJシステム接続情報
EJ_HOST = "172.17.107.102"
EJ_PORT = 1521
EJ_SERVICE = "EXPJ"
EJ_USER = "EXPJ2"
EJ_PASSWORD = "EXPJ2"

# oracledb thick mode初期化フラグ
_ej_thick_mode_initialized = False


def init_oracle_thick_mode():
    """Oracle thick modeを初期化"""
    global _ej_thick_mode_initialized
    if not _ej_thick_mode_initialized:
        try:
            oracledb.init_oracle_client()
            _ej_thick_mode_initialized = True
            log("oracledb thick mode初期化完了")
        except Exception as e:
            log(f"thick mode初期化スキップ: {e}")

# 抽出開始日
EXTRACT_START_DATE = datetime(2025, 12, 1, 0, 0, 0)

# 出力ファイル
OUTPUT_CSV = "01_EJ受入データ.csv"

# =============================================================================
# ロギング
# =============================================================================
def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# EJデータ取得
# =============================================================================
def fetch_ej_acceptance_data() -> list:
    """
    EJシステムからT_ACPT_RSLTのデータを取得

    Returns:
        list: 受入実績データのリスト
    """
    # thick mode初期化
    init_oracle_thick_mode()

    dsn = oracledb.makedsn(EJ_HOST, EJ_PORT, service_name=EJ_SERVICE)

    sql = """
        SELECT
            A.PUCH_ODR_CD,
            A.ACPT_NO,
            A.ACPT_DATE,
            A.ACPT_QTY,
            A.CREATED_DATE,
            O.PUCH_ODR_STS_TYP,
            O.ODR_CANCEL_SLIP_ISS_FLG
        FROM
            EXPJ2.T_ACPT_RSLT A
            LEFT JOIN EXPJ2.T_RLSD_PUCH_ODR O
                ON A.PUCH_ODR_CD = O.PUCH_ODR_CD
        WHERE
            A.CREATED_DATE >= :start_date
        ORDER BY
            A.PUCH_ODR_CD,
            A.ACPT_NO
    """

    results = []

    try:
        with oracledb.connect(user=EJ_USER, password=EJ_PASSWORD, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"start_date": EXTRACT_START_DATE})
                columns = [col[0] for col in cursor.description]

                for row in cursor:
                    results.append(dict(zip(columns, row)))

        log(f"EJデータ取得完了: {len(results)}件")
        return results

    except oracledb.Error as e:
        log(f"Oracle接続エラー: {e}")
        raise


# =============================================================================
# CSV出力
# =============================================================================
def write_output_csv(data: list, output_path: Path):
    """
    rBOM送信用CSVを出力

    Args:
        data: EJから取得したデータ
        output_path: 出力ファイルパス
    """
    # 出力カラム
    output_columns = [
        "EDKBN", "RCVDT", "PONO", "POLINENO", "IPTANCD",
        "RCVQTY", "OKQTY", "NGQTY", "MEINOTE", "NOTE",
        # 参照用（EJ元データ）
        "EJ_PUCH_ODR_CD", "EJ_ACPT_NO", "EJ_CREATED_DATE",
        "EJ_PUCH_ODR_STS_TYP", "EJ_ODR_CANCEL_SLIP_ISS_FLG"
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()

        for row in data:
            # ACPT_DATEのフォーマット（日付のみ）
            acpt_date = row.get("ACPT_DATE")
            if acpt_date:
                if isinstance(acpt_date, datetime):
                    rcvdt = acpt_date.strftime("%Y-%m-%d")
                else:
                    rcvdt = str(acpt_date)[:10]
            else:
                rcvdt = ""

            # CREATED_DATEのフォーマット
            created_date = row.get("CREATED_DATE")
            if created_date:
                if isinstance(created_date, datetime):
                    created_date_str = created_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_date_str = str(created_date)
            else:
                created_date_str = ""

            output_row = {
                "EDKBN": "",
                "RCVDT": rcvdt,
                "PONO": "",
                "POLINENO": "",
                "IPTANCD": "",
                "RCVQTY": row.get("ACPT_QTY", 0),
                "OKQTY": row.get("ACPT_QTY", 0),
                "NGQTY": 0,
                "MEINOTE": row.get("PUCH_ODR_CD", ""),
                "NOTE": "",
                # 参照用
                "EJ_PUCH_ODR_CD": row.get("PUCH_ODR_CD", ""),
                "EJ_ACPT_NO": row.get("ACPT_NO", ""),
                "EJ_CREATED_DATE": created_date_str,
                "EJ_PUCH_ODR_STS_TYP": row.get("PUCH_ODR_STS_TYP", ""),
                "EJ_ODR_CANCEL_SLIP_ISS_FLG": row.get("ODR_CANCEL_SLIP_ISS_FLG", "")
            }
            writer.writerow(output_row)

    log(f"CSV出力完了: {output_path} ({len(data)}件)")


# =============================================================================
# メイン処理
# =============================================================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # カレントディレクトリをスクリプトの場所に変更
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # workディレクトリ確認
    work_dir = script_dir / "work"
    if not work_dir.exists():
        work_dir.mkdir(parents=True)
        log(f"workディレクトリ作成: {work_dir}")

    print("=" * 60)
    print("01_EJ受入データ変換")
    print(f"抽出条件: CREATED_DATE >= {EXTRACT_START_DATE}")
    print("=" * 60)

    try:
        # EJデータ取得
        log("EJデータ取得中...")
        ej_data = fetch_ej_acceptance_data()

        if not ej_data:
            log("対象データがありません")
            print("=" * 60)
            print("完了: 対象データなし")
            print("=" * 60)
            return

        # CSV出力
        output_path = work_dir / OUTPUT_CSV
        write_output_csv(ej_data, output_path)

        print("=" * 60)
        print(f"完了: {output_path}")
        print(f"件数: {len(ej_data)}")
        print("=" * 60)

    except Exception as e:
        log(f"エラー: {e}")
        raise


if __name__ == "__main__":
    main()
