import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import uuid
import time
import pytz

st.set_page_config(
    page_title="お知らせ管理画面",
    page_icon="📢"
)

# ヘッダー部を完全に削除
st.markdown("""
<style>
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .main .block-container {
        max-width: none;
    }
    /* Streamlitのヘッダーを完全に非表示 */
    header[data-testid="stHeader"] {
        display: none;
    }
    /* メニューボタンを非表示 */
    .css-1rs6os.edgvbvh3 {
        display: none;
    }
    /* Deploy等のボタンを非表示 */
    .css-14xtw13.e8zbici0 {
        display: none;
    }
    /* オレンジ色の線を非表示 */
    .css-1d391kg {
        display: none;
    }
    /* タイトルの余白調整 */
    h1 {
        padding-top: 0rem;
        margin-top: 0rem;
    }
</style>
""", unsafe_allow_html=True)

DATABASE_PATH = "notices.db"

def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # お知らせテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id TEXT PRIMARY KEY,
            department TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            emoji TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL
        )
    ''')
    
    # ユーザーテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初期管理者アカウントの作成
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('administrator',))
    if cursor.fetchone()[0] == 0:
        jst = pytz.timezone('Asia/Tokyo')
        created_at = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO users (id, username, password, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), 'administrator', 'administrator', 1, created_at))
    
    conn.commit()
    conn.close()

def auto_delete_expired_notices():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    thirty_days_ago = datetime.now() - timedelta(days=30)
    # 日本時間で削除時刻を設定
    jst = pytz.timezone('Asia/Tokyo')
    deleted_at = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE notices 
        SET deleted_at = ? 
        WHERE end_date < ? AND deleted_at IS NULL
    ''', (deleted_at, thirty_days_ago.date()))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def get_all_notices():
    conn = sqlite3.connect(DATABASE_PATH)
    df = pd.read_sql_query('SELECT * FROM notices WHERE deleted_at IS NULL ORDER BY start_date DESC', conn)
    conn.close()
    return df

def insert_notice(department, start_date, end_date, title, content, emoji):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    notice_id = str(uuid.uuid4())
    # 日本時間で作成日時を設定
    jst = pytz.timezone('Asia/Tokyo')
    created_at = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO notices (id, department, start_date, end_date, title, content, emoji, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (notice_id, department, start_date, end_date, title, content, emoji, created_at))
    conn.commit()
    conn.close()
    return notice_id

