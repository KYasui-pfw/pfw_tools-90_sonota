# -*- coding: utf-8 -*-
"""
04_購入単価突合.py
CSVの「カム課_子部番」をキーにEJサーバーのM_PUCH_UNIT_COST/M_PUCH_UNIT_COST_Hと突合

処理内容:
  1. CSVの「カム課_子部番」= M_PUCH_UNIT_COST.ITEM_CD で完全一致
  2. M_PUCH_UNIT_COST と M_PUCH_UNIT_COST_H を INNER JOIN
  3. 絞り込み:
     - その1: PUCH_PRIORITY_REF_NO が最小
     - その2: EFF_PHASE_IN_DATE が最新 かつ PUCH_SIZE が最小
     - その3: それでも2行以上あれば最初の行
  4. 取得カラム: PUCH_PRIORITY_REF_NO, EFF_PHASE_IN_DATE, PUCH_SIZE, VEND_CD, UNIT_COST

出力:
  - 一致: work/04_カム課データ_購入単価付き.csv
  - 不一致: work/04_カム課データ_購入単価不一致.csv
"""

import sys
import csv
import oracledb
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# 設定
# =============================================================================
# EJシステム接続情報
EJ_HOST = "172.17.107.102"
EJ_PORT = 1521
EJ_SERVICE = "EXPJ"
EJ_USER = "EXPJ2"
EJ_PASSWORD = "EXPJ2"

# 入力ファイル
INPUT_CSV = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work\02_5_カム課データ_重複削除.csv")

# 出力ファイル
OUTPUT_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work")
OUTPUT_MATCHED = OUTPUT_DIR / "04_カム課データ_購入単価付き.csv"
OUTPUT_UNMATCHED = OUTPUT_DIR / "04_カム課データ_購入単価不一致.csv"

# oracledb thick mode初期化フラグ
_thick_mode_initialized = False


# =============================================================================
# ロギング
# =============================================================================
def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# Oracle接続
# =============================================================================
def init_oracle_thick_mode():
    """Oracle thick modeを初期化"""
    global _thick_mode_initialized
    if not _thick_mode_initialized:
        try:
            oracledb.init_oracle_client()
            _thick_mode_initialized = True
            log("oracledb thick mode初期化完了")
        except Exception as e:
            log(f"thick mode初期化スキップ: {e}")


def get_ej_connection():
    """EJシステムへの接続を取得"""
    init_oracle_thick_mode()
    dsn = oracledb.makedsn(EJ_HOST, EJ_PORT, service_name=EJ_SERVICE)
    return oracledb.connect(user=EJ_USER, password=EJ_PASSWORD, dsn=dsn)


# =============================================================================
# 購入単価データ取得
# =============================================================================
def fetch_unit_cost_data(item_codes: list) -> dict:
    """
    M_PUCH_UNIT_COST と M_PUCH_UNIT_COST_H を結合してデータ取得

    Args:
        item_codes: 検索対象の品目コードリスト

    Returns:
        dict: {ITEM_CD: [(PUCH_PRIORITY_REF_NO, EFF_PHASE_IN_DATE, PUCH_SIZE, VEND_CD, UNIT_COST), ...]}
    """
    if not item_codes:
        return {}

    log(f"EJサーバーから購入単価データを取得中... (対象: {len(item_codes)}件)")

    # 重複除去
    unique_codes = list(set([code for code in item_codes if code]))
    if not unique_codes:
        return {}

    log(f"ユニークな品目コード: {len(unique_codes)}件")

    result = defaultdict(list)

    conn = get_ej_connection()
    try:
        cursor = conn.cursor()

        # バッチサイズ（IN句の制限対策）
        batch_size = 500

        for i in range(0, len(unique_codes), batch_size):
            batch = unique_codes[i:i + batch_size]
            placeholders = ','.join([f':p{j}' for j in range(len(batch))])

            sql = f"""
                SELECT
                    c.ITEM_CD,
                    h.PUCH_PRIORITY_REF_NO,
                    c.EFF_PHASE_IN_DATE,
                    c.PUCH_SIZE,
                    c.VEND_CD,
                    c.UNIT_COST
                FROM EXPJ2.M_PUCH_UNIT_COST c
                INNER JOIN EXPJ2.M_PUCH_UNIT_COST_H h
                    ON c.COMPANY_CD = h.COMPANY_CD
                    AND c.VEND_CD = h.VEND_CD
                    AND c.ITEM_CD = h.ITEM_CD
                    AND c.PLANT_CD = h.PLANT_CD
                WHERE c.ITEM_CD IN ({placeholders})
                ORDER BY c.ITEM_CD, h.PUCH_PRIORITY_REF_NO, c.EFF_PHASE_IN_DATE DESC, c.PUCH_SIZE
            """

            params = {f'p{j}': code for j, code in enumerate(batch)}
            cursor.execute(sql, params)

            for row in cursor:
                item_cd = row[0]
                result[item_cd].append({
                    'PUCH_PRIORITY_REF_NO': row[1],
                    'EFF_PHASE_IN_DATE': row[2],
                    'PUCH_SIZE': row[3],
                    'VEND_CD': row[4],
                    'UNIT_COST': row[5]
                })

            log(f"  バッチ {i // batch_size + 1}: {len(batch)}件処理完了")

        log(f"購入単価データ取得完了: {len(result)}品目")

    finally:
        conn.close()

    return result


