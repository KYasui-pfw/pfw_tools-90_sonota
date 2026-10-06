# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

設計の図面管理システム **Obbligato（PDM）** のダンプを esrv11 の Docker Oracle に毎日取り込み、
**参照用の複製を最新に保つ**ツール。稼働見込みは約2年（2026-09-09 構築）。

このフォルダが**マスター**で、esrv11 へは `deploy.py` で一方向同期する。

```
C:\Dev\90_tools\88_obl_oracle\   （Git管理・ここを編集する）
        │  deploy.py
        ▼
esrv11:/home/docker-user/docker-apps/12_obl_oracle/   （実体）
```

⚠ **esrv11 側で直接編集しないこと。**次の `deploy.py` で上書きされて消える。

## 接続情報

| 項目 | 値 |
|---|---|
| ホスト / ポート | `esrv11`（172.17.85.101） / `1521` |
| **サービス名** | **`FREEPDB1`** ← SID ではない。A5:SQL Mk-2 では「サービス名」側に入れる |
| ユーザー | `OBL` / `obl` |
| 管理者 | `SYSTEM`（パスワードは esrv11 の `.env`） |
| DB | Oracle AI Database 26ai Free 23.26.3.0.0 / AL32UTF8 |

```python
import oracledb   # thin モードなので Instant Client 不要
conn = oracledb.connect(user="obl", password="obl", dsn="esrv11:1521/FREEPDB1")
```

⚠ **毎日 12:40 から約9分は接続できない**（後述のリフレッシュ中）。
**業務時間内に止まる**ので、この時間帯に参照すると「テーブルが無い」エラーになる
（`DROP USER` 済みで `impdp` の途中のため）。
⚠ **リフレッシュ開始時に OBL で接続中のセッションは強制切断される。**
接続が残っていると `DROP USER` が ORA-01940 で失敗するため（2026-09-29 に発生）、
`refresh.sh` の 4) で OBL をロック → 残ったセッションを `KILL SESSION` → DROP（最大60秒やり直し）
の順にしている。消せなかったときはロックを戻して異常終了する（DB は無傷）。

## コマンド

```bash
# デプロイ（このフォルダで実行）
$PYTHON deploy.py --dry-run     # 差分だけ確認
$PYTHON deploy.py               # 転送。CRLF→LF 変換と実行権限付与も行う
# $PYTHON = C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe

# esrv11 側
ssh docker-user@esrv11
cd /home/docker-user/docker-apps/12_obl_oracle
./refresh.sh                    # 更新があれば取り込む（cron と同じ）
./refresh.sh --force            # 同じダンプでも強制的に取り込み直す
tail -f logs/refresh_*.log      # 実行中の進捗
cat .last_dmp_sig               # 取り込み済みダンプの識別子
ls -lt /mnt/fsrv24/obl_dmp/     # fsrv24 に来ているダンプ
```

`deploy.py` の転送対象は `SYNC_FILES` に列挙した3ファイルのみ（`docker-compose.yml` / `refresh.sh` / `setup/01_init.sql`）。
ファイルを増やしたらここに追記する。`.env` `oradata/` `dmp/` `logs/` は**意図的に対象外**。

## 日次処理（cron: 毎日 12:40）

```
fsrv24 //172.17.22.102/Obbligato_Backup  →  /mnt/fsrv24/obl_dmp（ro でマウント）
  PDM_DB_<日時>.tar.gz の最新を名前順で選ぶ
    ↓ tar -tzf で中身と CRC を検証        ← コピー途中ならここで中止（DBは無傷）
    ↓ dmp/PDM_DB.DMP へ展開（約10秒・3GB）
    ↓ OBL ユーザーと obl_data テーブルスペースをデータファイルごと破棄
    ↓ impdp REMAP_SCHEMA=MINI_TM_SERVER:OBL（約5分）
    ↓ DBMS_STATS.GATHER_SCHEMA_STATS
    ↓ 件数検証（0件なら異常終了）
    ↓ 図面一覧を出力（output/obbligate_copy/obbligate_all_zumen.csv・約4秒）
    ↓ 前回との差分を diff/obbligate_zumen_diff_<日付>.csv に出力（30日保持）
    ↓ 品目の単価・在庫情報を出力（output/obbligate_copy/obbligate_part_price.csv）
  logs/refresh_<日時>.log に記録（60日で自動削除）
```

