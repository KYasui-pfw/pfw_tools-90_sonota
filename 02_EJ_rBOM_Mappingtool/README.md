# EJ-rBOM マッピングツール

製造業の生産管理システム更新に伴い、旧EJシステムと新rBOMシステムの発注残データをマッピングするStreamlitアプリケーションです。

## 機能概要

- **自動マッピング**: 品目コードと数量をキーにしたEJ-rBOMデータの自動マッピング
- **データ表示**: Ag-gridを使用したマッピング結果の一覧表示
- **CSV出力**: マッピング結果のCSVエクスポート
- **手動マッピング**: 未マッピングデータの手動調整（仮実装）

## システム要件

- Python 3.8+
- Oracle Database（EJシステム用）
- インターネット接続（rBOM API用）

## インストール

1. リポジトリのクローンと仮想環境作成
```bash
cd C:\Dev\90_tools\02_EJ_rBOM_Mappingtool
python -m venv venv
```

2. 仮想環境の有効化とライブラリインストール
```bash
# Windows
.\venv\Scripts\activate

# パッケージインストール
pip install -r requirements.txt
```

3. 環境変数設定
```bash
# .env.exampleをコピーして.envを作成
copy .env.example .env

# 必要に応じて.envファイルを編集
```

## 使用方法

1. アプリケーション起動
```bash
streamlit run app.py
```

2. ブラウザで`http://localhost:8501`にアクセス

3. 抽出条件を設定（納期は2025年7月1日以降）

4. 「自動マッピング」ボタンをクリック

5. マッピング結果を確認・CSV出力

## データソース

### EJシステム（Oracle Database）
- **接続先**: 172.17.107.102:1521/SN=EXPJ
- **テーブル**: T_RLSD_PUCH_ODR（発注残）+ M_ITEM（品目マスタ）
- **制限**: 納期2025年7月1日以降のデータのみ（データ量削減のため）

### rBOMシステム（API）
- **URL**: http://pfw-api/orders/
- **認証**: READ_API_KEY="oG5^Ls%#20yq"

## マッピングロジック

1. **完全マッチング**: 品目コード + 数量が一致
2. **EJのみ**: EJ側にのみ存在するデータ
3. **rBOMのみ**: rBOM側にのみ存在するデータ

## プロジェクト構造

```
├── app.py              # メインアプリケーション
├── requirements.txt    # Python依存関係
├── .env.example       # 環境変数テンプレート
├── Database/          # SQLiteデータベース格納
├── Document/          # 設計ドキュメント
├── database/          # データベース管理モジュール
├── data_sources/      # データソース接続モジュール
├── mapping/           # マッピングエンジン
└── ui/               # UIコンポーネント
```

## 注意事項

- **データ量制限**: EJシステムのデータ量を考慮し、納期は2025年7月1日以降のみ対応
- **短期運用**: Windows Server 2022での短期間運用を想定
- **Ag-grid**: 無料版のみ使用
- **手動マッピング**: 現在は仮実装（将来拡張予定）

## トラブルシューティング

### Oracle接続エラー
- cx_Oracleライブラリのインストール確認
- Oracle Clientの設定確認
- 接続情報（IP、ポート、認証情報）の確認

### API接続エラー
- ネットワーク接続確認
- API URL（http://pfw-api/）へのアクセス確認
- API キーの確認

### Streamlitエラー
- 仮想環境の有効化確認
- 依存ライブラリのバージョン確認
- ポート8501の使用状況確認