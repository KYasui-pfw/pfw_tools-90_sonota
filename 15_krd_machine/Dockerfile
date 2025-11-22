# ベースイメージとしてPython 3.12のスリム版を選択
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
# - cron: スケジュール実行用
# - tzdata: タイムゾーン設定用
# - dos2unix: 改行コード変換用
RUN apt-get update && \
    apt-get install -y \
    cron \
    tzdata \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# タイムゾーンを日本時間に設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Pythonライブラリをインストール（キャッシュ効率化のため先に実行）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# スクリプトファイルをコピー
COPY krd_sync_frequent.py ./
COPY krd_sync_hourly.py ./
COPY krd_sqlite_helper.py ./

# エントリーポイントスクリプトをコピー
COPY entrypoint.sh /app/entrypoint.sh

# 改行コードをLFに変換して実行権限を付与
RUN dos2unix /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# .envファイルをコピー（cron実行時に読み込むため）
COPY .env /app/.env
RUN dos2unix /app/.env

# crontabファイルをコピーして設定
COPY crontab /etc/cron.d/krd-sync-cron
RUN dos2unix /etc/cron.d/krd-sync-cron && \
    chmod 0644 /etc/cron.d/krd-sync-cron && \
    touch /var/log/cron.log

# ログディレクトリとDBディレクトリを作成
RUN mkdir -p /app/logs /app/db

# エントリーポイントを実行（起動時処理 + cron起動）
CMD ["/app/entrypoint.sh"]
