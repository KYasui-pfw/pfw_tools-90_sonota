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
import zipfile
import calendar
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
            # ファイル名から日付を抽出（log_YYYYMMDD.txt形式）
            import re
            match = re.search(r'log_(\d{8})\.txt$', log_file)
            if match:
                file_date_str = match.group(1)
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if file_date < cutoff_date:
                    os.remove(log_file)
                    print(f"古いログファイル {os.path.basename(log_file)} を削除しました (日付: {file_date.strftime('%Y-%m-%d')})")
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

# TimedRotatingFileHandlerを使用して日付でローテーション
import re
log_filename = os.path.join(LOG_DIR, "log.txt")
file_handler = TimedRotatingFileHandler(
    filename=log_filename,
    when='midnight',  # 毎日午前0時にローテーション
    interval=1,       # 1日間隔
    backupCount=7,    # 7日分のログを保持
    encoding='utf-8',
    delay=False,
    utc=False        # ローカル時間を使用
)

# ローテーション時のファイル名フォーマット設定（log_YYYYMMDD.txt形式）
file_handler.suffix = "_%Y%m%d.txt"
file_handler.extMatch = re.compile(r"^_\d{8}\.txt$")
file_handler.namer = lambda name: name.replace('log.txt.', 'log')

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
RBOM_DIR = os.getenv('RBOM_DIR')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))

# ファイル名に年が入っていないため、古いメールを読み直すと別年の同名ファイルと衝突する。
# メールの検索範囲は直近FETCH_DAYS日に絞り、ARCHIVE_MONTHSか月より古いファイルは月替わりにzipへ退避する。
# （FETCH_DAYS < ARCHIVE_MONTHSか月 を保つこと。退避したファイルが再取得されないようにするため）
FETCH_DAYS = 20
ARCHIVE_MONTHS = 1
BACKUP_SUBDIR = 'backup'
ARCHIVE_MARKER = '.last_archive_month'
IMAP_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def months_ago(dt, n):
    """dtのnか月前の日時を返す（月末は存在する日に丸める）"""
    y, m = dt.year, dt.month - n
    while m < 1:
        m += 12
        y -= 1
    return dt.replace(year=y, month=m, day=min(dt.day, calendar.monthrange(y, m)[1]))


def archive_old_files():
    """SAVE_DIR直下のARCHIVE_MONTHSか月より古いファイルを、更新月ごとにbackup/S_YYYYMM.zipへ移す。
    zipへの書き込みと検証が済んだファイルだけ削除する（失敗時は元ファイルを残す）。"""
    backup_dir = os.path.join(SAVE_DIR, BACKUP_SUBDIR)
    cutoff = months_ago(datetime.now(), ARCHIVE_MONTHS).timestamp()

    groups = {}
    for name in os.listdir(SAVE_DIR):
        path = os.path.join(SAVE_DIR, name)
        if not os.path.isfile(path):
            continue
        mtime = os.path.getmtime(path)
        if mtime < cutoff:
            ym = datetime.fromtimestamp(mtime).strftime('%Y%m')
            groups.setdefault(ym, []).append((name, path, mtime))

    if not groups:
        logger.info("退避対象の古いファイルはありません")
        return True

    os.makedirs(backup_dir, exist_ok=True)
    ok = True
    for ym, items in sorted(groups.items()):
        zip_path = os.path.join(backup_dir, f"S_{ym}.zip")
        try:
            arcnames = {}
            with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zf:
                existing = set(zf.namelist())
                for name, path, mtime in items:
                    arcname = name
                    if arcname in existing:
                        # 同名がzip内にある場合は更新日時を付けて区別する
                        stem, ext = os.path.splitext(name)
                        arcname = f"{stem}_{datetime.fromtimestamp(mtime).strftime('%Y%m%d%H%M%S')}{ext}"
                    zf.write(path, arcname)
                    existing.add(arcname)
                    arcnames[path] = arcname
            # 検証してから削除
            with zipfile.ZipFile(zip_path) as zf:
                bad = zf.testzip()
                names = set(zf.namelist())
            if bad is not None or any(a not in names for a in arcnames.values()):
                raise RuntimeError(f"zip検証に失敗しました: {zip_path} ({bad})")
            for name, path, mtime in items:
                os.remove(path)
            logger.info(f"📦 {len(items)}件を {os.path.basename(zip_path)} に退避しました")
        except Exception as e:
            ok = False
            logger.error(f"❌ 古いファイルの退避に失敗しました ({ym}): {e}")
            logger.error(traceback.format_exc())
    return ok


