# app/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Config:
    """環境変数から設定を読み込むクラス"""

    # プロジェクトルートディレクトリ
    BASE_DIR = Path(__file__).parent.parent

    # データベース設定
    DB_PATH = BASE_DIR / "db" / "mail_management.db"

    # Oracle DB設定（FastAPI経由でアクセス）
    FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://fastapi:8000")
    READ_API_KEY = os.getenv("READ_API_KEY", "")

    # 監視設定（DK020: 受入、DK040: 棚出）
    # SYORIZUMIKBN: 1=未処理, 2=正常終了, 3=エラー
    ERROR_STATUS_VALUE = "3"  # エラーと判定する値
    EMPLOYEE_CODE_FIELD = "IPTANCD"  # 社員コードフィールド（更新した社員）

    # メール送信設定（すべて.envから読み込み）
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "rBOM System")
    MAIL_SUBJECT = os.getenv("MAIL_SUBJECT", "【rBOM】実績登録エラー通知")

    # ログ設定
    LOG_DIR = BASE_DIR / "logs"
    LOG_FILE = LOG_DIR / "monitor.log"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# 設定のシングルトンインスタンス
config = Config()
