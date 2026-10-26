"""genpinhyo.db の接続・テーブル定義・バックアップ・記録（履歴とエラー）。

【テーブルの役割】
    genpinhyo             現品票の本体（1ロット1行）。⚠ i-Reporter の header_koushin.py が
                          列名で読んでいるので、列名を変えたり消したりしない（足すのはよい）
    buhin_irepo_mst       部品名ごとの設定（i-Reporter 管理・QR のレイアウト・縦横）。画面から人が直す
    delete_mst            ロットごとの削除フラグ（1 = 加工伝票から消えた → 一覧に出さない）
    excluded_lots         払出先で全行が除外になったロット（一覧に出さない）。データ更新のたびに作り直す
    cgb_seino_ch_mapping  CHANGE GEAR BOX の製番 → CH番号（時限処理）
    print_history         印刷した記録（いつ・どのロットを・どのレイアウトで）
    flag_change_log       削除フラグが変わった記録
    error_log             エラーの記録

⚠ 2026-10 の作り直しより前は、印刷した表や削除フラグの変化を **表ごと JSON で**
  output_history に貯めていた（1.45GB のうち 973MB）。いまは1行＝1ロットで持つ。
  古いデータの移し替えは tools/migrate_genpinhyo_db.py。
"""

import sqlite3
from datetime import datetime

from . import config

# genpinhyo の列（REPLACE INTO の並び）。
# ⚠ 先頭26列は昔からの列。i-Reporter の header_koushin.py が読んでいる。
GENPINHYO_COLUMNS = [
    "ロット番号", "月次", "組立番号", "機種", "吋", "G", "完成部番", "部品名", "客先名", "国名",
    "B1図番", "B2図番", "F1図番", "F2図番", "L図番", "R図番", "C図番",
    "組立開始日", "梱包開始日", "指定納期", "必要数", "SKDK", "工程", "工程VERSION", "ﾒｯｷ", "客先コード",
    # 2026-10-23 追加。保存と参考表示だけで、印字や QR には使わない。
    "手書き図番", "予備図番1", "予備図番2", "予備図番3", "予備図番4",
]

# 一覧に出さない列（保存しているだけのもの）。
HIDDEN_DRAWING_COLUMNS = ["手書き図番", "予備図番1", "予備図番2", "予備図番3", "予備図番4"]

