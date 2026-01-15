import streamlit as st
from datetime import datetime, timedelta
import db_manager

# データベース初期化
db_manager.init_db()

# アプリのタイトルとスタイル
st.set_page_config(page_title="かんばんボード", layout="wide")
st.markdown("""
<style>
    /* ヘッダーとフッターを非表示 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 上部の余白を削減 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }

    /* タイトルの余白を削減 */
    h1 {
        margin-top: 0;
        padding-top: 0;
    }

    /* メイン背景 */
    .main {
        background-color: #F5FBFF;
        color: #1a1a1a;
    }

    /* サイドバー背景 */
    [data-testid="stSidebar"] {
        background-color: #EBF5FB;
    }

    .stButton > button {
        width: 100%;
    }

    /* カードボタンの基本スタイル */
    .stButton > button[kind="secondary"] {
        text-align: left !important;
        padding: 12px !important;
        white-space: pre-wrap !important;
        font-weight: normal !important;
        min-height: 50px !important;
    }

    /* カラムの基本スタイル */
    [data-testid="column"] {
        border-radius: 10px;
        padding: 10px;
    }

    /* カラム間のギャップを削減 */
    .stHorizontalBlock {
        gap: 0.25rem !important;
    }

    /* タスクカードのスタイル */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }



    /* 各カラムの背景色（nth-childで指定） */
    [data-testid="column"]:nth-child(1) {
        background-color: #FFFDE7; /* 未着手 - 薄い黄色 */
    }

    [data-testid="column"]:nth-child(2) {
        background-color: #FFEBEE; /* 進行中 - 薄い赤色 */
    }

    [data-testid="column"]:nth-child(3) {
        background-color: #E8F5E9; /* 完了 - 薄い緑色 */
    }

    [data-testid="column"]:nth-child(4) {
        background-color: #F5F5F5; /* 保留 - 薄い灰色 */
    }

    /* カラムヘッダー */
    .column-header {
        text-align: center;
        padding: 10px 0;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }

    /* 各ステータス別のヘッダー色 */
    .column-header-misyakusyu {
        color: #F57F17;
        border-bottom: 2px solid #FBC02D;
    }

    .column-header-shinkochu {
        color: #1565C0;
        border-bottom: 2px solid #1976D2;
    }

    .column-header-kanryo {
        color: #2E7D32;
        border-bottom: 2px solid #43A047;
    }

    .column-header-horyu {
        color: #424242;
        border-bottom: 2px solid #757575;
    }
</style>
""", unsafe_allow_html=True)

# アプリのタイトル
st.title("かんばんボード")

# ステータスは固定（保留、未着手、進行中、完了の順）
STATUSES = ["保留", "未着手", "進行中", "完了"]

# タスク詳細を表示するダイアログ（即編集可能）
@st.dialog("タスク詳細・編集")
def show_task_detail(task):
    st.markdown(f"### No.{task['no']}")

    # タスク情報
    st.markdown(f"**ステータス:** {task['status']}")

    if task['created_at']:
        created_time = datetime.fromisoformat(task['created_at']).strftime('%Y/%m/%d %H:%M')
        st.markdown(f"**作成日時:** {created_time}")

    if task['completed_at']:
        completed_time = datetime.fromisoformat(task['completed_at']).strftime('%Y/%m/%d %H:%M')
        st.markdown(f"**完了日時:** {completed_time}")

    st.markdown("---")

    # 編集フォーム（常に表示）
    st.markdown("### タスク内容")
    edit_title = st.text_input("タイトル", value=task['title'], key=f"edit_title_{task['no']}")
    edit_details = st.text_area("詳細", value=task['details'] or "", height=200, key=f"edit_details_{task['no']}")

    # 保存ボタン
    if st.button("💾 保存", key=f"save_task_{task['no']}", type="primary", use_container_width=True):
        db_manager.update_task(task['no'], edit_title, edit_details)
        st.success("タスクを更新しました！")
        st.rerun()

