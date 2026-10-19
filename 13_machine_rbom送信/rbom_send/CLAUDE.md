# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Machine Data rBOM送信システム - PostgreSQL (iRepoDB) から機械データを取得し、FastAPI rBOMシステムに自動送信する統合処理。

**Core Flow:**
1. PostgreSQL `view_report_405` + 19テーブル → データ取得
2. 月次フィルタリング（当月・翌月・翌々月）
3. パターン分岐処理（パターン1: LINENO=1のみ / パターン3: 全LINENO）
4. FastAPI completion エンドポイント送信

## Quick Start Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run main script
python machine_data_extract.py

# Or use batch file
machine_data_extract.bat

# Check database columns (utility)
python check_columns.py
```

⚠ **専用venvは無い。システムPythonの `python` で直接動く。**`machine_data_extract.bat` の
venvアクティベート行はコメントアウトされたままで、`90_tools` の共通venv
（`09_EJ_rBOM_マッピング２/venv`）も使わない。`requirements.txt` はシステムPythonに入れる想定。

### 動作確認（テストスイートは無い）

`python machine_data_extract.py` を素で実行すると**本番rBOMに実績を書き込む**（`POST /completion/`）。
安全に検証するには `send_completion_record()` を差し替えて `main_async()` を回す。
DB・APIの読み取りは本物のまま、書き込みだけ止まる。

```python
import asyncio, logging, machine_data_extract as m
m.logger = logging.getLogger('dry'); m.logger.addHandler(logging.StreamHandler())
m.logger.setLevel(logging.INFO)
sent = []
async def fake_send(client, url, key, payload, row_info=""):
    sent.append(payload); return True, "DRYRUN"
m.send_completion_record = fake_send
asyncio.run(m.main_async())   # setup_logger() を通さないので本番ログを汚さない
print(len(sent), sent[:3])
```

`main()` ではなく `main_async()` を直接呼ぶこと（`main()` は `setup_logger()` で
`logs/machine_extract_YYYYMMDD.log` に追記してしまう）。
変更の影響を測るときは、対象ロジックを無効化した版と2回走らせてA/B比較するとよい。

### Production Deployment
- **Execution frequency**: 15分間隔（タスクスケジューラ設定上）。⚠ 実際の本番ログ（`logs/machine_extract_*.log`）のタイムスタンプを見ると毎時ほぼ同一分（例: 23:10, 22:10, 21:10）にしか実行記録が無く、実質1時間間隔で動いているように見える。タスクスケジューラの実設定と乖離している可能性があるため、実行間隔が問題になる調査の際は思い込まずログの実タイムスタンプで確認すること
- **Target server**: Windows Server
- **Logs**: `./logs/machine_extract_YYYYMMDD.log` (7日保持)
- **Debug CSV**: `./output/machine_data_YYYYMMDD_HHMMSS.csv` (ENABLE_CSV_OUTPUT=true時のみ)
  - ⚠ **現行の `.env` は `ENABLE_CSV_OUTPUT=true`**（既定値の説明とは逆）。実行ごとに1ファイル増え、
    ログと違って**自動削除の仕組みが無い**ため `output/` に溜まり続ける（2026-09-07時点で53ファイル）

### ⚠ このディレクトリのファイルについて

- **`README.md` は信用しないこと。** 2025-11時点のもので、パスが全て旧構成
  （`C:\Dev\90_tools\13_machine\` ＝現在の `13_machine_rbom送信\rbom_send\`）、
  存在しないログ名（`machine_send_YYYYMMDD.log`）、パターン1を「500件→1回のAPI呼び出し」と説明
  （現在は `INSTRUCTIONS_BATCH_CHUNK_SIZE=100` で分割）等、実装とずれている。**このCLAUDE.mdが正**
- **`missing.txt`** はどのコード・batからも参照されない置き土産（CH系ロット番号の一覧、2026-07-30）
- **`db/lot_mapping.db`** は `90_tools/14_lot番号マッピング` が生成するDBのコピー。
  内容は **2026-07-16 までのスナップショット**で止まっており、それ以降に採番されたロット番号は
  変換できず `指示データ取得失敗` に毎回並ぶ（CH系186件が該当）。
  変換が効かない話を追うときは、まずこのDBの `max(created_at)` を確認すること

## Architecture & Key Design Patterns

### 1. Two-Pattern Processing Architecture

**Pattern 1 (cluster flags):**
- Filters rows where `cluster_1_24_n` ~ `cluster_1_636_n` (any) = 1.0
- Sends **LINENO=1 only**
- Uses batch API: `/instructions/slip/batch` (1 API call for N records)
- Performance: 500 records = 500 calls → **1 call**

**Pattern 3 (judge column):**
- Filters rows where judge column (e.g., `cluster_1_641_t`) = '2' or '4'
- Sends **all LINENOs** for each INDNO
- Uses monthly API: `/instructions/?year=YYYY&month=MM` (max 3 calls)
- Groups instructions by INDNO, iterates all LINENOs

### 2. Multi-Table Pattern 3 Configuration (.env-driven)

20テーブル（`PATTERN3_TABLES` の要素数）を `.env` 設定で動的処理。同一の設定パターン（FROM_API + 年月分離日付 + 判定カラム'2'/'4'）が複数の帳票シリーズで再利用されている：

- `393`〜`398`: 編機調整報告書（生産機、6バリエーション。SEINO=top_remarks4, KTCD=`KNIT`固定, JUDGE=`cluster_2_166_t`）
- `572`〜`577`: 【必須無】編機調整報告書（393〜398と同じ帳票の必須項目なし版。設定は393〜398と同一パターン）
- `636`〜`638`, `747`, `751`, `752`: 本体GRチェックシート（636-638=生産機／747,751,752=整備機。KTCD=`FASSY`固定, JUDGE=`cluster_2/3/4_397_t`〈テンプレートの行数違いでカラム番号がテーブルごとに異なる〉, IPTANCD=`SECT1786`）

新しい帳票シリーズを追加する際は、対応する進捗確認画面（例: `90_tools/50_tools/hontaigr_checksheet/pages/6進捗確認画面.py`）を参考にテーブル名・SEINO/KTCD/判定カラムを特定し、.envに`PATTERN3_<ID>_*`を追加するだけでよい（コード変更不要）。KTCD・IPTANCDの固定値はrBOM D3420マスタの実データと突き合わせて検証すること（本番Postgres/FastAPI `/query` に直接接続して確認可能）。

```ini
PATTERN3_TABLES=view_report_405,view_report_334,view_report_393,...

