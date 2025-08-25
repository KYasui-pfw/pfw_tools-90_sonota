"""
rBOMシステム接続モジュール（API経由）
"""
import requests
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

class RBOMConnector:
    """rBOMシステム（API）接続クラス"""
    
    def __init__(self):
        """初期化"""
        # API接続情報（直接記述でテスト）
        self.base_url = 'http://pfw-api'
        self.api_key = r'oG5^Ls%#20yq'  # raw stringで特殊文字をエスケープ
        
        # APIエンドポイント
        self.orders_endpoint = f"{self.base_url}/orders/"
        
        # リクエストヘッダー（curlテスト結果に基づく正しい形式）
        self.headers = {
            'X-API-KEY': self.api_key,  # 正しい認証ヘッダー形式
            'accept': 'application/json'
        }
    
    def get_orders(self, year: int, month: int, cycle: Optional[int] = None) -> List[Dict]:
        """
        発注明細データを取得
        
        Args:
            year: 年（例: 2025）
            month: 月（例: 8）
            cycle: 次（省略可能）
            
        Returns:
            発注明細データのリスト
        """
        
        # リクエストパラメータ
        params = {
            'year': year,
            'month': month
        }
        
        if cycle is not None:
            params['cycle'] = cycle
        
        try:
            # APIリクエスト実行
            response = requests.get(
                self.orders_endpoint,
                params=params,
                headers=self.headers,
                timeout=30  # 30秒タイムアウト
            )
            
            # レスポンスチェック
            response.raise_for_status()
            
            # JSONデータを取得
            data = response.json()
            
            # データの正規化
            normalized_data = []
            for item in data:
                record = {
                    'order_no': item.get('PONO'),
                    'line_no': item.get('LINENO'),
                    'status': item.get('STATUS'),
                    'seino': item.get('SEINO'),
                    'item_code': item.get('HMCD'),
                    'item_name': item.get('HMNM'),
                    'delivery_date': item.get('DRVDT'),
                    'receive_date': item.get('RECDT'),
                    
                    # D3010テーブル情報
                    'd3010_seino': item.get('D3010_SEINO'),
                    'd3010_item_name': item.get('D3010_HMNM'),
                    'inch': item.get('INCH'),
                    'gauge': item.get('GAUGE'),
                    'deadline': item.get('DEADLINE'),
                    'getsuji': item.get('GETSUJI'),
                    
                    # D3360テーブル情報
                    'd3360_order_no': item.get('D3360_PONO'),
                    'd3360_line_no': item.get('D3360_LINENO'),
                    'receive_date_d3360': item.get('RCVDT'),
                    'receive_quantity': item.get('RCVQTY'),
                    'memo': item.get('MEINOTE'),
                    
                    # DK020テーブル情報
                    'dk020_order_no': item.get('DK020_PONO'),
                    'dk020_line_no': item.get('DK020_LINENO'),
                    'process_status': item.get('SYORIZUMIKB')
                }
                
                # 日付フィールドの正規化
                for date_field in ['delivery_date', 'receive_date', 'deadline', 'receive_date_d3360']:
                    if record.get(date_field):
                        try:
                            # 日付文字列をYYYY-MM-DD形式に統一
                            if isinstance(record[date_field], str):
                                # 既にYYYY-MM-DD形式の場合はそのまま
                                if len(record[date_field]) == 10 and record[date_field][4] == '-':
                                    continue
                                # その他の形式は適宜変換
                                record[date_field] = record[date_field]
                        except:
                            pass
                
                normalized_data.append(record)
            
            return normalized_data
            
        except requests.RequestException as e:
            raise Exception(f"rBOMシステムAPIへのリクエストに失敗しました: {str(e)}")
        except ValueError as e:
            raise Exception(f"rBOMシステムからのレスポンス解析に失敗しました: {str(e)}")
        except Exception as e:
            raise Exception(f"予期しないエラーが発生しました: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        接続テスト
        
        Returns:
            接続成功の場合True
        """
        try:
            # テスト用の最小限のリクエスト
            response = requests.get(
                self.orders_endpoint,
                params={'year': 2025, 'month': 1},
                headers=self.headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_api_info(self) -> Dict:
        """
        API情報を取得
        
        Returns:
            API情報の辞書
        """
        try:
            # テスト接続
            test_result = self.test_connection()
            
            return {
                'base_url': self.base_url,
                'orders_endpoint': self.orders_endpoint,
                'api_key_configured': bool(self.api_key),
                'connection_test': 'OK' if test_result else 'NG'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_orders_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """
        日付範囲でデータを取得（複数月対応）
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            発注明細データのリスト
        """
        all_data = []
        
        # 年月の範囲を計算
        current_date = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        
        while current_date <= end_month:
            try:
                month_data = self.get_orders(current_date.year, current_date.month)
                
                # 日付範囲でフィルタリング
                filtered_data = []
                for item in month_data:
                    delivery_date_str = item.get('delivery_date')
                    if delivery_date_str:
                        try:
                            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
                            if start_date <= delivery_date <= end_date:
                                filtered_data.append(item)
                        except:
                            # 日付変換に失敗した場合はそのまま追加
                            filtered_data.append(item)
                    else:
                        # 納期が設定されていない場合もそのまま追加
                        filtered_data.append(item)
                
                all_data.extend(filtered_data)
                
            except Exception as e:
                # API取得失敗は重要なのでログ出力を復活
                print(f"Warning: {current_date.year}/{current_date.month}のデータ取得に失敗: {str(e)}")
            
            # 次の月へ
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return all_data