# process4.py 仕様書

## 概要

シリンダ（CYLINDER）・ダイアル（DIAL）の製造実績を rBOM FastAPI の `/completion` エンドポイントに送信する処理です。

---

## 入力ファイル

```
Cyl_pfw_table_KaLstCyl_All.csv
```

- Access DB（`Cyl_pfw_table.accdb`）から process2.py で抽出されたCSV
- 主要カラム: `DENPYONO`, `CAT2`, `resultStart`, `resultEnd`, `JOB_1`～`JOB_8`

---

## CAT2パターン判定

CAT2カラムの**末尾3文字**でシリンダ/ダイアルを判定：

| 末尾3文字 | 種別 | 例 |
|-----------|------|-----|
| `405` | CYLINDER | `S405`, `D405` |
| `409` | DIAL | `S409`, `D409` |

---

## 工程・品名マッピング

10個の日付カラムそれぞれに対して、KTCD（工程コード）とHMNM（品名）が定義されています。

### 405（CYLINDER）パターン

| 日付カラム | KTCD | HMNM |
|------------|------|------|
| resultStart | SL1ST | NEEDLE CYLINDER |
| resultEnd | SL1 | NEEDLE CYLINDER |
| JOB_8 | TQT | NEEDLE CYLINDER |
| JOB_1 | TY | NEEDLE CYLINDER |
| JOB_2 | DQT | NEEDLE CYLINDER |
| JOB_6 | BF | UNIT CYLINDER |
| JOB_4 | RST | UNIT CYLINDER |
| JOB_5 | G | UNIT CYLINDER |
| JOB_3 | FL | UNIT CYLINDER |
| JOB_7 | CYFIN | UNIT CYLINDER |

### 409（DIAL）パターン

| 日付カラム | KTCD | HMNM |
|------------|------|------|
| resultStart | SL1ST | NEEDLE DIAL |
| resultEnd | SL1 | NEEDLE DIAL |
| JOB_8 | TQT | NEEDLE DIAL |
| JOB_1 | TY | NEEDLE DIAL |
| JOB_2 | **DDQT** | NEEDLE DIAL |
| JOB_6 | BF | UNIT DIAL |
| JOB_4 | RST | UNIT DIAL |
| JOB_5 | G | UNIT DIAL |
| JOB_3 | FL | UNIT DIAL |
| JOB_7 | **DIFIN** | UNIT DIAL |

※ CYLINDERとDIALで異なるのは JOB_2（DQT/DDQT）と JOB_7（CYFIN/DIFIN）のみ

---

## 処理フロー

```
1. CSV全件読み込み（日付フィルタリングなし）
       ↓
2. 5ヶ月分の指示データを一括取得（前月～翌々々月）
       ↓
3. 各CSV行をループ処理:
   ├─ CAT2パターン判定（405/409）
   ├─ DENPYONO → lot_mapping.db でINDNO変換（任意）
   ├─ INDNO → FastAPI でSEINO（組立番号）取得
   ├─ 10個の日付カラムをチェック:
   │   ├─ 日付が入っていればマッピング取得
   │   ├─ SEINO + KTCD + HMNM で指示データ検索
   │   ├─ SL1/SL1STの場合はOYALISTNO前方一致検索
   │   ├─ 送信可能状態チェック
   │   └─ /completion に POST送信
   └─ 次の行へ
```

---

## lot_mapping.db マッピング

DENPYONOが `F000...` 形式の場合、`H000...` 形式のINDNOに変換します。

### 処理内容

```python
# 例: F000012345 → H000012345
if denpyono in lot_mapping:
    api_lookup_key = lot_mapping[denpyono]
```

### 重複処理

同一 `lot_number` に複数 `indno` がある場合、数値部分（先頭1文字を除く）が最小のものを選択します。

### データベース

- パス: `/app/data/lot_mapping.db`（環境変数 `LOT_MAPPING_DB_PATH` で指定）
- テーブル: `mapping_results`
- カラム: `lot_number`, `indno`

---

## SL1/SL1ST 特殊処理

KTCD が `SL1` または `SL1ST` の場合、OYALISTNO前方一致検索を実行します。

### 処理手順

1. 基準データ取得（SEINO + KTCD + HMNM で検索）
2. OYALISTNOから親品番を抽出（末尾ハイフン以降を削除）
   - 例: `25C11-01-130-20` → `25C11-01-130`
   - 例: `25DKJ002-240-20-40-10` → `25DKJ002-240-20-40`