# Per-table configuration (4 patterns supported):
# Pattern A: Direct INDNO + Single date column (YYYYMMDD)
# Pattern B: Direct INDNO + Separate year/month columns
# Pattern C: API-fetched INDNO (SEINO+KTCD) + Single date
# Pattern D: API-fetched INDNO + Separate year/month

PATTERN3_405_SOURCE_TABLE=view_report_405
PATTERN3_405_INDNO_COLUMN=cluster_1_2_t          # Direct INDNO
PATTERN3_405_JUDGE_COLUMN=cluster_1_641_t        # '2' or '4'
PATTERN3_405_DATE_COLUMN=top_remarks3            # YYYYMMDD format
PATTERN3_405_IPTANCD=SECT1557

PATTERN3_393_INDNO_COLUMN=FROM_API               # Fetch via API
PATTERN3_393_SEINO_COLUMN=top_remarks4           # SEINO for API
PATTERN3_393_KTCD_COLUMN=KNIT                    # Fixed KTCD value
PATTERN3_393_DATE_COLUMN=top_remarks1,top_remarks2  # Year,Month
```

主要関数は末尾の「Key Code Locations」表を参照。

### 3. INDNO Mapping System (F000→H000 Conversion)

**Database:** `./db/lot_mapping.db` (SQLite)
**Table:** `mapping_results` (lot_number, indno)

**Logic (load_indno_mapping, 154-199行):**
- 同一 lot_number に複数 indno が存在する場合、**数値部分が最小**のものを採用
- 例: H00001, H00002, H00003 → **H00001** を選択
- API取得/送信の**前**に変換実行（変換後INDNOでキャッシュ検索）

### 3-2. 特定5部品の実績返却先リダイレクト（払出先60 → 払出先40）

**対象部品（`SPECIAL_PART_NAMES`）:** `SINKER REST RING` / `NEEDLE DIAL` / `NEEDLE CYLINDER` / `SINKER DIAL` / `WRAP DIAL`

**背景:** 現品票発行（`90_tools/50_tools/genpin_check/1_現品票発行.py` の時限処理 20260115追加）が
この5部品だけ「払出先(`D3410.SRCD`)=40を除外・60を通過」させているため、**40側の伝票には現品票が出ず、
i-Reporter のチェックシートは60側にしか作られない**。結果として実績は60側にしか返らず、
40側の指示が `STATUS='1'` のまま残り続けていた（NEEDLE CYLINDER だけで339件が該当）。

**動作:** 5部品に限り、i-Reporter が持つINDNO（＝60側）を**同一SEINO・同一OYALISTNOで払出先40のINDNOに差し替えて**送信する。

```
i-Reporter の INDNO → D3420.LISTNO → D3110 で親を引く（OYALISTNO）
  → 同一 (SEINO, OYALISTNO) を持つ D3420 のうち D3410.SRCD='40' の INDNO
