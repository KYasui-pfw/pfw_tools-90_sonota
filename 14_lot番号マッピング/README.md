# ロット番号マッピングツール

PostgreSQL/CSVファイルからロット番号データを取得し、FastAPIから取得した指示データとマッピングするStreamlitアプリケーションです。

## 機能概要

### データ取得機能
- PostgreSQLから以下のテーブルデータを自動取得
  - `view_report_405` (汎用ランニングチェックシート)
  - `view_report_334` (ダイヤルキャップ)
- CSVファイルから以下のデータを自動取得
  - `Cyl_pfw_table_KaLstCyl_All.csv`
- FastAPI (http://pfw-api) から指示データを自動取得
  - 対象期間: 2025/11～2026/02
  - 取得項目: INDNO, HMCD, SEINO, KTCD

### 取得対象外データ
以下のデータは取得しません：
- **CAM加工伝票** (`4-01 CAMKakouDenpyo.csv`): 全ての実績を一括返却する運用に変更されたため
- **月次**: 2024年10月〜2025年11月のデータ（202410〜202511, 2410〜2511 始まり）
- **組立番号**: "L"始まり、"K"始まりのデータ

### マッピング機能
- **自動マッピング**: 品目コード=HMCD かつ 組立番号=SEINO で自動マッピング
- **手動マッピング**: ロット番号とSEINOを手動で紐付け
- **マッピング結果表示**: ロット番号と指示番号(INDNO)の対応関係を表示

### その他の機能
- SQLiteデータベースへの重複なし保存
- データ一覧表示（フィルター・検索機能付き）
- CSVエクスポート機能
- マルチページ構成（メイン・手動マッピング・マッピング結果）

## データ取得項目

### view_report_405（PostgreSQL）
- **ロット番号**: cluster_1_2_t
- **品目コード**: cluster_1_3_t
- **組立番号**: cluster_1_5_t
- **月次**: cluster_1_4_t（YYYYMMX形式）

### view_report_334（PostgreSQL）
- **ロット番号**: cluster_1_0_t
- **品目コード**: cluster_1_3_t
- **組立番号**: cluster_1_4_t
- **月次**: cluster_1_2_t（YYYYMMX形式）

### Cyl_pfw_table_KaLstCyl_All.csv
- **ロット番号**: DENPYONO
- **品目コード**: SETU_F
- **組立番号**: KUMITATENO
- **月次**: SEISANJI（YYMMX形式）
- **ソースパス**: `\\esrv11\KakouJisseki\Cyl_pfw_table_KaLstCyl_All.csv`

### FastAPI指示データ
- **API URL**: http://pfw-api/instructions/
- **取得項目**:
  - **INDNO**: 指示番号
  - **HMCD**: 品目コード
  - **SEINO**: 製番（25または26から始まる場合は最後の4文字のみ取得）
  - **KTCD**: 工程コード
- **対象期間**: 2025年11月～2026年2月
- **認証**: X-API-KEY ヘッダー（READ_API_KEY使用）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルに以下の設定が含まれています：

```env
# PostgreSQL Database Configuration
DB_URL=postgresql://postgres:cimtops@ESRV10/irepodb

# SQLite Database Configuration
SQLITE_DB_PATH=./db/lot_mapping.db

# CSV Data Sources
CYL_CSV_SOURCE=\\esrv11\KakouJisseki\Cyl_pfw_table_KaLstCyl_All.csv

# Data Directory
DATA_DIR=./data

# Log Directory
LOG_DIR=./logs

# Log Retention Days
LOG_RETENTION_DAYS=7
```

## 起動方法

### 方法1: バッチファイル（推奨）

```cmd
start_app.bat
```

### 方法2: Streamlitコマンド

```bash
streamlit run app.py --server.headless true --server.port 8511
```

## アクセス

アプリケーション起動後、ブラウザで以下のURLにアクセスします：

```
http://localhost:8511
```

## 機能詳細

### 自動データ更新

アプリケーションを起動すると、自動的に以下の処理を実行します：

1. **CSVファイルのコピー**: ネットワーク上のCSVファイルをdataフォルダにコピー（上書き）
2. **入力データ取得**: PostgreSQLとCSVファイルからロット番号データを取得
3. **APIデータ取得**: FastAPIから指示データ（INDNO, HMCD, SEINO, KTCD）を取得
4. **自動マッピング実行**: 品目コード=HMCD かつ 組立番号=SEINO でマッピング
5. **手動マッピング実行**: manual_mappingsテーブルの設定を使用してマッピング
6. **結果表示**: 新規追加件数とマッピング結果を画面に表示

### データ表示

- 統計情報
  - 総件数
  - データソース別件数（view_report_405、view_report_334、Cyl CSV）
  - ユニークロット番号数
- データフィルター機能
  - データソース選択（3種類のソースから選択可能）
  - 月次選択
  - ロット番号検索
- データ一覧表示（テーブル形式）

### CSVエクスポート

フィルター適用後のデータをCSV形式でダウンロード可能です。

## データベース構造

### 1. lot_mapping_data (入力データ)

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| id | INTEGER | 主キー（自動採番） |
| lot_number | TEXT | ロット番号 |
| item_code | TEXT | 品目コード |
| assembly_number | TEXT | 組立番号 |
| month | TEXT | 月次（YYYYMMX、YYMMX形式など） |
| data_source | TEXT | データソース（view_report_405 / view_report_334 / Cyl_pfw_table_KaLstCyl_All） |
| created_at | TIMESTAMP | 登録日時 |

**ユニーク制約**: (lot_number, item_code, assembly_number, month, data_source)

### 2. api_instructions (APIから取得した指示データ)

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| id | INTEGER | 主キー（自動採番） |
| indno | TEXT | 指示番号 |
| hmcd | TEXT | 品目コード |
| seino | TEXT | 製番（処理済み） |
| seino_original | TEXT | 製番（元データ） |
| ktcd | TEXT | 工程コード |
| created_at | TIMESTAMP | 登録日時 |

**ユニーク制約**: (indno, hmcd, seino, ktcd)

### 3. mapping_results (マッピング結果)

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| id | INTEGER | 主キー（自動採番） |
| lot_number | TEXT | ロット番号 |
| indno | TEXT | 指示番号 |
| item_code | TEXT | 品目コード |
| assembly_number | TEXT | 組立番号 |
| hmcd | TEXT | HMCD |
| seino | TEXT | SEINO |
| mapping_type | TEXT | マッピング種別（auto/manual） |
| created_at | TIMESTAMP | 登録日時 |

**ユニーク制約**: (lot_number, indno)

### 4. manual_mappings (手動マッピング設定)

| カラム名 | データ型 | 説明 |
|---------|---------|------|
| id | INTEGER | 主キー（自動採番） |
| lot_number | TEXT | ロット番号 |
| seino | TEXT | SEINO（組立番号） |
| created_at | TIMESTAMP | 登録日時 |
| updated_at | TIMESTAMP | 更新日時 |

**ユニーク制約**: (lot_number, seino)

## ログ

アプリケーションのログは `./logs/log_YYYYMMDD.txt` に出力されます。

- データ取得処理の実行状況
- エラー情報
- 新規追加件数

## ページ構成

### メインページ（app.py）
- 入力データの表示と統計情報
- データ取得とマッピング処理の自動実行
- フィルター・検索機能
- CSVエクスポート

### 手動マッピングページ
- ロット番号とSEINOの手動紐付け
- 登録済みマッピングの一覧表示
- マッピングの追加・削除機能

### マッピング結果ページ
- ロット番号とINDNOの対応関係表示
- 自動/手動マッピングの区別
- フィルター・検索機能
- CSVエクスポート

## マッピングロジック

### 自動マッピング
```sql
品目コード = HMCD AND 組立番号 = SEINO
```
入力データとAPIデータの品目コードと組立番号が一致した場合、自動的にマッピングされます。

### 手動マッピング
```sql
manual_mappings.lot_number = lot_mapping_data.lot_number
AND manual_mappings.seino = api_instructions.seino
```
手動マッピングテーブルで設定したロット番号とSEINOの組み合わせでマッピングされます。自動マッピングと重複する場合は、自動マッピングが優先されます。

### SEINO処理ルール
- 25または26から始まる文字列: 最後の4文字のみ取得
  - 例: "251234" → "1234"
  - 例: "262345" → "2345"
- その他の文字列: そのまま使用
  - 例: "K001" → "K001"

## 注意事項

- PostgreSQLサーバー（ESRV10）への接続が必要です
- FastAPI（http://pfw-api）への接続が必要です
- ネットワーク共有フォルダ（\\esrv11）へのアクセス権が必要です
- 初回起動時にSQLiteデータベースとdataフォルダが自動作成されます
- データは起動時に毎回取得・更新されます
- マッピング結果は起動時に再計算されます（既存のマッピング結果はクリアされます）
- 重複データは自動的にスキップされます
- CSVファイルは起動時にdataフォルダにコピーされます（上書き）

## トラブルシューティング

### PostgreSQL接続エラー

- ネットワーク接続を確認してください
- データベースサーバー（ESRV10）が稼働しているか確認してください
- 認証情報が正しいか確認してください

### CSVファイルコピーエラー

- ネットワーク共有フォルダへのアクセス権があるか確認してください
- CSVファイルが以下のパスに存在するか確認してください：
  - `\\esrv11\KakouJisseki\Cyl_pfw_table_KaLstCyl_All.csv`
- ログファイルでエラー詳細を確認してください

### データが取得できない

- ログファイル（`./logs/log_YYYYMMDD.txt`）を確認してください
- PostgreSQLのview_report_405とview_report_334のテーブルが存在するか確認してください
- CSVファイルのカラム名が正しいか確認してください
  - Cyl CSV: DENPYONO, SETU_F, KUMITATENO, SEISANJI

## 今後の拡張予定

現在は基本的なデータ取得・表示機能のみ実装されています。今後、以下の機能を追加予定です：

- データ編集機能
- マッピング設定機能
- データエクスポート形式の追加
- 検索機能の強化
- データ分析・可視化機能
