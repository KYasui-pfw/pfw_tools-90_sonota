"""データ更新（加工伝票 → genpinhyo）。画面の「データ更新」と夜間処理が使う、ただ1つの処理。

⚠⚠ 2026-10 の作り直しより前は、同じ処理が3か所（1_現品票発行.py・create_report.py・dbupdate.py）に
  書かれていて、**中身が食い違っていた**（夜間処理には払出先の除外も CHANGE GEAR BOX も無かった）。
  そのため2つが交互に走るたびに約4,000件の削除フラグが反転し、記録が1GB近く貯まっていた。
  この処理を変えるときは、ここだけを直す（コピーを作らない）。

【流れ】
    1. 業務ポータルから加工伝票（伝票単位・払出先で絞る前）を取る。VER・工程・メッキも付いてくる
    2. 対象外の伝票を外す（A+数字8桁の組立番号・払出先）
    3. （停止中）CHANGE GEAR BOX を rBOM の引当から足す（時限処理。2026-10-28 に止めた）
    4. 客先名・国名（i-Reporter の客先マスタ）と図番（業務ポータル）を付ける
    5. genpinhyo に書く。新しい部品名を buhin_irepo_mst に足す
    6. 削除フラグを付け直す（当月〜3か月先で、加工伝票から消えたロット＝1）
    7. 払出先で全行が除外になったロットを excluded_lots に入れ直す
   5〜7 は1つのトランザクション（途中で失敗したら何も書かない）。
"""

import re
from dataclasses import dataclass

from dateutil.relativedelta import relativedelta

from . import config, db, irepo, portal_api, rbom

# ---------------------------------------------------------------------------
# 対象外にする伝票の決まり
# ---------------------------------------------------------------------------
# 組立番号が A＋数字8桁（例 A00012345）は在庫用の製番なので、現品票を出さない。
STOCK_ASSY_PATTERN = re.compile(r"^A\d{8}$")

CHANGE_GEAR_BOX = "CHANGE GEAR BOX"

# 払出先の除外（時限処理・2026-01-15 追加）。
#   特定5部品 … 払出先 40 を捨て、60 を残す（シリンダー課の伝票を残す）
#   それ以外  … 払出先 49・60 を捨てる
# ⚠ 業務ポータル側（apps/machining_schedule/pipeline.py の is_output_target）にも同じ決まりがある。
#   あちらは払出先 PT も捨てるが、現品票では捨てていない（昔からの違い）。
SPECIAL_PARTS = frozenset({
    "SINKER REST RING", "NEEDLE DIAL", "NEEDLE CYLINDER", "SINKER DIAL", "WRAP DIAL",
})
SPECIAL_EXCLUDE_SRCD = {"40"}
NORMAL_EXCLUDE_SRCD = {"49", "60"}

# 削除フラグを付け直す範囲（当月から何か月先まで）。
DELETE_CHECK_MONTHS = 4

# buhin_irepo_mst に新しい部品名を足すときの初期値。
# QRコードレイアウト区分 = 2 は「新しい部品名なので設定してほしい」の目印
# （現品票にはエラーの画像が出る。2025-01-22 から）。
NEW_PART_DEFAULTS = {"ireporter管理flg": 0, "QRコードレイアウト区分": 2, "縦横区分": 0}

# メッキありのときに genpinhyo.ﾒｯｷ に入れる値。
# ⚠ i-Reporter の header_koushin.py が '1.0' と一致するかで判定しているので変えないこと。
PLATING_TEXT = "1.0"


@dataclass
class UpdateResult:
    """データ更新の結果（画面に件数を出すため）。"""
    written: int = 0          # genpinhyo に書いたロット数
    excluded: int = 0         # 払出先で全行が除外になったロット数
    change_gear_boxes: int = 0
    deleted_on: int = 0       # 削除フラグが 0 → 1 になったロット数
    deleted_off: int = 0      # 削除フラグが 1 → 0 になったロット数
    new_parts: int = 0        # buhin_irepo_mst に新しく足した部品名の数


# ---------------------------------------------------------------------------
# 値の表記をそろえる小さな関数
# ---------------------------------------------------------------------------

def to_int_text(value):
    """'34.0' → '34'、'34.5' → '34.5'、'' → ''。数値で読めなければそのまま。"""
    if value is None:
        return ""
    text = str(value).strip()
    if text in ("", "nan", "None"):
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return str(int(number))
    return text


def to_slash_date(value):
    """'2026-03-12T00:00:00' や '2026/03/12' を '2026/03/12' にする。空は ''。"""
    if not value:
        return ""
    text = str(value).strip()
    return text[:10].replace("-", "/")


