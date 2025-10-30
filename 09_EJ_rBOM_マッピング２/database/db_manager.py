"""
SQLiteデータベース管理モジュール
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLiteデータベース管理クラス"""
    
    def __init__(self, db_path: str = "./Database/mapping.db"):
        """
        初期化
        
        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        
        # Databaseディレクトリが存在しない場合は作成
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _convert_na_values(self, data):
        """pandas.NAやNaNをNoneに変換する共通関数"""
        if isinstance(data, dict):
            return {key: (None if pd.isna(value) else value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [None if pd.isna(value) else value for value in data]
        else:
            return None if pd.isna(data) else data
    
    def get_connection(self):
        """データベース接続を取得（オートコミット無効・明示的トランザクション管理）"""
        conn = sqlite3.connect(self.db_path)
        # オートコミットを明示的に無効化（デフォルトでは無効だが確実にするため）
        conn.isolation_level = 'DEFERRED'
        return conn
    
    def initialize_database(self):
        """データベースとテーブルを初期化"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # mapping_resultsテーブル作成（統合表示用）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mapping_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    -- 統一品目コード
                    item_code TEXT,                  -- 統一品目コード（マッピング時はEJ/rBOM共通、未マッピング時は存在する側）

                    -- EJ側データ
                    ej_order_no TEXT,                -- EJ発注番号 (T_RLSD_PUCH_ODR.PUCH_ODR_CD)
                    ej_item_code TEXT,              -- EJ品目コード (T_RLSD_PUCH_ODR.ITEM_CD)
                    ej_item_name TEXT,              -- EJ品目名 (M_ITEM.ITEM_NAME)
                    ej_quantity REAL,               -- EJ発注数 (T_RLSD_PUCH_ODR.PUCH_ODR_QTY)
                    ej_status TEXT,                 -- EJステータス (T_RLSD_PUCH_ODR.PUCH_ODR_STS_TYP)
                    ej_purch_odr_typ TEXT,          -- EJ発注種別 (T_RLSD_PUCH_ODR.PUCH_ODR_TYP)
                    ej_delivery_date DATE,          -- EJ納期 (T_RLSD_PUCH_ODR.PUCH_ODR_DLV_DATE)
                    ej_vend_cd TEXT,                -- EJ仕入先コード (T_RLSD_PUCH_ODR.VEND_CD)

                    -- rBOM側データ
                    rbom_order_no TEXT,             -- rBOM発注番号
                    rbom_line_no INTEGER,           -- rBOM行番号
                    rbom_item_code TEXT,            -- rBOM品目コード
                    rbom_item_name TEXT,            -- rBOM品目名
                    rbom_quantity REAL,             -- rBOM数量
                    rbom_delivery_date DATE,        -- rBOM納期
                    rbom_seino TEXT,                -- rBOM製番
                    rbom_ktcd TEXT,                 -- rBOM工程コード
                    rbom_srcd TEXT,                 -- rBOM仕入先コード
                    mk020_note TEXT,                -- MK020備考 (MK020.NOTE)

                    -- マッピング管理項目
                    ej_m_sequence INTEGER DEFAULT 1,    -- EJ連番（固定値1）
                    rbom_m_sequence INTEGER DEFAULT 1,  -- rBOM連番（固定値1）
                    status TEXT DEFAULT '',          -- 状態（空欄）
                    mapping_type TEXT,               -- マッピング種別（自動/手動）
                    is_fixed BOOLEAN DEFAULT FALSE, -- 固定フラグ
                    is_manual_mapping BOOLEAN DEFAULT FALSE, -- 手動マッピングフラグ

                    -- システム項目
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            
            # fixed_mappingsテーブル作成（固定マッピング管理）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fixed_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    -- EJ側データ
                    ej_order_no TEXT,                -- EJ発注番号
                    ej_item_code TEXT,              -- EJ品目コード
                    ej_item_name TEXT,              -- EJ品目名
                    ej_quantity REAL,               -- EJ発注数
                    ej_status TEXT,                 -- EJステータス
                    ej_purch_odr_typ TEXT,          -- EJ発注種別
                    ej_delivery_date DATE,          -- EJ納期
                    ej_vend_cd TEXT,                -- EJ仕入先コード
                    
                    -- rBOM側データ
                    rbom_order_no TEXT,             -- rBOM発注番号
                    rbom_line_no INTEGER,           -- rBOM行番号
                    rbom_item_code TEXT,            -- rBOM品目コード
                    rbom_item_name TEXT,            -- rBOM品目名
                    rbom_quantity REAL,             -- rBOM数量
                    rbom_delivery_date DATE,        -- rBOM納期
                    rbom_seino TEXT,                -- rBOM製番
                    rbom_ktcd TEXT,                 -- rBOM工程コード
                    rbom_srcd TEXT,                 -- rBOM仕入先コード
                    mk020_note TEXT,                -- MK020備考 (MK020.NOTE)

                    -- マッピング管理項目
                    ej_m_sequence INTEGER DEFAULT 1,    -- EJ連番（固定値1）
                    rbom_m_sequence INTEGER DEFAULT 1,  -- rBOM連番（固定値1）
                    status TEXT DEFAULT '',          -- 状態（空欄）
                    
                    -- システム項目
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # manual_mappingsテーブル作成（手動マッピング専用）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manual_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ej_order_no TEXT NOT NULL,       -- EJ発注番号
                    rbom_order_no TEXT NOT NULL,     -- rBOM発注番号
                    rbom_line_no INTEGER NOT NULL,   -- rBOM行番号
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- 複合ユニーク制約
                    UNIQUE(ej_order_no, rbom_order_no, rbom_line_no)
                )
            """)

            # インデックス作成
            # mapping_results用
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_ej_key 
                ON mapping_results(ej_item_code, ej_quantity)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_rbom_key 
                ON mapping_results(rbom_item_code, rbom_quantity)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_type 
                ON mapping_results(mapping_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_fixed
                ON mapping_results(is_fixed)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mapping_manual
                ON mapping_results(is_manual_mapping)
            """)

            # fixed_mappings用
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fixed_ej_order
                ON fixed_mappings(ej_order_no)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fixed_rbom_order
                ON fixed_mappings(rbom_order_no, rbom_line_no)
            """)

            # 既存テーブルにej_vend_cdカラムを追加（カラムが存在しない場合のみ）
            try:
                cursor.execute("SELECT ej_vend_cd FROM mapping_results LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("mapping_resultsテーブルにej_vend_cdカラムを追加")
                cursor.execute("ALTER TABLE mapping_results ADD COLUMN ej_vend_cd TEXT")

            try:
                cursor.execute("SELECT ej_vend_cd FROM fixed_mappings LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("fixed_mappingsテーブルにej_vend_cdカラムを追加")
                cursor.execute("ALTER TABLE fixed_mappings ADD COLUMN ej_vend_cd TEXT")

            # 既存テーブルにrbom_ktcdカラムを追加（カラムが存在しない場合のみ）
            try:
                cursor.execute("SELECT rbom_ktcd FROM mapping_results LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("mapping_resultsテーブルにrbom_ktcdカラムを追加")
                cursor.execute("ALTER TABLE mapping_results ADD COLUMN rbom_ktcd TEXT")

            try:
                cursor.execute("SELECT rbom_ktcd FROM fixed_mappings LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("fixed_mappingsテーブルにrbom_ktcdカラムを追加")
                cursor.execute("ALTER TABLE fixed_mappings ADD COLUMN rbom_ktcd TEXT")

            # 既存テーブルにrbom_srcdカラムを追加（カラムが存在しない場合のみ）
            try:
                cursor.execute("SELECT rbom_srcd FROM mapping_results LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("mapping_resultsテーブルにrbom_srcdカラムを追加")
                cursor.execute("ALTER TABLE mapping_results ADD COLUMN rbom_srcd TEXT")

            try:
                cursor.execute("SELECT rbom_srcd FROM fixed_mappings LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("fixed_mappingsテーブルにrbom_srcdカラムを追加")
                cursor.execute("ALTER TABLE fixed_mappings ADD COLUMN rbom_srcd TEXT")

            # 既存テーブルにmk020_noteカラムを追加（カラムが存在しない場合のみ）
            try:
                cursor.execute("SELECT mk020_note FROM mapping_results LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("mapping_resultsテーブルにmk020_noteカラムを追加")
                cursor.execute("ALTER TABLE mapping_results ADD COLUMN mk020_note TEXT")

            try:
                cursor.execute("SELECT mk020_note FROM fixed_mappings LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("fixed_mappingsテーブルにmk020_noteカラムを追加")
                cursor.execute("ALTER TABLE fixed_mappings ADD COLUMN mk020_note TEXT")

            conn.commit()

    def save_last_execution_time(self, execution_time: datetime):
        """
        最終実行時刻をデータベースに保存

        Args:
            execution_time: 実行時刻
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # system_settings テーブルが存在しない場合は作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 実行時刻を保存（既存レコードがあればUPDATE、なければINSERT）
            cursor.execute("""
                INSERT OR REPLACE INTO system_settings (key, value, updated_at)
                VALUES ('last_execution_time', ?, CURRENT_TIMESTAMP)
            """, (execution_time.strftime('%Y-%m-%d %H:%M:%S'),))
            
            conn.commit()
            logger.info(f"最終実行時刻をデータベースに保存: {execution_time}")

    def get_last_execution_time(self) -> datetime:
        """
        最終実行時刻をデータベースから取得
        データベースに記録がない場合は、バックアップフォルダの最新ファイル時刻を返す

        Returns:
            最終実行時刻（取得できない場合はNone）
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # テーブル存在チェック
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='system_settings'
                """)
                
                if cursor.fetchone() is None:
                    logger.info("system_settingsテーブルが存在しないため、バックアップから取得します")
                    return self._get_latest_backup_time()
                
                # 実行時刻を取得
                cursor.execute("""
                    SELECT value FROM system_settings 
                    WHERE key = 'last_execution_time'
                """)
                
                result = cursor.fetchone()
                
                if result is None:
                    logger.info("データベースに実行時刻の記録がないため、バックアップから取得します")
                    return self._get_latest_backup_time()
                
                # 文字列からdatetimeに変換
                execution_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                logger.info(f"データベースから最終実行時刻を取得: {execution_time}")
                return execution_time
                
        except Exception as e:
            logger.warning(f"最終実行時刻の取得に失敗（バックアップから取得します）: {str(e)}")
            return self._get_latest_backup_time()

    def _get_latest_backup_time(self) -> datetime:
        """
        バックアップフォルダから最新のバックアップファイルの作成時刻を取得

        Returns:
            最新バックアップの作成時刻（バックアップがない場合はNone）
        """
        try:
            backup_dir = Path("./database/DB_backup")
            
            if not backup_dir.exists():
                logger.info("バックアップディレクトリが存在しません")
                return None
            
            # バックアップファイルを取得
            backup_files = list(backup_dir.glob("*.db.zip"))
            
            if not backup_files:
                logger.info("バックアップファイルが存在しません")
                return None
            
            # 最新のファイルを取得（更新時刻順）
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            
            logger.info(f"最新バックアップから実行時刻を取得: {backup_time} (ファイル: {latest_backup.name})")
            return backup_time
            
        except Exception as e:
            logger.warning(f"バックアップファイルからの時刻取得に失敗: {str(e)}")
            return None
    
    def clear_mapping_results(self):
        """既存のマッピング結果をクリア"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mapping_results")
            conn.commit()
    
    def save_mapping_results(self, mapping_results: list):
        """
        マッピング結果を保存

        Args:
            mapping_results: マッピング結果のリスト
        """
        if not mapping_results:
            logger.warning("保存するマッピング結果が空です")
            return

        logger.info(f"マッピング結果保存開始: {len(mapping_results)}件")
        start_time = datetime.now()

        # 既存データをクリア
        clear_start = datetime.now()
        self.clear_mapping_results()
        logger.debug(f"  既存データクリア完了 ({(datetime.now() - clear_start).total_seconds():.3f}秒)")
        
        insert_start = datetime.now()
        with self.get_connection() as conn:
            cursor = conn.cursor()

            insert_count = 0
            diff_count = 0
            manual_count = 0
            for result in mapping_results:
                # EJ連番とrBOM連番の設定（mapper側で指定されていればそれを使用、なければデフォルト処理）
                ej_m_seq = result.get('ej_m_sequence')
                if ej_m_seq is None:
                    # mapper側で指定がない場合はデフォルト処理
                    ej_m_seq = 1 if result.get('ej_order_no') is not None else None
                elif ej_m_seq == 2:
                    diff_count += 1
                    if diff_count <= 3:  # 最初の3件だけログ出力
                        logger.debug(f"  [差分行検出] EJ連番=2, order_no={result.get('ej_order_no')}, qty={result.get('ej_quantity')}")

                rbom_m_seq = result.get('rbom_m_sequence')
                if rbom_m_seq is None:
                    # mapper側で指定がない場合はデフォルト処理
                    rbom_m_seq = 1 if result.get('rbom_order_no') is not None else None
                elif rbom_m_seq == 2:
                    diff_count += 1
                    if diff_count <= 3:  # 最初の3件だけログ出力
                        logger.debug(f"  [差分行検出] rBOM連番=2, order_no={result.get('rbom_order_no')}, qty={result.get('rbom_quantity')}")

                # 手動マッピングフラグの確認
                is_manual = result.get('is_manual_mapping', False)
                if is_manual:
                    manual_count += 1
                    if manual_count <= 3:  # 最初の3件だけログ出力
                        logger.debug(f"  [手動マッピング検出] ej_order_no={result.get('ej_order_no')}, is_manual_mapping={is_manual} (型: {type(is_manual)})")

                status_value = result.get('status', '')
                # 済2のデバッグログ（最初の3件のみ）
                if status_value == '済2' and insert_count < 3:
                    logger.info(f"【デバッグ】DB保存前 status='済2'検出: EJ={result.get('ej_order_no')}, rBOM={result.get('rbom_order_no')}+{result.get('rbom_line_no')}")

                cursor.execute("""
                    INSERT INTO mapping_results (
                        item_code,
                        ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
                        rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
                        rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd, mk020_note,
                        ej_m_sequence, rbom_m_sequence, status, mapping_type, is_fixed, is_manual_mapping
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.get('item_code'),
                    result.get('ej_order_no'),
                    result.get('ej_item_code'),
                    result.get('ej_item_name'),
                    result.get('ej_quantity'),
                    result.get('ej_status'),
                    result.get('ej_purch_odr_typ'),
                    result.get('ej_delivery_date'),
                    result.get('ej_vend_cd'),
                    result.get('rbom_order_no'),
                    result.get('rbom_line_no'),
                    result.get('rbom_item_code'),
                    result.get('rbom_item_name'),
                    result.get('rbom_quantity'),
                    result.get('rbom_delivery_date'),
                    result.get('rbom_seino'),
                    result.get('rbom_ktcd'),
                    result.get('rbom_srcd'),
                    result.get('mk020_note'),
                    ej_m_seq,  # mapper側で指定された連番、またはデフォルト
                    rbom_m_seq,  # mapper側で指定された連番、またはデフォルト
                    status_value,  # status（"済2"など、デフォルトは空欄）
                    result.get('mapping_type'),
                    result.get('is_fixed', False),  # is_fixed デフォルトFalse
                    result.get('is_manual_mapping', False)  # is_manual_mapping デフォルトFalse
                ))
                insert_count += 1

            commit_start = datetime.now()
            conn.commit()
            logger.debug(f"  コミット完了 ({(datetime.now() - commit_start).total_seconds():.3f}秒)")

        logger.info(f"マッピング結果保存完了: {insert_count}件 (差分行: {diff_count}件, 手動: {manual_count}件含む) (合計: {(datetime.now() - start_time).total_seconds():.3f}秒)")
    
    def get_mapping_results(self) -> pd.DataFrame:
        """
        マッピング結果を取得

        Returns:
            マッピング結果のDataFrame
        """
        with self.get_connection() as conn:
            query = """
                SELECT
                    item_code,
                    ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
                    rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name, rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd, mk020_note,
                    ej_m_sequence, rbom_m_sequence, status, mapping_type, is_fixed, is_manual_mapping
                FROM mapping_results
                ORDER BY item_code, ej_order_no, rbom_order_no
            """

            df = pd.read_sql_query(query, conn)
            return df
    
    def save_fixed_mapping(self, mapping_data: dict):
        """
        固定マッピングを保存
        
        Args:
            mapping_data: 固定マッピングデータの辞書
        """
        # pandas.NAをNoneに変換
        clean_data = self._convert_na_values(mapping_data)

        # EJ連番とrBOM連番の条件付き設定
        ej_m_seq = 1 if clean_data.get('ej_order_no') is not None else None
        rbom_m_seq = 1 if clean_data.get('rbom_order_no') is not None else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fixed_mappings (
                    ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date, ej_vend_cd,
                    rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
                    rbom_quantity, rbom_delivery_date, rbom_seino, rbom_ktcd, rbom_srcd, mk020_note,
                    ej_m_sequence, rbom_m_sequence, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_data.get('ej_order_no'),
                clean_data.get('ej_item_code'),
                clean_data.get('ej_item_name'),
                clean_data.get('ej_quantity'),
                clean_data.get('ej_status'),
                clean_data.get('ej_purch_odr_typ'),
                clean_data.get('ej_delivery_date'),
                clean_data.get('ej_vend_cd'),
                clean_data.get('rbom_order_no'),
                clean_data.get('rbom_line_no'),
                clean_data.get('rbom_item_code'),
                clean_data.get('rbom_item_name'),
                clean_data.get('rbom_quantity'),
                clean_data.get('rbom_delivery_date'),
                clean_data.get('rbom_seino'),
                clean_data.get('rbom_ktcd'),
                clean_data.get('rbom_srcd'),
                clean_data.get('mk020_note'),
                ej_m_seq,  # EJ発注番号がNoneならNone、それ以外は1
                rbom_m_seq,  # rBOM発注番号がNoneならNone、それ以外は1
                ''  # status 空欄
            ))
            conn.commit()
    
    def get_fixed_mappings(self) -> pd.DataFrame:
        """固定マッピング一覧を取得"""
        with self.get_connection() as conn:
            query = "SELECT * FROM fixed_mappings ORDER BY created_at DESC"
            return pd.read_sql_query(query, conn)
    
    def delete_fixed_mapping(self, ej_order_no: str, rbom_order_no: str, rbom_line_no: int):
        """
        固定マッピングを削除
        
        Args:
            ej_order_no: EJ発注番号
            rbom_order_no: rBOM発注番号  
            rbom_line_no: rBOM行番号
        """
        # pandas.NAをNoneに変換
        clean_params = self._convert_na_values([ej_order_no, rbom_order_no, rbom_line_no])
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM fixed_mappings 
                WHERE ej_order_no = ? AND rbom_order_no = ? AND rbom_line_no = ?
            """, clean_params)
            conn.commit()

    def update_mapping_fixed_status(self, ej_order_no: str, rbom_order_no: str, rbom_line_no: int, is_fixed: bool):
        """
        mapping_resultsテーブルのis_fixedフラグを更新
        
        Args:
            ej_order_no: EJ発注番号
            rbom_order_no: rBOM発注番号
            rbom_line_no: rBOM行番号
            is_fixed: 固定フラグ
        """
        # pandas.NAをNoneに変換
        clean_params = self._convert_na_values([ej_order_no, rbom_order_no, rbom_line_no])
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # EJ_ONLY（rBOMデータがない）ケースとMATCHEDケースを区別して処理
            if clean_params[1] is None or clean_params[2] is None:
                # EJ_ONLYケース: rbom_order_noとrbom_line_noがNULL
                cursor.execute("""
                    UPDATE mapping_results 
                    SET is_fixed = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE ej_order_no = ? AND rbom_order_no IS NULL AND rbom_line_no IS NULL
                """, (is_fixed, clean_params[0]))
            else:
                # MATCHEDケース: 通常の更新
                cursor.execute("""
                    UPDATE mapping_results 
                    SET is_fixed = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE ej_order_no = ? AND rbom_order_no = ? AND rbom_line_no = ?
                """, (is_fixed, clean_params[0], clean_params[1], clean_params[2]))
            
            conn.commit()
    
    def bulk_update_fixed_status(self, updates: list):
        """
        is_fixedフラグを一括更新（安定版）
        
        Args:
            updates: [(ej_order_no, rbom_order_no, rbom_line_no, is_fixed), ...] のリスト
        """
        if not updates:
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # トランザクション開始
                cursor.execute("BEGIN TRANSACTION")
                
                # 一括更新処理
                for ej_order_no, rbom_order_no, rbom_line_no, is_fixed in updates:
                    # pandas.NAをNoneに変換
                    clean_params = self._convert_na_values([ej_order_no, rbom_order_no, rbom_line_no])
                    
                    if clean_params[1] is None or clean_params[2] is None:
                        # EJ_ONLYケース
                        cursor.execute("""
                            UPDATE mapping_results 
                            SET is_fixed = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE ej_order_no = ? AND rbom_order_no IS NULL AND rbom_line_no IS NULL
                        """, (is_fixed, clean_params[0]))
                    else:
                        # MATCHEDケース
                        cursor.execute("""
                            UPDATE mapping_results 
                            SET is_fixed = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE ej_order_no = ? AND rbom_order_no = ? AND rbom_line_no = ?
                        """, (is_fixed, clean_params[0], clean_params[1], clean_params[2]))
                
                # トランザクションをコミット
                cursor.execute("COMMIT")
                
            except Exception as e:
                # エラー時はロールバック
                cursor.execute("ROLLBACK")
                raise Exception(f"一括更新でエラーが発生しました: {str(e)}")
    
    def bulk_update_fixed_and_save_mappings(self, updates: list):
        """
        固定マッピングの保存と削除を一括処理

        Args:
            updates: [(ej_order_no, rbom_order_no, rbom_line_no, is_fixed, mapping_data), ...] のリスト
        """
        if not updates:
            logger.warning("一括更新対象が空です")
            return

        logger.info(f"固定マッピング一括更新開始: {len(updates)}件")
        start_time = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # トランザクション開始
                cursor.execute("BEGIN TRANSACTION")
                logger.debug("  トランザクション開始")

                insert_count = 0
                delete_count = 0
                update_count = 0

                for ej_order_no, rbom_order_no, rbom_line_no, is_fixed, mapping_data in updates:
                    clean_params = self._convert_na_values([ej_order_no, rbom_order_no, rbom_line_no])

                    if is_fixed:
                        # 固定登録: fixed_mappingsテーブルに追加
                        clean_data = self._convert_na_values(mapping_data)

                        # EJ連番とrBOM連番の条件付き設定
                        ej_m_seq = 1 if clean_data.get('ej_order_no') is not None else None
                        rbom_m_seq = 1 if clean_data.get('rbom_order_no') is not None else None

                        cursor.execute("""
                            INSERT OR REPLACE INTO fixed_mappings (
                                ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date,
                                rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name,
                                rbom_quantity, rbom_delivery_date, rbom_seino,
                                ej_m_sequence, rbom_m_sequence, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            clean_data.get('ej_order_no'), clean_data.get('ej_item_code'),
                            clean_data.get('ej_item_name'), clean_data.get('ej_quantity'),
                            clean_data.get('ej_status'), clean_data.get('ej_purch_odr_typ'), clean_data.get('ej_delivery_date'),
                            clean_data.get('rbom_order_no'), clean_data.get('rbom_line_no'),
                            clean_data.get('rbom_item_code'), clean_data.get('rbom_item_name'),
                            clean_data.get('rbom_quantity'), clean_data.get('rbom_delivery_date'),
                            clean_data.get('rbom_seino'), ej_m_seq, rbom_m_seq, ''
                        ))
                        insert_count += 1
                    else:
                        # 固定解除: fixed_mappingsテーブルから削除
                        if clean_params[1] is None or clean_params[2] is None:
                            cursor.execute("""
                                DELETE FROM fixed_mappings
                                WHERE ej_order_no = ? AND rbom_order_no IS NULL AND rbom_line_no IS NULL
                            """, (clean_params[0],))
                        else:
                            cursor.execute("""
                                DELETE FROM fixed_mappings
                                WHERE ej_order_no = ? AND rbom_order_no = ? AND rbom_line_no = ?
                            """, clean_params)
                        delete_count += 1
                    
                    # mapping_resultsテーブルのis_fixedフラグを更新
                    if clean_params[1] is None or clean_params[2] is None:
                        cursor.execute("""
                            UPDATE mapping_results
                            SET is_fixed = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE ej_order_no = ? AND rbom_order_no IS NULL AND rbom_line_no IS NULL
                        """, (is_fixed, clean_params[0]))
                    else:
                        cursor.execute("""
                            UPDATE mapping_results
                            SET is_fixed = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE ej_order_no = ? AND rbom_order_no = ? AND rbom_line_no = ?
                        """, (is_fixed, clean_params[0], clean_params[1], clean_params[2]))
                    update_count += 1

                # トランザクションをコミット
                commit_start = datetime.now()
                cursor.execute("COMMIT")
                logger.debug(f"  コミット完了: INSERT={insert_count}, DELETE={delete_count}, UPDATE={update_count} ({(datetime.now() - commit_start).total_seconds():.3f}秒)")

            except Exception as e:
                # エラー時はロールバック
                cursor.execute("ROLLBACK")
                logger.error(f"一括固定登録エラー（ロールバック実行）: {str(e)}")
                raise Exception(f"一括固定登録でエラーが発生しました: {str(e)}")

        logger.info(f"固定マッピング一括更新完了 (合計: {(datetime.now() - start_time).total_seconds():.3f}秒)")

    def save_manual_mapping(self, ej_order_no: str, rbom_order_no: str, rbom_line_no: int):
        """
        手動マッピングを保存

        Args:
            ej_order_no: EJ発注番号
            rbom_order_no: rBOM発注番号
            rbom_line_no: rBOM行番号
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO manual_mappings (ej_order_no, rbom_order_no, rbom_line_no)
                    VALUES (?, ?, ?)
                """, (ej_order_no, rbom_order_no, rbom_line_no))
                conn.commit()
            except Exception as e:
                raise Exception(f"手動マッピング保存エラー: {str(e)}")

    def get_manual_mappings(self) -> pd.DataFrame:
        """
        手動マッピング一覧を取得

        Returns:
            手動マッピングのDataFrame
        """
        with self.get_connection() as conn:
            query = """
                SELECT id, ej_order_no, rbom_order_no, rbom_line_no, created_at
                FROM manual_mappings
                ORDER BY created_at DESC
            """
            return pd.read_sql_query(query, conn)

    def delete_manual_mapping(self, mapping_id: int):
        """
        手動マッピングを削除

        Args:
            mapping_id: マッピングID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM manual_mappings WHERE id = ?", (mapping_id,))
            conn.commit()