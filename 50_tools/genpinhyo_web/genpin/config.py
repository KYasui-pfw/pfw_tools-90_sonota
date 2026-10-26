"""現品票システムの設定（ファイルの場所・接続先）を1か所にまとめたもの。

画面・夜間処理・i-Reporter 連携のどれも、場所や接続先はここから読む。
本番のサーバーを移すときや接続先が変わったときは、このファイルだけを直せばよい。
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# ファイルの場所
# ---------------------------------------------------------------------------
# このファイル（genpin/config.py）の1つ上がプロジェクトの直下。
# 起動したときのカレントディレクトリに左右されないよう、必ずここから組み立てる。
ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = ROOT_DIR / "Database"
GENPINHYO_DB = DATABASE_DIR / "genpinhyo.db"     # 現品票の本体（i-Reporter の header_koushin.py も読む）
CHECKSHEET_DB = DATABASE_DIR / "checksheet.db"   # 工程図とチェック項目（i-Reporter・Django も読む）
BACKUP_DIR = DATABASE_DIR / "backup"

TEMPLATE_DIR = ROOT_DIR / "template"             # 現品票の Excel のひな形
CSV_DIR = ROOT_DIR / "csv"                       # i-Reporter に取り込ませる CSV の置き場
CSV_DONE_DIR = CSV_DIR / "sumi"                  # 取り込みが終わった CSV の置き場
SCREENSHOT_DIR = ROOT_DIR / "work" / "sumi" / "png"  # ConMas の画面の記録
ERROR_TEXT = ROOT_DIR / "err.txt"                # DB に書けなかったときのエラーの書き先

# genpinhyo.db のバックアップを何日分残すか。
BACKUP_KEEP_DAYS = 7

# ---------------------------------------------------------------------------
# 接続先
# ---------------------------------------------------------------------------
# 業務ポータル（Django）の読み取りAPI。ログインも API キーも不要。
PORTAL_API_BASE = "http://pfw-gyomu"
PORTAL_API_TIMEOUT_SEC = 120

# rBOM の FastAPI（CHANGE GEAR BOX の引当を読むのに使う。読み取り専用のキー）。
RBOM_API_BASE = "http://pfw-api"
RBOM_API_KEY = "oG5^Ls%#20yq"
RBOM_API_TIMEOUT_SEC = 60

# i-Reporter の PostgreSQL（客先マスタ・帳票の発行状況を読む）。
IREPORTER_DB_URL = "postgresql://postgres:cimtops@ESRV10/irepodb"

# ConMas Manager（i-Reporter の帳票を自動で作る画面）。
CONMAS_URL = "http://172.17.52.101/ConMasManager/AutoGenerate"
CONMAS_USER = "mainte"
CONMAS_PASSWORD = "@next123"

# ---------------------------------------------------------------------------
# 日時
# ---------------------------------------------------------------------------
JST = timezone(timedelta(hours=9))


def now():
    """日本時刻の現在日時。サーバーの時刻設定に左右されないよう、必ずこれを使う。"""
    return datetime.now(JST)
