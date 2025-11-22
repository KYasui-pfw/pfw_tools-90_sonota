# 出荷シール作成システム (Streamlit版)

Power Automate Desktop版からStreamlit Webアプリ版へ移行した出荷シール自動作成システムです。

## 概要

ネットワークドライブ上の生産機情報と構成ファイルから、7種類の出荷シールExcelファイルを自動生成します。

### 生成されるシール（全7種類対応）
1. ✅ ドライビングバー（部品4種まで対応）
2. ✅ スクリュー（部品7種まで対応、セル結合処理）
3. ✅ 電柄Y付きチップ箱（ULM/NEEDLE判定）
4. ✅ KYK（2枚印刷）
5. ✅ キャスター（1/2枚判定）
6. ✅ ODチェック表
7. ✅ ガードネットプレート（部品7種まで対応）

## システム要件

### ホストサーバー要件
- Docker
- Docker Compose
- ネットワークドライブマウント: `\\esrv06\帳票開発` → `/mnt/esrv06/帳票開発`

### 外部ネットワーク
- `app-shared-net` (Docker external network)

## ディレクトリ構造

```
シール作成/
├── streamlit_app_full.py # 完全版メインアプリケーション（全7種類対応）
├── streamlit_app.py      # 基本版（ドライビングバーのみ）
├── pg/                   # テンプレートフォルダ
│   ├── テンプレート１.xlsx
│   ├── テンプレート２.xlsx
│   ├── テンプレート３.xlsx
│   ├── ODチェック表.xlsx
│   ├── 抽出条件.xlsx
│   └── factcnv.py        # 元のPython処理スクリプト（参照用）
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## セットアップ

### 1. ネットワークドライブマウント（ホスト側）

```bash
# マウントポイント作成
sudo mkdir -p /mnt/esrv06/帳票開発

# CIFSマウント（/etc/fstabに追加することを推奨）
sudo mount -t cifs //esrv06/帳票開発 /mnt/esrv06/帳票開発 -o username=YOUR_USER,password=YOUR_PASSWORD
```

### 2. Dockerネットワーク作成（初回のみ）

```bash
docker network create app-shared-net
```

### 3. アプリケーションのデプロイ

```bash
cd /path/to/シール作成

# ビルドと起動
docker-compose up --build -d

# ログ確認
docker-compose logs -f
```

## 使用方法

### Webアプリケーション

1. ブラウザで `http://SERVER_IP:8508` にアクセス
2. **処理対象年月**を入力（YYYYMM形式、例：202501）
3. **処理開始**ボタンをクリック
4. 生成されたExcelファイルをダウンロード

### 入力データ自動取得

アプリケーションは以下のパスから自動的にファイルを取得します：
- `\\esrv06\帳票開発\{年月}\生産機情報.xls(x)`
- `\\esrv06\帳票開発\{年月}\構成\*.xls(x)`

## Windowsローカル環境でのテスト

### 前提条件
- Python 3.12.3以上
- ネットワークドライブ `\\esrv06\帳票開発` へのアクセス権限

### セットアップ手順

```powershell
# 1. 作業ディレクトリに移動
cd "C:\Dev\90_tools\16_出荷シール作成"

# 2. 仮想環境作成（推奨）
python -m venv venv

# 3. 仮想環境を有効化
venv\Scripts\activate

# 4. 依存パッケージインストール
pip install -r requirements.txt

# 5. アプリケーション起動

# 完全版（全7種類対応）
streamlit run streamlit_app_full.py

# または基本版（ドライビングバーのみ）
streamlit run streamlit_app.py

# ブラウザで http://localhost:8501 が自動的に開きます
```

### テスト方法

1. 処理対象年月を入力（例：202501）
2. 処理開始ボタンをクリック
3. 生成されたExcelファイルをダウンロード

### トラブルシューティング（Windows）

#### ネットワークドライブにアクセスできない

```powershell
# ネットワークドライブの接続確認
net use

# 接続されていない場合は手動でマウント
net use Z: \\esrv06\帳票開発 /user:USERNAME PASSWORD
```

#### Python not found

```powershell
# Pythonバージョン確認
python --version

# インストールされていない場合
# https://www.python.org/downloads/ からダウンロード
```

