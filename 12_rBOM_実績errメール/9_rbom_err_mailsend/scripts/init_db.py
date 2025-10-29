# scripts/init_db.py

import sqlite3
import os
from pathlib import Path

# データベースファイルのパス
DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "mail_management.db"


def init_database():
    """データベースとテーブルを初期化"""
    # dbディレクトリが存在しない場合は作成
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 社員マスタテーブル（M0540から同期）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_master (
            tancd VARCHAR(20) PRIMARY KEY,
            tannm VARCHAR(100),
            valflg VARCHAR(1) DEFAULT '1',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # メール送信先テーブル（受入/棚出、TO/CC別）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mail_recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tancd VARCHAR(20) NOT NULL,
            function_type VARCHAR(20) NOT NULL,
            recipient_type VARCHAR(10) NOT NULL,
            email_address VARCHAR(255) NOT NULL,
            display_order INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tancd) REFERENCES employee_master(tancd),
            UNIQUE(tancd, function_type, recipient_type, display_order)
        )
    """)

    # メール送信履歴テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mail_send_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name VARCHAR(50) NOT NULL,
            record_id VARCHAR(100) NOT NULL,
            employee_code VARCHAR(20) NOT NULL,
            email_address VARCHAR(255) NOT NULL,
            error_detail TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(table_name, record_id)
        )
    """)

    # インデックス作成
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mail_recipients_tancd
        ON mail_recipients(tancd)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mail_recipients_function
        ON mail_recipients(tancd, function_type, recipient_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_mail_send_history_record
        ON mail_send_history(table_name, record_id)
    """)

    conn.commit()
    conn.close()

    print(f"データベース初期化完了: {DB_PATH}")


if __name__ == "__main__":
    init_database()
