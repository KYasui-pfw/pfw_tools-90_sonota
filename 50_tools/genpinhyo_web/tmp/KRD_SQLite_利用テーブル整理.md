# KRD SQLite（krd_machine.db）の利用テーブル整理

調査日: 2026-10-23
対象: `C:\Dev\90_tools\50_tools\genpin_check`（現行の画面・スクリプト）
読み先: `\esrv11\KakouDenpyo\krd_machine.db`（`90_tools/15_krd_machine` が MySQL から同期）

## 1. 結論

SQLite の KRD は約52テーブルあるが、現品票システムが読んでいるのは **6テーブルだけ**。

| テーブル | 同期頻度 | 主な用途 |
|---|---|---|
| `DATA_ASP2_PUT` | 5分 | 伝票No → 工程バージョン(VERSION) |
| `MSTR_PROCODESTR` | 5分 | 加工部番 + VERSION → 工程コード文字列 |
| `DATA_KOUTEIZUKAN` | 1時間 | 加工部番 → 各図番（B/B2/F/F2/L/R/C/M） |
| `MSTR_METAL` | 5分 | 加工部番 → メッキ区分 |
| `DATA_RES_CAPA` | 5分 | 完成部番・Ver・工程順 → 工程・加工機コード |
| `MSTR_RES` | 5分 | 加工機コード → 加工機名 |

以下は読んでいない（現品票側から見れば同期不要）。
- 上記6テーブル以外の MySQL 由来テーブル（`KA_LIST01`〜`KA_LIST12` など）
- rBOM 由来の `_rBOM_MSTR_RES` / `_rBOM_DATA_RES_CAPA`
  - genpin_check 内に参照なし。確認済み: genpin_check と check_input
  - 別アプリ側（machining_schedule など）が使っている可能性は未確認

## 2. 画面別の利用テーブル

凡例: ○=使用

| 画面 / スクリプト | DATA_ASP2_PUT | MSTR_PROCODESTR | DATA_KOUTEIZUKAN | MSTR_METAL | DATA_RES_CAPA | MSTR_RES |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| ① メイン「現品票発行」`1_現品票発行.py`（Streamlit :8502） | ○ | ○ | ○ | ○ | | |
| ② `pages/2_現品票手入力発行.py`（Streamlit） | | ○ | ○ | | | |
| ③ `pages/4_iReporterチェック項目入力.py`（Streamlit・旧版） | | | ○ | | ○ | ○ |
| ④ `check_input/main.py`（NiceGUI :8506・③の後継） | | | ○ | | ○ | ○ |
| ⑤ `dbupdate.py`（DB更新モジュール） | ○ | ○ | ○ | ○ | | |
| ⑥ `create_report.py`（i-Reporter自動帳票作成・夜間処理） | ○ | ○ | ○ | ○ | | |

KRD を読まない画面: `pages/3_チェックシート再作成.py`、`pages/5_iReporter進捗確認.py`、`pages/95_管理画面.py`
（genpinhyo.db / checksheet.db / mapping_data.db だけを使う）

## 3. 画面ごとの詳細

### ① メイン `1_現品票発行.py`
- 呼び出し箇所: `db_update()` 内（198行〜）。「データ更新」ボタンと、セッション初回に実行される。
- 取得内容と用途:
  - `SELECT SLIP_NO as 伝票Ｎｏ, VERSION FROM DATA_ASP2_PUT`
    - 伝票No から工程VERSIONを取る。
    - lot_mapping.db で H始まり → F始まりに変換してから結合する。
    - 取れなければ VERSION=1 とする（`fillna(1)`）。
  - `SELECT FINAL_ITEM_CODE, VERSION, PROCODESTR FROM MSTR_PROCODESTR`
    - 加工部番 + VERSION で工程コード文字列を取る。
  - `SELECT SETU_F, B_FIG, B2_FIG, F_FIG, F2_FIG, L_FIG, R_FIG, C_FIG FROM DATA_KOUTEIZUKAN`
    - 各図番を取る。
  - `SELECT FIN_CODE, METAL FROM MSTR_METAL`
    - メッキ表示用。
- 各取得は try/except で、失敗時は空DataFrameで続行する。

