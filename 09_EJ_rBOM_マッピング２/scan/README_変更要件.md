# ej_ukeire_list_tenkai.py 変更要件

## 変更対象ファイル
- **本番環境:** `D:\ConMas\gateway\scripts\scan\ej_ukeire_list_tenkai.py`
- **開発環境:** `C:\Dev\90_tools\09_EJ_rBOM_マッピング２\scan\ej_ukeire_list_tenkai.py`

## 変更箇所
107～109行目のデータ取得処理を変更

### 現在のコード（変更前）
```python
po_text = jdata[n-5].replace(' ', '').replace('　', '')
pono = po_text[:-4]
lineno = po_text[-3:]
```

### 変更理由
データの扱い方に変更があり、上記のように直接データを取得できなくなった。
代わりに `mapping.db` を経由して `rbom_order_no` と `rbom_line_no` を取得する必要がある。

## 変更仕様

### 入力データ
- `jdata[n-5]`: EJ発注番号（`mapping_results.ej_order_no`に相当）

### データベース情報
- **パス:** `D:\py\EJ_rBOM_mapping\database\mapping.db`
- **テーブル:** `mapping_results`
- **検索条件:**
  - `ej_order_no = jdata[n-5]`（空白・全角スペース除去後）
  - `status IN ('済', '済2')`
  - **追加条件（未確定）:** 複数行がマッチする場合の優先順位

### 取得データ
- `rbom_order_no` → `pono` に設定
- `rbom_line_no` → `lineno` に設定（**3桁ゼロ埋め必須**）
  - 例: `2` → `"002"`
  - 例: `15` → `"015"`

### エラーハンドリング
- 該当データが見つからない場合：エラーを発生させる
  ```python
  raise ValueError(f"エラー: EJ発注番号 {ej_order_no} に対応するマッピングデータが見つかりません")
  ```

## 実装予定（確定部分）

### 1. インポート追加
```python
import sqlite3
```

### 2. データベースパス定義
```python
DB_PATH = r"D:\py\EJ_rBOM_mapping\database\mapping.db"
```

### 3. データ取得処理（仮実装）
```python
# jdata[n-5]からej_order_noを取得
ej_order_no = jdata[n-5].replace(' ', '').replace('　', '')

# mapping.dbから対応するrbom情報を取得
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ★★★ ここの検索条件が未確定 ★★★
cursor.execute("""
    SELECT rbom_order_no, rbom_line_no
    FROM mapping_results
    WHERE ej_order_no = ?
    AND status IN ('済', '済2')
    -- ★ 複数行マッチ時の優先順位条件が必要 ★
    -- 候補: ORDER BY ej_m_sequence ASC LIMIT 1
    -- 候補: AND is_fixed = 1
    -- 候補: その他の条件
""", (ej_order_no,))

result = cursor.fetchone()
conn.close()

# データが見つからない場合はエラー
if not result:
    raise ValueError(f"エラー: EJ発注番号 {ej_order_no} に対応するマッピングデータが見つかりません")

# ponoとlinenoに設定
pono = result[0]  # rbom_order_no
lineno = str(result[1]).zfill(3)  # rbom_line_noを3桁ゼロ埋め

# ここから下は元の処理を継続
# API_URL = f"http://pfw-api/orders/slip?pono={pono}&lineno={lineno}"
# ...
```

## 未確定事項（要検討）

### ❓ 複数行マッチ時の優先順位

同じ `ej_order_no` で複数のマッピング結果が存在する場合、どの行を取得するか？

#### 候補1: 連番が最小のもの
```sql
ORDER BY ej_m_sequence ASC LIMIT 1
```
- **理由:** 最初にマッピングされたデータを優先

#### 候補2: 固定マッピングを優先
```sql
AND is_fixed = 1
```
- **理由:** 確定したマッピングのみを対象

#### 候補3: 備考マッピング（済2）を除外
```sql
AND status = '済'  -- '済2'を除外
```
- **理由:** 通常の自動マッピングのみを対象

#### 候補4: その他の条件
- `rbom_m_sequence` の優先順位
- `created_at` の最新/最古
- 特定の条件の組み合わせ

## 確認済み事項 ✅

1. ✅ `import sqlite3` を追加 → 問題なし
2. ⏳ 複数行マッチ時の条件 → **要検討**（難問）
3. ✅ データ未発見時の処理 → エラーを発生させる
4. ✅ `rbom_line_no` のゼロ埋め → `str(rbom_line_no).zfill(3)`
5. ✅ データベースパス → `r"D:\py\EJ_rBOM_mapping\database\mapping.db"`

## 次回作業時のチェックリスト

- [ ] 複数行マッチ時の優先順位を決定
- [ ] 実装コードを作成
- [ ] 開発環境でテスト（`C:\Dev\90_tools\09_EJ_rBOM_マッピング２\scan\ej_ukeire_list_tenkai.py`）
- [ ] 本番環境に配置（`D:\ConMas\gateway\scripts\scan\ej_ukeire_list_tenkai.py`）
- [ ] 動作確認

## 参考情報

### mapping_results テーブル構造（抜粋）
```sql
CREATE TABLE mapping_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    ej_order_no TEXT,                -- EJ発注番号（検索キー）
    ej_m_sequence INTEGER DEFAULT 1, -- EJ連番
    rbom_order_no TEXT,              -- rBOM発注番号（取得対象）
    rbom_line_no INTEGER,            -- rBOM行番号（取得対象・3桁ゼロ埋め）
    rbom_m_sequence INTEGER DEFAULT 1, -- rBOM連番
    status TEXT DEFAULT '',          -- ステータス（'済', '済2', '未'など）
    is_fixed BOOLEAN DEFAULT FALSE,  -- 固定マッピングフラグ
    -- その他のカラム...
);
```

### ステータスの意味
- **'済'**: 通常の自動マッピング成功
- **'済2'**: 備考マッピング成功（EJ品目コード = rBOM備考）
- **'未'**: 未マッピング（EJ_ONLYまたはrBOM_ONLY）
- **'手'**: 手動マッピング（このツールでは未使用）

### 関連ファイル
- マッピングツール本体: `C:\Dev\90_tools\09_EJ_rBOM_マッピング２\発注残マッピングリスト.py`
- データベース管理: `C:\Dev\90_tools\09_EJ_rBOM_マッピング２\database\db_manager.py`
- マッピングエンジン: `C:\Dev\90_tools\09_EJ_rBOM_マッピング２\mapping\mapper.py`

## メモ
- 2025-10-30: 要件整理完了、複数行マッチ時の優先順位について検討が必要と判明
- この問題は「かなりの難問」とのこと、慎重に検討する必要あり
