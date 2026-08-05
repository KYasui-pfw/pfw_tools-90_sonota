# process1.py 仕様書

## 概要

rBOM ディレクトリから4つのCSVファイルを読み込み、加工・変換してKakouDenpyoディレクトリに出力する前処理です。

---

## 入力ファイル

| ファイル | 環境変数 | 説明 |
|----------|----------|------|
| CAMKakouDenpyou.csv | CSV1_PATH | CAM加工伝票 |
| CONV.csv | CSV2_PATH | コンバージョン |
| SEISANKI.csv | CSV3_PATH | 生産機 |
| ASPKakouDenpyo.csv | CSV4_PATH | ASP加工伝票 |

---

## 出力ファイル

| 入力 | 出力 | 処理内容 |
|------|------|----------|
| CAMKakouDenpyou.csv | 4-01 CAMKakouDenpyo.csv | 項目削除・重複削除・カラム名変更・並び替え |
| CONV.csv | 4-01 CONV.csv | 0行フィルタ・重複削除 |
| SEISANKI.csv | 4-01 SEISANKI.csv | 0行フィルタ・重複削除 |
| ASPKakouDenpyo.csv | 4-03 ASPKakouDenpyo.csv | **高度な重複削除**・項目削除・カラム名変更・並び替え |

---

## 処理フロー

```
1. 環境変数からCSVパスを取得
       ↓
2. 各CSVファイルを順次処理:
   ├─ エンコーディング自動判定（utf-8-sig → utf-8 → cp932 → shift_jis → latin1）
   ├─ ファイル種別に応じた加工処理
   └─ CP932エンコーディングで出力
       ↓
3. 処理結果サマリーをログ出力
```

---

## 処理詳細

### CAMKakouDenpyou.csv（通常処理）

1. **カラム削除**: `DELETE_COLUMNS_FILE1` で指定されたカラムを削除
2. **カラム名変更**: `RENAME_COLUMNS_FILE1` でマッピング（例：`仕入先コード:払出先`）
3. **重複削除**: 全カラムで単純な `drop_duplicates()`
4. **型変換**: 生産月次・払出先をint型に変換（空欄は保持）
5. **カラム並び替え**: `REORDER_COLUMNS_FILE1` で指定順に並び替え

### CONV.csv / SEISANKI.csv（0行フィルタ処理）

1. **0行フィルタ**: 「数量」「セットアップ」「スペア」が全て0の行を削除
2. **重複削除**: 全カラムで単純な `drop_duplicates()`

### ASPKakouDenpyo.csv（高度な重複削除処理）

1. **API呼び出し**: FastAPI `/instructions/slip/batch` に `(伝票No, 行番号)` を送信
2. **OYALISTNO取得**: APIからOYALISTNO（親リスト番号）を取得
3. **MCKR事前記録**: `工程コード=MCKR` かつ特定5部品の伝票NoをSetに記録（この後の列削除で `工程コード` が消えるため、削除前に実施）
4. **1段階目重複削除**: `(伝票No, OYALISTNO)` でグループ化 → 各グループの1行目を保持
5. **2段階目重複削除**: 同一伝票Noで異なるOYALISTNOがある場合 → 必要数を合計して1行に集約
6. **MCKR複製**: 手順3で記録した伝票Noの行を複製し、複製行の払出先を60に変更して元行の直下に挿入
7. **カラム削除**: `DELETE_COLUMNS_FILE2` で指定されたカラムを削除（`工程コード` 含む）
8. **カラム名変更**: `RENAME_COLUMNS_FILE2` でマッピング
9. **型変換**: 生産月次・払出先をint型に変換（空欄は保持）
10. **組立開始日上書き**: 生産月次の末尾が `0`・`9`・`_` の行について、D3010.DEADLINEで組立開始日を上書き（`YYYY/MM/DD`形式）
11. **カラム並び替え**: `REORDER_COLUMNS_FILE2` で指定順に並び替え

---

## 高度な重複削除（Advanced Deduplication）

### 目的

同一伝票Noで複数の親リスト（OYALISTNO）を持つデータを適切に集約する。

### 処理フロー

```
1. FastAPI にバッチリクエスト（100件/バッチ）
       ↓
2. レスポンスから OYALISTNO を取得
   ※ FastAPIは大文字キー（INDNO, LINENO, OYALISTNO）で返却
       ↓
3. 1段階目: (伝票No, OYALISTNO) でグループ化
   → 各グループの1行目のみ保持
       ↓
4. 2段階目: 同一伝票Noで異なるOYALISTNO
   → 必要数を合計して1行に集約
       ↓
5. OYALISTNOカラムを削除（作業用）
```

### ログ出力例

```
  FastAPI に 5000 件のデータをリクエスト中...
  100件ずつのバッチ処理を実行します
    バッチ 1/50: 100件を処理開始...
      → 完了: 100件取得, 所要時間: 1.23秒
  ...
  1段階目重複削除: 500行削除 → 4500行
  2段階目重複削除: 100行削除（必要数を集約） → 4400行
  合計重複削除: 600行削除 → 4400行
```

