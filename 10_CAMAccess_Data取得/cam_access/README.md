# Access Database to CSV Converter (Docker版)

UCanAccessを使ってAccessデータベース(.accdb)内の**全テーブル**を自動的に読み取り、**項目名付きのCSVファイル**として一括出力するDockerアプリケーションです。

## 主な機能

- データベース内の全テーブルを自動検出
- 各テーブルを個別のCSVファイルとして出力（ファイル名: `テーブル名.csv`）
- 項目名（カラム名）を含むCSV形式で出力
- システムテーブル（MSysで始まるテーブル）を自動除外
- 処理結果のサマリー表示（成功/失敗件数）

## フォルダ構成

```
cam_access/
├── Dockerfile              # Dockerイメージの設計図
├── requirements.txt        # Pythonのライブラリリスト
├── app.py                  # メインの処理スクリプト
├── README.md               # このファイル
│
├── ucanaccess_lib/         # UCanAccessのjarファイルを入れるフォルダ
│   ├── ucanaccess-5.0.1.jar
│   ├── commons-lang3-3.8.1.jar
│   ├── commons-logging-1.2.jar
│   ├── hsqldb-2.5.0.jar
│   └── jackcess-3.0.1.jar
│
├── data/                   # 入力となるAccess DBを置く場所
│   └── your_database.accdb
│
└── output/                 # 出力されるCSVが保存される場所 (実行時に自動作成)
    ├── テーブル1.csv
    ├── テーブル2.csv
    └── テーブル3.csv
```

## 事前準備

### 1. UCanAccessライブラリのダウンロード