```

- ⚠ **60側へは送信しない（差し替え。追加送信ではない）**
- LINENOの範囲は現行どおり（パターン1 = LINENO=1のみ / パターン3 = 差し替え先の全LINENO）
- i-Reporter のINDNOが既に払出先40の場合はそのまま送信する
- 40側が複数伝票に分かれている場合（荒加工が2伝票に分割等）は**全てに送信**する
- 5部品だが40側が見つからない場合は送信せずスキップし、`特定5部品リダイレクト先(払出先40)なし: N件 - ...` として1行にまとめてログ出力
- **`OYALISTNO`・`SRCD` は `GET /instructions/` の応答に含まれるため追加のDB問い合わせは不要**。
  月次データは `_MONTHLY_INSTRUCTIONS_CACHE` で実行中キャッシュされ、パターン1・パターン3・20テーブル間で共有される
- 検証: `(SEINO, OYALISTNO)` グループ 9,606件で品目(HMCD)の不一致は0件＝グループは常に単一品目

**主要関数:** `build_special_part_redirect_index()` (771-806行) / `resolve_special_part_targets()` (808-845行) / `get_target_year_months()` (756-769行)

**サマリーログ:** `完了: ... 特定5部品リダイレクト=P1:N件/P3:N件`

### 3-3. SEINO+HMCD による返却先INDNOの解決（405・`MODE=seino_hmcd`）

**背景:** INDNO は作業開始後に再発行されることがあり、旧INDNOに実績を送っても現行INDNOが未完了のまま残る。
実データ（2026-07〜12月の405完了行4,092INDNO）では、2026-09生産月次の約6割（967件中581件）で旧INDNOが
D3420・D3410から**物理削除**されていた。このため i-Reporter のINDNOではなく、
「同一SEINO・同一HMCD で 払出先(SRCD)=40」の現行INDNOへ送る。

**対象:** 405（マシニング課）のパターン3のみ。パターン1・他テーブルは従来どおり（INDNO+LINENO）。
`.env` で有効化する。**未設定なら従来動作**（戻すときは3行を消すだけ）:
```ini
PATTERN3_405_MODE=seino_hmcd
PATTERN3_405_SEINO_COLUMN=top_remarks2    # SEINO末尾（短縮されている。4桁が大半）
PATTERN3_405_HMCD_COLUMN=cluster_1_3_t    # HMCD
```

**動作（`resolve_targets_by_seino_hmcd()`）:**
1. i-Reporter のロット番号を従来どおりINDNOへ変換（`lot_mapping.db`）。
2. 旧INDNOが**月次指示データにある** → rBOM側の SEINO・HMCD を使い、SEINOは**完全一致**。
   **無い**（rBOM側で消えた） → 405の `top_remarks2`・`cluster_1_3_t` を使い、SEINOは**末尾一致**。
3. 月次指示データ（`/instructions/`・追加のAPI呼び出し不要）から「HMCD一致＋SEINO一致＋SRCD=40」のINDNOを全て求める。
4. 解決した**全INDNOの全LINENO**へ、各行の `THQTY` で送る（伝票分割でも全INDNOに送る。親LISTNO違いも区別しない）。
   送信可否判定（`is_sendable_status()`）は**解決後のINDNO**に対して行う。
5. 同一実行内で複数行が同じINDNOに解決された場合は1回だけ送る（`resolved_targets`）。

**前年以前の除外:** SEINO先頭2桁が数字ならそれを年（26=2026年）とみなし、今年（JST下2桁）より小さければ送らない。
**先頭が数字でないSEINO（`K7470` 等）は年を判定できないので除外せず送る**。年初は前年の製番が作業中でも送られない点に注意。

**送らずログに出すもの（理由別に1行ずつ集約）:**
| 理由 | ログ | レベル |
|---|---|---|
| SEINO・HMCD取得不可 | `SEINO・HMCD取得不可: N件` | ERROR |
| 払出先40に該当なし | `払出先40のSEINO+HMCD該当なし: N件` | ERROR |
| 末尾一致で別SEINOが複数（年を除いても特定不可） | `SEINO末尾一致が複数（特定不可）: N件` | ERROR |
| 前年以前の製番 | `前年以前の製番のため対象外: N件` | WARNING |

- ⚠ 「該当なし」の大半は `CH` から始まる番号（SEINO末尾 K0xx・HMCD `G-6503GD` 等）で、旧ロジックでも
  「指示データ取得失敗」で送れていなかった分と同じ種類。**実行のたびに同じ行がログに出る**（自然消滅しない）。
- ⚠ **旧INDNOが払出先60/49（40以外）の405行**は、同じSEINO+HMCDの40側へ付け替えて送る。40側が無ければ「該当なし」でスキップ。
- 特定5部品リダイレクト（3-2）はこのモードでは呼ばない（払出先40で絞るため不要）。`FROM_API` は405では使っていない（INDNOを直接読む）。
- `lot_mapping.db` への依存（入口のロット番号→INDNO変換）は残る。`KARI` ロットは従来どおり解決できない。

**検証（2026-10-19）:** dry-run で旧ロジックと比較し、旧の送信先は全て新でも送られ（旧のみ0件）、
新のみ16件（全て払出先40・26年・rBOM未完了）が追加された。年違い除外・数字なしSEINO・曖昧判定は合成データで単体確認。
旧INDNOが消えた587ロットは、405の末尾一致で555件が新INDNOを1つに特定（残り32件は該当なし）。

### 4. Sendable Status Logic

**Function:** `is_sendable_status()` (638-679行)

送信不可条件（優先順）:
1. `EDKKBN` = '1' or '2' → 完納済み
2. `STATUS` = '3', '4', '8' → 完了状態
3. `STATUS` = '9' → 中止
4. `SYORIZUMIKB` = '1' → 実績登録中

送信可能: 上記以外（未完了 or `SYORIZUMIKB='3'` 登録エラー）

### 5. Temporal Filtering (Time-Limited Processing) — 現在は無効

**Function:** `filter_out_202603_and_later()`

**Purpose:** Exclude data where `top_remarks3` ≥ 202603 (March 2026+)

**現在の状態: 無効（コメントアウト済み）。** 呼び出し箇所（`main_async()` 内のパターン1・パターン3）はいずれもコメントアウトされており、この時限処理は動作していない。関数定義自体は将来の再利用のため残置。

**Applied at（いずれもコメントアウト済み）:**
- パターン1: `filter_by_top_remarks3()` の直後
- パターン3: 各テーブルの `filter_by_date_column()` の直後

**再度有効化する場合:** 上記2箇所の `# df_...= filter_out_202603_and_later(...)` のコメントを外す（`========== 時限処理 ==========` で明示）。

