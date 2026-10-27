# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

現品票発行システム。加工伝票から現品票（QRコード付きの Excel）を作り、i-Reporter のチェックシートと連携する。
`genpin_check`（本番は `D:\py\genpin_check`）の後継として 2026-10 に作り直した（Streamlit のまま、中身を整理）。

## 起動・実行

| もの | コマンド | 備考 |
|---|---|---|
| 画面（Streamlit） | `Genpin_Start.bat`（`streamlit run 1_現品票発行.py --server.port 8502`） | ページ: 1 現品票発行 / 2 手入力発行 / 3 チェックシート再作成 / 4 i-Reporter チェック登録（check_input へのリンクだけ） / 90 操作マニュアル / 95 管理画面 |
| チェック項目入力（NiceGUI） | `Check_input_start.bat`（port 8506・専用 venv） | 詳細は `check_input/CLAUDE.md` |
| 夜間処理 | `python create_report.py`（データ更新＋i-Reporter 帳票作成）／ `python dbupdate.py`（データ更新だけ） | タスクスケジューラから。**ファイル名を変えない** |
| テスト | `python -m unittest discover tests` | 外にはつながない（全部モック） |
| DB の移行（1回だけ） | `python tools/migrate_genpinhyo_db.py [--dry-run]` | output_history → zip＋print_history、VACUUM、WAL |
| checksheet.db の掃除（1回だけ） | `python tools/clean_checksheet_db.py [--dry-run]` | 工程順が数字でない壊れた行を消す |

## 構成

画面のファイル（`1_現品票発行.py`・`pages/*.py`）は表示とボタンだけ。処理は `genpin/` にある。

| モジュール | 役割 |
|---|---|
| `genpin/config.py` | ファイルの場所・接続先（URL・パスワード）をすべてここに置く |
| `genpin/db.py` | genpinhyo.db の接続（WAL・timeout 30秒）・テーブル定義・バックアップ・印刷の記録・エラーの記録 |
| `genpin/update.py` | **データ更新。画面と夜間処理で共通の、ただ1つの処理** |
| `genpin/listing.py` | 画面の一覧を組み立てる（部品の設定・削除フラグ・帳票発行ID） |
| `genpin/tag_layout.py` | 現品票1枚分のレイアウト（罫線・結合・見出し・行の高さ・印刷設定）。**ひな形の Excel は使わない**。見た目を変えるときはここ |
| `genpin/tag_excel.py` | 現品票の Excel（レイアウトを必要な枚数だけ並べ、値と QR を入れる。値のセル位置は `TAG_CELLS`） |
| `genpin/conmas.py` | i-Reporter 帳票の自動作成（ConMas Manager を Selenium で操作） |
| `genpin/portal_api.py` | 業務ポータル（Django）の読み取りAPI。**標準ライブラリだけ**（check_input も使う） |
| `genpin/irepo.py` | i-Reporter の PostgreSQL（客先マスタ・帳票発行ID・帳票定義） |
| `genpin/rbom.py` | rBOM の FastAPI `/query`（CHANGE GEAR BOX の引当） |
| `genpin/ui.py` | Streamlit の共通の見た目 |

⚠ `genpin/__init__.py` では何も import しない（check_input の venv には pandas が無い）。

## データの流れ（データ更新）

```
業務ポータル A4 /machining-schedule/api/genpinhyo/denpyo/
  （加工伝票の伝票単位・払出先で絞る前 ＋ VER・工程・メッキ）
    ↓ 対象外を外す: 組立番号 A＋数字8桁 / CHANGE GEAR BOX の数字製番 / 払出先（下記）
    ↓ ＋ CHANGE GEAR BOX（rBOM D3520 の引当 → CH＋8桁。VER は A1 lots で引く）
    ↓ ＋ 客先名・国名（i-Reporter 客先マスタ）＋ 図番（業務ポータル drawings）
genpinhyo（REPLACE）・buhin_irepo_mst（新しい部品名を QRコードレイアウト区分=2 で）
    ↓ 削除フラグ: 当月〜3か月先で、加工伝票に無いロット＝1（変化は flag_change_log）
    ↓ excluded_lots: 払出先で全行が除外になったロット（毎回作り直す）
```
- 払出先の除外（時限処理）: 特定5部品（SINKER REST RING / NEEDLE DIAL / NEEDLE CYLINDER / SINKER DIAL / WRAP DIAL）は 40 を捨てて 60 を残す。それ以外は 49・60 を捨てる。PT は捨てない
- 外から取るもの（API・i-Reporter）は DB を開く前にそろえ、書き込みは1トランザクション。**失敗したら何も書かない**
- ⚠ 書く前に `PRAGMA quick_check` で点検し、壊れていれば止める（`db.check_integrity`）。ロット番号の索引が壊れていると
  REPLACE が既存の行を見つけられず、同じロットの行が更新のたびに増える（2026-10-26 に本番の写しで発生）。
  直すのは `tools/migrate_genpinhyo_db.py`（`db.rebuild_genpinhyo`。⚠ 壊れたテーブルを rowid で引くと行が消えるので、全件を読んで Python で整理する）
