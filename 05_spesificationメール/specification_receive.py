import imaplib
import email
from email.header import decode_header
import os
import time
import traceback
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
import glob
from dotenv import load_dotenv

load_dotenv()

# 古いログファイル削除関数
def cleanup_old_logs(log_dir, days_to_keep=7):
    """指定した日数を過ぎたログファイルを自動削除"""
    try:
        log_pattern = os.path.join(log_dir, "log_*.txt")
        log_files = glob.glob(log_pattern)
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for log_file in log_files:
            file_time = datetime.fromtimestamp(os.path.getctime(log_file))
            if file_time < cutoff_date:
                os.remove(log_file)
                print(f"古いログファイル {os.path.basename(log_file)} を削除しました (作成日: {file_time.strftime('%Y-%m-%d')})")
                deleted_count += 1
        
        if deleted_count == 0:
            print(f"削除対象のログファイルはありません (保持期間: {days_to_keep}日)")
        else:
            print(f"{deleted_count}個のログファイルを削除しました")
            
    except Exception as e:
        print(f"ログファイル削除エラー: {e}")

# ログ設定
LOG_DIR = os.getenv('LOG_DIR', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# ログローテーション設定（日次で新しいファイル作成）
log_filename = os.path.join(LOG_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.txt")
file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler]
)
logger = logging.getLogger(__name__)

# 古いログファイルを削除
cleanup_old_logs(LOG_DIR)

IMAP_SERVER = os.getenv('IMAP_SERVER')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
PASSWORD = os.getenv('PASSWORD')
TARGET_SENDER = os.getenv('TARGET_SENDER')
SAVE_DIR = os.getenv('SAVE_DIR')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))

def fetch_attachments():
    """IMAPサーバーに接続し、条件に合うメールから添付ファイルを取得する関数"""
    try:
        # --- 1. IMAPサーバーに接続してログイン ---
        logger.info("IMAPサーバーに接続しています...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, PASSWORD)
        mail.select('inbox')
        logger.info("接続成功。")

        # --- 2. 未読メールの中から特定の送信元のメールを検索 ---
        # criteria = f'(UNSEEN FROM "{TARGET_SENDER}")' # 未読のみ
        criteria = f'(FROM "{TARGET_SENDER}")' # 既読・未読問わず
        status, messages = mail.search(None, criteria)

        if status != 'OK' or not messages[0]:
            logger.info("対象のメールは見つかりませんでした。")
            mail.logout()
            return

        mail_ids = messages[0].split()
        logger.info(f"{len(mail_ids)}件の対象メールが見つかりました。")

        # --- 3. メールを1通ずつ処理 ---
        for mail_id in mail_ids:
            status, data = mail.fetch(mail_id, '(RFC822)')
            if status != 'OK':
                continue

            # メールデータをパース
            msg = email.message_from_bytes(data[0][1])

            # --- 4. 添付ファイルを検索して保存 ---
            for part in msg.walk():
                # マルチパートでない、かつContent-Dispositionがない場合はスキップ
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue

                # 添付ファイルの場合のみ処理
                if 'attachment' in part.get('Content-Disposition'):
                    # ファイル名を取得してデコード（日本語ファイル名対応）
                    filename = part.get_filename()
                    if filename:
                        decoded_header = decode_header(filename)
                        # デコード後のファイル名を結合
                        filename = ''.join(
                            s.decode(charset if charset else 'utf-8', 'ignore') if isinstance(s, bytes) else s
                            for s, charset in decoded_header
                        )
                        
                        # ファイル名がSで始まるかチェック
                        if not filename.upper().startswith('S'):
                            logger.info(f"⏭️  ファイル '{filename}' はSから始まらないため、スキップしました。")
                            continue
                        
                        # 保存先ディレクトリがなければ作成
                        if not os.path.exists(SAVE_DIR):
                            os.makedirs(SAVE_DIR)
                        
                        filepath = os.path.join(SAVE_DIR, filename)

                        # ファイルが既に存在するかどうかを確認
                        if os.path.exists(filepath):
                            logger.warning(f"⚠️  ファイル '{filename}' は既に存在するため、スキップしました。")
                            continue  # 存在する場合はこのファイルの処理をスキップして次の添付ファイルへ
                        
                        # ファイルをバイナリモードで保存
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        logger.info(f"✅ 添付ファイル '{filename}' を保存しました。")
            
            # 処理済みのメールを既読にする（不要な場合はこの行をコメントアウト）
            mail.store(mail_id, '+FLAGS', '\\Seen')

        # --- 5. サーバーからログアウト ---
        mail.logout()

    except imaplib.IMAP4.error as e:
        logger.error(f"❌ IMAPエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"❌ 予期せぬエラーが発生しました: {e}")
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("添付ファイル自動取得スクリプトを開始します。")
    logger.info(f"送信元: {TARGET_SENDER}")
    logger.info(f"チェック間隔: {CHECK_INTERVAL // 5}分")
    logger.info("----------------------------------------")

    while True:
        logger.info("メールの確認を開始します。")
        fetch_attachments()
        logger.info("確認完了。次の確認まで待機します...")
        time.sleep(CHECK_INTERVAL)
