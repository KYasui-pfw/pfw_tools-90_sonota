# rBOM 実績登録エラーメール通知システム

Oracle DBの実績テーブルでエラーを検知し、登録者に自動でメール通知を行うシステムです。

## システム概要

### 主な機能
1. **エラー監視**: 5分ごとにOracle DBの指定テーブルを監視し、エラーデータを検出
2. **メール通知**: エラーデータの登録者に自動でメール送信
3. **送信履歴管理**: SQLiteでメール送信済みかを管理（重複送信防止）
4. **ユーザー管理**: Streamlit管理画面で社員コードとメールアドレスの紐付けを管理

### システム構成
- **監視プログラム**: Python + Cron（5分間隔）
- **管理画面**: Streamlit
- **データベース**: SQLite（送信履歴・ユーザーマスタ）
- **API連携**: FastAPI Generic Query API経由でOracle DBにアクセス
- **デプロイ**: Docker Compose

---

## ディレクトリ構成

```
9_rbom_err_mailsend/
├── db/                          # SQLiteデータベース
│   └── mail_management.db
├── app/                         # アプリケーションコード
│   ├── __init__.py
│   ├── config.py                # 設定管理
│   ├── db_manager.py            # SQLite操作
│   ├── mail_sender.py           # メール送信
│   └── monitor.py               # エラー監視メインプログラム
├── streamlit_app/               # Streamlit管理画面
│   └── main.py
├── logs/                        # ログファイル
├── scripts/                     # 運用スクリプト
│   └── init_db.py               # DB初期化
├── docker/                      # Docker関連
│   ├── Dockerfile.monitor
│   ├── Dockerfile.streamlit
│   └── crontab
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## セットアップ手順

### 1. 環境変数の設定

`.env.example` をコピーして `.env` ファイルを作成し、実際の値を設定してください。

```bash
cp .env.example .env
```

**必須設定項目**:

```bash
# FastAPI接続設定
FASTAPI_BASE_URL=http://your-fastapi-server:8000
READ_API_KEY=your_actual_read_api_key

# 監視設定
MONITOR_TABLE=DK030
ERROR_STATUS_FIELD=SYORIZUMIKB
ERROR_STATUS_VALUE=9
EMPLOYEE_CODE_FIELD=TANCD

# メール送信設定
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password
MAIL_FROM=noreply@example.com
MAIL_FROM_NAME=rBOM System
```

### 2. Dockerコンテナの起動

```bash
docker-compose up -d --build
```

起動されるサービス:
- `monitor`: エラー監視プログラム（5分ごとに実行）
- `streamlit`: 管理画面（ポート8507）

### 3. 管理画面へアクセス

ブラウザで以下にアクセス:

```
http://localhost:8507
```

### 4. ユーザー・メールアドレスの登録

管理画面から社員コードとメールアドレスの紐付けを登録してください。

---

## データベーステーブル構造

### user_email_master（社員・メールアドレス紐付けマスタ）

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| employee_code | VARCHAR(20) | 社員コード（UNIQUE） |
| employee_name | VARCHAR(100) | 社員名 |
| email_address | VARCHAR(255) | メールアドレス |
| is_active | BOOLEAN | 有効/無効フラグ |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

### mail_send_history（メール送信履歴）

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| table_name | VARCHAR(50) | 監視対象テーブル名 |
| record_id | VARCHAR(100) | レコード識別子 |
| employee_code | VARCHAR(20) | 送信先社員コード |
| email_address | VARCHAR(255) | 送信先メールアドレス |
| error_detail | TEXT | エラー内容 |
| sent_at | TIMESTAMP | 送信日時 |

※ `(table_name, record_id)` にUNIQUE制約（重複送信防止）

---

## 運用方法

### ログ確認

```bash
# 監視プログラムのログ
docker logs rbom_error_monitor

# Cron実行ログ
docker exec rbom_error_monitor cat /app/logs/cron.log

# 監視プログラムの詳細ログ
docker exec rbom_error_monitor cat /app/logs/monitor.log
```

### コンテナの停止・再起動

```bash
# 停止
docker-compose down

# 再起動
docker-compose restart

# 再ビルド
docker-compose up -d --build
```

### データベース初期化（手動実行）

```bash
docker exec rbom_error_monitor python /app/scripts/init_db.py
```

---

## トラブルシューティング

### メールが送信されない

1. `.env` のSMTP設定を確認
2. ログで送信エラーの詳細を確認: `logs/monitor.log`
3. ユーザー・メールアドレスが正しく登録されているか管理画面で確認

### エラーデータが検出されない

1. `.env` の監視設定（テーブル名、フィールド名、エラー値）を確認
2. FastAPI接続設定（URL、API Key）を確認
3. Oracle DBに実際にエラーデータが存在するか確認

### 管理画面にアクセスできない

1. Streamlitコンテナが起動しているか確認: `docker ps`
2. ポート8507が使用可能か確認
3. コンテナログを確認: `docker logs rbom_admin_ui`

---

## Linux環境への移行

このディレクトリ全体をLinuxサーバーにコピーして以下を実行:

```bash
# .envファイルを作成・編集
cp .env.example .env
vi .env

# Docker Composeで起動
docker-compose up -d --build
```

---

## 開発・カスタマイズ

### エラー判定条件の変更

`.env` ファイルで以下を変更:

```bash
MONITOR_TABLE=対象テーブル名
ERROR_STATUS_FIELD=エラー判定フィールド名
ERROR_STATUS_VALUE=エラーと判定する値
EMPLOYEE_CODE_FIELD=社員コードフィールド名
```

### メール本文のカスタマイズ

`app/mail_sender.py` の `_create_mail_body()` メソッドを編集してください。

### 監視間隔の変更

`docker/crontab` のcron設定を変更してください。

```bash
# 例: 10分ごとに変更
*/10 * * * * cd /app && /usr/local/bin/python -m app.monitor >> /app/logs/cron.log 2>&1
```

変更後は再ビルドが必要です:

```bash
docker-compose up -d --build
```

---

## ライセンス

社内利用のみ

---

## 問い合わせ

システム管理者までお問い合わせください。
