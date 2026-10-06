#!/bin/bash
# ============================================================
#  Obbligato 複製DB 日次リフレッシュ
#
#  fsrv24 に置かれた PDM_DB.tar.gz を取り込み、OBL スキーマを作り直す。
#
#  使い方:
#    ./refresh.sh            # 更新があれば取り込む（cron 用）
#    ./refresh.sh --force    # 更新が無くても強制的に取り込む
#
#  重要な設計:
#    - impdp はパイプから読めないため、必ず実ファイルに展開してから流す
#    - 展開（＝CRC検証）が成功してから DROP する。順序を守らないと
#      壊れた dmp を掴んだときに「空のDB」が残る
#    - DROP USER だけではデータファイルが縮まないため、テーブルスペースごと
#      データファイル込みで破棄して作り直す
# ============================================================
set -uo pipefail

cd "$(dirname "$0")" || exit 1
set -a; source .env; set +a

FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

# fsrv24 には PDM_DB_20260909_093540.tar.gz のように日時付きで積まれるので、
# 「その中でいちばん新しいもの」を選ぶ。ファイル名の日時が昇順に並ぶ形式なので名前順で足りる
# （CIFS のタイムスタンプに依存しないぶん、mtime 順より確実）。
DMP_DIR="${DMP_DIR:-/mnt/fsrv24/obl_dmp}"
DMP_PATTERN="${DMP_PATTERN:-PDM_DB_*.tar.gz}"
WORK="dmp/PDM_DB.DMP"
CONN="system/${ORACLE_PWD}@localhost:1521/FREEPDB1"
CONTAINER="${CONTAINER_NAME:-obl-oracle}"

mkdir -p logs dmp/archive
LOG="logs/refresh_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

echo "=== $(date '+%F %T') refresh 開始 (dir=$DMP_DIR pattern=$DMP_PATTERN force=$FORCE) ==="

fail() { echo "!! $1"; echo "=== $(date '+%F %T') 異常終了 ==="; exit 1; }

sq() {  # sqlplus をサイレント実行して標準出力を返す
    # ★NLS_LANG を明示する。既定のままだとクライアント側が US7ASCII 扱いになり、
    #   9) で出す CSV の品名（日本語）が「?」に化ける。
    docker exec -i -e NLS_LANG=Japanese_Japan.AL32UTF8 "$CONTAINER" sqlplus -S -L "$CONN"
}

# ------------------------------------------------------------
# 1) 最新の入力を選ぶ／更新有無を判定
# ------------------------------------------------------------
[ -d "$DMP_DIR" ] || fail "入力ディレクトリが見つからない（マウント切れ？）: $DMP_DIR"

SRC="$(ls -1 "$DMP_DIR"/$DMP_PATTERN 2>/dev/null | sort | tail -1)"
[ -n "$SRC" ] || fail "$DMP_DIR に $DMP_PATTERN が1つも無い"
echo "-- 対象: $SRC"

SIG="$(stat -c '%Y %s' "$SRC")" || fail "stat に失敗: $SRC"
SIG="$SRC | $SIG"   # ファイル名も含める（新しいファイルが来たら必ず別の値になる）

if [ "$FORCE" -eq 0 ] && [ "$SIG" = "$(cat .last_dmp_sig 2>/dev/null)" ]; then
    echo "-- 前回と同じ dmp のため何もしない（--force で強制実行）"
    echo "=== $(date '+%F %T') 正常終了（更新なし） ==="
    exit 0
fi

# ------------------------------------------------------------
# 2) 展開（ここで CRC 検証される。壊れていれば必ず落ちる）
# ------------------------------------------------------------
echo "-- 展開中..."
case "$SRC" in
    *.tar.gz|*.tgz)
        # アーカイブ内の .DMP の名前は固定とは限らないので、実際に見て決める。
        # この tar -t の時点で gzip の CRC も検証されるため、途中コピーはここで落ちる。
        MEMBER="$(tar -tzf "$SRC" 2>/dev/null | grep -iE '\.dmp$' | head -1)"
        [ -n "$MEMBER" ] || fail "アーカイブ内に .DMP が無い（未完成またはコピー途中の可能性）"
        echo "-- アーカイブ内: $MEMBER"
        tar -xzOf "$SRC" "$MEMBER" > "$WORK" \
            || { rm -f "$WORK"; fail "アーカイブが未完成または破損している"; }
        ;;
    *.gz)
        gzip -dc "$SRC" > "$WORK" \
            || { rm -f "$WORK"; fail "gz が未完成または破損している"; }
        ;;
    *.DMP|*.dmp)
        cp -f "$SRC" "$WORK" || fail "コピーに失敗"
        ;;
    *)
        fail "対応していない拡張子: $SRC"
        ;;