#### pip install エラー

```powershell
# pipを最新にアップグレード
python -m pip install --upgrade pip

# requirements.txtを再インストール
pip install -r requirements.txt --upgrade
```

## 開発環境での実行（Linux/Mac）

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# ローカル実行（ネットワークドライブアクセス可能な環境）

# 完全版（全7種類対応）
streamlit run streamlit_app_full.py

# または基本版（ドライビングバーのみ）
streamlit run streamlit_app.py
```

## Docker コマンド

```bash
# サービス起動
docker-compose up -d

# サービス停止
docker-compose down

# ログ確認
docker-compose logs -f seal-maker

# 再ビルド
docker-compose up --build -d

# コンテナ内に入る
docker-compose exec seal-maker bash
```

## 技術スタック

- **Python**: 3.12.3
- **Streamlit**: 1.39.0 - Webアプリフレームワーク
- **pandas**: 2.1.4 - データ処理
- **openpyxl**: 3.1.2 - Excel操作

## アーキテクチャ

### データフロー

```
ネットワークドライブ
    ↓
生産機情報.xlsx + 構成/*.xlsx
    ↓
pandas処理（マージ・集計・抽出）
    ↓
7種類のDataFrame
    ↓
openpyxlによるExcel生成
    ↓
ダウンロード提供
```

### 処理ロジック

元のPower Automate Desktop + Python (factcnv.py) の処理ロジックをStreamlitアプリに統合：

1. 生産機情報と構成ファイルのマージ
2. 抽出条件.xlsxに基づく7種類のフィルタリング
3. テンプレートExcelへのデータ流し込み
4. セル配置・結合・印刷範囲設定

## 実装状況

### ✅ 完全版実装済み（streamlit_app_full.py）

全7種類のシール対応が完了しました：

1. **ドライビングバーシール**（部品4種まで対応）
   - 部品数量の自動集計
   - 5個以上の部品がある場合はエラーログ出力

2. **スクリューシール**（部品7種まで対応）
   - キャスター種類判定（ガードネット/ステップ/インホイールモーター）
   - 部品数に応じた自動セル結合処理
   - 8個以上の部品がある場合はエラーログ出力

3. **電柄Y付きチップ箱シール**
   - LEC/SEC判定によるULM自動追加
   - NEEDLE有無の自動判定

4. **KYKシール**
   - 自動2枚印刷対応

5. **キャスターシール**
   - ステップキャスターの1/2枚判定
   - ガードネットキャスターの1/1表示

6. **ODチェック表**
   - 月次自動フォーマット

7. **ガードネットプレートシール**（部品7種まで対応）
   - 部品数に応じた自動セル結合処理
   - 8個以上の部品がある場合はエラーログ出力

### その他の機能

- ✅ ファイルアップロード不要（ネットワークドライブから自動取得）
- ✅ Webベースの簡単UI（プログレスバー表示）
- ✅ エラーログExcel出力（部品数表示超過一覧）
- ✅ Windows/Docker両対応
- ✅ 環境自動判定（ローカル/Docker）

## トラブルシューティング

### ネットワークドライブにアクセスできない

```bash
# マウント状態確認
df -h | grep esrv06

# 再マウント
sudo umount /mnt/esrv06/帳票開発
sudo mount -t cifs //esrv06/帳票開発 /mnt/esrv06/帳票開発 -o username=USER,password=PASS
```

### コンテナ起動エラー

```bash
# ログ確認
docker-compose logs seal-maker

# コンテナ再起動
docker-compose restart seal-maker
```

### ポート競合

docker-compose.ymlで別のポートに変更：
```yaml
ports:
  - "8509:8508"  # ホスト側ポートを変更
```

## 変更履歴

- **2025-01-22**: Streamlit版完全版作成（全7種類対応）
  - streamlit_app_full.py: 全シール対応
  - streamlit_app.py: 基本版（ドライビングバーのみ）
  - 元のfactcnv.pyの全ロジックを統合
- **2025-02-10**: PAD版でガードネットプレート対応追加
- **2024-06-11**: PAD版でスクリュー部品数上限を6→7に変更

## ライセンス

社内専用
