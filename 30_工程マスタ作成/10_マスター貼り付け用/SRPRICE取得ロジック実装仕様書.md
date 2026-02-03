# SRPRICE取得ロジック実装仕様書

このドキュメントは、品目工程マスタ(M0840)作成時のSRPRICE（購入単価）取得ロジックの完全な実装仕様です。
AIがこの仕様を読んで同じ実装を再現できるように記述しています。

---

## 1. 概要

**目的:** 前工程コードをキーとして、EJ Oracleデータベースから購入単価（SRPRICE）を取得する

**重要原則:**
- SRCDとSRPRICEは**必ず同一レコードから取得**（一貫性保証）
- 検索キーは**前工程**（完成部番ではない）
- 優先度の高いデータソースから順に検索し、見つかった時点で確定
- PEFIN工程は例外処理で固定値0

---

## 2. データソース（優先順）

### 2.1 プライマリデータソース（最優先）

**テーブル:**
- `EXPJ2.M_PUCH_UNIT_COST_H` (購入単価ヘッダマスタ)
- `EXPJ2.M_PUCH_UNIT_COST` (購入単価マスタ)

**結合条件:** INNER JOIN
```sql
ON h.ITEM_CD = c.ITEM_CD AND h.VEND_CD = c.VEND_CD
```

**取得カラム:**
| カラム | テーブル | 用途 |
|--------|---------|------|
| ITEM_CD | M_PUCH_UNIT_COST_H | 品目コード（検索キー） |
| VEND_CD | M_PUCH_UNIT_COST_H | 仕入先コード → SRCD |
| PUCH_PRIORITY_REF_NO | M_PUCH_UNIT_COST_H | 優先順位番号（ソート用） |
| UNIT_COST | M_PUCH_UNIT_COST | **購入単価 → SRPRICE** |
| EFF_PHASE_IN_DATE | M_PUCH_UNIT_COST | 有効開始日（ソート用） |
| PUCH_SIZE | M_PUCH_UNIT_COST | 購入サイズ（ソート用） |

**WHERE条件（必須）:**
```sql
WHERE h.PUCH_PRIORITY_REF_NO IS NOT NULL
  AND c.EFF_PHASE_IN_DATE < TO_DATE('2025-12-01', 'YYYY-MM-DD')
```

**優先順位（ORDER BY）:**
```sql
ORDER BY h.ITEM_CD,
         h.PUCH_PRIORITY_REF_NO ASC,    -- 1. 優先順位番号が小さい方
         c.EFF_PHASE_IN_DATE DESC,      -- 2. 有効開始日が新しい方
         c.PUCH_SIZE ASC                -- 3. 購入サイズが小さい方
```

**選定ルール:**
- ITEM_CD（前工程）ごとに、ORDER BY条件で**最初に出現したレコード1行のみ**を採用
- そのレコードから`VEND_CD` (SRCD) と `UNIT_COST` (SRPRICE) を同時に取得

---

### 2.2 フォールバックデータソース（プライマリで見つからない場合）

**テーブル:**
- `EXPJ2.T_RLSD_PUCH_ODR` (発注実績テーブル)

**取得カラム:**
| カラム | 用途 |
|--------|------|
| ITEM_CD | 品目コード（検索キー） |
| VEND_CD | 仕入先コード → SRCD |
| UNIT_COST | **購入単価 → SRPRICE** |
| PUCH_ODR_DLV_DATE | 発注納期（ソート用） |

**WHERE条件（必須）:**
```sql
WHERE ITEM_CD IS NOT NULL
  AND VEND_CD IS NOT NULL
```

**優先順位（ORDER BY）:**
```sql
ORDER BY ITEM_CD,
         PUCH_ODR_DLV_DATE DESC  -- 納期が新しい方
```

**選定ルール:**
- ITEM_CD（前工程）ごとに、最新納期（PUCH_ODR_DLV_DATE DESC）の**レコード1行のみ**を採用
- そのレコードから`VEND_CD` (SRCD) と `UNIT_COST` (SRPRICE) を同時に取得

---

### 2.3 どちらでも見つからない場合