_SCHEMA = [
    # 現品票の本体。列はすべて TEXT（昔からそう。ﾒｯｷ は '1.0'、工程VERSION は '1' のような文字で入る）。
    "CREATE TABLE IF NOT EXISTS genpinhyo ("
    + ", ".join(
        f"{name} TEXT PRIMARY KEY" if name == "ロット番号" else f"{name} TEXT"
        for name in GENPINHYO_COLUMNS
    )
    + ")",
    # 一覧は月次で絞り込んで読むので索引を張る。
    "CREATE INDEX IF NOT EXISTS idx_genpinhyo_getsuji ON genpinhyo (月次)",
    """CREATE TABLE IF NOT EXISTS buhin_irepo_mst (
        部品名 TEXT PRIMARY KEY,
        ireporter管理flg INTEGER,
        QRコードレイアウト区分 INTEGER,
        縦横区分 INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS delete_mst (
        ロット番号 TEXT PRIMARY KEY,
        削除flg INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS excluded_lots (
        ロット番号 TEXT PRIMARY KEY
    )""",
    """CREATE TABLE IF NOT EXISTS cgb_seino_ch_mapping (
        seino TEXT PRIMARY KEY,
        ch_no TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS print_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        printed_at TEXT NOT NULL,
        kind TEXT NOT NULL,
        ロット番号 TEXT,
        完成部番 TEXT,
        部品名 TEXT,
        月次 TEXT,
        帳票発行ID TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_print_history_lot ON print_history (ロット番号)",
    """CREATE TABLE IF NOT EXISTS flag_change_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        changed_at TEXT NOT NULL,
        ロット番号 TEXT NOT NULL,
        old_flg INTEGER,
        new_flg INTEGER NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS error_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        error_message TEXT NOT NULL
    )""",
]

# 印刷の種類（print_history.kind に入れる値）。
PRINT_KIND_NORMAL = "現品票"
PRINT_KIND_SHIFTED = "現品票（ずれる場合）"
PRINT_KIND_MANUAL = "手入力"
PRINT_KIND_REISSUE = "チェックシート再作成"


class DatabaseCorruptedError(Exception):
    """genpinhyo.db が壊れている（索引とテーブルの中身が食い違っている）。"""


def check_integrity(conn):
    """DB が壊れていないか点検する。壊れていれば DatabaseCorruptedError。

    ⚠ ロット番号の索引が壊れていると、REPLACE INTO が既にある行を見つけられず、
      データ更新のたびに同じロットの行が1行ずつ増えていく（2026-10-26 に本番の写しで発生）。
      そうならないよう、書き込む前に必ず点検する。quick_check は数十MBなら1秒もかからない。
    """
    result = conn.execute("PRAGMA quick_check").fetchone()[0]
    if result != "ok":
        raise DatabaseCorruptedError(
            "genpinhyo.db が壊れているため、データ更新を中止しました。"
            "tools/migrate_genpinhyo_db.py で修復してください。"
            f"（{result.splitlines()[0]}）"
        )


def rebuild_genpinhyo(conn):
    """壊れた genpinhyo テーブルを作り直す。同じロットの行が複数あれば、最後に書かれた行を残す。

    「最後に書かれた行」＝ rowid がいちばん大きい行（REPLACE INTO は書くたびに新しい rowid を振る）。

    ⚠ 壊れたテーブルでは「rowid で行を探す」と見つからない行がある（rowid の並びが崩れているため）。
      必ずテーブルを頭から全部読み（NOT INDEXED）、重なりの整理は Python 側で行う。
      SQL の `WHERE rowid IN (...)` で絞ると行が消える（2026-10-26 に実際に約2,400行消えた）。
    ⚠ 作り直したあとの行数が「元のロットの数」と合わなければ、元に戻して止める。

    Returns:
        (作り直す前の行数, 作り直したあとの行数)
    """
    existing = [row[1] for row in conn.execute("PRAGMA table_info(genpinhyo)")]
    columns = [name for name in GENPINHYO_COLUMNS if name in existing]

    # テーブルを頭から全部読み、ロットごとに rowid が最大の行を残す。
    latest = {}
    scanned = 0
    for rowid, *values in conn.execute(
        f"SELECT rowid, {', '.join(columns)} FROM genpinhyo NOT INDEXED"
    ):
        scanned += 1
        lot_no = values[0]
        if lot_no not in latest or rowid > latest[lot_no][0]:
            latest[lot_no] = (rowid, values)

    conn.commit()
    conn.execute("BEGIN")
    try:
        conn.execute("DROP TABLE IF EXISTS genpinhyo_rebuild")
        conn.execute(_SCHEMA[0].replace("genpinhyo (", "genpinhyo_rebuild (", 1))
        conn.executemany(
            f"INSERT INTO genpinhyo_rebuild ({', '.join(columns)})"
            f" VALUES ({', '.join('?' for _ in columns)})",
            [values for _, values in latest.values()],
        )
        conn.execute("DROP TABLE genpinhyo")
        conn.execute("ALTER TABLE genpinhyo_rebuild RENAME TO genpinhyo")
        conn.execute(_SCHEMA[1])   # 月次の索引を張り直す
        after = conn.execute("SELECT COUNT(*) FROM genpinhyo").fetchone()[0]
        if after != len(latest):
            raise DatabaseCorruptedError(
                f"genpinhyo の作り直しで行数が合いません（ロット {len(latest):,}件 → {after:,}行）"
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return scanned, after


def connect(path=None):
    """genpinhyo.db につなぐ。

    ・timeout=30 … ほかの処理（画面・夜間処理・i-Reporter）が書き込み中なら最大30秒待つ。
      待たずに諦めると「database is locked」「unable to open database file」になる。
    ・WAL モード … 読む人と書く人が互いを待たなくてよくなる（DB に1回設定すれば残る）。
    """
    conn = sqlite3.connect(path or config.GENPINHYO_DB, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema(conn):
    """テーブルが無ければ作る。古い genpinhyo に足りない列があれば足す。"""
    for sql in _SCHEMA:
        conn.execute(sql)

    existing = {row[1] for row in conn.execute("PRAGMA table_info(genpinhyo)")}
    for name in GENPINHYO_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE genpinhyo ADD COLUMN {name} TEXT")
    conn.commit()


def backup_genpinhyo():
    """genpinhyo.db を Database/backup/YYYYMMDD_genpinhyo.db に写す（1日1つ・7日分）。

    ⚠ ファイルのコピー（shutil.copy）ではなく SQLite のバックアップ機能を使う。
      コピーは書き込み中に取ると壊れた写しになることがあるが、こちらは使用中でも正しく取れる。
    """
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    today = config.now()
    target = config.BACKUP_DIR / f"{today:%Y%m%d}_genpinhyo.db"

    source = connect()
    dest = sqlite3.connect(target)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    # 古いバックアップを消す。ファイル名の先頭8文字が日付。
    for path in config.BACKUP_DIR.glob("*_genpinhyo.db"):
        try:
            made = datetime.strptime(path.name[:8], "%Y%m%d").date()
        except ValueError:
            continue
        if (today.date() - made).days > config.BACKUP_KEEP_DAYS:
            path.unlink(missing_ok=True)


def record_prints(rows, kind):
    """印刷した記録を残す（1ロット1行）。

    Args:
        rows: 辞書のリスト（ロット番号・完成部番・部品名・月次・帳票発行ID のキーを読む）
        kind: PRINT_KIND_* のどれか
    """
    stamp = f"{config.now():%Y-%m-%d %H:%M:%S}"
    values = [
        (stamp, kind, row.get("ロット番号"), row.get("完成部番"), row.get("部品名"),
         row.get("月次"), str(row.get("帳票発行ID", "")))
        for row in rows
    ]
    conn = connect()
    try:
        ensure_schema(conn)
        conn.executemany(
            "INSERT INTO print_history"
            " (printed_at, kind, ロット番号, 完成部番, 部品名, 月次, 帳票発行ID)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            values,
        )
        conn.commit()
    finally:
        conn.close()


def log_error(message):
    """エラーを error_log に残す。DB に書けなければ err.txt に追記する。"""
    stamp = f"{config.now():%Y-%m-%d %H:%M:%S}"
    try:
        conn = connect()
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS error_log (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " created_at TEXT NOT NULL, error_message TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO error_log (created_at, error_message) VALUES (?, ?)",
                (stamp, str(message)),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as db_error:
        with open(config.ERROR_TEXT, mode="a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}（DBに書けなかった: {db_error}）\n")