esac

# Data Pump のダンプであることを確認（誤ったファイルで DROP しないため）
head -c 16384 "$WORK" | grep -q 'SYS_EXPORT_SCHEMA_01' \
    || fail "Data Pump のダンプではない、または内容が不正"
echo "-- 展開完了: $(stat -c '%s' "$WORK") バイト"

# ------------------------------------------------------------
# 3) 現在の件数を控える
# ------------------------------------------------------------
BEFORE=$(sq <<'SQL' | tr -d ' \r'
SET HEAD OFF FEED OFF PAGES 0
SELECT COUNT(*) FROM obl.assembly_component;
EXIT
SQL
)
case "$BEFORE" in ''|*[!0-9]*) BEFORE="(なし)" ;; esac
echo "-- 取込前の ASSEMBLY_COMPONENT: $BEFORE"

# ------------------------------------------------------------
# 4) 破棄 → 作り直し（データファイルごと消してディスクを解放）
#    ⚠ OBL で接続中の人が1人でもいると DROP USER が ORA-01940 で失敗する
#      （2026-09-29 に発生）。業務時間内に走るので、先にアカウントをロックして
#      新しい接続を止め、残っているセッションを切断してから DROP する。
#      切断直後はセッションが KILLED のまま残ることがあるので、最大60秒やり直す。
#      それでも消せなければロックを戻してから異常終了する（DB は無傷のまま）。
#    ★ヒアドキュメントは変数展開ありなので v\$session の $ はエスケープする
# ------------------------------------------------------------
echo "-- 旧スキーマを破棄して作り直し..."
sq <<SQL
WHENEVER SQLERROR EXIT 1
SET SERVEROUTPUT ON
BEGIN
  BEGIN EXECUTE IMMEDIATE 'ALTER USER OBL ACCOUNT LOCK';
  EXCEPTION WHEN OTHERS THEN IF SQLCODE != -1918 THEN RAISE; END IF; END;
  FOR i IN 1 .. 30 LOOP
    FOR s IN (SELECT sid, serial#, osuser, machine, program
                FROM v\$session WHERE username = 'OBL' AND status <> 'KILLED') LOOP
      DBMS_OUTPUT.PUT_LINE('-- 接続中のセッションを切断: ' || s.osuser || ' / ' ||
                           s.machine || ' / ' || s.program);
      BEGIN
        EXECUTE IMMEDIATE 'ALTER SYSTEM KILL SESSION ''' || s.sid || ',' || s.serial# || ''' IMMEDIATE';
      EXCEPTION WHEN OTHERS THEN NULL;   -- 切断の間に自分で抜けた場合など
      END;
    END LOOP;
    BEGIN
      EXECUTE IMMEDIATE 'DROP USER OBL CASCADE';
      EXIT;
    EXCEPTION WHEN OTHERS THEN
      IF SQLCODE = -1918 THEN EXIT; END IF;          -- 元々いない
      IF SQLCODE != -1940 OR i = 30 THEN
        BEGIN EXECUTE IMMEDIATE 'ALTER USER OBL ACCOUNT UNLOCK';
        EXCEPTION WHEN OTHERS THEN NULL; END;
        RAISE;
      END IF;
      DBMS_SESSION.SLEEP(2);
    END;
  END LOOP;
  BEGIN EXECUTE IMMEDIATE 'DROP TABLESPACE obl_data INCLUDING CONTENTS AND DATAFILES';
  EXCEPTION WHEN OTHERS THEN IF SQLCODE != -959 THEN RAISE; END IF; END;