- `.last_dmp_sig`（ファイル名＋mtime＋サイズ）と同じなら**何もせず数秒で終了**する
- 失敗しても**通知はしない**（ログのみ）。データが古いままになるだけで業務は止まらない
- 成功すると展開済み `.DMP` は `dmp/archive/` へ移動（切り戻し用に1世代のみ）

## ファイルサーバー突合用の図面一覧（obbligate_all_zumen.csv）

取り込みの最後（`refresh.sh` の 9)）に、図面の一覧を
**`\\esrv11\output\obbligate_copy\obbligate_all_zumen.csv`** へ出力する。
約 242,000 行・24MB・所要4秒。毎回まるごと作り直して差し替える。

| 列 | 内容 |
|---|---|
| PART_NUMBER / PART_NAME | 品番・品名（`part.part_number` / `part.name`） |
| PART_VERSION_NAME | 版の品名（`part_version.name`。Approved の最新版）。PART_NAME とは別に並べて出す |
| DOCUMENT_NUMBER | 図番 |
| DOCUMENT_NAME | 図面名（`document.name`） |
| VER / REV | 版数・改訂 |
| LIFECYCLE | `document_version.lifecycle_state_name` |
| FILE_BASE | **図番 + REVISION 2桁**（`VERSION` ではない。拡張子なし） |
| FILE_MODIFIED_ON | `document_entry.file_modify_date`（UNIX秒）を `YYYY-MM-DD` に |

- **抽出条件は `90_temp/99_tmp/08_obli/09_export_copy_target.py` と同じ**
  （CADネイティブが `mi` / `tif`。ライフサイクルでは絞らず InWork も含める）。
  条件を変えるときは両方を見比べること
- ⚠ **列を絞っても行は重複しない**ため `DISTINCT` は付けていない（実測で 242,220 = 242,220）。
  FILE_BASE 自体は 81,292 種類で、同じ図面が複数の品番から参照されるぶん行が増える
- **UTF-8 BOM 付き・CRLF**（Excel でそのまま開ける。Python は `encoding="utf-8-sig"`）
- ⚠ **`sq()` の `NLS_LANG=Japanese_Japan.AL32UTF8` を外さないこと。**
  クライアント側が US7ASCII 扱いになり、PART_NAME の日本語が `?` に化ける
- ⚠ **ヘッダー行はシェル側で書いている。** sqlplus の `SET MARKUP CSV` は `PAGESIZE` ごとに
  列名を繰り返すため、`PAGESIZE 0`（ヘッダー無し）にして先頭1行だけ自前で付けている
- 出力先は `.env` の `ZUMEN_OUT_DIR` で変更できる（既定 `/home/docker-user/output/obbligate_copy`）
- **更新が無くてスキップした日は CSV も作り直さない**（前日のものがそのまま残る）
- ここで失敗しても取り込み自体は完了している（`.last_dmp_sig` は 8) で更新済み）。
  翌日まるごとやり直しにはならず、`./refresh.sh --force` で作り直せる

### 前回との差分（diff/obbligate_zumen_diff_<日付>.csv）

同じ `refresh.sh` の 10) で、上の一覧を**前回分とまるごと比較**した差分を
**`\\esrv11\output\obbligate_copy\diff\obbligate_zumen_diff_YYYYMMDD.csv`** へ出す。

- 一覧の9列を**1行として**比べ、先頭に `DIFF_TYPE` 列（`追加` / `削除`）を足した10列で出力する。
  キーを置かないので、**REV や更新日が変わった図面は「削除」＋「追加」の2行**で現れる
- **差分が無い日もヘッダー行だけの CSV を必ず作る**（0行＝比較はした、の意）
- 比較用の前回分は **`.obbligate_all_zumen.prev.csv`**（ヘッダー・BOM 無しの生データ）として
  同じフォルダに**1世代だけ**持つ。差分 CSV は **30日で自動削除**（`-mtime +30`）
- ⚠ **前回分の列構成は `.obbligate_all_zumen.prev.csv.header` に控える。**列を増減した直後は
  全行が「削除＋追加」になって巨大な差分になるため、構成が違う（または控えが無い）ときは差分0行にする。
  ヘッダーは `refresh.sh` の `ZUMEN_HEADER` 1か所で定義し、一覧・差分・控えのすべてがこれを使う