3. 親品番で前方一致検索 → 1～3件ヒット
4. 各ヒットに対して completion 送信

### 目的

同一親品番に紐づく複数の指示データに対して、一括で完了実績を登録するため。

---

## 送信可能状態チェック

以下の条件で送信不可と判定します：

| 条件 | 値 | 判定 |
|------|-----|------|
| EDKBN（完納区分） | 1, 2 | 送信不可（完了済み） |
| STATUS | 3, 4, 8 | 送信不可（完了条件） |
| STATUS | 9 | 送信不可（中止） |
| SYORIZUMIKB | 1 | 送信不可（実績登録中） |
| 上記以外 | - | **送信可能** |

---

## API送信ペイロード

```python
payload = {
    "KTEDDT": kteddt,        # 日付カラムの値（YYYY-MM-DD形式）
    "INDNO": instruction.get('INDNO'),
    "lineno": instruction.get('LINENO'),
    "IPTANCD": "SECT1707",   # 固定値
    "prdqty": 1,             # 固定値
    "ktedqty": 1             # 固定値
}
```

### 送信先

- エンドポイント: `{FASTAPI_BASE_URL}/completion/`
- 認証: `X-API-KEY` ヘッダ（INSERT_API_KEY）

---

## 処理結果サマリー

| カウンタ | 内容 |
|----------|------|
| total | CSV総件数 |
| success | 送信成功件数 |
| skip | CAT2パターン不明・DENPYONOが空 |
| no_seino | SEINO取得失敗 |
| blocked | 送信不可状態により除外 |
| error | API送信失敗 |

---

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| PROCESS4_CSV_PATH | 入力CSVパス | /app/output/KakouJisseki/Cyl_pfw_table_KaLstCyl_All.csv |
| LOT_MAPPING_DB_PATH | lot_mapping.db パス | /app/data/lot_mapping.db |
| FASTAPI_BASE_URL | FastAPI URL | http://fastapi-rbom-app:8000 |
| READ_API_KEY | 読み取り用APIキー | （必須） |
| INSERT_API_KEY | 書き込み用APIキー | （必須） |
| LOG_DIR | ログ出力先 | /app/logs |
| LOG_RETENTION_DAYS | ログ保持日数 | 7 |

---

## 実行タイミング

- 15分ごと（cron）
- process3.py が成功した場合のみ実行

---

## ログ出力

- ファイル: `process4_YYYYMMDD.log`
- 場所: `/app/logs/`
- 保持期間: 7日間（自動削除）

### ログ出力例

```
[2026-01-15 10:30:00] [INFO] 処理4: CSV → FastAPI completion エンドポイント送信処理（シリンダ・ダイアル）を開始
[2026-01-15 10:30:01] [INFO] CSVファイルを読み込みました: /app/output/KakouJisseki/Cyl_pfw_table_KaLstCyl_All.csv (encoding: utf-8)
[2026-01-15 10:30:01] [INFO] データ件数: 1,234行, カラム数: 25
[2026-01-15 10:30:02] [INFO] 5ヶ月分の指示データを取得中（前月～翌々々月）...
[2026-01-15 10:30:05] [INFO]   2025年12月: 500件
[2026-01-15 10:30:06] [INFO]   2026年1月: 450件
[2026-01-15 10:30:07] [INFO]   2026年2月: 380件
[2026-01-15 10:30:08] [INFO]   2026年3月: 320件
[2026-01-15 10:30:09] [INFO]   2026年4月: 280件
[2026-01-15 10:30:09] [INFO] 5ヶ月分合計: 1,930件
[2026-01-15 10:30:10] [INFO]   [1/1234 列=resultStart] ✓ 送信成功: INDNO=H000012345, lineno=1, DATE=2026-01-10
```

---

## 関連ファイル

| ファイル | 説明 |
|----------|------|
| process4.py | メイン処理スクリプト |
| logger_config.py | ロギング設定モジュール |
| lot_mapping.db | DENPYONO→INDNOマッピングDB |
| run_all.sh | 全処理実行ラッパー |

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-11-22 | lot_mapping.db マッピング機能追加 |
| 2025-11-22 | SL1/SL1ST OYALISTNO前方一致検索追加 |
| 2025-11-22 | 5ヶ月分指示データ一括取得に変更（前月～翌々々月） |
