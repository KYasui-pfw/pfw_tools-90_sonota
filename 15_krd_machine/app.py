"""
KRD SQLite データ管理画面
6テーブルのCRUD操作を行うStreamlitアプリ

対象テーブル:
    - DATA_ASP2_PUT: ASP2投入データ（伝票情報・工程Ver）
    - MSTR_PROCODESTR: 工程コードマスタ
    - MSTR_METAL: メタルマスタ（メッキ情報）
    - DATA_RES_CAPA: 資源稼働データ（負荷情報）
    - MSTR_RES: 資源マスタ
    - _rBOM_MSTR_RES: rBOM資源マスタ（M0430から取得）

起動方法:
    streamlit run app.py --server.port 8509
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timezone, timedelta

# ========== 設定 ==========

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'krd_machine.db')

# 対象テーブル定義
TABLES = {
    'DATA_ASP2_PUT': {
        'name': 'ASP2投入データ',
        'description': '伝票情報・工程Ver（SLIP_NO, VERSIONのみ編集可）',
        'key_columns': ['SLIP_NO'],
        'edit_columns': ['SLIP_NO', 'VERSION'],  # 編集対象カラム
        'simple_mode': True,  # 簡易編集モード
    },
    'MSTR_PROCODESTR': {
        'name': '工程コードマスタ',
        'description': '工程コード→加工部番',
        'key_columns': ['FINAL_ITEM_CODE', 'VERSION'],
    },
    'MSTR_METAL': {
        'name': 'メタルマスタ',
        'description': '加工部番→メッキ情報',
        'key_columns': ['FIN_CODE'],
    },
    'DATA_RES_CAPA': {
        'name': '資源稼働データ',
        'description': '負荷情報',
        'key_columns': ['FINAL_ITEM_CODE', 'PROCESS_ORDER', 'VERSION'],
    },
    'MSTR_RES': {
        'name': '資源マスタ',
        'description': '資源情報（KRD MySQL）',
        'key_columns': ['NO', 'CODE'],
    },
    '_rBOM_MSTR_RES': {
        'name': 'rBOM資源マスタ',
        'description': '資源情報（rBOM M0430から取得）',
        'key_columns': ['NO', 'CODE'],
    },
    '_rBOM_DATA_RES_CAPA': {
        'name': 'rBOM資源稼働データ',
        'description': '資源稼働情報（rBOM M0840から取得）',
        'key_columns': ['FINAL_ITEM_CODE', 'PROCESS_ORDER', 'VERSION'],
    },
}

# ========== カスタムCSS ==========

CUSTOM_CSS = """
<style>
    /* ヘッダー部分の余白を削減 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* タイトル上部の余白削減 */
    h1 {
        margin-top: 0rem;
        padding-top: 0rem;
    }
    /* Streamlitのデフォルトヘッダーを非表示 */
    header[data-testid="stHeader"] {
        display: none;
    }
    /* メインメニューを非表示 */
    #MainMenu {
        display: none;
    }
    /* フッターを非表示 */
    footer {
        display: none;
    }
</style>
"""

# ========== DB操作関数 ==========

def get_connection():
    """SQLite接続を取得"""
    return sqlite3.connect(SQLITE_DB_PATH)

def get_table_data(table_name, limit=1000, offset=0, search_column=None, search_value=None):
    """テーブルデータを取得"""
    conn = get_connection()

    if search_column and search_value:
        query = f"SELECT rowid, * FROM {table_name} WHERE {search_column} LIKE ? LIMIT ? OFFSET ?"
        df = pd.read_sql(query, conn, params=[f'%{search_value}%', limit, offset])
    else:
        query = f"SELECT rowid, * FROM {table_name} LIMIT ? OFFSET ?"
        df = pd.read_sql(query, conn, params=[limit, offset])

    conn.close()
    return df

def get_table_count(table_name, search_column=None, search_value=None):
    """テーブルの件数を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if search_column and search_value:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {search_column} LIKE ?", [f'%{search_value}%'])
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")

        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        # テーブルが存在しない場合
        count = -1
    finally:
        conn.close()
    return count