def archive_if_new_month():
    """前回の退避と月が違えば（＝月が替わっていれば）archive_old_filesを実行する"""
    if not SAVE_DIR or not os.path.exists(SAVE_DIR):
        return
    marker = os.path.join(SAVE_DIR, BACKUP_SUBDIR, ARCHIVE_MARKER)
    this_month = datetime.now().strftime('%Y%m')
    try:
        last = open(marker, encoding='utf-8').read().strip() if os.path.exists(marker) else None
    except Exception:
        last = None
    if last == this_month:
        return
    logger.info(f"月次の古いファイル退避を開始します（前回: {last or '未実行'} → 今回: {this_month}）")
    try:
        if archive_old_files():
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, 'w', encoding='utf-8') as f:
                f.write(this_month)
    except Exception as e:
        logger.error(f"❌ 月次退避で予期せぬエラー: {e}")
        logger.error(traceback.format_exc())


def get_latest_s_file():
    """SAVE_DIRから最新のSで始まるファイルを取得する関数"""
    if not os.path.exists(SAVE_DIR):
        logger.warning(f"SAVE_DIRが存在しません: {SAVE_DIR}")
        return None
        
    try:
        # Sで始まるファイルを検索
        s_files = []
        for filename in os.listdir(SAVE_DIR):
            if filename.upper().startswith('S') and os.path.isfile(os.path.join(SAVE_DIR, filename)):
                filepath = os.path.join(SAVE_DIR, filename)
                mtime = os.path.getmtime(filepath)
                s_files.append((filename, filepath, mtime))
        
        if not s_files:
            logger.info("SAVE_DIRにSで始まるファイルが見つかりません")
            return None
            
        # 更新時間で最新のファイルを取得
        latest_file = max(s_files, key=lambda x: x[2])
        logger.info(f"最新のSファイル: {latest_file[0]} (更新時間: {datetime.fromtimestamp(latest_file[2]).strftime('%Y-%m-%d %H:%M:%S')})")
        
        return latest_file[1]  # filepath を返す
        
    except Exception as e:
        logger.error(f"最新ファイル検索エラー: {e}")
        return None

