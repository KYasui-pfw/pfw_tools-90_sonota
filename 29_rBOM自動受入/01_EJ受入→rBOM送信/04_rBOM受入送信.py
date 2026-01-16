# -*- coding: utf-8 -*-
"""
03_rBOM受入送信.py
02_送信データ.csvを読み込み、rBOM受入APIに送信する

入力CSV: 02_送信データ.csv
  - EDKBN, RCVDT, PONO, POLINENO, IPTANCD, RCVQTY, OKQTY, NGQTY, MEINOTE, NOTE

送信先: POST /acceptance/
"""

import sys
import os
import csv
import httpx
from datetime import datetime
from pathlib import Path

# =============================================================================
# 設定
# =============================================================================
API_BASE_URL = "http://pfw-api"
INSERT_API_KEY = "uV7$flb#AtMK"
TIMEOUT = 10.0

# 入力ファイル
INPUT_CSV = "03_送信データ.csv"

# ログファイル
LOG_FILE = "04_send_log.txt"
ERROR_LOG_FILE = "04_send_error_log.txt"


# =============================================================================
# ロギング
# =============================================================================
def log(message: str, is_error: bool = False):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)

    # スクリプトディレクトリにログ出力
    script_dir = Path(__file__).parent
    log_file = script_dir / (ERROR_LOG_FILE if is_error else LOG_FILE)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


# =============================================================================
# API送信
# =============================================================================
def send_acceptance_record(
    edkbn: str,
    pono: str,
    polineno: int,
    rcvdt: str,
    iptancd: str,
    rcvqty: float,
    okqty: float,
    meinote: str,
    note: str
) -> dict:
    """
    受入実績をAPIに送信

    Args:
        edkbn: 完納区分（1=分納, 2=完納）
        pono: 発注番号
        polineno: 発注行番号
        rcvdt: 受入日（YYYY-MM-DD）
        iptancd: 入力担当者コード
        rcvqty: 受入数
        okqty: 良品数
        meinote: 明細備考
        note: 備考

    Returns:
        APIレスポンス
    """
    headers = {
        "X-API-KEY": INSERT_API_KEY,
        "Content-Type": "application/json"
    }

    # リクエストデータ
    data = {
        "EDKBN": edkbn,
        "PONO": pono,
        "POLINENO": polineno,
        "RCVDT": rcvdt,
        "IPTANCD": iptancd,
        "RCVQTY": rcvqty,
        "OKQTY": okqty,
        "MEINOTE": meinote,
        "NOTE": note
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
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # workディレクトリ
    work_dir = script_dir / "work"

    # コマンドライン引数
    input_csv = work_dir / INPUT_CSV
    dry_run = False

    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
        elif not arg.startswith("-"):
            input_csv = Path(arg)

    print("=" * 60)
    print("03_rBOM受入送信")
    print(f"入力CSV: {input_csv}")
    print(f"APIサーバー: {API_BASE_URL}")
    print(f"Dry Run: {dry_run}")
    print("=" * 60)

    if not input_csv.exists():
        log(f"エラー: 入力ファイルが見つかりません: {input_csv}", is_error=True)
        return

    success_count = 0
    error_count = 0

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                # 必須項目取得
                edkbn = row.get("EDKBN", "").strip()
                pono = row.get("PONO", "").strip()
                polineno_str = row.get("POLINENO", "").strip()
                rcvdt = row.get("RCVDT", "").strip()
                iptancd = row.get("IPTANCD", "").strip()
                rcvqty_str = row.get("RCVQTY", "").strip()
                okqty_str = row.get("OKQTY", "").strip()
                meinote = row.get("MEINOTE", "").strip()
                note = row.get("NOTE", "").strip()

                # バリデーション
                if not edkbn or not pono or not polineno_str or not rcvdt or not rcvqty_str:
                    log(f"行{row_num}: 必須項目不足 EDKBN={edkbn}, PONO={pono}, POLINENO={polineno_str}, RCVDT={rcvdt}, RCVQTY={rcvqty_str}", is_error=True)
                    error_count += 1
                    continue

                polineno = int(polineno_str)
                rcvqty = float(rcvqty_str)
                okqty = float(okqty_str) if okqty_str else rcvqty

                log(f"行{row_num}: EDKBN={edkbn}, PONO={pono}, POLINENO={polineno}, RCVDT={rcvdt}, RCVQTY={rcvqty}, MEINOTE={meinote}")

                if dry_run:
                    log(f"行{row_num}: [DRY RUN] APIコールをスキップ")
                    success_count += 1
                    continue

                # API送信
                result = send_acceptance_record(
                    edkbn=edkbn,
                    pono=pono,
                    polineno=polineno,
                    rcvdt=rcvdt,
                    iptancd=iptancd,
                    rcvqty=rcvqty,
                    okqty=okqty,
                    meinote=meinote,
                    note=note
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