END;
/
-- ごみ箱の掃除。DROP TABLESPACE ... INCLUDING CONTENTS AND DATAFILES は
-- ごみ箱を経由しないので保険にすぎない。26ai では SYSTEM に PURGE DBA_RECYCLEBIN
-- 権限が既定で付いておらず ORA-01031 になるため、失敗しても止めない。
BEGIN
  EXECUTE IMMEDIATE 'PURGE DBA_RECYCLEBIN';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
CREATE TABLESPACE obl_data
  DATAFILE '/opt/oracle/oradata/FREE/FREEPDB1/obl_data01.dbf'
  SIZE 2G AUTOEXTEND ON NEXT 512M MAXSIZE 9G;
CREATE USER OBL IDENTIFIED BY "${OBL_PWD}"
  DEFAULT TABLESPACE obl_data
  QUOTA UNLIMITED ON obl_data
  PROFILE app_profile;
GRANT CREATE SESSION, RESOURCE, CREATE VIEW, CREATE SYNONYM TO OBL;
EXIT
SQL
[ $? -ne 0 ] && fail "スキーマの再作成に失敗"

# ------------------------------------------------------------
# 5) インポート
#    ★impdp は「エラーありで完了」でも 5 を返す。
#      11.2 由来の PL/SQL が INVALID になる ORA-39082 等は想定内なので 5 は正常扱い。
# ------------------------------------------------------------
echo "-- impdp 実行中（5分ほどかかります）..."
docker exec "$CONTAINER" impdp "$CONN" \
    DIRECTORY=DMPDIR \
    DUMPFILE="$(basename "$WORK")" \
    REMAP_SCHEMA=MINI_TM_SERVER:OBL \
    TRANSFORM=SEGMENT_ATTRIBUTES:N \
    EXCLUDE=STATISTICS \
    LOGFILE="impdp_$(date +%Y%m%d_%H%M%S).log"
RC=$?
if [ $RC -ne 0 ] && [ $RC -ne 5 ]; then
    fail "impdp が異常終了した (rc=$RC)"
fi
echo "-- impdp 完了 (rc=$RC)"

# ------------------------------------------------------------
# 6) 統計収集（EXCLUDE=STATISTICS しているため。2CPU 環境では効果が大きい）
# ------------------------------------------------------------
echo "-- 統計を収集中..."
sq <<'SQL'
SET FEED OFF
EXEC DBMS_STATS.GATHER_SCHEMA_STATS('OBL', degree=>2, cascade=>TRUE);
EXIT
SQL

# ------------------------------------------------------------
# 7) 検証
# ------------------------------------------------------------
AFTER=$(sq <<'SQL' | tr -d ' \r'
SET HEAD OFF FEED OFF PAGES 0
SELECT COUNT(*) FROM obl.assembly_component;
EXIT
SQL
)
case "$AFTER" in
    ''|*[!0-9]*) fail "取込後の件数が取得できない（インポート失敗の疑い）: '$AFTER'" ;;
esac
[ "$AFTER" -eq 0 ] && fail "取込後の件数が 0 件（インポート失敗）"

SIZE_GB=$(sq <<'SQL' | tr -d ' \r'
SET HEAD OFF FEED OFF PAGES 0
SELECT ROUND(SUM(bytes)/1024/1024/1024,2) FROM dba_segments WHERE owner='OBL';
EXIT
SQL
)

echo "-- ASSEMBLY_COMPONENT: $BEFORE -> $AFTER 行"
echo "-- OBL スキーマサイズ: ${SIZE_GB} GB（Free版の上限 12GB）"

# ------------------------------------------------------------
# 8) 後始末
# ------------------------------------------------------------
echo "$SIG" > .last_dmp_sig
mv -f "$WORK" dmp/archive/PDM_DB.DMP        # 切り戻し用に1世代だけ保持
find logs -name 'refresh_*.log' -mtime +60 -delete 2>/dev/null
find dmp  -name 'impdp_*.log'   -mtime +60 -delete 2>/dev/null   # impdp のログも溜まる（1回115KB）

