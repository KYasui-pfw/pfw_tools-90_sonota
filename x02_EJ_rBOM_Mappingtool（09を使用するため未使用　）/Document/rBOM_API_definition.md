# rBOMシステム - Orders API定義

## 接続情報
- **API URL**: http://pfw-api/orders/
- **メソッド**: GET
- **認証**: READ_API_KEY="oG5^Ls%#20yq"

## リクエストパラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|---|------|------|
| year | integer | ✓ | 年（2000-2100） |
| month | integer | ✓ | 月（1-12） |
| cycle | integer | - | 次（0-9）※省略可能 |

## レスポンス（マッピング用主要項目）

| フィールド名 | 説明 | マッピング用途 |
|-------------|------|---------------|
| HMCD | 品目コード | マッピングキー |
| PONO | 発注番号 | 識別用 |
| LINENO | 明細番号 | 識別用 |
| SEINO | 製番 | 表示用 |
| HMNM | 品目名 | 表示用 |
| DRVDT | 納期日 | 条件抽出用 |
| RCVQTY | 受領数量 | マッピングキー（数量） |

## APIクエリ例
```python
import requests

response = requests.get(
    "http://pfw-api/orders/",
    params={"year": 2025, "month": 8},
    headers={"Authorization": f"Bearer oG5^Ls%#20yq"}
)
orders = response.json()
```

## 注意事項
- 品目コード（HMCD）と受領数量（RCVQTY）でEJシステムとマッピング
- 納期日（DRVDT）による条件抽出が可能
- cycle指定で特定次のデータのみ取得可能