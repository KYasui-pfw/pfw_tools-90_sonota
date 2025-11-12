# coding: utf-8
import streamlit as st
import pandas as pd
import pyexcel  # xlsをxlsxに変換するために使用
import numpy as np  # NaNの扱いに使用
import os  # 一時ファイルの削除に使用
import sqlite3
import io  # BytesIO を使用するためにインポート
import tempfile  # 一時ファイル/ディレクトリの管理
import traceback  # エラー詳細表示用
import time
from datetime import datetime, timedelta, timezone  # datetimeのインポートを確認
from sqlalchemy import create_engine  # sqlalchemyのインポートを確認
import psycopg2  # psycopg2のインポートを確認
import csv  # csvモジュールのインポートを確認

# --- 定数 ---
DB_FILE = "mapping_data.db"
TEMP_DIR = "temp_excel_conversion"  # 一時ファイル用ディレクトリ名
INPUT_XLS_FILE = r"\\fsrv24\会議室予約\内線電話一覧表.xls"
OUTPUT_XLS_PATH = r"D:\CustomMaster\CSV_UPLOAD/"  # ユーザー提供コードから
DEFAULT_SHOZOKU_CODE = 8888  # 所属コードのデフォルト値
DEFAULT_HYOUJI_JUN = 88  # 表示順のデフォルト値
EMPTY_YAKUSHOKU_HYOUJI_JUN_KEY = "一般"  # 役職空欄時の表示順マッピングキー
CORRECT_PASSWORD = "dxadmin"  # ★★★ 認証用パスワード ★★★

# --- データベース関連 ---


def init_db():
    """データベースとテーブルを初期化する"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 所属コードマッピングテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shozoku_map (
            shozoku TEXT PRIMARY KEY,
            code INTEGER UNIQUE NOT NULL
        )
    ''')
    # 初期データ投入 (存在しない場合)
    cursor.execute("SELECT COUNT(*) FROM shozoku_map")
    if cursor.fetchone()[0] == 0:
        initial_shozoku_data = {
            "DX推進室": 501, "総務部": 1000, "総務課": 1001, "技術部": 2000,
            "設計課": 2001, "開発課": 2005, "技術サービス課": 2007, "品質管理課": 2009,
            "企画部": 3000, "購買課": 3001, "戦略企画課": 3003, "生産技術課": 3011,
            "生産部": 4000, "アッセンブリー課": 4003, "ニット課": 4005, "マシニング課": 4007,
            "カム課": 4009, "シリンダー課": 4011, "社長": 9999, "業務委託": 8000,
            "新入社員": 8500
        }
        cursor.executemany("INSERT INTO shozoku_map (shozoku, code) VALUES (?, ?)",
                           initial_shozoku_data.items())

    # 表示順マッピングテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hyouji_jun_map (
            yakushoku TEXT PRIMARY KEY,
            jun INTEGER UNIQUE NOT NULL
        )
    ''')
    # 初期データ投入 (存在しない場合)
    cursor.execute("SELECT COUNT(*) FROM hyouji_jun_map")
    if cursor.fetchone()[0] == 0:
        initial_hyouji_jun_data = {
            "社長": 0, "専務": 1, "常務": 2, "部長": 3, "次長": 4, "顧問": 5,
            "CL": 6, "担当課長": 7, "専任課長": 8, "参事": 9, "副参事": 10,
            "SL": 11, "参事補": 12, "GL": 13, "主事": 14, "主任": 15,
            "主事補": 16, "一般": 20, "嘱託": 21, "臨時": 22, "委託": 23,
            "派遣": 30, "パート": 99
        }
        cursor.executemany("INSERT INTO hyouji_jun_map (yakushoku, jun) VALUES (?, ?)",
                           initial_hyouji_jun_data.items())

    # 追加社員情報テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS additional_employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shozoku TEXT NOT NULL,
            yakushoku TEXT NOT NULL,
            shimei TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()


def load_shozoku_map_from_db():
    """データベースから所属コードマップを読み込む"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT DISTINCT shozoku, code FROM shozoku_map WHERE shozoku IS NOT NULL AND code IS NOT NULL ORDER BY code ASC", conn)
    conn.close()
    return df