def to_getsuji_text(value):
    """生産月次を文字にする。6桁（YYYYMM だけ）なら末尾に '_' を足す（例 '202610' → '202610_'）。"""
    text = to_int_text(value)
    if len(text) == 6:
        text += "_"
    return text


def half_space(value):
    """全角スペースを半角にする（印字の幅がずれないよう、昔からしている）。"""
    return (value or "").replace("　", " ")


def make_assy_no(seino):
    """CHANGE GEAR BOX の組立番号を製番から作る（数字2＋英字3＋数字3 なら末尾4文字。26SKD002 → D002）。"""
    text = str(seino).strip()
    if len(text) == 8 and text[:2].isdigit() and text[2:5].isalpha() and text[5:].isdigit():
        return text[-4:]
    return text


# ---------------------------------------------------------------------------
# 2. 対象外の伝票を外す
# ---------------------------------------------------------------------------

def is_excluded_by_srcd(part_name, srcd):
    """払出先で除外する行か（決まりは SPECIAL_PARTS の説明を参照）。"""
    if part_name in SPECIAL_PARTS:
        return srcd in SPECIAL_EXCLUDE_SRCD
    return srcd in NORMAL_EXCLUDE_SRCD


def filter_slips(slips):
    """対象外の伝票を外す。

    Returns:
        (残す伝票のリスト, 払出先で「全行が」除外になったロット番号の集合)

    ⚠ 同じ伝票Ｎｏが2行あることがある（特定5部品の MCKR 複製＝払出先 40 と 60 の組）。
      片方だけ除外になったロットは excluded_lots に入れない（残した行まで隠れてしまうため）。
    """
    kept = []
    excluded_flags = {}   # ロット番号 → 全行が除外か
    for slip in slips:
        assy_no = (slip.get("assy_no") or "").strip()
        if STOCK_ASSY_PATTERN.match(assy_no):
            continue
        # （停止中・2026-10-28）CHANGE GEAR BOX で製番が数字だけのもの（時限処理・2026-05-26 追加）は、
        # rBOM の引当から CH番号で別に作るので、加工伝票側は使わない。
        # 戻すときは下の2行と、run_update の build_change_gear_boxes・cgb_seino_ch_mapping の書き込みを一緒に戻す。
        # if (slip.get("model_name") or "").strip() == CHANGE_GEAR_BOX and assy_no.isdigit():
        #     continue

        excluded = is_excluded_by_srcd(slip.get("part_name", ""), slip.get("srcd", ""))
        lot_no = slip["denpyo_no"]
        excluded_flags[lot_no] = excluded_flags.get(lot_no, True) and excluded
        if not excluded:
            kept.append(slip)

    fully_excluded = {lot_no for lot_no, flag in excluded_flags.items() if flag}
    return kept, fully_excluded


# ---------------------------------------------------------------------------
# 3. CHANGE GEAR BOX（時限処理・2026-05-26 追加）
# ---------------------------------------------------------------------------
# ⚠ 2026-10-28 に停止（CH のロット番号はもう発生しない見込みのため）。run_update から呼んでいない。
#   何かのときの参考に、処理はそのまま残してある（rbom.py も同じ）。
# rBOM の加工伝票に出てこない CHANGE GEAR BOX を、引当（D3520）から現品票にする。
# ロット番号は製番ごとに CH＋8桁で振り、cgb_seino_ch_mapping に覚えておく（次回も同じ番号になる）。