# ------------------------------------------------------------
# 9) 図面一覧の出力（ファイルサーバーとの突合用）
#    \esrv11\output\obbligate_copy\obbligate_all_zumen.csv として参照できる。
#
#    抽出条件は 90_temp/99_tmp/08_obli/09_export_copy_target.py と同じ。
#      - CADネイティブ（DOCUMENT_ENTRY.FILE_NAME）の拡張子が mi / tif であること
#        ＝ファイルサーバーへコピーされる図面。索引JSONとの突合で再現率100%だった。
#        pdf / xlsx / jpg などは一切コピーされないので拾わない
#      - ライフサイクルでは絞らない（InWork も含める）。いまは Approved に
#        なっている図面を落とさないため
#      - FILE_BASE は 図番 + REVISION 2桁。VERSION ではない
#      - 品名は PART.NAME（PART_NAME）と PART_VERSION.NAME（PART_VERSION_NAME）を
#        どちらかに寄せず並べて出す
#      - 列を絞っても行は重複しないので DISTINCT は付けない（実測で同数）
#
#    ⚠ 取り込みが終わってから出す。ここで落ちても DB は最新化済みで
#      .last_dmp_sig も 8) で更新してあるため、翌日まるごとやり直しにはならない。
# ------------------------------------------------------------
ZUMEN_OUT_DIR="${ZUMEN_OUT_DIR:-/home/docker-user/output/obbligate_copy}"
ZUMEN_CSV="$ZUMEN_OUT_DIR/obbligate_all_zumen.csv"
ZUMEN_RAW="dmp/obbligate_all_zumen.raw"
ZUMEN_HEADER='"PART_NUMBER","PART_NAME","PART_VERSION_NAME","DOCUMENT_NUMBER","DOCUMENT_NAME","VER","REV","LIFECYCLE","FILE_BASE","FILE_MODIFIED_ON"'

echo "-- 図面一覧を出力中: $ZUMEN_CSV"
mkdir -p "$ZUMEN_OUT_DIR" || fail "出力先を作成できない: $ZUMEN_OUT_DIR"

sq > "$ZUMEN_RAW" <<'SQL'
WHENEVER SQLERROR EXIT 1
SET MARKUP CSV ON QUOTE ON
SET PAGESIZE 0 FEEDBACK OFF HEADING OFF TERMOUT OFF TRIMSPOOL ON LINESIZE 32767 ARRAYSIZE 1000
SELECT
    p.part_number,
    p.name,
    pv.name,
    d.document_number,
    d.name,
    TO_CHAR(dv.version),
    TO_CHAR(dv.revision),
    dv.lifecycle_state_name,
    d.document_number || LPAD(dv.revision, 2, '0'),
    TO_CHAR(DATE '1970-01-01' + de.file_modify_date / 86400, 'YYYY-MM-DD')
FROM       obl.part                  p
JOIN       obl.part_version          pv  ON pv.super_identification = p.identification
                                        AND pv.lifecycle_state_name = 'Approved'
                                        AND pv.version_mark IN ('LAST','ALONE')
                                        AND pv.to_date = 0
JOIN       obl.part_version_document pvd ON pvd.plus_identification = pv.identification
JOIN       obl.document_version      dv  ON dv.identification       = pvd.minus_identification
                                        AND dv.version_mark IN ('LAST','ALONE')
                                        AND dv.revision IS NOT NULL
JOIN       obl.document              d   ON d.identification        = dv.super_identification
JOIN       obl.document_entry        de  ON de.super_identification = dv.identification
WHERE LOWER(SUBSTR(de.file_name, INSTR(de.file_name, '.', -1) + 1)) IN ('mi','tif')
ORDER BY p.part_number, d.document_number;
EXIT
SQL
RC_CSV=$?

if [ $RC_CSV -ne 0 ]; then
    rm -f "$ZUMEN_RAW"
    fail "図面一覧の抽出に失敗した (rc=$RC_CSV)"
fi
# sqlplus は SQL のエラーでも rc=0 で本文にメッセージを吐くことがあるため中身も見る
if grep -qE '^(ORA|SP2)-[0-9]' "$ZUMEN_RAW"; then
    grep -m3 -E '^(ORA|SP2)-[0-9]' "$ZUMEN_RAW"
    rm -f "$ZUMEN_RAW"
    fail "図面一覧の抽出中にエラーが出た"