[UCanAccess公式サイト](http://ucanaccess.sourceforge.net/site.html)から最新版をダウンロードし、以下の5つの.jarファイルを`ucanaccess_lib/`フォルダにコピーしてください。

- ucanaccess-5.0.1.jar
- commons-lang3-3.8.1.jar
- commons-logging-1.2.jar
- hsqldb-2.5.0.jar
- jackcess-3.0.1.jar

### 2. Accessデータベースファイルの配置

変換したいAccessデータベースファイル(.accdb)を`data/`フォルダに配置してください。

## 使用方法

### ビルド (イメージの作成)

PowerShellまたはコマンドプロンプトで、`cam_access`フォルダに移動して以下のコマンドを実行します。

```bash
cd C:\Dev\90_tools\10_CAMAccess_Data取得\cam_access
docker build -t access-to-csv .
```

### 実行 (コンテナの起動)

#### Windows (Git Bash) での実行方法

Windows環境でGit Bashを使用する場合、パス変換を無効化する必要があります：

```bash
# 基本的な実行（デフォルトのyour_database.accdbを使用）
MSYS_NO_PATHCONV=1 docker run --rm \
  -v /c/Dev/90_tools/10_CAMAccess_Data取得/cam_access/data:/app/data \
  -v /c/Dev/90_tools/10_CAMAccess_Data取得/cam_access/output:/app/output \
  access-to-csv

# 特定のデータベースファイルを指定
MSYS_NO_PATHCONV=1 docker run --rm \
  -v /c/Dev/90_tools/10_CAMAccess_Data取得/cam_access/data:/app/data \
  -v /c/Dev/90_tools/10_CAMAccess_Data取得/cam_access/output:/app/output \
  -e DB_FILE=EJデータマスター.accdb \
  access-to-csv
```

**重要**: パスは自分の環境に合わせて変更してください。`/c/Dev/...`は`C:\Dev\...`に対応します。

#### PowerShell での実行方法

PowerShellを使用する場合：

```powershell
# カレントディレクトリを使用
docker run --rm `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/output:/app/output `
  -e DB_FILE=EJデータマスター.accdb `
  access-to-csv
```

#### Linux / macOS での実行方法

```bash
# 相対パスで実行
docker run --rm -v ./data:/app/data -v ./output:/app/output access-to-csv

# データベースファイルを指定
docker run --rm \
  -v ./data:/app/data \
  -v ./output:/app/output \
  -e DB_FILE=your_database.accdb \
  access-to-csv
```

### コマンドオプションの説明

- `--rm`: コンテナの処理が終わったら自動的に削除します
- `-v <ホストパス>:/app/data`: PC上のdataフォルダをコンテナ内の/app/dataフォルダにマウント
- `-v <ホストパス>:/app/output`: PC上のoutputフォルダをコンテナ内の/app/outputフォルダにマウント
- `-e DB_FILE=xxx`: データベースファイル名を指定（デフォルト: your_database.accdb）
- `MSYS_NO_PATHCONV=1`: Git Bash環境でのパス自動変換を無効化（Windowsのみ必要）

### 実行結果の例

```
データベースに接続しています: /app/data/EJデータマスター.accdb
接続に成功しました。

検出されたテーブル数: 5
テーブル一覧: 顧客マスタ, 商品マスタ, 受注データ, 出荷データ, 在庫管理

[1/5] テーブル '顧客マスタ' を処理中...
  ✓ 150件のデータを出力しました: 顧客マスタ.csv
[2/5] テーブル '商品マスタ' を処理中...
  ✓ 320件のデータを出力しました: 商品マスタ.csv
[3/5] テーブル '受注データ' を処理中...
  ✓ 1250件のデータを出力しました: 受注データ.csv
[4/5] テーブル '出荷データ' を処理中...
  ✓ 980件のデータを出力しました: 出荷データ.csv
[5/5] テーブル '在庫管理' を処理中...
  ✓ 450件のデータを出力しました: 在庫管理.csv

=== 処理完了 ===
成功: 5テーブル
失敗: 0テーブル
出力先: /app/output
```

## Linuxサーバーへの移行

### 方法1: Docker Hubを使う (推奨)

#### Windowsで:

```bash
docker login
docker tag access-to-csv yourusername/access-to-csv:latest
docker push yourusername/access-to-csv:latest
```

#### Linuxサーバーで:

```bash
docker pull yourusername/access-to-csv:latest
docker run --rm -v ./data:/app/data -v ./output:/app/output yourusername/access-to-csv:latest
```

### 方法2: イメージをファイルとして保存・ロードする

#### Windowsで:

```bash
docker save -o access-to-csv.tar access-to-csv
```

`access-to-csv.tar`ファイルをSCPなどでLinuxサーバーに転送します。

#### Linuxサーバーで:

```bash
docker load -i access-to-csv.tar
docker run --rm -v ./data:/app/data -v ./output:/app/output access-to-csv
```

## トラブルシューティング

### エラー: "データベースに接続できません"

- `data/`フォルダに正しいAccessデータベースファイルが配置されているか確認してください
- 環境変数`DB_FILE`の値が正しいか確認してください
- データベースファイルが破損していないか確認してください

### テーブルが1つも検出されない

- Accessデータベースにユーザーテーブルが含まれているか確認してください
- システムテーブル（MSysで始まるテーブル）のみの場合は出力されません

### 一部のテーブルで処理が失敗する

- 処理結果のサマリーで失敗したテーブルを確認してください
- 特定のテーブルにアクセス権限の問題や破損がある可能性があります
- エラーメッセージの詳細をログで確認してください

### 出力ファイルが生成されない

- `output/`フォルダの権限を確認してください
- コンテナのログを確認してエラーメッセージを確認してください
- Docker Desktopのボリュームマウントが正しく設定されているか確認してください

## 技術仕様

- **Python**: 3.12.0
- **ベースイメージ**: python:3.12.0-slim-bullseye
- **Java**: default-jdk-headless
- **主要ライブラリ**:
  - JayDeBeApi (JDBC接続)
  - pandas (データ処理・CSV出力)

## 仕様メモ
- シリンダ課のAccess
  - Cyl_pfw_table.accdb 
  - KaLstCyl_Allテーブルの"JOB_7"が完成日。ここに日付が入れば送信対象。
  - KaLstCyl_Allテーブルの"DENPYONO"が伝票番号（社内指示番号）。フィールドサイズが20桁なので、社内指示番号＋行番号を一つの項目にまとめることで対応可能。
  - シリンダは今も工程毎に伝票番号が出ている
- カム課のAccess
  - EJデータマスター.accdb
  - CAMFIN_LOG_ALLテーブルから実績を取得する。
  - SRNO=社内指示番号、FINUM=完了数、DATE=完了日（実績報告日）なので、これで送信する