**SRCD:** 空文字 `""`
**SRPRICE:** `0`

---

## 3. 検索キー仕様

**検索キー:** `前工程` フィールドの値

**例:**
- `AO-12345` → このコードでM_ITEMテーブルのITEM_CDを検索
- `MC-67890` → このコードでM_ITEMテーブルのITEM_CDを検索
- `PEFIN-ABC123` → PEFIN例外処理（後述）

**注意:** 完成部番（HMCD）ではなく、前工程をキーにする

---

## 4. 例外処理

### 4.1 PEFIN工程の例外

**条件:** KTCD（工程コード）が `'PEFIN'` の場合

**固定値設定:**
```python
SRPRICE = 0.0  # 固定値
SRCD = ''      # 空欄（またはデータベースから取得した値を無視）
LDTIME = 0     # リードタイムも0
CSBCD = '10'   # 原価区分（通常は'13'だが、PEFINは'10'）
RCVTSTKBN = '2'  # 受入検査区分（通常は'1'だが、PEFINは'2'）
RCVCHKKBN = '2'  # 受入チェック区分（通常は'1'だが、PEFINは'2'）
```

**理由:** PEFIN工程は外部表面処理工程であり、購入単価の管理を行わない

---

## 5. 実装例（Python）

### 5.1 データベース接続関数

```python
import cx_Oracle
import pandas as pd

def ej_data_get(sql):
    """EJシステム（Oracle Database）に接続してSQLを実行する"""
    try:
        # EJシステム接続情報
        host = '172.17.107.102'
        port = '1521'
        service_name = 'EXPJ'
        username = 'EXPJ2'
        password = 'EXPJ2'

        # 接続文字列
        connection_string = f"{username}/{password}@{host}:{port}/{service_name}"

        # データベース接続
        connection = cx_Oracle.connect(connection_string)

        # SQLを実行してDataFrameに変換
        df = pd.read_sql(sql, connection)

        # 接続を閉じる
        connection.close()

        return df

    except Exception as e:
        print(f"EJシステムへの接続でエラーが発生しました: {str(e)}")
        raise
```

---

### 5.2 プライマリデータソース取得

```python
# ステップ1: M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COSTからSRCD/SRPRICE統合データを取得
print("=== EJシステム（M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COST）統合データ取得 ===")
try:
    # INNER JOINで一貫データ取得
    srcd_srprice_sql = """
    SELECT h.ITEM_CD, h.VEND_CD, h.PUCH_PRIORITY_REF_NO,
           c.UNIT_COST, c.EFF_PHASE_IN_DATE, c.PUCH_SIZE
    FROM EXPJ2.M_PUCH_UNIT_COST_H h
    INNER JOIN EXPJ2.M_PUCH_UNIT_COST c
    ON h.ITEM_CD = c.ITEM_CD AND h.VEND_CD = c.VEND_CD
    WHERE h.PUCH_PRIORITY_REF_NO IS NOT NULL
    AND c.EFF_PHASE_IN_DATE < TO_DATE('2025-12-01', 'YYYY-MM-DD')
    ORDER BY h.ITEM_CD, h.PUCH_PRIORITY_REF_NO ASC,
             c.EFF_PHASE_IN_DATE DESC, c.PUCH_SIZE ASC
    """
    combined_df = ej_data_get(srcd_srprice_sql)
    print(f"統合データ取得: {len(combined_df)}行")

    # ステップ2: ITEM_CD（前工程）ごとに最優先レコード1行のみ選定
    srcd_srprice_dict = {}
    for _, record in combined_df.iterrows():
        item_cd = record['ITEM_CD']
        if item_cd not in srcd_srprice_dict:
            # 最初に見つかったレコード（ORDER BY条件により最優先）を採用
            srcd_srprice_dict[item_cd] = {
                'SRCD': record['VEND_CD'],
                'SRPRICE': record['UNIT_COST'],
                'EFF_PHASE_IN_DATE': record['EFF_PHASE_IN_DATE'],
                'PUCH_SIZE': record['PUCH_SIZE'],
                'PRIORITY': record['PUCH_PRIORITY_REF_NO']
            }

    print(f"1行選定辞書作成: {len(srcd_srprice_dict)}件")

except Exception as e:
    print(f"統合データ取得エラー: {e}")
    srcd_srprice_dict = {}
```