**Implementation Notes:**
- Extracts first 6 chars of date column as YYYYMM
- Keeps only rows where YYYYMM ≤ 202602
- 通常の月次フィルタ（`filter_by_date_column`）が当月・翌月・翌々月のみを対象とするため、過去データは元々送信対象外（この時限処理とは別）

## Environment Variables (.env)

### Required
```ini
DB_URL=postgresql://postgres:cimtops@ESRV10/irepodb
FASTAPI_BASE_URL=http://pfw-api
READ_API_KEY=<your_read_key>
INSERT_API_KEY=<your_insert_key>
```

### Optional
```ini
ENABLE_CSV_OUTPUT=false              # true = debug CSV output
LOG_RETENTION_DAYS=7
LOT_MAPPING_DB_PATH=./db/lot_mapping.db
```

### Pattern 3 Tables
```ini
PATTERN3_TABLES=view_report_405,view_report_334,...
PATTERN3_<ID>_SOURCE_TABLE=...
PATTERN3_<ID>_INDNO_COLUMN=...       # or "FROM_API"
PATTERN3_<ID>_SEINO_COLUMN=...       # if FROM_API
PATTERN3_<ID>_KTCD_COLUMN=...        # column name or fixed value
PATTERN3_<ID>_JUDGE_COLUMN=...
PATTERN3_<ID>_DATE_COLUMN=...        # single or "year,month"
PATTERN3_<ID>_IPTANCD=...
PATTERN3_<ID>_MODE=...               # seino_hmcd = SEINO+HMCDで返却先INDNOを解決（3-3参照）
PATTERN3_<ID>_HMCD_COLUMN=...        # MODE=seino_hmcd のとき必須（SEINO_COLUMN はSEINO末尾のカラム）
```

