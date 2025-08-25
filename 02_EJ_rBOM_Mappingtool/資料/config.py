###
# アッセンブリー課チェックシート
# Start 20250625 ダイヤルキャップとホルダーを開始
# ADD_20250626 ギアボックス追加
###
import os

# --- アプリケーション基本設定 ---
PAGE_TITLE = "アセンブリチェックシート管理"

# --- データベース設定 ---
DB_DIR = "Database"
DB_NAME = "assembly_checksheet_DB.sqlite"
DB_PATH = os.path.join(DB_DIR, DB_NAME)

# --- テーブル名定義 ---
DIAL_CAP_CHECKSHEET_TABLE = "dial_cap_checks"
HOLDER_CHECKSHEET_TABLE = "holder_checks"
GEARBOX_CHECKSHEET_TABLE = "gearbox_gr_checks"
SINKER_CAP_CHECKSHEET_TABLE = "sinker_cap_checks"
WORKER_MASTER_TABLE = "worker_master"
INSTRUMENT_MASTER_TABLE = "instrument_master"

# --- 外部データベース接続情報 ---


def get_db_connection_url():
    """
    外部SQL Serverへの接続URLを生成します。
    接続情報はこの関数内で一元管理します。
    """
    username, password = "fukuharaadmin", "xrTRzAJtKQ7B"
    server = "production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com"
    database = "common"
    driver = "ODBC Driver 17 for SQL Server".replace(' ', '+')
    return f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}"


# --- UIスタイル設定 ---
# StreamlitのUIを調整するためのカスタムCSS
HIDE_ST_STYLE = """
<style>
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    #MainMenu,
    header,
    footer {
        display: none !important;
        height: 0px !important;
    }
    .appview-container .main .block-container{
        padding-top: 1rem;
        padding-right: 3rem;
        padding-left: 3rem;
        padding-bottom: 1rem;
    }
    header[data-testid="stHeader"] {
        z-index: -1;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 1rem !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        gap: 0.75rem;
    }
    div[data-testid="stButton"] > button {
        height: 38.4px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    /* AgGridのスタイル */
    .ag-header-cell { display: flex !important; align-items: center !important; } /* justify-contentは個別クラスで制御 */
    .ag-header-cell-text, .ag-header-group-cell-label { white-space: normal !important; text-align: center !important; line-height: 1.3 !important; }
    .custom-wrap-header .ag-header-group-cell-label { overflow: visible !important; overflow-wrap: break-word; }
    .ag-root-wrapper, .ag-cell, .ag-header-cell, .ag-header-group-cell { border-color: #000 !important; }
    .ag-header-cell, .ag-header-group-cell { border-bottom: 1px solid #000 !important; }
    .ag-cell { border-right: 1px solid #e2e2e2 !important; border-bottom: 1px solid #e2e2e2 !important; }

    /* [修正] ヘッダーを強制的に中央揃えにするためのスタイル */
    .ag-header-cell-center-aligned {
        justify-content: center !important;
    }
    /* [追加] グループヘッダーも中央揃えにするためのスタイル */
    .ag-header-group-cell-centered .ag-header-group-cell-label {
        justify-content: center !important;
    }
</style>
"""
