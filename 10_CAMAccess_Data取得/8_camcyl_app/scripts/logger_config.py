"""
ログ設定モジュール
7日間のログローテーションを提供
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


def setup_logger(name, log_dir="/app/logs", retention_days=7):
    """
    ロガーを設定する

    Args:
        name (str): ロガー名（プロセス名）
        log_dir (str): ログ出力ディレクトリ
        retention_days (int): ログ保持期間（日数）

    Returns:
        logging.Logger: 設定済みロガー
    """
    # ログディレクトリが存在しない場合は作成
    os.makedirs(log_dir, exist_ok=True)

    # ロガーの取得
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 既存のハンドラーをクリア（重複を防ぐ）
    if logger.handlers:
        logger.handlers.clear()

    # ログファイル名（日付付き）
    log_filename = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    # ファイルハンドラー（日次ローテーション）
    file_handler = TimedRotatingFileHandler(
        filename=log_filename,
        when='midnight',
        interval=1,
        backupCount=retention_days,
        encoding='utf-8'
    )

    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # コンソールハンドラー（標準出力）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # ハンドラーを追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def cleanup_old_logs(log_dir, retention_days=7):
    """
    古いログファイルを削除する

    Args:
        log_dir (str): ログディレクトリ
        retention_days (int): 保持期間（日数）
    """
    import time

    if not os.path.exists(log_dir):
        return

    current_time = time.time()
    retention_seconds = retention_days * 86400  # 日数を秒に変換

    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)

        # ファイルのみ対象
        if not os.path.isfile(file_path):
            continue

        # .logファイルのみ対象
        if not filename.endswith('.log'):
            continue

        # ファイルの最終更新時刻を確認
        file_mtime = os.path.getmtime(file_path)

        # 保持期間を過ぎていたら削除
        if current_time - file_mtime > retention_seconds:
            try:
                os.remove(file_path)
                print(f"古いログファイルを削除しました: {filename}")
            except Exception as e:
                print(f"ログファイル削除エラー: {filename} - {e}")
