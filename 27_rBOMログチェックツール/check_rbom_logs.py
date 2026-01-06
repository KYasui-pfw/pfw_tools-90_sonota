"""
rBOMログチェックツール
- yac010bat, yac020bat のログファイルを確認
- 前日のログが10KB以上で存在するかチェック
- ログ内のエラー行を抽出
- 月替わり時にログをzip圧縮してバックアップ
"""

import os
import shutil
import zipfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# 設定
LOG_CONFIGS = [
    {
        "name": "yac010",
        "path": r"\\esrv11\rbom\rBOM_bat\PFW\log\yac010\PATH",
        "file_pattern": "yac010bat_{date}.log",
        "min_size_kb": 10,
    },
    {
        "name": "yac020",
        "path": r"\\esrv11\rbom\rBOM_bat\PFW\log\yac020\PATH",
        "file_pattern": "yac020bat_{date}.log",
        "min_size_kb": 10,
    },
]

# エラー検索キーワード
ERROR_KEYWORDS = [
    "error", "Error", "ERROR",
    "エラー", "異常", "失敗",
    "exception", "Exception",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")
FULL_BACKUP_DIR = os.path.join(BASE_DIR, "全ログbackup")
FULL_BACKUP_COPY_DIR = r"D:\rBOM_log"
SHARE_DIR = r"\\fsrv24\rbom\夜間処理ログ"
SHARE_RETENTION_DAYS = 7  # 共有フォルダの保持日数

# 全ログバックアップ対象ファイル
# {date} は YYYYMMDD に置換される。None の場合は日付なしのファイル
FULL_BACKUP_FILES = [
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\i-Reporter\KOUTEIKANRYO", "i-Reporterデータ取込（工程完了）_{date}.log"),
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\i-Reporter\TANADASHI", "i-Reporterデータ取込（棚出）_{date}.log"),
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\i-Reporter\UKEIRE", "i-Reporterデータ取込（受入）_{date}.log"),
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\yac010\PATH", "yac010bat_{date}.log"),
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\yac020\PATH", "yac020bat_{date}.log"),
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\yac040", "yac040.log"),  # 日付なし
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\yac050", "yac050.log"),  # 日付なし
    (r"\\esrv11\rbom\rBOM_bat\PFW\log\yac060", "yac060.log"),  # 日付なし
]


def get_yesterday_jst() -> datetime:
    """日本時間で前日の日付を取得"""
    jst = ZoneInfo("Asia/Tokyo")
    now_jst = datetime.now(jst)
    yesterday = now_jst - timedelta(days=1)
    return yesterday


def ensure_directories():
    """必要なディレクトリを作成"""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(FULL_BACKUP_DIR, exist_ok=True)


def copy_to_share(source_path: str):
    """ログファイルを共有フォルダにコピー"""
    if not os.path.exists(SHARE_DIR):
        print(f"警告: 共有フォルダにアクセスできません: {SHARE_DIR}")
        return False

    filename = os.path.basename(source_path)
    dest_path = os.path.join(SHARE_DIR, filename)

    try:
        shutil.copy2(source_path, dest_path)
        print(f"共有フォルダにコピーしました: {dest_path}")
        return True
    except Exception as e:
        print(f"警告: 共有フォルダへのコピーに失敗しました: {e}")
        return False


def cleanup_old_logs_in_share():
    """共有フォルダの古いログファイルを削除（1週間以上前のファイル）"""
    if not os.path.exists(SHARE_DIR):
        return

    jst = ZoneInfo("Asia/Tokyo")
    now = datetime.now(jst)
    cutoff_date = now - timedelta(days=SHARE_RETENTION_DAYS)

    deleted_count = 0
    for filename in os.listdir(SHARE_DIR):
        if not filename.startswith("rBOMログチェック_") or not filename.endswith(".log"):
            continue

        # ファイル名から日付を抽出: rBOMログチェック_YYYYMMDD.log
        try:
            date_str = filename.replace("rBOMログチェック_", "").replace(".log", "")
            file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=jst)

            if file_date < cutoff_date:
                filepath = os.path.join(SHARE_DIR, filename)
                os.remove(filepath)
                deleted_count += 1
        except ValueError:
            continue  # 日付形式が不正なファイルはスキップ

    if deleted_count > 0:
        print(f"共有フォルダの古いログを削除しました: {deleted_count}件")