---

## MCKR複製（duplicate_mckr_rows）

### 目的

`17_EJ_rBOM_ASPKAKOUDEPYO_mapping/asp_kakou_mapping.py` の時限処理と連携し、特定5部品のMCKR工程について払出先=60 の行を出力に含める。

asp_kakou_mapping.py 側では「特定5部品の払出先=40を除外・60は通過」するため、process1.py 側で払出先=60 のコピー行を生成することで、最終マッピング対象に含められる。

### 特定5部品リスト

```python
['SINKER REST RING', 'NEEDLE DIAL', 'NEEDLE CYLINDER', 'SINKER DIAL', 'WRAP DIAL']
```

### 処理フロー

```
列削除前に: 部品名 ∈ 特定5種 かつ 工程コード=MCKR の 伝票No を Set に記録
       ↓
（列削除で 工程コード 消える）
       ↓
重複削除後に: 記録した伝票No の行を特定
       ↓
該当行の直下にコピー行を挿入（払出先 40 → 60、他は同一）
```

### 出力イメージ

```
... | NEEDLE DIAL | ... | 40 | ...   ← 元行（払出先=40）
... | NEEDLE DIAL | ... | 60 | ...   ← 複製行（払出先=60）
```

### 注意事項

- `工程コード` は `DELETE_COLUMNS_FILE2` で削除されるため、事前記録が必須
- 重複削除（dedup）の**後**に複製する。重複削除前に挿入すると `(伝票No, OYALISTNO)` が同じため一方が除去される
- asp_kakou_mapping.py の時限処理ブロック（20260122追加）と同期して管理すること

---

## 組立開始日上書き（D3010 DEADLINE参照）

### 目的

生産月次の末尾値が特定の文字の行は締め日系の計画データであり、rBOMのD3010に登録されたDEADLINEを組立開始日として使用する。

### 処理フロー

```
1. 生産月次の末尾1文字が 0・9・_ の行を抽出
       ↓
2. 対象行の製番（SEINO）を収集（ユニーク）
       ↓
3. FastAPI /query で D3010 に SEINO IN (...) 検索（100件バッチ）
       ↓
4. 取得した DEADLINE を YYYY/MM/DD 形式に変換
       ↓
5. 対象行の組立開始日を上書き
   ※ D3010 に SEINO が存在しない行はスキップ（上書きなし）
```

### ログ出力例

```
  D3010上書き開始: 生産月次末尾=0の行 120件
  対象製番: 45件
  D3010取得: 43件のDEADLINEを取得
  D3010上書き完了: 更新=118件, D3010未取得=2件
```

---

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| CSV1_PATH | CAMKakouDenpyou.csv パス | （必須） |
| CSV2_PATH | CONV.csv パス | （必須） |
| CSV3_PATH | SEISANKI.csv パス | （必須） |
| CSV4_PATH | ASPKakouDenpyo.csv パス | （必須） |
| OUTPUT_DIR_DENPYO | 出力先ディレクトリ | /app/output/KakouDenpyo |
| DELETE_COLUMNS_FILE1 | 削除カラム（CAM用、カンマ区切り） | （空） |
| DELETE_COLUMNS_FILE2 | 削除カラム（ASP用、カンマ区切り） | （空） |
| RENAME_COLUMNS_FILE1 | カラム名変更（CAM用、`old:new,old2:new2`形式） | （空） |
| RENAME_COLUMNS_FILE2 | カラム名変更（ASP用、`old:new,old2:new2`形式） | （空） |
| REORDER_COLUMNS_FILE1 | カラム並び順（CAM用、カンマ区切り） | （空） |
| REORDER_COLUMNS_FILE2 | カラム並び順（ASP用、カンマ区切り） | （空） |
| FASTAPI_BASE_URL | FastAPI URL（高度な重複削除用） | http://fastapi-rbom-app:8000 |
| READ_API_KEY | 読み取り用APIキー | （必須） |
| LOG_DIR | ログ出力先 | /app/logs |
| LOG_RETENTION_DAYS | ログ保持日数 | 7 |

---

## 注意事項

### カラム名の一致

`REORDER_COLUMNS_FILE2` で指定するカラム名は、CSVファイルのカラム名と完全一致する必要があります。

- **正**: `伝票No`（半角N）
- **誤**: `伝票Ｎｏ`（全角Ｎ）

### エンコーディング

- 入力: 自動判定（utf-8-sig → utf-8 → cp932 → shift_jis → latin1）
- 出力: CP932（Shift-JIS）

### ファイルパーミッション

出力ファイルには自動的に 666 パーミッションが設定されます。

---

## 実行タイミング

- 15分ごと（cron）
- process2.py と並列実行

---

## ログ出力

- ファイル: `process1_YYYYMMDD.log`
- 場所: `/app/logs/`
- 保持期間: 7日間（自動削除）

---

## 関連ファイル

| ファイル | 説明 |
|----------|------|
| process1.py | メイン処理スクリプト |
| logger_config.py | ロギング設定モジュール |
| run_all.sh | 全処理実行ラッパー |
