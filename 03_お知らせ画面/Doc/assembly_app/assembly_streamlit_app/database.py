###
# アッセンブリー課チェックシート
# Start 20250625 ダイヤルキャップとホルダーを開始
# ADD_20250626 ギアボックス追加
###

import sqlite3
import pandas as pd
import datetime
from sqlalchemy import create_engine
import streamlit as st
import os

# configモジュールから、DBパスやテーブル名、外部DB接続関数などをインポート
from config import (
    DB_PATH, DB_DIR, get_db_connection_url,
    DIAL_CAP_CHECKSHEET_TABLE, HOLDER_CHECKSHEET_TABLE, GEARBOX_CHECKSHEET_TABLE, SINKER_CAP_CHECKSHEET_TABLE,
    WORKER_MASTER_TABLE, INSTRUMENT_MASTER_TABLE
)


def init_db():
    """データベースとテーブルを初期化する。テーブルやカラムが存在しない場合のみ作成する。"""
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # チェックシート用テーブルを作成する共通関数
        def create_checksheet_table(table_name):
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in cursor.fetchall()]

            # 旧バージョンからの互換性のためのカラム追加処理
            if 'production_plan_month_full' not in columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN production_plan_month_full TEXT;")
                except sqlite3.OperationalError:
                    pass  # テーブルがまだ存在しない場合はエラーを無視

            # テーブル作成クエリ
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    production_year INTEGER, production_month INTEGER, machine_no TEXT, model_name TEXT,
                    size_inch TEXT, gauge TEXT, production_plan_month_full TEXT, task1_date TEXT, task1_worker TEXT,
                    task2_date TEXT, task2_worker TEXT, task3_date TEXT, task3_worker TEXT, task3_checker TEXT,
                    instrument_no TEXT, completion_status TEXT, remarks TEXT, last_modified_timestamp TEXT,
                    PRIMARY KEY (production_year, production_month, machine_no)
                )""")

        # 各チェックシートテーブルを初期化
        create_checksheet_table(DIAL_CAP_CHECKSHEET_TABLE)
        create_checksheet_table(HOLDER_CHECKSHEET_TABLE)

        # --- [新規追加] シンカーキャップ用テーブルを初期化 ---
        # 既存テーブルのスキーマを確認し、なければ列を追加
        cursor.execute(f"PRAGMA table_info({SINKER_CAP_CHECKSHEET_TABLE});")
        sinker_cap_columns = [row[1] for row in cursor.fetchall()]
        new_columns = {
            'mounting_cam_info': 'TEXT', 'cam_scratch': 'TEXT', 'cam_endmill_mark': 'TEXT',
            'cam_parallelism': 'TEXT', 'cam_adjustment': 'TEXT', 'cam_needling': 'TEXT',
            'carrier_ring_centering': 'TEXT', 'carrier_ring_vertical': 'TEXT',
            'filler_plug': 'TEXT', 'carrier_ring_position': 'TEXT', 'instrument_no': 'TEXT',
            'spare_1': 'TEXT', 'spare_2': 'TEXT', 'spare_3': 'TEXT'
        }
        for col, col_type in new_columns.items():
            if col not in sinker_cap_columns:
                try:
                    cursor.execute(f"ALTER TABLE {SINKER_CAP_CHECKSHEET_TABLE} ADD COLUMN {col} {col_type};")
                except sqlite3.OperationalError:
                    pass # テーブルがまだ存在しない場合など

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SINKER_CAP_CHECKSHEET_TABLE} (
                production_year INTEGER,
                production_month INTEGER,
                machine_no TEXT,
                model_name TEXT,
                size_inch TEXT, 
                gauge TEXT,
                production_plan_month_full TEXT,
                sinker_cap_prep_worker TEXT,
                sinker_cap_assy_worker TEXT,
                mounting_cam_info TEXT,
                cam_scratch TEXT,
                cam_endmill_mark TEXT,
                cam_parallelism TEXT,
                cam_adjustment TEXT,
                cam_needling TEXT,
                carrier_ring_centering TEXT,
                carrier_ring_vertical TEXT,
                filler_plug TEXT,
                carrier_ring_position TEXT,
                instrument_no TEXT,
                spare_1 TEXT,
                spare_2 TEXT,
                spare_3 TEXT,
                completion_status TEXT,
                completion_date TEXT,
                remarks TEXT,
                last_modified_timestamp TEXT,
                PRIMARY KEY (production_year, production_month, machine_no)
            )
        """)

        # --- [新規追加] ギアボックスGr用テーブルを初期化 ---
        # 既存テーブルのスキーマを確認し、なければ予備列を追加
        cursor.execute(f"PRAGMA table_info({GEARBOX_CHECKSHEET_TABLE});")
        gearbox_columns = [row[1] for row in cursor.fetchall()]
        spare_columns = {
            'spare_1_worker': 'TEXT',
            'spare_2_worker': 'TEXT',
            'spare_3_worker': 'TEXT'
        }
        for col, col_type in spare_columns.items():
            if col not in gearbox_columns:
                try:
                    cursor.execute(f"ALTER TABLE {GEARBOX_CHECKSHEET_TABLE} ADD COLUMN {col} {col_type};")
                except sqlite3.OperationalError:
                    # テーブルがまだ存在しない場合など
                    pass
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {GEARBOX_CHECKSHEET_TABLE} (
                production_year INTEGER,
                production_month INTEGER,
                machine_no TEXT,
                model_name TEXT,
                size_inch TEXT, 
                gauge TEXT,
                production_plan_month_full TEXT,
                gearbox_prep_worker TEXT,
                gearbox_internal_mfg_worker TEXT,
                gearbox_assy_worker TEXT,
                handwheel_prep_worker TEXT,
                handwheel_parts_mfg_worker TEXT,
                oneway_clutch_check_worker TEXT,
                handwheel_assy_worker TEXT,
                counter_gear_prep_worker TEXT,
                counter_gear_assy_worker TEXT,
                side_assy_worker TEXT,
                spare_1_worker TEXT,
                spare_2_worker TEXT,
                spare_3_worker TEXT,
                completion_status TEXT,
                completion_date TEXT,
                remarks TEXT,
                last_modified_timestamp TEXT,
                PRIMARY KEY (production_year, production_month, machine_no)
            )
        """)

        # 作業者マスターテーブルのスキーマ確認・変更
        cursor.execute(f"PRAGMA table_info({WORKER_MASTER_TABLE});")
        if 'display_order' not in [row[1] for row in cursor.fetchall()]:
            try:
                cursor.execute(
                    f"ALTER TABLE {WORKER_MASTER_TABLE} ADD COLUMN display_order INTEGER;")
            except sqlite3.OperationalError:
                pass
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {WORKER_MASTER_TABLE} (
                checksheet_name TEXT NOT NULL, worker_name TEXT NOT NULL,
                display_order INTEGER, PRIMARY KEY (checksheet_name, worker_name)
            )""")

        # 計測器マスターテーブルのスキーマ確認・変更
        cursor.execute(f"PRAGMA table_info({INSTRUMENT_MASTER_TABLE});")
        if 'display_order' not in [row[1] for row in cursor.fetchall()]:
            try:
                cursor.execute(
                    f"ALTER TABLE {INSTRUMENT_MASTER_TABLE} ADD COLUMN display_order INTEGER;")
            except sqlite3.OperationalError:
                pass
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {INSTRUMENT_MASTER_TABLE} (
                checksheet_name TEXT NOT NULL, instrument_no TEXT NOT NULL,
                display_order INTEGER, PRIMARY KEY (checksheet_name, instrument_no)
            )""")
        conn.commit()


# --- チェックシート用 共通DB関数 ---

def fetch_production_machine_info(year, month, product_type):
    """
    外部DBから生産機情報を取得する共通関数。
    product_typeに応じてSQLの条件を切り替える。
    """
    dt_nengetsu = f"{str(year)[-2:]}{month:02d}"
    engine = create_engine(get_db_connection_url())

    # an_SKDKの条件を製品タイプに応じて変更
    if product_type == 'dial_cap':
        skdk_filter = "AND an_SKDK = 'DK'"
    elif product_type == 'sinker_cap':
        skdk_filter = "AND an_SKDK = 'SK'"
    else:
        skdk_filter = ""

    try:
        with engine.connect() as connection:
            sql = f"""
                SELECT an_item_cd, an_item_category, an_model_name, an_inch, an_gauge, an_monthly 
                FROM m_items_sub_71 
                WHERE an_monthly LIKE '{dt_nengetsu}%' {skdk_filter}
            """
            df = pd.read_sql(sql, connection)
            if df.empty:
                return pd.DataFrame()

            df_filtered = df[df['an_item_category'] != '替釜'].copy()
            df_renamed = df_filtered.rename(columns={
                'an_item_cd': 'machine_no', 'an_model_name': 'model_name',
                'an_inch': 'size_inch', 'an_gauge': 'gauge',
                'an_monthly': 'production_plan_month_full'
            })
            return df_renamed[['machine_no', 'model_name', 'size_inch', 'gauge', 'production_plan_month_full']]
    except Exception as e:
        st.error(f"{product_type}の生産機情報の取得中にエラーが発生しました: {e}")
        return pd.DataFrame()


def upsert_production_machine_data(df, year, month, table_name):
    """取得した生産機データをSQLiteにUPSERTする共通関数"""
    with sqlite3.connect(DB_PATH) as conn:
        for _, row in df.iterrows():
            conn.execute(f"""
                INSERT INTO {table_name} (production_year, production_month, machine_no, model_name, size_inch, gauge, production_plan_month_full) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(production_year, production_month, machine_no) 
                DO UPDATE SET model_name=excluded.model_name, size_inch=excluded.size_inch, gauge=excluded.gauge, production_plan_month_full=excluded.production_plan_month_full
                """, (year, month, row['machine_no'], row['model_name'], row['size_inch'], row['gauge'], row['production_plan_month_full']))
        conn.commit()


def get_checksheet_data(year, month, table_name):
    """指定年月のチェックシートデータを取得する共通関数"""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            f"SELECT * FROM {table_name} WHERE production_year = ? AND production_month = ?", conn, params=(year, month))
        if df.empty:
            return pd.DataFrame()
        df.sort_values(by='machine_no', inplace=True)
        # 念のためカラム存在確認
        for col in ['task3_checker', 'last_modified_timestamp', 'production_plan_month_full']:
            if col not in df.columns:
                df[col] = None
        return df


def update_row_with_lock(data_row, year, month, original_timestamp, table_name):
    """[修正] チェックシートの行を排他ロック付きで更新する共通関数(汎用化)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        row_dict = data_row.to_dict()

        # テーブルスキーマから全てのカラム名を取得
        cursor.execute(f"PRAGMA table_info({table_name});")
        table_columns = [row[1] for row in cursor.fetchall()]

        # この関数では更新しないカラムのリスト
        non_updatable_cols = [
            'production_year', 'production_month', 'machine_no', 'model_name',
            'size_inch', 'gauge', 'production_plan_month_full', 'last_modified_timestamp'
        ]

        # 更新対象のカラムを動的に決定
        update_cols = [
            col for col in table_columns if col in row_dict and col not in non_updatable_cols]
        date_like_cols = [col for col in update_cols if 'date' in col.lower()]

        # SET句と値リストを生成
        values = []
        for col in update_cols:
            val = row_dict.get(col)
            if pd.isna(val) or val == '':
                values.append(None)
            elif col in date_like_cols:
                try:
                    values.append(pd.to_datetime(val).strftime('%Y-%m-%d'))
                except (ValueError, TypeError):
                    values.append(None)
            else:
                values.append(val)

        new_timestamp = datetime.datetime.now(
            datetime.timezone.utc).isoformat()
        set_clause = ", ".join(
            [f"{col} = ?" for col in update_cols]) + ", last_modified_timestamp = ?"

        values.extend([new_timestamp, year, month, row_dict['machine_no']])

        where_ts_clause = "last_modified_timestamp IS NULL" if pd.isna(
            original_timestamp) else "last_modified_timestamp = ?"
        if not pd.isna(original_timestamp):
            values.append(original_timestamp)

        cursor.execute(f"""
            UPDATE {table_name} SET {set_clause} 
            WHERE production_year = ? AND production_month = ? AND machine_no = ? AND {where_ts_clause}
            """, tuple(values))

        if cursor.rowcount == 1:
            conn.commit()
            return True
        else:
            conn.rollback()
            return False


