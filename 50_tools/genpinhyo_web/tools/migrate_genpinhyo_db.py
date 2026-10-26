"""genpinhyo.db を 2026-10 の作り直しの形に移す（1回だけ実行する）。

    1. 移す前の DB を丸ごとバックアップする（Database/backup/before_migrate_YYYYMMDDhhmmss.db）
    2. output_history（表を丸ごと JSON で貯めていた記録）を zip に書き出す（Database/archive/）
    3. そのうち印刷の「履歴」を、1ロット1行の print_history に移す
    4. output_history を消す
    5. excluded_lots を「ロット番号だけ」の形に作り直す
    6. DB を点検し、壊れていれば genpinhyo を作り直す（同じロットの行が複数あれば最後に書かれた行を残す）
    7. 索引などを作り、VACUUM で空いた領域を詰める（ファイルが小さくなる）
    8. WAL モードにする

⚠ 2026-10-26 に受け取った本番の写しは、genpinhyo のロット番号の索引が壊れていた
  （行が索引に載っていない）。そのままデータ更新すると同じロットの行が増えていくので、6 で直す。

使い方（⚠ 現品票の画面・夜間処理・i-Reporter 連携を止めてから）:
    python tools/migrate_genpinhyo_db.py --dry-run   … 何が起きるかの件数だけ表示（何も変えない）
    python tools/migrate_genpinhyo_db.py             … 実行する

もう一度実行しても壊れない（output_history が無ければ 2〜4 は飛ばす）。
"""

import argparse
import json
import sqlite3
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genpin import config, db  # noqa: E402

ARCHIVE_DIR = config.DATABASE_DIR / "archive"
HISTORY_PRINT = "履歴"           # output_history.filename：印刷した表
MIGRATED_PRINT_KIND = "現品票（移行前の記録）"


def size_mb(path):
    return path.stat().st_size / 1024 / 1024


def has_table(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", [name]
    ).fetchone() is not None


def print_rows_from_history(conn):
    """output_history の「履歴」を print_history の行に変換する。"""
    rows = []
    for created_at, data in conn.execute(
        "SELECT created_at, data FROM output_history WHERE filename = ? ORDER BY id", [HISTORY_PRINT]
    ):
        for item in json.loads(data):
            rows.append((
                created_at, MIGRATED_PRINT_KIND, item.get("ロット番号"), item.get("完成部番"),
                item.get("部品名"), item.get("月次"), str(item.get("帳票発行ID", "")),
            ))
    return rows


def archive_output_history(conn, stamp):
    """output_history を種類ごとに JSON Lines にして zip に書き出す。"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    target = ARCHIVE_DIR / f"output_history_{stamp}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        kinds = [row[0] for row in conn.execute("SELECT DISTINCT filename FROM output_history")]
        for kind in kinds:
            lines = (
                json.dumps({"id": id_, "created_at": created_at, "data": json.loads(data)}, ensure_ascii=False)
                for id_, created_at, data in conn.execute(
                    "SELECT id, created_at, data FROM output_history WHERE filename = ? ORDER BY id", [kind])
            )
            with archive.open(f"{kind}.jsonl", "w") as f:
                for line in lines:
                    f.write((line + "\n").encode("utf-8"))
    return target


def duplicate_lots(conn):
    """同じロット番号の行が複数あるロットの数（索引を使わずに数える）。"""
    return conn.execute(
        "SELECT COUNT(*) FROM (SELECT ロット番号 FROM genpinhyo NOT INDEXED"
        " GROUP BY ロット番号 HAVING COUNT(*) > 1)"
    ).fetchone()[0]


def integrity_report(conn):
    """点検の結果を1行で返す（--dry-run で表示する用）。"""
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    duplicates = duplicate_lots(conn)
    if result == "ok" and not duplicates:
        return "壊れていません"
    first = result.splitlines()[0] if result != "ok" else "索引は正常"
    return f"⚠ 壊れています（{first}／同じロットが複数行あるロット {duplicates:,}件）→ 実行すると作り直します"


def rebuild_excluded_lots(conn):
    """excluded_lots を「ロット番号だけ（主キー）」の形に作り直す。"""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(excluded_lots)")]
    if columns == ["ロット番号"]:
        return
    conn.execute("CREATE TABLE excluded_lots_new (ロット番号 TEXT PRIMARY KEY)")
    conn.execute(
        "INSERT OR IGNORE INTO excluded_lots_new SELECT ロット番号 FROM excluded_lots WHERE ロット番号 IS NOT NULL"
    )
    conn.execute("DROP TABLE excluded_lots")
    conn.execute("ALTER TABLE excluded_lots_new RENAME TO excluded_lots")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="件数を表示するだけで何も変えない")
    args = parser.parse_args()

    path = config.GENPINHYO_DB
    print(f"対象: {path}（{size_mb(path):,.0f}MB）")
    conn = sqlite3.connect(path, timeout=30)

    if has_table(conn, "output_history"):
        for kind, count, mb in conn.execute(
            "SELECT filename, COUNT(*), ROUND(SUM(LENGTH(data)) / 1048576.0) FROM output_history GROUP BY filename"
        ):
            print(f"  output_history「{kind}」: {count:,}件・{mb:,.0f}MB")
        print_rows = print_rows_from_history(conn)
        print(f"  → print_history に移す行: {len(print_rows):,}行")
    else:
        print_rows = None
        print("  output_history はありません（移行済み）")

    integrity = integrity_report(conn)
    print(f"  点検: {integrity}")

    if args.dry_run:
        print("--dry-run なので何も変えていません。")
        return

    stamp = f"{config.now():%Y%m%d%H%M%S}"
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = config.BACKUP_DIR / f"before_migrate_{stamp}.db"
    print(f"1. バックアップ: {backup}")
    dest = sqlite3.connect(backup)
    conn.backup(dest)
    dest.close()

    db.ensure_schema(conn)
    if print_rows is not None:
        archive = archive_output_history(conn, stamp)
        print(f"2. 書き出し: {archive}（{size_mb(archive):,.1f}MB）")
        conn.executemany(
            "INSERT INTO print_history (printed_at, kind, ロット番号, 完成部番, 部品名, 月次, 帳票発行ID)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            print_rows,
        )
        print(f"3. print_history に {len(print_rows):,}行を移しました")
        conn.execute("DROP TABLE output_history")
        print("4. output_history を消しました")

    rebuild_excluded_lots(conn)
    print("5. excluded_lots を作り直しました")
    db.ensure_schema(conn)
    conn.commit()

    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or duplicate_lots(conn):
        before, after = db.rebuild_genpinhyo(conn)
        conn.execute("REINDEX")
        conn.commit()
        print(f"6. genpinhyo を作り直しました（{before:,}行 → {after:,}行。重なっていたロットは最後に書かれた行を残した）")
    else:
        print("6. 点検: 壊れていません")
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        conn.close()
        print(f"⚠ 作り直しても直りませんでした。バックアップ（{backup}）から戻して、DX推進室で調べてください: {result[:200]}")
        sys.exit(1)

    print("7. VACUUM（数分かかることがあります）")
    conn.execute("VACUUM")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()
    print(f"8. 完了: {path}（{size_mb(path):,.0f}MB）")


if __name__ == "__main__":
    main()