# 完了後1週間経過したタスクを自動削除
deleted_count = db_manager.auto_delete_old_completed_tasks()
if deleted_count > 0:
    st.info(f"完了後1週間経過したタスク {deleted_count} 件を自動削除しました")

# サイドバーで新しい付箋の追加
with st.sidebar:
    st.header("新しいタスクを追加")

    # セッション状態の初期化
    if 'task_title' not in st.session_state:
        st.session_state.task_title = ""
    if 'task_details' not in st.session_state:
        st.session_state.task_details = ""

    note_title = st.text_input("タイトル", value=st.session_state.task_title, key="new_task_title")
    note_details = st.text_area("詳細", value=st.session_state.task_details, height=100, key="new_task_details")
    # 新規タスクは未着手と進行中のみ選択可能
    new_task_statuses = ["未着手", "進行中"]
    status = st.selectbox("ステータス", new_task_statuses, key="new_task_status")

    if st.button("追加", key="add_task"):
        if note_title:
            task_no = db_manager.add_task(note_title, note_details, status)
            # フィールドをリセット
            st.session_state.task_title = ""
            st.session_state.task_details = ""
            st.success(f"タスク No.{task_no} が追加されました！")
            st.rerun()
        else:
            st.warning("タイトルを入力してください")

    # タスク削除セクション
    st.header("タスク削除")
    tasks = db_manager.get_all_tasks()

    if tasks:
        # タスク番号のリストを作成
        task_options = [
            f"No.{task['no']} - {task['title'][:20]}..." if len(task['title']) > 20 else f"No.{task['no']} - {task['title']}"
            for task in tasks
        ]
        selected_task = st.selectbox("削除するタスクを選択", task_options, key="delete_task_select")

        if st.button("削除", key="delete_task"):
            # 選択されたタスク番号を抽出
            selected_no = int(selected_task.split('.')[1].split(' ')[0])
            # タスクを削除（手動削除）
            db_manager.delete_task(selected_no, delete_type='manual')
            st.success(f"タスク No.{selected_no} を削除しました！")
            st.rerun()
    else:
        st.info("削除できるタスクがありません")

# メインコンテンツ: カラムとカードの表示
tasks = db_manager.get_all_tasks()

cols = st.columns(len(STATUSES))

for i, status in enumerate(STATUSES):
    with cols[i]:
        # カラムヘッダー（ステータスに応じた色を適用）
        header_class_map = {
            "未着手": "column-header-misyakusyu",
            "進行中": "column-header-shinkochu",
            "完了": "column-header-kanryo",
            "保留": "column-header-horyu"
        }
        header_class = header_class_map.get(status, "")
        st.markdown(f"<div class='column-header {header_class}'>{status}</div>", unsafe_allow_html=True)

        # このステータスのカード
        status_notes = [task for task in tasks if task["status"] == status]

        if not status_notes:
            # 全てのステータスで「〇〇のタスクはありません」と表示
            st.markdown(f"<div style='text-align: center; color: #666; padding: 20px 0;'>"
                       f"{status}のタスクはありません"
                       f"</div>", unsafe_allow_html=True)

        # カードとアクションボタンを表示
        for note in status_notes:
            # 完了日時を表示（完了ステータスの場合）
            if note['status'] == '完了' and note['completed_at']:
                completed_time = datetime.fromisoformat(note['completed_at']).strftime('%Y/%m/%d %H:%M')
                time_text = f"\n完了: {completed_time}"
            else:
                time_text = ""

            # カード全体をボタンとして表示
            card_text = f"No.{note['no']} - {note['title']}{time_text}"

            # 横並びレイアウト: 左矢印、カード、右矢印
            has_prev = STATUSES.index(status) > 0
            has_next = STATUSES.index(status) < len(STATUSES) - 1

            # コンテナでカード全体を囲む（columnsは使わずボタンを横並びに）
            with st.container():
                # 左矢印
                col1, col2, col3 = st.columns([1, 10, 1])
                with col1:
                    if has_prev:
                        prev_status = STATUSES[STATUSES.index(status) - 1]
                        if st.button("←", key=f"prev_{note['no']}"):
                            db_manager.update_task_status(note['no'], prev_status)
                            st.rerun()

                # カードボタン（中央）
                with col2:
                    if st.button(card_text, key=f"card_{note['no']}", use_container_width=True, type="secondary"):
                        show_task_detail(note)

                # 右矢印
                with col3:
                    if has_next:
                        next_status = STATUSES[STATUSES.index(status) + 1]
                        if st.button("→", key=f"next_{note['no']}"):
                            db_manager.update_task_status(note['no'], next_status)
                            st.rerun()