## Data Flow Details

### PostgreSQL Columns (view_report_405)
- **107列取得** (generate_column_list, 250-269行):
  - `cluster_1_2_t` (INDNO)
  - `cluster_1_24_n` ~ `cluster_1_636_n` (52列, 12刻み) - Pattern 1 flags
  - `cluster_1_14_t` ~ `cluster_1_626_t` (52列)
  - `cluster_1_641_t` (判定カラム)
  - `top_remarks3` (YYYYMMDD日付)

### API Endpoints Used

**Read:**
- `GET /instructions/?year=YYYY&month=MM` - 月次全件取得（パターン3＋特定5部品リダイレクト用）
  - 応答には `SRCD`（払出先）・`OYALISTNO`・`LISTNO`・`HMNM`・`SEINO` も含まれるため、
    リダイレクト解決に `/query` での D3110/D3410 追加検索は不要
  - `_MONTHLY_INSTRUCTIONS_CACHE` により同一実行中は同じ月を再取得しない（20テーブル×3か月 → 最大3回）
- `POST /instructions/slip/batch` - 指示データ一括取得（パターン1）
  - Request: `[{"indno": "...", "lineno": 1}, ...]`
  - Response: キャッシュ対象4項目のみ (STATUS, SYORIZUMIKB, EDKKBN, THQTY)
  - **重要（分割送信）**: 大量のslip_keysを1回で送るとバックエンドのOracle呼び出しが call timeout（30秒, DPY-4024/ORA-03156）を超えてHTTP 500になる。`get_instructions_batch()` は `INSTRUCTIONS_BATCH_CHUNK_SIZE`（既定100件）ずつ分割してPOSTし、キャッシュをマージする。クライアント側 timeout は60秒
- `POST /query` - D3420からINDNO取得（FROM_API時）
  - Payload: `{"table": "D3420", "where": {"and": [{"SEINO": ...}, {"KTCD": ...}]}}`

**Write:**
- `POST /completion/` - 実績送信
  - Payload: `{"KTEDDT": "YYYY-MM-DD", "INDNO": "...", "lineno": 1, "IPTANCD": "SECT1557", "prdqty": 100.0, "ktedqty": 100.0}`

### Payload Mapping
```python
{
    "KTEDDT": datetime.now(JST).strftime('%Y-%m-%d'),  # システム日付
    "INDNO": send_indno,          # 変換後INDNO (from mapping or original)
    "lineno": lineno,             # Pattern 1: 1 / Pattern 3: 各LINENO
    "IPTANCD": "SECT1557",        # .env設定値
    "prdqty": THQTY,              # 指示データから取得
    "ktedqty": THQTY              # prdqtyと同じ
}
```

## Logging & Error Handling

### Log Files
- **Format**: `machine_extract_YYYYMMDD.log`
- **Rotation**: Daily at midnight (TimedRotatingFileHandler)
- **Retention**: 7 days (cleanup_old_logs)
- **Encoding**: UTF-8

### Log Levels
`print()` は1箇所も使っておらず、出力はすべて `logger` 経由。

