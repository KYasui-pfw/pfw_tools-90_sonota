"""
D3360受入明細ファイル接続モジュール（Generic Query API経由）

D3360テーブル（受入明細ファイル）のNOTE列から原材料情報を取得し、
EJ発注番号とrBOM発注番号のマッピングに使用する
"""
import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class D3360Connector:
    """D3360受入明細ファイル接続クラス"""

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

    def get_d3360_note_data(self) -> List[Dict]:
        """
        D3360テーブルからNOTE列に原材料情報が入っているデータを取得

        NOTE列のパターン:
        - "(原材料)E8921079" → 有効（"(原材料)"を除去してEJ発注番号を取得）
        - "(原材料)" → 無効（EJ発注番号がない）
        - 空欄 → 無効

        Returns:
            D3360データのリスト（PONO, POLINENO, NOTEを含む）
            ※NOTE列が"(原材料)"で始まり、かつ8文字以上のEJ発注番号を持つもののみ
        """

        try:
            # Generic Query APIリクエストボディ
            # NOTE列に"(原材料)"が含まれるデータのみ取得
            request_body = {
                "table": "D3360",
                "columns": ["PONO", "POLINENO", "NOTE"],
                "where": {
                    "NOTE": {"like": "(原材料)%"}
                }
            }

            logger.info("D3360原材料データ取得開始")

            # APIリクエスト実行
            response = requests.post(
                self.query_endpoint,
                json=request_body,
                headers=self.headers,
                timeout=120  # 120秒タイムアウト（データ量が多い可能性）
            )

            # レスポンスチェック
            response.raise_for_status()

            # JSONデータを取得
            data = response.json()

            # データの正規化とフィルタリング
            normalized_data = []
            for row in data.get('rows', []):
                note = row.get('NOTE', '')

                if not note:
                    continue

                # "(原材料)"プレフィックスの長さは5文字
                prefix = "(原材料)"
                if not note.startswith(prefix):
                    continue

                # プレフィックスを除去してEJ発注番号を取得
                ej_order_no = note[len(prefix):]

                # EJ発注番号が空または空白のみの場合はスキップ
                if not ej_order_no or not ej_order_no.strip():
                    logger.debug(f"D3360 NOTE='{note}' - EJ発注番号が空のためスキップ")
                    continue

                record = {
                    'rbom_pono': row.get('PONO'),
                    'rbom_polineno': row.get('POLINENO'),
                    'note': note,
                    'ej_order_no': ej_order_no.strip()  # 抽出したEJ発注番号
                }
                normalized_data.append(record)

            logger.info(f"D3360原材料データ取得完了: {len(normalized_data)}件（有効なEJ発注番号を持つレコード）")
            return normalized_data

        except requests.RequestException as e:
            logger.error(f"D3360 APIへのリクエストに失敗しました: {str(e)}")
            raise Exception(f"D3360 APIへのリクエストに失敗しました: {str(e)}")
        except ValueError as e:
            logger.error(f"D3360からのレスポンス解析に失敗しました: {str(e)}")
            raise Exception(f"D3360からのレスポンス解析に失敗しました: {str(e)}")
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
                "table": "D3360",
                "columns": ["PONO"],
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