fi
ZUMEN_ROWS=$(wc -l < "$ZUMEN_RAW")
if [ "$ZUMEN_ROWS" -lt 1000 ]; then
    rm -f "$ZUMEN_RAW"
    fail "図面一覧が $ZUMEN_ROWS 行しかない（抽出失敗の疑い）"
fi

# Excel でそのまま開けるよう UTF-8 BOM 付き・CRLF で書く（09_export_copy_target.py と同じ）
{
    printf '\xEF\xBB\xBF'
    printf '%s\r\n' "$ZUMEN_HEADER"
    sed 's/\r*$/\r/' "$ZUMEN_RAW"
} > "$ZUMEN_CSV.tmp" || { rm -f "$ZUMEN_RAW" "$ZUMEN_CSV.tmp"; fail "CSV の書き出しに失敗した"; }

# 読み取り中の半端なファイルを見せないよう、書き終えてから差し替える
mv -f "$ZUMEN_CSV.tmp" "$ZUMEN_CSV" || fail "CSV の差し替えに失敗した"
chmod 644 "$ZUMEN_CSV"
echo "-- 図面一覧: $ZUMEN_ROWS 行 / $(stat -c '%s' "$ZUMEN_CSV") バイト"


# ------------------------------------------------------------
# 10) 前回との差分を出力（行単位の 追加／削除）
#     \esrv11\output\obbligate_copy\diff\obbligate_zumen_diff_<日付>.csv
#
#     9) の一覧を前回分とまるごと比べ、前回に無かった行を「追加」、
#     前回にあって今回消えた行を「削除」として DIFF_TYPE 列を先頭に付ける。
#     REV や更新日が変わった図面は「削除」＋「追加」の2行で現れる（キーを置かず
#     全列を1行として比べるため、取りこぼしが出ない）。
#     差分が無い日もヘッダー行だけの CSV を必ず作る（0行＝比較はした、の意）。
#
#     比較用の前回分は .obbligate_all_zumen.prev.csv（ヘッダー・BOM 無しの生データ）
#     として1世代だけ持つ。⚠ 24MB のフル一覧を日ごとに残すと 700MB を超えるので、
#     1か月分残すのは小さい差分 CSV だけにしてある。
#     ⚠ 前回分の列構成は .prev.csv.header に控える。列を増減した直後に比べると
#       全行が「削除＋追加」になり巨大な差分が出るため、構成が違えば初回と同じく 0 行にする。
# ------------------------------------------------------------
ZUMEN_PREV="$ZUMEN_OUT_DIR/.obbligate_all_zumen.prev.csv"
ZUMEN_DIFF_DIR="$ZUMEN_OUT_DIR/diff"
ZUMEN_DIFF="$ZUMEN_DIFF_DIR/obbligate_zumen_diff_$(date +%Y%m%d).csv"
ZUMEN_ADDED="$ZUMEN_RAW.added"
ZUMEN_DELETED="$ZUMEN_RAW.deleted"
ZUMEN_PREV_HEADER="$ZUMEN_PREV.header"

mkdir -p "$ZUMEN_DIFF_DIR" || fail "差分の出力先を作成できない: $ZUMEN_DIFF_DIR"
: > "$ZUMEN_ADDED"
: > "$ZUMEN_DELETED"

if [ -s "$ZUMEN_PREV" ] && [ "$(cat "$ZUMEN_PREV_HEADER" 2>/dev/null)" != "$ZUMEN_HEADER" ]; then
    # 列を増減した直後。比べると全行が差分になるので 0 行にする
    echo "-- 前回分と列構成が違うため差分は 0 行（次回から比較する）"
