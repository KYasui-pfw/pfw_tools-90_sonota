# KRD MySQL → SQLite 同期システム

## 概要

KRD MySQLデータベース（krd/machin）のBASE TABLEをSQLiteに同期するシステムです。
テーブルを利用頻度に応じて2つのグループに分け、異なる頻度で同期します。

## 仕様

### 共通仕様
- **同期対象**: BASE TABLEのみ（VIEWは除外）
- **同期方向**: MySQL → SQLite（一方向、読み取り専用）
- **更新戦略**: 全件置き換え（DELETE & INSERT）
- **エラー処理**: ログ記録のみ（処理継続）
- **ログ保持**: 日次ローテーション、7日間保持

### 高頻度同期（5分ごと）
- **対象**: genpinhyoシステムで使用している5テーブル
- **スクリプト**: `krd_sync_frequent.py`
- **ログファイル**: `logs/log_frequent.txt`

### 低頻度同期（1時間ごと）
- **対象**: その他の45テーブル
- **スクリプト**: `krd_sync_hourly.py`
- **ログファイル**: `logs/log_hourly.txt`

## ファイル構成

```
C:\Dev\90_tools\15_krd_machine\
├── Dockerfile               # Docker イメージ定義
├── docker-compose.yml       # Docker Compose 設定
├── entrypoint.sh            # コンテナ起動スクリプト
├── crontab                  # cron 設定ファイル
├── requirements.txt         # Python 依存パッケージ
├── .env                     # 環境変数設定（要作成）
├── .env.example             # 環境変数設定サンプル
├── .gitignore               # Git 除外設定
├── krd_sync_frequent.py     # 高頻度同期スクリプト（5分ごと）
├── krd_sync_hourly.py       # 低頻度同期スクリプト（1時間ごと）
├── krd_sqlite_helper.py     # SQLiteヘルパーモジュール
├── README_KRD_SYNC.md       # このファイル
├── db/
│   └── krd_machine.db       # SQLiteデータベース（自動作成）
└── logs/
    ├── log_frequent.txt     # 高頻度同期ログ（当日）
    ├── log_frequent_20251122.txt  # 過去の高頻度ログ
    ├── log_hourly.txt       # 低頻度同期ログ（当日）
    ├── log_hourly_20251122.txt    # 過去の低頻度ログ
    ├── cron_frequent.log    # cron 高頻度実行ログ
    └── cron_hourly.log      # cron 低頻度実行ログ
```

## 初回セットアップ（Docker推奨）

### 1. 環境変数ファイルの作成

```bash
cd /home/docker-user/docker-apps/10_krd_machine

# .env.exampleをコピーして.envを作成
cp .env.example .env

# 必要に応じて.envを編集（デフォルト値で動作します）
vi .env
```

**.env の設定項目:**
```bash
MYSQL_HOST=krd
MYSQL_DATABASE=machin
MYSQL_USER=pfw
MYSQL_PASSWORD=mejiriHoo
MYSQL_CHARSET=utf8
```

### 2. Dockerイメージのビルド

```bash
cd /home/docker-user/docker-apps/10_krd_machine
docker-compose build
```

### 3. コンテナの起動

```bash
# バックグラウンドで起動
docker-compose up -d

# ログを確認（リアルタイム）
docker-compose logs -f
```

**起動時の動作:**
- 高頻度同期（5テーブル）が即座に実行されます
- 低頻度同期（45テーブル）が即座に実行されます
- cronが起動し、5分ごと/1時間ごとに自動実行されます

### 4. 動作確認

```bash
# コンテナの状態確認
docker ps | grep krd-sync-app

# cron が動作しているか確認
docker exec krd-sync-app pgrep cron

# ログファイルの確認
docker exec krd-sync-app cat /app/logs/log_frequent.txt
docker exec krd-sync-app cat /app/logs/log_hourly.txt

# cronのログ確認
docker exec krd-sync-app cat /app/logs/cron_frequent.log
docker exec krd-sync-app cat /app/logs/cron_hourly.log

# データベースが作成されているか確認
docker exec krd-sync-app ls -lh /app/db/krd_machine.db
```

## 代替: 直接実行（非Docker）

