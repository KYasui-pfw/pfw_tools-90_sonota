"""
MK020マスタ接続モジュール（Generic Query API経由）
"""
import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class MK020Connector:
    """MK020マスタテーブル接続クラス"""

    def __init__(self):
        """初期化"""
        # API接続情報
        self.base_url = 'http://pfw-api'
        self.api_key = r'oG5^Ls%#20yq'

        # Generic Query APIエンドポイント
        self.query_endpoint = f"{self.base_url}/query"

        # リクエストヘッダー
        self.headers = {
            'X-API-KEY': self.api_key,
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_mk020_data(self) -> List[Dict]:
        """
        MK020マスタデータを取得

        Returns:
            MK020データのリスト（OYAHMCD, KTCD, SRCD, NOTE, VALQTY, VALDTFを含む）
        """

        try:
            # Generic Query APIリクエストボディ
            request_body = {
                "table": "MK020",
                "columns": ["OYAHMCD", "KTCD", "SRCD", "NOTE", "VALQTY", "VALDTF"]
                # limitを指定しない = 全件取得
            }

            logger.info("MK020データ取得開始")

            # APIリクエスト実行
            response = requests.post(
                self.query_endpoint,
                json=request_body,
                headers=self.headers,
                timeout=60  # 60秒タイムアウト
            )

            # レスポンスチェック
            response.raise_for_status()

            # JSONデータを取得
            data = response.json()

            # データの正規化
            normalized_data = []
            for row in data.get('rows', []):
                record = {
                    'oyahmcd': row.get('OYAHMCD'),
                    'ktcd': row.get('KTCD'),
                    'srcd': row.get('SRCD'),
                    'note': row.get('NOTE'),
                    'valqty': row.get('VALQTY'),
                    'valdtf': row.get('VALDTF')
                }
                normalized_data.append(record)

            logger.info(f"MK020データ取得完了: {len(normalized_data)}件")
            return normalized_data

        except requests.RequestException as e:
            logger.error(f"MK020マスタAPIへのリクエストに失敗しました: {str(e)}")
            raise Exception(f"MK020マスタAPIへのリクエストに失敗しました: {str(e)}")
        except ValueError as e:
            logger.error(f"MK020マスタからのレスポンス解析に失敗しました: {str(e)}")
            raise Exception(f"MK020マスタからのレスポンス解析に失敗しました: {str(e)}")
        except Exception as e:
            logger.error(f"予期しないエラーが発生しました: {str(e)}")
            raise Exception(f"予期しないエラーが発生しました: {str(e)}")

    def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            接続成功の場合True
        """
        try:
            # テスト用の最小限のリクエスト
            request_body = {
                "table": "MK020",
                "columns": ["OYAHMCD"],
                "limit": 1
            }

            response = requests.post(
                self.query_endpoint,
                json=request_body,
                headers=self.headers,
                timeout=10
            )

            return response.status_code == 200

        except Exception:
            return False