- `INFO`: **`処理開始` と `完了: ...` の2行だけ**（成功したcompletion送信は個別に記録しない）
- `WARNING`: `THQTY が空` / `THQTY が数値変換不可` / `INDNOが空` / `SEINOが空` / `KTCDが空` / 各フィルタ後0件
- `ERROR`: 送信失敗（`送信失敗 [n/N]: INDNO=... - ...`）、集約系（`指示データ取得失敗: N件 - ...`、`特定5部品リダイレクト先(払出先40)なし: N件 - ...`）、API/DB例外

⚠ **「ログにそのINDNOが出てこない＝未送信」ではない。** 送信成功は一切ログに残らないため、
ログの沈黙は「成功した」「そもそも対象データが無かった」「送信不可状態で除外された」の
いずれとも区別できない。ある指示の実績が返らない理由を追うときは、ログではなく
**i-Reporter（irepodb）側にその帳票が存在するか**と **rBOM側 `D3420.STATUS`/`D3410.SRCD`** を直接見ること。

### 「指示データ取得失敗」のログ集約（2026-08-21〜）
`process_dataframe_data()`（パターン1）・`process_pattern3_table()`（パターン3）とも、rBOM側に対応する指示データが見つからないケースをループ内で都度 `logger.error` するのではなく、`missing_instructions` リストに蓄積し、処理完了後に**1行**（`指示データ取得失敗: N件 - indno1, indno2, ...`）にまとめて出力する。これは特定INDNO（i-Reporter側に残るがrBOM側D3420には存在しない仮伝票KARI等）が月次フィルタの範囲内（当月〜翌々月）にある限り実行のたびに再発し、個別ログのままだとログファイルが急速に肥大化していたための対策。対象月から2か月経過すると自動的に月次フィルタ対象外になりログも止まる（根本原因の解消ではなく自然消滅）。

⚠ **`パターン3-{idx}: {table} からのデータ取得失敗。スキップします。`というログは、PostgreSQL接続エラー時だけでなく、テーブルが単に0件だった場合にも同じ文言で出る**（`fetch_data_from_table()` が返す `None` と空DataFrameを区別していないため）。「必須無」版の編機調整報告書（572,574-577）や本体GRチェックシートの一部（638,747,751,752）は実データがほぼ0件のため、正常時でも毎回このエラーが出る。慌てず対象テーブルの実データ件数を本番Postgresで確認すること。

### Summary Output
`main_async()` 末尾の**1行だけ**。パターンごとの内訳（skip/blocked/converted）は
戻り値の辞書には入っているが**どこにも出力していない**。

```
完了: P1成功=17件/エラー=0件, P3成功=9件/エラー=0件, 特定5部品リダイレクト=P1:0件/P3:0件
```

終了コード: エラー0件なら `0`、1件以上あれば `1`（タスクスケジューラの成否判定に使われる）。

## Key Code Locations

| Function | Lines | Purpose |
|----------|-------|---------|
| `load_pattern3_configs()` | 82-153 | .env解析、バリデーション（`MODE`/`HMCD_COLUMN` もここ） |
| `load_indno_mapping()` | 173-218 | INDNO変換辞書読込 |
| `extract_data_from_postgres()` | 290-326 | PostgreSQL 107列取得（view_report_405固定） |
| `fetch_data_from_table(table_name)` | 328-356 | パターン3用の任意テーブル全カラム取得（0件とエラーを区別しない点に注意） |
| `fetch_indno_from_api()` | 358-406 | API経由INDNO取得（SEINO+KTCD→D3420検索） |
| `filter_by_top_remarks3()` | 408-420 | 月次フィルタ（view_report_405専用・後方互換） |
| `filter_by_date_column()` | 422-517 | 汎用月次フィルタ（単一/年月分離カラム対応） |
| `filter_by_cluster_flags()` | 519-551 | パターン1フラグ抽出 |
| `filter_by_judge_column()` | 567-613 | パターン3判定カラム |
| `filter_out_202603_and_later()` | 615-655 | **時限処理：202603以降除外（現在無効）** |
| `is_sendable_status()` | 657-701 | 送信可否判定 |
| `get_instructions_by_month()` | 703-754 | 月次取得（パターン3・実行中キャッシュあり） |
| `get_target_year_months()` | 756-769 | 対象月（当月・翌月・翌々月）の算出 |
| `build_special_part_redirect_index()` | 771-806 | 特定5部品リダイレクト用インデックス構築 |
| `resolve_special_part_targets()` | 808-845 | 特定5部品→払出先40のINDNO解決 |
| `get_cell_text()` / `get_seino_year()` | 847-859 | セル値の文字列化 / SEINO先頭2桁の年判定（seino_hmcd用） |
| `build_seino_hmcd_index()` | 861-878 | 払出先40の {HMCD: {(SEINO, INDNO)}} 索引（seino_hmcd用） |
| `resolve_targets_by_seino_hmcd()` | 880-945 | SEINO+HMCD→現行INDNO解決・前年除外・曖昧判定（seino_hmcd用） |
| `get_instructions_batch()` | 950-1016 | 一括取得（パターン1、100件分割） |
| `send_completion_record()` | 1018-1066 | completion API送信 |
| `process_dataframe_data()` | 1068-1240 | パターン1送信処理（指示データ取得失敗をまとめてログ出力） |
| `process_pattern3_table()` | 1265-1553 | パターン3送信処理（同上。`resolve_mode='seino_hmcd'` の分岐あり） |
| `main_async()` | 1555-1684 | メイン処理フロー |