Dockerを使用しない場合は、以下の手順で直接実行できます：

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
export MYSQL_HOST=krd
export MYSQL_DATABASE=machin
export MYSQL_USER=pfw
export MYSQL_PASSWORD=mejiriHoo
export MYSQL_CHARSET=utf8
```

### 3. 手動実行

```bash
cd /home/docker-user/docker-apps/10_krd_machine

# 高頻度同期の手動実行
python3 krd_sync_frequent.py

# 低頻度同期の手動実行
python3 krd_sync_hourly.py
```

### 4. cronへの登録（非Docker）

```bash
crontab -e
```

以下を追加：
```bash
# 環境変数を設定
MYSQL_HOST=krd
MYSQL_DATABASE=machin
MYSQL_USER=pfw
MYSQL_PASSWORD=mejiriHoo
MYSQL_CHARSET=utf8

# 高頻度同期（5分ごと）
*/5 * * * * cd /home/docker-user/docker-apps/10_krd_machine && python3 krd_sync_frequent.py >> /home/docker-user/docker-apps/10_krd_machine/logs/cron_frequent.log 2>&1

# 低頻度同期（1時間ごと）
0 * * * * cd /home/docker-user/docker-apps/10_krd_machine && python3 krd_sync_hourly.py >> /home/docker-user/docker-apps/10_krd_machine/logs/cron_hourly.log 2>&1
```

## 同期対象テーブル

### 高頻度同期テーブル（5個 - 5分ごと）

genpinhyoシステムで使用されているテーブル：

| テーブル名 | 説明 | 備考 |
|---|---|---|
| DATA_ASP2_PUT | ASP2投入データ | 伝票情報・工程Ver |
| MSTR_PROCODESTR | 工程コードマスタ | 工程コード→加工部番 |
| MSTR_METAL | メタルマスタ | 加工部番→メッキ情報 |
| DATA_RES_CAPA | 資源稼働データ | 負荷情報 |
| MSTR_RES | 資源マスタ | 資源情報 |

### 低頻度同期テーブル（45個 - 1時間ごと）

上記以外の全BASE TABLE（VIEWは除外）：

#### DATAテーブル（14個）
- DATA_ASP_PUT
- DATA_CALENDAR, DATA_JOB, DATA_JOB2, DATA_JOB_BakUp, DATA_JOB2_BK
- DATA_KOUTEIZUKAN
- DATA_LOT, DATA_LOT2, DATA_LOT2_BK
- DATA_NAT_CAL
- DATA_RES_END_PRO_0, DATA_RES2_END_PRO_0
- DATA_RESULTS_STOP, DATA_SUB_PUT
- DATA_UNREG_ITEM, DATA_UNREG_METAL

#### MSTRテーブル（9個）
- MSTR_JOB_VIEW_PNAME
- MSTR_KUMI_BEFO, MSTR_KUMI_MIDL
- MSTR_OPENAME
- MSTR_PROCESS
- MSTR_RES_GROUP, MSTR_RES_QRY, MSTR_RES_TYPE, MSTR_RES_WORKING
- MSTR_SHIFT

#### その他（22個）
- BAK_RES_CAPA
- KA_LIST01～KA_LIST12（12個）
- UNREGITEM_3LETTERS, UNREGITEM_DIFFINCH
- WORK_INSERT_RESCAPA, WORK_RES_CAPA, WORK_UPDATE_RESCAPA

※VIEWテーブルは処理が重いため、同期対象から除外しています。

## ログ形式

```
2025-11-22 10:15:00 - INFO - ================================================================================
2025-11-22 10:15:00 - INFO - KRD MySQL → SQLite 同期開始
2025-11-22 10:15:00 - INFO - ================================================================================
2025-11-22 10:15:00 - INFO - MySQL接続成功
2025-11-22 10:15:00 - INFO - SQLite接続成功: C:\Dev\90_tools\15_krd_machine\db\krd_machine.db
2025-11-22 10:15:01 - INFO - 取得したテーブル/VIEW数: 57
2025-11-22 10:15:01 - INFO - 処理中: DATA_ASP2_PUT (BASE TABLE)
2025-11-22 10:15:01 - INFO - テーブル DATA_ASP2_PUT を作成しました
2025-11-22 10:15:02 - INFO - テーブル DATA_ASP2_PUT: 54850件 同期完了
...
2025-11-22 10:20:30 - INFO - ================================================================================
2025-11-22 10:20:30 - INFO - 同期完了サマリー
2025-11-22 10:20:30 - INFO - 成功: 57 テーブル
2025-11-22 10:20:30 - INFO - 失敗: 0 テーブル
2025-11-22 10:20:30 - INFO - 総レコード数: 123,456 件
2025-11-22 10:20:30 - INFO - ================================================================================
```

## トラブルシューティング

### MySQL接続エラー

```
ERROR - MySQL接続失敗: (2003, "Can't connect to MySQL server on 'krd'")
```

**対処法**:
- KRD MySQLサーバーが起動しているか確認
- ネットワーク接続を確認
- ホスト名 `krd` が名前解決できるか確認

### SQLite書き込みエラー

```
ERROR - SQLite接続失敗: database is locked
```

**対処法**:
- 他のプロセスがSQLiteファイルを開いていないか確認
- タスクスケジューラで複数のタスクが同時実行されていないか確認

### データ型エラー

```
ERROR - テーブル XXX のデータ同期失敗: ...
```

**対処法**:
- ログの詳細を確認
- 必要に応じて `mysql_to_sqlite_type()` 関数のデータ型マッピングを調整

## メンテナンス（Docker）

### コンテナの再起動

```bash
cd /home/docker-user/docker-apps/10_krd_machine