- 動くのは、タスクスケジューラの `dbupdate.py`（**15分ごと**）・`create_report.py` と、画面の「データ更新」ボタン。
  ボタンのときは、表示中の月の未作成の i-Reporter 帳票も作る
- ⚠ 画面を開いたときにはデータ更新をしない（2026-10-26 決定。開くのが約5秒遅くなるため）。
  一覧は DB ファイルの更新日時が変わると読み直す（`load_tag_list` の `db_stamp`）ので、夜間処理の結果もそのまま出る
- ⚠ 加工伝票の「加工部番」は**変換済み**（`478-409TA33`）。A1 `lots/` は変換前の品目CDを受け取る約束なので、加工伝票の部番を送ると二重に変換されて引けない。加工伝票は A4 を使う

## DB（`Database/`）

**genpinhyo.db**
| テーブル | 中身 |
|---|---|
| genpinhyo | 現品票の本体（1ロット1行・全列 TEXT）。⚠ i-Reporter `header_koushin.py` が**列名で**読む（`ﾒｯｷ='1.0'` で判定）。列名を変えない |
| buhin_irepo_mst | 部品名ごとの設定（ireporter管理flg / QRコードレイアウト区分 0=i-Reporter・1=旧形式・2=新部品 / 縦横区分 1=縦405・0=横406）。check_input のタブ4で人が直す |
| delete_mst / flag_change_log | 削除フラグとその変化の記録 |
| excluded_lots | 払出先で全行が除外になったロット（ロット番号だけ） |
| cgb_seino_ch_mapping | CHANGE GEAR BOX の製番 → CH番号 |
| print_history | 印刷の記録（1ロット1行。種類・帳票発行ID） |
| error_log | エラー（書けないときは `err.txt` に追記） |

- 表記: 必要数・工程VERSION は整数の文字（`1`）、ﾒｯｷは `'1.0'` か空。⚠ 2026-10 より前の行には `1.0` 表記が混ざっている（読む側で吸収している）
- バックアップ: データ更新のたびに `Database/backup/YYYYMMDD_genpinhyo.db`（SQLite のバックアップ機能・7日分）

**checksheet.db**（工程図とチェック項目。⚠ i-Reporter `75_genpin展開`・Django `machining_schedule`・esrv10 の写しが読む。形を変えない）
- kouteizuban（完成部番×工程Ver×工程順）と zubancheck（チェック項目15組。連携ID＝kouteizuban.ID）
- check_input が起動時に業務ポータルの品目工程マスタ（A3）と同期する。⚠ マスタから消えた工程は、そのチェック項目ごと消える（消した行は `Database/backup/*_mastersync_deleted_*.csv`）。2割を超えて消えるときは中止

## 外部との接続（`genpin/config.py`）

| 相手 | 用途 |
|---|---|
| 業務ポータル `http://pfw-gyomu`（キーレス） | A4 denpyo・A1 lots・A2 process-strings・A3 process-master・drawings。仕様は Django `apps/machining_schedule/Document/仕様書.md`「現品票システム向けAPI」 |
| rBOM FastAPI `http://pfw-api/query` | D3520・D3010（CHANGE GEAR BOX） |
| i-Reporter PostgreSQL `ESRV10/irepodb` | view_mst_custom_record（客先）・view_report_405/406（帳票発行ID）・view_def_top |
| ConMas Manager `172.17.52.101` | 帳票の自動作成（Selenium・Chrome） |

## 注意

- ⚠ **本番の場所はまだ `D:\py\genpin_check`**。i-Reporter スクリプト（`90_tools/75_genpin展開`）と Django の checksheet.db の読み先がそこを向いている。切り替えるときは両方を直す
- ⚠ 時限処理（CHANGE GEAR BOX・払出先の除外）は `genpin/update.py` の該当ブロックだけ。終わらせるときはそこを直す
- ⚠ 現品票は1枚20行（図番9行＝B・B・F・F・L・R・C・手書図番・予備項目）。**A4 1枚に3枚**（昔のひな形と同じ）で、3枚ごとに改ページ（`tag_layout.TAGS_PER_PAGE`）。
  **点線で切ると A4 が3等分になり、枠がそれぞれの真ん中に来る**ようにしてある（すき間を点線で2等分・ページの最後の1枚はすき間を隠す・上下左右の中央寄せ・余白の最小値は上下0）。
  最後のページの足りない枚数ぶんは空の行で埋めて印刷範囲に入れる（1〜2枚のページも同じ位置に出すため）。
  ⚠ 行の高さ（`tag_layout.ROW_HEIGHTS`）を増やすと Excel が途中で勝手に改ページし、以降が全部ずれる。余裕は2〜3%しかない（詳しくは tag_layout.py のコメント）
  2枚目以降は1枚目の書式を写して作る（1枚ずつ書式を設定すると openpyxl が遅い）。結合も openpyxl の merge_cells を使わない（`tag_layout._merge`。結合が増えると急に遅くなる）
- ⚠ 半角カナの列名 `ﾒｯｷ` は Python のキーワード引数に書けない（全角に読み替えられる）。辞書のキーとして扱う