def backup_all_logs(target_date: datetime):
    """対象日の全ログファイルをzipにまとめてバックアップ"""
    date_str = target_date.strftime("%Y%m%d")
    zip_filename = f"rBOMログ_{date_str}.zip"
    zip_path = os.path.join(FULL_BACKUP_DIR, zip_filename)

    # 既に存在する場合はスキップ
    if os.path.exists(zip_path):
        print(f"全ログバックアップは既に存在します: {zip_filename}")
        return

    collected_files = []
    missing_files = []

    for dir_path, file_pattern in FULL_BACKUP_FILES:
        # {date} を置換
        if "{date}" in file_pattern:
            filename = file_pattern.replace("{date}", date_str)
        else:
            filename = file_pattern

        filepath = os.path.join(dir_path, filename)

        if os.path.exists(filepath):
            collected_files.append((filepath, filename))
        else:
            missing_files.append(filename)

    if not collected_files:
        print(f"全ログバックアップ: 対象ファイルが見つかりませんでした")
        return

    # zipファイルを作成
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, arcname in collected_files:
            zf.write(filepath, arcname)

    print(f"全ログバックアップを作成しました: {zip_filename}")
    print(f"  収集ファイル数: {len(collected_files)}件")
    if missing_files:
        print(f"  見つからなかったファイル: {len(missing_files)}件")
        for f in missing_files:
            print(f"    - {f}")

    # D:\rBOM_log にコピー
    if os.path.exists(FULL_BACKUP_COPY_DIR):
        try:
            dest_path = os.path.join(FULL_BACKUP_COPY_DIR, zip_filename)
            shutil.copy2(zip_path, dest_path)
            print(f"  コピー先: {dest_path}")
        except Exception as e:
            print(f"  警告: コピーに失敗しました: {e}")
    else:
        print(f"  警告: コピー先フォルダにアクセスできません: {FULL_BACKUP_COPY_DIR}")


def archive_previous_month_logs(current_date: datetime):
    """月が替わった場合、前月のログをzip圧縮してバックアップ

    current_date: 日本時間での現在日時
    """
    # 前日の日付を取得
    yesterday = current_date - timedelta(days=1)

    # 月が替わったかチェック（前日と今日の月が異なる場合）
    if yesterday.month == current_date.month:
        return  # 同じ月なので何もしない

    # 前月の年月を取得
    prev_year = yesterday.year
    prev_month = yesterday.month

    # logフォルダ内のファイルを確認
    if not os.path.exists(LOG_DIR):
        return

    log_files = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    if not log_files:
        return

    # zipファイル名: YYYYMM.zip
    zip_filename = f"{prev_year}{prev_month:02d}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_filename)

    # zipファイルを作成
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for log_file in log_files:
            log_path = os.path.join(LOG_DIR, log_file)
            zf.write(log_path, log_file)

    # 元のログファイルを削除
    for log_file in log_files:
        log_path = os.path.join(LOG_DIR, log_file)
        os.remove(log_path)

    print(f"前月ログをバックアップしました: {zip_path}")
    print(f"  圧縮ファイル数: {len(log_files)}件")


