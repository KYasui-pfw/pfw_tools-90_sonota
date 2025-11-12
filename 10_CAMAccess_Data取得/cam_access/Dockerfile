# ベースイメージとしてPython 3.12.0のスリム版を選択
FROM python:3.12.0-slim-bullseye

# 作業ディレクトリを設定
WORKDIR /app

# 最初にJava (JDK) をインストール
# aptのキャッシュを削除してイメージサイズを小さくする
RUN apt-get update && \
    apt-get install -y default-jdk-headless && \
    rm -rf /var/lib/apt/lists/*

# Pythonライブラリをインストール（先にこれを行うと、ソースコード変更時のビルドが高速化する）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# UCanAccessのjarファイル群をコンテナ内にコピー
COPY ucanaccess_lib/ ./ucanaccess_lib/

# 実行するPythonスクリプトをコピー
COPY app.py .

# コンテナ起動時に実行するコマンド
CMD [ "python", "app.py" ]