def build_change_gear_boxes(conn, kept_slips):
    """CHANGE GEAR BOX の伝票（加工伝票と同じ形の辞書）を作る。

    Returns:
        (伝票のリスト, 新しく振った (製番, CH番号) のリスト)
    """
    allocations = rbom.fetch_change_gear_boxes()
    if not allocations:
        return [], []

    ch_by_seino = dict(conn.execute("SELECT seino, ch_no FROM cgb_seino_ch_mapping"))
    last_number = max(
        _ch_number(conn.execute(
            "SELECT MAX(ロット番号) FROM genpinhyo WHERE ロット番号 LIKE 'CH%'").fetchone()[0]),
        _ch_number(conn.execute(
            "SELECT MAX(ch_no) FROM cgb_seino_ch_mapping WHERE ch_no LIKE 'CH%'").fetchone()[0]),
    )

    # 機種・客先などは、同じ製番の加工伝票から借りる（引当には無いため）。
    slip_by_seino = {}
    for slip in kept_slips:
        slip_by_seino.setdefault((slip.get("seino") or "").strip(), slip)

    slips = []
    new_mappings = []
    for row in allocations:
        seino = str(row.get("SEINO") or "").strip()
        if seino in ch_by_seino:
            ch_no = ch_by_seino[seino]
        else:
            last_number += 1
            ch_no = f"CH{last_number:08d}"
            ch_by_seino[seino] = ch_no
            new_mappings.append((seino, ch_no))

        source = slip_by_seino.get(seino, {})
        slips.append({
            "denpyo_no": ch_no,
            "getsuji": to_int_text(row.get("GETSUJI")),
            "assy_no": make_assy_no(seino),
            "model_name": source.get("model_name", ""),
            "inch": source.get("inch", ""),
            "gauge": source.get("gauge", ""),
            "hmcd": str(row.get("HMCD") or ""),
            "part_name": CHANGE_GEAR_BOX,
            "required_qty": row.get("ALCQTY"),
            "seino": seino,
            "srcd": "40",
            "customer_cd": source.get("customer_cd", ""),
            "skdk": source.get("skdk", ""),
            "assy_start": to_slash_date(row.get("ASPLDT")),
            "konpo_start": to_slash_date(row.get("SPPLDT")),
            "due_date": to_slash_date(row.get("TDPLNDT")),
        })

    # VER・工程・メッキは、作業計画に無い伝票と同じ決め方（優先VER → 1）で業務ポータルに聞く。
    resolved = portal_api.fetch_lots([(slip["denpyo_no"], slip["hmcd"]) for slip in slips])
    for slip, info in zip(slips, resolved):
        slip["version"] = info["version"]
        slip["process_str"] = info["process_str"]
        slip["is_plating"] = info["is_plating"]
    return slips, new_mappings


def _ch_number(text):
    """'CH00000635' → 635。空なら 0。"""
    if not text:
        return 0
    try:
        return int(str(text)[2:])
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# 4〜5. genpinhyo の1行を作る
# ---------------------------------------------------------------------------

def build_records(slips, customers, drawings):
    """伝票から genpinhyo の行（列名 → 値の辞書）を作る。

    Args:
        slips: 伝票の辞書のリスト（業務ポータルの項目名）
        customers: 客先コード → (客先名, 国名)
        drawings: 加工部番 → 図番の辞書（portal_api.fetch_drawings の1行）
    """
    records = []
    for slip in slips:
        hmcd = slip.get("hmcd") or ""
        customer_name, country = customers.get(slip.get("customer_cd") or "", ("", ""))
        drawing = drawings.get(hmcd, {})

        record = {
            "ロット番号": slip["denpyo_no"],
            "月次": to_getsuji_text(slip.get("getsuji")),
            "組立番号": half_space(slip.get("assy_no")),
            "機種": half_space(slip.get("model_name")),
            "吋": to_int_text(slip.get("inch")),
            "G": to_int_text(slip.get("gauge")),
            "完成部番": half_space(hmcd),
            "部品名": (slip.get("part_name") or "").strip(),
            "客先名": half_space(customer_name),
            "国名": half_space(country),
            "組立開始日": slip.get("assy_start") or "",
            "梱包開始日": slip.get("konpo_start") or "",
            "指定納期": slip.get("due_date") or "",
            "必要数": to_int_text(slip.get("required_qty")),
            "SKDK": slip.get("skdk") or "",
            "工程": slip.get("process_str") or "",
            "工程VERSION": to_int_text(slip.get("version")),
            "ﾒｯｷ": PLATING_TEXT if slip.get("is_plating") else "",
            "客先コード": slip.get("customer_cd") or "",
        }
        for api_key, column in portal_api.DRAWING_COLUMNS.items():
            record[column] = drawing.get(api_key) or ""
        records.append(record)
    return records


# ---------------------------------------------------------------------------
# 6. 削除フラグ
# ---------------------------------------------------------------------------

def delete_check_prefixes(today):
    """削除フラグを付け直す月次の先頭6桁（当月〜3か月先）。"""
    return [f"{today + relativedelta(months=offset):%Y%m}" for offset in range(DELETE_CHECK_MONTHS)]


