import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'kanban.db')

def init_db():
    """データベースとテーブルを初期化"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # アクティブなタスクテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL
        )
    ''')

    # 削除済みタスクテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_no INTEGER NOT NULL,
            title TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP NULL,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delete_type TEXT NOT NULL
        )
    ''')

    # 次のタスク番号を管理するテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    ''')

    # 初期設定
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', ('next_no', 1))

    conn.commit()
    conn.close()

def get_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_next_task_no():
    """次のタスク番号を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', ('next_no',))
    result = cursor.fetchone()
    next_no = result['value'] if result else 1
    conn.close()
    return next_no

def increment_task_no():
    """タスク番号をインクリメント"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE settings SET value = value + 1 WHERE key = ?', ('next_no',))
    conn.commit()
    conn.close()

def get_all_tasks():
    """全てのアクティブタスクを取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY no')
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def add_task(title, details, status):
    """タスクを追加"""
    no = get_next_task_no()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tasks (no, title, details, status, created_at) VALUES (?, ?, ?, ?, ?)',
        (no, title, details, status, datetime.now())
    )
    conn.commit()
    conn.close()
    increment_task_no()
    return no

def update_task_status(task_no, new_status):
    """タスクのステータスを更新"""
    conn = get_connection()
    cursor = conn.cursor()

    if new_status == '完了':
        # 完了に移動した場合は完了時間を記録
        cursor.execute(
            'UPDATE tasks SET status = ?, completed_at = ? WHERE no = ?',
            (new_status, datetime.now(), task_no)
        )
    else:
        # 完了以外に移動した場合は完了時間をリセット
        cursor.execute(
            'UPDATE tasks SET status = ?, completed_at = NULL WHERE no = ?',
            (new_status, task_no)
        )

    conn.commit()
    conn.close()

def update_task(task_no, title, details):
    """タスクの内容を更新"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE tasks SET title = ?, details = ? WHERE no = ?',
        (title, details, task_no)
    )
    conn.commit()
    conn.close()

def delete_task(task_no, delete_type='manual'):
    """タスクを削除（削除済みテーブルに移動）"""
    conn = get_connection()
    cursor = conn.cursor()

    # タスク情報を取得
    cursor.execute('SELECT * FROM tasks WHERE no = ?', (task_no,))
    task = cursor.fetchone()

    if task:
        # 削除済みテーブルに挿入
        cursor.execute(
            '''INSERT INTO deleted_tasks
               (task_no, title, details, status, created_at, completed_at, deleted_at, delete_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (task['no'], task['title'], task['details'], task['status'], task['created_at'],
             task['completed_at'], datetime.now(), delete_type)
        )

        # アクティブテーブルから削除
        cursor.execute('DELETE FROM tasks WHERE no = ?', (task_no,))

        conn.commit()

    conn.close()

def auto_delete_old_completed_tasks():
    """完了後1週間経過したタスクを自動削除"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1週間前の日時を計算
    one_week_ago = datetime.now() - timedelta(days=7)

    # 完了後1週間経過したタスクを取得
    cursor.execute(
        '''SELECT * FROM tasks
           WHERE status = ? AND completed_at IS NOT NULL AND completed_at <= ?''',
        ('完了', one_week_ago)
    )
    old_tasks = cursor.fetchall()

    # 削除処理
    for task in old_tasks:
        cursor.execute(
            '''INSERT INTO deleted_tasks
               (task_no, title, details, status, created_at, completed_at, deleted_at, delete_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (task['no'], task['title'], task['details'], task['status'], task['created_at'],
             task['completed_at'], datetime.now(), 'auto_complete')
        )
        cursor.execute('DELETE FROM tasks WHERE no = ?', (task['no'],))

    conn.commit()
    deleted_count = len(old_tasks)
    conn.close()

    return deleted_count

def search_deleted_tasks(start_date=None, end_date=None, delete_type=None):
    """削除済みタスクを検索"""
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM deleted_tasks WHERE 1=1'
    params = []

    if start_date:
        query += ' AND deleted_at >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND deleted_at <= ?'
        params.append(end_date)

    if delete_type and delete_type != 'all':
        query += ' AND delete_type = ?'
        params.append(delete_type)

    query += ' ORDER BY deleted_at DESC'

    cursor.execute(query, params)
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return tasks

# データベース初期化
if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")
