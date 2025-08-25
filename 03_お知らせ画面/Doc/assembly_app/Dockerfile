FROM python:3.12.3-slim

WORKDIR /assembly_streamlit_app


# 1. 必要なシステムパッケージのインストール
#    - apt-transport-https, curl, gnupg: Microsoftリポジトリを追加するために必要
#    - unixodbc-dev: pyodbcが依存するODBCマネージャの開発ファイル (libodbc.so.2 は unixodbc-dev または unixodbc から提供される)
#    - msodbcsql17: Microsoft ODBC Driver 17 for SQL Server
#    - mssql-tools: sqlcmd, bcp など (必要なければ省略可)

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    apt-transport-https \
    curl \
    gnupg \
    unixodbc-dev \
    libgssapi-krb5-2 \
    && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft-prod.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# 2. pipを最新にアップグレード (任意だが推奨)
RUN pip install --no-cache-dir --upgrade pip

COPY ./assembly_streamlit_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./assembly_streamlit_app .

#CMD ["streamlit", "run", "assembly_checksheet.py", "--server.port=8502", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "main.py", "--server.port=8502", "--server.address=0.0.0.0"]