# コンテナの再起動
docker-compose restart

# コンテナの停止
docker-compose down

# コンテナの再ビルド＆起動（コード変更時）
docker-compose down && docker-compose build && docker-compose up -d
```

### ログの確認

```bash
# コンテナログの確認
docker-compose logs -f

# Pythonスクリプトのログ確認
docker exec krd-sync-app tail -f /app/logs/log_frequent.txt
docker exec krd-sync-app tail -f /app/logs/log_hourly.txt

# cronのログ確認
docker exec krd-sync-app tail -f /app/logs/cron_frequent.log
docker exec krd-sync-app tail -f /app/logs/cron_hourly.log
```

### ログの手動削除

```bash
# 7日より古いログを削除（コンテナ内で実行）
docker exec krd-sync-app find /app/logs -name "log_*.txt" -type f -mtime +7 -delete
```

### SQLiteデータベースの再作成

```bash
# コンテナ内のDBを削除
docker exec krd-sync-app rm -f /app/db/krd_machine.db

# 手動で同期を実行
docker exec krd-sync-app python3 /app/krd_sync_frequent.py
docker exec krd-sync-app python3 /app/krd_sync_hourly.py
```

### 環境変数の変更

```bash
# .envファイルを編集
cd /home/docker-user/docker-apps/10_krd_machine
vi .env

# 変更を反映するため、再ビルド＆再起動が必要
docker-compose down && docker-compose build && docker-compose up -d
```

### コンテナの完全削除

```bash
cd /home/docker-user/docker-apps/10_krd_machine

# コンテナとイメージを削除
docker-compose down --rmi all

# データは保持される（./db/ と ./logs/ はホスト側に残る）
```

## 注意事項

1. **一方向同期**: SQLite側でデータを変更しても、MySQLには反映されません
2. **全件置き換え**: 同期のたびに全データが置き換えられます（差分更新ではありません）
3. **VIEW**: VIEWはスナップショットとして物理化されるため、元のVIEW定義とは異なります
4. **データ型**: MySQLからSQLiteへの変換で一部のデータ型が変更される場合があります

## 更新履歴

| 日付 | 内容 |
|---|---|
| 2025-11-22 | 初版作成 |
| 2025-11-22 | ファイル配置変更（C:\Dev\90_tools\15_krd_machine に移行）<br>Linux cron対応（Windows Task Scheduler → cron）<br>DATA_KOUTEIZUKANを高頻度→低頻度同期に変更（5分→1時間）<br>高頻度テーブル数: 6→5、低頻度テーブル数: 44→45 |
| 2025-11-22 | Docker化対応<br>- Dockerfile、docker-compose.yml、entrypoint.sh、crontab 追加<br>- 環境変数対応（.env ファイルで設定管理）<br>- Python 3.12 + cron によるコンテナ化<br>- 起動時即時同期 + 定期実行（5分/1時間） |