---

### 5.3 フォールバックデータソース取得

```python
# ステップ3: T_RLSD_PUCH_ODRからフォールバックデータを取得
print("=== EJシステム（T_RLSD_PUCH_ODR）フォールバックデータ取得 ===")
try:
    fallback_sql = """
    SELECT ITEM_CD, VEND_CD, UNIT_COST, PUCH_ODR_DLV_DATE
    FROM EXPJ2.T_RLSD_PUCH_ODR
    WHERE ITEM_CD IS NOT NULL AND VEND_CD IS NOT NULL
    ORDER BY ITEM_CD, PUCH_ODR_DLV_DATE DESC
    """
    fallback_df = ej_data_get(fallback_sql)
    print(f"フォールバック用データ取得: {len(fallback_df)}行")

    # 最新日付のレコードのみを抽出（groupby().first()で最初の行=最新日付を取得）
    fallback_latest = fallback_df.groupby('ITEM_CD').first().reset_index()
    print(f"フォールバック最新日付で重複除去: {len(fallback_latest)}件")

    # 辞書作成
    fallback_srcd_dict = dict(zip(fallback_latest['ITEM_CD'], fallback_latest['VEND_CD']))
    fallback_srprice_dict = dict(zip(fallback_latest['ITEM_CD'], fallback_latest['UNIT_COST']))
    print(f"フォールバックSRCD辞書作成: {len(fallback_srcd_dict)}件")
    print(f"フォールバックSRPRICE辞書作成: {len(fallback_srprice_dict)}件")

except Exception as e:
    print(f"フォールバック用データ取得エラー: {e}")
    fallback_srcd_dict = {}
    fallback_srprice_dict = {}
```

---

### 5.4 実際のSRPRICE取得処理

```python
# ステップ4: 各レコードに対してSRCD/SRPRICE取得処理
for idx, row in work_df.iterrows():
    zenkatei = str(row['前工程']) if pd.notna(row['前工程']) else ''
    kansei_bango = str(row['完成部番']) if pd.notna(row['完成部番']) else ''

    # KTCDを計算（前工程の"-"より前を抽出）
    if '-' in zenkatei:
        ktcd = zenkatei.split('-')[0]
    else:
        ktcd = zenkatei

    # KTCD変換処理
    if ktcd == "A0":
        ktcd = "AO"
    elif ktcd in ["PA1", "PA2"]:
        ktcd = "PA"

    # 前工程をキーとして使用（重要！）
    zenkatei_key = zenkatei

    # === PEFIN例外処理 ===
    if ktcd == 'PEFIN':
        # PEFIN工程は固定値
        srcd_value = ''
        srprice_value = 0.0
        print(f"PEFIN例外処理: {kansei_bango} -> SRPRICE=0（固定値）")
    else:
        # === 通常処理 ===

        # 統合辞書からSRCD/SRPRICE一貫取得（プライマリ）
        record_data = srcd_srprice_dict.get(zenkatei_key, {})
        srcd_value = record_data.get('SRCD', '')
        srprice_value = record_data.get('SRPRICE', 0)

        # 統合辞書で見つからない場合、T_RLSD_PUCH_ODRからフォールバック取得
        if not srcd_value:
            srcd_value = fallback_srcd_dict.get(zenkatei_key, "")
            srprice_value = fallback_srprice_dict.get(zenkatei_key, 0)

            if srcd_value:
                # フォールバックで見つかった場合のログ
                print(f"フォールバック取得: {zenkatei_key} -> SRCD: {srcd_value}, SRPRICE: {srprice_value}")

        # どちらでも見つからない場合は空欄/0のまま

    # === 最終値設定 ===
    srprice_final = float(srprice_value) if srprice_value is not None else 0.0
    srcd_final = str(srcd_value) if srcd_value else ''

    # レコード作成
    output_record = {
        'HMCD': kansei_bango,
        'KTCD': ktcd,
        'SRCD': srcd_final,
        'SRPRICE': srprice_final,
        # ... その他のフィールド
    }
```

