# 31_5-7突合

このディレクトリには、EJデータベース（Oracle）とKRDデータベース（MySQL）への接続方法と、データ突合処理のためのユーティリティが含まれています。

## ファイル一覧

| ファイル名 | 説明 |
|-----------|------|
| データベース接続方法.md | EJとKRDへの接続方法の詳細ドキュメント |
| database_utils.py | データベース接続関数のユーティリティモジュール |
| test_database_connection.py | データベース接続テストスクリプト |

## クイックスタート

### 1. 必要なライブラリのインストール

```bash
pip install cx_Oracle pymysql sqlalchemy pandas
```

### 2. 接続テストの実行

```bash
cd "C:\Dev\90_tools\90_temp\31_5-7突合"
python test_database_connection.py
```

### 3. 新しいスクリプトの作成例

```python
from database_utils import ej_data_get, krd_data_get
import pandas as pd

# EJからデータ取得
ej_sql = """
SELECT ITEM_CD, PUCH_FIXED_LT
FROM EXPJ2.M_ITEM
WHERE PRODUCT_TYP = 5
"""
ej_df = ej_data_get(ej_sql)

# KRDからデータ取得
krd_sql = """
SELECT 品番, 工程, 設備
FROM DATA_RES_CAPA
"""
krd_df = krd_data_get(krd_sql)

# データ突合
merged_df = pd.merge(
    ej_df,
    krd_df,
    left_on='ITEM_CD',
    right_on='品番',
    how='inner'
)

print(f"突合結果: {len(merged_df)}件")
```

## データベース接続情報

### EJデータベース（Oracle）
- ホスト: 172.17.107.102:1521
- サービス名: EXPJ
- ユーザー: EXPJ2
- スキーマ: EXPJ2

### KRDデータベース（MySQL）
- ホスト: krd
- データベース: machin
- ユーザー: pfw

詳細は `データベース接続方法.md` を参照してください。

## 主要なテーブル

### EJ（Oracle）
- **M_ITEM**: 品目マスタ
- **M_PUCH_UNIT_COST_H**: 仕入単価ヘッダ
- **M_PUCH_UNIT_COST**: 仕入単価
- **T_RLSD_PUCH_ODR**: 発注履歴

### KRD（MySQL）
- **DATA_RES_CAPA**: 加工能力データ

## トラブルシューティング

### Oracle接続エラー
```
DPI-1047: Cannot locate a 64-bit Oracle Client library
```
→ Oracle Instant Client 19.23をインストールしてPATHに追加

### MySQL接続エラー
```
Can't connect to MySQL server on 'krd'
```
→ ホスト名'krd'が名前解決できるか確認

詳細は `データベース接続方法.md` の「トラブルシューティング」セクションを参照してください。
