# PostgreSQL データ取得処理

## 概要

PostgreSQL データベース (irepodb) の `view_report_405` から機械データを取得し、FastAPI rBOMシステムに自動送信する統合処理です。

## 処理内容

**統合処理フロー (machine_data_extract.py):**

1. **PostgreSQL データ取得**
   - データソース: `view_report_405` (PostgreSQL irepodb)
   - 取得カラム数: 107列
     - `cluster_1_2_t` (1列)
     - `cluster_1_24_n` ～ `cluster_1_636_n` (52列、12刻み、末尾 _n)
     - `cluster_1_14_t` ～ `cluster_1_626_t` (52列、12刻み+2、末尾 _t)
     - `cluster_1_641_t` (1列)
     - `top_remarks3` (1列)

2. **デバッグ用CSV出力（オプション）**
   - 環境変数 `ENABLE_CSV_OUTPUT=true` の場合のみ出力
   - ファイル名: `machine_data_YYYYMMDD_HHMMSS.csv`
   - エンコーディング: UTF-8 BOM付き
   - 出力先: `./output/`

3. **データフィルタリング（共通）**
   - `top_remarks3` で当月・翌月・翌々月のデータを抽出

4. **パターン分岐処理**
   - **パターン1**: `cluster_1_24_n` ～ `cluster_1_636_n` のいずれかが `1.0` の行を抽出 → LINENO=1のみ送信
   - **パターン3**: `cluster_1_641_t` が `'2'` または `'4'` の行を抽出 → 全LINENO送信

5. **FastAPI送信**
   - **パターン1（バッチ処理）**:
     - 全INDNOリストを作成（LINENO=1固定）
     - `/instructions/slip/batch` で一括取得（1回のAPI呼び出し）
     - 必要な4項目のみキャッシュ（STATUS, SYORIZUMIKB, EDKKBN, THQTY）
     - **パフォーマンス**: 500件の場合、500回 → 1回のAPI呼び出しに削減

   - **パターン3（月次取得）**:
     - 対象月を抽出（当月・翌月・翌々月）
     - 各月ごとに `/instructions/?year=YYYY&month=MM` で全件取得（最大3回のAPI呼び出し）
     - INDNO別に全LINENOをグループ化
     - 各LINENO×送信可否チェック→送信

   - 状態チェックして送信可能なデータのみ `completion` エンドポイントに送信

**データマッピング（パターン1・パターン3共通）:**
- `KTEDDT` ← システム日付（日本時間、YYYY-MM-DD形式）
- `INDNO` ← `cluster_1_2_t`
- `lineno` ← パターン1: 固定値 `1` / パターン3: APIから取得した各LINENO
- `IPTANCD` ← 固定値 `"SECT1557"`
- `prdqty` ← GET取得した `THQTY`
- `ktedqty` ← `prdqty` と同じ値

**送信可否ロジック:**
- 完納済み（EDKKBN='1'/'2'）→ 送信不可
- 完了状態（STATUS='3'/'4'/'8'）→ 送信不可
- 中止（STATUS='9'）→ 送信不可
- 実績登録中（SYORIZUMIKB='1'）→ 送信不可
- 登録エラー（SYORIZUMIKB='3'）または未完了 → 送信可能

**ログ管理:**
- **ファイル名**: `machine_extract_YYYYMMDD.log`
- **ローテーション**: 日次（深夜0時）
- **保持期間**: 7日間
- **出力先**: `./logs/`

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd C:\Dev\90_tools\13_machine
pip install -r requirements.txt
```

**必要パッケージ**:
- sqlalchemy
- psycopg2-binary
- pandas
- python-dotenv

### 2. 環境変数の設定

`.env` ファイルで設定を確認・変更：

```ini
# PostgreSQL Database Configuration
DB_URL=postgresql://postgres:cimtops@ESRV10/irepodb

# Output Directory
OUTPUT_DIR=./output

# Log Directory
LOG_DIR=./logs

# Log Retention Days
LOG_RETENTION_DAYS=7

# FastAPI Configuration
FASTAPI_BASE_URL=http://127.0.0.1:8000
READ_API_KEY=your_read_api_key_here
INSERT_API_KEY=your_insert_api_key_here

# Debug Configuration
ENABLE_CSV_OUTPUT=false
```

**重要**:
- `READ_API_KEY` と `INSERT_API_KEY` は実際のAPIキーに置き換えてください。
- `ENABLE_CSV_OUTPUT=true` に設定すると、デバッグ用にCSVファイルが出力されます（通常は不要）

## 実行方法

### 手動実行

```bash
# 統合処理を実行（データ取得 → FastAPI送信）
python machine_data_extract.py