---

## 6. 処理フローチャート

```
開始
  ↓
前工程をキーとして取得 (zenkatei_key)
  ↓
KTCDを計算（"-"より前を抽出、A0→AO、PA1/PA2→PA変換）
  ↓
┌────────────────────┐
│ KTCD = 'PEFIN' ?   │
└────────────────────┘
  ↓YES                    ↓NO
  │                       │
  │                       ↓
  │              ┌──────────────────────────┐
  │              │ M_PUCH_UNIT_COST_H +     │
  │              │ M_PUCH_UNIT_COST         │
  │              │ (INNER JOIN)             │
  │              │                          │
  │              │ zenkatei_keyで検索       │
  │              └──────────────────────────┘
  │                       ↓
  │              ┌────────────────────┐
  │              │ 見つかった？       │
  │              └────────────────────┘
  │                ↓YES        ↓NO
  │                │           │
  │                │           ↓
  │                │    ┌──────────────────────┐
  │                │    │ T_RLSD_PUCH_ODR      │
  │                │    │ (フォールバック)      │
  │                │    │                      │
  │                │    │ zenkatei_keyで検索   │
  │                │    └──────────────────────┘
  │                │           ↓
  │                │    ┌────────────────────┐
  │                │    │ 見つかった？       │
  │                │    └────────────────────┘
  │                │      ↓YES        ↓NO
  │                │      │           │
  ↓                ↓      ↓           ↓
SRPRICE=0      UNIT_COST  UNIT_COST   SRPRICE=0
SRCD=''        をSRPRICE   をSRPRICE   SRCD=''
               に設定      に設定
               VEND_CDを   VEND_CDを
               SRCDに設定  SRCDに設定
  │                │      │           │
  └────────────────┴──────┴───────────┘
                   ↓
            SRPRICE確定
                   ↓
                  終了
```

---

## 7. 重要な注意点

### 7.1 一貫性保証

**必須:** SRCDとSRPRICEは**必ず同一レコードから取得**すること

```python
# ✅ 正しい実装（同一レコードから取得）
record_data = srcd_srprice_dict.get(zenkatei_key, {})
srcd_value = record_data.get('SRCD', '')      # 同じrecord_dataから
srprice_value = record_data.get('SRPRICE', 0)  # 同じrecord_dataから

# ❌ 間違った実装（別々に取得）
srcd_value = some_dict.get(zenkatei_key, '')
srprice_value = other_dict.get(zenkatei_key, 0)  # 別のレコードから取得されるリスク
```

### 7.2 検索キーの重要性

**必須:** 検索キーは**前工程**（完成部番ではない）

```python
# ✅ 正しい実装
zenkatei_key = str(row['前工程'])  # 前工程をキーに使用
srprice_value = srcd_srprice_dict.get(zenkatei_key, {}).get('SRPRICE', 0)

# ❌ 間違った実装（過去のバグ）
kansei_bango_key = str(row['完成部番'])  # 完成部番をキーに使用
srprice_value = srcd_srprice_dict.get(kansei_bango_key, {}).get('SRPRICE', 0)
# → 誤ったリードタイムや単価が設定される
```

### 7.3 日付フィルタ

**必須:** `EFF_PHASE_IN_DATE < 2025-12-01` で将来日付を除外

```sql
-- 必ず含めること
AND c.EFF_PHASE_IN_DATE < TO_DATE('2025-12-01', 'YYYY-MM-DD')
```

**理由:** 将来適用予定の単価が誤って選択されないようにするため

### 7.4 NULL値処理

**必須:** NULL値のチェックと初期値設定

```python
# 取得した値がNoneの場合の処理
srprice_final = float(srprice_value) if srprice_value is not None else 0.0
srcd_final = str(srcd_value) if srcd_value else ''
```

---

## 8. テストケース

### テストケース1: プライマリデータソースで取得成功