def select_best_record(records: list) -> dict:
    """
    絞り込みルールに従って最適なレコードを選択

    絞り込み順序:
      1. PUCH_PRIORITY_REF_NO が最小
      2. EFF_PHASE_IN_DATE が最新 かつ PUCH_SIZE が最小
      3. それでも2行以上あれば最初の行

    Args:
        records: 同一ITEM_CDのレコードリスト

    Returns:
        dict: 選択されたレコード
    """
    if not records:
        return None

    if len(records) == 1:
        return records[0]

    # その1: PUCH_PRIORITY_REF_NO が最小
    min_priority = min(r['PUCH_PRIORITY_REF_NO'] for r in records if r['PUCH_PRIORITY_REF_NO'] is not None)
    filtered = [r for r in records if r['PUCH_PRIORITY_REF_NO'] == min_priority]

    if len(filtered) == 1:
        return filtered[0]

    # その2: EFF_PHASE_IN_DATE が最新
    max_date = max(r['EFF_PHASE_IN_DATE'] for r in filtered if r['EFF_PHASE_IN_DATE'] is not None)
    filtered = [r for r in filtered if r['EFF_PHASE_IN_DATE'] == max_date]

    if len(filtered) == 1:
        return filtered[0]

    # その2続き: PUCH_SIZE が最小
    min_size = min(r['PUCH_SIZE'] for r in filtered if r['PUCH_SIZE'] is not None)
    filtered = [r for r in filtered if r['PUCH_SIZE'] == min_size]

    # その3: それでも2行以上あれば最初の行
    return filtered[0]


# =============================================================================
# メイン処理
# =============================================================================
def main():
    log("=" * 60)
    log("04_購入単価突合")
    log(f"入力: {INPUT_CSV}")
    log(f"出力(一致): {OUTPUT_MATCHED}")
    log(f"出力(不一致): {OUTPUT_UNMATCHED}")
    log("=" * 60)

    # 入力ファイル確認
    if not INPUT_CSV.exists():
        log(f"エラー: 入力ファイルが見つかりません: {INPUT_CSV}")
        return False

    # 出力ディレクトリ確認
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # CSVを読み込み
    log("CSVファイルを読み込み中...")
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        original_fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    log(f"CSV読み込み完了: {len(rows)}行")

    # カム課_子部番を収集
    item_codes = [row.get('カム課_子部番', '') for row in rows]

    # EJから購入単価データ取得
    unit_cost_data = fetch_unit_cost_data(item_codes)

    # 突合処理
    log("突合処理中...")
    matched_rows = []
    unmatched_rows = []

    # 追加カラム
    additional_columns = ['EJ_PUCH_PRIORITY_REF_NO', 'EJ_EFF_PHASE_IN_DATE', 'EJ_PUCH_SIZE', 'EJ_VEND_CD', 'EJ_UNIT_COST']

    for row in rows:
        child_buban = row.get('カム課_子部番', '')

        if child_buban and child_buban in unit_cost_data:
            # 一致: 最適なレコードを選択
            records = unit_cost_data[child_buban]
            best = select_best_record(records)

            if best:
                row['EJ_PUCH_PRIORITY_REF_NO'] = best['PUCH_PRIORITY_REF_NO']
                row['EJ_EFF_PHASE_IN_DATE'] = best['EFF_PHASE_IN_DATE'].strftime('%Y-%m-%d') if best['EFF_PHASE_IN_DATE'] else ''
                row['EJ_PUCH_SIZE'] = best['PUCH_SIZE']
                row['EJ_VEND_CD'] = best['VEND_CD']
                row['EJ_UNIT_COST'] = best['UNIT_COST']
                matched_rows.append(row)
            else:
                # レコードはあるが選択できなかった（通常は起こらない）
                for col in additional_columns:
                    row[col] = ''
                unmatched_rows.append(row)
        else:
            # 不一致
            for col in additional_columns:
                row[col] = ''
            unmatched_rows.append(row)

    log(f"突合完了: 一致={len(matched_rows)}件, 不一致={len(unmatched_rows)}件")

    # 出力カラム
    output_fieldnames = list(original_fieldnames) + additional_columns

    # 一致データ出力
    log(f"一致データを出力中: {OUTPUT_MATCHED}")
    with open(OUTPUT_MATCHED, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(matched_rows)

    # 不一致データ出力
    log(f"不一致データを出力中: {OUTPUT_UNMATCHED}")
    with open(OUTPUT_UNMATCHED, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(unmatched_rows)

    log("=" * 60)
    log("処理完了")
    log(f"  一致: {len(matched_rows)}件 → {OUTPUT_MATCHED.name}")
    log(f"  不一致: {len(unmatched_rows)}件 → {OUTPUT_UNMATCHED.name}")
    log("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
