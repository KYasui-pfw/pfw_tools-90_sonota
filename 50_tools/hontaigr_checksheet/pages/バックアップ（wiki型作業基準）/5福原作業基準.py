import streamlit as st
import sqlite3
import datetime
import os
import hashlib

# データベースの初期化


def init_db():
    conn = sqlite3.connect(os.path.dirname(
        os.path.dirname(__file__))+'\\Database\\wiki.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS wiki_pages (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL UNIQUE,
        content TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')

    # 編集履歴を保存するテーブル
    c.execute('''
    CREATE TABLE IF NOT EXISTS edit_history (
        id INTEGER PRIMARY KEY,
        page_id INTEGER,
        content TEXT,
        edited_at TEXT,
        FOREIGN KEY (page_id) REFERENCES wiki_pages (id)
    )
    ''')

    conn.commit()
    return conn

# 認証関数 - シンプルなパスワード認証


def authenticate(password):
    # パスワードは "knitadmin"
    return password == "knitadmin"

# ページの取得


def get_pages(conn):
    c = conn.cursor()
    c.execute("SELECT title FROM wiki_pages")
    return [row[0] for row in c.fetchall()]

# ページの保存


def save_page(conn, title, content):
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()

    # ページが存在するか確認
    c.execute("SELECT id, content FROM wiki_pages WHERE title = ?", (title,))
    result = c.fetchone()

    if result:
        page_id, old_content = result
        # 既存ページの更新
        c.execute("UPDATE wiki_pages SET content = ?, updated_at = ? WHERE id = ?",
                  (content, now, page_id))

        # 編集履歴を保存
        c.execute("INSERT INTO edit_history (page_id, content, edited_at) VALUES (?, ?, ?)",
                  (page_id, old_content, now))
    else:
        # 新規ページ作成
        c.execute("INSERT INTO wiki_pages (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                  (title, content, now, now))

    conn.commit()

# ページの削除


def delete_page(conn, title):
    c = conn.cursor()

    # ページIDを取得
    c.execute("SELECT id FROM wiki_pages WHERE title = ?", (title,))
    result = c.fetchone()

    if result:
        page_id = result[0]

        # 編集履歴を削除
        c.execute("DELETE FROM edit_history WHERE page_id = ?", (page_id,))

        # ページを削除
        c.execute("DELETE FROM wiki_pages WHERE id = ?", (page_id,))

        conn.commit()
        return True

    return False

# ページの読み込み


def load_page(conn, title):
    c = conn.cursor()
    c.execute("SELECT content, updated_at FROM wiki_pages WHERE title = ?", (title,))
    result = c.fetchone()
    if result:
        return result
    return None, None

# 編集履歴の取得


def get_history(conn, title):
    c = conn.cursor()
    c.execute("""
    SELECT e.edited_at, e.content 
    FROM edit_history e
    JOIN wiki_pages p ON e.page_id = p.id
    WHERE p.title = ?
    ORDER BY e.edited_at DESC
    """, (title,))
    return c.fetchall()

# 日時の表示を整形する関数


def format_datetime(iso_datetime):
    if iso_datetime:
        # T を取り除いて空白に置換
        return iso_datetime.replace('T', ' ').split('.')[0]
    return ""


# データベース接続
conn = init_db()

# セッション状態の初期化
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'delete_confirm' not in st.session_state:
    st.session_state.delete_confirm = False
if 'page_to_delete' not in st.session_state:
    st.session_state.page_to_delete = None

# Streamlitアプリ
st.title("福原作業基準")

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


# タブを作成
tab1, tab2 = st.tabs(["作業基準選択", "作業基準編集"])

with tab1:
    # 利用可能なページの一覧を取得
    pages = get_pages(conn)

    if not pages:
        st.info("作業基準がまだありません。作業基準編集タブから新規作成してください。")
    else:
        selected_page = st.selectbox("作業基準を選択してください", pages)

        # 選択されたページを表示
        if selected_page:
            content, updated_at = load_page(conn, selected_page)

            # 水平線
            # st.markdown("---")

            # 表示モードはマークダウンとして表示 - 改行を保持するため<pre>タグで囲む
            # st.markdown(f"<pre style='white-space: pre-wrap; word-break: keep-all;'>{content}</pre>", unsafe_allow_html=True)
            st.markdown(content)

            # 水平線
            st.markdown("---")

            # 最終更新日時を表示
            if updated_at:
                st.write(f"最終更新: {format_datetime(updated_at)}")

            #隠しコマンド    
            #uploaded_file = st.file_uploader("ファイルをアップロードしてください")
            #if uploaded_file is not None:
            #    # ファイルを保存する
            #    with open(os.path.join(r"D:\py\hontaigr_checksheet\work", uploaded_file.name), "wb") as f:
            #        f.write(uploaded_file.getbuffer())
            #    st.write(f"ファイルを保存しました: {uploaded_file.name}")


            # 編集履歴の表示
            # with st.expander("編集履歴"):
            #     history = get_history(conn, selected_page)
            #     for date, old_content in history:
            #         st.write(f"編集日: {format_datetime(date)}")
            #         if st.button(f"この版を表示 ({date[:10]})", key=date):
            #             # 履歴表示も改行を保持
            #             st.markdown(f"<pre style='white-space: pre-wrap; word-break: keep-all;'>{old_content}</pre>", unsafe_allow_html=True)

with tab2:
    # 認証部分
    if not st.session_state.authenticated:
        st.subheader("認証(knitadmin)")
        password = st.text_input("パスワード", type="password")

        if st.button("ログイン"):
            if authenticate(password):
                st.session_state.authenticated = True
                st.success("認証に成功しました")
                st.rerun()
            else:
                st.error("パスワードが違います")
    else:
        # 作業基準編集（新規作成と既存編集を統合）
        st.subheader("作業基準編集")

        # 削除確認ダイアログ表示中
        if st.session_state.delete_confirm:
            st.warning(
                f"作業基準「{st.session_state.page_to_delete}」を削除しますか？この操作は取り消せません。")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("はい、削除します"):
                    if delete_page(conn, st.session_state.page_to_delete):
                        st.success(
                            f"作業基準「{st.session_state.page_to_delete}」を削除しました")
                        st.session_state.delete_confirm = False
                        st.session_state.page_to_delete = None
                        st.rerun()
                    else:
                        st.error("削除中にエラーが発生しました")

            with col2:
                if st.button("キャンセル"):
                    st.session_state.delete_confirm = False
                    st.session_state.page_to_delete = None
                    st.rerun()

        else:  # 通常の編集モード
            # まず既存の作業基準を選択するか、新規作成を選択するオプションを表示
            pages = get_pages(conn)
            # 「新規作成」を最後に表示するように順序を変更
            edit_options = pages + ["新規作成"]
            edit_selection = st.selectbox("編集する作業基準を選択、または新規作成", edit_options)

            if edit_selection == "新規作成":
                # 新規作成モード
                new_page_title = st.text_input("作業基準のタイトル")

                if new_page_title:
                    if new_page_title in pages:
                        st.error("このタイトルの作業基準は既に存在します")
                    else:
                        new_content = st.text_area("作業基準内容", "", height=300)

                        if st.button("作業基準を保存"):
                            save_page(conn, new_page_title, new_content)
                            st.success(f"作業基準 '{new_page_title}' を作成しました")
                            st.rerun()
            else:
                # 既存の作業基準編集モード
                content, updated_at = load_page(conn, edit_selection)

                # 編集エリア
                new_content = st.text_area("作業基準内容", content, height=300)

                col1, col2 = st.columns([3, 1])

                with col1:
                    if st.button("変更を保存"):
                        save_page(conn, edit_selection, new_content)
                        st.success(f"作業基準 '{edit_selection}' を更新しました")
                        st.rerun()

                with col2:
                    # 削除ボタン
                    if st.button("削除", type="secondary"):
                        st.session_state.delete_confirm = True
                        st.session_state.page_to_delete = edit_selection
                        st.rerun()

                # 最終更新日時を表示
                if updated_at:
                    st.write(f"最終更新: {format_datetime(updated_at)}")

        # 水平線を追加
        st.markdown("---")
        
        # ログアウトボタンを画面の最下部に配置
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.rerun()