# 削除済みタスク詳細を表示するダイアログ（グローバルに定義）
@st.dialog("削除済みタスク詳細")
def show_deleted_task_detail(task):
    st.markdown(f"### No.{task['task_no']} - {task['title']}")

    # 削除種類のバッジ
    if task['delete_type'] == 'manual':
        st.markdown("🔴 **手動削除**")
    else:
        st.markdown("🔵 **完了後自動削除**")

    st.markdown(f"**削除時ステータス:** {task['status']}")

    if task['created_at']:
        created_time = datetime.fromisoformat(task['created_at']).strftime('%Y/%m/%d %H:%M')
        st.markdown(f"**作成日時:** {created_time}")

    if task['completed_at']:
        completed_time = datetime.fromisoformat(task['completed_at']).strftime('%Y/%m/%d %H:%M')
        st.markdown(f"**完了日時:** {completed_time}")

    if task['deleted_at']:
        deleted_time = datetime.fromisoformat(task['deleted_at']).strftime('%Y/%m/%d %H:%M')
        st.markdown(f"**削除日時:** {deleted_time}")

    st.markdown("---")
    st.markdown("### 詳細")
    if task['details']:
        st.markdown(task['details'])
    else:
        st.info("詳細情報はありません")

# メモ欄セクション（3分割）
st.markdown("---")

# セッション状態の初期化（DBから読み込み）
if 'board_memo_1' not in st.session_state:
    st.session_state.board_memo_1 = db_manager.get_board_memo(1)
if 'board_memo_2' not in st.session_state:
    st.session_state.board_memo_2 = db_manager.get_board_memo(2)
if 'board_memo_3' not in st.session_state:
    st.session_state.board_memo_3 = db_manager.get_board_memo(3)

memo_cols = st.columns(3)

with memo_cols[0]:
    st.markdown("**メモ1**")
    memo_content_1 = st.text_area(
        "メモ1",
        value=st.session_state.board_memo_1,
        height=200,
        key="memo_input_1",
        placeholder="メモ1",
        label_visibility="collapsed"
    )
    if memo_content_1 != st.session_state.board_memo_1:
        db_manager.update_board_memo(1, memo_content_1)
        st.session_state.board_memo_1 = memo_content_1

with memo_cols[1]:
    st.markdown("**メモ2**")
    memo_content_2 = st.text_area(
        "メモ2",
        value=st.session_state.board_memo_2,
        height=200,
        key="memo_input_2",
        placeholder="メモ2",
        label_visibility="collapsed"
    )
    if memo_content_2 != st.session_state.board_memo_2:
        db_manager.update_board_memo(2, memo_content_2)
        st.session_state.board_memo_2 = memo_content_2

with memo_cols[2]:
    st.markdown("**メモ3**")
    memo_content_3 = st.text_area(
        "メモ3",
        value=st.session_state.board_memo_3,
        height=200,
        key="memo_input_3",
        placeholder="メモ3",
        label_visibility="collapsed"
    )
    if memo_content_3 != st.session_state.board_memo_3:
        db_manager.update_board_memo(3, memo_content_3)
        st.session_state.board_memo_3 = memo_content_3

