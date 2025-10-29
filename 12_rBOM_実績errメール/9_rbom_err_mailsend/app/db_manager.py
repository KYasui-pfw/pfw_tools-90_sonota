# app/db_manager.py

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo
from .config import config


class DatabaseManager:
    """SQLiteデータベース操作を管理するクラス"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(config.DB_PATH)

    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする
        return conn

    # ==================== 社員マスタ操作 ====================

    def sync_employee_master(self, employees: List[Dict]) -> int:
        """
        M0540から取得した社員マスタをSQLiteに同期（UPSERT）

        Args:
            employees: [{"TANCD": "xxx", "TANNM": "xxx", "VALFLG": "1"}, ...]

        Returns:
            同期した件数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        count = 0

        # 日本時間で現在時刻を取得
        jst_now = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

        for emp in employees:
            cursor.execute("""
                INSERT INTO employee_master (tancd, tannm, valflg, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tancd) DO UPDATE SET
                    tannm = excluded.tannm,
                    valflg = excluded.valflg,
                    updated_at = ?
            """, (emp.get("TANCD"), emp.get("TANNM"), emp.get("VALFLG"), jst_now, jst_now))
            count += 1

        conn.commit()
        conn.close()
        return count

    def get_all_employees(self, include_inactive: bool = False) -> List[Dict]:
        """
        全社員情報を取得

        Args:
            include_inactive: True の場合、VALFLG='2'（退職者）も含める

        Returns:
            社員情報のリスト
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_inactive:
            cursor.execute("""
                SELECT tancd, tannm, valflg, updated_at
                FROM employee_master
                ORDER BY tancd
            """)
        else:
            cursor.execute("""
                SELECT tancd, tannm, valflg, updated_at
                FROM employee_master
                WHERE valflg = '1'
                ORDER BY tancd
            """)

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_employee_by_tancd(self, tancd: str) -> Optional[Dict]:
        """社員コード(TANCD)で社員情報を取得"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tancd, tannm, valflg, updated_at
            FROM employee_master
            WHERE tancd = ?
        """, (tancd,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== メール送信先操作 ====================

    def get_recipients(self, tancd: str, function_type: str, recipient_type: str) -> List[Dict]:
        """
        特定の社員・機能・送信先種別のメールアドレスリストを取得

        Args:
            tancd: 社員コード
            function_type: "acceptance" or "picking"
            recipient_type: "TO" or "CC"

        Returns:
            [{"id": 1, "email_address": "...", "display_order": 1}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tancd, function_type, recipient_type, email_address, display_order,
                   created_at, updated_at
            FROM mail_recipients
            WHERE tancd = ? AND function_type = ? AND recipient_type = ?
            ORDER BY display_order
        """, (tancd, function_type, recipient_type))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_recipients_by_tancd(self, tancd: str) -> Dict[str, Dict[str, List[str]]]:
        """
        特定社員の全メール送信先を取得

        Returns:
            {
                "acceptance": {"TO": ["email1", "email2"], "CC": ["email3"]},
                "picking": {"TO": ["email4"], "CC": []}
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT function_type, recipient_type, email_address
            FROM mail_recipients
            WHERE tancd = ?
            ORDER BY function_type, recipient_type, display_order
        """, (tancd,))
        rows = cursor.fetchall()
        conn.close()

        result = {
            "acceptance": {"TO": [], "CC": []},
            "picking": {"TO": [], "CC": []}
        }

        for row in rows:
            func = row["function_type"]
            rtype = row["recipient_type"]
            if func in result and rtype in result[func]:
                result[func][rtype].append(row["email_address"])

        return result

    def add_recipient(self, tancd: str, function_type: str, recipient_type: str,
                     email_address: str, display_order: int) -> int:
        """メール送信先を追加"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 日本時間で現在時刻を取得
            jst_now = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO mail_recipients
                (tancd, function_type, recipient_type, email_address, display_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tancd, function_type, recipient_type, email_address, display_order, jst_now, jst_now))
            conn.commit()
            recipient_id = cursor.lastrowid
            conn.close()
            return recipient_id
        except sqlite3.IntegrityError:
            conn.close()
            return -1

    def update_recipient(self, recipient_id: int, email_address: str) -> bool:
        """メール送信先を更新"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 日本時間で現在時刻を取得
        jst_now = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            UPDATE mail_recipients
            SET email_address = ?, updated_at = ?
            WHERE id = ?
        """, (email_address, jst_now, recipient_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def delete_recipient(self, recipient_id: int) -> bool:
        """メール送信先を削除"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mail_recipients WHERE id = ?", (recipient_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def bulk_update_recipients(self, tancd: str, function_type: str, recipient_type: str,
                              email_addresses: List[str]) -> bool:
        """
        特定の社員・機能・送信先種別のメールアドレスを一括更新

        Args:
            tancd: 社員コード
            function_type: "acceptance" or "picking"
            recipient_type: "TO" or "CC"
            email_addresses: メールアドレスリスト（最大5件）
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 日本時間で現在時刻を取得
            jst_now = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

            # 既存データを削除
            cursor.execute("""
                DELETE FROM mail_recipients
                WHERE tancd = ? AND function_type = ? AND recipient_type = ?
            """, (tancd, function_type, recipient_type))

            # 新規データを挿入
            for i, email in enumerate(email_addresses, start=1):
                if email.strip():  # 空文字列は無視
                    cursor.execute("""
                        INSERT INTO mail_recipients
                        (tancd, function_type, recipient_type, email_address, display_order, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (tancd, function_type, recipient_type, email.strip(), i, jst_now, jst_now))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e

    # ==================== メール送信履歴操作 ====================

    def is_mail_sent(self, table_name: str, record_id: str) -> bool:
        """指定レコードにメール送信済みか確認"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM mail_send_history
            WHERE table_name = ? AND record_id = ?
        """, (table_name, record_id))
        result = cursor.fetchone()
        conn.close()
        return result["count"] > 0

    def add_mail_history(self, table_name: str, record_id: str, employee_code: str,
                        email_address: str, error_detail: str = None) -> int:
        """メール送信履歴を追加"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 日本時間で現在時刻を取得
            jst_now = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO mail_send_history
                (table_name, record_id, employee_code, email_address, error_detail, sent_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (table_name, record_id, employee_code, email_address, error_detail, jst_now))
            conn.commit()
            history_id = cursor.lastrowid
            conn.close()
            return history_id
        except sqlite3.IntegrityError:
            # 既に送信済みの場合（UNIQUE制約違反）
            conn.close()
            return -1

    def get_mail_history(self, limit: int = 100) -> List[Dict]:
        """メール送信履歴を取得（最新順）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, table_name, record_id, employee_code, email_address,
                   error_detail, sent_at
            FROM mail_send_history
            ORDER BY sent_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