**入力:**
- 前工程: `AO-12345`
- M_PUCH_UNIT_COST_Hに該当レコード存在
- M_PUCH_UNIT_COSTに該当レコード存在（INNER JOINで結合可能）

**期待される動作:**
- `PUCH_PRIORITY_REF_NO`最小のレコードを選択
- 同値の場合は`EFF_PHASE_IN_DATE`最新を選択
- さらに同値の場合は`PUCH_SIZE`最小を選択
- `UNIT_COST`をSRPRICEに設定
- `VEND_CD`をSRCDに設定

---

### テストケース2: フォールバックで取得成功

**入力:**
- 前工程: `MC-67890`
- M_PUCH_UNIT_COST_Hに該当レコードなし
- T_RLSD_PUCH_ODRに該当レコード存在

**期待される動作:**
- T_RLSD_PUCH_ODRから最新納期（PUCH_ODR_DLV_DATE DESC）のレコードを選択
- `UNIT_COST`をSRPRICEに設定
- `VEND_CD`をSRCDに設定
- ログに「フォールバック取得」メッセージを出力

---

### テストケース3: どちらでも見つからない

**入力:**
- 前工程: `XYZ-99999`
- M_PUCH_UNIT_COST_Hに該当レコードなし
- T_RLSD_PUCH_ODRに該当レコードなし

**期待される動作:**
- SRPRICE = `0`
- SRCD = `""`（空文字）

---

### テストケース4: PEFIN例外処理

**入力:**
- 前工程: `PEFIN-ABC123`
- KTCD = `PEFIN`

**期待される動作:**
- データベース検索を行わず（または結果を無視）
- SRPRICE = `0.0`（固定値）
- SRCD = `""`（空文字）
- LDTIME = `0`
- CSBCD = `'10'`
- RCVTSTKBN = `'2'`
- RCVCHKKBN = `'2'`

---

## 9. エラーハンドリング

### 9.1 データベース接続エラー

```python
try:
    combined_df = ej_data_get(srcd_srprice_sql)
except Exception as e:
    print(f"統合データ取得エラー: {e}")
    srcd_srprice_dict = {}
    # 空の辞書で継続（全てフォールバックまたは0になる）
```

### 9.2 フォールバック取得エラー

```python
try:
    fallback_df = ej_data_get(fallback_sql)
except Exception as e:
    print(f"フォールバック用データ取得エラー: {e}")
    fallback_srcd_dict = {}
    fallback_srprice_dict = {}
    # 空の辞書で継続（全て0になる）
```

---

## 10. パフォーマンス最適化

### 10.1 辞書による高速検索

**実装:**
```python
# 全データを一度に取得してメモリ上で辞書化
srcd_srprice_dict = {}
for _, record in combined_df.iterrows():
    item_cd = record['ITEM_CD']
    if item_cd not in srcd_srprice_dict:
        srcd_srprice_dict[item_cd] = { ... }

# 各レコード処理時はO(1)で検索
record_data = srcd_srprice_dict.get(zenkatei_key, {})
```

**利点:**
- レコードごとにSQL実行する必要がない（N+1問題の回避）
- 検索がO(1)で高速

### 10.2 ORDER BYによるソート

**実装:**
```sql
ORDER BY h.ITEM_CD,
         h.PUCH_PRIORITY_REF_NO ASC,
         c.EFF_PHASE_IN_DATE DESC,
         c.PUCH_SIZE ASC
```

**利点:**
- データベース側でソートされるため、Pythonで複雑な比較処理が不要
- 最初のレコードを採用するだけで最優先レコードが確定

---

## 11. 実装チェックリスト

実装時に以下の項目を確認してください：