def check_log_file(config: dict, target_date: datetime) -> dict:
    """ログファイルの存在と容量をチェック"""
    date_str = target_date.strftime("%Y%m%d")
    filename = config["file_pattern"].format(date=date_str)
    filepath = os.path.join(config["path"], filename)

    result = {
        "name": config["name"],
        "filepath": filepath,
        "date": date_str,
        "exists": False,
        "size_kb": 0,
        "status": "NG",
        "message": "",
    }

    if not os.path.exists(filepath):
        result["message"] = f"ファイルが存在しません: {filepath}"
        return result

    result["exists"] = True
    size_bytes = os.path.getsize(filepath)
    result["size_kb"] = size_bytes / 1024

    if result["size_kb"] < config["min_size_kb"]:
        result["message"] = (
            f"ファイル容量が小さいです ({result['size_kb']:.2f}KB < {config['min_size_kb']}KB): "
            f"処理が完了していない可能性があります"
        )
        return result

    result["status"] = "OK"
    result["message"] = f"正常 ({result['size_kb']:.2f}KB)"
    return result


def extract_error_lines(filepath: str) -> list:
    """ログファイルからエラー行を抽出"""
    error_lines = []

    if not os.path.exists(filepath):
        return error_lines

    try:
        with open(filepath, "r", encoding="cp932", errors="replace") as f:
            for line_num, line in enumerate(f, start=1):
                line_stripped = line.rstrip()
                for keyword in ERROR_KEYWORDS:
                    if keyword in line_stripped:
                        error_lines.append(f"  {line_num}: {line_stripped}")
                        break
    except Exception as e:
        error_lines.append(f"  ファイル読み取りエラー: {e}")

    return error_lines


def extract_log_output_blocks(filepath: str) -> list:
    """「▲ログ出力」を検出し、マーク行まで遡ってブロックを抽出

    - 「希望納期が過去日になっています」の場合: ■まで遡り、連続は1件のみ
    - それ以外: ★まで遡る
    """
    blocks = []

    if not os.path.exists(filepath):
        return blocks

    try:
        # ファイル全体を読み込む
        with open(filepath, "r", encoding="cp932", errors="replace") as f:
            lines = f.readlines()

        # 連続する「希望納期が過去日」を追跡
        last_past_date_block_end = -1

        # 「▲ログ出力」を含む行を検索
        for i, line in enumerate(lines):
            if "▲ログ出力" in line:
                line_stripped = line.rstrip()

                # 「希望納期が過去日になっています」の場合
                if "希望納期が過去日になっています" in line_stripped:
                    # 連続している場合はスキップ
                    if last_past_date_block_end == i - 1 or last_past_date_block_end == i - 2:
                        # 直前の行が「・発注明細F登録」などの場合も連続とみなす
                        last_past_date_block_end = i
                        continue

                    # ■マークの行まで遡る
                    start_index = i
                    for j in range(i - 1, -1, -1):
                        if "■" in lines[j]:
                            start_index = j
                            break

                    # ■からログ出力までのブロックを抽出
                    block_lines = []
                    for k in range(start_index, i + 1):
                        block_lines.append(lines[k].rstrip())
                    blocks.append(block_lines)
                    last_past_date_block_end = i

                else:
                    # それ以外の▲ログ出力: ★まで遡る
                    start_index = i
                    for j in range(i - 1, -1, -1):
                        if "★" in lines[j]:
                            start_index = j
                            break

                    # ★からログ出力までのブロックを抽出
                    block_lines = []
                    for k in range(start_index, i + 1):
                        block_lines.append(lines[k].rstrip())
                    blocks.append(block_lines)

    except Exception as e:
        blocks.append([f"ファイル読み取りエラー: {e}"])

    return blocks


