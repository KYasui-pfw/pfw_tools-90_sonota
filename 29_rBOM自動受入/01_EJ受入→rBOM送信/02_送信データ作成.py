# -*- coding: utf-8 -*-
"""
02_送信データ作成.py
01_EJ受入データ.csvとmapping.dbを突合し、rBOM送信用データを作成する

処理内容:
  1. 01_EJ受入データ.csvを読み込む
  2. mapping.dbのmapping_resultsテーブルとMEINOTE=ej_order_noで照合
  3. 一致なし → 02_マッピングDBに発注番号無し.csv（対象外）
  4. 一致あり:
     - rbom_order_no → PONO
     - rbom_line_no → POLINENO
     - PONOが0埋め9桁でない → 02_rBOMに発注無し.csv（対象外）
  5. IPTANCD = "PFW-1320" 固定
  6. EDKBN判定:
     - ODR_CANCEL_SLIP_ISS_FLG=1or2 → EDKBN="2"
     - PUCH_ODR_STS_TYP=1or2 かつ FLG=0 → EDKBN="1"
     - PUCH_ODR_STS_TYP=9 かつ FLG=0 → 同一MEINOTEで最大ACPT_NOは"2"、それ以外"1"
  7. 出力:
     - EJ送信対象受入データ.csv: 全カラム出力
     - 02_送信データ.csv: EJ_列5つを除外して出力
"""

import sys
import os
import csv
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# =============================================================================
# 設定
# =============================================================================
# 入力ファイル
INPUT_CSV = "01_EJ受入データ.csv"
MAPPING_DB = "mapping.db"

# 出力ファイル
OUTPUT_CSV = "02_送信データ全件.csv"
OUTPUT_FULL_CSV = "02_EJ送信対象受入データ.csv"
OUTPUT_NO_MAPPING = "02_マッピングDBに発注番号無し.csv"
OUTPUT_NO_RBOM = "02_rBOMに発注無し.csv"

# 送信データから除外するEJ参照用カラム
# ※EJ_CREATED_DATEは03_フィルタリングで使用するため含める
EJ_COLUMNS = [
    "EJ_PUCH_ODR_CD", "EJ_ACPT_NO",
    "EJ_PUCH_ODR_STS_TYP", "EJ_ODR_CANCEL_SLIP_ISS_FLG"
]

# 固定値
IPTANCD = "PFW-1320"


# =============================================================================
# ロギング
# =============================================================================
def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# PONOバリデーション
# =============================================================================
def is_valid_pono(pono: str) -> bool:
    """
    PONOが0埋め9桁の数字かどうかを判定

    Args:
        pono: 発注番号

    Returns:
        True: 有効（0埋め9桁）
        False: 無効
    """
    if not pono:
        return False
    # 9桁の数字（0埋め）かどうか
    return bool(re.match(r'^\d{9}$', str(pono)))