### ② `pages/2_現品票手入力発行.py`
- 部番を入力したときに表示する。
  - `MSTR_PROCODESTR`（FINAL_ITEM_CODE, VERSION, PROCODESTR）→ 工程情報
  - `DATA_KOUTEIZUKAN`（`SELECT *`、`SETU_F==部番` で絞る）→ 図番情報
    - 使う列は SETU_F, B_FIG, B2_FIG, F_FIG, F2_FIG, L_FIG, R_FIG, C_FIG, M_FIG。

### ③ `pages/4_iReporterチェック項目入力.py`（旧・一部不具合あり）
- 画面表示のたびに `db_update1_on_view()` で同期する（10秒間引き）。
  - `DATA_RES_CAPA`（FINAL_ITEM_CODE, VERSION, PROCESS_CODE, PROCESS_ORDER, RES_CODE1）
  - `MSTR_RES`（CODE, NAME）→ 加工機名を結合し、checksheet.db の kouteizuban へ反映
- タブ1「加工機・図番 登録」の参考表示で `DATA_KOUTEIZUKAN`（`SELECT *`）を使う。

### ④ `check_input/main.py`（NiceGUI）
- 接続先は `KRD_DB = \esrv11\KakouDenpyo\krd_machine.db` に直書き。
- ページ表示時にバックグラウンドで `db_update1()` を実行する。
  - `DATA_RES_CAPA LEFT JOIN MSTR_RES`（RES_CODE1 = CODE）
  - kouteizuban に UPSERT する。KRD から消えた工程は削除して KRD に合わせる。
  - 0件、または削除対象が異常に多い場合は同期を中止する（安全弁）。
- タブ1の検索で `load_kouteizukan_filtered()` が `DATA_KOUTEIZUKAN` の SETU_F, F_FIG, F2_FIG, B_FIG, B2_FIG, L_FIG, R_FIG, C_FIG, M_FIG を読む。

### ⑤ `dbupdate.py` / ⑥ `create_report.py`
- ①と同じ4テーブルを同じSQLで読む。
- ⑥は夜間処理のi-Reporter自動帳票作成（ヘッダコメントより）。
- genpin_check 内に両者の呼び出し元は見つからなかった。外部のスケジューラ等から起動されている可能性がある。
- try/except が無く、読めないと処理ごと止まる（①は空でフォールバックする）。

## 4. 同期頻度との対応（15_krd_machine 側）

- 高頻度（5分）: `DATA_ASP2_PUT` / `MSTR_PROCODESTR` / `MSTR_METAL` / `DATA_RES_CAPA` / `MSTR_RES`
- 低頻度（1時間）: `DATA_KOUTEIZUKAN` ほか
- つまり使用6テーブルのうち、5分同期は5つで、1時間同期は `DATA_KOUTEIZUKAN` の1つ。

## 5. 対象外（参考）

次のものも同じ `krd_machine.db` を読んでいるが、保守対象の現行画面ではない。
- バックアップ・旧版・コピー
  - `genpin_check/backup/`、`履歴バックアップ/`、`pages/未使用/`、`pages/backup/`
  - `1_現品票発行_49排除前.py`、`1_現品票発行_49_60排除前.py`、`x1_現品票発行.py`、`pages/x4_*.py`
  - `genpin_check - コピー/`、`genpin_check_bk/`
- コピー（読み先は同じ）
  - `90_tools/75_genpin展開/4_iReporterチェック項目入力.py`（③のコピー）
  - `90_tools/90_temp/99_tmp/14_genpintyousa/check_input/`（④の調査用コピー）
  - `genpin_check/4_iReporterチェック項目入力.py`（ルート直下。pages/ 配下ではないため画面には出ない）

## 6. 気づいた点（参考）

1. `krd_data_get` が各ファイルに複製されている（①②③④⑤⑥ と各コピー）。接続先 `\esrv11\KakouDenpyo\krd_machine.db` も各所に直書きで、移行時の変更箇所が多い。
2. `DATA_ASP2_PUT` は SQLite が MySQL より欠落・重複している（`15_krd_machine/KRD同期不具合_DATA_ASP2_PUT.md`）。
   - ①は VERSION を取れないと 1 にするため、欠落してもエラーにならず、工程が VERSION=1 で引かれる可能性がある。
3. `SELECT * FROM DATA_KOUTEIZUKAN` は全列取得だが、実際に使う列は9列（SETU_F ＋ 各図番8種）。
