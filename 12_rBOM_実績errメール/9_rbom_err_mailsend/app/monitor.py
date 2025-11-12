# app/monitor.py

import requests
import logging
from datetime import datetime
from typing import List, Dict
from .config import config
from .db_manager import DatabaseManager
from .mail_sender import MailSender

# ロギング設定
config.LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ErrorMonitor:
    """エラーデータ監視・メール送信を行うクラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.mail_sender = MailSender()
        self.api_url = f"{config.FASTAPI_BASE_URL}/query"
        self.headers = {"X-API-KEY": config.READ_API_KEY}

    def run(self):
        """監視処理のメイン実行"""
        logger.info("=" * 60)
        logger.info("監視処理を開始します")

        try:
            # DK020（受入）のエラーを監視
            self._monitor_table("DK020", "acceptance")

            # DK040（棚出）のエラーを監視
            self._monitor_table("DK040", "picking")

            # DK020（受入）の経費工具受入を監視
            self._monitor_expense_tool_acceptance()

        except Exception as e:
            logger.error(f"監視処理中にエラーが発生しました: {e}", exc_info=True)
        finally:
            logger.info("監視処理を終了します")
            logger.info("=" * 60)

    def _monitor_table(self, table_name: str, function_type: str):
        """
        特定のテーブルを監視

        Args:
            table_name: 監視対象テーブル名（DK020/DK040）
            function_type: 機能タイプ（acceptance/picking）
        """
        logger.info(f"[{table_name}] 監視開始（機能: {function_type}）")

        try:
            # エラーデータを取得
            error_records = self._fetch_error_records(table_name)

            if not error_records:
                logger.info(f"[{table_name}] エラーデータは見つかりませんでした")
                return

            logger.info(f"[{table_name}] {len(error_records)}件のエラーデータを検出しました")

            # 各エラーレコードを処理
            for record in error_records:
                self._process_error_record(table_name, function_type, record)

        except Exception as e:
            logger.error(f"[{table_name}] 監視処理中にエラーが発生しました: {e}", exc_info=True)

    def _fetch_error_records(self, table_name: str) -> List[Dict]:
        """
        FastAPI経由でエラーレコードを取得

        Args:
            table_name: テーブル名

        Returns:
            エラーレコードのリスト
        """
        try:
            # Generic Query APIを使ってエラーデータを取得
            payload = {
                "table": table_name,
                "where": {
                    "SYORIZUMIKBN": "3"  # エラーステータス（1=未処理, 2=正常終了, 3=エラー）
                }
            }

            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("rows", [])

        except requests.exceptions.RequestException as e:
            logger.error(f"FastAPI通信エラー: {e}")
            return []

    def _process_error_record(self, table_name: str, function_type: str, record: Dict):
        """
        個別のエラーレコードを処理

        Args:
            table_name: テーブル名
            function_type: 機能タイプ（acceptance/picking）
            record: エラーレコード
        """
        # レコードIDを生成
        record_id = self._generate_record_id(table_name, record)
        employee_code = record.get("IPTANCD")

        if not employee_code:
            logger.warning(f"[{table_name}] レコードID {record_id}: 社員コード（IPTANCD）が見つかりません")
            return

        logger.info(f"[{table_name}] レコードID {record_id}: 社員コード {employee_code} を処理中")

        # 送信済みかチェック
        if self.db_manager.is_mail_sent(table_name, record_id):
            logger.info(f"[{table_name}] レコードID {record_id}: 既にメール送信済みです")
            return

        # 社員情報を取得
        employee = self.db_manager.get_employee_by_tancd(employee_code)
        if not employee:
            logger.warning(f"[{table_name}] レコードID {record_id}: 社員コード {employee_code} の社員情報が見つかりません")
            return

        employee_name = employee.get("tannm") or employee_code

        # メール送信先を取得（TO/CC）
        to_emails = self.db_manager.get_recipients(employee_code, function_type, "TO")
        cc_emails = self.db_manager.get_recipients(employee_code, function_type, "CC")

        # メールアドレスのリストを抽出
        to_addresses = [r["email_address"] for r in to_emails]
        cc_addresses = [r["email_address"] for r in cc_emails]

        if not to_addresses and not cc_addresses:
            logger.warning(f"[{table_name}] レコードID {record_id}: 社員コード {employee_code} のメール送信先が設定されていません")

            # エラー詳細を作成（送信先未設定の場合もレコード情報は取得）
            function_name = "受入機能" if function_type == "acceptance" else "棚出機能"
            record_info = self._extract_record_info(table_name, record, record_id, employee_code, employee_name)

            # 送信先未設定でも履歴に記録（再送信を防ぐため）
            self.db_manager.add_mail_history(
                table_name=table_name,
                record_id=record_id,
                employee_code=employee_code,
                employee_name=employee_name,
                to_addresses=["（送信先未設定）"],
                cc_addresses=[],
                function_name=function_name,
                order_no=record_info.get('order_no', '-'),
                order_label=record_info.get('order_label', '番号'),
                line_no=record_info.get('line_no', '-'),
                listno=record_info.get('listno', '-'),
                hmcd=record_info.get('hmcd', '-'),
                hmnm=record_info.get('hmnm', '-'),
                instdt=record_info.get('instdt', '-'),
                error_detail="メール送信先が設定されていないため送信スキップ"
            )
            logger.info(f"[{table_name}] レコードID {record_id}: 送信先未設定として履歴を記録しました")
            return

        logger.info(f"[{table_name}] レコードID {record_id}: {employee_name} にメールを送信します（TO={to_addresses}, CC={cc_addresses}）")

        # エラー詳細を作成
        function_name = "受入機能" if function_type == "acceptance" else "棚出機能"

        # レコード情報を整形
        record_info = self._extract_record_info(table_name, record, record_id, employee_code, employee_name)

        error_data = {
            "function_name": function_name,
            "record_info": record_info
        }

        # メール送信
        if self.mail_sender.send_error_notification(to_addresses, cc_addresses, employee_name, error_data):
            # 送信履歴を記録（1エラーにつき1レコード）
            error_detail_summary = f"{function_name} - {record_info.get('order_no', '-')} / {record_info.get('line_no', '-')}"
            self.db_manager.add_mail_history(
                table_name=table_name,
                record_id=record_id,
                employee_code=employee_code,
                employee_name=employee_name,
                to_addresses=to_addresses,
                cc_addresses=cc_addresses,
                function_name=function_name,
                order_no=record_info.get('order_no', '-'),
                order_label=record_info.get('order_label', '番号'),
                line_no=record_info.get('line_no', '-'),
                listno=record_info.get('listno', '-'),
                hmcd=record_info.get('hmcd', '-'),
                hmnm=record_info.get('hmnm', '-'),
                instdt=record_info.get('instdt', '-'),
                error_detail=error_detail_summary
            )
            logger.info(f"[{table_name}] レコードID {record_id}: メール送信完了（TO={len(to_addresses)}件, CC={len(cc_addresses)}件）、履歴を記録しました")
        else:
            logger.error(f"[{table_name}] レコードID {record_id}: メール送信に失敗しました")

    def _generate_record_id(self, table_name: str, record: Dict) -> str:
        """
        レコードから一意のIDを生成

        Args:
            table_name: テーブル名
            record: レコード

        Returns:
            レコードID（例: "PONO-POLINENO-INSTDT" または "ALCNO-ALCLINENO-INSTDT"）
        """
        instdt = record.get("INSTDT", "")

        # DK020（受入）の場合: PONO + POLINENO + INSTDT で識別
        if table_name == "DK020":
            pono = record.get("PONO", "")
            polineno = record.get("POLINENO", "")
            return f"{pono}-{polineno}-{instdt}"

        # DK040（棚出）の場合: ALCNO + ALCLINENO + INSTDT で識別
        elif table_name == "DK040":
            alcno = record.get("ALCNO", "")
            alclineno = record.get("ALCLINENO", "")
            return f"{alcno}-{alclineno}-{instdt}"

        # その他のテーブルの場合: 全フィールドを結合
        return "-".join(str(v) for v in record.values() if v is not None)

    def _format_error_detail(self, table_name: str, record: Dict) -> str:
        """
        エラー詳細をフォーマット

        Args:
            table_name: テーブル名
            record: レコード

        Returns:
            エラー詳細文字列
        """
        details = []

        if table_name == "DK020":
            # DK020（受入）の主要フィールド
            details.append(f"発注番号: {record.get('PONO', '-')}")
            details.append(f"行番号: {record.get('POLINENO', '-')}")
            details.append(f"登録日時: {record.get('INSTDT', '-')}")
            details.append(f"処理済区分: {record.get('SYORIZUMIKBN', '-')} (3=エラー)")
            details.append(f"更新社員: {record.get('IPTANCD', '-')}")

        elif table_name == "DK040":
            # DK040（棚出）の主要フィールド
            details.append(f"引当番号: {record.get('ALCNO', '-')}")
            details.append(f"行番号: {record.get('ALCLINENO', '-')}")
            details.append(f"登録日時: {record.get('INSTDT', '-')}")
            details.append(f"処理済区分: {record.get('SYORIZUMIKBN', '-')} (3=エラー)")
            details.append(f"更新社員: {record.get('IPTANCD', '-')}")

        else:
            # その他のテーブルの場合は全フィールドを表示
            for key, value in record.items():
                details.append(f"{key}: {value}")

        return "\n".join(details)

    def _extract_record_info(self, table_name: str, record: Dict, record_id: str, employee_code: str, employee_name: str) -> Dict:
        """
        メール表示用のレコード情報を抽出

        Args:
            table_name: テーブル名
            record: レコード
            record_id: レコードID
            employee_code: 社員コード
            employee_name: 社員名

        Returns:
            メール表示用の情報辞書
        """
        # 登録日時をフォーマット
        def format_datetime(instdt_str: str) -> str:
            """INSTDTをYYYY/MM/DD HH:MM:SS形式にフォーマット"""
            if not instdt_str or instdt_str == "-":
                return "-"
            try:
                instdt_str = str(instdt_str).strip()
                
                # 既に / を含む場合（フォーマット済みまたはエラー）
                if "/" in instdt_str:
                    return instdt_str
                
                # ISO形式（YYYY-MM-DDTHH:MM:SS または YYYY-MM-DD HH:MM:SS）
                if "T" in instdt_str:
                    # YYYY-MM-DDTHH:MM:SS -> YYYY/MM/DD HH:MM:SS
                    date_part, time_part = instdt_str.split("T")
                    date_part = date_part.replace("-", "/")
                    return f"{date_part} {time_part}"
                elif "-" in instdt_str and " " in instdt_str:
                    # YYYY-MM-DD HH:MM:SS -> YYYY/MM/DD HH:MM:SS
                    parts = instdt_str.split(" ")
                    date_part = parts[0].replace("-", "/")
                    return f"{date_part} {parts[1]}"
                
                # 14桁の数値文字列 (YYYYMMDDHHmmss)
                elif len(instdt_str) >= 14 and instdt_str.isdigit():
                    year = instdt_str[0:4]
                    month = instdt_str[4:6]
                    day = instdt_str[6:8]
                    hour = instdt_str[8:10]
                    minute = instdt_str[10:12]
                    second = instdt_str[12:14]
                    return f"{year}/{month}/{day} {hour}:{minute}:{second}"
                
                # その他の形式はそのまま返す
                return instdt_str
                
            except Exception as e:
                logger.warning(f"日時フォーマットエラー: {instdt_str}, {e}")
                return str(instdt_str)

        if table_name == "DK020":
            # DK020（受入）の場合
            pono = record.get("PONO", "-")
            polineno = record.get("POLINENO", "-")
            
            # D3340から詳細情報を取得
            detail = self._fetch_order_detail("D3340", pono, polineno)
            
            return {
                "record_id": record_id,
                "order_no": pono,
                "order_label": "発注番号",
                "line_no": polineno,
                "instdt": format_datetime(record.get("INSTDT", "-")),
                "iptancd": employee_code,
                "employee_name": employee_name,
                "listno": detail.get("LISTNO", "-"),
                "hmcd": detail.get("HMCD", "-"),
                "hmnm": detail.get("HMNM", "-")
            }
        elif table_name == "DK040":
            # DK040（棚出）の場合
            alcno = record.get("ALCNO", "-")
            alclineno = record.get("ALCLINENO", "-")
            
            # D3520から詳細情報を取得
            detail = self._fetch_order_detail("D3520", alcno, alclineno)
            
            return {
                "record_id": record_id,
                "order_no": alcno,
                "order_label": "引当番号",
                "line_no": alclineno,
                "instdt": format_datetime(record.get("INSTDT", "-")),
                "iptancd": employee_code,
                "employee_name": employee_name,
                "listno": detail.get("LISTNO", "-"),
                "hmcd": detail.get("HMCD", "-"),
                "hmnm": detail.get("HMNM", "-")
            }
        else:
            # その他の場合
            return {
                "record_id": record_id,
                "order_no": "-",
                "order_label": "番号",
                "line_no": "-",
                "instdt": format_datetime(record.get("INSTDT", "-")),
                "iptancd": employee_code,
                "employee_name": employee_name,
                "listno": "-",
                "hmcd": "-",
                "hmnm": "-"
            }

    def _fetch_order_detail(self, table_name: str, order_no: str, line_no: str) -> Dict:
        """
        発注または棚出の詳細情報を取得

        Args:
            table_name: 参照先テーブル名（D3340 or D3520）
            order_no: 発注番号またはALCNO
            line_no: 行番号

        Returns:
            詳細情報（LISTNO, HMCD, HMNM）
        """
        try:
            # D3340（発注）またはD3520（棚出）から詳細を取得
            if table_name == "D3340":
                key_field = "PONO"
            elif table_name == "D3520":
                key_field = "ALCNO"
            else:
                return {"LISTNO": "-", "HMCD": "-", "HMNM": "-"}

            payload = {
                "table": table_name,
                "columns": ["LISTNO", "HMCD", "HMNM"],
                "where": {
                    "and": [
                        {key_field: order_no},
                        {"LINENO": line_no}
                    ]
                }
            }

            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            rows = data.get("rows", [])
            
            if rows:
                return rows[0]
            else:
                logger.warning(f"{table_name}から詳細情報が取得できませんでした: {key_field}={order_no}, LINENO={line_no}")
                return {"LISTNO": "-", "HMCD": "-", "HMNM": "-"}

        except requests.exceptions.RequestException as e:
            logger.error(f"{table_name}詳細取得エラー: {e}")
            return {"LISTNO": "-", "HMCD": "-", "HMNM": "-"}


    def _monitor_expense_tool_acceptance(self):
        """
        経費工具受入を監視してメール送信

        条件:
        - DK020で SYORIZUMIKBN='2' (正常終了)
        - D3340のSEINOが "KEIHI"
        """
        logger.info("[経費工具受入] 監視開始")

        try:
            # DK020で正常終了したレコードを取得
            payload = {
                "table": "DK020",
                "where": {
                    "SYORIZUMIKBN": "2"  # 正常終了
                }
            }

            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            records = data.get("rows", [])

            if not records:
                logger.info("[経費工具受入] 正常終了データは見つかりませんでした")
                return

            logger.info(f"[経費工具受入] {len(records)}件の正常終了データを検出しました")

            # 各レコードをチェック
            expense_tool_count = 0
            for record in records:
                pono = record.get("PONO")
                polineno = record.get("POLINENO")

                if not pono or not polineno:
                    continue

                # D3340からSEINOと仕入先を含む詳細情報を取得
                detail_payload = {
                    "table": "D3340",
                    "columns": ["SEINO", "HMNM", "SRCD"],
                    "where": {
                        "and": [
                            {"PONO": pono},
                            {"LINENO": polineno}
                        ]
                    }
                }

                try:
                    detail_response = requests.post(self.api_url, json=detail_payload, headers=self.headers, timeout=30)
                    detail_response.raise_for_status()
                    detail_data = detail_response.json()
                    detail_rows = detail_data.get("rows", [])

                    if not detail_rows:
                        logger.debug(f"[経費工具受入] D3340データなし: PONO={pono}, LINENO={polineno}")
                        continue

                    detail = detail_rows[0]
                    seino = detail.get("SEINO", "")

                    # SEINOが"KEIHI"の場合のみ処理
                    if seino == "KEIHI":
                        expense_tool_count += 1
                        self._process_expense_tool_record(record, detail)

                except requests.exceptions.RequestException as e:
                    logger.error(f"[経費工具受入] D3340取得エラー: PONO={pono}, LINENO={polineno}, {e}")
                    continue

            logger.info(f"[経費工具受入] 経費工具該当件数: {expense_tool_count}件")

        except requests.exceptions.RequestException as e:
            logger.error(f"[経費工具受入] DK020取得エラー: {e}")
        except Exception as e:
            logger.error(f"[経費工具受入] 監視処理中にエラーが発生しました: {e}", exc_info=True)

    def _process_expense_tool_record(self, record: Dict, detail: Dict):
        """
        経費工具受入レコードを処理してメール送信

        Args:
            record: DK020のレコード
            detail: D3340のレコード（SEINO, HMNM, SRCD）
        """
        # レコードIDを生成
        pono = record.get("PONO", "")
        polineno = record.get("POLINENO", "")
        instdt = record.get("INSTDT", "")
        record_id = f"{pono}-{polineno}-{instdt}"

        employee_code = record.get("IPTANCD")

        if not employee_code:
            logger.warning(f"[経費工具受入] レコードID {record_id}: 社員コード（IPTANCD）が見つかりません")
            return

        logger.info(f"[経費工具受入] レコードID {record_id}: 社員コード {employee_code} を処理中")

        # 送信済みかチェック（テーブル名はDK020だが、履歴では区別される）
        if self.db_manager.is_mail_sent("DK020_EXPENSE_TOOL", record_id):
            logger.info(f"[経費工具受入] レコードID {record_id}: 既にメール送信済みです")
            return

        # 社員情報を取得
        employee = self.db_manager.get_employee_by_tancd(employee_code)
        if not employee:
            logger.warning(f"[経費工具受入] レコードID {record_id}: 社員コード {employee_code} の社員情報が見つかりません")
            return

        employee_name = employee.get("tannm") or employee_code

        # 仕入先名を取得
        srcd = detail.get("SRCD", "")
        vendor_name = "-"
        if srcd:
            try:
                vendor_payload = {
                    "table": "M0710",
                    "columns": ["HTRNM1"],
                    "where": {"HTRCD": srcd}
                }
                vendor_response = requests.post(self.api_url, json=vendor_payload, headers=self.headers, timeout=30)
                vendor_response.raise_for_status()
                vendor_data = vendor_response.json()
                vendor_rows = vendor_data.get("rows", [])
                if vendor_rows:
                    vendor_name = vendor_rows[0].get("HTRNM1", "-")
            except Exception as e:
                logger.warning(f"[経費工具受入] 仕入先名取得エラー: SRCD={srcd}, {e}")

        # メール送信先を取得（TO/CC）
        to_emails = self.db_manager.get_recipients(employee_code, "expense_tool", "TO")
        cc_emails = self.db_manager.get_recipients(employee_code, "expense_tool", "CC")

        # メールアドレスのリストを抽出
        to_addresses = [r["email_address"] for r in to_emails]
        cc_addresses = [r["email_address"] for r in cc_emails]

        if not to_addresses and not cc_addresses:
            logger.warning(f"[経費工具受入] レコードID {record_id}: 社員コード {employee_code} のメール送信先が設定されていません")

            # 登録日時をフォーマット
            instdt_formatted = self._format_datetime(instdt)

            # 送信先未設定でも履歴に記録（再送信を防ぐため）
            self.db_manager.add_mail_history(
                table_name="DK020_EXPENSE_TOOL",
                record_id=record_id,
                employee_code=employee_code,
                employee_name=employee_name,
                to_addresses=["（送信先未設定）"],
                cc_addresses=[],
                function_name="経費工具受入機能",
                order_no=pono,
                order_label="発注番号",
                line_no=polineno,
                listno=f"{srcd} ({vendor_name})",  # 仕入先コード (仕入先名)
                hmcd=str(record.get("RCVQTY", "-")),  # 受入数
                hmnm=detail.get("HMNM", "-"),
                instdt=instdt_formatted,
                error_detail="メール送信先が設定されていないため送信スキップ"
            )
            logger.info(f"[経費工具受入] レコードID {record_id}: 送信先未設定として履歴を記録しました")
            return

        logger.info(f"[経費工具受入] レコードID {record_id}: {employee_name} にメールを送信します（TO={to_addresses}, CC={cc_addresses}）")

        # 登録日時をフォーマット
        instdt_formatted = self._format_datetime(instdt)

        # メール送信用のデータを作成
        record_info = {
            "record_id": record_id,
            "order_no": pono,
            "order_label": "発注番号",
            "line_no": polineno,
            "instdt": instdt_formatted,
            "iptancd": employee_code,
            "employee_name": employee_name,
            "listno": f"{srcd} ({vendor_name})",  # 仕入先コード (仕入先名)
            "hmcd": str(record.get("RCVQTY", "-")),  # 受入数
            "hmnm": detail.get("HMNM", "-")
        }

        error_data = {
            "function_name": "経費工具受入機能",
            "record_info": record_info
        }

        # メール送信
        if self.mail_sender.send_error_notification(to_addresses, cc_addresses, employee_name, error_data):
            # 送信履歴を記録
            error_detail_summary = f"経費工具受入機能 - {pono} / {polineno}"
            self.db_manager.add_mail_history(
                table_name="DK020_EXPENSE_TOOL",
                record_id=record_id,
                employee_code=employee_code,
                employee_name=employee_name,
                to_addresses=to_addresses,
                cc_addresses=cc_addresses,
                function_name="経費工具受入機能",
                order_no=pono,
                order_label="発注番号",
                line_no=polineno,
                listno=f"{srcd} ({vendor_name})",  # 仕入先コード (仕入先名)
                hmcd=str(record.get("RCVQTY", "-")),  # 受入数
                hmnm=detail.get("HMNM", "-"),
                instdt=instdt_formatted,
                error_detail=error_detail_summary
            )
            logger.info(f"[経費工具受入] レコードID {record_id}: メール送信完了（TO={len(to_addresses)}件, CC={len(cc_addresses)}件）、履歴を記録しました")
        else:
            logger.error(f"[経費工具受入] レコードID {record_id}: メール送信に失敗しました")

    def _format_datetime(self, instdt_str: str) -> str:
        """INSTDTをYYYY/MM/DD HH:MM:SS形式にフォーマット"""
        if not instdt_str or instdt_str == "-":
            return "-"
        try:
            instdt_str = str(instdt_str).strip()

            # 既に / を含む場合（フォーマット済みまたはエラー）
            if "/" in instdt_str:
                return instdt_str

            # ISO形式（YYYY-MM-DDTHH:MM:SS または YYYY-MM-DD HH:MM:SS）
            if "T" in instdt_str:
                # YYYY-MM-DDTHH:MM:SS -> YYYY/MM/DD HH:MM:SS
                date_part, time_part = instdt_str.split("T")
                date_part = date_part.replace("-", "/")
                return f"{date_part} {time_part}"
            elif "-" in instdt_str and " " in instdt_str:
                # YYYY-MM-DD HH:MM:SS -> YYYY/MM/DD HH:MM:SS
                parts = instdt_str.split(" ")
                date_part = parts[0].replace("-", "/")
                return f"{date_part} {parts[1]}"

            # 14桁の数値文字列 (YYYYMMDDHHmmss)
            elif len(instdt_str) >= 14 and instdt_str.isdigit():
                year = instdt_str[0:4]
                month = instdt_str[4:6]
                day = instdt_str[6:8]
                hour = instdt_str[8:10]
                minute = instdt_str[10:12]
                second = instdt_str[12:14]
                return f"{year}/{month}/{day} {hour}:{minute}:{second}"

            # その他の形式はそのまま返す
            return instdt_str

        except Exception as e:
            logger.warning(f"日時フォーマットエラー: {instdt_str}, {e}")
            return str(instdt_str)


def main():
    """メイン実行関数"""
    monitor = ErrorMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