- [ ] M_PUCH_UNIT_COST_HとM_PUCH_UNIT_COSTをINNER JOINしている
- [ ] WHERE句に`PUCH_PRIORITY_REF_NO IS NOT NULL`を含めている
- [ ] WHERE句に`EFF_PHASE_IN_DATE < TO_DATE('2025-12-01', 'YYYY-MM-DD')`を含めている
- [ ] ORDER BYで`PUCH_PRIORITY_REF_NO ASC, EFF_PHASE_IN_DATE DESC, PUCH_SIZE ASC`を指定している
- [ ] ITEM_CDごとに最初のレコード1行のみを採用している
- [ ] SRCDとSRPRICEを同一レコードから取得している
- [ ] 検索キーに前工程（zenkatei_key）を使用している（完成部番ではない）
- [ ] プライマリで見つからない場合、T_RLSD_PUCH_ODRでフォールバック検索している
- [ ] T_RLSD_PUCH_ODRでは最新納期（PUCH_ODR_DLV_DATE DESC）のレコードを採用している
- [ ] KTCD='PEFIN'の場合、SRPRICE=0を固定設定している
- [ ] どちらでも見つからない場合、SRPRICE=0, SRCD=""を設定している
- [ ] NULL値のチェックと初期値設定を実装している
- [ ] エラーハンドリングを実装している（try-exceptブロック）
- [ ] フォールバック取得時にログ出力している

---

## 12. 実装例の完全版（まとめ）

以下は、上記仕様に基づく完全な実装例です：

```python
import pandas as pd
import cx_Oracle

def ej_data_get(sql):
    """EJシステム（Oracle Database）に接続してSQLを実行する"""
    try:
        host = '172.17.107.102'
        port = '1521'
        service_name = 'EXPJ'
        username = 'EXPJ2'
        password = 'EXPJ2'
        connection_string = f"{username}/{password}@{host}:{port}/{service_name}"
        connection = cx_Oracle.connect(connection_string)
        df = pd.read_sql(sql, connection)
        connection.close()
        return df
    except Exception as e:
        print(f"EJシステムへの接続でエラーが発生しました: {str(e)}")
        raise

# ===== SRPRICE取得処理 =====

# 1. プライマリデータソース取得
print("=== EJシステム（M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COST）統合データ取得 ===")
try:
    srcd_srprice_sql = """
    SELECT h.ITEM_CD, h.VEND_CD, h.PUCH_PRIORITY_REF_NO,
           c.UNIT_COST, c.EFF_PHASE_IN_DATE, c.PUCH_SIZE
    FROM EXPJ2.M_PUCH_UNIT_COST_H h
    INNER JOIN EXPJ2.M_PUCH_UNIT_COST c
    ON h.ITEM_CD = c.ITEM_CD AND h.VEND_CD = c.VEND_CD
    WHERE h.PUCH_PRIORITY_REF_NO IS NOT NULL
    AND c.EFF_PHASE_IN_DATE < TO_DATE('2025-12-01', 'YYYY-MM-DD')
    ORDER BY h.ITEM_CD, h.PUCH_PRIORITY_REF_NO ASC,
             c.EFF_PHASE_IN_DATE DESC, c.PUCH_SIZE ASC
    """
    combined_df = ej_data_get(srcd_srprice_sql)
    print(f"統合データ取得: {len(combined_df)}行")

    srcd_srprice_dict = {}
    for _, record in combined_df.iterrows():
        item_cd = record['ITEM_CD']
        if item_cd not in srcd_srprice_dict:
            srcd_srprice_dict[item_cd] = {
                'SRCD': record['VEND_CD'],
                'SRPRICE': record['UNIT_COST'],
                'EFF_PHASE_IN_DATE': record['EFF_PHASE_IN_DATE'],
                'PUCH_SIZE': record['PUCH_SIZE'],
                'PRIORITY': record['PUCH_PRIORITY_REF_NO']
            }
    print(f"1行選定辞書作成: {len(srcd_srprice_dict)}件")
except Exception as e:
    print(f"統合データ取得エラー: {e}")
    srcd_srprice_dict = {}

# 2. フォールバックデータソース取得
print("=== EJシステム（T_RLSD_PUCH_ODR）フォールバックデータ取得 ===")
try:
    fallback_sql = """
    SELECT ITEM_CD, VEND_CD, UNIT_COST, PUCH_ODR_DLV_DATE
    FROM EXPJ2.T_RLSD_PUCH_ODR
    WHERE ITEM_CD IS NOT NULL AND VEND_CD IS NOT NULL
    ORDER BY ITEM_CD, PUCH_ODR_DLV_DATE DESC
    """
    fallback_df = ej_data_get(fallback_sql)
    print(f"フォールバック用データ取得: {len(fallback_df)}行")

    fallback_latest = fallback_df.groupby('ITEM_CD').first().reset_index()
    fallback_srcd_dict = dict(zip(fallback_latest['ITEM_CD'], fallback_latest['VEND_CD']))
    fallback_srprice_dict = dict(zip(fallback_latest['ITEM_CD'], fallback_latest['UNIT_COST']))
    print(f"フォールバック辞書作成: {len(fallback_srcd_dict)}件")
except Exception as e:
    print(f"フォールバック用データ取得エラー: {e}")
    fallback_srcd_dict = {}
    fallback_srprice_dict = {}

# 3. 各レコードに対してSRPRICE取得
output_data = []
for idx, row in work_df.iterrows():
    zenkatei = str(row['前工程']) if pd.notna(row['前工程']) else ''
    kansei_bango = str(row['完成部番']) if pd.notna(row['完成部番']) else ''

    # KTCDを計算
    if '-' in zenkatei:
        ktcd = zenkatei.split('-')[0]
    else:
        ktcd = zenkatei

    if ktcd == "A0":
        ktcd = "AO"
    elif ktcd in ["PA1", "PA2"]:
        ktcd = "PA"

    # 前工程をキーとして使用
    zenkatei_key = zenkatei

    # PEFIN例外処理
    if ktcd == 'PEFIN':
        srcd_value = ''
        srprice_value = 0.0
    else:
        # 統合辞書からSRCD/SRPRICE一貫取得
        record_data = srcd_srprice_dict.get(zenkatei_key, {})
        srcd_value = record_data.get('SRCD', '')
        srprice_value = record_data.get('SRPRICE', 0)

        # フォールバック取得
        if not srcd_value:
            srcd_value = fallback_srcd_dict.get(zenkatei_key, "")
            srprice_value = fallback_srprice_dict.get(zenkatei_key, 0)
            if srcd_value:
                print(f"フォールバック取得: {zenkatei_key} -> SRCD: {srcd_value}, SRPRICE: {srprice_value}")

    # 最終値設定
    srprice_final = float(srprice_value) if srprice_value is not None else 0.0
    srcd_final = str(srcd_value) if srcd_value else ''

    output_data.append({
        'HMCD': kansei_bango,
        'KTCD': ktcd,
        'SRCD': srcd_final,
        'SRPRICE': srprice_final,
        # ... その他のフィールド
    })

# 4. 出力
output_df = pd.DataFrame(output_data)
output_df.to_csv('M0840_品目工程マスタ.csv', encoding='utf-8-sig', index=False)
print(f"出力完了: {len(output_df)}行")
```