# バッチファイル経由
machine_data_extract.bat
```

### 定期実行（タスクスケジューラ）

#### タスクの作成

1. **タスクスケジューラ**を開く
2. **タスクの作成** をクリック
3. **全般**タブ:
   - 名前: `PostgreSQL Machine Data Extract`
   - 説明: `irepodb から機械データを15分ごとに取得`
   - セキュリティオプション: `ユーザーがログオンしているかどうかにかかわらず実行する`

4. **トリガー**タブ:
   - **新規** をクリック
   - 開始: 毎日
   - 開始時刻: `00:00:00`
   - 詳細設定:
     - ☑ **繰り返し間隔**: `15分間`
     - **継続時間**: `無期限`
     - ☑ **有効**

5. **操作**タブ:
   - **新規** をクリック
   - 操作: `プログラムの開始`
   - プログラム/スクリプト: `C:\Dev\90_tools\13_machine\machine_data_extract.bat`
   - 開始: `C:\Dev\90_tools\13_machine`

6. **条件**タブ:
   - ☐ コンピューターをAC電源で使用している場合のみタスクを開始する（チェックを外す）
   - ☐ コンピューターの電源をバッテリに切り替える場合は停止する（チェックを外す）

7. **設定**タブ:
   - ☑ タスクが失敗した場合の再起動の間隔: `1分間`
   - ☑ 最大試行回数: `3回`

#### タスクのテスト

```bash
# タスクスケジューラから手動実行してテスト
# ログを確認: C:\Dev\90_tools\13_machine\logs\machine_extract_YYYYMMDD.log
# 出力を確認: C:\Dev\90_tools\13_machine\output\machine_data_YYYYMMDD_HHMMSS.csv
```

## ディレクトリ構造

```
C:\Dev\90_tools\13_machine\
├── .env                        # 環境変数設定
├── requirements.txt            # Pythonパッケージ
├── machine_data_extract.py     # 統合処理スクリプト（DB取得→FastAPI送信）
├── machine_data_extract.bat    # 実行用バッチファイル
├── check_columns.py            # カラム確認ユーティリティ
├── README.md                   # このファイル
├── logs/                       # ログ出力先
│   └── machine_extract_YYYYMMDD.log
└── output/                     # CSV出力先（デバッグ用）
    └── machine_data_YYYYMMDD_HHMMSS.csv
```

## トラブルシューティング

### データベース接続エラー

```
エラー: (psycopg2.OperationalError) could not connect to server
```

**対処法**:
- ESRV10 サーバーへの疎通確認
- PostgreSQL サービス起動確認
- 認証情報（ユーザー名・パスワード）確認

### モジュールが見つからない

```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**対処法**:
```bash
pip install -r requirements.txt
```

### デバッグ用CSVファイルを出力したい

`.env` ファイルで以下を設定：
```ini
ENABLE_CSV_OUTPUT=true
```

再度実行すると、`./output/machine_data_YYYYMMDD_HHMMSS.csv` が出力されます。

### FastAPI送信が失敗する

**確認項目**:
1. ログファイルでエラー確認: `./logs/machine_send_YYYYMMDD.log`
2. FastAPIサーバーが起動しているか確認
3. `.env` の `FASTAPI_BASE_URL` が正しいか確認
4. `.env` の `READ_API_KEY` と `INSERT_API_KEY` が正しいか確認
5. ネットワーク疎通確認: `curl http://127.0.0.1:8000/`

### 送信対象データが0件

**確認項目**:
1. `top_remarks3` が当月・翌月・翌々月のデータか確認
2. `cluster_1_24_n` ～ `cluster_1_636_n` のいずれかに `1.0` が入っているか確認
3. ログで除外理由を確認（送信不可状態、指示データ取得失敗など）

### タスクスケジューラで実行されない

**確認項目**:
1. タスクの**最終実行結果**を確認（0x0 = 成功）
2. タスクの**履歴**タブで実行ログ確認
3. バッチファイルを手動実行してエラー確認
4. 実行アカウントの権限確認

## 仕様

- **Python**: 3.12以上推奨
- **PostgreSQL**: 9.6以上
- **FastAPI**: rBOMシステムとの連携
- **OS**: Windows Server 2016以降
- **実行頻度**: 15分ごと（カスタマイズ可能）
- **タイムゾーン**: 日本時間（JST, UTC+9）

## 今後の拡張

- ✅ CSV中間ファイルの削除と2スクリプトの統合（完了）
- 2パターン目のロジック追加予定
- データ加工・変換処理の追加
- 異常値検知・アラート通知
