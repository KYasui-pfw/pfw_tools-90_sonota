# ベースイメージとしてPython 3.12のスリム版を選択
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
# - default-jdk-headless: Java（UCanAccess用）
# - cron: スケジュール実行用
# - tzdata: タイムゾーン設定用
RUN apt-get update && \
    apt-get install -y \
    default-jdk-headless \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# タイムゾーンを日本時間に設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Pythonライブラリをインストール（キャッシュ効率化のため先に実行）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# UCanAccessのjarファイル群をコンテナ内にコピー
COPY ucanaccess_lib/ ./ucanaccess_lib/

# スクリプトファイルをコピー
COPY scripts/ ./scripts/

# エントリーポイントスクリプトをコピー
COPY entrypoint.sh /app/entrypoint.sh

# スクリプトに実行権限を付与
RUN chmod +x /app/scripts/*.sh /app/entrypoint.sh

# crontabファイルをコピーして設定
COPY crontab /etc/cron.d/camcyl-cron
RUN chmod 0644 /etc/cron.d/camcyl-cron && \
    crontab /etc/cron.d/camcyl-cron

# ログディレクトリを作成
RUN mkdir -p /app/logs /app/data /app/output/KakouDenpyo /app/output/KakouJisseki

# エントリーポイントを実行（起動時処理 + cron起動）
CMD ["/app/entrypoint.sh"]
