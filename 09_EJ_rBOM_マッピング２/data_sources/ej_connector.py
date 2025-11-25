"""
EJシステム接続モジュール
"""
import oracledb
import pandas as pd
from datetime import datetime, date
from typing import List, Dict
import os
from dotenv import load_dotenv
import logging

# 環境変数読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class EJConnector:
    """EJシステム（Oracle Database）接続クラス"""

    # クラス変数でthick mode初期化フラグを管理
    _thick_mode_initialized = False

    def __init__(self):
        """初期化"""
        # thick modeの初期化（初回のみ実行）
        if not EJConnector._thick_mode_initialized:
            try:
                oracledb.init_oracle_client()
                EJConnector._thick_mode_initialized = True
                logger.info("oracledb thick mode初期化完了")
            except Exception as e:
                # 既に初期化済みの場合はエラーを無視
                logger.debug(f"oracledb thick mode初期化スキップ: {str(e)}")

        # データベース接続情報（環境変数または固定値）
        self.host = os.getenv('EJ_DB_HOST', '172.17.107.102')
        self.port = os.getenv('EJ_DB_PORT', '1521')
        self.service_name = os.getenv('EJ_DB_SERVICE', 'EXPJ')
        self.username = os.getenv('EJ_DB_USER', 'EXPJ2')
        self.password = os.getenv('EJ_DB_PASSWORD', 'EXPJ2')

        # 接続文字列
        self.connection_string = f"{self.username}/{self.password}@{self.host}:{self.port}/{self.service_name}"
    
    def get_connection(self):
        """データベース接続を取得"""
        try:
            connection = oracledb.connect(self.connection_string)
            return connection
        except oracledb.DatabaseError as e:
            raise Exception(f"EJシステムへの接続に失敗しました: {str(e)}")
    
    def get_order_backlog(self, start_date: date, end_date: date) -> List[Dict]:
        """
        発注残データを取得（2025年11月1日〜2027年1月31日の範囲）

        Args:
            start_date: 納期開始日（2025年11月1日以降）
            end_date: 納期終了日（2027年1月31日まで）

        Returns:
            発注残データのリスト
        """
        logger.info(f"EJデータ取得開始: {start_date} 〜 {end_date}")

        # 日付範囲のバリデーション
        min_date = date(2025, 11, 1)
        max_date = date(2027, 1, 31)

        if start_date < min_date:
            raise ValueError(f"納期開始日は{min_date}以降を指定してください。データ量削減のための制限です。")

        if end_date > max_date:
            raise ValueError(f"納期終了日は{max_date}以前を指定してください。データ範囲の制限です。")
        
        # query = """
        #     SELECT 
        #         t.PUCH_ODR_CD as order_no,
        #         t.ITEM_CD as item_code,
        #         m.ITEM_NAME as item_name,
        #         t.PUCH_ODR_QTY as quantity,
        #         t.PUCH_ODR_DLV_DATE as delivery_date
        #     FROM EXPJ2.T_RLSD_PUCH_ODR t
        #     LEFT JOIN EXPJ2.M_ITEM m ON t.ITEM_CD = m.ITEM_CD
        #     WHERE 1=1
        #       -- AND t.PUCH_ODR_DLV_DATE >= :start_date 
        #       -- AND t.PUCH_ODR_DLV_DATE <= :end_date
        #       AND t.ACPT_CMPLT_DATE IS NULL  -- 受入完了日が空欄のもののみ
        #     ORDER BY t.PUCH_ODR_CD
        # """
        # #AND t.PUCH_ODR_DLV_DATE >= DATE '2025-07-01'  -- 固定条件

        query = """
            SELECT
                t.PUCH_ODR_CD as order_no,
                t.ITEM_CD as item_code,
                m.ITEM_NAME as item_name,
                t.PUCH_ODR_QTY as quantity,
                t.PUCH_ODR_STS_TYP as status,
                t.PUCH_ODR_TYP as purch_odr_typ,
                t.PUCH_ODR_DLV_DATE as delivery_date,
                t.VEND_CD as vend_cd
            FROM EXPJ2.T_RLSD_PUCH_ODR t
            LEFT JOIN EXPJ2.M_ITEM m ON t.ITEM_CD = m.ITEM_CD
            WHERE t.PUCH_ODR_STS_TYP = 2
            AND t.PUCH_ODR_TYP != 4
            AND t.PUCH_ODR_DLV_DATE >= DATE '2025-11-01'
            AND t.PUCH_ODR_DLV_DATE <= DATE '2027-01-31'
            ORDER BY t.PUCH_ODR_CD
        """
        #WHERE t.PUCH_ODR_STS_TYP = 2 1は未発注、
        #AND t.ACPT_CMPLT_DATE IS NULL  -- 受入完了日が空欄のもののみ
        #AND t.PUCH_ODR_DLV_DATE >= DATE '2025-11-01'  -- 開始日固定条件
        #AND t.PUCH_ODR_DLV_DATE <= DATE '2027-01-31'  -- 終了日固定条件


        try:
            query_start = datetime.now()
            with self.get_connection() as conn:
                logger.debug(f"Oracle接続確立 ({(datetime.now() - query_start).total_seconds():.3f}秒)")

                cursor = conn.cursor()

                # クエリ実行
                execute_start = datetime.now()
                cursor.execute(query)
                logger.debug(f"クエリ実行完了 ({(datetime.now() - execute_start).total_seconds():.3f}秒)")

                # 結果取得
                fetch_start = datetime.now()
                columns = [desc[0].lower() for desc in cursor.description]
                rows = cursor.fetchall()
                logger.debug(f"データフェッチ完了: {len(rows)}行 ({(datetime.now() - fetch_start).total_seconds():.3f}秒)")

                # 辞書形式に変換
                convert_start = datetime.now()
                results = []
                for row in rows:
                    record = dict(zip(columns, row))

                    # 日付フィールドの処理
                    if record.get('delivery_date'):
                        record['delivery_date'] = record['delivery_date'].strftime('%Y-%m-%d')

                    # 数値フィールドの明示的な型変換（根本解決: Oracleから取得した数値を確実にPython intに変換）
                    if record.get('status') is not None:
                        record['status'] = int(record['status'])
                    if record.get('purch_odr_typ') is not None:
                        record['purch_odr_typ'] = int(record['purch_odr_typ'])

                    results.append(record)

                logger.debug(f"辞書変換完了 ({(datetime.now() - convert_start).total_seconds():.3f}秒)")
                logger.info(f"EJデータ取得完了: {len(results)}件 (合計: {(datetime.now() - query_start).total_seconds():.3f}秒)")

                return results

        except oracledb.DatabaseError as e:
            raise Exception(f"EJシステムからのデータ取得に失敗しました: {str(e)}")
        except Exception as e:
            raise Exception(f"予期しないエラーが発生しました: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        接続テスト
        
        Returns:
            接続成功の場合True
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception:
            return False
    
    def get_database_info(self) -> Dict:
        """
        データベース情報を取得
        
        Returns:
            データベース情報の辞書
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # バージョン情報取得
                cursor.execute("SELECT * FROM V$VERSION WHERE ROWNUM = 1")
                version_info = cursor.fetchone()[0]
                
                # 発注残テーブルのレコード数取得（2025/11/1〜2027/1/31）
                cursor.execute("""
                    SELECT COUNT(*) FROM EXPJ2.T_RLSD_PUCH_ODR
                    WHERE PUCH_ODR_DLV_DATE >= DATE '2025-11-01'
                    AND PUCH_ODR_DLV_DATE <= DATE '2027-01-31'
                """)
                record_count = cursor.fetchone()[0]

                return {
                    'version': version_info,
                    'record_count_20251101_to_20270131': record_count,
                    'connection_string': f"{self.host}:{self.port}/{self.service_name}",
                    'username': self.username
                }
                
        except Exception as e:
            return {'error': str(e)}