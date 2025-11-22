FROM python:3.12.3-slim

WORKDIR /app

# pipを最新にアップグレード
RUN pip install --no-cache-dir --upgrade pip

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルとテンプレートをコピー
COPY streamlit_app_full.py .
COPY streamlit_app.py .
COPY pg/ /app/pg/

# ポート8508を公開
EXPOSE 8508

# Streamlitアプリを起動（完全版）
CMD ["streamlit", "run", "streamlit_app_full.py", "--server.port=8508", "--server.address=0.0.0.0", "--server.headless=true"]
