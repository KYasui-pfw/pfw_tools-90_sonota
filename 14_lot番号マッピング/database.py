"""
データベース操作モジュール

PostgreSQLからデータを取得してSQLiteに保存する機能を提供
"""

import os
import logging
import shutil
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
import httpx

# 環境変数の読み込み
load_dotenv()

# ロギング設定
LOG_DIR = os.getenv('LOG_DIR', './logs')
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.txt")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_filename, mode='a', encoding='utf-8')]
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self):
        self.pg_db_url = os.getenv('DB_URL')
        self.sqlite_db_path = os.getenv('SQLITE_DB_PATH', './db/lot_mapping.db')
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.cyl_csv_source = os.getenv('CYL_CSV_SOURCE')

        # FastAPI設定
        self.fastapi_base_url = os.getenv('FASTAPI_BASE_URL', 'http://pfw-api')
        self.read_api_key = os.getenv('READ_API_KEY')

        # SQLiteデータベースディレクトリの作成
        os.makedirs(os.path.dirname(self.sqlite_db_path), exist_ok=True)

        # データディレクトリの作成
        os.makedirs(self.data_dir, exist_ok=True)

        # データベースエンジンの初期化
        self.pg_engine = None
        self.sqlite_engine = None

    def _connect_postgresql(self):
        """PostgreSQLに接続"""
        if self.pg_engine is None:
            try:
                self.pg_engine = create_engine(self.pg_db_url)
                logger.info("PostgreSQL接続成功")
            except Exception as e:
                logger.error(f"PostgreSQL接続エラー: {e}")
                raise
        return self.pg_engine

    def _connect_sqlite(self):
        """SQLiteに接続"""
        if self.sqlite_engine is None:
            try:
                self.sqlite_engine = create_engine(f'sqlite:///{self.sqlite_db_path}')
                logger.info(f"SQLite接続成功: {self.sqlite_db_path}")
            except Exception as e:
                logger.error(f"SQLite接続エラー: {e}")
                raise
        return self.sqlite_engine

    def _initialize_sqlite_table(self):
        """SQLiteテーブルの初期化"""
        engine = self._connect_sqlite()

        # テーブルが存在するかチェック
        inspector = inspect(engine)
        if 'lot_mapping_data' not in inspector.get_table_names():
            create_table_sql = text("""
            CREATE TABLE lot_mapping_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_number TEXT,
                item_code TEXT,
                assembly_number TEXT,
                month TEXT,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lot_number, item_code, assembly_number, month, data_source)
            )
            """)

            with engine.connect() as conn:
                conn.execute(create_table_sql)
                conn.commit()
                logger.info("テーブル lot_mapping_data を作成しました")
        else:
            logger.info("テーブル lot_mapping_data は既に存在します")

        # 新しいテーブルの初期化
        self._initialize_api_instructions_table()
        self._initialize_mapping_results_table()
        self._initialize_manual_mappings_table()

    def _initialize_api_instructions_table(self):
        """APIから取得したデータを格納するテーブルの初期化"""
        engine = self._connect_sqlite()
        inspector = inspect(engine)

        if 'api_instructions' not in inspector.get_table_names():
            create_table_sql = text("""
            CREATE TABLE api_instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indno TEXT NOT NULL,
                hmcd TEXT,
                seino TEXT,
                seino_original TEXT,
                ktcd TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(indno, hmcd, seino, ktcd)
            )
            """)

            with engine.connect() as conn:
                conn.execute(create_table_sql)
                conn.commit()
                logger.info("テーブル api_instructions を作成しました")
        else:
            logger.info("テーブル api_instructions は既に存在します")

    def _initialize_mapping_results_table(self):
        """マッピング結果を格納するテーブルの初期化"""
        engine = self._connect_sqlite()
        inspector = inspect(engine)

        if 'mapping_results' not in inspector.get_table_names():
            create_table_sql = text("""
            CREATE TABLE mapping_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_number TEXT NOT NULL,
                indno TEXT NOT NULL,
                item_code TEXT,
                assembly_number TEXT,
                hmcd TEXT,
                seino TEXT,
                mapping_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lot_number, indno)
            )
            """)

            with engine.connect() as conn:
                conn.execute(create_table_sql)
                conn.commit()
                logger.info("テーブル mapping_results を作成しました")
        else:
            logger.info("テーブル mapping_results は既に存在します")

    def _initialize_manual_mappings_table(self):
        """手動マッピング設定を格納するテーブルの初期化"""
        engine = self._connect_sqlite()
        inspector = inspect(engine)

        if 'manual_mappings' not in inspector.get_table_names():
            create_table_sql = text("""
            CREATE TABLE manual_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_number TEXT NOT NULL,
                seino TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lot_number, seino)
            )
            """)

            with engine.connect() as conn:
                conn.execute(create_table_sql)
                conn.commit()
                logger.info("テーブル manual_mappings を作成しました")
        else:
            logger.info("テーブル manual_mappings は既に存在します")

    def _clean_month_value(self, val):
        """月次データから小数点を除去"""
        if pd.isna(val) or val == '' or val is None:
            return ''
        try:
            # 数値に変換してから整数化して文字列化（小数点を除去）
            return str(int(float(val)))
        except:
            # 変換できない場合はそのまま文字列化
            return str(val).replace('.0', '')

    def fetch_view_report_405(self) -> pd.DataFrame:
        """view_report_405からデータを取得

        Returns:
            pd.DataFrame: 取得したデータ
        """
        engine = self._connect_postgresql()

        # 月次が2024年10月〜2025年11月は取得しない
        # 組立番号が"L"または"K"始まりは取得しない
        query = text("""
        SELECT
            cluster_1_2_t AS lot_number,
            cluster_1_3_t AS item_code,
            cluster_1_5_t AS assembly_number,
            cluster_1_4_t AS month
        FROM view_report_405
        WHERE cluster_1_4_t NOT LIKE '202410%'
          AND cluster_1_4_t NOT LIKE '202411%'
          AND cluster_1_4_t NOT LIKE '202412%'
          AND cluster_1_4_t NOT LIKE '202501%'
          AND cluster_1_4_t NOT LIKE '202502%'
          AND cluster_1_4_t NOT LIKE '202503%'
          AND cluster_1_4_t NOT LIKE '202504%'
          AND cluster_1_4_t NOT LIKE '202505%'
          AND cluster_1_4_t NOT LIKE '202506%'
          AND cluster_1_4_t NOT LIKE '202507%'
          AND cluster_1_4_t NOT LIKE '202508%'
          AND cluster_1_4_t NOT LIKE '202509%'
          AND cluster_1_4_t NOT LIKE '202510%'
          AND cluster_1_4_t NOT LIKE '202511%'
          AND cluster_1_4_t NOT LIKE '2410%'
          AND cluster_1_4_t NOT LIKE '2411%'
          AND cluster_1_4_t NOT LIKE '2412%'
          AND cluster_1_4_t NOT LIKE '2501%'
          AND cluster_1_4_t NOT LIKE '2502%'
          AND cluster_1_4_t NOT LIKE '2503%'
          AND cluster_1_4_t NOT LIKE '2504%'
          AND cluster_1_4_t NOT LIKE '2505%'
          AND cluster_1_4_t NOT LIKE '2506%'
          AND cluster_1_4_t NOT LIKE '2507%'
          AND cluster_1_4_t NOT LIKE '2508%'
          AND cluster_1_4_t NOT LIKE '2509%'
          AND cluster_1_4_t NOT LIKE '2510%'
          AND cluster_1_4_t NOT LIKE '2511%'
          AND cluster_1_5_t NOT LIKE 'L%'
          AND cluster_1_5_t NOT LIKE 'K%'
        """)

        try:
            df = pd.read_sql(query, engine)
            # 月次データから小数点を除去
            df['month'] = df['month'].apply(self._clean_month_value)
            df['data_source'] = 'view_report_405'
            logger.info(f"view_report_405から{len(df)}件のデータを取得しました")
            return df
        except Exception as e:
            logger.error(f"view_report_405データ取得エラー: {e}")
            raise

    def fetch_view_report_334(self) -> pd.DataFrame:
        """view_report_334からデータを取得

        Returns:
            pd.DataFrame: 取得したデータ
        """
        engine = self._connect_postgresql()

        # 月次が2024年10月〜2025年11月は取得しない
        # 組立番号が"L"または"K"始まりは取得しない
        query = text("""
        SELECT
            cluster_1_0_t AS lot_number,
            cluster_1_3_t AS item_code,
            cluster_1_4_t AS assembly_number,
            cluster_1_2_t AS month
        FROM view_report_334
        WHERE cluster_1_2_t NOT LIKE '202410%'
          AND cluster_1_2_t NOT LIKE '202411%'
          AND cluster_1_2_t NOT LIKE '202412%'
          AND cluster_1_2_t NOT LIKE '202501%'
          AND cluster_1_2_t NOT LIKE '202502%'
          AND cluster_1_2_t NOT LIKE '202503%'
          AND cluster_1_2_t NOT LIKE '202504%'
          AND cluster_1_2_t NOT LIKE '202505%'
          AND cluster_1_2_t NOT LIKE '202506%'
          AND cluster_1_2_t NOT LIKE '202507%'
          AND cluster_1_2_t NOT LIKE '202508%'
          AND cluster_1_2_t NOT LIKE '202509%'
          AND cluster_1_2_t NOT LIKE '202510%'
          AND cluster_1_2_t NOT LIKE '202511%'
          AND cluster_1_2_t NOT LIKE '2410%'
          AND cluster_1_2_t NOT LIKE '2411%'
          AND cluster_1_2_t NOT LIKE '2412%'
          AND cluster_1_2_t NOT LIKE '2501%'
          AND cluster_1_2_t NOT LIKE '2502%'
          AND cluster_1_2_t NOT LIKE '2503%'
          AND cluster_1_2_t NOT LIKE '2504%'
          AND cluster_1_2_t NOT LIKE '2505%'
          AND cluster_1_2_t NOT LIKE '2506%'
          AND cluster_1_2_t NOT LIKE '2507%'
          AND cluster_1_2_t NOT LIKE '2508%'
          AND cluster_1_2_t NOT LIKE '2509%'
          AND cluster_1_2_t NOT LIKE '2510%'
          AND cluster_1_2_t NOT LIKE '2511%'
          AND cluster_1_4_t NOT LIKE 'L%'
          AND cluster_1_4_t NOT LIKE 'K%'
        """)

        try:
            df = pd.read_sql(query, engine)
            # 月次データから小数点を除去
            df['month'] = df['month'].apply(self._clean_month_value)
            df['data_source'] = 'view_report_334'
            logger.info(f"view_report_334から{len(df)}件のデータを取得しました")
            return df
        except Exception as e:
            logger.error(f"view_report_334データ取得エラー: {e}")
            raise

    def copy_csv_files(self):
        """CSVファイルをdataフォルダにコピー"""
        try:
            # Cyl_pfw_table_KaLstCyl_All.csvのコピー
            if self.cyl_csv_source and os.path.exists(self.cyl_csv_source):
                cyl_dest = os.path.join(self.data_dir, 'Cyl_pfw_table_KaLstCyl_All.csv')
                shutil.copy2(self.cyl_csv_source, cyl_dest)
                logger.info(f"Cyl CSVファイルをコピーしました: {cyl_dest}")
            else:
                logger.warning(f"Cyl CSVファイルが見つかりません: {self.cyl_csv_source}")

        except Exception as e:
            logger.error(f"CSVファイルコピーエラー: {e}")
            raise

    def fetch_cyl_csv(self) -> pd.DataFrame:
        """Cyl_pfw_table_KaLstCyl_All.csvからデータを取得

        Returns:
            pd.DataFrame: 取得したデータ
        """
        cyl_csv_path = os.path.join(self.data_dir, 'Cyl_pfw_table_KaLstCyl_All.csv')

        if not os.path.exists(cyl_csv_path):
            logger.warning(f"Cyl CSVファイルが存在しません: {cyl_csv_path}")
            return pd.DataFrame(columns=['lot_number', 'item_code', 'assembly_number', 'month', 'data_source'])

        try:
            # CSVファイルを読み込み（複数のエンコーディングを試行）
            encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(cyl_csv_path, encoding=encoding)
                    logger.info(f"Cyl CSVファイルを読み込みました（エンコーディング: {encoding}）")
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise ValueError("CSVファイルを読み込めませんでした")

            # カラム名を確認してマッピング
            df_filtered = pd.DataFrame()
            df_filtered['lot_number'] = df['DENPYONO']
            df_filtered['item_code'] = df['SETU_F']
            df_filtered['assembly_number'] = df['KUMITATENO']
            df_filtered['month'] = df['SEISANJI'].apply(self._clean_month_value)

            # 月次が2024年10月〜2025年11月は取得しない
            excluded_prefixes = [
                '202410', '202411', '202412',
                '202501', '202502', '202503', '202504', '202505', '202506', '202507', '202508', '202509', '202510', '202511',
                '2410', '2411', '2412',
                '2501', '2502', '2503', '2504', '2505', '2506', '2507', '2508', '2509', '2510', '2511'
            ]
            mask = ~df_filtered['month'].astype(str).apply(
                lambda x: any(x.startswith(prefix) for prefix in excluded_prefixes)
            )
            df_filtered = df_filtered[mask]

            # 組立番号が"L"または"K"始まりは取得しない
            df_filtered = df_filtered[
                ~df_filtered['assembly_number'].astype(str).str.startswith('L', na=False) &
                ~df_filtered['assembly_number'].astype(str).str.startswith('K', na=False)
            ]

            df_filtered['data_source'] = 'Cyl_pfw_table_KaLstCyl_All'

            logger.info(f"Cyl CSVから{len(df_filtered)}件のデータを取得しました")
            return df_filtered

        except Exception as e:
            logger.error(f"Cyl CSVデータ取得エラー: {e}")
            return pd.DataFrame(columns=['lot_number', 'item_code', 'assembly_number', 'month', 'data_source'])

    def merge_and_save_data(self) -> int:
        """データを取得・結合してSQLiteに保存

        Returns:
            int: 新規追加されたレコード数
        """
        # テーブル初期化
        self._initialize_sqlite_table()

        # CSVファイルをコピー
        self.copy_csv_files()

        # データ取得
        df_405 = self.fetch_view_report_405()
        df_334 = self.fetch_view_report_334()
        df_cyl = self.fetch_cyl_csv()

        # 縦に結合
        df_combined = pd.concat([df_405, df_334, df_cyl], ignore_index=True)
        logger.info(f"結合後のデータ件数: {len(df_combined)}件")

        # SQLiteに保存（重複は無視）
        engine = self._connect_sqlite()
        inserted_count = 0

        with engine.connect() as conn:
            for _, row in df_combined.iterrows():
                try:
                    insert_sql = text("""
                    INSERT OR IGNORE INTO lot_mapping_data
                    (lot_number, item_code, assembly_number, month, data_source)
                    VALUES (:lot_number, :item_code, :assembly_number, :month, :data_source)
                    """)

                    result = conn.execute(insert_sql, {
                        'lot_number': row['lot_number'],
                        'item_code': row['item_code'],
                        'assembly_number': row['assembly_number'],
                        'month': row['month'],
                        'data_source': row['data_source']
                    })

                    if result.rowcount > 0:
                        inserted_count += 1

                except Exception as e:
                    logger.warning(f"データ挿入エラー（スキップ）: {e}")
                    continue

            conn.commit()

        logger.info(f"新規追加: {inserted_count}件")
        return inserted_count

    def get_all_data(self) -> pd.DataFrame:
        """SQLiteから全データを取得

        Returns:
            pd.DataFrame: 全データ
        """
        # テーブル初期化（存在しない場合のみ）
        self._initialize_sqlite_table()

        engine = self._connect_sqlite()
        query = text("""
        SELECT
            id,
            lot_number AS ロット番号,
            item_code AS 品目コード,
            assembly_number AS 組立番号,
            month AS 月次,
            data_source AS データソース,
            created_at AS 登録日時
        FROM lot_mapping_data
        ORDER BY created_at DESC
        """)

        try:
            df = pd.read_sql(query, engine)
            logger.info(f"SQLiteから{len(df)}件のデータを取得しました")
            return df
        except Exception as e:
            logger.error(f"SQLiteデータ取得エラー: {e}")
            raise

    def _process_seino(self, seino: str) -> str:
        """SEINOを処理（25または26から始まる場合は最後の4文字のみ取得）"""
        if not seino:
            return ''
        seino_str = str(seino).strip()
        if seino_str.startswith('25') or seino_str.startswith('26'):
            if len(seino_str) >= 4:
                return seino_str[-4:]
        return seino_str

    async def fetch_api_instructions(self) -> int:
        """FastAPIから指示データを取得してSQLiteに保存

        Returns:
            int: 新規追加されたレコード数
        """
        # 2025/11～2026/02のデータを取得
        target_periods = [
            (2025, 11), (2025, 12),
            (2026, 1), (2026, 2)
        ]

        all_instructions = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for year, month in target_periods:
                try:
                    url = f"{self.fastapi_base_url}/instructions/"
                    params = {"year": year, "month": month}
                    headers = {"X-API-KEY": self.read_api_key}

                    logger.info(f"API呼び出し: {url} (year={year}, month={month})")
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    all_instructions.extend(data)
                    logger.info(f"{year}年{month}月: {len(data)}件取得")

                except Exception as e:
                    logger.error(f"API取得エラー ({year}年{month}月): {e}")
                    continue

        logger.info(f"API総取得件数: {len(all_instructions)}件")

        # SQLiteに保存
        engine = self._connect_sqlite()
        inserted_count = 0

        with engine.connect() as conn:
            for instruction in all_instructions:
                try:
                    indno = instruction.get('INDNO', '')
                    hmcd = instruction.get('HMCD', '')
                    seino_original = instruction.get('SEINO', '')
                    seino = self._process_seino(seino_original)
                    ktcd = instruction.get('KTCD', '')

                    insert_sql = text("""
                    INSERT OR IGNORE INTO api_instructions
                    (indno, hmcd, seino, seino_original, ktcd)
                    VALUES (:indno, :hmcd, :seino, :seino_original, :ktcd)
                    """)

                    result = conn.execute(insert_sql, {
                        'indno': indno,
                        'hmcd': hmcd,
                        'seino': seino,
                        'seino_original': seino_original,
                        'ktcd': ktcd
                    })

                    if result.rowcount > 0:
                        inserted_count += 1

                except Exception as e:
                    logger.warning(f"データ挿入エラー（スキップ）: {e}")
                    continue

            conn.commit()

        logger.info(f"API新規追加: {inserted_count}件")
        return inserted_count

    def execute_mapping(self) -> Dict[str, int]:
        """マッピング処理を実行

        Returns:
            Dict[str, int]: マッピング結果の統計
        """
        engine = self._connect_sqlite()

        auto_mapped = 0
        manual_mapped = 0

        with engine.connect() as conn:
            # 既存のマッピング結果をクリア
            conn.execute(text("DELETE FROM mapping_results"))

            # 自動マッピング: 品目コード=HMCD かつ 組立番号=SEINO
            auto_mapping_sql = text("""
            INSERT OR IGNORE INTO mapping_results
            (lot_number, indno, item_code, assembly_number, hmcd, seino, mapping_type)
            SELECT
                l.lot_number,
                a.indno,
                l.item_code,
                l.assembly_number,
                a.hmcd,
                a.seino,
                'auto'
            FROM lot_mapping_data l
            INNER JOIN api_instructions a
                ON l.item_code = a.hmcd
                AND l.assembly_number = a.seino
            """)

            result = conn.execute(auto_mapping_sql)
            auto_mapped = result.rowcount

            # 手動マッピング: manual_mappingsテーブルを使用
            manual_mapping_sql = text("""
            INSERT OR IGNORE INTO mapping_results
            (lot_number, indno, item_code, assembly_number, hmcd, seino, mapping_type)
            SELECT
                l.lot_number,
                a.indno,
                l.item_code,
                l.assembly_number,
                a.hmcd,
                a.seino,
                'manual'
            FROM lot_mapping_data l
            INNER JOIN manual_mappings m
                ON l.lot_number = m.lot_number
            INNER JOIN api_instructions a
                ON m.seino = a.seino
            WHERE NOT EXISTS (
                SELECT 1 FROM mapping_results mr
                WHERE mr.lot_number = l.lot_number AND mr.indno = a.indno
            )
            """)

            result = conn.execute(manual_mapping_sql)
            manual_mapped = result.rowcount

            conn.commit()

        logger.info(f"マッピング完了: 自動={auto_mapped}件, 手動={manual_mapped}件")
        return {"auto": auto_mapped, "manual": manual_mapped}

    def close(self):
        """データベース接続をクローズ"""
        if self.pg_engine:
            self.pg_engine.dispose()
            logger.info("PostgreSQL接続をクローズしました")

        if self.sqlite_engine:
            self.sqlite_engine.dispose()
            logger.info("SQLite接続をクローズしました")
