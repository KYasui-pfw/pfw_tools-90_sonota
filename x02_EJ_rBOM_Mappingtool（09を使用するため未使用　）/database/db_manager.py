"""
SQLiteデータベース管理モジュール
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os

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
                    -- EJ側データ
                    ej_order_no TEXT,                -- EJ発注番号 (T_RLSD_PUCH_ODR.PUCH_ODR_CD)
                    ej_item_code TEXT,              -- EJ品目コード (T_RLSD_PUCH_ODR.ITEM_CD)
                    ej_item_name TEXT,              -- EJ品目名 (M_ITEM.ITEM_NAME)
                    ej_quantity REAL,               -- EJ発注数 (T_RLSD_PUCH_ODR.PUCH_ODR_QTY)
                    ej_status TEXT,                 -- EJステータス (T_RLSD_PUCH_ODR.PUCH_ODR_STS_TYP)
                    ej_purch_odr_typ TEXT,          -- EJ発注種別 (T_RLSD_PUCH_ODR.PUCH_ODR_TYP)
                    ej_delivery_date DATE,          -- EJ納期 (T_RLSD_PUCH_ODR.PUCH_ODR_DLV_DATE)
                    
                    -- rBOM側データ
                    rbom_order_no TEXT,             -- rBOM発注番号
                    rbom_line_no INTEGER,           -- rBOM行番号
                    rbom_item_code TEXT,            -- rBOM品目コード
                    rbom_item_name TEXT,            -- rBOM品目名
                    rbom_quantity REAL,             -- rBOM数量
                    rbom_delivery_date DATE,        -- rBOM納期
                    rbom_seino TEXT,                -- rBOM製番
                    
                    -- マッピング管理項目
                    ej_m_sequence INTEGER DEFAULT 1,    -- EJ連番（固定値1）
                    rbom_m_sequence INTEGER DEFAULT 1,  -- rBOM連番（固定値1）
                    status TEXT DEFAULT '',          -- 状態（空欄）
                    mapping_type TEXT,               -- マッピング種別（自動/手動）
                    is_fixed BOOLEAN DEFAULT FALSE, -- 固定フラグ
                    
                    -- システム項目
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # manual_mappingsテーブル作成（手動マッピング管理）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manual_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    -- EJ側データ
                    ej_order_no TEXT,                -- EJ発注番号
                    ej_item_code TEXT,              -- EJ品目コード
                    ej_item_name TEXT,              -- EJ品目名 
                    ej_quantity REAL,               -- EJ発注数
                    ej_status TEXT,                 -- EJステータス
                    ej_purch_odr_typ TEXT,          -- EJ発注種別
                    ej_delivery_date DATE,          -- EJ納期
                    
                    -- rBOM側データ
                    rbom_order_no TEXT,             -- rBOM発注番号
                    rbom_line_no INTEGER,           -- rBOM行番号
                    rbom_item_code TEXT,            -- rBOM品目コード
                    rbom_item_name TEXT,            -- rBOM品目名
                    rbom_quantity REAL,             -- rBOM数量
                    rbom_delivery_date DATE,        -- rBOM納期
                    rbom_seino TEXT,                -- rBOM製番
                    
                    -- マッピング管理項目
                    ej_m_sequence INTEGER DEFAULT 1,    -- EJ連番（固定値1）
                    rbom_m_sequence INTEGER DEFAULT 1,  -- rBOM連番（固定値1）
                    status TEXT DEFAULT '',          -- 状態（空欄）
                    
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
                    
                    -- rBOM側データ
                    rbom_order_no TEXT,             -- rBOM発注番号
                    rbom_line_no INTEGER,           -- rBOM行番号
                    rbom_item_code TEXT,            -- rBOM品目コード
                    rbom_item_name TEXT,            -- rBOM品目名
                    rbom_quantity REAL,             -- rBOM数量
                    rbom_delivery_date DATE,        -- rBOM納期
                    rbom_seino TEXT,                -- rBOM製番
                    
                    -- マッピング管理項目
                    ej_m_sequence INTEGER DEFAULT 1,    -- EJ連番（固定値1）
                    rbom_m_sequence INTEGER DEFAULT 1,  -- rBOM連番（固定値1）
                    status TEXT DEFAULT '',          -- 状態（空欄）
                    
                    -- システム項目
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # extraction_conditionsテーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extraction_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition_name TEXT NOT NULL,
                    delivery_date_from DATE,
                    delivery_date_to DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            # manual_mappings用
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_manual_ej_order 
                ON manual_mappings(ej_order_no)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_manual_rbom_order 
                ON manual_mappings(rbom_order_no, rbom_line_no)
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
            
            conn.commit()
    
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
            return
        
        # 既存データをクリア
        self.clear_mapping_results()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for result in mapping_results:
                cursor.execute("""
                    INSERT INTO mapping_results (
                        ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date,
                        rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name, 
                        rbom_quantity, rbom_delivery_date, rbom_seino,
                        ej_m_sequence, rbom_m_sequence, status, mapping_type, is_fixed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.get('ej_order_no'),
                    result.get('ej_item_code'),
                    result.get('ej_item_name'),
                    result.get('ej_quantity'),
                    result.get('ej_status'),
                    result.get('ej_purch_odr_typ'),
                    result.get('ej_delivery_date'),
                    result.get('rbom_order_no'),
                    result.get('rbom_line_no'),
                    result.get('rbom_item_code'),
                    result.get('rbom_item_name'),
                    result.get('rbom_quantity'),
                    result.get('rbom_delivery_date'),
                    result.get('rbom_seino'),
                    1,  # ej_m_sequence 固定値
                    1,  # rbom_m_sequence 固定値
                    '',  # status 空欄
                    result.get('mapping_type'),
                    result.get('is_fixed', False)  # is_fixed デフォルトFalse
                ))
            
            conn.commit()
    
    def get_mapping_results(self) -> pd.DataFrame:
        """
        マッピング結果を取得
        
        Returns:
            マッピング結果のDataFrame
        """
        with self.get_connection() as conn:
            query = """
                SELECT 
                    ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date,
                    rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name, rbom_quantity, rbom_delivery_date,
                    ej_m_sequence, rbom_m_sequence, status, mapping_type, is_fixed
                FROM mapping_results
                ORDER BY ej_order_no, rbom_order_no
            """
            
            df = pd.read_sql_query(query, conn)
            return df
    
    def save_manual_mapping(self, mapping_data: dict):
        """
        手動マッピングを保存
        
        Args:
            mapping_data: 手動マッピングデータの辞書
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO manual_mappings (
                    ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date,
                    rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name, 
                    rbom_quantity, rbom_delivery_date, rbom_seino,
                    ej_m_sequence, rbom_m_sequence, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mapping_data.get('ej_order_no'),
                mapping_data.get('ej_item_code'),
                mapping_data.get('ej_item_name'),
                mapping_data.get('ej_quantity'),
                mapping_data.get('ej_status'),
                mapping_data.get('ej_purch_odr_typ'),
                mapping_data.get('ej_delivery_date'),
                mapping_data.get('rbom_order_no'),
                mapping_data.get('rbom_line_no'),
                mapping_data.get('rbom_item_code'),
                mapping_data.get('rbom_item_name'),
                mapping_data.get('rbom_quantity'),
                mapping_data.get('rbom_delivery_date'),
                mapping_data.get('rbom_seino'),
                1,  # ej_m_sequence 固定値
                1,  # rbom_m_sequence 固定値
                ''  # status 空欄
            ))
            conn.commit()
    
    def save_fixed_mapping(self, mapping_data: dict):
        """
        固定マッピングを保存
        
        Args:
            mapping_data: 固定マッピングデータの辞書
        """
        # pandas.NAをNoneに変換
        clean_data = self._convert_na_values(mapping_data)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fixed_mappings (
                    ej_order_no, ej_item_code, ej_item_name, ej_quantity, ej_status, ej_purch_odr_typ, ej_delivery_date,
                    rbom_order_no, rbom_line_no, rbom_item_code, rbom_item_name, 
                    rbom_quantity, rbom_delivery_date, rbom_seino,
                    ej_m_sequence, rbom_m_sequence, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_data.get('ej_order_no'),
                clean_data.get('ej_item_code'),
                clean_data.get('ej_item_name'),
                clean_data.get('ej_quantity'),
                clean_data.get('ej_status'),
                clean_data.get('ej_purch_odr_typ'),
                clean_data.get('ej_delivery_date'),
                clean_data.get('rbom_order_no'),
                clean_data.get('rbom_line_no'),
                clean_data.get('rbom_item_code'),
                clean_data.get('rbom_item_name'),
                clean_data.get('rbom_quantity'),
                clean_data.get('rbom_delivery_date'),
                clean_data.get('rbom_seino'),
                1,  # ej_m_sequence 固定値
                1,  # rbom_m_sequence 固定値
                ''  # status 空欄
            ))
            conn.commit()
    
    def get_manual_mappings(self) -> pd.DataFrame:
        """手動マッピング一覧を取得"""
        with self.get_connection() as conn:
            query = "SELECT * FROM manual_mappings ORDER BY created_at DESC"
            return pd.read_sql_query(query, conn)
    
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
    
    def delete_manual_mapping(self, ej_order_no: str, rbom_order_no: str, rbom_line_no: int):
        """
        手動マッピングを削除
        
        Args:
            ej_order_no: EJ発注番号
            rbom_order_no: rBOM発注番号
            rbom_line_no: rBOM行番号
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM manual_mappings 
                WHERE ej_order_no = ? AND rbom_order_no = ? AND rbom_line_no = ?
            """, (ej_order_no, rbom_order_no, rbom_line_no))
            conn.commit()
    
    def save_extraction_condition(self, condition_name: str, date_from, date_to):
        """
        抽出条件を保存
        
        Args:
            condition_name: 条件名
            date_from: 開始日
            date_to: 終了日
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO extraction_conditions (condition_name, delivery_date_from, delivery_date_to)
                VALUES (?, ?, ?)
            """, (condition_name, date_from, date_to))
            conn.commit()
    
    def get_extraction_conditions(self) -> pd.DataFrame:
        """
        抽出条件を取得
        
        Returns:
            抽出条件のDataFrame
        """
        with self.get_connection() as conn:
            query = """
                SELECT condition_name, delivery_date_from, delivery_date_to, created_at
                FROM extraction_conditions
                ORDER BY created_at DESC
            """
            
            df = pd.read_sql_query(query, conn)
            return df
    
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
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # トランザクション開始
                cursor.execute("BEGIN TRANSACTION")
                
                for ej_order_no, rbom_order_no, rbom_line_no, is_fixed, mapping_data in updates:
                    clean_params = self._convert_na_values([ej_order_no, rbom_order_no, rbom_line_no])
                    
                    if is_fixed:
                        # 固定登録: fixed_mappingsテーブルに追加
                        clean_data = self._convert_na_values(mapping_data)
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
                            clean_data.get('rbom_seino'), 1, 1, ''
                        ))
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
                
                # トランザクションをコミット
                cursor.execute("COMMIT")
                
            except Exception as e:
                # エラー時はロールバック
                cursor.execute("ROLLBACK")
                raise Exception(f"一括固定登録でエラーが発生しました: {str(e)}")