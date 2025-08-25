# Orders API エンドポイント仕様書

## 概要

Orders APIは、発注明細関連データを取得するためのエンドポイントです。年・月・次（任意）を条件として、複数のデータベーステーブル（D3340, D3010, D3360, DK020）から統合されたデータを返します。

## エンドポイント情報

- **URL**: `/orders/`
- **メソッド**: `GET`
- **認証**: 読み取り専用トークンが必要
- **タグ**: `Orders`

## 追記：読み取り専用のAPIキー

READ_API_KEY="oG5^Ls%#20yq"


## リクエストパラメータ

### クエリパラメータ

| パラメータ名 | 型 | 必須 | 制約 | 説明 |
|-------------|---|------|------|------|
| `year` | integer | ✓ | 2000 ≤ year ≤ 2100 | 年（例: 2025） |
| `month` | integer | ✓ | 1 ≤ month ≤ 12 | 月（例: 8） |
| `cycle` | integer | - | 0 ≤ cycle ≤ 9 | 次（例: 3）※省略可能 |

### リクエスト例

```bash
# 2025年8月の全データを取得
GET /orders/?year=2025&month=8

# 2025年8月3次のデータを取得
GET /orders/?year=2025&month=8&cycle=3
```

## レスポンス

### 成功時（200 OK）

リスト形式で発注明細データを返します。

#### レスポンススキーマ

```json
[
  {
    "PONO": "string",           // 発注番号
    "LINENO": "integer",        // 明細番号
    "STATUS": "string",         // ステータス
    "SEINO": "string",          // 製番
    "HMCD": "string",           // 品目コード
    "HMNM": "string",           // 品目名
    "DRVDT": "2025-08-15",      // 納期日
    "RECDT": "2025-08-10",      // 受信日
    
    // D3010テーブルからの情報
    "D3010_SEINO": "string",    // D3010製番
    "D3010_HMNM": "string",     // D3010品目名
    "INCH": 12.5,               // インチ
    "GAUGE": 2.3,               // ゲージ
    "DEADLINE": "2025-08-20",   // 期限日
    "GETSUJI": "202508",        // 月次（YYYYMM形式）
    
    // D3360テーブルからの情報
    "D3360_PONO": "string",     // D3360発注番号
    "D3360_LINENO": "integer",  // D3360明細番号
    "RCVDT": "2025-08-12",      // 受領日
    "RCVQTY": 100.0,            // 受領数量
    "MEINOTE": "string",        // メモ
    
    // DK020テーブルからの情報
    "DK020_PONO": "string",     // DK020発注番号
    "DK020_LINENO": "integer",  // DK020明細番号
    "SYORIZUMIKB": "string"     // 処理済区分
  }
]
```

### エラー時

#### 500 Internal Server Error
データベースエラーが発生した場合

```json
{
  "detail": "Database error occurred: {エラー詳細}"
}
```

## データソース

以下のOracleデータベーステーブルからデータを取得します：

- **D3340**: 発注明細マスタ（メインテーブル）
- **D3010**: 製番マスタ（INNER JOIN）
- **D3360**: 受領明細（LEFT JOIN）
- **DK020**: 処理済みデータ（LEFT JOIN）

## データフィルタリングロジック

### cycleパラメータあり
`GETSUJI`フィールドが`{年}{月}{次}`（例: `20250803`）と完全一致するレコードを取得

### cycleパラメータなし
`GETSUJI`フィールドが`{年}{月}`（例: `202508`）で始まるレコードを取得

※ `GETSUJI`はD3010.GETSUJIまたはD3340.DRVDTから生成されます

## ソート順

結果は以下の順序でソートされます：
1. 発注番号（PONO）昇順
2. 明細番号（LINENO）昇順

## 使用例

### Python（requests）

```python
import requests

# 基本的な使用例
response = requests.get(
    "http://your-api-server/orders/",
    params={"year": 2025, "month": 8},
    headers={"Authorization": "Bearer your-read-token"}
)

orders = response.json()
print(f"取得件数: {len(orders)}")
```

### curl

```bash
curl -X GET "http://your-api-server/orders/?year=2025&month=8&cycle=3" \
     -H "Authorization: Bearer your-read-token"
```

## 注意事項

1. **認証が必要**: 読み取り専用トークンによる認証が必須です
2. **データベース接続**: Oracleデータベースへの接続が必要です
3. **パフォーマンス**: 大量データ取得時は処理時間にご注意ください
4. **日付フォーマット**: 日付は`YYYY-MM-DD`形式で返されます
5. **NULL値**: 一部フィールドはNULL値を含む可能性があります