- ⚠ **24MBのフル一覧を日ごとに残さない。** 30日分で700MBを超えるため、1か月残すのは差分だけ
  （esrv11 はホストの容量が枯渇した事故があるので増やさないこと）
- ⚠ **初回（`.prev.csv` が無い）は差分0行**。全件を「追加」として出すと 24MB になるため出さない。
  比較は次回から始まる
- ⚠ **並べ替えは `LC_ALL=C`。** `comm` は「同じ並び順で整列済み」が前提なので、
  ロケールで並びが変わると差分が壊れる
- 更新が無くてスキップした日は差分も作られない（＝その日付のファイルができない）

## 品目の単価・在庫情報（obbligate_part_price.csv）

`refresh.sh` の 11) で **`\\esrv11\output\obbligate_copy\obbligate_part_price.csv`** へ全品番を出力する
（約40万行・28MB・毎回まるごと作り直し）。Obbligato へ取り込まれている単価CSV（`E<日時>.csv`）と同じ形式。

| 列 | 内容 |
|---|---|
| 品目番号 | `part.part_number` |
| 品目名 | `part_version.name` |
| 在庫数 / 単価 / 発注担当者 / 保管区 / 仕入先 | `fks_part.fks_prt_stock_count` / `fks_prt_unit_price` / `fks_prt_order_person` / `fks_prt_storage_place` / `fks_prt_supplier` |

- `fks_part` は **`part_version` と1:1**（`fks_part.super_identification = part_version.identification`）。
  1品番1行にするため **VERSION 最大の版**を採る
- **書式は取込元CSVに合わせる**: UTF-8 **BOM 無し**・CRLF・全項目を `""` で囲み、**行末に余分なカンマ**。
  単価は整数なら小数点なし（`504`）、小数はそのまま（`6142.5`）。そのため `SET MARKUP CSV` を使わず1行を SQL で組み立てている
- ⚠ **品目名は取込元CSVと一致しない行がある**（2026-07-03 分で 2,280件中44件）。取込元の品目名は
  Obbligato に書き込まれない（登録元の名称）ため。突合は**品目番号＋5項目**で行う（5項目は全件一致を確認済み）
- ⚠ **DB に Shift-JIS のバイトのまま入った品番がある**（`4119-67T0130017402ﾚｰｽS`）。そのまま出すと
  ファイル全体が UTF-8 で開けなくなるため、**UTF-8 として読めない項目は ASCII 以外のバイトをすべて `?` にする**
  （→ `4119-67T0130017402???S`）。項目単位なのは、バイト単位だと一部がたまたま UTF-8 として読めて
  別の文字（`ڰ`）に化けるため

## 触るときの注意

- ⚠ **`impdp` の `rc=5` は正常。** `ORA-31684: Object type USER:"OBL" already exists` が1件出るため必ず5になる。
  先に OBL を作ってから入れる構造なので消えない。`rc` が 0 と 5 以外のときだけ異常
- ⚠ **展開（＝CRC検証）が成功してから DROP する順序を崩さないこと。**
  逆にすると、壊れたダンプを掴んだときに「DROP 済みでインポートできず空DB」になる
- ⚠ **`impdp` はパイプ（FIFO）から読めない**ので「解凍しながらリストア」は不可。必ず実ファイルに展開する
- ⚠ **`DROP USER ... CASCADE` だけではデータファイルが縮まない。**テーブルスペースごと
  `INCLUDING CONTENTS AND DATAFILES` で破棄している。新旧2世代を同時に持つ構成（4.82×2＝9.6GB）は
  Free版の12GB上限に対して際どいので採らない
- ⚠ **`PURGE DBA_RECYCLEBIN` は 26ai では `SYSTEM` に権限が無い**（ORA-01031）。
  失敗しても止めない形にしてある。テーブルスペースごと破棄する方式ではごみ箱を経由しないため保険にすぎない
- ⚠ **イメージはダイジェストで固定**している。このリポジトリは `latest` タグしか公開しておらず、
  バージョンタグが存在しないため。意図してバージョンを上げるときだけ `docker-compose.yml` の1行を差し替える
