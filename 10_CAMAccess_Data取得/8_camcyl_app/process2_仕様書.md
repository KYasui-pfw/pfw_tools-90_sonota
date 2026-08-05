# process2.py 仕様書

## 概要

ネットワークドライブ上のMicrosoft Access データベース（.accdb）からテーブルを抽出し、CSV形式で出力する処理です。

---

## 入力ファイル

| ファイル | 環境変数 | 抽出テーブル |
|----------|----------|--------------|
| Cyl_pfw_table.accdb | ACCDB_SOURCE1 | KaLstCyl_All（+ ジョブテーブルとLEFT JOIN） |
| EJデータマスター.accdb | ACCDB_SOURCE2 | CAMFIN_LOG_ALL |

---

## 出力ファイル

| 入力DB | 出力CSV | 説明 |
|--------|---------|------|
| Cyl_pfw_table.accdb | Cyl_pfw_table_KaLstCyl_All.csv | シリンダ/ダイアル製造データ |
| EJデータマスター.accdb | EJデータマスター_CAMFIN_LOG_ALL.csv | EJ完了実績データ |

---

## 処理フロー

```
1. ネットワークドライブからAccess DBをコンテナ内(/app/data/)にコピー
       ↓
2. UCanAccess JDBCドライバでAccess DBに接続
       ↓
3. テーブル抽出（必要に応じてLEFT JOIN実行）
       ↓
4. CSV形式で出力（UTF-8-sig）
       ↓
5. 処理結果サマリーをログ出力
```

---

## LEFT JOIN処理

### 対象

Cyl_pfw_table.accdb の KaLstCyl_All テーブルのみ

### 結合条件

```sql
SELECT t1.*, t2.*
FROM [KaLstCyl_All] AS t1
LEFT JOIN [ジョブ] AS t2
ON t1.KUMITATENO_Job = t2.lotCode
```

### 目的

KaLstCyl_All テーブルの組立番号（KUMITATENO_Job）をキーに、ジョブテーブルから関連データを結合する。

---

## UCanAccess技術詳細

### 概要

Microsoft Access なしでAccess データベースを読み込むためのJava JDBCドライバです。

### 必須JARファイル

| ファイル | 説明 |
|----------|------|
| ucanaccess-5.0.1.jar | メインドライバ |
| jackcess-3.0.1.jar | Access DBパーサー |
| hsqldb-2.5.0.jar | 内部SQL処理 |
| commons-lang3-3.8.1.jar | 共通ユーティリティ |
| commons-logging-1.2.jar | ロギング |

### JDBC接続文字列

```
jdbc:ucanaccess://{db_path}
```

### Python連携

```python
import jaydebeapi

conn = jaydebeapi.connect(
    'net.ucanaccess.jdbc.UcanaccessDriver',
    f'jdbc:ucanaccess://{db_path}',
    {},
    jars=classpath
)
```

---

## テストモード

開発・テスト用に、`_test.accdb` ファイルが存在する場合は優先使用されます。

| 本番ファイル | テストファイル |
|--------------|----------------|
| Cyl_pfw_table.accdb | Cyl_pfw_table_test.accdb |
| EJデータマスター.accdb | EJデータマスター_test.accdb |

テストファイルは `/app/data/` ディレクトリに配置します。

---

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| ACCDB_SOURCE1 | Cyl_pfw_table.accdb パス | （必須） |
| ACCDB_SOURCE2 | EJデータマスター.accdb パス | （必須） |
| TABLE1_NAME | 抽出テーブル名（DB1） | KaLstCyl_All |
| TABLE2_NAME | 抽出テーブル名（DB2） | CAMFIN_LOG_ALL |
| JOB_TABLE_NAME | LEFT JOINするジョブテーブル名 | ジョブ |
| OUTPUT_PREFIX1 | 出力ファイル名プレフィックス（DB1） | Cyl_pfw_table |
| OUTPUT_PREFIX2 | 出力ファイル名プレフィックス（DB2） | EJデータマスター |
| OUTPUT_DIR_JISSEKI | 出力先ディレクトリ | /app/output/KakouJisseki |
| LOG_DIR | ログ出力先 | /app/logs |
| LOG_RETENTION_DAYS | ログ保持日数 | 7 |

---

## 注意事項

### ネットワークドライブ

- ホスト側で `/etc/fstab` によるマウント設定が必要
- Docker コンテナ内では `/mnt/schejule` にマウント
- 読み取り専用（`:ro`）でマウント推奨

### Java実行環境

- Dockerイメージに `default-jdk-headless` がインストールされている必要あり
- UCanAccess JARファイルは `/app/ucanaccess_lib/` に配置

### エンコーディング

- 出力: UTF-8-sig（BOM付きUTF-8）

---

## 実行タイミング

- 15分ごと（cron）
- process1.py と並列実行

---

## ログ出力

- ファイル: `process2_YYYYMMDD.log`
- 場所: `/app/logs/`
- 保持期間: 7日間（自動削除）

### ログ出力例

```
[1/2] データベースに接続しています: Cyl_pfw_table.accdb
  ✓ コピー完了: Cyl_pfw_table.accdb (15,728,640 bytes)
  テーブル 'KaLstCyl_All' を処理中...
  ジョブテーブル 'ジョブ' とLEFT JOINを実行中...
  ✓ 12,345件のデータを出力しました: Cyl_pfw_table_KaLstCyl_All.csv (2,048,576 bytes)

[2/2] データベースに接続しています: EJデータマスター.accdb
  ✓ コピー完了: EJデータマスター.accdb (8,192,000 bytes)
  テーブル 'CAMFIN_LOG_ALL' を処理中...
  ✓ 5,678件のデータを出力しました: EJデータマスター_CAMFIN_LOG_ALL.csv (512,000 bytes)
```

---

## 関連ファイル

| ファイル | 説明 |
|----------|------|
| process2.py | メイン処理スクリプト |
| logger_config.py | ロギング設定モジュール |
| ucanaccess_lib/ | UCanAccess JARファイル群 |
| run_all.sh | 全処理実行ラッパー |
