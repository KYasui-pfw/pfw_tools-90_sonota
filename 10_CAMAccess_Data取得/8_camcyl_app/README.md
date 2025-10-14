# CAM/CYL Access データベース抽出アプリケーション

## 概要

このアプリケーションは、以下のタイミングで処理を自動実行します：

- **起動時**: コンテナ起動直後に1回実行
- **定期実行**: 15分ごとに自動実行

**処理内容**:

1. **処理1**: rBOMディレクトリからCSVファイルをコピー・加工
2. **処理2**: ネットワークドライブ上のAccess DBからCSVを抽出

※処理1と処理2は並列実行されます

## ディレクトリ構造

```
8_camcyl_app/
├── Dockerfile              # Python + Java + cron環境
├── docker-compose.yml      # コンテナ定義
├── entrypoint.sh           # エントリーポイント（起動時処理）
├── .env.example            # 環境変数テンプレート
├── .env                    # 環境変数（要作成）
├── requirements.txt        # Pythonライブラリ
├── crontab                 # cron設定ファイル
├── scripts/                # 処理スクリプト
│   ├── process1.py        # rBOM CSVコピー・加工
│   ├── process2.py        # Access DB → CSV抽出
│   ├── logger_config.py   # ログ設定
│   └── run_all.sh         # 全処理実行ラッパー
├── ucanaccess_lib/        # UCanAccess JARファイル群
├── data/                  # Access DBコピー先（一時）
└── logs/                  # ログ出力先
```

## 事前準備

### 1. ネットワークドライブのマウント

```bash
# cifsツールのインストール
sudo apt-get update
sudo apt-get install cifs-utils

# マウントポイント作成
sudo mkdir -p /mnt/schejule

# 認証情報ファイル作成
sudo nano /etc/smbcredentials
# 以下を記述
username=ユーザー名
password=パスワード
domain=ドメイン名（あれば）

# パーミッション設定
sudo chmod 600 /etc/smbcredentials

# /etc/fstabに追加
sudo nano /etc/fstab
# 以下を追加
//172.17.81.101/schejule /mnt/schejule cifs credentials=/etc/smbcredentials,uid=1000,gid=1000,iocharset=utf8 0 0

# マウント実行
sudo mount -a

# 確認
ls /mnt/schejule/cylline
ls /mnt/schejule/camline
```

### 2. 出力先ディレクトリの作成

```bash
mkdir -p /home/docker-user/KakouDenpyo
mkdir -p /home/docker-user/KakouJisseki
```

### 3. 環境変数ファイルの作成

```bash
cd /home/docker-user/docker-apps/8_camcyl_app
cp .env.example .env
nano .env  # 必要に応じて設定を変更
```

## 使用方法

### ビルドと起動

```bash
cd /home/docker-user/docker-apps/8_camcyl_app

# イメージのビルド
docker-compose build

# コンテナの起動（バックグラウンド）
docker-compose up -d

# ログ確認
docker-compose logs -f

# コンテナの停止
docker-compose down
```

### 手動実行（テスト用）

```bash
# コンテナ内でシェルを起動
docker-compose exec camcyl-app bash

# 処理1を手動実行
python /app/scripts/process1.py

# 処理2を手動実行
python /app/scripts/process2.py

# 両方を並列実行
/app/scripts/run_all.sh
```

### ログ確認

```bash
# cronログ
tail -f logs/cron.log

# 処理1のログ
tail -f logs/process1_YYYYMMDD.log

# 処理2のログ
tail -f logs/process2_YYYYMMDD.log
```

## 処理詳細

### 処理1: rBOM CSVコピー・加工

- **入力**: `/home/docker-user/rBOM/rBOM_bat/PFW_OT/File/KAKOU_EXP/`配下の4ファイル
  - `CAM/CAMKakouDenpyou.csv` - 項目削除・重複削除あり
  - `CAM/CONV.csv` - そのままコピー
  - `CAM/SEISANKI.csv` - そのままコピー
  - `M_S/ASPKakouDenpyo.csv` - 項目削除・重複削除あり

- **出力**: `/home/docker-user/KakouDenpyo/`

- **実行間隔**: 15分

### 処理2: Access DB → CSV抽出

- **入力**:
  - `\\172.17.81.101\schejule\cylline\Cyl_pfw_table.accdb`
  - `\\172.17.81.101\schejule\camline\EJ\EJ_DETA_SERVER\EJデータマスター.accdb`

- **抽出テーブル**:
  - `KaLstCyl_All` → `Cyl_pfw_table_KaLstCyl_All.csv`
  - `CAMFIN_LOG_ALL` → `EJデータマスター_CAMFIN_LOG_ALL.csv`

- **出力**: `/home/docker-user/KakouJisseki/`

- **実行間隔**: 15分

## トラブルシューティング

### cronが実行されない

```bash
# コンテナ内でcronの状態確認
docker-compose exec camcyl-app pgrep cron

# cronログ確認
docker-compose exec camcyl-app cat /app/logs/cron.log
```

### ネットワークドライブにアクセスできない

```bash
# マウント確認
mount | grep schejule

# 再マウント
sudo umount /mnt/schejule
sudo mount -a
```

### ファイルが出力されない

- ログファイルでエラーを確認
- 出力先ディレクトリのパーミッションを確認
- .envファイルのパス設定を確認

## 技術仕様

- **Python**: 3.12
- **Java**: default-jdk-headless
- **ライブラリ**: pandas, JayDeBeApi, python-dotenv
- **スケジューラー**: cron
- **ログローテーション**: 7日間保持
- **エンコーディング**: UTF-8

## 将来の拡張（処理3）

`/home/docker-user/KakouJisseki`のCSVファイルをAPIサーバー経由で更新する処理を追加予定。
処理2のCSV出力後すぐに実行する設計。