# 削除済みタスク検索セクション
st.markdown("---")
with st.expander("🗑️ 削除済みタスク検索"):
    st.markdown("### 検索条件")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "開始日",
            value=datetime.now() - timedelta(days=30),
            key="search_start_date"
        )
    with col2:
        end_date = st.date_input(
            "終了日",
            value=datetime.now(),
            key="search_end_date"
        )

    delete_type_select = st.selectbox(
        "削除種類",
        ["すべて", "手動削除", "完了後自動削除"],
        key="search_delete_type"
    )

    # 削除種類をデータベースの値にマッピング
    delete_type_map = {
        "すべて": "all",
        "手動削除": "manual",
        "完了後自動削除": "auto_complete"
    }

    # セッション状態の初期化
    if 'deleted_tasks_results' not in st.session_state:
        st.session_state.deleted_tasks_results = None

    if st.button("検索", key="search_deleted_tasks"):
        # 日時に時刻を追加
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 検索実行
        st.session_state.deleted_tasks_results = db_manager.search_deleted_tasks(
            start_date=start_datetime,
            end_date=end_datetime,
            delete_type=delete_type_map[delete_type_select]
        )

    # 検索結果の表示
    if st.session_state.deleted_tasks_results is not None:
        deleted_tasks = st.session_state.deleted_tasks_results
        st.markdown(f"### 検索結果: {len(deleted_tasks)} 件")

        if deleted_tasks:
            # タスクリストを表示
            for task in deleted_tasks:
                # 削除種類の表示
                delete_type_label = "🔴 手動削除" if task['delete_type'] == 'manual' else "🔵 完了後自動削除"

                # 削除日時
                deleted_time = datetime.fromisoformat(task['deleted_at']).strftime('%Y/%m/%d %H:%M')

                # タイトルクリックで詳細表示
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    button_text = f"No.{task['task_no']} - {task['title']}"
                    if st.button(button_text, key=f"deleted_card_{task['id']}", use_container_width=True, type="secondary"):
                        show_deleted_task_detail(task)
                with col2:
                    st.markdown(f"{delete_type_label}")
                with col3:
                    st.caption(f"削除: {deleted_time}")

                st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
        else:
            st.info("指定された条件に一致する削除済みタスクが見つかりませんでした。")

# 使い方のセクション
with st.expander("使い方"):
    st.markdown("""
    ### 基本的な使い方:
    1. **タスクの追加**: サイドバーでタイトルと詳細を入力して「追加」ボタンをクリックします。タスクには自動的に番号が付与されます。
    2. **タスクの詳細表示**: タスクカードをクリックすると、タスクの詳細情報がダイアログで表示されます。
    3. **タスクの移動**: 各カードの下にある矢印ボタンをクリックして、ステータスを変更できます。
    4. **タスクの削除**: サイドバーの「タスク削除」セクションで番号を選択して削除できます。

    ### ステータス:
    - **未着手** → **進行中** → **完了** → **保留** の4つのステータスが利用できます。
    - ステータスは固定されており、追加や削除はできません。

    ### タスク番号:
    - 各タスクには自動的に連番（No.1, No.2, ...）が付与されます。
    - タスク削除時は番号を選択して削除します。

    ### 完了タスクの自動削除:
    - 「完了」ステータスに移動したタスクは完了時間が記録されます。
    - 完了後1週間経過したタスクは自動的に削除されます。
    - 削除されたタスクは下部の「削除済みタスク検索」から確認できます。

    ### 削除済みタスク検索:
    - ボードの下にある「🗑️ 削除済みタスク検索」セクションから削除済みタスクを検索できます。
    - 期間指定と削除種類（手動削除/完了後自動削除）で絞り込みが可能です。
    - 削除済みタスクをクリックすると詳細情報が表示されます。

    ### データ管理:
    - 全てのタスクはSQLiteデータベースに保存されます。
    - ブラウザを閉じてもデータは保持されます。
    """)