def load_hyouji_jun_map_from_db():
    """データベースから表示順マップを読み込む"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT DISTINCT yakushoku, jun FROM hyouji_jun_map WHERE yakushoku IS NOT NULL AND jun IS NOT NULL ORDER BY jun ASC", conn)
    conn.close()
    return df


def update_shozoku_map_in_db(df):
    """データベースの所属コードマップを更新する"""
    # NaNや空文字を除外
    df_cleaned = df.dropna(subset=['shozoku', 'code'])
    df_cleaned = df_cleaned[df_cleaned['shozoku'].astype(
        str).str.strip() != '']
    df_cleaned['code'] = pd.to_numeric(
        df_cleaned['code'], errors='coerce').dropna().astype(int)
    # 重複を削除 (最初のものを残す)
    df_cleaned = df_cleaned.drop_duplicates(subset=['shozoku'], keep='first')
    df_cleaned = df_cleaned.drop_duplicates(subset=['code'], keep='first')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shozoku_map")  # 既存データを全削除
    df_cleaned.to_sql('shozoku_map', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()


def update_hyouji_jun_map_in_db(df):
    """データベースの表示順マップを更新する"""
    # NaNや空文字を除外
    df_cleaned = df.dropna(subset=['yakushoku', 'jun'])
    df_cleaned = df_cleaned[df_cleaned['yakushoku'].astype(
        str).str.strip() != '']
    df_cleaned['jun'] = pd.to_numeric(
        df_cleaned['jun'], errors='coerce').dropna().astype(int)
    # 重複を削除 (最初のものを残す)
    df_cleaned = df_cleaned.drop_duplicates(subset=['yakushoku'], keep='first')
    df_cleaned = df_cleaned.drop_duplicates(subset=['jun'], keep='first')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hyouji_jun_map")  # 既存データを全削除
    df_cleaned.to_sql('hyouji_jun_map', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()

# 追加社員情報関連のDB関数


def load_additional_employees():
    """追加社員情報をデータベースから読み込む (id を除く)"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT shozoku, yakushoku, shimei FROM additional_employees ORDER BY id", conn)
    conn.close()
    return df