def get_table_columns(table_name):
    """テーブルのカラム情報を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    return columns

def save_changes(table_name, original_df, edited_df):
    """data_editorの変更をDBに保存"""
    conn = get_connection()
    cursor = conn.cursor()

    results = {'inserted': 0, 'updated': 0, 'deleted': 0, 'errors': []}

    try:
        # 元のrowidセット
        original_rowids = set(original_df['rowid'].tolist())
        edited_rowids = set(edited_df['rowid'].dropna().astype(int).tolist())

        # カラム名（rowid以外）
        columns = [col for col in original_df.columns if col != 'rowid']

        # 削除: 元にあって編集後にない行
        deleted_rowids = original_rowids - edited_rowids
        for rowid in deleted_rowids:
            try:
                cursor.execute(f"DELETE FROM {table_name} WHERE rowid = ?", [rowid])
                results['deleted'] += 1
            except Exception as e:
                results['errors'].append(f"削除エラー (rowid={rowid}): {e}")

        # 更新と追加
        for idx, row in edited_df.iterrows():
            rowid = row.get('rowid')

            # データ準備（rowid以外）
            data = {col: (None if pd.isna(row[col]) else row[col]) for col in columns}

            if pd.isna(rowid):
                # 新規追加（rowidがNaN）
                cols = ', '.join(columns)
                placeholders = ', '.join(['?' for _ in columns])
                values = [data[col] for col in columns]
                try:
                    cursor.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", values)
                    results['inserted'] += 1
                except Exception as e:
                    results['errors'].append(f"追加エラー: {e}")
            else:
                # 既存行の更新チェック
                rowid = int(rowid)
                if rowid in original_rowids:
                    # 元の行と比較
                    orig_row = original_df[original_df['rowid'] == rowid].iloc[0]
                    changed = False
                    for col in columns:
                        orig_val = orig_row[col]
                        new_val = row[col]
                        # NaN同士は同じとみなす
                        if pd.isna(orig_val) and pd.isna(new_val):
                            continue
                        if orig_val != new_val:
                            changed = True
                            break

                    if changed:
                        set_clause = ', '.join([f"{col} = ?" for col in columns])
                        values = [data[col] for col in columns] + [rowid]
                        try:
                            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE rowid = ?", values)
                            results['updated'] += 1
                        except Exception as e:
                            results['errors'].append(f"更新エラー (rowid={rowid}): {e}")

        conn.commit()
    except Exception as e:
        results['errors'].append(f"保存エラー: {e}")
    finally:
        conn.close()

    return results

# ========== UI関数 ==========

def show_simple_editor(table_name, table_info):
    """DATA_ASP2_PUT専用の簡易編集画面（SLIP_NO, VERSIONのみ）"""
    st.caption(f"{table_info['name']} ({table_name}) - {table_info['description']}")

    # 検索・ページネーション（1行にまとめる）
    page_size = 100
    search_value = st.session_state.get(f"search_val_{table_name}", "")
    total_count = get_table_count(
        table_name,
        'SLIP_NO' if search_value else None,
        search_value if search_value else None
    )
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
    with col1:
        search_value = st.text_input("SLIP_NO検索", key=f"search_val_{table_name}", placeholder="F000...", label_visibility="collapsed")
    with col2:
        page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1, key=f"page_{table_name}", label_visibility="collapsed")
    with col3:
        st.write(f"{page}/{total_pages}頁")
    with col4:
        st.write(f"全{total_count:,}件")

    # データ取得（SLIP_NO, VERSIONのみ表示）
    conn = get_connection()
    offset = (page - 1) * page_size
    if search_value:
        query = f"SELECT rowid, SLIP_NO, VERSION FROM {table_name} WHERE SLIP_NO LIKE ? ORDER BY SLIP_NO DESC LIMIT ? OFFSET ?"
        df = pd.read_sql(query, conn, params=[f'%{search_value}%', page_size, offset])
    else:
        query = f"SELECT rowid, SLIP_NO, VERSION FROM {table_name} ORDER BY SLIP_NO DESC LIMIT ? OFFSET ?"
        df = pd.read_sql(query, conn, params=[page_size, offset])
    conn.close()

    # セッションに元データを保存
    session_key = f"original_df_{table_name}_{page}_{search_value}"
    if session_key not in st.session_state or st.session_state.get(f"reload_{table_name}", False):
        st.session_state[session_key] = df.copy()
        st.session_state[f"reload_{table_name}"] = False

    original_df = st.session_state[session_key]

    # 操作説明
    st.caption("セルをダブルクリックで編集 / 下部「+」で行追加 / 左端チェック→Deleteで削除")

    # data_editor（SLIP_NO, VERSIONのみ編集可能）
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=500,
        key=f"editor_{table_name}_{page}_{search_value}",
        disabled=['rowid'],
        column_config={
            'rowid': st.column_config.NumberColumn('rowid', help='システム内部ID', disabled=True),
            'SLIP_NO': st.column_config.TextColumn('SLIP_NO', help='伝票No（ユニーク）', required=True),
            'VERSION': st.column_config.NumberColumn('VERSION', help='工程Ver', default=1),
        },
    )

    # 保存ボタン
    col1, col2, col3 = st.columns([1, 1, 6])
    with col1:
        if st.button("💾 保存", type="primary", key=f"save_{table_name}"):
            results = save_simple_changes(table_name, original_df, edited_df)

            if results['errors']:
                for err in results['errors']:
                    st.error(err)

            msg_parts = []
            if results['inserted'] > 0:
                msg_parts.append(f"追加: {results['inserted']}件")
            if results['updated'] > 0:
                msg_parts.append(f"更新: {results['updated']}件")
            if results['deleted'] > 0:
                msg_parts.append(f"削除: {results['deleted']}件")

            if msg_parts:
                st.success("保存完了: " + ", ".join(msg_parts))
                st.session_state[f"reload_{table_name}"] = True
                st.rerun()
            elif not results['errors']:
                st.info("変更はありませんでした")

    with col2:
        if st.button("🔄 リロード", key=f"reload_btn_{table_name}"):
            st.session_state[f"reload_{table_name}"] = True
            st.rerun()


def save_simple_changes(table_name, original_df, edited_df):
    """DATA_ASP2_PUT専用の保存処理（SLIP_NO, VERSIONのみ、他は固定値）"""
    conn = get_connection()
    cursor = conn.cursor()

    results = {'inserted': 0, 'updated': 0, 'deleted': 0, 'errors': []}

    # 固定値（他のカラム用）
    DEFAULT_VALUES = {
        'SETU_F': '1', 'PNAME': '1', 'SEISANJI': '1', 'KUMIKAISHI': '1',
        'IS_DATE': '1', 'PACK_DATE': '1', 'KOSUU': 1, 'KUMI_NO': '1',
        'UNALL_STOCK': '1', 'HAND_STOCK': '1', 'PRE_UNLOAD': '1', 'HD': '1',
        'RES_DATE': '1', 'RES_NUM': 1, 'STATUS': '1', 'SKDK': '1',
        'DEF_DATE': 1, 'KUMI_ITEM': '1', 'MODEL': '1', 'INCH': 1,
        'GUGE': 1, 'CUST_U_NAME': '1', 'FILC': '1', 'CUST_U_CD': '1',
    }

    try:
        original_rowids = set(original_df['rowid'].tolist()) if not original_df.empty else set()
        edited_rowids = set(edited_df['rowid'].dropna().astype(int).tolist()) if not edited_df.empty else set()

        # 削除
        deleted_rowids = original_rowids - edited_rowids
        for rowid in deleted_rowids:
            try:
                cursor.execute(f"DELETE FROM {table_name} WHERE rowid = ?", [rowid])
                results['deleted'] += 1
            except Exception as e:
                results['errors'].append(f"削除エラー (rowid={rowid}): {e}")

        # 更新と追加
        for idx, row in edited_df.iterrows():
            rowid = row.get('rowid')
            slip_no = row.get('SLIP_NO')
            version = row.get('VERSION', 1)

            if pd.isna(slip_no) or str(slip_no).strip() == '':
                continue  # SLIP_NOが空なら無視

            if pd.isna(version):
                version = 1

            if pd.isna(rowid):
                # 新規追加: 重複チェック
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE SLIP_NO = ?", [slip_no])
                if cursor.fetchone()[0] > 0:
                    results['errors'].append(f"追加エラー: SLIP_NO '{slip_no}' は既に存在します")
                    continue

                # INSERT（全カラム）
                columns = ['SLIP_NO', 'VERSION'] + list(DEFAULT_VALUES.keys())
                values = [slip_no, int(version)] + list(DEFAULT_VALUES.values())
                placeholders = ', '.join(['?' for _ in columns])
                cols_str = ', '.join(columns)
                try:
                    cursor.execute(f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})", values)
                    results['inserted'] += 1
                except Exception as e:
                    results['errors'].append(f"追加エラー: {e}")
            else:
                # 更新: 変更があるかチェック
                rowid = int(rowid)
                if rowid in original_rowids:
                    orig_row = original_df[original_df['rowid'] == rowid].iloc[0]
                    if orig_row['SLIP_NO'] != slip_no or orig_row['VERSION'] != version:
                        # SLIP_NO変更時は重複チェック
                        if orig_row['SLIP_NO'] != slip_no:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE SLIP_NO = ? AND rowid != ?", [slip_no, rowid])
                            if cursor.fetchone()[0] > 0:
                                results['errors'].append(f"更新エラー: SLIP_NO '{slip_no}' は既に存在します")
                                continue

                        try:
                            cursor.execute(f"UPDATE {table_name} SET SLIP_NO = ?, VERSION = ? WHERE rowid = ?",
                                           [slip_no, int(version), rowid])
                            results['updated'] += 1
                        except Exception as e:
                            results['errors'].append(f"更新エラー (rowid={rowid}): {e}")

        conn.commit()
    except Exception as e:
        results['errors'].append(f"保存エラー: {e}")
    finally:
        conn.close()

    return results


def show_table_editor(table_name, table_info):
    """テーブル編集画面（data_editor使用）"""
    st.caption(f"{table_info['name']} ({table_name}) - {table_info['description']}")

    # カラム情報取得
    columns_info = get_table_columns(table_name)

    # テーブルが存在しない場合
    if not columns_info:
        st.warning(f"テーブル '{table_name}' はまだ作成されていません。")
        st.info("同期処理が実行されるとテーブルが作成されます。")
        return

    column_names = [col[1] for col in columns_info]

    # 検索・ページネーション（1行にまとめる）
    page_size = 100
    search_column = st.session_state.get(f"search_col_{table_name}", "")
    search_value = st.session_state.get(f"search_val_{table_name}", "")
    total_count = get_table_count(
        table_name,
        search_column if search_column else None,
        search_value if search_value else None
    )

    # テーブルが存在しない場合（-1が返される）
    if total_count < 0:
        st.warning(f"テーブル '{table_name}' はまだ作成されていません。")
        st.info("同期処理が実行されるとテーブルが作成されます。")
        return

    total_pages = max(1, (total_count + page_size - 1) // page_size)

    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
    with col1:
        search_column = st.selectbox("カラム", [""] + column_names, key=f"search_col_{table_name}", label_visibility="collapsed")
    with col2:
        search_value = st.text_input("検索値", key=f"search_val_{table_name}", placeholder="検索値...", label_visibility="collapsed")
    with col3:
        page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1, key=f"page_{table_name}", label_visibility="collapsed")
    with col4:
        st.write(f"{page}/{total_pages}頁")
    with col5:
        st.write(f"全{total_count:,}件")

    # データ取得
    offset = (page - 1) * page_size
    df = get_table_data(
        table_name,
        limit=page_size,
        offset=offset,
        search_column=search_column if search_column else None,
        search_value=search_value if search_value else None
    )

    if df.empty:
        st.info("データがありません")
        # 空のDataFrameでも追加できるようにする
        df = pd.DataFrame(columns=['rowid'] + column_names)

    # セッションに元データを保存（比較用）
    session_key = f"original_df_{table_name}_{page}"
    if session_key not in st.session_state or st.session_state.get(f"reload_{table_name}", False):
        st.session_state[session_key] = df.copy()
        st.session_state[f"reload_{table_name}"] = False

    original_df = st.session_state[session_key]

    # 操作説明
    st.caption("セルをダブルクリックで編集 / 下部「+」で行追加 / 左端チェック→Deleteで削除")

    # data_editor（編集可能なデータグリッド）
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",  # 行の追加・削除を許可
        use_container_width=True,
        height=500,
        key=f"editor_{table_name}_{page}",
        disabled=['rowid'],  # rowidは編集不可
        column_config={
            'rowid': st.column_config.NumberColumn(
                'rowid',
                help='システム内部ID（編集不可）',
                disabled=True,
            ),
        },
    )

    # 保存ボタン
    col1, col2, col3 = st.columns([1, 1, 6])
    with col1:
        if st.button("💾 保存", type="primary", key=f"save_{table_name}"):
            results = save_changes(table_name, original_df, edited_df)

            if results['errors']:
                for err in results['errors']:
                    st.error(err)

            msg_parts = []
            if results['inserted'] > 0:
                msg_parts.append(f"追加: {results['inserted']}件")
            if results['updated'] > 0:
                msg_parts.append(f"更新: {results['updated']}件")
            if results['deleted'] > 0:
                msg_parts.append(f"削除: {results['deleted']}件")

            if msg_parts:
                st.success("保存完了: " + ", ".join(msg_parts))
                # 元データを更新
                st.session_state[f"reload_{table_name}"] = True
                st.rerun()
            elif not results['errors']:
                st.info("変更はありませんでした")

    with col2:
        if st.button("🔄 リロード", key=f"reload_btn_{table_name}"):
            st.session_state[f"reload_{table_name}"] = True
            st.rerun()

def show_overview():
    """概要画面"""
    JST = timezone(timedelta(hours=9))
    now_jst = datetime.now(JST)

    # DBファイル情報
    if os.path.exists(SQLITE_DB_PATH):
        file_stat = os.stat(SQLITE_DB_PATH)
        file_size_mb = file_stat.st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(file_stat.st_mtime)
        st.caption(f"DB: {SQLITE_DB_PATH} | {file_size_mb:.2f}MB | 更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S')} | 現在: {now_jst.strftime('%Y-%m-%d %H:%M:%S')}")

    # 各テーブルの件数
    data = []
    for table_name, table_info in TABLES.items():
        try:
            count = get_table_count(table_name)
            data.append({
                'テーブル名': table_name,
                '論理名': table_info['name'],
                '説明': table_info['description'],
                '件数': f"{count:,}",
                'キーカラム': ', '.join(table_info['key_columns']),
            })
        except Exception as e:
            data.append({
                'テーブル名': table_name,
                '論理名': table_info['name'],
                '説明': table_info['description'],
                '件数': 'エラー',
                'キーカラム': ', '.join(table_info['key_columns']),
            })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ========== メイン ==========

def main():
    st.set_page_config(
        page_title="KRD データ管理",
        page_icon="🗃️",
        layout="wide",
    )

    # カスタムCSSを適用
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("KRD データ管理")

    # サイドバー
    st.sidebar.title("メニュー")

    menu_options = ["概要"] + list(TABLES.keys())
    selected = st.sidebar.radio("選択", menu_options, format_func=lambda x: TABLES[x]['name'] if x in TABLES else x)

    st.sidebar.divider()
    st.sidebar.caption("2025年12月以降は手動運用")

    # メインコンテンツ
    if selected == "概要":
        show_overview()
    elif selected in TABLES:
        table_info = TABLES[selected]
        if table_info.get('simple_mode'):
            show_simple_editor(selected, table_info)
        else:
            show_table_editor(selected, table_info)

if __name__ == "__main__":
    main()
