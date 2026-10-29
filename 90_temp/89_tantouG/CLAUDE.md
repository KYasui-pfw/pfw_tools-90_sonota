# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要
担当G向けの単一HTMLアプリ `発注一覧変換_担当G.html`。
集約注文書発行の発注一覧 Excel をアップロードすると、**rBOM から引き直して**「注文書1枚＝1行」の発注一覧を作り、
**仕入先ごとに1ファイル**の Excel にしてダウンロードさせる（仕入先ごとのボタン＋全部まとめた ZIP ボタン）。
骨組みは `../88_担当I発注一覧/発注一覧変換_担当I.html`（担当I）の複製で、列・集約備考・並び順が違う。
入力は `../86_横田さんExcel変換ツール`（担当2）と同じ Excel。

作成ルールは `C:\Dev\80_Documents\90_ビルドレスSPAテンプレート\template.md`（ビルドレスSPAテンプレート）に従う：
Alpine.js＋Pico CSS（`:root` で 85%／余白0.5rem／角丸0／Noto Sans JP）＋Pyodide v0.25.0、すべてCDN、単一HTML。

## 実行・動作確認
- 利用者はHTMLをブラウザで直接開くだけ。サーバー・venv不要。ただし次の2つが必要:
  - **インターネット**（Pyodide を CDN、openpyxl を PyPI（`micropip.install`）から取る）。読み込み中は黄色い枠の大きな表示を出す
  - **社内LAN**（`http://pfw-api/query` を呼ぶ。rBOM の API は CORS で全オリジンを許可しているので `file://` でも呼べる）
- **変換ロジックはブラウザ無しで試せる**。HTMLから Python 部分を抜き出し、`api_post` だけ `requests` に差し替えて
  共通venv（openpyxl・requests 入り）で動かす（本物の rBOM を**読むだけ**）:
  ```python
  import re, asyncio, requests
  src = re.search(r'<script id="py-convert" type="text/plain">(.*?)</script>',
                  open('発注一覧変換_担当G.html', encoding='utf-8').read(), re.S).group(1)
  ns = {}; exec(src, ns)
  async def api_post(payload):
      r = requests.post(ns['API_URL'], headers={'X-API-KEY': ns['API_KEY']}, json=payload, timeout=120)
      r.raise_for_status(); return r.json()['rows']
  ns['api_post'] = api_post
  res = asyncio.run(ns['convert'](open('発注一覧_〇〇.xlsx', 'rb').read(), print))
  # res = {"log": [...], "files": [{"name", "label", "count", "data"}], "zip": {"name", "data"}}
  ```
  実行は `"C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe" -X utf8 ...`。
  サンプル Excel はこのフォルダに無い。`../88_担当I発注一覧/発注一覧_20261022_142342.xlsx`（11,503行・212社。約34秒）
  と `../88_担当I発注一覧/発行一覧.xlsx`（15明細・集約3件）を使う
- ⚠ **ブラウザ（Pyodide）上での動作は Claude からは未確認**（2026-10-27 時点。開発機ではヘッドレスブラウザが起動しない。担当I と同じ）。
  JS 部分は担当I と同じ（ZIP ボタンの表示条件だけ違う）

## 構成
HTML内で JS と Python が分かれている（担当I と同じ）：
- **Python（`<script id="py-convert" type="text/plain">`）**: 変換ロジックの本体
  - `convert(data, progress)` … **async**
    1. `read_source` … Excel を読み、発注番号＋行番号ごとに1件にする（受入ごとに行が分かれるので最初の1行だけ）
    2. `fetch_rbom` … rBOM から D3340・D3330・D3010・M0540・M0710 を IN で引く（1000件ずつ・1万件でページ送り）
    3. `build_lines` → 集約は `aggregate_row`、集約でない発注は `single_row` で1行にする → `sort_key` で並べる
    4. 仕入先ごとに `build_book` → 全部を ZIP にも入れる
  - `api_post` … rBOM への1回の問い合わせ（ブラウザでは `pyodide.http.pyfetch`）。**テストではこれだけ差し替える**
- **JS（Alpine.js `app()`）**: Pyodide初期化、ファイル選択／ドラッグ＆ドロップ、`convert` 呼び出し、Blob でダウンロード
  - ⚠ **`x-init="init()"` を付けない**（Alpine が `init()` を自動で呼ぶので二重初期化になる）
  - **仕入先が1社のときは「すべてZIPでダウンロード」ボタンを出さない**（`x-show="files.length > 1"`。利用者の指示）

⚠ **Excel の列は必ず1行目の項目名で引く**（列は途中に挿入されることがある）。列番号を直書きしないこと。

## 入力 Excel
`発注一覧_〇〇.xlsx`（集約注文書発行の発注一覧出力。先頭シート `集約発注マッピング`）。86 と同じもの。
担当I と同じく `発行一覧_〇〇.xlsx`（シート `発行一覧_rBOM発注番号`）も読める（集約個数・集約金額を使う）。
- 読む列: **集約発注番号・集約納期・発注番号・行番号・仕入先CD**（`REQUIRED_COLUMNS`）＋ 発注数計／集約個数・集約金額（あれば）。
  ほかの値はすべて rBOM から取り直す

