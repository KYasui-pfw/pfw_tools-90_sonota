"""checksheet.db から、使われていない壊れた行を消す（1回だけ実行する）。

消すもの（2026-10-26 の調査で見つかったもの）:
    ・kouteizuban の「工程順が数字でない行」
        - 列がずれて入った行（完成部番に F始まりの伝票番号、工程Verに払出先、工程順に部番、工程に部品名）約5,900行
        - 完成部番が 'MCW' だけで、工程順・工程が空の行 約90行
      旧 Streamlit 版のチェック項目入力（pages/4）が KRD から取り込んだときに入ったものと見られる。
      F番号の伝票はもう使わない（2026-10 決定）。
    ・それらにぶら下がる zubancheck の行

⚠ 消す行の zubancheck にチェック項目が1つでも入っていたら、何も消さずに止まる。

使い方（⚠ check_input・現品票の画面・i-Reporter 連携を止めてから）:
    python tools/clean_checksheet_db.py --dry-run   … 消す件数を表示するだけ
    python tools/clean_checksheet_db.py             … 実行する（先に Database/backup にバックアップを取る）
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genpin import config  # noqa: E402

ITEM_NUMS = ["１", "２", "３", "４", "５", "６", "７", "８", "９", "１０", "１１", "１２", "１３", "１４", "１５"]
BROKEN_CONDITION = "typeof(工程順) <> 'integer'"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="件数を表示するだけで何も変えない")
    args = parser.parse_args()

    conn = sqlite3.connect(config.CHECKSHEET_DB, timeout=30)
    broken = conn.execute(f"SELECT * FROM kouteizuban WHERE {BROKEN_CONDITION}").fetchall()
    ids = [row[0] for row in broken]
    print(f"kouteizuban の壊れた行: {len(ids):,}行（全体 {conn.execute('SELECT COUNT(*) FROM kouteizuban').fetchone()[0]:,}行）")

    conn.execute("CREATE TEMP TABLE target (ID INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO target VALUES (?)", [(id_,) for id_ in ids])
    filled = " OR ".join(f"IFNULL(TRIM(チェック項目{n}), '') <> ''" for n in ITEM_NUMS)
    checks = conn.execute("SELECT COUNT(*) FROM zubancheck WHERE 連携ID IN (SELECT ID FROM target)").fetchone()[0]
    with_items = conn.execute(
        f"SELECT COUNT(*) FROM zubancheck WHERE 連携ID IN (SELECT ID FROM target) AND ({filled})"
    ).fetchone()[0]
    print(f"それにぶら下がる zubancheck: {checks:,}行（チェック項目が入っている行 {with_items}行）")

    if with_items:
        print("チェック項目が入っている行があるので、何も消さずに止めます。中身を確かめてください。")
        return
    if args.dry_run:
        print("--dry-run なので何も変えていません。")
        return

    stamp = f"{config.now():%Y%m%d%H%M%S}"
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = config.BACKUP_DIR / f"before_clean_{stamp}_checksheet.db"
    dest = sqlite3.connect(backup)
    conn.backup(dest)
    dest.close()
    print(f"バックアップ: {backup}")

    # 消した行は CSV にも残す（あとで中身を見られるように）。
    deleted_csv = config.BACKUP_DIR / f"{stamp}_clean_deleted_kouteizuban.csv"
    columns = [row[1] for row in conn.execute("PRAGMA table_info(kouteizuban)")]
    with open(deleted_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(broken)

    conn.execute("DELETE FROM zubancheck WHERE 連携ID IN (SELECT ID FROM target)")
    conn.execute("DELETE FROM kouteizuban WHERE ID IN (SELECT ID FROM target)")
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"消しました（消した行の一覧: {deleted_csv}）")


if __name__ == "__main__":
    main()