---

## 13. よくある質問（FAQ）

### Q1: なぜSRCDとSRPRICEを同一レコードから取得する必要があるのか？

**A:** 仕入先ごとに購入単価が異なるため、SRCDとSRPRICEが別のレコードから取得されると、「仕入先Aの単価が仕入先Bのものになる」といった不整合が発生します。

### Q2: なぜ検索キーは完成部番ではなく前工程なのか？

**A:** M0840品目工程マスタは「完成部番（HMCD）の各工程（KTCD）」を管理するテーブルです。各工程の購入単価やリードタイムは、その工程で使用する材料（前工程）に紐づくため、前工程をキーにする必要があります。

### Q3: なぜ日付フィルタが2025-12-01なのか？

**A:** システム移行日が2025年12月1日であり、それ以降のデータは新システムで管理されるためです。将来適用予定の単価が誤って選択されないようにするフィルタです。

### Q4: PEFIN工程が例外処理される理由は？

**A:** PEFIN（表面処理）工程は外部委託工程であり、通常の購入単価管理とは異なる管理方法を取るためです。この工程では単価ではなく別の管理方法（工程単価など）を使用します。

---

以上がSRPRICE取得ロジックの完全な実装仕様書です。この仕様書に従えば、AIが同じ実装を正確に再現できます。