def add_manual_row(year, month, data, table_name):
    """[修正] チェックシートに手動で行を追加する共通関数(汎用化)"""
    with sqlite3.connect(DB_PATH) as conn:
        try:
            # 渡されたデータに共通のカラムを追加
            full_data = {
                'production_year': year,
                'production_month': month,
                **data
            }

            # データ辞書から動的にINSERT文を構築
            columns = ', '.join(full_data.keys())
            placeholders = ', '.join('?' for _ in full_data)
            values = list(full_data.values())

            conn.execute(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", tuple(values))
            conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            return False, "指定された機番は既に存在します。"
        except Exception as e:
            return False, f"追加中にエラーが発生しました: {e}"


def delete_rows(year, month, machine_numbers, table_name):
    """チェックシートから複数の行を削除する共通関数"""
    with sqlite3.connect(DB_PATH) as conn:
        placeholders = ','.join('?' for _ in machine_numbers)
        conn.execute(f"DELETE FROM {table_name} WHERE production_year = ? AND production_month = ? AND machine_no IN ({placeholders})",
                     tuple([year, month] + machine_numbers))
        conn.commit()
        return len(machine_numbers)


# --- マスター管理用 共通DB関数 ---

def get_workers_for_checksheet(checksheet_name):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            f"SELECT worker_name, display_order FROM {WORKER_MASTER_TABLE} WHERE checksheet_name = ? ORDER BY display_order, worker_name",
            conn, params=(checksheet_name,))