def copy_latest_to_rbom():
    """最新のSファイルをRBOM_DIRにspecification-fit.xlsとしてコピーする関数"""
    if not RBOM_DIR:
        logger.warning("⚠️ RBOM_DIRが設定されていません。")
        return
        
    latest_filepath = get_latest_s_file()
    if not latest_filepath:
        logger.warning("コピー対象の最新ファイルが見つかりません")
        return
        
    latest_filename = os.path.basename(latest_filepath)
    
    # RBOM_DIRが存在しなければ作成
    if not os.path.exists(RBOM_DIR):
        logger.info(f"📁 RBOM_DIRを作成します: {RBOM_DIR}")
        os.makedirs(RBOM_DIR)
    
    logger.info(f"RBOM_DIRへのコピーを開始: {latest_filename} → specification-fit.xls")
    rbom_filepath = os.path.join(RBOM_DIR, "specification-fit.xls")
    
    try:
        # 元ファイルの情報を取得
        stat_info = os.stat(latest_filepath)
        
        with open(latest_filepath, 'rb') as src:
            with open(rbom_filepath, 'wb') as dst:
                dst.write(src.read())
        
        # コピー先ファイルに元ファイルのタイムスタンプを設定
        os.utime(rbom_filepath, (stat_info.st_atime, stat_info.st_mtime))
        
        # Windowsの場合、ファイル属性も可能な限り保持
        try:
            import stat
            os.chmod(rbom_filepath, stat_info.st_mode)
        except Exception as chmod_error:
            logger.debug(f"ファイル権限の設定をスキップ: {chmod_error}")
        
        logger.info(f"✅ ファイルをRBOM_DIRに 'specification-fit.xls' としてコピーしました。（タイムスタンプ・属性保持）")
    except Exception as e:
        # エラーが発生した場合はerrlogに出力
        error_msg = f"❌ RBOM_DIR保存エラー: {rbom_filepath}"
        logger.error(error_msg)
        
        # errlogファイルに詳細を出力
        errlog_path = os.path.join(LOG_DIR, f"errlog_{datetime.now().strftime('%Y%m%d')}.txt")
        try:
            with open(errlog_path, 'a', encoding='utf-8') as errlog:
                errlog.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
                errlog.write(f"詳細エラー: {str(e)}\n")
                errlog.write(f"元ファイル名: {latest_filename}\n")
                errlog.write("=" * 50 + "\n")
        except Exception as errlog_error:
            logger.error(f"errlogファイル出力エラー: {errlog_error}")


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
        since = datetime.now() - timedelta(days=FETCH_DAYS)
        since_str = f"{since.day:02d}-{IMAP_MONTHS[since.month - 1]}-{since.year}"
        criteria = f'(FROM "{TARGET_SENDER}" SINCE {since_str})' # 既読・未読問わず・直近FETCH_DAYS日
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
                    logger.info(f"🔍 添付ファイル発見: {filename}")
                    if filename:
                        decoded_header = decode_header(filename)
                        # デコード後のファイル名を結合
                        filename = ''.join(
                            s.decode(charset if charset else 'utf-8', 'ignore') if isinstance(s, bytes) else s
                            for s, charset in decoded_header
                        )
                        logger.info(f"📝 デコード後ファイル名: {filename}")
                        
                        # ファイル名がSで始まるかチェック
                        if not filename.upper().startswith('S'):
                            logger.info(f"⏭️  ファイル '{filename}' はSから始まらないため、スキップしました。")
                            continue
                        
                        logger.info(f"✅ ファイル '{filename}' は条件に合致します。処理を開始します。")
                        
                        # 保存先ディレクトリがなければ作成
                        if not os.path.exists(SAVE_DIR):
                            logger.info(f"📁 SAVE_DIRを作成します: {SAVE_DIR}")
                            os.makedirs(SAVE_DIR)
                        if RBOM_DIR and not os.path.exists(RBOM_DIR):
                            logger.info(f"📁 RBOM_DIRを作成します: {RBOM_DIR}")
                            os.makedirs(RBOM_DIR)
                        
                        # ファイル内容を取得
                        file_content = part.get_payload(decode=True)
                        
                        # SAVE_DIRへの保存処理
                        filepath = os.path.join(SAVE_DIR, filename)
                        if os.path.exists(filepath):
                            logger.warning(f"⚠️  ファイル '{filename}' は既に存在するため、SAVE_DIRへの保存をスキップしました。")
                        else:
                            # SAVE_DIRにオリジナル名で保存
                            with open(filepath, 'wb') as f:
                                f.write(file_content)
                            logger.info(f"✅ 添付ファイル '{filename}' を保存しました。")
            
            # 処理済みのメールを既読にする（不要な場合はこの行をコメントアウト）
            mail.store(mail_id, '+FLAGS', '\\Seen')

        # --- 5. サーバーからログアウト ---
        mail.logout()
        
        # --- 6. 最新のSファイルをRBOM_DIRにコピー ---
        copy_latest_to_rbom()

    except imaplib.IMAP4.error as e:
        logger.error(f"❌ IMAPエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"❌ 予期せぬエラーが発生しました: {e}")
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info("添付ファイル自動取得スクリプトを開始します。")
    logger.info(f"送信元: {TARGET_SENDER}")
    logger.info(f"チェック間隔: {CHECK_INTERVAL // 60}分")
    logger.info(f"SAVE_DIR: {SAVE_DIR}")
    logger.info(f"RBOM_DIR: {RBOM_DIR}")
    logger.info("----------------------------------------")

    while True:
        archive_if_new_month()
        logger.info("メールの確認を開始します。")
        fetch_attachments()
        logger.info("確認完了。次の確認まで待機します...")
        time.sleep(CHECK_INTERVAL)
