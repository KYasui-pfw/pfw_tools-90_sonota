# -*- coding: utf-8 -*-
"""
スクリプト2: 受入API送信
中間CSVを読み込み、受入APIに送信する

入力CSV: EJNO, PONO, POLINENO, RCVQTY
送信データ:
  - EDKBN: "2" (完納固定)
  - IPTANCD: "PFW-1253" (固定)
  - RCVQTY: 中間CSVから
  - OKQTY: RCVQTYと同値
  - NGQTY: 0 (固定)
  - NOTE: 空欄
  - MEINOTE: "(原材料)" + EJNO
"""

import sys
import os
import csv
import httpx
from datetime import date, datetime

# =============================================================================
# 設定
# =============================================================================
API_BASE_URL = "http://pfw-api"
INSERT_API_KEY = "uV7$flb#AtMK"
TIMEOUT = 10.0

# 固定値
EDKBN = "2"          # 完納
IPTANCD = "PFW-1253" # 入力担当者コード
NGQTY = 0            # 不良数

# ファイル名
DEFAULT_INPUT_CSV = "intermediate.csv"
LOG_FILE = "02_send_log.txt"
ERROR_LOG_FILE = "02_send_error_log.txt"

# =============================================================================
# ロギング
# =============================================================================
def log(message: str, is_error: bool = False):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)

    log_file = ERROR_LOG_FILE if is_error else LOG_FILE
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


# =============================================================================
# API送信
# =============================================================================
def send_acceptance_record(
    pono: str,
    polineno: int,
    rcvqty: float,
    ejno: str
) -> dict:
    """
    受入実績をAPIに送信

    Args:
        pono: 発注番号
        polineno: 発注行番号
        rcvqty: 受入数
        ejno: EJ番号（MEINOTE用）

    Returns:
        APIレスポンス
    """
    headers = {
        "X-API-KEY": INSERT_API_KEY,
        "Content-Type": "application/json"
    }

    # MEINOTE: (原材料)EJNO
    meinote = f"(原材料){ejno}"

    # リクエストデータ
    data = {
        "EDKBN": EDKBN,
        "PONO": pono,
        "POLINENO": polineno,
        "RCVDT": date.today().isoformat(),
        "IPTANCD": IPTANCD,
        "RCVQTY": rcvqty,
        "OKQTY": rcvqty,
        "NGQTY": NGQTY,
        "MEINOTE": meinote
    }

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(
                f"{API_BASE_URL}/acceptance/",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        return {"success": False, "error": str(e), "detail": error_detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# メイン処理
# =============================================================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # カレントディレクトリをスクリプトの場所に変更
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # コマンドライン引数
    input_csv = DEFAULT_INPUT_CSV
    dry_run = False

    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
        elif not arg.startswith("-"):
            input_csv = arg

    print("=" * 60)
    print("スクリプト2: 受入API送信")
    print(f"入力CSV: {input_csv}")
    print(f"APIサーバー: {API_BASE_URL}")
    print(f"Dry Run: {dry_run}")
    print(f"固定値: EDKBN={EDKBN}, IPTANCD={IPTANCD}, NGQTY={NGQTY}")
    print("=" * 60)

    if not os.path.exists(input_csv):
        log(f"エラー: 入力ファイルが見つかりません: {input_csv}", is_error=True)
        return

    success_count = 0
    error_count = 0

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                ejno = row.get("EJNO", "").strip()
                pono_raw = row.get("PONO", "").strip()
                # PONOを9桁にゼロ埋め
                pono = pono_raw.zfill(9)
                polineno_str = row.get("POLINENO", "").strip()
                rcvqty_str = row.get("RCVQTY", "").strip()

                if not ejno or not pono or not polineno_str or not rcvqty_str:
                    log(f"行{row_num}: 必須項目不足 EJNO={ejno}, PONO={pono}, POLINENO={polineno_str}, RCVQTY={rcvqty_str}", is_error=True)
                    error_count += 1
                    continue

                polineno = int(polineno_str)
                rcvqty = float(rcvqty_str)

                meinote = f"(原材料){ejno}"
                log(f"行{row_num}: PONO={pono}, POLINENO={polineno}, RCVQTY={rcvqty}, MEINOTE={meinote}")

                if dry_run:
                    log(f"行{row_num}: [DRY RUN] APIコールをスキップ")
                    success_count += 1
                    continue

                # API送信
                result = send_acceptance_record(
                    pono=pono,
                    polineno=polineno,
                    rcvqty=rcvqty,
                    ejno=ejno
                )

                if result["success"]:
                    log(f"行{row_num}: 送信成功")
                    success_count += 1
                else:
                    log(f"行{row_num}: 送信失敗 - {result.get('error', '')} {result.get('detail', '')}", is_error=True)
                    error_count += 1

            except ValueError as e:
                log(f"行{row_num}: データ変換エラー - {e}", is_error=True)
                error_count += 1
            except Exception as e:
                log(f"行{row_num}: 予期せぬエラー - {e}", is_error=True)
                error_count += 1

    log(f"処理完了: 成功={success_count}, 失敗={error_count}")
    print("=" * 60)
    print(f"完了: 成功={success_count}, 失敗={error_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