def update_notice(notice_id, department, start_date, end_date, title, content, emoji):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE notices 
        SET department=?, start_date=?, end_date=?, title=?, content=?, emoji=?
        WHERE id=?
    ''', (department, start_date, end_date, title, content, emoji, notice_id))
    conn.commit()
    conn.close()

def delete_notice(notice_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # 日本時間で削除時刻を設定
    jst = pytz.timezone('Asia/Tokyo')
    deleted_at = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE notices SET deleted_at = ? WHERE id=?', (deleted_at, notice_id))
    conn.commit()
    conn.close()

def get_notice_by_id(notice_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notices WHERE id=? AND deleted_at IS NULL', (notice_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def authenticate_user(username, password):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role FROM users WHERE username=? AND password=?', (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_users():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC')
    result = cursor.fetchall()
    conn.close()
    return result

def create_user(username, password, role):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    # 日本時間で作成日時を設定
    jst = pytz.timezone('Asia/Tokyo')
    created_at = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO users (id, username, password, role, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, password, role, created_at))
    conn.commit()
    conn.close()
    return user_id

def update_user_password(user_id, new_password):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password=? WHERE id=?', (new_password, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()

@st.dialog("ユーザー削除確認")
def show_delete_user_dialog(user_id, username):
    """ユーザー削除の確認ダイアログ"""
    st.warning(f"ユーザー「{username}」を削除しますか？")
    st.write("この操作は取り消せません。")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("削除実行", type="primary", use_container_width=True):
            delete_user(user_id)
            st.success(f"ユーザー「{username}」を削除しました")
            st.rerun()
    with col2:
        if st.button("キャンセル", type="secondary", use_container_width=True):
            st.rerun()

def validate_input(department, start_date, end_date, title, content):
    errors = []
    
    if not department or len(department) > 10:
        errors.append("部門は1文字以上10文字以下で入力してください。")
    
    if end_date > datetime.now().date() + timedelta(days=60):
        errors.append("お知らせ終了日は本日から2カ月以内で設定してください。")
    
    if end_date < start_date:
        errors.append("終了日は開始日以降の日付を選択してください。")
    
    if not title or len(title) > 30:
        errors.append("タイトルは1文字以上30文字以下で入力してください。")
    
    if not content or len(content) > 1200:
        errors.append("本文は1文字以上1200文字以下で入力してください。")
    
    return errors

def login_page():
    st.title("📢 お知らせ編集アプリ")
    
    with st.form("login_form"):
        username = st.text_input("ユーザーID")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")
        
        if submitted:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1] 
                    st.session_state.role = user[2]
                    st.rerun()
                else:
                    st.error("ユーザーIDまたはパスワードが間違っています")
            else:
                st.error("ユーザーIDとパスワードを入力してください")

def main():
    init_database()
    
    # セッション状態の初期化
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'form_counter' not in st.session_state:
        st.session_state.form_counter = 0
    
    # ログインしていない場合はログイン画面を表示
    if not st.session_state.logged_in:
        login_page()
        return
    
    # ログイン後のメイン画面
    deleted_count = auto_delete_expired_notices()
    if deleted_count > 0:
        st.info(f"期限切れのお知らせ {deleted_count} 件を自動削除しました。")
    
    # ヘッダー部分
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📢 お知らせ管理画面")
    with col2:
        if st.button("ログアウト"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["新規作成・編集", "一覧・削除", "マークダウン記法", "管理用"])
    
    with tab1:
        notices_df = get_all_notices()
        edit_mode = False
        selected_notice = None
        
        if not notices_df.empty:
            notice_options = ["新規作成"] + [f"{row['title']} ({row['department']}) - {row['start_date']}" for _, row in notices_df.iterrows()]
            notice_ids = [""] + notices_df['id'].tolist()
            
            selected_option = st.selectbox(
                "編集するお知らせを選択（新規作成の場合は「新規作成」を選択）",
                notice_options
            )
            
            if selected_option != "新規作成":
                selected_index = notice_options.index(selected_option) - 1
                selected_notice_id = notice_ids[selected_index + 1]
                selected_notice = get_notice_by_id(selected_notice_id)
                edit_mode = True
        
        # フォーム外でのリアルタイム入力（プレビュー用）
        default_department = selected_notice[1] if selected_notice else ""
        default_start = datetime.strptime(selected_notice[2], "%Y-%m-%d").date() if selected_notice else datetime.now().date()
        default_end = datetime.strptime(selected_notice[3], "%Y-%m-%d").date() if selected_notice else datetime.now().date() + timedelta(days=7)
        default_title = selected_notice[4] if selected_notice else ""
        default_content = selected_notice[5] if selected_notice else ""
        default_emoji = selected_notice[6] if selected_notice else ""
        
        col1, col2, col3 = st.columns(3)
        with col1:
            department = st.text_input(
                "部門 (最大10文字) *",
                value=default_department,
                max_chars=10,
                help="お知らせを発信する部門名を入力してください",
                key=f"dept_{st.session_state.form_counter}"
            )
        
        with col2:
            # 過去の日付も選択可能
            start_date = st.date_input(
                "お知らせ開始日 *",
                value=default_start,
                help="お知らせの表示開始日を選択してください",
                key=f"start_{st.session_state.form_counter}"
            )
        
        with col3:
            # 編集モードの場合は元の終了日も許可、新規作成の場合は今日+60日まで
            max_end_date = datetime.now().date() + timedelta(days=60)
            min_end_date = start_date
            if edit_mode and selected_notice:
                if default_end > max_end_date:
                    max_end_date = default_end
                if default_end < min_end_date:
                    min_end_date = default_end
            end_date = st.date_input(
                "お知らせ終了日 *",
                value=default_end,
                min_value=min_end_date,
                max_value=max_end_date,
                help="お知らせの表示終了日を選択してください（本日から最大2カ月）",
                key=f"end_{st.session_state.form_counter}"
            )
        
        col_emoji, col_title = st.columns([1, 4])
        
        with col_emoji:
            emoji_options = ["", "📋", "📢", "🔔", "⚠️", "💡", "📝", "🎉", "🚨", "📊", "💼"]
            emoji = st.selectbox(
                "絵文字",
                emoji_options,
                index=emoji_options.index(default_emoji) if default_emoji in emoji_options else 0,
                help="一覧で表示する絵文字を選択してください（空欄も可）",
                key=f"emoji_{st.session_state.form_counter}"
            )
        
        with col_title:
            title = st.text_input(
                "タイトル (最大30文字) *",
                value=default_title,
                max_chars=30,
                help="お知らせのタイトルを入力してください",
                key=f"title_{st.session_state.form_counter}"
            )
        
        content = st.text_area(
            "本文 (最大1200文字・マークダウン対応) *",
            value=default_content,
            max_chars=1200,
            height=200,
            help="お知らせの本文を入力してください。マークダウン記法については「マークダウン記法」タブをご確認ください。",
            key=f"content_{st.session_state.form_counter}"
        )
        
        # プレビューと作成ボタンを横並びに配置
        col_preview, col_button = st.columns([7, 1])
        
        with col_preview:
            # リアルタイムプレビュー機能（常に表示）
            with st.expander("📋 プレビュー", expanded=False):
                if content:
                    formatted_preview = content.replace('\n', '  \n')
                    st.markdown(formatted_preview, unsafe_allow_html=True)
                else:
                    st.write("*本文を入力するとここにプレビューが表示されます*")
        
        with col_button:
            # 作成・更新ボタン
            submitted = st.button(
                "更新" if edit_mode else "作成",
                type="primary",
                key=f"submit_{st.session_state.form_counter}"
            )
        
        if submitted:
                errors = validate_input(department, start_date, end_date, title, content)
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        if edit_mode and selected_notice:
                            update_notice(selected_notice[0], department, start_date, end_date, title, content, emoji)
                            st.success("✅ お知らせを更新しました！")
                            time.sleep(3)
                            st.rerun()
                        else:
                            notice_id = insert_notice(department, start_date, end_date, title, content, emoji)
                            st.success("✅ 新しいお知らせを作成しました！")
                            # フォームカウンターをインクリメントしてフォームをリセット
                            st.session_state.form_counter += 1
                            time.sleep(3)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.write("")
    with tab2:
        
        notices_df = get_all_notices()
        
        if notices_df.empty:
            st.info("📝 登録されているお知らせはありません。")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**登録件数:** {len(notices_df)} 件")
            with col2:
                st.write("※終了日から30日で自動削除されます")
            
            for _, notice in notices_df.iterrows():
                emoji_display = notice.get('emoji', '')
                emoji_prefix = f"{emoji_display} " if emoji_display else ""
                with st.expander(f"{emoji_prefix}{notice['title']} ({notice['department']}) | {notice['start_date']} ～ {notice['end_date']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write("**部門:**", notice['department'])
                        st.write("**期間:**", f"{notice['start_date']} ～ {notice['end_date']}")
                        st.write("**タイトル:**", notice['title'])
                        st.write("**本文:**")
                        # 改行を含むテキストを正しく表示、HTMLタグも有効化
                        formatted_content = notice['content'].replace('\n', '  \n')
                        st.markdown(formatted_content, unsafe_allow_html=True)
                        st.write("**作成日時:**", notice['created_at'])
                    
                    with col2:
                        if st.button(f"🗑️ 削除", key=f"delete_{notice['id']}", type="secondary"):
                            delete_notice(notice['id'])
                            st.success("削除しました")
                            time.sleep(3)
                            st.rerun()
    
    with tab3:
        st.header("📝 マークダウン記法の使い方")
        
        st.subheader("基本的な文字装飾")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**記法**")
            st.code("""**太字**
*斜体*
~~取り消し線~~
`コード`""")
        
        with col2:
            st.write("**表示結果**")
            st.markdown("**太字**")
            st.markdown("*斜体*")
            st.markdown("~~取り消し線~~")
            st.markdown("`コード`")
        
        st.subheader("色付きテキスト（HTML）")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**記法**")
            st.code("""<span style="color:red">赤文字</span>
<span style="color:blue">青文字</span>
<span style="color:green">緑文字</span>
<span style="color:orange">オレンジ文字</span>""")
        
        with col2:
            st.write("**表示結果**")
            st.markdown('<span style="color:red">赤文字</span>', unsafe_allow_html=True)
            st.markdown('<span style="color:blue">青文字</span>', unsafe_allow_html=True)
            st.markdown('<span style="color:green">緑文字</span>', unsafe_allow_html=True)
            st.markdown('<span style="color:orange">オレンジ文字</span>', unsafe_allow_html=True)
        
        st.subheader("リンク")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**記法**")
            st.code("""[リンクテキスト](https://example.com)
[Googleで検索](https://www.google.com)""")
        
        with col2:
            st.write("**表示結果**")
            st.markdown("[リンクテキスト](https://example.com)")
            st.markdown("[Googleで検索](https://www.google.com)")
        
        st.subheader("見出しとリスト")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**記法**")
            st.code("""# 大見出し
## 中見出し
### 小見出し
- リスト項目1
- リスト項目2
1. 番号付きリスト
2. 番号付きリスト""")
        
        with col2:
            st.write("**表示結果**")
            st.markdown("# 大見出し")
            st.markdown("## 中見出し")
            st.markdown("### 小見出し")
            st.markdown("- リスト項目1\n- リスト項目2")
            st.markdown("1. 番号付きリスト\n2. 番号付きリスト")
    
    with tab4:
        st.header("🔧 管理用")
        
        # パスワード変更セクション
        st.subheader("パスワード変更")
        with st.form("change_password_form"):
            new_password = st.text_input("新しいパスワード", type="password")
            confirm_password = st.text_input("新しいパスワード（確認）", type="password")
            change_submitted = st.form_submit_button("パスワード変更")
            
            if change_submitted:
                if new_password and confirm_password:
                    if new_password == confirm_password:
                        if len(new_password) >= 4:
                            update_user_password(st.session_state.user_id, new_password)
                            st.success("パスワードを変更しました。5秒後に自動ログアウトします。")
                            time.sleep(5)
                            for key in list(st.session_state.keys()):
                                del st.session_state[key]
                            st.rerun()
                        else:
                            st.error("パスワードは4文字以上で入力してください")
                    else:
                        st.error("パスワードが一致しません")
                else:
                    st.error("すべての項目を入力してください")
        
        st.write("---")
        
        # 管理者のみアクセス可能なセクション
        if st.session_state.role == 1:
            st.subheader("ユーザー管理 (管理者のみ)")
            
            # ユーザー追加
            st.write("**新規ユーザー追加**")
            with st.form("add_user_form"):
                new_username = st.text_input("ユーザーID")
                initial_password = st.text_input("初期パスワード")
                user_role = st.selectbox("権限レベル", options=[0, 1], format_func=lambda x: "編集者" if x == 0 else "管理者")
                add_user_submitted = st.form_submit_button("ユーザー追加")
                
                if add_user_submitted:
                    if new_username and initial_password:
                        if len(new_username) >= 3 and len(initial_password) >= 4:
                            try:
                                create_user(new_username, initial_password, user_role)
                                st.success(f"ユーザー「{new_username}」を追加しました")
                            except Exception as e:
                                if "UNIQUE constraint failed" in str(e):
                                    st.error("このユーザーIDは既に使用されています")
                                else:
                                    st.error(f"エラーが発生しました: {str(e)}")
                        else:
                            st.error("ユーザーIDは3文字以上、パスワードは4文字以上で入力してください")
                    else:
                        st.error("すべての項目を入力してください")
            
            st.write("---")
            
            # ユーザー一覧
            st.write("**登録ユーザー一覧**")
            users = get_all_users()
            if users:
                for user in users:
                    user_id, username, role, created_at = user
                    role_text = "管理者" if role == 1 else "編集者"
                    
                    col_user, col_delete = st.columns([4, 1])
                    with col_user:
                        st.write(f"・{username} ({role_text}) - 作成日: {created_at}")
                    with col_delete:
                        # 自分自身は削除できない
                        if user_id != st.session_state.user_id:
                            if st.button("削除", key=f"delete_user_{user_id}", type="secondary"):
                                show_delete_user_dialog(user_id, username)
                        else:
                            st.write("")  # 自分自身の場合は空白
            else:
                st.info("登録されているユーザーはありません")

if __name__ == "__main__":
    main()