- ⚠ **`restart: unless-stopped` を外さないこと。** esrv11 は root の crontab
  （`0 1 * * * /sbin/reboot`）で毎日 1:00 に再起動する。`no` にすると毎朝1時以降DBが落ちたままになる。
  例外は **`oradata/` が空の状態から作り直すとき**で、そのときだけ一時的に `no` にする
  （`unless-stopped` のままだと、ホストが不安定なとき再起動ごとにDB作成をやり直して負荷をかけ続ける）
- ⚠ **書き込み帯域を 50MB/s に絞っている**（`blkio_config.device_write_bps`）。
  LVM を挟むので `/dev/dm-0` と `/dev/sda` の**両方**に指定が必要。2026-09-09 の事故対策。外さないこと
- ⚠ **整合性チェック（ファイルサーバーとの突合）はこの処理に含めない。**取り込みのみに専念させる方針
  （2026-09-09 決定）。突合が必要なときは、最新化された DB に対して
  `90_tools/90_temp/99_tmp/08_obli/09_export_copy_target.py` を流す

## esrv11 側の構成

```
/home/docker-user/docker-apps/12_obl_oracle/
├── docker-compose.yml / refresh.sh / setup/   ← deploy.py で同期
├── .env            パスワードと DMP_DIR / DMP_PATTERN。★同期対象外・Git対象外
├── .last_dmp_sig   前回取り込んだダンプの識別子
├── oradata/        DB本体（実測 約11GB。うち FREEPDB1 7.1GB＝obl_data01.dbf 5.6GB。コンテナの /opt/oracle/oradata）
├── dmp/            展開先（約3GB）＋ impdp ログ。取込後に archive/ へ移すので平常時は 2.8GB、取込中だけ倍になる
└── logs/           refresh_<日時>.log

/home/docker-user/output/obbligate_copy/     ← 図面一覧CSVの出力先（docker-apps の外）
├── obbligate_all_zumen.csv         約24MB / 242,220行。\\esrv11\output\obbligate_copy\ で参照
├── .obbligate_all_zumen.prev.csv   差分比較用の前回分（ヘッダー・BOM無し）。1世代のみ
└── diff/                           前回との差分 obbligate_zumen_diff_<日付>.csv。30日で自動削除
```

- `dmp/` はコンテナの `/opt/oracle/dmp` にマウントされ、Oracle の `DMPDIR` がそこを指す。
  **ホスト側に展開したファイルをそのまま impdp が読む**（コンテナへの送り込みは不要）
- `dmp/` は `docker-user:54321` の setgid 2775。docker-user が展開し、Oracle(54321) が impdp ログを書くため
- `oradata/` は `54321:54321`。**docker-user では `du` で降りられず 56K に見える**。実サイズは `sudo du -sh`
- SMB: `\\esrv11\obl_oracle`（`docker-user` 認証で書き込み可）。
  **`veto files = /oradata/dmp/`** で DB本体とダンプは共有から見えない（誤操作とスキャン負荷の防止）
- fstab: `//172.17.22.102/Obbligato_Backup /mnt/fsrv24/obl_dmp cifs credentials=/etc/smbcredentials_fsrv24,iocharset=utf8,ro 0 0`

## トラブル時

| 症状 | 対処 |
|---|---|
| 途中で中断した／OBLが空 | `./refresh.sh --force` をもう一度流す。毎回まるごと作り直す方式なので中途半端な状態から復旧できる |
| `入力ディレクトリが見つからない` | CIFS マウント切れ。`sudo mount -a` で復旧 |
| `アーカイブ内に .DMP が無い` | fsrv24 へのコピーが未完了。次のサイクルを待つ（DBは無傷） |
| DBに繋がらない | `docker ps --filter name=obl-oracle`。落ちていれば `docker compose up -d` |
| 12GB上限に近づいた | OBL で接続して `SELECT ROUND(SUM(bytes)/1024/1024/1024,2) FROM user_segments;`（SYSTEM なら `FROM dba_segments WHERE owner='OBL'`。refresh.sh はこちら）。現在4.82GB |

## 詳細ドキュメント

設計判断の根拠・検証データ・2026-09-09 の障害記録は
`90_tools/90_temp/99_tmp/08_obli/11_esrv11_Oracle構築計画.md` にある。
Oracle 26ai で 11.2 のダンプが読める根拠、`.tar.gz` を選んだ理由、
ローカル21c との突合結果（全項目一致）などはそちらを参照。
