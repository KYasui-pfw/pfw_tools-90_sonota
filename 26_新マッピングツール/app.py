"""
発注情報ビューア

SQLiteデータベースのmapping_resultsを表示するStreamlitアプリ
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import os
import configparser

import streamlit as st
import pandas as pd
import requests
import oracledb

# 設定
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "mapping.db"
CONFIG_PATH = SCRIPT_DIR / "config.ini"

# rBOM API設定
API_URL = "http://pfw-api/query"
API_KEY = "oG5^Ls%#20yq"


def get_exclude_ej_orders():
    """config.iniから除外するEJ発注番号リストを取得"""
    if not CONFIG_PATH.exists():
        return set()
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH, encoding='utf-8')
        exclude_str = config.get('price_mismatch', 'exclude_ej_orders', fallback='')
        if not exclude_str.strip():
            return set()
        # カンマ区切りで分割し、空白を除去
        exclude_list = [x.strip() for x in exclude_str.split(',') if x.strip()]
        return set(exclude_list)
    except Exception:
        return set()

st.set_page_config(
    page_title="EJ⇔rBOM発注マッピング情報",
    page_icon="📊",
    layout="wide"
)

# ヘッダー縮小・Deploy非表示用CSS
st.markdown("""
<style>
    /* 上部パディング縮小 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* タイトル縮小 */
    h1 {
        font-size: 1.5rem !important;
        margin-bottom: 0 !important;
    }
    /* タブ間隔 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    /* タブのパディング */
    .stTabs [data-baseweb="tab"] {
        padding-left: 16px;
        padding-right: 16px;
    }
    /* 背景色（ごく薄い黄色系） */
    .stApp {
        background-color: #FFFEFB;
    }
    .stMainBlockContainer {
        background-color: #FFFEFB;
    }
    /* Deployボタン非表示 */
    .stDeployButton {
        display: none !important;
    }
    /* メインメニュー非表示 */
    #MainMenu {
        visibility: hidden !important;
    }
    /* フッター非表示 */
    footer {
        visibility: hidden !important;
    }
    /* ヘッダー非表示 */
    header {
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)


def get_last_update():
    """最終更新日時を取得"""
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT updated_at FROM update_history ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return None


def load_data(period: str = None) -> pd.DataFrame:
    """テーブルからデータを読み込み"""
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    if period:
        df = pd.read_sql_query(
            "SELECT ej_order_no, rbom_order_no, rbom_line_no, rbom_quantity, hmcd FROM mapping_results WHERE period = ?",
            conn,
            params=(period,)
        )
    else:
        df = pd.read_sql_query("SELECT ej_order_no, rbom_order_no, rbom_line_no, rbom_quantity, hmcd FROM mapping_results", conn)
    conn.close()

    # カラム名を日本語に変換
    df = df.rename(columns={
        'ej_order_no': 'EJ発注番号',
        'rbom_order_no': 'rBOM発注番号',
        'rbom_line_no': 'rBOM行番号',
        'rbom_quantity': '発注数量',
        'hmcd': '品目コード'
    })
    return df


# 期間区分
PERIOD_DEC = "2025年12月15日以降の発注マッピング"
PERIOD_NOV = "2025年11月以前の発注残マッピング"


