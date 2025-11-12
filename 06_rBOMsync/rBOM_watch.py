import os
import time
import logging
import subprocess
from logging.handlers import RotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import threading

# --- 初期設定 ---
# .envファイルから環境変数を読み込む
load_dotenv()

# ログ設定
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)

# 環境変数から設定を読み込み
SOURCE_DIR = os.getenv('SOURCE_DIR')
DEST_UNC_PATH = os.getenv('DEST_UNC_PATH')
LINUX_USER = os.getenv('LINUX_USER')
LINUX_PASSWORD = os.getenv('LINUX_PASSWORD')

# --- 同期処理の定義 ---
class SyncEventHandler(FileSystemEventHandler):
    """ファイルシステムのイベントを処理し、同期をトリガーするハンドラ"""
    def __init__(self):
        super().__init__()
        self.timer = None
        self.lock = threading.Lock()
        self.debounce_seconds = 5  # イベント発生後、5秒待ってから同期実行（連続変更をまとめるため）

    def on_any_event(self, event):
        """全てのファイルシステムイベントを捕捉する"""
        if event.is_directory:
            logging.info(f"ディレクトリイベント検知: {event.event_type} - {event.src_path}")
        else:
            logging.info(f"ファイルイベント検知: {event.event_type} - {event.src_path}")
        
        self.schedule_sync()

    def schedule_sync(self):
        """重複実行を防ぎつつ、同期処理をスケジュールする（デバウンス）"""
        with self.lock:
            if self.timer:
                self.timer.cancel()
            
            self.timer = threading.Timer(self.debounce_seconds, self.run_sync_task)
            self.timer.start()
            logging.info(f"{self.debounce_seconds}秒後に同期をスケジュールしました。")

    def run_sync_task(self):
        """資格情報の設定、robocopyの実行、資格情報の削除を順に行う"""
        logging.info("="*20 + " 同期処理開始 " + "="*20)
        
        # 1. 共有フォルダに接続
        logging.info(f"共有フォルダ '{DEST_UNC_PATH}' に接続します。")
        connect_command = [
            'net', 'use', DEST_UNC_PATH, f'/user:{LINUX_USER}', LINUX_PASSWORD, '/persistent:no'
        ]
        try:
            # 既に接続がある場合を考慮し、一度削除を試みる
            subprocess.run(['net', 'use', DEST_UNC_PATH, '/delete', '/y'], capture_output=True, text=True)
            result = subprocess.run(connect_command, check=True, capture_output=True, text=True, encoding='cp932')
            logging.info("共有フォルダへの接続に成功しました。")
        except subprocess.CalledProcessError as e:
            logging.error(f"共有フォルダへの接続に失敗しました。エラー: {e.stderr}")
            return # 接続失敗時はここで処理を中断

        # 2. robocopyで同期
        logging.info(f"robocopy を実行中... '{SOURCE_DIR}' -> '{DEST_UNC_PATH}'")
        # /MIR: ミラーリング（コピー元と先を同一にする。元にないファイルは削除）
        # /R:3 : リトライ回数3回
        # /W:5 : リトライ間隔5秒
        robocopy_command = [
            'robocopy', SOURCE_DIR, DEST_UNC_PATH, '/MIR', '/R:3', '/W:5'
        ]
        try:
            result = subprocess.run(robocopy_command, check=True, capture_output=True, text=True, encoding='cp932')
            logging.info("robocopy が正常に完了しました。")
            # robocopyは成功時も詳細を標準出力に出すため、ログに出力
            if result.stdout:
                logging.debug(f"robocopy 出力:\n{result.stdout}")

        except subprocess.CalledProcessError as e:
            # robocopyは正常なコピーでも終了コードが1以上になるため、2未満は成功とみなす
            if e.returncode < 2:
                logging.info(f"robocopy が正常に完了しました。終了コード: {e.returncode}")
                if e.stdout:
                    logging.debug(f"robocopy 出力:\n{e.stdout}")
            else:
                # robocopyは終了コードで成否を返すため、エラーコードに応じたログを出す
                logging.error(f"robocopy の実行でエラーまたは警告が発生しました。終了コード: {e.returncode}")
                if e.stdout:
                    logging.error(f"robocopy 出力:\n{e.stdout}")
                if e.stderr:
                    logging.error(f"robocopy エラー出力:\n{e.stderr}")

            if e.stdout:
                logging.error(f"robocopy 出力:\n{e.stdout}")
            if e.stderr:
                logging.error(f"robocopy エラー出力:\n{e.stderr}")
        
        finally:
            # 3. 共有フォルダから切断（成功・失敗に関わらず実行）
            logging.info(f"共有フォルダ '{DEST_UNC_PATH}' から切断します。")
            disconnect_command = ['net', 'use', DEST_UNC_PATH, '/delete', '/y']
            subprocess.run(disconnect_command, capture_output=True)
            logging.info("共有フォルダから切断しました。")
            logging.info("="*20 + " 同期処理完了 " + "="*20)

# --- メイン処理 ---
if __name__ == "__main__":
    if not all([SOURCE_DIR, DEST_UNC_PATH, LINUX_USER, LINUX_PASSWORD]):
        logging.critical(".envファイルに必要な設定が不足しています。スクリプトを終了します。")
        exit()
        
    logging.info("監視サービスを開始します。")
    logging.info(f"監視対象フォルダ: {SOURCE_DIR}")

    # 初回起動時に一度同期を実行
    event_handler_for_initial_sync = SyncEventHandler()
    logging.info("初回同期を実行します...")
    event_handler_for_initial_sync.run_sync_task()
    
    # 監視を開始
    event_handler = SyncEventHandler()
    observer = Observer()
    observer.schedule(event_handler, SOURCE_DIR, recursive=True)
    observer.start()
    logging.info("フォルダの監視を開始しました。")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("監視サービスが停止されました。")
    observer.join()