def main():
    # ディレクトリ作成
    ensure_directories()

    # 日本時間で現在日時と前日の日付を取得
    jst = ZoneInfo("Asia/Tokyo")
    now_jst = datetime.now(jst)
    yesterday = get_yesterday_jst()
    date_str = yesterday.strftime("%Y%m%d")

    # 月替わりバックアップ処理
    archive_previous_month_logs(now_jst)

    print(f"rBOMログチェック 対象日: {date_str}")
    print("=" * 60)

    results = []
    all_ok = True

    # ファイル存在・容量チェック
    for config in LOG_CONFIGS:
        result = check_log_file(config, yesterday)
        results.append(result)

        status_mark = "[OK]" if result["status"] == "OK" else "[NG]"
        print(f"\n{status_mark} {result['name']}")
        print(f"  ファイル: {result['filepath']}")
        print(f"  結果: {result['message']}")

        if result["status"] != "OK":
            all_ok = False

    # エラー行の抽出
    error_results = []
    for result in results:
        if result["exists"]:
            error_lines = extract_error_lines(result["filepath"])
            error_results.append({
                "name": result["name"],
                "filepath": result["filepath"],
                "error_lines": error_lines,
            })

    # ▲ログ出力ブロックの抽出
    log_output_results = []
    for result in results:
        if result["exists"]:
            blocks = extract_log_output_blocks(result["filepath"])
            log_output_results.append({
                "name": result["name"],
                "filepath": result["filepath"],
                "blocks": blocks,
            })

    # 結果をファイルに出力
    output_filename = f"rBOMログチェック_{date_str}.log"
    output_path = os.path.join(LOG_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"rBOMログチェック結果\n")
        f.write(f"実行日時: {datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')} (JST)\n")
        f.write(f"対象日: {date_str}\n")
        f.write("=" * 60 + "\n\n")

        # ファイルチェック結果
        for result in results:
            status_mark = "[OK]" if result["status"] == "OK" else "[NG]"
            f.write(f"{status_mark} {result['name']}\n")
            f.write(f"  ファイル: {result['filepath']}\n")
            f.write(f"  存在: {'あり' if result['exists'] else 'なし'}\n")
            if result["exists"]:
                f.write(f"  容量: {result['size_kb']:.2f} KB\n")
            f.write(f"  結果: {result['message']}\n\n")

        f.write("=" * 60 + "\n")
        f.write(f"ログファイルチェック：{'問題なし' if all_ok else '要確認'}\n")
        f.write("=" * 60 + "\n\n")

        # エラー行の出力
        f.write("【ログ内容チェック - エラー行抽出】\n\n")
        for err_result in error_results:
            f.write(f"■ {err_result['name']}\n")
            if err_result["error_lines"]:
                f.write(f"  エラー行数: {len(err_result['error_lines'])}件\n")
                for line in err_result["error_lines"]:
                    f.write(f"{line}\n")
            else:
                f.write("  エラー行: なし\n")
            f.write("\n")

        # ▲ログ出力ブロックの出力
        f.write("【ログ内容チェック - ▲ログ出力抽出】\n\n")
        for log_result in log_output_results:
            f.write(f"■ {log_result['name']}\n")
            if log_result["blocks"]:
                f.write(f"  検出数: {len(log_result['blocks'])}件\n\n")
                for idx, block in enumerate(log_result["blocks"], start=1):
                    f.write(f"  --- {idx} ---\n")
                    for line in block:
                        f.write(f"  {line}\n")
                    f.write("\n")
            else:
                f.write("  ▲ログ出力: なし\n")
            f.write("\n")

    print("\n" + "=" * 60)
    print(f"結果ファイル出力: {output_path}")
    print(f"ログファイルチェック：{'問題なし' if all_ok else '要確認'}")

    # エラー行サマリー
    total_errors = sum(len(e["error_lines"]) for e in error_results)
    if total_errors > 0:
        print(f"エラー行: {total_errors}件検出")

    # ▲ログ出力サマリー
    total_log_outputs = sum(len(l["blocks"]) for l in log_output_results)
    if total_log_outputs > 0:
        print(f"▲ログ出力: {total_log_outputs}件検出")

    # 共有フォルダへのコピーと古いファイル削除
    print()
    copy_to_share(output_path)
    cleanup_old_logs_in_share()

    # 全ログバックアップ
    print()
    backup_all_logs(yesterday)

    return 0 if all_ok else 1


if __name__ == "__main__":
    exit(main())