## 出力仕様（2026-10-27 利用者指示）
⚠ **このレイアウトは仕入先CD 1592 向けに決めたもの**。ほかの仕入先はまだ決まっていないので、**当面は全仕入先をこのレイアウトで出す**。
仕入先ごとに変えるときは担当I の `columns_for`（`COLUMNS_ONLY_FOR` / `COLUMNS_EXCEPT_FOR`）のように仕入先CDで列を切り替える。

**1行の単位**: 集約発注番号がある明細は**集約1件＝1行**、無い明細は発注番号＋行番号ごとに1行。
集約で rBOM の値を使う項目は全明細で同じはず。違えば**重複を除いて ` / ` でつなぐ**（空は飛ばす）。

列（左から。`OUTPUT_COLUMNS`）:
| 列 | 集約の行 | 集約でない行 |
|---|---|---|
| 注文書発行区分 | `発行済`（固定） | D3330.PRNKBN を文字に（1→未発行／2→発行済） |
| 発注番号 | 集約発注番号 | D3340.PONO（行番号は付けない） |
| 品目ｺｰﾄﾞ | D3340.HMCD | 同左 |
| 発注数 | Excel の発注数計／集約個数（無ければ THQTY の合計） | D3340.THQTY |
| 希望納期 | Excel の集約納期 | 集約納期があればそれ、無ければ D3340.DRVDT |
| 単価 | D3340.PRICE | 同左 |
| 工程ｺｰﾄﾞ | D3340.KTCD | 同左 |
| 備考 | D3340.NOTE を / でつなぐ | D3340.NOTE |
| 金額 | Excel の集約金額。無ければ 単価×発注数 | D3340.AMOUNT |
| 品名 | D3340.HMNM | 同左 |
| 回答納期 | **空欄**（集約は回答納期を持てない） | D3340.RECDT |
| 注文書発行日 | D3330.PRNDT を / でつなぐ | D3330.PRNDT |
| 担当者略称 | M0540.TANRNM（D3330.TANCD で引く） | 同左 |
| 集約備考 | 集約注文書PDFの備考欄と同じ内訳（下記） | 空欄 |

- **注文書発行日**: 集約注文書を発行すると明細の rBOM 発注も同じ日に発行済になるので、集約日＝注文書発行日で**原則1つ**
  （サンプルの集約340件はすべて1つ）。ずれていれば / でつないで出る。
  集約注文書側には発行日の列が無く（`updated_at` で代用）、ブラウザから Django の API は呼べない（CORS 未対応）ので rBOM の値を使う
- **集約備考**: 明細ごとに `発注番号+行番号 / 製番 / 月次 / 数量` を作り、`, ` でつなぐ。
  例 `002129892+001 / 27DKA057 / 1月7次 / 1, 002129894+001 / 27DKA054 / 1月7次 / 1`
  - **明細2件ごとにセル内で改行する**（`breakdown_text`・`BREAKDOWN_PER_LINE`。行末の `,` は残す。利用者の指示 2026-10-29）
  - 元の実装は `C:\Dev\03_PFW_Django\apps\purchase_order\views.py` の `_build_pdf_context`（breakdown）と `_format_getsuji`
  - 数量は **D3340.QTY**（THQTY ではない。PDF と同じ）。月次は製番で **D3010.GETSUJI** を引いて「1月7次」の形（月はゼロ埋めしない）。
    Excel の月次列は使わない。空の項目は飛ばしてつなぐ。明細は発注番号→行番号の順
  - PDF は13件で打ち切る（ほか n 件）が、Excel では**全件出す**
- **並び順**: **注文書発行日 → 発注番号 → 行番号** の昇順（`sort_key`）。集約の行は明細のうち最も古い注文書発行日で比べる。
  rBOM に無い明細の行はいちばん最後
- 受入済・中止も外さない。rBOM に無い明細（削除済みなど）は Excel の値だけで行を残し、画面に ⚠ で番号を出す
- 日付はすべて `YYYY/MM/DD` の**文字列**。数値の列（発注数・単価・金額）以外はセルの書式も文字列（`@`）

### ファイル
- 仕入先CD ごとに1ファイル `発注一覧_担当G_<仕入先CD>_<仕入先略称>.xlsx`（M0710.HTRRNM）。シート名は仕入先CD。
  全部を入れた `発注一覧_担当G_<日時>.zip` も作る（仕入先が1社のときは画面にボタンを出さない）
- 印刷は担当I と同じ: A4 横・余白小（上だけ 0.5インチ）・横は1ページ・見出し行を全ページに・ページ中央（水平）。
  罫線は見出し行と外枠が細線、表の中は hair（`draw_borders`）。見出し行は固定（`A2`）
- **列幅**: 集約備考以外は見出しと中身のいちばん長いものに合わせる（`fit_widths`。全角2・半角1で数える）。
  **集約備考は固定幅 85.4（約750px）**（`FIXED_WIDTHS`。利用者の指示 2026-10-29）。利用者の Excel で幅81＝711px だった比で換算した値。
  セル内改行＋折り返し表示（`wrap_text`）で、**行の高さは指定せず Excel が開いたときに合わせる**
