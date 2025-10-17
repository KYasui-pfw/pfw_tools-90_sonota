# データベース設計仕様書

## SQLite設計

### 保存場所
```
./Database/mapping.db
```

### テーブル設計

#### 1. mapping_results テーブル
マッピング結果を管理するメインテーブル

```sql
CREATE TABLE mapping_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- EJ側データ
    ej_order_no TEXT,                -- EJ発注番号 (T_RLSD_PUCH_ODR.PUCH_ODR_CD)
    ej_item_code TEXT,              -- EJ品目コード (T_RLSD_PUCH_ODR.ITEM_CD)
    ej_item_name TEXT,              -- EJ品目名 (M_ITEM.ITEM_NAME)
    ej_quantity REAL,               -- EJ発注数 (T_RLSD_PUCH_ODR.PUCH_ODR_QTY)
    ej_delivery_date DATE,          -- EJ納期 (T_RLSD_PUCH_ODR.PUCH_ODR_DLV_DATE)
    ej_vendor_code TEXT,            -- EJ取引先コード (T_RLSD_PUCH_ODR.VEND_CD)
    ej_company_code TEXT,           -- EJ会社コード (T_RLSD_PUCH_ODR.COMPANY_CD)
    ej_plant_code TEXT,             -- EJ工場コード (T_RLSD_PUCH_ODR.PLANT_CD)
    
    -- rBOM側データ
    rbom_order_no TEXT,             -- rBOM発注番号
    rbom_line_no INTEGER,           -- rBOM明細番号
    rbom_item_code TEXT,            -- rBOM品目コード
    rbom_item_name TEXT,            -- rBOM品目名
    rbom_quantity REAL,             -- rBOM数量
    rbom_delivery_date DATE,        -- rBOM納期
    rbom_seino TEXT,                -- rBOM製番
    
    -- マッピング管理項目
    m_sequence INTEGER DEFAULT 1,    -- M連番（固定値1）
    status TEXT DEFAULT '',         -- 状態（空欄）
    manual_mapping TEXT DEFAULT '', -- 手動マッピング（空欄）
    mapping_type TEXT,              -- マッピング種別（MATCHED/EJ_ONLY/RBOM_ONLY）
    
    -- システム項目
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. extraction_conditions テーブル
抽出条件の保存用テーブル

```sql
CREATE TABLE extraction_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_name TEXT NOT NULL,
    delivery_date_from DATE,
    delivery_date_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### インデックス設計

```sql
-- マッピングキー用インデックス
CREATE INDEX idx_mapping_ej_key ON mapping_results(ej_item_code, ej_quantity);
CREATE INDEX idx_mapping_rbom_key ON mapping_results(rbom_item_code, rbom_quantity);

-- 検索用インデックス
CREATE INDEX idx_mapping_type ON mapping_results(mapping_type);
CREATE INDEX idx_delivery_date ON mapping_results(ej_delivery_date, rbom_delivery_date);
```

## マッピングロジック

### 1. マッピング条件
```
EJ.ITEM_CD = rBOM.HMCD AND EJ.PUCH_ODR_QTY = rBOM.RCVQTY
```

### 2. マッピング種別
- **MATCHED**: 両システムでマッピング成功
- **EJ_ONLY**: EJ側のみ存在（rBOM側項目は空欄）
- **RBOM_ONLY**: rBOM側のみ存在（EJ側項目は空欄）

### 3. データ処理フロー
1. EJシステムからデータ取得
2. rBOMシステムからデータ取得
3. 品目コード + 数量でマッピング処理
4. マッピング結果をSQLiteに保存
5. 画面表示用にデータ整形

## データ操作

### 初期化処理
```sql
-- 既存データクリア
DELETE FROM mapping_results;

-- 新規データ投入
INSERT INTO mapping_results (...) VALUES (...);
```

### CSV出力用クエリ
```sql
SELECT 
    ej_order_no,
    ej_item_code,
    ej_item_name,
    ej_quantity,
    ej_delivery_date,
    rbom_order_no,
    rbom_item_code,
    rbom_item_name,
    rbom_quantity,
    rbom_delivery_date,
    m_sequence,
    status,
    manual_mapping
FROM mapping_results
ORDER BY ej_order_no, rbom_order_no;
```