elif [ -s "$ZUMEN_PREV" ]; then
    # comm は「同じ並び順で整列済み」が前提。ロケールで並びが変わらないよう LC_ALL=C で揃える
    LC_ALL=C sort "$ZUMEN_RAW"  > "$ZUMEN_RAW.new" || fail "差分用の整列に失敗した（今回分）"
    LC_ALL=C sort "$ZUMEN_PREV" > "$ZUMEN_RAW.old" || fail "差分用の整列に失敗した（前回分）"
    LC_ALL=C comm -13 "$ZUMEN_RAW.old" "$ZUMEN_RAW.new" > "$ZUMEN_ADDED"   || fail "差分（追加）の抽出に失敗した"
    LC_ALL=C comm -23 "$ZUMEN_RAW.old" "$ZUMEN_RAW.new" > "$ZUMEN_DELETED" || fail "差分（削除）の抽出に失敗した"
    rm -f "$ZUMEN_RAW.new" "$ZUMEN_RAW.old"
else
    # 初回は比べる相手が無い。全件を「追加」として出すと 24MB になるので 0 行にする
    echo "-- 前回分が無いため差分は 0 行（次回から比較する）"
fi

# 9) と同じく UTF-8 BOM 付き・CRLF
{
    printf '\xEF\xBB\xBF'
    printf '"DIFF_TYPE",%s\r\n' "$ZUMEN_HEADER"
    sed 's/^/"追加",/; s/\r*$/\r/' "$ZUMEN_ADDED"
    sed 's/^/"削除",/; s/\r*$/\r/' "$ZUMEN_DELETED"
} > "$ZUMEN_DIFF.tmp" || { rm -f "$ZUMEN_DIFF.tmp" "$ZUMEN_ADDED" "$ZUMEN_DELETED"; fail "差分の書き出しに失敗した"; }

mv -f "$ZUMEN_DIFF.tmp" "$ZUMEN_DIFF" || fail "差分 CSV の差し替えに失敗した"
chmod 644 "$ZUMEN_DIFF"
echo "-- 差分: 追加 $(wc -l < "$ZUMEN_ADDED") 行 / 削除 $(wc -l < "$ZUMEN_DELETED") 行 → $ZUMEN_DIFF"

# 次回の比較用に今回分を残す（書き終えてから差し替える）
cp -f "$ZUMEN_RAW" "$ZUMEN_PREV.tmp" || fail "前回分の控えを書けない: $ZUMEN_PREV"
mv -f "$ZUMEN_PREV.tmp" "$ZUMEN_PREV" || fail "前回分の差し替えに失敗した"
chmod 644 "$ZUMEN_PREV"
printf '%s\n' "$ZUMEN_HEADER" > "$ZUMEN_PREV_HEADER" || fail "前回分の列構成を書けない: $ZUMEN_PREV_HEADER"
rm -f "$ZUMEN_RAW" "$ZUMEN_ADDED" "$ZUMEN_DELETED"

# 1か月分だけ残す
find "$ZUMEN_DIFF_DIR" -name 'obbligate_zumen_diff_*.csv' -mtime +30 -delete 2>/dev/null


# ------------------------------------------------------------
# 11) 品目の単価・在庫情報の全件出力
#     \esrv11\output\obbligate_copy\obbligate_part_price.csv
#
#     Obbligato へ取り込まれている単価CSV（E<日時>.csv）と同じ形式で、
#     FKS_PART（PART_VERSION と1:1の独自属性）を全品番ぶん出す。
#       - 1品番1行。版が複数あれば VERSION 最大の版の値を出す
#       - 品目名は PART_VERSION.NAME。取込元CSVの品目名は Obbligato に
#         書き込まれていない（登録元の名称）ため一致しない行がある
#       - 書式は取込元CSVに合わせる: UTF-8 BOM 無し・CRLF・全項目を "" で囲み、
#         行末に余分なカンマ。単価は整数なら小数点なし（504）、小数はそのまま（6142.5）
#     ⚠ SET MARKUP CSV は使わず、1行を SQL で組み立てる（行末カンマと NULL の "" を
#       取込元CSVと同じにするため）
# ------------------------------------------------------------
PRICE_CSV="$ZUMEN_OUT_DIR/obbligate_part_price.csv"
PRICE_RAW="dmp/obbligate_part_price.raw"
PRICE_HEADER='"品目番号","品目名","在庫数","単価","発注担当者","保管区","仕入先",'

