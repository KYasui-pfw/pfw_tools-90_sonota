"""
EJシステム接続モジュール
"""
import cx_Oracle
import pandas as pd
from datetime import datetime, date
from typing import List, Dict
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

class EJConnector:
    """EJシステム（Oracle Database）接続クラス"""
    
    def __init__(self):
        """初期化"""
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
            connection = cx_Oracle.connect(self.connection_string)
            return connection
        except cx_Oracle.DatabaseError as e:
            raise Exception(f"EJシステムへの接続に失敗しました: {str(e)}")
    
    def get_order_backlog(self, start_date: date, end_date: date) -> List[Dict]:
        """
        発注残データを取得（2025年7月1日以降の条件付き）
        
        Args:
            start_date: 納期開始日（2025年7月1日以降）
            end_date: 納期終了日
            
        Returns:
            発注残データのリスト
        """
        
        # 2025年7月1日以前の場合はエラー
        min_date = date(2025, 7, 1)
        if start_date < min_date:
            raise ValueError(f"納期開始日は{min_date}以降を指定してください。データ量削減のための制限です。")
        
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
                t.PUCH_ODR_DLV_DATE as delivery_date
            FROM EXPJ2.T_RLSD_PUCH_ODR t
            LEFT JOIN EXPJ2.M_ITEM m ON t.ITEM_CD = m.ITEM_CD
            WHERE t.PUCH_ODR_STS_TYP = 2
            AND t.PUCH_ODR_TYP != 4
            AND t.PUCH_ODR_DLV_DATE >= DATE '2025-07-01'
            ORDER BY t.PUCH_ODR_CD
        """
        #WHERE t.PUCH_ODR_STS_TYP = 2 1は未発注、
        #AND t.ACPT_CMPLT_DATE IS NULL  -- 受入完了日が空欄のもののみ
        #AND t.PUCH_ODR_DLV_DATE >= DATE '2025-07-01'  -- 固定条件


        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # パラメータをバインド（日付パラメータは一時的にコメントアウト）
                cursor.execute(query)
                # cursor.execute(query, {
                #     'start_date': start_date,
                #     'end_date': end_date
                # })
                
                # 結果を取得
                columns = [desc[0].lower() for desc in cursor.description]
                rows = cursor.fetchall()
                
                # 辞書形式に変換
                results = []
                for row in rows:
                    record = dict(zip(columns, row))
                    
                    # 日付フィールドの処理
                    if record.get('delivery_date'):
                        record['delivery_date'] = record['delivery_date'].strftime('%Y-%m-%d')
                    
                    results.append(record)
                
                return results
                
        except cx_Oracle.DatabaseError as e:
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
                
                # 発注残テーブルのレコード数取得
                cursor.execute("SELECT COUNT(*) FROM EXPJ2.T_RLSD_PUCH_ODR WHERE PUCH_ODR_DLV_DATE >= DATE '2025-07-01'")
                record_count = cursor.fetchone()[0]
                
                return {
                    'version': version_info,
                    'record_count_after_20250701': record_count,
                    'connection_string': f"{self.host}:{self.port}/{self.service_name}",
                    'username': self.username
                }
                
        except Exception as e:
            return {'error': str(e)}