def update_delete_flags(conn, current_lots, today):
    """当月〜3か月先のロットについて、加工伝票にあれば 0、無ければ 1 にする。

    Returns:
        (0→1 の件数, 1→0 の件数)
    """
    # genpinhyo にあって delete_mst に無いロットは 0 で足す。
    conn.execute(
        "INSERT OR IGNORE INTO delete_mst (ロット番号, 削除flg) SELECT ロット番号, 0 FROM genpinhyo"
    )

    prefixes = delete_check_prefixes(today)
    condition = " OR ".join("g.月次 LIKE ?" for _ in prefixes)
    rows = conn.execute(
        "SELECT g.ロット番号, d.削除flg FROM genpinhyo g"
        " JOIN delete_mst d ON d.ロット番号 = g.ロット番号"
        f" WHERE {condition}",
        [prefix + "%" for prefix in prefixes],
    ).fetchall()

    stamp = f"{config.now():%Y-%m-%d %H:%M:%S}"
    changes = []
    for lot_no, old_flag in rows:
        new_flag = 0 if lot_no in current_lots else 1
        if old_flag != new_flag:
            changes.append((lot_no, old_flag, new_flag))

    conn.executemany(
        "UPDATE delete_mst SET 削除flg = ? WHERE ロット番号 = ?",
        [(new_flag, lot_no) for lot_no, _, new_flag in changes],
    )
    conn.executemany(
        "INSERT INTO flag_change_log (changed_at, ロット番号, old_flg, new_flg) VALUES (?, ?, ?, ?)",
        [(stamp, lot_no, old_flag, new_flag) for lot_no, old_flag, new_flag in changes],
    )
    turned_on = sum(1 for _, _, new_flag in changes if new_flag == 1)
    return turned_on, len(changes) - turned_on


# ---------------------------------------------------------------------------
# 本体
# ---------------------------------------------------------------------------

def run_update():
    """データ更新を行う。

    Raises:
        portal_api.PortalApiError / rbom.RbomApiError: 外から取れなかった（DB は何も変わらない）
        db.DatabaseCorruptedError: DB が壊れている（DB は何も変わらない）
    """
    # 外から取ってくるものは、DB を開く前に全部そろえる（途中で失敗したら書かずに終わる）。
    slips = portal_api.fetch_denpyo()
    kept, fully_excluded = filter_slips(slips)
    customers = {
        str(row["客先コード"]): (row["客先名"] or "", row["国名"] or "")
        for row in irepo.fetch_customers().to_dict("records")
    }

    conn = db.connect()
    try:
        # 壊れた DB に書くと同じロットの行が増えていくので、点検してから書く。
        # バックアップより先に点検する（壊れた写しで、その日のバックアップを上書きしないため）。
        db.check_integrity(conn)
        db.backup_genpinhyo()
        db.ensure_schema(conn)
        # （停止中・2026-10-28）CHANGE GEAR BOX の時限処理。戻すときは filter_slips の除外も一緒に戻す。
        # change_gear_boxes, new_mappings = build_change_gear_boxes(conn, kept)
        # all_slips = kept + change_gear_boxes
        change_gear_boxes = []
        all_slips = kept

        hmcds = sorted({slip.get("hmcd") or "" for slip in all_slips} - {""})
        drawings = {row["item"]: row for row in portal_api.fetch_drawings(hmcds)}
        records = build_records(all_slips, customers, drawings)

        # --- ここから書き込み（1つのトランザクション） ---
        columns = db.GENPINHYO_COLUMNS
        conn.executemany(
            f"REPLACE INTO genpinhyo ({', '.join(columns)})"
            f" VALUES ({', '.join('?' for _ in columns)})",
            [[record[column] for column in columns] for record in records],
        )
        # （停止中・2026-10-28）CHANGE GEAR BOX の CH番号を覚えておく。
        # conn.executemany(
        #     "INSERT OR IGNORE INTO cgb_seino_ch_mapping (seino, ch_no) VALUES (?, ?)",
        #     new_mappings,
        # )

        before = conn.total_changes
        conn.executemany(
            "INSERT OR IGNORE INTO buhin_irepo_mst"
            " (部品名, ireporter管理flg, QRコードレイアウト区分, 縦横区分) VALUES (?, ?, ?, ?)",
            [(name, *NEW_PART_DEFAULTS.values()) for name in sorted({r["部品名"] for r in records})],
        )
        new_parts = conn.total_changes - before

        current_lots = {record["ロット番号"] for record in records}
        turned_on, turned_off = update_delete_flags(conn, current_lots, config.now())

        conn.execute("DELETE FROM excluded_lots")
        conn.executemany(
            "INSERT OR IGNORE INTO excluded_lots (ロット番号) VALUES (?)",
            [(lot_no,) for lot_no in sorted(fully_excluded)],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return UpdateResult(
        written=len(records),
        excluded=len(fully_excluded),
        change_gear_boxes=len(change_gear_boxes),
        deleted_on=turned_on,
        deleted_off=turned_off,
        new_parts=new_parts,
    )