echo "-- 単価・在庫情報を出力中: $PRICE_CSV"

sq > "$PRICE_RAW" <<'SQL'
WHENEVER SQLERROR EXIT 1
SET PAGESIZE 0 FEEDBACK OFF HEADING OFF TERMOUT OFF TRIMOUT ON TRIMSPOOL ON LINESIZE 32767 ARRAYSIZE 1000
SELECT '"' || REPLACE(part_number, '"', '""') || '",'
    || '"' || REPLACE(name,        '"', '""') || '",'
    || '"' || REPLACE(stock,       '"', '""') || '",'
    || '"' || RTRIM(TO_CHAR(price, 'FM999999999999990.99999999'), '.') || '",'
    || '"' || REPLACE(person,      '"', '""') || '",'
    || '"' || REPLACE(place,       '"', '""') || '",'
    || '"' || REPLACE(supplier,    '"', '""') || '",'
FROM (
    SELECT p.part_number,
           pv.name,
           f.fks_prt_stock_count   AS stock,
           f.fks_prt_unit_price    AS price,
           f.fks_prt_order_person  AS person,
           f.fks_prt_storage_place AS place,
           f.fks_prt_supplier      AS supplier,
           ROW_NUMBER() OVER (
               PARTITION BY p.identification
               ORDER BY TO_NUMBER(pv.version DEFAULT -1 ON CONVERSION ERROR) DESC
           ) AS rn
    FROM obl.part p
    JOIN obl.part_version pv ON pv.super_identification = p.identification
    JOIN obl.fks_part     f  ON f.super_identification  = pv.identification
)
WHERE rn = 1
ORDER BY part_number;
EXIT
SQL
RC_PRICE=$?

if [ $RC_PRICE -ne 0 ]; then
    rm -f "$PRICE_RAW"
    fail "単価・在庫情報の抽出に失敗した (rc=$RC_PRICE)"
fi
if grep -qE '^(ORA|SP2)-[0-9]' "$PRICE_RAW"; then
    grep -m3 -E '^(ORA|SP2)-[0-9]' "$PRICE_RAW"
    rm -f "$PRICE_RAW"
    fail "単価・在庫情報の抽出中にエラーが出た"
fi
PRICE_ROWS=$(wc -l < "$PRICE_RAW")
if [ "$PRICE_ROWS" -lt 100000 ]; then
    rm -f "$PRICE_RAW"
    fail "単価・在庫情報が $PRICE_ROWS 行しかない（抽出失敗の疑い）"
fi

# ⚠ DB には Shift-JIS のバイトのまま入った品番がある（4119-67T0130017402ﾚｰｽS。2026-10-06 確認）。
#   そのまま出すとファイル全体が UTF-8 として開けなくなるため、UTF-8 として読めない項目は
#   ASCII 以外のバイトをすべて ? にする（→ 4119-67T0130017402???S）。
#   バイト単位で置き換えないのは、先頭の2バイトがたまたま UTF-8 として読めて
#   別の文字（ڰ）に化け、文字化けと気づきにくくなるため
{
    printf '%s\r\n' "$PRICE_HEADER"
    perl -MEncode -pe '
        s{"((?:[^"]|"")*)"}{
            my $f = $1;
            eval { Encode::decode("UTF-8", $f, Encode::FB_CROAK | Encode::LEAVE_SRC); 1 }
                or $f =~ s/[\x80-\xFF]/?/g;
            "\"$f\""
        }ge' "$PRICE_RAW" | sed 's/\r*$/\r/'
} > "$PRICE_CSV.tmp" || { rm -f "$PRICE_RAW" "$PRICE_CSV.tmp"; fail "単価・在庫情報の書き出しに失敗した"; }

mv -f "$PRICE_CSV.tmp" "$PRICE_CSV" || fail "単価・在庫情報の差し替えに失敗した"
chmod 644 "$PRICE_CSV"
rm -f "$PRICE_RAW"
echo "-- 単価・在庫情報: $PRICE_ROWS 行 / $(stat -c '%s' "$PRICE_CSV") バイト"

echo "=== $(date '+%F %T') refresh 正常終了 (impdp rc=$RC) ==="