def sync_worker_master(checksheet_name, edited_df):
    if edited_df['display_order'].dropna().duplicated().any():
        raise ValueError("表示順に重複した値があります。修正してください。")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {WORKER_MASTER_TABLE} WHERE checksheet_name = ?", (checksheet_name,))
        records_to_insert = []
        for _, row in edited_df.dropna(subset=['worker_name']).iterrows():
            order_val = int(row['display_order']) if pd.notna(
                row['display_order']) else None
            records_to_insert.append(
                (checksheet_name, row['worker_name'], order_val))
        if records_to_insert:
            cursor.executemany(
                f"INSERT INTO {WORKER_MASTER_TABLE} (checksheet_name, worker_name, display_order) VALUES (?, ?, ?)", records_to_insert)
        conn.commit()


def get_instruments_for_checksheet(checksheet_name):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            f"SELECT instrument_no, display_order FROM {INSTRUMENT_MASTER_TABLE} WHERE checksheet_name = ? ORDER BY display_order, instrument_no",
            conn, params=(checksheet_name,))


def sync_instrument_master(checksheet_name, edited_df):
    if edited_df['display_order'].dropna().duplicated().any():
        raise ValueError("表示順に重複した値があります。修正してください。")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {INSTRUMENT_MASTER_TABLE} WHERE checksheet_name = ?", (checksheet_name,))
        records_to_insert = []
        for _, row in edited_df.dropna(subset=['instrument_no']).iterrows():
            order_val = int(row['display_order']) if pd.notna(
                row['display_order']) else None
            records_to_insert.append(
                (checksheet_name, row['instrument_no'], order_val))
        if records_to_insert:
            cursor.executemany(
                f"INSERT INTO {INSTRUMENT_MASTER_TABLE} (checksheet_name, instrument_no, display_order) VALUES (?, ?, ?)", records_to_insert)
        conn.commit()
