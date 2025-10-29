# app/mail_sender.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import logging
from typing import Dict, List
from .config import config

logger = logging.getLogger(__name__)


class MailSender:
    """メール送信を管理するクラス"""

    def __init__(self):
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
        self.mail_from = config.MAIL_FROM
        self.mail_from_name = config.MAIL_FROM_NAME
        self.mail_subject = config.MAIL_SUBJECT

    def send_error_notification(self, to_emails: List[str], cc_emails: List[str], employee_name: str, error_data: Dict) -> bool:
        """
        エラー通知メールを送信

        Args:
            to_emails: 送信先メールアドレスのリスト（TO）
            cc_emails: 送信先メールアドレスのリスト（CC）
            employee_name: 社員名
            error_data: エラーデータ（テーブル名、レコードID、エラー詳細など）

        Returns:
            送信成功した場合True、失敗した場合False
        """
        # 空のリストをフィルタリング
        to_emails = [email for email in to_emails if email and email.strip()]
        cc_emails = [email for email in cc_emails if email and email.strip()]

        # 送信先が1つもない場合
        if not to_emails and not cc_emails:
            logger.warning(f"送信先がありません: {employee_name}")
            return False

        try:
            # メール本文を作成
            body = self._create_mail_body(employee_name, error_data)

            # 機能名から件名を決定
            function_name = error_data.get("function_name", "")
            if function_name == "受入機能":
                subject = "【rBOM】受入実績登録エラー通知"
            elif function_name == "棚出機能":
                subject = "【rBOM】棚出実績登録エラー通知"
            else:
                subject = self.mail_subject  # デフォルト

            # MIMEメッセージを作成
            msg = MIMEMultipart()
            msg["From"] = formataddr((self.mail_from_name, self.mail_from))

            # TO/CCを設定
            if to_emails:
                msg["To"] = ", ".join(to_emails)
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)

            msg["Subject"] = subject

            # 本文を添付
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # 送信先リスト（TO + CC）
            all_recipients = to_emails + cc_emails

            # SMTP接続してメール送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # TLS暗号化
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.mail_from, all_recipients, msg.as_string())

            logger.info(f"メール送信成功: TO={to_emails}, CC={cc_emails}")
            return True

        except Exception as e:
            logger.error(f"メール送信失敗: TO={to_emails}, CC={cc_emails}, エラー: {e}")
            return False

    def _create_mail_body(self, employee_name: str, error_data: Dict) -> str:
        """
        メール本文を作成

        Args:
            employee_name: 社員名
            error_data: エラーデータ

        Returns:
            メール本文（テキスト）
        """
        function_name = error_data.get("function_name", "不明")
        record_info = error_data.get("record_info", {})
        
        # 基本情報
        order_no = record_info.get("order_no", "-")
        order_label = record_info.get("order_label", "番号")
        line_no = record_info.get("line_no", "-")
        instdt = record_info.get("instdt", "-")
        iptancd = record_info.get("iptancd", "-")
        employee_name_detail = record_info.get("employee_name", employee_name)
        
        # 品目情報
        listno = record_info.get("listno", "-")
        hmcd = record_info.get("hmcd", "-")
        hmnm = record_info.get("hmnm", "-")

        body = f"""
rBOMへの実績登録時に登録エラーを検知しました。

以下のデータでエラーが発生しています。
ご確認をお願いいたします。

【エラー情報】
機能: {function_name}
{order_label}: {order_no}　　行番号: {line_no}
リスト番号: {listno}
品目コード: {hmcd}
品目名: {hmnm}
登録日時: {instdt}
更新社員: {iptancd} ({employee_name_detail})

※このメールは自動送信されています。
※ご不明な点がございましたら、システム管理者までお問い合わせください。
"""
        return body
