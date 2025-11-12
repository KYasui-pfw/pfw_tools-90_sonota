"""
前工程CSVとEJ発注残データの一致抽出スクリプト

EJシステムから取得した発注残データと、前工程.csvの品目コードを比較し、
一致したデータを出力します。
"""
import sys
import os
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import logging

# 親ディレクトリをパスに追加（data_sourcesモジュールをインポートするため）
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from data_sources.ej_connector import EJConnector

# ログ設定
log_dir = current_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"前工程一致抽出_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_zenkohtei_csv(csv_path: Path) -> set:
    """
    前工程CSVを読み込み、品目コードのセットを返す

    Args:
        csv_path: 前工程CSVファイルのパス

    Returns:
        品目コードのセット（前後の空白を削除済み）
    """
    logger.info(f"前工程CSVを読み込み: {csv_path}")

    try:
        # ヘッダーなしで読み込み
        df = pd.read_csv(csv_path, header=None, names=['前工程'], encoding='utf-8')

        # 前後の空白を削除
        df['前工程'] = df['前工程'].astype(str).str.strip()

        # セットに変換（重複除去）
        item_codes = set(df['前工程'].unique())

        logger.info(f"前工程CSVから{len(item_codes)}件のユニークな品目コードを読み込みました")
        logger.debug(f"サンプル（最初の5件）: {list(item_codes)[:5]}")

        return item_codes, df

    except Exception as e:
        logger.error(f"前工程CSVの読み込みに失敗: {str(e)}", exc_info=True)
        raise

def get_ej_data(start_date: date, end_date: date) -> pd.DataFrame:
    """
    EJシステムから発注残データを取得

    Args:
        start_date: 納期開始日
        end_date: 納期終了日

    Returns:
        EJデータのDataFrame
    """
    logger.info(f"EJデータ取得開始: {start_date} 〜 {end_date}")

    try:
        connector = EJConnector()
        ej_data_list = connector.get_order_backlog(start_date, end_date)

        # DataFrameに変換
        df = pd.DataFrame(ej_data_list)

        logger.info(f"EJデータ取得完了: {len(df)}件")

        return df

    except Exception as e:
        logger.error(f"EJデータの取得に失敗: {str(e)}", exc_info=True)
        raise

def match_and_export(ej_df: pd.DataFrame, zenkohtei_codes: set, zenkohtei_df: pd.DataFrame, output_path: Path):
    """
    EJデータと前工程品目コードを照合し、一致データを出力

    Args:
        ej_df: EJデータのDataFrame
        zenkohtei_codes: 前工程品目コードのセット
        zenkohtei_df: 前工程のDataFrame（元のCSVデータ）
        output_path: 出力CSVファイルのパス
    """
    logger.info("EJデータと前工程CSVの照合開始")

    try:
        # EJ品目コードの前後空白を削除
        ej_df['item_code_clean'] = ej_df['item_code'].astype(str).str.strip()

        # 一致判定
        matched_df = ej_df[ej_df['item_code_clean'].isin(zenkohtei_codes)].copy()

        logger.info(f"一致件数: {len(matched_df)}件 / EJ総件数: {len(ej_df)}件")

        if len(matched_df) == 0:
            logger.warning("一致するデータがありませんでした")
            # 空のファイルを作成
            output_df = pd.DataFrame(columns=['order_no', 'item_code', 'item_name', 'quantity',
                                             'status', 'purch_odr_typ', 'delivery_date', '前工程'])
            output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"空のCSVファイルを出力: {output_path}")
            return

        # 前工程列を追加（マッチした品目コードをそのまま追加）
        matched_df['前工程'] = matched_df['item_code_clean']

        # 出力用に列を選択（item_code_cleanは除外、元のitem_codeを使用）
        output_df = matched_df[['order_no', 'item_code', 'item_name', 'quantity',
                               'status', 'purch_odr_typ', 'delivery_date', '前工程']]

        # 出力ディレクトリ作成
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # CSV出力（BOM付きUTF-8でExcel対応）
        output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        logger.info(f"一致データをCSV出力: {output_path}")
        logger.info(f"出力件数: {len(output_df)}件")

        # 統計情報を出力
        logger.info("=== 統計情報 ===")
        logger.info(f"EJ総件数: {len(ej_df)}件")
        logger.info(f"前工程ユニーク品目コード数: {len(zenkohtei_codes)}件")
        logger.info(f"一致件数: {len(matched_df)}件")
        logger.info(f"一致率: {len(matched_df)/len(ej_df)*100:.2f}%")

        # 一致した品目コードの内訳
        matched_items = matched_df['item_code_clean'].value_counts()
        logger.info(f"\n一致した品目コード別件数（上位10件）:")
        for item, count in matched_items.head(10).items():
            logger.info(f"  {item}: {count}件")

    except Exception as e:
        logger.error(f"照合処理に失敗: {str(e)}", exc_info=True)
        raise

def main():
    """メイン処理"""
    logger.info("=" * 80)
    logger.info("前工程一致抽出スクリプト開始")
    logger.info("=" * 80)

    try:
        # パス設定
        input_csv = current_dir / "input" / "前工程.csv"
        output_csv = current_dir / "output" / "前工程_EJ発注残_一致.csv"

        # 入力ファイル存在チェック
        if not input_csv.exists():
            raise FileNotFoundError(f"入力ファイルが見つかりません: {input_csv}")

        # 1. 前工程CSVを読み込み
        zenkohtei_codes, zenkohtei_df = load_zenkohtei_csv(input_csv)

        # 2. EJデータ取得（固定の日付範囲）
        start_date = date(2025, 7, 1)
        end_date = date(2027, 1, 31)
        ej_df = get_ej_data(start_date, end_date)

        # 3. 照合と出力
        match_and_export(ej_df, zenkohtei_codes, zenkohtei_df, output_csv)

        logger.info("=" * 80)
        logger.info("前工程一致抽出スクリプト正常終了")
        logger.info("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"スクリプト実行中にエラーが発生しました: {str(e)}")
        logger.error("=" * 80)
        raise

if __name__ == "__main__":
    main()