def init_duplicate_ok_table():
    """問題なしテーブルを初期化"""
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS duplicate_ok (
            pono TEXT,
            lineno INTEGER,
            created_at TEXT,
            PRIMARY KEY (pono, lineno)
        )
    ''')
    conn.commit()
    conn.close()


def get_duplicate_ok_set():
    """問題なし登録済みの発注番号+行番号セットを取得"""
    if not DB_PATH.exists():
        return set()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT pono, lineno FROM duplicate_ok")
        result = set((row[0], row[1]) for row in cursor.fetchall())
        conn.close()
        return result
    except Exception:
        return set()


def save_duplicate_ok(pono_lineno_list):
    """問題なしをデータベースに保存"""
    if not DB_PATH.exists():
        return 0
    init_duplicate_ok_table()
    conn = sqlite3.connect(DB_PATH)
    count = 0
    for pono, lineno in pono_lineno_list:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO duplicate_ok (pono, lineno, created_at) VALUES (?, ?, ?)",
                (str(pono), int(lineno), datetime.now().isoformat())
            )
            count += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return count


def delete_duplicate_ok(pono_lineno_list):
    """問題なしをデータベースから削除"""
    if not DB_PATH.exists():
        return 0
    conn = sqlite3.connect(DB_PATH)
    count = 0
    for pono, lineno in pono_lineno_list:
        try:
            cursor = conn.execute(
                "DELETE FROM duplicate_ok WHERE pono = ? AND lineno = ?",
                (str(pono), int(lineno))
            )
            count += cursor.rowcount
        except Exception:
            pass
    conn.commit()
    conn.close()
    return count


# EJ Oracle DB設定
EJ_DB_HOST = "172.17.107.102"
EJ_DB_PORT = "1521"
EJ_DB_SERVICE = "EXPJ"
EJ_DB_USER = "EXPJ2"
EJ_DB_PASSWORD = "EXPJ2"

# oracledb thick mode初期化フラグ
_ej_thick_mode_initialized = False


def init_oracle_client():
    """Oracle clientの初期化（初回のみ）"""
    global _ej_thick_mode_initialized
    if not _ej_thick_mode_initialized:
        try:
            oracledb.init_oracle_client()
            _ej_thick_mode_initialized = True
        except Exception:
            pass  # 既に初期化済みの場合


def get_mapped_data(period_filter=None):
    """マッピング済みデータを取得（status='済' or '済2'、rbom_order_noがあるもののみ）

    Args:
        period_filter: 期間フィルタ（'2025年12月15日以降' or '2025年11月以前' or None=全件）
    """
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT ej_order_no, rbom_order_no, rbom_line_no, period
        FROM mapping_results
        WHERE status IN ('済', '済2')
          AND rbom_order_no IS NOT NULL
          AND rbom_order_no != ''
          AND rbom_order_no != 'rBOMで対応する発注の入力をお願いします'
    """
    if period_filter:
        query += f" AND period = '{period_filter}'"

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_ej_data_by_orders(order_list):
    """EJ発注番号リストからEJデータを取得（1000件ずつ分割）"""
    if not order_list:
        return pd.DataFrame()

    init_oracle_client()

    connection_string = f"{EJ_DB_USER}/{EJ_DB_PASSWORD}@{EJ_DB_HOST}:{EJ_DB_PORT}/{EJ_DB_SERVICE}"

    try:
        conn = oracledb.connect(connection_string)
        cursor = conn.cursor()

        all_rows = []
        columns = None

        # OracleのIN句は1000件制限があるため分割
        chunk_size = 900
        for i in range(0, len(order_list), chunk_size):
            chunk = order_list[i:i + chunk_size]
            placeholders = ",".join([f"'{o}'" for o in chunk])

            query = f"""
                SELECT
                    PUCH_ODR_CD as ej_order_no,
                    PUCH_ODR_PERSON as ej_tancd,
                    VEND_CD as ej_srcd,
                    ITEM_CD as ej_hmcd,
                    PUCH_ODR_DLV_DATE as ej_drvdt,
                    PUCH_ODR_QTY as ej_qty,
                    UNIT_COST as ej_price
                FROM EXPJ2.T_RLSD_PUCH_ODR
                WHERE PUCH_ODR_CD IN ({placeholders})
            """

            cursor.execute(query)
            if columns is None:
                columns = [desc[0].lower() for desc in cursor.description]
            rows = cursor.fetchall()
            all_rows.extend(rows)

        conn.close()

        df = pd.DataFrame(all_rows, columns=columns)

        # 日付変換
        if 'ej_drvdt' in df.columns:
            df['ej_drvdt'] = pd.to_datetime(df['ej_drvdt']).dt.strftime("%Y-%m-%d")

        return df
    except Exception as e:
        return pd.DataFrame(), str(e)


def fetch_all_pages(table, columns, headers):
    """APIから全ページを取得"""
    all_data = []
    offset = 0
    limit = 10000

    while True:
        payload = {
            "table": table,
            "columns": columns,
            "limit": limit,
            "offset": offset
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            return None, f"{table} API エラー: {resp.status_code} - {resp.text[:200]}"

        data = resp.json().get("rows", [])
        if not data:
            break

        all_data.extend(data)
        if len(data) < limit:
            break
        offset += limit

    return all_data, None


def get_d3360_data_by_orders(pono_lineno_list):
    """D3360（受入明細F）からPONO+POLINENOでデータを取得

    同じPONO+POLINENO+PRICEの場合はRCVQTYを合計して1行に集約
    PRICEが異なる場合は複数行で返す
    """
    if not pono_lineno_list:
        return pd.DataFrame()

    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        # D3360から受入数と単価を取得（全件）
        data_d3360, err = fetch_all_pages("D3360", ["PONO", "POLINENO", "RCVQTY", "PRICE"], headers)
        if err:
            return pd.DataFrame()

        df_d3360 = pd.DataFrame(data_d3360)
        if df_d3360.empty:
            return pd.DataFrame()

        # 指定されたPONO+POLINENOのみ抽出
        pono_lineno_set = set([(str(p), int(l)) for p, l in pono_lineno_list])
        df_d3360["_key"] = list(zip(df_d3360["PONO"].astype(str), df_d3360["POLINENO"].astype(int)))
        df_filtered = df_d3360[df_d3360["_key"].isin(pono_lineno_set)].copy()
        df_filtered = df_filtered.drop(columns=["_key"])

        if df_filtered.empty:
            return pd.DataFrame()

        # PONO+POLINENO+PRICEでグループ化し、RCVQTYを合計
        df_filtered['RCVQTY'] = pd.to_numeric(df_filtered['RCVQTY'], errors='coerce').fillna(0)
        df_filtered['PRICE'] = pd.to_numeric(df_filtered['PRICE'], errors='coerce')

        df_grouped = df_filtered.groupby(['PONO', 'POLINENO', 'PRICE'], as_index=False).agg({
            'RCVQTY': 'sum'
        })

        # カラム名を変換
        df_grouped = df_grouped.rename(columns={
            "PONO": "rbom_order_no",
            "POLINENO": "rbom_line_no",
            "RCVQTY": "d3360_rcvqty",
            "PRICE": "d3360_price"
        })

        return df_grouped
    except Exception:
        return pd.DataFrame()


def get_rbom_data_by_orders(pono_lineno_list):
    """rBOM発注番号+行番号リストからrBOMデータを取得"""
    if not pono_lineno_list:
        return pd.DataFrame(), "PONO+LINENOリストが空です"

    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        # D3330（担当者コード、仕入先コード）- 全件取得
        data_d3330, err_d3330 = fetch_all_pages("D3330", ["PONO", "TANCD", "SRCD"], headers)
        if err_d3330:
            return pd.DataFrame(), err_d3330

        # D3340（品目コード、希望納期、発注数、単価、状態）- 全件取得
        data_d3340, err_d3340 = fetch_all_pages("D3340", ["PONO", "LINENO", "HMCD", "DRVDT", "THQTY", "PRICE", "STATUS"], headers)
        if err_d3340:
            return pd.DataFrame(), err_d3340

        df_d3330 = pd.DataFrame(data_d3330)
        df_d3340 = pd.DataFrame(data_d3340)

        if df_d3330.empty:
            return pd.DataFrame(), "D3330データが空です"
        if df_d3340.empty:
            return pd.DataFrame(), "D3340データが空です"

        # 結合
        df_merged = pd.merge(df_d3340, df_d3330, on="PONO", how="left")

        # 指定されたPONO+LINENOのみ抽出
        pono_lineno_set = set([(str(p), int(l)) for p, l in pono_lineno_list])
        df_merged["_key"] = list(zip(df_merged["PONO"].astype(str), df_merged["LINENO"].astype(int)))
        df_filtered = df_merged[df_merged["_key"].isin(pono_lineno_set)].copy()
        df_filtered = df_filtered.drop(columns=["_key"])

        if df_filtered.empty:
            return pd.DataFrame(), f"PONO+LINENOでフィルタ後データが空です（元データ: {len(df_merged)}件）"

        # カラム名を変換
        df_filtered = df_filtered.rename(columns={
            "PONO": "rbom_order_no",
            "LINENO": "rbom_line_no",
            "TANCD": "rbom_tancd",
            "SRCD": "rbom_srcd",
            "HMCD": "rbom_hmcd",
            "DRVDT": "rbom_drvdt",
            "THQTY": "rbom_qty",
            "PRICE": "rbom_price",
            "STATUS": "rbom_status"
        })

        # 日付変換
        if 'rbom_drvdt' in df_filtered.columns:
            df_filtered['rbom_drvdt'] = pd.to_datetime(df_filtered['rbom_drvdt']).dt.strftime("%Y-%m-%d")

        return df_filtered, None
    except Exception as e:
        return pd.DataFrame(), f"例外: {str(e)}"


def check_item_differences(period_filter=None):
    """EJとrBOMの項目差異をチェック

    Args:
        period_filter: 期間フィルタ（'2025年12月15日以降' or '2025年11月以前' or None=全件）
    """
    # 1. マッピング済みデータ取得
    df_mapped = get_mapped_data(period_filter)
    if df_mapped.empty:
        return None, "マッピング済みデータがありません"

    # 2. EJデータ取得
    ej_order_list = df_mapped['ej_order_no'].dropna().unique().tolist()
    ej_result = get_ej_data_by_orders(ej_order_list)
    if isinstance(ej_result, tuple):
        return None, f"EJデータ取得エラー: {ej_result[1]}"
    df_ej = ej_result
    if df_ej.empty:
        return None, "EJデータが取得できませんでした"

    # EJで取得できなかった発注番号を特定
    ej_found_orders = set(df_ej['ej_order_no'].unique())
    ej_missing_orders = [o for o in ej_order_list if o not in ej_found_orders]

    # 3. rBOMデータ取得
    pono_lineno_list = [
        (row['rbom_order_no'], int(row['rbom_line_no']))
        for _, row in df_mapped.iterrows()
        if pd.notna(row['rbom_order_no']) and pd.notna(row['rbom_line_no'])
    ]
    rbom_result = get_rbom_data_by_orders(pono_lineno_list)
    if isinstance(rbom_result, tuple):
        df_rbom, rbom_error = rbom_result
        if rbom_error:
            return None, f"rBOMデータ取得エラー: {rbom_error}"
    else:
        df_rbom = rbom_result
    if df_rbom.empty:
        return None, "rBOMデータが取得できませんでした"

    # 4. マッピングデータと結合
    df_merged = df_mapped.merge(df_ej, on='ej_order_no', how='left')
    # NaN行を除外してからint変換
    df_merged = df_merged.dropna(subset=['rbom_line_no'])
    df_merged['rbom_line_no'] = df_merged['rbom_line_no'].astype(int)
    df_merged = df_merged.merge(df_rbom, on=['rbom_order_no', 'rbom_line_no'], how='left')

    # 5. rBOMデータが存在しない行を特定（rbom_tancdがNaN）
    rbom_missing_mask = df_merged['rbom_tancd'].isna()
    df_rbom_missing = df_merged[rbom_missing_mask][['ej_order_no', 'rbom_order_no', 'rbom_line_no']].copy()
    df_rbom_missing.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号']

    # rBOMデータが存在する行のみで不一致チェック
    df_valid = df_merged[~rbom_missing_mask].copy()

    # 6. 各項目の不一致を検出
    results = {}

    # 担当者コード不一致
    mask_tancd = df_valid['ej_tancd'].astype(str) != df_valid['rbom_tancd'].astype(str)
    df_tancd = df_valid[mask_tancd][['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_tancd', 'rbom_tancd']].copy()
    df_tancd.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ担当者コード', 'rBOM担当者コード']
    results['担当者コード不一致'] = df_tancd

    # 仕入先コード不一致
    mask_srcd = df_valid['ej_srcd'].astype(str) != df_valid['rbom_srcd'].astype(str)
    df_srcd = df_valid[mask_srcd][['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_srcd', 'rbom_srcd']].copy()
    df_srcd.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ仕入先コード', 'rBOM仕入先コード']
    results['仕入先コード不一致'] = df_srcd

    # 品目コード不一致
    mask_hmcd = df_valid['ej_hmcd'].astype(str) != df_valid['rbom_hmcd'].astype(str)
    df_hmcd = df_valid[mask_hmcd][['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_hmcd', 'rbom_hmcd']].copy()

    # MK020のNOTEと照合して除外判定
    if not df_hmcd.empty:
        # MK020からOYAHMCDとNOTEを取得
        headers_mk020 = {
            "X-API-KEY": API_KEY,
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        mk020_data, mk020_err = fetch_all_pages("MK020", ["OYAHMCD", "NOTE"], headers_mk020)
        if mk020_data and not mk020_err:
            df_mk020 = pd.DataFrame(mk020_data)
            # OYAHMCDごとにNOTEをリスト化（同じOYAHMCDに複数行ある場合）
            df_mk020['NOTE'] = df_mk020['NOTE'].fillna('').astype(str)
            mk020_notes = df_mk020.groupby('OYAHMCD')['NOTE'].apply(set).to_dict()

            # 除外判定: rbom_hmcd（OYAHMCD）に紐づくNOTEの中にej_hmcdが含まれていれば除外
            def should_exclude(row):
                rbom_hmcd = str(row['rbom_hmcd'])
                ej_hmcd = str(row['ej_hmcd'])
                notes = mk020_notes.get(rbom_hmcd, set())
                return ej_hmcd in notes

            mask_exclude = df_hmcd.apply(should_exclude, axis=1)
            df_hmcd = df_hmcd[~mask_exclude].copy()

    df_hmcd = df_hmcd[['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_hmcd', 'rbom_hmcd']]
    df_hmcd.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ品目コード', 'rBOM品目コード']
    results['品目コード不一致'] = df_hmcd

    # 希望納期不一致
    mask_drvdt = df_valid['ej_drvdt'].astype(str) != df_valid['rbom_drvdt'].astype(str)
    df_drvdt = df_valid[mask_drvdt][['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_drvdt', 'rbom_drvdt']].copy()
    df_drvdt.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ希望納期', 'rBOM希望納期']
    results['希望納期不一致'] = df_drvdt

    # 発注数不一致
    df_valid['ej_qty_float'] = pd.to_numeric(df_valid['ej_qty'], errors='coerce')
    df_valid['rbom_qty_float'] = pd.to_numeric(df_valid['rbom_qty'], errors='coerce')
    mask_qty = df_valid['ej_qty_float'] != df_valid['rbom_qty_float']
    df_qty = df_valid[mask_qty][['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_qty', 'rbom_qty']].copy()
    df_qty.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ発注数', 'rBOM発注数']
    results['発注数不一致'] = df_qty

    # 単価不一致
    df_valid['ej_price_float'] = pd.to_numeric(df_valid['ej_price'], errors='coerce')
    df_valid['rbom_price_float'] = pd.to_numeric(df_valid['rbom_price'], errors='coerce')
    mask_price = df_valid['ej_price_float'] != df_valid['rbom_price_float']
    df_price = df_valid[mask_price][['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_price', 'rbom_price', 'ej_qty', 'rbom_status']].copy()

    # D3360（受入明細）からデータを取得して結合
    if not df_price.empty:
        price_pono_lineno_list = [
            (row['rbom_order_no'], int(row['rbom_line_no']))
            for _, row in df_price.iterrows()
            if pd.notna(row['rbom_order_no']) and pd.notna(row['rbom_line_no'])
        ]
        df_d3360 = get_d3360_data_by_orders(price_pono_lineno_list)

        if not df_d3360.empty:
            # rbom_line_noをintに変換して結合
            df_price['rbom_line_no'] = df_price['rbom_line_no'].astype(int)
            df_d3360['rbom_line_no'] = df_d3360['rbom_line_no'].astype(int)
            # D3360は同じPONO+LINENOで複数行（PRICEが異なる場合）があるのでleft join
            df_price = df_price.merge(df_d3360, on=['rbom_order_no', 'rbom_line_no'], how='left')

            # 同じEJ発注番号のrBOM受入_受入数の合計を計算
            df_price['d3360_rcvqty_numeric'] = pd.to_numeric(df_price['d3360_rcvqty'], errors='coerce').fillna(0)
            ej_rcvqty_sum = df_price.groupby('ej_order_no')['d3360_rcvqty_numeric'].transform('sum')
            df_price['d3360_rcvqty_total'] = ej_rcvqty_sum
            df_price = df_price.drop(columns=['d3360_rcvqty_numeric'])

            # 「不一致の中の一致データ」の発注数合計を計算（除外判定に使用するため先に計算）
            # EJ発注番号に対して、EJ単価=D3340.PRICEとなるマッピングのTHQTYを合計
            mismatch_ej_orders = df_price['ej_order_no'].unique().tolist()
            df_all_mapped_for_ej = df_mapped[df_mapped['ej_order_no'].isin(mismatch_ej_orders)].copy()
            if not df_all_mapped_for_ej.empty:
                # df_rbomにはrbom_price（D3340.PRICE）とrbom_qty（D3340.THQTY）が含まれている
                df_all_mapped_for_ej = df_all_mapped_for_ej.merge(
                    df_ej[['ej_order_no', 'ej_price']].drop_duplicates(),
                    on='ej_order_no', how='left'
                )
                df_all_mapped_for_ej['rbom_line_no'] = df_all_mapped_for_ej['rbom_line_no'].astype(int)
                df_all_mapped_for_ej = df_all_mapped_for_ej.merge(
                    df_rbom[['rbom_order_no', 'rbom_line_no', 'rbom_price', 'rbom_qty']],
                    on=['rbom_order_no', 'rbom_line_no'], how='left'
                )
                # EJ単価 = D3340.PRICE となるレコードを抽出
                ej_price_all = pd.to_numeric(df_all_mapped_for_ej['ej_price'], errors='coerce')
                rbom_price_all = pd.to_numeric(df_all_mapped_for_ej['rbom_price'], errors='coerce')
                mask_price_match = ej_price_all == rbom_price_all
                df_matched = df_all_mapped_for_ej[mask_price_match].copy()
                # EJ発注番号ごとにTHQTYを合計
                if not df_matched.empty:
                    df_matched['rbom_qty_numeric'] = pd.to_numeric(df_matched['rbom_qty'], errors='coerce').fillna(0)
                    matched_qty_sum = df_matched.groupby('ej_order_no')['rbom_qty_numeric'].sum().reset_index()
                    matched_qty_sum.columns = ['ej_order_no', 'matched_qty_total']
                    df_price = df_price.merge(matched_qty_sum, on='ej_order_no', how='left')
                else:
                    df_price['matched_qty_total'] = 0
            else:
                df_price['matched_qty_total'] = 0

            # matched_qty_totalのNaNを0に変換
            df_price['matched_qty_total'] = pd.to_numeric(df_price['matched_qty_total'], errors='coerce').fillna(0)

            # EJ単価=D3360単価 かつ EJ発注数量=(rBOM_受入合計+一致単価発注数合計) の行を除外
            ej_price_float = pd.to_numeric(df_price['ej_price'], errors='coerce')
            d3360_price_float = pd.to_numeric(df_price['d3360_price'], errors='coerce')
            ej_qty_float = pd.to_numeric(df_price['ej_qty'], errors='coerce')
            d3360_rcvqty_total_float = pd.to_numeric(df_price['d3360_rcvqty_total'], errors='coerce').fillna(0)
            matched_qty_total_float = pd.to_numeric(df_price['matched_qty_total'], errors='coerce').fillna(0)
            combined_total = d3360_rcvqty_total_float + matched_qty_total_float
            mask_exclude = (ej_price_float == d3360_price_float) & (ej_qty_float == combined_total)
            df_price = df_price[~mask_exclude].copy()

            # STATUSを日本語に変換
            status_map = {'2': '承認済み', '3': '一部完納', '4': '完納', '8': '強制完納'}
            df_price['rbom_status'] = df_price['rbom_status'].astype(str).map(lambda x: status_map.get(x, x))

            # 列順序を調整（状態を一番右に）
            df_price = df_price[['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_price', 'rbom_price', 'ej_qty', 'd3360_price', 'd3360_rcvqty', 'd3360_rcvqty_total', 'matched_qty_total', 'rbom_status']]
            df_price.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ単価', 'rBOM単価', 'EJ発注数量', 'rBOM受入_単価', 'rBOM受入_受入数', 'rBOM_受入合計', '一致単価発注数合計', '状態']
        else:
            df_price['d3360_price'] = None
            df_price['d3360_rcvqty'] = None
            df_price['d3360_rcvqty_total'] = None
            df_price['matched_qty_total'] = None
            # STATUSを日本語に変換
            status_map = {'2': '承認済み', '3': '一部完納', '4': '完納', '8': '強制完納'}
            df_price['rbom_status'] = df_price['rbom_status'].astype(str).map(lambda x: status_map.get(x, x))
            # 列順序を調整（状態を一番右に）
            df_price = df_price[['ej_order_no', 'rbom_order_no', 'rbom_line_no', 'ej_price', 'rbom_price', 'ej_qty', 'd3360_price', 'd3360_rcvqty', 'd3360_rcvqty_total', 'matched_qty_total', 'rbom_status']]
            df_price.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ単価', 'rBOM単価', 'EJ発注数量', 'rBOM受入_単価', 'rBOM受入_受入数', 'rBOM_受入合計', '一致単価発注数合計', '状態']
    else:
        # STATUSを日本語に変換
        status_map = {'2': '承認済み', '3': '一部完納', '4': '完納', '8': '強制完納'}
        df_price['rbom_status'] = df_price['rbom_status'].astype(str).map(lambda x: status_map.get(x, x))
        df_price.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号', 'EJ単価', 'rBOM単価', 'EJ発注数量', '状態']

    # config.iniで指定された除外EJ発注番号をフィルタリング
    exclude_ej_set = get_exclude_ej_orders()
    if exclude_ej_set and not df_price.empty:
        df_price = df_price[~df_price['EJ発注番号'].astype(str).isin(exclude_ej_set)].copy()

    results['単価不一致'] = df_price

    # EJ発注情報削除対象（EJで取得できなかった発注番号）
    if ej_missing_orders:
        df_missing = df_mapped[df_mapped['ej_order_no'].isin(ej_missing_orders)][['ej_order_no', 'rbom_order_no', 'rbom_line_no']].copy()
        df_missing.columns = ['EJ発注番号', 'rBOM発注番号', 'rBOM行番号']
        results['EJ発注情報削除'] = df_missing
    else:
        results['EJ発注情報削除'] = pd.DataFrame(columns=['EJ発注番号', 'rBOM発注番号', 'rBOM行番号'])

    # rBOM発注明細削除対象（D3340で取得できなかった行）
    results['rBOM発注明細削除'] = df_rbom_missing

    return results, None


def check_duplicate_orders():
    """rBOM重複発注チェック

    D3330.SRCD（仕入先コード）とD3340の品目コード、希望納期、発注数、単価で重複を検出
    """
    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    # D3330から仕入先コード、入力担当者、担当者コード取得（全件）
    d3330_data, err = fetch_all_pages("D3330", ["PONO", "SRCD", "UPDTID", "TANCD"], headers)
    if err:
        return None, f"D3330取得エラー: {err}"
    df_d3330 = pd.DataFrame(d3330_data)

    if df_d3330.empty:
        return None, "D3330データがありません"

    # D3340から品目コード、希望納期、発注数、単価、備考取得（全件）
    d3340_data, err = fetch_all_pages("D3340", ["PONO", "LINENO", "HMCD", "DRVDT", "THQTY", "PRICE", "NOTE"], headers)
    if err:
        return None, f"D3340取得エラー: {err}"
    df_d3340 = pd.DataFrame(d3340_data)

    if df_d3340.empty:
        return None, "D3340データがありません"

    # D3330とD3340をPONOで結合
    df_merged = pd.merge(df_d3340, df_d3330, on="PONO", how="left")

    # 重複チェック対象の6項目（担当者コードも含む）
    dup_columns = ["SRCD", "TANCD", "HMCD", "DRVDT", "THQTY", "PRICE"]

    # 重複キーを作成
    df_merged["dup_key"] = df_merged[dup_columns].astype(str).agg("-".join, axis=1)

    # 同じdup_keyで異なるPONOがあるものを重複として検出
    # （同じ発注番号内の重複は除外）
    dup_key_pono_count = df_merged.groupby("dup_key")["PONO"].nunique()
    dup_keys = dup_key_pono_count[dup_key_pono_count > 1].index.tolist()

    if not dup_keys:
        return pd.DataFrame(), None  # 重複なし

    # 重複行のみ抽出
    df_duplicates = df_merged[df_merged["dup_key"].isin(dup_keys)].copy()

    # 重複先を作成（同じdup_keyを持つ異なるPONOをリスト化）
    def get_dup_targets(row):
        same_key_rows = df_duplicates[df_duplicates["dup_key"] == row["dup_key"]]
        targets = []
        for _, r in same_key_rows.iterrows():
            # 異なるPONOのみを重複先として表示（同一PONO内の行は除外）
            if r["PONO"] != row["PONO"]:
                targets.append(f"{r['PONO']}+{int(r['LINENO'])}")
        return ", ".join(targets) if targets else ""

    df_duplicates["DUP_TARGET"] = df_duplicates.apply(get_dup_targets, axis=1)

    # 重複連番を作成（同じdup_keyを持つ行に同じ番号を振る）
    unique_dup_keys = df_duplicates["dup_key"].unique()
    dup_key_to_no = {key: i + 1 for i, key in enumerate(unique_dup_keys)}
    df_duplicates["DUP_NO"] = df_duplicates["dup_key"].map(dup_key_to_no)

    df_duplicates = df_duplicates.drop(columns=["dup_key"])

    # 希望納期を日付形式(yyyy-mm-dd)に変換
    if "DRVDT" in df_duplicates.columns:
        df_duplicates["DRVDT"] = pd.to_datetime(df_duplicates["DRVDT"]).dt.strftime("%Y-%m-%d")

    # カラム名を日本語に変換
    df_duplicates = df_duplicates.rename(columns={
        "DUP_NO": "重複No",
        "PONO": "発注番号",
        "LINENO": "行番号",
        "UPDTID": "入力担当者",
        "TANCD": "担当者コード",
        "SRCD": "仕入先コード",
        "HMCD": "品目コード",
        "DRVDT": "希望納期",
        "THQTY": "発注数",
        "PRICE": "単価",
        "NOTE": "備考",
        "DUP_TARGET": "重複先"
    })

    # 表示順序を整理（重複Noを発注番号の左に配置、備考を末尾に）
    display_columns = ["重複No", "発注番号", "行番号", "重複先", "入力担当者", "担当者コード", "仕入先コード", "品目コード", "希望納期", "発注数", "単価", "備考"]
    df_duplicates = df_duplicates[display_columns]

    # 重複Noでソート（同じ重複グループがまとまる）
    df_duplicates = df_duplicates.sort_values(by=["重複No", "発注番号"])

    return df_duplicates, None


def main():
    # ヘッダー行（タイトルと更新日時を横並び）
    col_title, col_update = st.columns([6, 1])
    with col_title:
        st.markdown("#### EJ⇔rBOM発注マッピング情報")
    with col_update:
        last_update = get_last_update()
        if last_update:
            st.caption(f"更新: {last_update[:16]}")
        else:
            st.warning("DBなし")
            return

    # 説明文
    st.caption("この画面はEJとrBOMの並行運用に伴い、両システムの発注情報の対応を確認するための画面です")

    # タブで切り替え
    tab1, tab2, tab3, tab4 = st.tabs([PERIOD_DEC, PERIOD_NOV, "EJ⇔rBOM項目チェック", "rBOM重複発注チェック"])

    with tab1:
        df_dec = load_data(PERIOD_DEC)
        if df_dec.empty:
            st.info("データがありません")
        else:
            # フィルタ行（左50%にフィルタ、右50%にデータソース情報）
            col_left, col_right = st.columns(2)
            with col_left:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    ej_filter = st.text_input("EJ発注番号", key="ej_dec")
                with col2:
                    rbom_filter = st.text_input("rBOM発注番号", key="rbom_dec")
                with col3:
                    st.caption(f"全{len(df_dec):,}件")
            with col_right:
                st.info('このデータは "\\\\fsrv24\\rbom\\発注情報12月EJとrBOM.xlsx" をもとに作成しています')

            filtered = df_dec.copy()
            if ej_filter:
                filtered = filtered[
                    filtered['EJ発注番号'].astype(str).str.contains(ej_filter, na=False)
                ]
            if rbom_filter:
                filtered = filtered[
                    filtered['rBOM発注番号'].astype(str).str.contains(rbom_filter, na=False)
                ]

            st.caption(f"表示: {len(filtered):,}件")
            st.dataframe(filtered, use_container_width=True, height=600, hide_index=True)

    with tab2:
        df_nov = load_data(PERIOD_NOV)
        if df_nov.empty:
            st.info("データがありません")
        else:
            # フィルタ行（左50%にフィルタ、右50%にデータソース情報）
            col_left, col_right = st.columns(2)
            with col_left:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    ej_filter = st.text_input("EJ発注番号", key="ej_nov")
                with col2:
                    rbom_filter = st.text_input("rBOM発注番号", key="rbom_nov")
                with col3:
                    st.caption(f"全{len(df_nov):,}件")
            with col_right:
                st.info('このデータは "\\\\fsrv24\\rbom\\発注情報EJとrBOM.xlsx" をもとに作成しています')

            filtered = df_nov.copy()
            if ej_filter:
                filtered = filtered[
                    filtered['EJ発注番号'].astype(str).str.contains(ej_filter, na=False)
                ]
            if rbom_filter:
                filtered = filtered[
                    filtered['rBOM発注番号'].astype(str).str.contains(rbom_filter, na=False)
                ]

            st.caption(f"表示: {len(filtered):,}件")
            st.dataframe(filtered, use_container_width=True, height=600, hide_index=True)

    with tab3:
        # EJ⇔rBOM項目チェック
        st.markdown("##### EJ⇔rBOM項目チェック")
        st.markdown("マッピング済みデータのEJとrBOMの「担当者コード、仕入先コード、品目コード、希望納期、発注数、単価」の6項目を比較し、不一致を検出します")

        # セッションステートで結果を保持
        if "item_check_results" not in st.session_state:
            st.session_state.item_check_results = None
        if "item_check_error" not in st.session_state:
            st.session_state.item_check_error = None

        # 期間選択とボタンを横並び
        col_period, col_btn_item, col_msg_item = st.columns([1.5, 1, 4])
        with col_period:
            period_options = ["2025年12月15日以降の発注マッピング", "2025年11月以前の発注残マッピング"]
            selected_period = st.selectbox("期間", period_options, key="item_check_period")
        with col_btn_item:
            btn_item_check = st.button("項目チェック実行", key="btn_item_check")
        with col_msg_item:
            if st.session_state.item_check_results is None:
                st.markdown("<span style='color: #666;'>「項目チェック実行」ボタンを押してください</span>", unsafe_allow_html=True)
            elif st.session_state.item_check_error:
                pass  # エラーは下で表示
            else:
                # 期間によって集計対象を変更
                if selected_period == "2025年11月以前の発注残マッピング":
                    count_keys = {'担当者コード不一致', '仕入先コード不一致', '単価不一致'}
                else:
                    count_keys = {'担当者コード不一致', '仕入先コード不一致', '品目コード不一致', '希望納期不一致', '発注数不一致', '単価不一致'}
                total_diff = sum(len(df) for key, df in st.session_state.item_check_results.items() if key in count_keys)
                ej_missing_count = len(st.session_state.item_check_results.get('EJ発注情報削除', []))
                rbom_missing_count = len(st.session_state.item_check_results.get('rBOM発注明細削除', []))
                msg = f"不一致が {total_diff} 件見つかりました"
                if ej_missing_count > 0:
                    msg += f"、EJ削除対象 {ej_missing_count} 件"
                if rbom_missing_count > 0:
                    msg += f"、rBOM削除対象 {rbom_missing_count} 件"
                st.markdown(f"<span style='color: #666;'>{msg}</span>", unsafe_allow_html=True)

        # チェック実行
        if btn_item_check:
            with st.spinner("チェック中..."):
                results, error = check_item_differences(selected_period)
                st.session_state.item_check_results = results
                st.session_state.item_check_error = error
                st.rerun()

        # 結果表示
        error = st.session_state.item_check_error
        results = st.session_state.item_check_results

        if error:
            st.error(error)
        elif results is not None:
            # 期間によって表示項目を変更
            if selected_period == "2025年11月以前の発注残マッピング":
                # 11月以前は3項目のみ
                check_items = [
                    '担当者コード不一致',
                    '仕入先コード不一致',
                    '単価不一致'
                ]
            else:
                # 12月以降は6項目すべて
                check_items = [
                    '担当者コード不一致',
                    '仕入先コード不一致',
                    '品目コード不一致',
                    '希望納期不一致',
                    '発注数不一致',
                    '単価不一致'
                ]

            for item_name in check_items:
                df = results.get(item_name, pd.DataFrame())
                with st.expander(f"{item_name}（{len(df)}件）", expanded=len(df) > 0):
                    if df.empty:
                        st.success("不一致なし")
                    else:
                        st.dataframe(df, use_container_width=True, height=300, hide_index=True)

            # 11月以前の場合、除外項目の理由を表示
            if selected_period == "2025年11月以前の発注残マッピング":
                st.markdown("---")
                st.markdown("##### 検証対象外の項目")
                st.markdown("""
- **品目コード不一致**: 工程発注の考え方が異なるため検証対象外です
- **希望納期不一致**: 11月発注残のマッピング処理に納期は未考慮のため検証対象外です
- **発注数不一致**: 1対多のマッピングを行っているため検証対象外です
""")

            # EJ発注情報削除セクション
            st.markdown("---")
            df_ej_missing = results.get('EJ発注情報削除', pd.DataFrame())
            with st.expander(f"EJ発注情報削除（{len(df_ej_missing)}件）", expanded=len(df_ej_missing) > 0):
                st.markdown("EJ発注番号をキーにしてもEJデータベースから行を取得できなかったデータです。EJで既に削除されている可能性があります。")
                if df_ej_missing.empty:
                    st.success("削除対象なし")
                else:
                    st.dataframe(df_ej_missing, use_container_width=True, height=300, hide_index=True)

            # rBOM発注明細削除セクション
            df_rbom_missing = results.get('rBOM発注明細削除', pd.DataFrame())
            with st.expander(f"rBOM発注明細削除（{len(df_rbom_missing)}件）", expanded=len(df_rbom_missing) > 0):
                st.markdown("rBOM発注番号+行番号をキーにしてもD3340から行を取得できなかったデータです。rBOMで既に削除されている可能性があります。")
                if df_rbom_missing.empty:
                    st.success("削除対象なし")
                else:
                    st.dataframe(df_rbom_missing, use_container_width=True, height=300, hide_index=True)

    with tab4:
        # rBOM重複発注チェック
        st.markdown("##### rBOM重複発注チェック")
        st.markdown("""
rBOMの発注のうち、担当者コード、仕入先コード、品目コード、希望納期、発注数、単価の6項目すべてが重複した発注を検出します
- 問題がない場合は問題無しにチェックして「問題なしチェック更新」ボタンを押下してください
- 重複発注だった場合は、rBOMの発注情報を削除して下さい
""")

        # セッションステートで結果を保持
        if "df_dup_result" not in st.session_state:
            st.session_state.df_dup_result = None
        if "df_dup_error" not in st.session_state:
            st.session_state.df_dup_error = None

        # ボタンとチェックボックスを横並び
        col_btn, col_update, col_show_all, col_gap, col_count, col_spacer = st.columns([1, 1.2, 1, 0.5, 2, 1.5])
        with col_btn:
            btn_check = st.button("重複チェック実行", key="btn_dup_check")
        with col_update:
            btn_update = st.button("問題なしチェック更新", key="btn_dup_ok_update")
        with col_show_all:
            show_all = st.checkbox("問題なしも表示", key="chk_show_all")
        # col_gap は空きスペース
        with col_count:
            # 件数表示またはメッセージ
            if st.session_state.df_dup_result is None:
                st.markdown("<span style='color: #666;'>「重複チェック実行」ボタンを押してください</span>", unsafe_allow_html=True)
            elif not st.session_state.df_dup_result.empty:
                df_result = st.session_state.df_dup_result
                if show_all:
                    # 問題なしも含めた全件数
                    display_count = len(df_result)
                else:
                    # 問題なし登録済みを除いた件数
                    ok_set = get_duplicate_ok_set()
                    display_count = sum(
                        1 for _, row in df_result.iterrows()
                        if (str(row["発注番号"]), int(row["行番号"])) not in ok_set
                    )
                st.markdown(f"<span style='color: #666;'>重複発注が {display_count} 件見つかりました</span>", unsafe_allow_html=True)

        # 重複チェック実行
        if btn_check:
            with st.spinner("チェック中..."):
                df_dup, error = check_duplicate_orders()
                st.session_state.df_dup_result = df_dup
                st.session_state.df_dup_error = error
                # チェック結果をクリア
                if "df_dup_edited_data" in st.session_state:
                    del st.session_state.df_dup_edited_data
                st.rerun()

        # 結果表示
        error = st.session_state.df_dup_error
        df_dup = st.session_state.df_dup_result

        if error:
            st.error(error)
        elif df_dup is None:
            pass  # メッセージはcol_countに表示済み
        elif df_dup.empty:
            st.success("重複発注はありませんでした")
        else:
            # 問題なし登録済みを取得
            ok_set = get_duplicate_ok_set()

            # 問題なしフラグを追加
            df_dup = df_dup.copy()
            df_dup["_is_ok"] = df_dup.apply(
                lambda row: (str(row["発注番号"]), int(row["行番号"])) in ok_set, axis=1
            )

            # 表示フィルタ
            if not show_all:
                df_display = df_dup[~df_dup["_is_ok"]].copy()
                # 問題なしチェック列を追加（デフォルトはFalse）
                df_display["問題なしチェック"] = False
            else:
                df_display = df_dup.copy()
                # 問題なしチェック列を追加（登録済みはTrue）
                df_display["問題なしチェック"] = df_display["_is_ok"]

            df_display = df_display.drop(columns=["_is_ok"])

            # 列順序を調整（重複Noを発注番号の左に、チェック列を行番号の後に、備考を末尾に）
            cols = ["重複No", "発注番号", "行番号", "問題なしチェック", "重複先", "入力担当者", "担当者コード", "仕入先コード", "品目コード", "希望納期", "発注数", "単価", "備考"]
            df_display = df_display[cols]

            if df_display.empty:
                st.success("未確認の重複発注はありません（問題なし登録済み）")
            else:
                # 編集可能なデータフレーム
                edited_df = st.data_editor(
                    df_display,
                    use_container_width=True,
                    height=600,
                    hide_index=True,
                    column_config={
                        "問題なしチェック": st.column_config.CheckboxColumn(
                            "問題なし",
                            default=False,
                        )
                    },
                    disabled=["重複No", "発注番号", "行番号", "重複先", "入力担当者", "担当者コード", "仕入先コード", "品目コード", "希望納期", "発注数", "単価", "備考"],
                    key="df_dup_editor"
                )

                # 編集結果をセッションステートに保存
                st.session_state.df_dup_edited_data = edited_df

        # 問題なしチェック更新（data_editorの後に処理）
        if btn_update:
            if "df_dup_edited_data" in st.session_state and st.session_state.df_dup_edited_data is not None:
                df_edited = st.session_state.df_dup_edited_data
                if "問題なしチェック" in df_edited.columns:
                    # 現在DBに登録済みのセット
                    current_ok_set = get_duplicate_ok_set()

                    # チェックが入っている行のセット
                    checked_rows = df_edited[df_edited["問題なしチェック"] == True]
                    checked_set = set(zip(checked_rows["発注番号"].astype(str), checked_rows["行番号"].astype(int)))

                    # チェックが外れている行のセット
                    unchecked_rows = df_edited[df_edited["問題なしチェック"] == False]
                    unchecked_set = set(zip(unchecked_rows["発注番号"].astype(str), unchecked_rows["行番号"].astype(int)))

                    # 新規登録対象（チェックされているが未登録）
                    to_add = [(pono, lineno) for pono, lineno in checked_set if (pono, lineno) not in current_ok_set]

                    # 削除対象（チェック解除されたが登録済み）
                    to_delete = [(pono, lineno) for pono, lineno in unchecked_set if (pono, lineno) in current_ok_set]

                    add_count = 0
                    del_count = 0

                    if to_add:
                        add_count = save_duplicate_ok(to_add)
                    if to_delete:
                        del_count = delete_duplicate_ok(to_delete)

                    if add_count > 0 or del_count > 0:
                        msg_parts = []
                        if add_count > 0:
                            msg_parts.append(f"{add_count} 件を登録")
                        if del_count > 0:
                            msg_parts.append(f"{del_count} 件を削除")
                        st.success("、".join(msg_parts) + "しました")
                        # 結果を再取得してリフレッシュ
                        st.rerun()
                    else:
                        st.info("変更がありません")
                else:
                    st.info("先に重複チェックを実行してください")
            else:
                st.info("先に重複チェックを実行してください")


if __name__ == "__main__":
    main()