## Testing & Debugging

### Enable CSV Output
```ini
# .env
ENABLE_CSV_OUTPUT=true   # 現行の .env は既にこの値
```
→ `./output/machine_data_YYYYMMDD_HHMMSS.csv` に中間結果出力（自動削除なし。上記の注意を参照）

### Check Columns
```bash
python check_columns.py
# → view_report_405のcluster列とremark列を一覧表示
```

### Manual Test Run
```bash
python machine_data_extract.py
# Check logs: ./logs/machine_extract_YYYYMMDD.log
```

⚠ これは**本番rBOMへの書き込みを伴う本番実行**であり、テストではない。
書き込まずに挙動を確かめる手順は「Quick Start Commands → 動作確認」を参照。

## Dependencies

```
sqlalchemy==2.0.23      # PostgreSQL ORM
psycopg2-binary==2.9.9  # PostgreSQL driver
pandas==2.1.4           # DataFrame処理
python-dotenv==1.0.0    # .env読込
httpx==0.25.2           # 非同期HTTP client
```

**Python**: 3.12+ required (JST timezone handling)

## Important Notes

### Timezone
- **JST = UTC+9** (datetime.now(JST))
- KTEDDT always uses Japanese time, not UTC

### Performance Optimization
- Pattern 1: Batch API reduces N calls → ceil(N/100) calls（Oracle call timeout回避のため100件ずつ分割。詳細は「API Endpoints Used」参照）
- Pattern 3: Monthly API reduces N×M calls → 3 calls (max)
- Instruction cache: Only 4 fields stored (STATUS, SYORIZUMIKB, EDKKBN, THQTY)

### INDNO Conversion Priority
1. Check lot_mapping.db
2. If multiple matches, select numerically smallest (e.g., H00001 over H00002)
3. Convert **before** API fetch/send
4. Log conversion count in summary

### Error Recovery
- Skip invalid rows (log warning)
- Continue processing on individual send failures
- Exit code: 0 if no errors, 1 if any errors
- All errors logged with traceback

### Pattern 3 Configuration Validation
- Required: SOURCE_TABLE, JUDGE_COLUMN, DATE_COLUMN, IPTANCD
- If INDNO_COLUMN="FROM_API": SEINO_COLUMN and KTCD_COLUMN also required
- Invalid configs logged and skipped (not fatal)

### Temporal Processing (202603+ Exclusion)
- **現在は無効（コメントアウト済み）**: `filter_out_202603_and_later()` の呼び出しはパターン1・パターン3ともコメントアウトされており動作しない
- **Location**: `main_async()` 内の `========== 時限処理 ==========` ブロック2箇所
- **To re-enable**: 上記2箇所のコメントを外す
- **Log marker**: `【時限処理】202603以降除外`
- 補足: 過去データの除外は通常の月次フィルタ（当月・翌月・翌々月のみ対象）が担っており、この時限処理とは別