def update_additional_employees(df):
    """追加社員情報をデータベースで更新する (id を除く)"""
    if 'カウント' in df.columns:
        df_cleaned = df.drop(columns=['カウント'])
    else:
        df_cleaned = df.copy()

    # NaNや空文字を除外
    df_cleaned = df_cleaned.dropna(subset=['shozoku', 'yakushoku', 'shimei'])
    df_cleaned = df_cleaned[df_cleaned['shozoku'].astype(
        str).str.strip() != '']
    df_cleaned = df_cleaned[df_cleaned['yakushoku'].astype(
        str).str.strip() != '']
    df_cleaned = df_cleaned[df_cleaned['shimei'].astype(str).str.strip() != '']
    # 氏名の重複を削除 (最初のものを残す)
    df_cleaned = df_cleaned.drop_duplicates(subset=['shimei'], keep='first')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM additional_employees")  # 既存データを全削除
    df_cleaned[['shozoku', 'yakushoku', 'shimei']].to_sql(
        'additional_employees', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()

# ireporterDB


def ireporter_data_get(sql):
    # SQLAlchemyのエンジンを作成
    engine = create_engine(
        "postgresql+psycopg2://postgres:cimtops@ESRV10/irepodb")

    # pandasの read_sql 関数にエンジンとSQLクエリを渡す
    df = pd.read_sql(sql, con=engine)

    # エンジンは明示的にdisposeする必要がある場合があります (特に長時間実行するアプリケーション)
    engine.dispose()

    return (df)


def df_csv_cnv(df):
    # DFをcsvにコンバートして出力
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    csv_name = OUTPUT_XLS_PATH+"\\" + \
        dt_now.strftime('%Y%m%d%H%M%S')+"_社員マスタデータ"+".csv"
    df.to_csv(csv_name, index=False, header=False,
              encoding='CP932', quoting=csv.QUOTE_ALL)

# --- データ処理関数 ---


def process_phonebook_data(file_path):
    """
    指定されたXLSファイルを処理し、データフレームを返す。
    元のスクリプトの処理1～11を実行する。
    """
    # 一時ディレクトリ作成 (存在しない場合)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # 一時ファイル名 (ファイル名から作成)
    base_name = os.path.basename(file_path)
    temp_xlsx_path = os.path.join(
        TEMP_DIR, f"temp_{os.path.splitext(base_name)[0]}.xlsx")

    # マッピングデータをDBから読み込む
    df_shozoku_map = load_shozoku_map_from_db()
    SHOZOKU_CODE_MAP = pd.Series(
        df_shozoku_map.code.values, index=df_shozoku_map.shozoku).to_dict()

    df_hyouji_jun_map = load_hyouji_jun_map_from_db()
    HYOUJI_JUN_MAP = pd.Series(
        df_hyouji_jun_map.jun.values, index=df_hyouji_jun_map.yakushoku).to_dict()

    processed_df = None
    error_message = None

    try:
        # --- xlsをxlsxに変換 ---
        print(f"'{file_path}' を一時XLSXファイルに変換しています...")
        pyexcel.save_book_as(file_name=file_path,
                             dest_file_name=temp_xlsx_path)
        print(f"変換完了: '{os.path.basename(temp_xlsx_path)}'")

        # --- Excelファイルの読み込み (openpyxlエンジンを使用) ---
        print(f"一時XLSXファイル '{os.path.basename(temp_xlsx_path)}' を読み込んでいます...")
        df_bcd = pd.read_excel(
            temp_xlsx_path, engine='openpyxl', header=None, usecols=[1, 2, 3])
        df_fgh = pd.read_excel(
            temp_xlsx_path, engine='openpyxl', header=None, usecols=[5, 6, 7])
        df_jkl = pd.read_excel(
            temp_xlsx_path, engine='openpyxl', header=None, usecols=[9, 10, 11])
        df_nop = pd.read_excel(
            temp_xlsx_path, engine='openpyxl', header=None, usecols=[13, 14, 15])
        print("ファイル読み込み完了。")

        # --- 以降、元のスクリプトの処理 ---

        # 【処理１】縦に結合
        print("処理1: 列データを縦に結合しています...")
        temp_cols = [0, 1, 2]
        df_bcd.columns = temp_cols
        df_fgh.columns = temp_cols
        df_jkl.columns = temp_cols
        df_nop.columns = temp_cols
        df_combined = pd.concat(
            [df_bcd, df_fgh, df_jkl, df_nop], ignore_index=True)
        print("結合完了。")

        # 【処理２】カラム名を変更
        print("処理2: カラム名を変更しています...")
        df_combined.columns = ["役職", "No", "氏名"]
        print("カラム名変更完了。")

        # ★★★ 追加: 役職が"-"の場合は"委託"に置換 ★★★
        df_combined.loc[df_combined["役職"] == "-", "役職"] = "委託"
        print("役職が'-'の行を'委託'に置換しました。")

        # データクリーニング前処理: 全ての列がNaNの行を削除
        df_combined.dropna(how='all', inplace=True)
        df_combined.reset_index(drop=True, inplace=True)

        # 【処理３】カラム名"役職"の中の空白文字列（全角スペースと半角スペース）と"☆"を削除
        print("処理3: '役職'カラムの値をクリーニングしています...")
        df_combined["役職"] = df_combined["役職"].fillna('').astype(str)
        df_combined["役職"] = df_combined["役職"].str.replace('　', '', regex=False)\
            .str.replace(' ', '', regex=False)\
            .str.replace('☆', '', regex=False)
        print("'役職'カラムのクリーニング完了。")

        # 【処理４】1列目にカラム名"所属"を追加
        print("処理4: '所属'カラムを追加しています...")
        df_combined.insert(0, "所属", "")
        print("'所属'カラム追加完了。")

        # 【処理５】カラム名"役職"の最後の一文字が"役"または"室"または"部"または"課"または"業務委託"または"新入社員"のとき、
        #           カラム名"所属"にカラム名"役職"をセットする
        print("処理5: '所属'カラムの初期値を設定しています...")
        shozoku_keywords = list(SHOZOKU_CODE_MAP.keys())  # DBから取得した所属名リスト
        conditions_shokumu_is_or_ends = (
            df_combined["役職"].isin(shozoku_keywords) |  # 完全一致 (DBのキーと比較)
            df_combined["役職"].str.endswith(tuple(k for k in shozoku_keywords if k.endswith(
                ("役", "室", "部", "課"))))  # 末尾一致 (DBのキーと比較)
        ) & (df_combined["役職"] != '')  # 空白でないこと
        df_combined.loc[conditions_shokumu_is_or_ends,
                        "所属"] = df_combined.loc[conditions_shokumu_is_or_ends, "役職"]
        print("'所属'カラム初期値設定完了。")

        # 【処理６】カラム名"所属"には一行上のカラム名"所属"を追加する (forward fill)
        print("処理6: '所属'カラムの値を前方補完しています...")
        df_combined['所属'] = df_combined['所属'].replace('', np.nan)
        df_combined["所属"] = df_combined["所属"].ffill()
        df_combined['所属'].fillna('', inplace=True)  # NaNが残る場合（先頭行など）は空文字に
        print("'所属'カラムの前方補完完了。")

        # 【処理７】
        print("処理7: 'No'カラムの処理と、'No'または'氏名'が不適切な行の削除を行っています...")
        # ★★★ 復活: 所属が"取締役"の場合は、"No"列に0をセットする ★★★
        df_combined.loc[df_combined["所属"] == "取締役", "No"] = 0
        df_combined["No"] = pd.to_numeric(df_combined["No"], errors='coerce')
        original_row_count = len(df_combined)

        # 'No'が数値でない行を削除
        df_combined.dropna(subset=["No"], inplace=True)
        deleted_rows_by_no = original_row_count - len(df_combined)
        if deleted_rows_by_no > 0:
            print(f"  'No'が数値でない、または空欄のため {deleted_rows_by_no} 行が削除されました。")

        df_combined["氏名"] = df_combined["氏名"].fillna('').astype(str)
        original_row_count = len(df_combined)
        # '氏名'が空欄の行を削除
        df_combined = df_combined[df_combined["氏名"].str.strip() != '']
        deleted_rows_by_shimei = original_row_count - len(df_combined)
        if deleted_rows_by_shimei > 0:
            print(f"  '氏名'が空欄のため {deleted_rows_by_shimei} 行が削除されました。")
        df_combined.reset_index(drop=True, inplace=True)
        print("'No'カラム処理と行削除完了。")

        # 【処理８】役職が"〇〇部次長"または"〇〇部部長"の場合、次長、部長のみ役職に残し、"〇〇部"の部分で所属を上書き
        print("処理8: 特定の役職パターンに基づいて'役職'と'所属'を更新しています...")
        pattern = r'(.+部)(部長|次長)$'
        extracted_parts = df_combined['役職'].str.extract(pattern, expand=True)
        extracted_parts.columns = ['extracted_shozoku', 'extracted_yakushoku']
        valid_indices = extracted_parts['extracted_shozoku'].notna(
        ) & extracted_parts['extracted_yakushoku'].notna()
        if valid_indices.any():
            df_combined.loc[valid_indices,
                            '所属'] = extracted_parts.loc[valid_indices, 'extracted_shozoku']
            df_combined.loc[valid_indices,
                            '役職'] = extracted_parts.loc[valid_indices, 'extracted_yakushoku']
            print(f"  {valid_indices.sum()} 行の'役職'と'所属'が更新されました。")
        else:
            print("  特定の役職パターンに一致する行はありませんでした。")
        print("特定パターンの'役職'と'所属'の更新完了。")

        # 【処理９】カラム名"所属コード"を追加
        print("処理9: '所属コード'カラムを追加しています...")
        df_combined['所属コード'] = df_combined['所属'].map(
            SHOZOKU_CODE_MAP).fillna(DEFAULT_SHOZOKU_CODE).astype(int)
        print("'所属コード'カラム追加完了。")

        # 【処理１０】カラム名"表示順"を追加
        print("処理10: '表示順'カラムを追加しています...")
        df_combined['役職_for_map'] = df_combined['役職'].fillna(
            '').astype(str).str.strip()
        # 空白またはマップにない役職の場合、'一般' として扱うか、デフォルト値を使う
        df_combined.loc[~df_combined['役職_for_map'].isin(
            HYOUJI_JUN_MAP.keys()), '役職_for_map'] = EMPTY_YAKUSHOKU_HYOUJI_JUN_KEY
        df_combined.loc[df_combined['役職_for_map'] == '',
                        '役職_for_map'] = EMPTY_YAKUSHOKU_HYOUJI_JUN_KEY  # 空白も'一般'に
        df_combined['表示順'] = df_combined['役職_for_map'].map(
            HYOUJI_JUN_MAP).fillna(DEFAULT_HYOUJI_JUN).astype(int)
        df_combined.drop(columns=['役職_for_map'], inplace=True)
        print("'表示順'カラム追加完了。")

        # 【処理１１】項目"表示順"を元に昇順に並べる
        print("処理11: '表示順'カラムでデータフレームを昇順に並べ替えています...")
        df_combined.sort_values(by=['所属コード', '表示順', 'No'], ascending=[
                                True, True, True], inplace=True)  # 所属コード、表示順、Noでソート
        df_combined.reset_index(drop=True, inplace=True)
        print("並べ替え完了。")

        # No列を整数型に変換 (dropnaしたのでNaNはないはず)
        df_combined['No'] = df_combined['No'].astype(int)

        processed_df = df_combined  # 最終結果を格納

    except FileNotFoundError:
        error_message = f"エラー: 指定されたファイルが見つかりません。\nパスを確認してください: {file_path}"
        print(error_message)
    except pyexcel.exceptions.FileTypeNotSupported:
        error_message = f"エラー: サポートされていないファイル形式です。'{os.path.basename(file_path)}' は有効な .xls ファイルですか？"
        print(error_message)
    except Exception as e:
        error_message = f"エラー: 処理中に予期せぬエラーが発生しました。\n{traceback.format_exc()}"
        print(error_message)

    finally:
        # 一時ファイルの削除
        print("一時ファイルをクリーンアップしています...")
        try:
            if 'temp_xlsx_path' in locals() and os.path.exists(temp_xlsx_path):  # 変数存在チェック追加
                os.remove(temp_xlsx_path)
                print(f"一時ファイル '{os.path.basename(temp_xlsx_path)}' を削除しました。")
            # ディレクトリが空なら削除
            if os.path.exists(TEMP_DIR) and not os.listdir(TEMP_DIR):
                os.rmdir(TEMP_DIR)
            print("クリーンアップ完了。")
        except Exception as e:
            print(f"警告: 一時ファイルの削除中にエラーが発生しました。{e}")

    return processed_df, error_message

# --- スタイル関数 ---


def highlight_updated_added(row):
    """行の _status 列に応じて背景色を適用する"""
    color = '#FFFFE0'  # LightYellow
    # _status 列が存在し、値が 'updated' または 'added' の場合に色を付ける
    if '_status' in row and row['_status'] in ['updated', 'added']:
        return [f'background-color: {color}'] * len(row)
    return [''] * len(row)  # それ以外はデフォルト

# --- 認証関数 ---


def check_password():
    """パスワード入力を要求し、認証状態を管理する"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.header("パスワード認証")
        password_placeholder = st.empty()
        password = password_placeholder.text_input(
            "パスワードを入力してください:", type="password", key="password_input")

        if st.button("ログイン", key="login_button"):
            if password == CORRECT_PASSWORD:
                st.session_state["authenticated"] = True
                password_placeholder.empty()  # 入力フィールドをクリア
                st.rerun()  # 認証成功後に再実行してメインアプリを表示
            else:
                st.error("パスワードが間違っています。")
        st.stop()  # 認証されるまでここで処理を停止

# --- メインアプリケーション関数 ---


def main_app():
    """メインのStreamlitアプリケーションロジック"""
    st.title("i-Reporter社員マスター取込みツール")

    HIDE_ST_STYLE = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
                    }
                    .appview-container .main .block-container{
                                padding-top: 1rem;
                                padding-right: 3rem;
                                padding-left: 3rem;
                                padding-bottom: 1rem;
                            }
                            .reportview-container {
                                padding-top: 0rem;
                                padding-right: 3rem;
                                padding-left: 3rem;
                                padding-bottom: 0rem;
                            }
                            header[data-testid="stHeader"] {
                                z-index: -1;
                            }
                            div[data-testid="stToolbar"] {
                            z-index: 100;
                            }
                            div[data-testid="stDecoration"] {
                            z-index: 100;
                            }
                    .block-container {
                            padding-top: 0rem !important;
                            padding-bottom: 0rem !important;
                            }
                    </style>
                    </style>
    """
    st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

    # セッションステートの初期化
    if 'processed_df' not in st.session_state:
        st.session_state['processed_df'] = None
    if 'last_error' not in st.session_state:
        st.session_state['last_error'] = None

    # タブの作成
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "内線電話帳取込", "所属修正", "表示順修正", "社員情報追加", "使い方"
    ])

    # --- タブ1: 内線電話帳取込 ---
    with tab1:
        st.header("内線電話帳取込")

        if st.button("取込開始"):
            with st.spinner("処理を実行中..."):
                processed_df, error_msg = process_phonebook_data(
                    INPUT_XLS_FILE)
                # ★★★ 取込時には _status 列を削除（または初期化）★★★
                if processed_df is not None and '_status' in processed_df.columns:
                    processed_df = processed_df.drop(columns=['_status'])
                st.session_state['processed_df'] = processed_df
                st.session_state['last_error'] = error_msg
                # 成功時はエラーメッセージをクリア
                if processed_df is not None:
                    st.session_state['last_error'] = None

        # エラーがあれば表示
        if st.session_state['last_error']:
            st.error(st.session_state['last_error'])

        # データフレームがあれば表示
        if st.session_state['processed_df'] is not None:
            st.success("データが読み込まれました。（「社員情報追加」タブで追加/更新された情報は、ボタン押下後にここに反映されます）")
            df_to_display = st.session_state['processed_df'].copy()
            df_to_display.sort_values(by=['表示順', '所属コード', 'No'], ascending=[
                                      True, True, True], inplace=True)  # 表示順でソート
            df_to_display.reset_index(drop=True, inplace=True)
            df_to_display.insert(
                0, 'カウント', df_to_display.index + 1)  # カウント列を追加
            in_df = df_to_display

            # ★★★ スタイルを適用して表示 ★★★
            st.dataframe(
                df_to_display.style.apply(highlight_updated_added, axis=1),
                column_config={
                    "カウント": st.column_config.NumberColumn(format="%d"),
                    "No": None,  # ★★★ "No"列を非表示 ★★★
                    "所属コード": st.column_config.NumberColumn(format="%d"),
                    "表示順": st.column_config.NumberColumn(format="%d"),
                    "_status": None  # _status 列を非表示にする
                },
                hide_index=True
            )
            if '_status' in in_df.columns:
                in_df = in_df.drop(columns=['_status'])

            # 取り込み用にデータを整える
            in_df = in_df[["カウント", "氏名", "役職", "表示順", "所属コード"]]
            in_df["役職"] = ""
            # 取込用の前２列を追加
            in_df.insert(0, 'アクション区分', 'M')
            in_df.insert(0, 'H', 'R')
            in_df.columns = ['0', '1', '2', '3', '4', '5', '6']

            sql = f"select record_key,value,group_id,display_number,field0001 from view_mst_custom_record where master_id = 7"
            out_df = ireporter_data_get(sql)
            out_df.insert(0, 'アクション区分', 'D')
            out_df.insert(0, 'H', 'R')
            out_df.columns = ['0', '1', '2', '3', '4', '5', '6']

            # ヘッダー部のdfを作成
            head = [["H", "アクション区分", "マスターキー", "マスター名称", "マスター種別", "フィールド型配列", "フィールド名称配列", "画像フィールド名称配列", "本体保存可否", "ダウンロード区分", "保持期間", "有効期限", "表示順", "備考", "レコードキーヘッダ名称", "レコーバリューヘッダ名称", "権限グループ", "ラベルモード", "ラベル", "帳票定義ＩＤ", "入力帳票ＩＤ"],
                    ["M", "M", "M_EMPLOYEE", "社員マスタ", "0", "text;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;",
                     "所属コード;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;", ";;;;", "1", "0", "0", "", "9000", "社員を管理するマスタです", "番号", "社員名", "4;5;6;9;11", "", "共通マスタ"],
                    ["H", "アクション区分", "レコードキー", "バリュー", "権限グループ", "表示順", "F001", "F002", "F003", "F004", "F005", "F006", "F007", "F008", "F009", "F010", "F011", "F012", "F013", "F014", "F015", "F016", "F017", "F018", "F019", "F020", "F021", "F022", "F023", "F024", "F025", "F026", "F027", "F028", "F029", "F030", "F031", "F032", "F033", "F034", "F035", "F036", "F037", "F038", "F039", "F040", "F041", "F042", "F043", "F044", "F045", "F046", "F047", "F048", "F049", "F050", "F051", "F052", "F053", "F054", "F055", "F056", "F057", "F058", "F059", "F060", "F061", "F062", "F063", "F064", "F065", "F066", "F067", "F068", "F069", "F070", "F071", "F072", "F073", "F074", "F075", "F076", "F077", "F078", "F079", "F080", "F081", "F082", "F083", "F084", "F085", "F086", "F087", "F088", "F089", "F090", "F091", "F092", "F093", "F094", "F095", "F096", "F097", "F098", "F099", "F100", "I001", "I002", "I003", "I004", "I005"]]
            dfh = pd.DataFrame(head)
            dfh.columns = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55',
                           '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110']

            # ヘッダー部と結合
            upload_df = pd.concat([dfh, out_df, in_df],
                                  axis=0, ignore_index=True)

            st.markdown("""注意：内線電話一覧表に載っていない社員を取込む場合は、  
                        「カスタムマスターcsv作成」ボタンを押下する前に、**[社員情報追加]画面から取込データを更新**してください""")

            if st.button("カスタムマスターcsv作成", key="update_csv"):
                df_csv_cnv(upload_df)
                st.success("カスタムマスター更新用csvを作成しました")

        elif not st.session_state['last_error']:
            st.info("「取込開始」ボタンを押してデータを読み込んでください。")

    # --- タブ2: 所属修正 ---
    with tab2:
        st.header("所属コード修正")
        st.write("所属名と所属コードの対応を編集します。")

        try:
            # 現在のマッピングデータを読み込み
            shozoku_df = load_shozoku_map_from_db()
            shozoku_df_sorted = shozoku_df.sort_values(
                by='code').reset_index(drop=True)

            # データエディタで編集
            edited_shozoku_df = st.data_editor(
                shozoku_df_sorted,
                num_rows="dynamic",
                column_config={
                    "shozoku": st.column_config.TextColumn("所属名", required=True),
                    "code": st.column_config.NumberColumn("所属コード", required=True, format="%d")
                },
                key="shozoku_editor",
                hide_index=True
            )

            if st.button("所属コードを更新", key="update_shozoku"):
                try:
                    # バリデーション
                    if edited_shozoku_df['shozoku'].isnull().any() or edited_shozoku_df['code'].isnull().any():
                        st.error("エラー: 所属名または所属コードが空欄の行があります。")
                    elif edited_shozoku_df['shozoku'].astype(str).str.strip().eq('').any():
                        st.error("エラー: 所属名が空欄の行があります。")
                    elif edited_shozoku_df['shozoku'].duplicated().any():
                        st.error("エラー: 所属名が重複しています。")
                    elif edited_shozoku_df['code'].duplicated().any():
                        st.error("エラー: 所属コードが重複しています。")
                    else:
                        update_shozoku_map_in_db(edited_shozoku_df)
                        st.success("所属コードマッピングを更新しました。")
                        st.rerun()
                except Exception as e:
                    st.error(f"データベースの更新中にエラーが発生しました: {e}")
                    print(traceback.format_exc())

        except Exception as e:
            st.error(f"所属コードデータの読み込みまたは表示中にエラーが発生しました: {e}")
            print(traceback.format_exc())

    # --- タブ3: 表示順修正 ---
    with tab3:
        st.header("表示順修正")
        st.write("役職名と表示順の対応を編集します。")

        try:
            # 現在のマッピングデータを読み込み
            hyouji_jun_df = load_hyouji_jun_map_from_db()
            hyouji_jun_df_sorted = hyouji_jun_df.sort_values(
                by='jun').reset_index(drop=True)

            # データエディタで編集
            edited_hyouji_jun_df = st.data_editor(
                hyouji_jun_df_sorted,
                num_rows="dynamic",
                column_config={
                    "yakushoku": st.column_config.TextColumn("役職名", required=True),
                    "jun": st.column_config.NumberColumn("表示順", required=True, format="%d")
                },
                key="hyouji_jun_editor",
                hide_index=True
            )

            if st.button("表示順を更新", key="update_hyouji_jun"):
                try:
                    # バリデーション
                    if edited_hyouji_jun_df['yakushoku'].isnull().any() or edited_hyouji_jun_df['jun'].isnull().any():
                        st.error("エラー: 役職名または表示順が空欄の行があります。")
                    elif edited_hyouji_jun_df['yakushoku'].astype(str).str.strip().eq('').any():
                        st.error("エラー: 役職名が空欄の行があります。")
                    elif edited_hyouji_jun_df['yakushoku'].duplicated().any():
                        st.error("エラー: 役職名が重複しています。")
                    elif edited_hyouji_jun_df['jun'].duplicated().any():
                        st.error("エラー: 表示順が重複しています。")
                    else:
                        update_hyouji_jun_map_in_db(edited_hyouji_jun_df)
                        st.success("表示順マッピングを更新しました。")
                        st.rerun()
                except Exception as e:
                    st.error(f"データベースの更新中にエラーが発生しました: {e}")
                    print(traceback.format_exc())

        except Exception as e:
            st.error(f"表示順データの読み込みまたは表示中にエラーが発生しました: {e}")
            print(traceback.format_exc())

    # --- タブ4: 社員情報追加 ---
    with tab4:
        st.header("社員情報追加")
        st.write("内線電話帳に未掲載の社員情報を管理し、取込データに追加・更新します。")

        try:
            # プルダウン用の選択肢を取得
            shozoku_options = load_shozoku_map_from_db()['shozoku'].tolist()
            yakushoku_options = load_hyouji_jun_map_from_db()[
                'yakushoku'].tolist()

            # 追加社員情報を読み込み
            additional_employees_df = load_additional_employees()
            additional_employees_df_display = additional_employees_df.copy()
            additional_employees_df_display.insert(
                0, 'カウント', range(1, len(additional_employees_df_display) + 1))

            # データエディタで編集
            st.write("追加・編集する社員情報:")
            edited_additional_employees_df_with_count = st.data_editor(
                additional_employees_df_display,
                num_rows="dynamic",
                column_config={
                    "カウント": st.column_config.NumberColumn("カウント", disabled=True, format="%d"),
                    "shozoku": st.column_config.SelectboxColumn(
                        "所属",
                        options=shozoku_options,
                        required=True
                    ),
                    "yakushoku": st.column_config.SelectboxColumn(
                        "役職",
                        options=yakushoku_options,
                        required=True
                    ),
                    "shimei": st.column_config.TextColumn("氏名", required=True)
                },
                key="additional_employees_editor",
                hide_index=True
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("追加社員情報をDBに更新", key="update_additional"):
                    try:
                        edited_additional_employees_df = edited_additional_employees_df_with_count.drop(columns=[
                            'カウント'])

                        # バリデーション
                        if edited_additional_employees_df[['shozoku', 'yakushoku', 'shimei']].isnull().values.any():
                            st.error("エラー: 所属、役職、氏名のいずれかが空欄の行があります。")
                        elif edited_additional_employees_df['shimei'].astype(str).str.strip().eq('').any():
                            st.error("エラー: 氏名が空欄の行があります。")
                        elif edited_additional_employees_df['shimei'].duplicated().any():
                            st.error("エラー: 氏名が重複しています。")
                        else:
                            update_additional_employees(
                                edited_additional_employees_df)
                            st.success("追加社員情報をデータベースに更新しました。")
                            st.rerun()
                    except Exception as e:
                        st.error(f"追加社員情報の更新中にエラーが発生しました: {e}")
                        print(traceback.format_exc())

            with col2:
                if st.button("取込データ更新", key="update_processed"):
                    if st.session_state['processed_df'] is None:
                        st.warning("先に「内線電話帳取込」タブでデータを読み込んでください。")
                    else:
                        try:
                            with st.spinner("追加社員情報で取込データを更新中..."):
                                # 最新の追加社員情報とマッピングをDBから取得
                                current_additional_df = load_additional_employees()
                                if current_additional_df.empty:
                                    st.info("データベースに追加社員情報が登録されていません。")
                                else:
                                    df_shozoku_map = load_shozoku_map_from_db()
                                    SHOZOKU_CODE_MAP = pd.Series(
                                        df_shozoku_map.code.values, index=df_shozoku_map.shozoku).to_dict()
                                    df_hyouji_jun_map = load_hyouji_jun_map_from_db()
                                    HYOUJI_JUN_MAP = pd.Series(
                                        df_hyouji_jun_map.jun.values, index=df_hyouji_jun_map.yakushoku).to_dict()

                                    processed_df_copy = st.session_state['processed_df'].copy(
                                    )
                                    # 既存の _status 列があれば削除して初期化
                                    if '_status' in processed_df_copy.columns:
                                        processed_df_copy = processed_df_copy.drop(
                                            columns=['_status'])
                                    # 新しい _status 列を追加
                                    processed_df_copy['_status'] = ''

                                    if 'カウント' in processed_df_copy.columns:
                                        processed_df_copy = processed_df_copy.drop(columns=[
                                            'カウント'])

                                    new_rows_list = []
                                    updated_count = 0
                                    added_count = 0

                                    for _, add_row in current_additional_df.iterrows():
                                        shozoku = add_row['shozoku']
                                        yakushoku = add_row['yakushoku']
                                        shimei = add_row['shimei']

                                        # 所属コードと表示順を計算
                                        shozoku_code = SHOZOKU_CODE_MAP.get(
                                            shozoku, DEFAULT_SHOZOKU_CODE)
                                        yakushoku_for_map = yakushoku.strip() if pd.notna(yakushoku) else ''
                                        if yakushoku_for_map == '' or yakushoku_for_map not in HYOUJI_JUN_MAP:
                                            yakushoku_for_map = EMPTY_YAKUSHOKU_HYOUJI_JUN_KEY
                                        hyouji_jun = HYOUJI_JUN_MAP.get(
                                            yakushoku_for_map, DEFAULT_HYOUJI_JUN)

                                        # 取込データ内に同じ氏名が存在するかチェック
                                        existing_indices = processed_df_copy.index[processed_df_copy['氏名'] == shimei].tolist(
                                        )

                                        if existing_indices:
                                            # --- 既存データの更新 ---
                                            idx = existing_indices[0]
                                            processed_df_copy.loc[idx,
                                                                  '所属'] = shozoku
                                            processed_df_copy.loc[idx, '役職'] = yakushoku if pd.notna(
                                                yakushoku) else ''
                                            processed_df_copy.loc[idx, '所属コード'] = int(
                                                shozoku_code)
                                            processed_df_copy.loc[idx, '表示順'] = int(
                                                hyouji_jun)
                                            # ★★★ ステータスを updated に設定 ★★★
                                            processed_df_copy.loc[idx,
                                                                  '_status'] = 'updated'
                                            updated_count += 1
                                            print(
                                                f"情報: '{shimei}' の情報を更新しました。")
                                        else:
                                            # --- 新規データの追加準備 ---
                                            valid_nos = processed_df_copy[processed_df_copy['所属']
                                                                          == shozoku]['No']
                                            max_no_in_shozoku = valid_nos.max() if not valid_nos.empty else 0
                                            next_no = int(
                                                max_no_in_shozoku + 1)

                                            new_rows_list.append({
                                                "所属": shozoku,
                                                "役職": yakushoku if pd.notna(yakushoku) else '',
                                                "No": next_no,
                                                "氏名": shimei,
                                                "所属コード": int(shozoku_code),
                                                "表示順": int(hyouji_jun),
                                                "_status": 'added'  # ★★★ ステータスを added に設定 ★★★
                                            })
                                            added_count += 1
                                            print(f"情報: '{shimei}' を新規追加します。")

                                    # 新規追加行があれば結合
                                    if new_rows_list:
                                        df_new_rows = pd.DataFrame(
                                            new_rows_list)
                                        # データ型を合わせる
                                        df_new_rows['No'] = df_new_rows['No'].astype(
                                            int)
                                        df_new_rows['所属コード'] = df_new_rows['所属コード'].astype(
                                            int)
                                        df_new_rows['表示順'] = df_new_rows['表示順'].astype(
                                            int)
                                        processed_df_copy = pd.concat(
                                            [processed_df_copy, df_new_rows], ignore_index=True)

                                    # セッションステートを更新
                                    processed_df_copy.reset_index(
                                        drop=True, inplace=True)
                                    st.session_state['processed_df'] = processed_df_copy
                                    success_message = f"{updated_count}件の情報を更新し、{added_count}件の情報を追加しました。「内線電話帳取込」タブで確認できます。"
                                    st.success(success_message)
                                    print(success_message)
                                    # ★★★ 2秒待機を追加 ★★★
                                    time.sleep(2)
                                    st.rerun()

                        except Exception as e:
                            st.error(f"取込データの更新中にエラーが発生しました: {e}")
                            print(traceback.format_exc())

        except Exception as e:
            st.error(f"追加社員情報の読み込みまたは表示中にエラーが発生しました: {e}")
            print(traceback.format_exc())
    with tab5:

        # マニュアルを開く（今後Streamlitでマニュアルを扱うときの共通処理になる）
        with open(os.getcwd()+r'/static/社員マスター取込みマニュアル.md', 'r', encoding='utf-8') as f:
            # ファイルの内容を読み取る
            text = f.read()
        text = text.replace(r'](i', r'](app/static/i')
        st.markdown(text, unsafe_allow_html=True)


# --- アプリケーション実行 ---
if __name__ == "__main__":
    st.set_page_config(page_title="i-Reporter社員マスター取込みツール",
                       layout="wide")  # 先に config を設定
    check_password()  # 認証チェックを最初に行う
    init_db()  # データベース初期化
    main_app()  # 認証後にメインアプリを実行