# =============================================================================
# mapping.db読み込み
# =============================================================================
def load_mapping_data(db_path: Path) -> dict:
    """
    mapping.dbからmapping_resultsを読み込む

    Args:
        db_path: mapping.dbのパス

    Returns:
        dict: {ej_order_no: {"rbom_order_no": ..., "rbom_line_no": ...}, ...}
    """
    mapping = {}

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ej_order_no, rbom_order_no, rbom_line_no
                FROM mapping_results
                WHERE ej_order_no IS NOT NULL
                  AND rbom_order_no IS NOT NULL
            """)

            for row in cursor.fetchall():
                ej_order_no = row[0]
                rbom_order_no = row[1]
                rbom_line_no = row[2]

                # 同じej_order_noが複数ある場合は最初のものを使用
                if ej_order_no not in mapping:
                    mapping[ej_order_no] = {
                        "rbom_order_no": rbom_order_no,
                        "rbom_line_no": rbom_line_no
                    }

        log(f"mapping.db読み込み完了: {len(mapping)}件")
        return mapping

    except sqlite3.Error as e:
        log(f"SQLite接続エラー: {e}")
        raise


# =============================================================================
# メイン処理
# =============================================================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # カレントディレクトリをスクリプトの場所に変更
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # workディレクトリ
    work_dir = script_dir / "work"

    print("=" * 60)
    print("02_送信データ作成")
    print("=" * 60)

    # 入力ファイル確認
    input_csv_path = work_dir / INPUT_CSV
    mapping_db_path = work_dir / MAPPING_DB

    if not input_csv_path.exists():
        log(f"エラー: 入力ファイルが見つかりません: {input_csv_path}")
        return

    if not mapping_db_path.exists():
        log(f"エラー: mapping.dbが見つかりません: {mapping_db_path}")
        return

    # mapping.db読み込み
    log("mapping.db読み込み中...")
    mapping_data = load_mapping_data(mapping_db_path)

    # 入力CSV読み込み
    log(f"入力CSV読み込み中: {input_csv_path}")
    input_rows = []
    with open(input_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            input_rows.append(row)

    log(f"入力CSV読み込み完了: {len(input_rows)}件")

    # ==========================================================================
    # Phase 1: マッピング処理（PONO, POLINENO設定）
    # ==========================================================================
    mapped_rows = []       # マッピング成功
    no_mapping_rows = []   # 02_マッピングDBに発注番号無し.csv
    no_rbom_rows = []      # 02_rBOMに発注無し.csv

    for row in input_rows:
        meinote = row.get("MEINOTE", "").strip()

        # mapping.dbと照合
        if meinote not in mapping_data:
            # マッピングなし
            no_mapping_rows.append(row)
            continue

        # マッピングあり
        mapping_info = mapping_data[meinote]
        pono = mapping_info["rbom_order_no"]
        polineno = mapping_info["rbom_line_no"]

        # PONOバリデーション（0埋め9桁）
        if not is_valid_pono(pono):
            # rBOM発注番号が無効
            row["PONO"] = pono
            row["POLINENO"] = polineno
            no_rbom_rows.append(row)
            continue

        # 正常データ
        row["PONO"] = pono
        row["POLINENO"] = polineno
        mapped_rows.append(row)

    log(f"Phase1完了: マッピング成功={len(mapped_rows)}, マッピング無し={len(no_mapping_rows)}, rBOM発注無し={len(no_rbom_rows)}")

    # ==========================================================================
    # Phase 2: IPTANCD設定、EDKBN設定
    # ==========================================================================
    output_rows = []       # 送信対象

    # まず、MEINOTE毎に最大のEJ_ACPT_NOを特定
    # PUCH_ODR_STS_TYP=9 かつ 取消でない場合のみ対象
    meinote_max_acpt_no = defaultdict(int)
    for row in mapped_rows:
        meinote = row.get("MEINOTE", "").strip()
        sts_typ = str(row.get("EJ_PUCH_ODR_STS_TYP", "")).strip()
        cancel_flg = str(row.get("EJ_ODR_CANCEL_SLIP_ISS_FLG", "")).strip()

        # PUCH_ODR_STS_TYP=9 かつ 取消でない場合のみ最大ACPT_NOを追跡
        if sts_typ == "9" and cancel_flg == "0":
            try:
                acpt_no = int(row.get("EJ_ACPT_NO", 0))
                if acpt_no > meinote_max_acpt_no[meinote]:
                    meinote_max_acpt_no[meinote] = acpt_no
            except (ValueError, TypeError):
                pass

    # 各行を処理
    for row in mapped_rows:
        meinote = row.get("MEINOTE", "").strip()
        sts_typ = str(row.get("EJ_PUCH_ODR_STS_TYP", "")).strip()
        cancel_flg = str(row.get("EJ_ODR_CANCEL_SLIP_ISS_FLG", "")).strip()

        # IPTANCD設定
        row["IPTANCD"] = IPTANCD

        # MEINOTE設定（(原材料)EJ_PUCH_ODR_CD）
        ej_puch_odr_cd = row.get("EJ_PUCH_ODR_CD", "").strip()
        row["MEINOTE"] = f"(原材料){ej_puch_odr_cd}"

        # NOTE設定（EJ_PUCH_ODR_CD + EJ_ACPT_NO）
        ej_acpt_no = row.get("EJ_ACPT_NO", "").strip()
        row["NOTE"] = f"{ej_puch_odr_cd}{ej_acpt_no}"

        # EDKBN設定
        if cancel_flg in ("1", "2"):
            # 取消済み（ODR_CANCEL_SLIP_ISS_FLG = 1 or 2）→ EDKBN="2"
            row["EDKBN"] = "2"
        elif sts_typ in ("1", "2"):
            # PUCH_ODR_STS_TYP=1or2 → EDKBN="1"（分納）
            row["EDKBN"] = "1"
        elif sts_typ == "9":
            # PUCH_ODR_STS_TYP=9 → 最大ACPT_NOは"2"、それ以外"1"
            try:
                acpt_no = int(row.get("EJ_ACPT_NO", 0))
                if acpt_no == meinote_max_acpt_no[meinote]:
                    row["EDKBN"] = "2"  # 完納
                else:
                    row["EDKBN"] = "1"  # 分納
            except (ValueError, TypeError):
                row["EDKBN"] = "1"
        else:
            # その他のステータス → EDKBN="1"（デフォルト）
            row["EDKBN"] = "1"

        output_rows.append(row)

    log(f"Phase2完了: 送信対象={len(output_rows)}")

    # ==========================================================================
    # 出力
    # ==========================================================================
    # EJ送信対象受入データ.csv（全カラム）
    full_csv_path = work_dir / OUTPUT_FULL_CSV
    with open(full_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    log(f"出力: {full_csv_path} ({len(output_rows)}件)")

    # 02_送信データ.csv（EJ_列を除外）
    send_fieldnames = [f for f in fieldnames if f not in EJ_COLUMNS]
    output_csv_path = work_dir / OUTPUT_CSV
    with open(output_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=send_fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(output_rows)
    log(f"出力: {output_csv_path} ({len(output_rows)}件)")

    # 02_マッピングDBに発注番号無し.csv
    if no_mapping_rows:
        no_mapping_path = work_dir / OUTPUT_NO_MAPPING
        with open(no_mapping_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(no_mapping_rows)
        log(f"出力: {no_mapping_path} ({len(no_mapping_rows)}件)")

    # 02_rBOMに発注無し.csv
    if no_rbom_rows:
        no_rbom_path = work_dir / OUTPUT_NO_RBOM
        with open(no_rbom_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(no_rbom_rows)
        log(f"出力: {no_rbom_path} ({len(no_rbom_rows)}件)")

    print("=" * 60)
    print(f"完了:")
    print(f"  送信対象(全):   {len(output_rows)}件 → {OUTPUT_FULL_CSV}")
    print(f"  送信対象:       {len(output_rows)}件 → {OUTPUT_CSV}")
    print(f"  マッピング無し: {len(no_mapping_rows)}件 → {OUTPUT_NO_MAPPING}")
    print(f"  rBOM発注無し:   {len(no_rbom_rows)}件 → {OUTPUT_NO_RBOM}")
    print("=" * 60)


if __name__ == "__main__":
    main()
