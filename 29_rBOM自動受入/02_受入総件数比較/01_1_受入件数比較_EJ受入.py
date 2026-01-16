# -*- coding: utf-8 -*-
"""
01_受入件数比較_EJ受入.py
EJシステムの受入実績をITEM_CD単位・月別に集計する

処理内容:
  1. T_RLSD_PUCH_ODRとT_ACPT_RSLTをPUCH_ODR_CDで結合
  2. ACPT_DATE >= 2025/12/01 のデータを抽出
  3. 月別・ITEM_CD別にACPT_QTYを集計
  4. 月ごとにCSV出力

出力CSV項目:
  - ITEM_CD: 品目コード
  - ACPT_QTY_SUM: 受入数量合計
  - PUCH_ODR_CD_LIST: 集計対象の発注番号一覧（カンマ区切り）
"""

import sys
import os
import csv
import oracledb
from datetime import datetime
from pathlib import Path
from collections import defaultdict

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
EXTRACT_START_DATE = datetime(2025, 12, 1)

# 出力ファイル名プレフィックス
OUTPUT_PREFIX = "01_1_受入件数比較_EJ受入"


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
def fetch_ej_data() -> list:
    """
    EJシステムからT_ACPT_RSLTとT_RLSD_PUCH_ODRを結合してデータを取得

    Returns:
        list: 受入実績データのリスト
    """
    init_oracle_thick_mode()

    dsn = oracledb.makedsn(EJ_HOST, EJ_PORT, service_name=EJ_SERVICE)

    sql = """
        SELECT
            O.ITEM_CD,
            A.PUCH_ODR_CD,
            A.ACPT_DATE,
            A.ACPT_QTY
        FROM
            EXPJ2.T_ACPT_RSLT A
            INNER JOIN EXPJ2.T_RLSD_PUCH_ODR O
                ON A.PUCH_ODR_CD = O.PUCH_ODR_CD
        WHERE
            A.ACPT_DATE >= :start_date
        ORDER BY
            O.ITEM_CD,
            A.ACPT_DATE
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
# データ集計
# =============================================================================
def aggregate_by_month_and_item(data: list) -> dict:
    """
    月別・ITEM_CD別にデータを集計

    Args:
        data: EJから取得したデータ

    Returns:
        dict: {YYYYMM: {ITEM_CD: {"qty": 合計数量, "orders": [発注番号リスト]}}}
    """
    result = defaultdict(lambda: defaultdict(lambda: {"qty": 0, "orders": set()}))

    for row in data:
        acpt_date = row.get("ACPT_DATE")
        item_cd = row.get("ITEM_CD", "")
        acpt_qty = row.get("ACPT_QTY", 0) or 0
        puch_odr_cd = row.get("PUCH_ODR_CD", "")

        if not acpt_date or not item_cd:
            continue

        # YYYYMM形式の年月を取得
        if isinstance(acpt_date, datetime):
            yyyymm = acpt_date.strftime("%Y%m")
        else:
            yyyymm = str(acpt_date)[:7].replace("-", "")

        # 集計
        result[yyyymm][item_cd]["qty"] += float(acpt_qty)
        result[yyyymm][item_cd]["orders"].add(puch_odr_cd)

    return result


# =============================================================================
# CSV出力
# =============================================================================
def write_monthly_csv(aggregated_data: dict, work_dir: Path):
    """
    月別CSVを出力

    Args:
        aggregated_data: 集計済みデータ
        work_dir: 出力先ディレクトリ
    """
    output_columns = ["ITEM_CD", "ACPT_QTY_SUM", "PUCH_ODR_CD_LIST"]

    for yyyymm, items in sorted(aggregated_data.items()):
        output_path = work_dir / f"{OUTPUT_PREFIX}_{yyyymm}.csv"

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=output_columns)
            writer.writeheader()

            for item_cd in sorted(items.keys()):
                item_data = items[item_cd]
                writer.writerow({
                    "ITEM_CD": item_cd,
                    "ACPT_QTY_SUM": item_data["qty"],
                    "PUCH_ODR_CD_LIST": ",".join(sorted(item_data["orders"]))
                })

        log(f"出力: {output_path} ({len(items)}件)")


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
    print("01_受入件数比較_EJ受入")
    print(f"抽出条件: ACPT_DATE >= {EXTRACT_START_DATE.strftime('%Y-%m-%d')}")
    print("=" * 60)

    try:
        # EJデータ取得
        log("EJデータ取得中...")
        ej_data = fetch_ej_data()

        if not ej_data:
            log("対象データがありません")
            print("=" * 60)
            print("完了: 対象データなし")
            print("=" * 60)
            return

        # 月別・ITEM_CD別に集計
        log("データ集計中...")
        aggregated = aggregate_by_month_and_item(ej_data)

        # 月別CSV出力
        write_monthly_csv(aggregated, work_dir)

        print("=" * 60)
        print("完了:")
        for yyyymm in sorted(aggregated.keys()):
            print(f"  {yyyymm}: {len(aggregated[yyyymm])}品目")
        print("=" * 60)

    except Exception as e:
        log(f"エラー: {e}")
        raise


if __name__ == "__main__":
    main()
