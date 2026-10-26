import csv
import os
import shutil
import sqlite3
import sys
import threading
from datetime import datetime, timedelta, timezone

from nicegui import ui, app, run

# 業務ポータル（Django）の API 呼び出しは親フォルダの genpin/portal_api.py を使う
# （標準ライブラリだけで書いてあるので、この venv にも追加のインストールは要らない）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from genpin import portal_api  # noqa: E402

# ── Constants ──────────────────────────────────────────────────────────────
PASSWORD = 'pfwpass'
PORT = 8506
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Database')
CHECKSHEET_DB = os.path.join(DB_DIR, 'checksheet.db')
GENPINHYO_DB  = os.path.join(DB_DIR, 'genpinhyo.db')
# KRD（krd_machine.db）は使わなくなった（2026-10-23）。工程・加工機・図番は業務ポータルの API から取る

ITEM_NUMS = ['１','２','３','４','５','６','７','８','９','１０','１１','１２','１３','１４','１５']

_master_synced = False

# ── DB helpers ─────────────────────────────────────────────────────────────

def _connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def backup_db(path):
    jst = datetime.now(timezone(timedelta(hours=9)))
    backup_dir = os.path.join(DB_DIR, 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    dest = os.path.join(backup_dir, f'{jst.strftime("%Y%m%d")}_{os.path.basename(path)}')
    if os.path.exists(path) and not os.path.exists(dest):
        shutil.copy(path, dest)

def ensure_tables():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(CHECKSHEET_DB)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS kouteizuban(
        ID integer primary key autoincrement,
        完成部番 TEXT, 工程Ver INTEGER, 工程順 INTEGER, 工程 TEXT,
        加工機１ TEXT, 図番１ TEXT, 加工機２ TEXT, 図番２ TEXT,
        未使用flg INTEGER,
        UNIQUE(完成部番, 工程Ver, 工程順))''')
    item_cols = ' '.join(
        f'チェック項目{n} TEXT, チェック基準{n} TEXT,' for n in ITEM_NUMS
    ).rstrip(',')
    cur.execute(f'''CREATE TABLE IF NOT EXISTS zubancheck(
        ID integer primary key autoincrement,
        連携ID INTEGER, 工程順 INTEGER, 工程順SUB INTEGER, 図面Ver INTEGER,
        生産開始月 TEXT, {item_cols}, 未使用flg INTEGER,
        UNIQUE(連携ID, 工程順SUB, 図面Ver))''')
    conn.commit()
    conn.close()

# ── DB write functions ─────────────────────────────────────────────────────

def _log_master_deleted(kz_rows, zc_rows):
    """品目工程マスタとの同期で削除した行をCSVに残す（誤削除時の確認・復旧用）"""
    jst = datetime.now(timezone(timedelta(hours=9)))
    out_dir = os.path.join(DB_DIR, 'backup')
    os.makedirs(out_dir, exist_ok=True)
    stamp = jst.strftime('%Y%m%d_%H%M%S')
    for name, rows in (('kouteizuban', kz_rows), ('zubancheck', zc_rows)):
        if not rows:
            continue
        path = os.path.join(out_dir, f'{stamp}_mastersync_deleted_{name}.csv')
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(rows[0].keys())
            w.writerows(tuple(r) for r in rows)


def db_update1():
    global _master_synced
    if _master_synced:
        return
    try:
        backup_db(CHECKSHEET_DB)
        ensure_tables()
        # 業務ポータルの品目工程マスタ＋加工機名（KRD の DATA_RES_CAPA＋MSTR_RES の代わり。2026-10-23）
        # 並びは KRD のときと同じ（完成部番, 工程Ver, 工程, 工程順, 加工機１）
        try:
            master = portal_api.fetch_process_master()
        except portal_api.PortalApiError as e:
            # 読めなかった／0件のときに全削除してしまわないための安全弁（0件も PfwApiError になる）
            print(f'[db_update1] 業務ポータルから取得できないため同期を中止しました: {e}')
            return
        rows = [(r['final_item_code'], r['version'], r['process_code'], r['process_order'],
                 r['res_name1'] or '') for r in master]

        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            c.executemany('''
                INSERT INTO kouteizuban(完成部番, 工程Ver, 工程, 工程順, 加工機１)
                VALUES(?,?,?,?,?)
                ON CONFLICT(完成部番, 工程Ver, 工程順) DO UPDATE SET
                    工程=excluded.工程, 加工機１=excluded.加工機１, 未使用flg=0
            ''', rows[i:i + batch_size])

        # ── 品目工程マスタから消えた工程を削除して、マスタに合わせ直す ──────
        # 対象はマスタ由来の行（工程順が整数）のみ。工程順が数値でない行
        # （完成部番=伝票Ｎｏ型など）は別用途データなので触らない。
        c.execute('CREATE TEMP TABLE master_key(完成部番 TEXT, 工程Ver INTEGER, 工程順 INTEGER)')
        c.executemany('INSERT INTO master_key VALUES(?,?,?)',
                      [(r[0], r[1], r[3]) for r in rows])
        c.execute('CREATE INDEX ix_master_key ON master_key(完成部番, 工程Ver, 工程順)')
        c.execute('''
            CREATE TEMP TABLE stale AS
            SELECT k.ID AS ID FROM kouteizuban k
            WHERE typeof(k.工程順) = 'integer'
              AND NOT EXISTS (SELECT 1 FROM master_key t
                              WHERE t.完成部番 = k.完成部番
                                AND t.工程Ver  = k.工程Ver
                                AND t.工程順   = k.工程順)
        ''')
        n_stale = c.execute('SELECT COUNT(*) FROM stale').fetchone()[0]
        n_master_side = c.execute(
            "SELECT COUNT(*) FROM kouteizuban WHERE typeof(工程順)='integer'").fetchone()[0]
        limit = max(500, int(n_master_side * 0.2))
        if n_stale > limit:
            # マスタ側の事故で大量に消える事態を防ぐ。取り込み自体を巻き戻す
            conn.rollback()
            conn.close()
            print(f'[db_update1] 削除対象が異常に多いため同期を中止しました'
                  f' (対象{n_stale}行 / マスタ由来{n_master_side}行, 上限{limit}行)')
            return

        kz = c.execute('SELECT k.* FROM kouteizuban k JOIN stale s ON k.ID = s.ID').fetchall()
        zc = c.execute('''
            SELECT z.* FROM zubancheck z
            WHERE z.連携ID IN (SELECT ID FROM stale)
               OR (z.連携ID IS NOT NULL
                   AND z.連携ID NOT IN (SELECT ID FROM kouteizuban))
        ''').fetchall()
        if kz or zc:
            _log_master_deleted(kz, zc)
        c.execute('DELETE FROM zubancheck WHERE 連携ID IN (SELECT ID FROM stale)')
        c.execute('DELETE FROM kouteizuban WHERE ID IN (SELECT ID FROM stale)')
        # 連携先が消えている zubancheck の孤児も掃除する
        c.execute('''DELETE FROM zubancheck
                     WHERE 連携ID IS NOT NULL
                       AND 連携ID NOT IN (SELECT ID FROM kouteizuban)''')

        c.execute('''
            INSERT INTO zubancheck(連携ID, 工程順, 図面Ver, 工程順SUB)
            SELECT k.ID, k.工程順, 1, 1 FROM kouteizuban k
            LEFT JOIN zubancheck z ON k.ID=z.連携ID WHERE z.連携ID IS NULL
        ''')
        conn.commit()
        conn.close()
        _master_synced = True
        if kz or zc:
            print(f'[db_update1] 品目工程マスタに合わせて kouteizuban {len(kz)}行 /'
                  f' zubancheck {len(zc)}行 を削除しました')
    except Exception as e:
        print(f'[db_update1] 品目工程マスタの同期でエラー: {e}')
        ensure_tables()

def db_update2(rows):
    backup_db(CHECKSHEET_DB)
    conn = sqlite3.connect(CHECKSHEET_DB)
    c = conn.cursor()
    try:
        delete_ids = [r['ID'] for r in rows if int(r.get('未使用flg') or 0) == 1]
        update_rows = [
            (r.get('加工機１') or 'なし', r.get('図番１') or 'なし',
             r.get('加工機２') or 'なし', r.get('図番２') or 'なし', r['ID'])
            for r in rows if int(r.get('未使用flg') or 0) != 1
        ]
        if update_rows:
            c.executemany(
                'UPDATE kouteizuban SET 加工機１=?,図番１=?,加工機２=?,図番２=?,未使用flg=0 WHERE ID=?',
                update_rows)
        for id_ in delete_ids:
            c.execute('DELETE FROM kouteizuban WHERE ID=?', (id_,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def db_update3(row_dict):
    backup_db(CHECKSHEET_DB)
    conn = sqlite3.connect(CHECKSHEET_DB)
    c = conn.cursor()
    try:
        cols = ['連携ID', '工程順', '工程順SUB', '図面Ver', '生産開始月']
        for n in ITEM_NUMS:
            cols += [f'チェック項目{n}', f'チェック基準{n}']
        ph = ','.join(['?'] * len(cols))
        up = ','.join(f'{col}=excluded.{col}' for col in cols if col != '連携ID')
        vals = tuple(row_dict.get(col, '') or '' for col in cols)
        c.execute(
            f'INSERT INTO zubancheck({",".join(cols)}) VALUES({ph})'
            f' ON CONFLICT(連携ID,工程順SUB,図面Ver) DO UPDATE SET {up}',
            vals)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def db_update4(rows):
    conn = sqlite3.connect(GENPINHYO_DB)
    c = conn.cursor()
    try:
        c.executemany(
            'UPDATE buhin_irepo_mst SET ireporter管理flg=?,QRコードレイアウト区分=?,縦横区分=? WHERE 部品名=?',
            [(int(r.get('ireporter管理flg') or 0),
              int(r.get('QRコードレイアウト区分') or 0),
              int(r.get('縦横区分') or 0),
              r['部品名']) for r in rows])
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def db_update5(renkeii_id, zumen_ver):
    backup_db(CHECKSHEET_DB)
    conn = sqlite3.connect(CHECKSHEET_DB)
    c = conn.cursor()
    try:
        c.execute('DELETE FROM zubancheck WHERE 連携ID=? AND 図面Ver=?', (renkeii_id, zumen_ver))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ── DB read functions ──────────────────────────────────────────────────────

def load_kouteizuban(buban='', match='前方一致', ver='', limit=None):
    try:
        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        params = []
        conds = ["(完成部番 != '' AND 完成部番 != 'なし')"]
        if buban:
            pat = (buban + '%') if match == '前方一致' else ('%' + buban + '%')
            conds.append('完成部番 LIKE ?')
            params.append(pat)
        if ver:
            conds.append('工程Ver=?')
            params.append(ver)
        where = f"WHERE {' AND '.join(conds)}"
        c.execute(f'SELECT COUNT(*) FROM kouteizuban {where}', params)
        total = c.fetchone()[0]
        sql = f'SELECT * FROM kouteizuban {where} ORDER BY 完成部番, 工程Ver, 工程順'
        if limit:
            sql += f' LIMIT {int(limit)}'
        c.execute(sql, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows, total
    except Exception as e:
        print(f'load_kouteizuban: {e}')
        return [], 0
        return []

def get_ver_options():
    try:
        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        c.execute("""SELECT 工程Ver FROM kouteizuban
                     WHERE 完成部番!='' AND 完成部番!='なし'
                     GROUP BY 工程Ver HAVING COUNT(*)>1 ORDER BY 工程Ver""")
        vers = [str(r[0]) for r in c.fetchall()]
        conn.close()
        return [''] + vers
    except:
        return ['']

def zuban_list_from_rows(rows):
    seen = set()
    result = []
    for r in rows:
        for sub, kakou_f, zuban_f in ((1, '加工機１', '図番１'), (2, '加工機２', '図番２')):
            if sub == 2 and r.get(kakou_f, 'なし') == 'なし' and r.get(zuban_f, 'なし') == 'なし':
                continue
            label = (f"{r.get(zuban_f, '')}　【{r.get('完成部番', '')}　工程：{r.get('工程', '')}　"
                     f"工程順：{r.get('工程順', '')}　加工機：{r.get(kakou_f, '')}　工程Ver：{r.get('工程Ver', '')}】")
            if label not in seen:
                seen.add(label)
                result.append({'label': label, 'ID': r.get('ID'), '完成部番': r.get('完成部番'),
                                '工程Ver': r.get('工程Ver'), '工程順': r.get('工程順'),
                                '工程': r.get('工程'), '加工機': r.get(kakou_f),
                                '図番': r.get(zuban_f), '工程順SUB': sub})
    return result

def load_zuban_list(buban='', match='前方一致', ver=''):
    try:
        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        conds = ["完成部番!='' AND 完成部番!='なし'"]
        params = []
        if buban:
            pat = (buban + '%') if match == '前方一致' else ('%' + buban + '%')
            conds.append('完成部番 LIKE ?')
            params.append(pat)
        if ver:
            conds.append('工程Ver=?')
            params.append(ver)
        where = ' AND '.join(conds)
        c.execute(f"""
            SELECT ID, 完成部番, 工程Ver, 工程順, 工程, 加工機１ as 加工機, 図番１ as 図番, 1 as 工程順SUB
            FROM kouteizuban WHERE {where}
            UNION ALL
            SELECT ID, 完成部番, 工程Ver, 工程順, 工程, 加工機２, 図番２, 2
            FROM kouteizuban WHERE {where}
              AND NOT (加工機２='なし' AND 図番２='なし')
            ORDER BY 完成部番, 工程Ver, 工程順, 工程順SUB
        """, params + params)
        raw = [dict(zip([d[0] for d in c.description], r)) for r in c.fetchall()]
        conn.close()
        seen = set()
        result = []
        for r in raw:
            label = (f"{r['図番']}　【{r['完成部番']}　工程：{r['工程']}　"
                     f"工程順：{r['工程順']}　加工機：{r['加工機']}　工程Ver：{r['工程Ver']}】")
            if label not in seen:
                seen.add(label)
                result.append({'label': label, **r})
        return result
    except Exception as e:
        print(f'load_zuban_list: {e}')
        return []

def get_available_versions(renkeii_id, koteijun_sub):
    try:
        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        c.execute(
            'SELECT 図面Ver FROM zubancheck WHERE 連携ID=? AND 工程順SUB=? ORDER BY 図面Ver',
            (renkeii_id, koteijun_sub))
        vers = [r[0] for r in c.fetchall()]
        conn.close()
        return vers
    except:
        return []

def load_zubancheck_row(renkeii_id, koteijun_sub, zumen_ver):
    try:
        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        c.execute(
            'SELECT * FROM zubancheck WHERE 連携ID=? AND 工程順SUB=? AND 図面Ver=?',
            (renkeii_id, koteijun_sub, zumen_ver))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except:
        return None

def load_buhin_irepo_mst():
    try:
        conn = _connect(GENPINHYO_DB)
        c = conn.cursor()
        c.execute('SELECT * FROM buhin_irepo_mst ORDER BY 部品名')
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f'load_buhin_irepo_mst: {e}')
        return []

# 図番の参考表示：API の項目名 → この画面の列名（M図番は不要になったので無い。2026-10-23）
KOUTEIZU_FIELDS = {
    'item': '完成部番',
    'F1': 'F1_図番', 'F2': 'F2_図番', 'B1': 'B1_図番', 'B2': 'B2_図番',
    'L': 'L_図番', 'R': 'R_図番', 'C': 'C_図番',
    'handwritten': '手書き_図番',
    'spare1': '予備_図番1', 'spare2': '予備_図番2', 'spare3': '予備_図番3', 'spare4': '予備_図番4',
}

def load_kouteizukan_filtered(buban='', match='前方一致'):
    # 業務ポータルの工程図管理から探す（KRD の DATA_KOUTEIZUKAN の代わり。2026-10-23）
    # 部番なしでは探さない（全件は6万行あり重いため。呼び出し側も部番指定時だけ呼んでいる）
    if not buban:
        return []
    try:
        api_match = 'prefix' if match == '前方一致' else 'contains'
        rows, _truncated = portal_api.search_drawings(buban, api_match)
        return [{label: (r.get(key) or '') for key, label in KOUTEIZU_FIELDS.items()} for r in rows]
    except Exception as e:
        print(f'load_kouteizukan_filtered: {e}')
        return []

def load_preview_data(buban, ver):
    try:
        conn = _connect(CHECKSHEET_DB)
        c = conn.cursor()
        check_cols = ', '.join(
            f'z.チェック項目{n}, z.チェック基準{n}' for n in ITEM_NUMS)
        c.execute(f"""
            WITH base AS (
                SELECT ID, 工程, 工程順, 加工機１ as 加工機, 図番１ as 図番, 1 as 工程順SUB
                FROM kouteizuban WHERE 完成部番=? AND 工程Ver=?
                UNION ALL
                SELECT ID, 工程, 工程順, 加工機２, 図番２, 2
                FROM kouteizuban WHERE 完成部番=? AND 工程Ver=?
                AND NOT (加工機２='なし' AND 図番２='なし')
            ), latest AS (
                SELECT z.連携ID, z.工程順SUB, MAX(z.図面Ver) as max_ver
                FROM zubancheck z JOIN base b ON z.連携ID=b.ID AND z.工程順SUB=b.工程順SUB
                GROUP BY z.連携ID, z.工程順SUB
            )
            SELECT b.工程, b.工程順, b.加工機, b.図番, b.工程順SUB,
                   z.図面Ver, z.生産開始月, {check_cols}
            FROM base b
            LEFT JOIN latest l ON b.ID=l.連携ID AND b.工程順SUB=l.工程順SUB
            LEFT JOIN zubancheck z ON z.連携ID=l.連携ID AND z.工程順SUB=l.工程順SUB AND z.図面Ver=l.max_ver
            ORDER BY b.工程順, b.工程順SUB
        """, (buban, ver, buban, ver))
        rows = [dict(zip([d[0] for d in c.description], r)) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f'load_preview_data: {e}')
        return []

# ── Data transforms ────────────────────────────────────────────────────────

def wide_to_tall(row):
    if not row:
        return [{'no': i+1, 'チェック項目': '', 'チェック基準': ''} for i in range(15)]
    return [{'no': i+1,
             'チェック項目': row.get(f'チェック項目{n}', '') or '',
             'チェック基準': row.get(f'チェック基準{n}', '') or ''}
            for i, n in enumerate(ITEM_NUMS)]

def tall_to_wide(items, meta):
    row = {k: meta[k] for k in ('連携ID', '工程順', '工程順SUB', '図面Ver', '生産開始月')}
    for i, n in enumerate(ITEM_NUMS):
        item = items[i] if i < len(items) else {}
        row[f'チェック項目{n}'] = item.get('チェック項目', '') or ''
        row[f'チェック基準{n}'] = item.get('チェック基準', '') or ''
    return row

def build_preview_display(rows):
    # チェック項目数を工程順ごとに集計（blank行挿入判定用）
    ord_check_counts = {}

    display = []
    for row in rows:
        ver = str(int(row['図面Ver'])) if row.get('図面Ver') else ''
        start_month = (row.get('生産開始月', '') or '').strip()
        if start_month == 'なし':
            start_month = ''
        ver_text = f'Ver:{ver}　{start_month}' if ver else ''
        ord_val = row['工程順']

        group_rows = []
        first = True
        for i, n in enumerate(ITEM_NUMS):
            item = (row.get(f'チェック項目{n}', '') or '').strip()
            crit = (row.get(f'チェック基準{n}', '') or '').strip()
            if item in ('', 'なし') and crit in ('', 'なし'):
                continue
            group_rows.append({
                '工程':    row['工程'] if first else '',
                '加工機':  row['加工機'] if first else '',
                '図番':    row['図番'] if first else '',
                'チェック項目': item,
                'チェック基準': crit,
                '_ord':    ord_val,
            })
            first = False

        # チェック項目数を工程順ごとに累積（サブグループ分を合算）
        ord_check_counts[ord_val] = ord_check_counts.get(ord_val, 0) + len(group_rows)

        # チェック項目がない工程も1行表示（Streamlit互換）
        if not group_rows:
            group_rows.append({
                '工程': row['工程'], '加工機': row['加工機'], '図番': row['図番'],
                'チェック項目': '', 'チェック基準': '', '_ord': ord_val,
            })
            if ver_text:
                group_rows.append({
                    '工程': '', '加工機': '', '図番': ver_text,
                    'チェック項目': '', 'チェック基準': '', '_ord': ord_val,
                })
        elif ver_text:
            if len(group_rows) >= 2:
                group_rows[1]['図番'] = ver_text
            else:
                group_rows.append({
                    '工程': '', '加工機': '', '図番': ver_text,
                    'チェック項目': '', 'チェック基準': '', '_ord': ord_val,
                })

        display.extend(group_rows)

    # セパレータ挿入：チェック項目が2行以上のグループのみblank行を追加
    result = []
    prev_ord = None
    for d in display:
        cur_ord = d['_ord']
        if prev_ord is not None and cur_ord != prev_ord:
            if ord_check_counts.get(prev_ord, 0) >= 2:
                result.append({
                    '工程': '', '加工機': '', '図番': '',
                    'チェック項目': '', 'チェック基準': '', '_ord': -1,
                })
            result.append({
                '工程': '=====', '加工機': '=============',
                '図番': '========================',
                'チェック項目': '=======================',
                'チェック基準': '===================',
                '_ord': -1,
            })
        result.append(d)
        prev_ord = cur_ord

    for i, r in enumerate(result):
        r['_id'] = i
        r['行'] = i + 1
    return result

# ── Year/month lists ───────────────────────────────────────────────────────

def _year_list():
    jst = datetime.now(timezone(timedelta(hours=9)))
    y = int(jst.strftime('%Y')) + 1
    return [''] + [str(y - i) for i in range(-1, 12)]

def _month_list():
    return ['', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

# ── Login page ─────────────────────────────────────────────────────────────

def _add_common_head():
    ui.add_head_html('<link rel="stylesheet" href="/_nicegui/3.13.0/static/fonts.css">')
    ui.add_head_html(
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap" rel="stylesheet">')
    ui.add_css('* { font-family: "Noto Sans JP", sans-serif; }')

@ui.page('/login')
def login_page():
    _add_common_head()

    with ui.card().classes('absolute-center w-96'):
        ui.label('i-Reporter チェック項目入力').classes('text-h6 font-bold w-full text-center mb-4')
        pwd = ui.input('パスワード', password=True, password_toggle_button=True).classes('w-full')
        msg = ui.label('').classes('text-red-500 text-sm')

        def do_login():
            if pwd.value == PASSWORD:
                app.storage.user['authenticated'] = True
                ui.navigate.to('/')
            else:
                msg.set_text('パスワードが違います')

        ui.button('ログイン', on_click=do_login).props('color=blue-9').classes('w-full mt-2 text-white')
        pwd.on('keydown.enter', do_login)

# ── Main page ──────────────────────────────────────────────────────────────

@ui.page('/')
def main_page():
    if not app.storage.user.get('authenticated'):
        ui.navigate.to('/login')
        return

    _add_common_head()
    ui.add_css('.q-table td { white-space: nowrap; }')
    ui.add_css('.q-tab-panel { padding-top: 6px !important; }')
    ui.add_css('.q-tab-panel h5 { margin-top: 2px !important; margin-bottom: 6px !important; }')
    ui.add_css('.q-tab-panels { background-color: #e8eef8 !important; }')
    ui.add_css('.q-tabs__arrow { display: none !important; }')
    ui.add_css('.q-table tbody tr:nth-child(even) { background-color: #f0f4ff; }')
    ui.add_css('.q-table tbody tr:nth-child(odd)  { background-color: #ffffff; }')
    ui.add_css('.preview-table .q-table tbody tr:nth-child(even) { background-color: #fffef0 !important; }')
    ui.add_css('.preview-table .q-table tbody tr:nth-child(odd)  { background-color: #ffffff !important; }')
    ui.add_css('.q-table th, .q-table td { border-right: 1px solid #d0d7e8 !important; }')
    ui.add_css('.q-table th:last-child, .q-table td:last-child { border-right: none !important; }')
    ui.add_css('.readonly-cell { background-color: #f8f8f8 !important; }')
    ui.add_css('.edit-first { border-left: 3px solid #888 !important; }')
    ui.add_css('.q-table th.edit-last, .q-table td.edit-last { border-right: 3px solid #888 !important; }')
    ui.add_css('.q-table thead th.edit-first, .q-table thead th.edit-mid, .q-table thead th.edit-last { border-top: 3px solid #888 !important; }')
    ui.add_css('.tab2-selected { background-color: #cfe2ff !important; }')
    ui.add_head_html('''
    <script>
    window.__tab2Sel = {start: null, end: null};
    window.__tab2Dragging = false;

    window.__tab2UpdateHighlight = function() {
        document.querySelectorAll('.tab2-selected').forEach(function(el){ el.classList.remove('tab2-selected'); });
        var s = window.__tab2Sel;
        if (!s.start || !s.end) return;
        var noMin = Math.min(s.start.no, s.end.no), noMax = Math.max(s.start.no, s.end.no);
        var colMin = Math.min(s.start.col, s.end.col), colMax = Math.max(s.start.col, s.end.col);
        if (noMin === noMax && colMin === colMax) return;
        for (var n = noMin; n <= noMax; n++) {
            for (var c = colMin; c <= colMax; c++) {
                var el = document.querySelector('[data-tab2-no="' + n + '"][data-tab2-col="' + c + '"]');
                if (el) el.classList.add('tab2-selected');
            }
        }
    };

    document.addEventListener('mousedown', function(ev){
        var el = ev.target.closest('[data-tab2-no]');
        if (!el) return;
        var no = parseInt(el.getAttribute('data-tab2-no'));
        var col = parseInt(el.getAttribute('data-tab2-col'));
        window.__tab2Dragging = true;
        if (ev.shiftKey && window.__tab2Sel.start) {
            window.__tab2Sel.end = {no: no, col: col};
        } else {
            window.__tab2Sel.start = {no: no, col: col};
            window.__tab2Sel.end = {no: no, col: col};
        }
        window.__tab2UpdateHighlight();
    });

    document.addEventListener('mouseover', function(ev){
        if (!window.__tab2Dragging || ev.buttons !== 1) return;
        var el = ev.target.closest('[data-tab2-no]');
        if (!el) return;
        window.__tab2Sel.end = {no: parseInt(el.getAttribute('data-tab2-no')), col: parseInt(el.getAttribute('data-tab2-col'))};
        window.__tab2UpdateHighlight();
    });

    document.addEventListener('mouseup', function(){ window.__tab2Dragging = false; });

    document.addEventListener('copy', function(ev){
        var s = window.__tab2Sel;
        if (!s.start || !s.end) return;
        var noMin = Math.min(s.start.no, s.end.no), noMax = Math.max(s.start.no, s.end.no);
        var colMin = Math.min(s.start.col, s.end.col), colMax = Math.max(s.start.col, s.end.col);
        if (noMin === noMax && colMin === colMax) return;
        var lines = [];
        for (var n = noMin; n <= noMax; n++) {
            var cells = [];
            for (var c = colMin; c <= colMax; c++) {
                var el = document.querySelector('input[data-tab2-no="' + n + '"][data-tab2-col="' + c + '"]');
                cells.push(el ? el.value : '');
            }
            lines.push(cells.join('\\t'));
        }
        var text = lines.join('\\n');
        ev.clipboardData.setData('text/plain', text);
        ev.preventDefault();
    });
    </script>
    ''')

    threading.Thread(target=db_update1, daemon=True).start()

    # ── Tab1 state ──
    tab1_rows = []
    tab1_ref_rows = []

    # ── Tab2 state ──
    tab2_state = {
        'zuban_list': [],
        'selected_label': '',
        'selected_meta': None,
        'available_vers': [],
        'zumen_ver': 1,
        'nen': '',
        'getsu': '',
        'check_rows': wide_to_tall(None),
        'delete_confirm': False,
        'buban': '',
        'kouteiver': '',
    }

    # ── Tab4 state ──
    tab4_rows = []

    # ── Header + Tabs (1行) ──
    with ui.header(elevated=True).classes('bg-blue-700 text-white items-center').style('min-height:64px; padding: 0 16px'):
        ui.label('i-Reporter チェック項目入力').classes('text-subtitle1 font-bold shrink-0 mr-4')
        with ui.tabs().classes('flex-grow') as tabs:
            t1 = ui.tab('t1', label='加工機・図番 登録')
            t2 = ui.tab('t2', label='チェックシート項目 登録')
            t3 = ui.tab('t3', label='チェックシートイメージの表示')
            t4 = ui.tab('t4', label='i-Reporter発行対象管理')
        ui.button('ログアウト', icon='logout',
                  on_click=lambda: (app.storage.user.__setitem__('authenticated', False),
                                    ui.navigate.to('/login'))).props('flat').classes('text-white shrink-0 ml-4')

    with ui.tab_panels(tabs, value=t1).classes('w-full p-4'):

        # ══════════════════════════════════════════════════════════════════
        # TAB 1: 加工機・図番 登録
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel(t1):
            ui.markdown('##### 加工機・図番　登録')

            with ui.row(align_items='center').classes('gap-2 flex-wrap w-full'):
                buban_in = ui.input('完成部番').props('dense').style('width:220px')
                match_radio = ui.radio(['前方一致', '部分一致'], value='前方一致').props('inline')
                ver_select = ui.select(get_ver_options(), value='', label='工程Ver').props('dense').style('width:120px')
                btn_search_tab1 = ui.button('検索', icon='search').props('color=primary dense')
                tab1_count = ui.label('').classes('text-sm text-gray-500')
                ui.space()
                btn_update_tab1 = ui.button('加工機・図番更新', icon='save').props('color=green dense')

            # ── Tab1 table ──
            TAB1_COLS = [
                {'name': '完成部番', 'label': '完成部番', 'field': '完成部番', 'align': 'left',   'classes': 'readonly-cell', 'headerClasses': 'readonly-cell'},
                {'name': '工程Ver', 'label': '工程Ver', 'field': '工程Ver', 'align': 'center', 'classes': 'readonly-cell', 'headerClasses': 'readonly-cell'},
                {'name': '工程順',  'label': '工程順',  'field': '工程順',  'align': 'center', 'classes': 'readonly-cell', 'headerClasses': 'readonly-cell'},
                {'name': '工程',    'label': '工程',    'field': '工程',    'align': 'left',   'classes': 'readonly-cell', 'headerClasses': 'readonly-cell'},
                {'name': '加工機１', 'label': '加工機１', 'field': '加工機１', 'align': 'left',   'headerClasses': 'edit-first'},
                {'name': '図番１',   'label': '図番１',   'field': '図番１',   'align': 'left',   'headerClasses': 'edit-mid'},
                {'name': '加工機２', 'label': '加工機２', 'field': '加工機２', 'align': 'left',   'headerClasses': 'edit-mid'},
                {'name': '図番２',   'label': '図番２',   'field': '図番２',   'align': 'left',   'headerClasses': 'edit-mid'},
                {'name': '未使用flg', 'label': '未使用', 'field': '未使用flg', 'align': 'center', 'headerClasses': 'edit-last'},
            ]
            tab1_table = ui.table(columns=TAB1_COLS, rows=[], row_key='ID', pagination=50) \
                .classes('w-full').props('dense flat bordered :rows-per-page-options="[50,100,200,0]"')

            _edit_classes = {'加工機１': 'edit-first', '図番１': 'edit-mid', '加工機２': 'edit-mid', '図番２': 'edit-mid'}
            for field, cls in _edit_classes.items():
                tab1_table.add_slot(f'body-cell-{field}', f'''
                    <q-td :props="props" class="{cls}">
                        <q-input v-model="props.row['{field}']"
                            @update:model-value="$parent.$parent.$emit('tab1_cell',
                                {{id: props.row.ID, field: '{field}', value: $event}})"
                            dense borderless style="min-width:100px" />
                    </q-td>
                ''')
            tab1_table.add_slot('body-cell-未使用flg', r'''
                <q-td :props="props" class="text-center edit-last">
                    <q-checkbox v-model="props.row['未使用flg']" :true-value="1" :false-value="0"
                        @update:model-value="$parent.$parent.$emit('tab1_cell',
                            {id: props.row.ID, field: '未使用flg', value: $event})" />
                </q-td>
            ''')

            def handle_tab1_cell(e):
                if not e.args:
                    return
                id_ = e.args.get('id')
                field = e.args.get('field')
                value = e.args.get('value')
                for row in tab1_rows:
                    if row.get('ID') == id_:
                        row[field] = value
                        break

            tab1_table.on('tab1_cell', handle_tab1_cell)

            ui.separator().classes('my-3')
            ui.markdown('###### ※参考　工程図番情報')

            TAB1_REF_COLS = [
                {'name': '完成部番', 'label': '完成部番', 'field': '完成部番'},
                {'name': 'F1_図番', 'label': 'F1_図番', 'field': 'F1_図番'},
                {'name': 'F2_図番', 'label': 'F2_図番', 'field': 'F2_図番'},
                {'name': 'B1_図番', 'label': 'B1_図番', 'field': 'B1_図番'},
                {'name': 'B2_図番', 'label': 'B2_図番', 'field': 'B2_図番'},
                {'name': 'L_図番',  'label': 'L_図番',  'field': 'L_図番'},
                {'name': 'R_図番',  'label': 'R_図番',  'field': 'R_図番'},
                {'name': 'C_図番',  'label': 'C_図番',  'field': 'C_図番'},
                # M図番は不要になったので削除。手書き・予備は参考として出す（2026-10-23）
                {'name': '手書き_図番', 'label': '手書き_図番', 'field': '手書き_図番'},
                {'name': '予備_図番1', 'label': '予備_図番1', 'field': '予備_図番1'},
                {'name': '予備_図番2', 'label': '予備_図番2', 'field': '予備_図番2'},
                {'name': '予備_図番3', 'label': '予備_図番3', 'field': '予備_図番3'},
                {'name': '予備_図番4', 'label': '予備_図番4', 'field': '予備_図番4'},
            ]
            tab1_ref_table = ui.table(columns=TAB1_REF_COLS, rows=[], row_key='完成部番') \
                .classes('w-full').props('dense flat bordered')

            # ── Functions defined after all UI ──
            async def search_tab1():
                nonlocal tab1_rows, tab1_ref_rows
                buban = buban_in.value.strip()
                match = match_radio.value
                ver = ver_select.value or ''
                btn_search_tab1.props('loading')
                try:
                    tab1_rows, total = await run.io_bound(load_kouteizuban, buban, match, ver)
                    tab1_table.rows = tab1_rows
                    tab1_table.update()
                    tab1_count.set_text(f'{total} 件')
                    # Tab2図番リストはtab1_rowsから直接生成（DB追加クエリ不要）
                    filtered = zuban_list_from_rows(tab1_rows)
                    tab2_state['zuban_list'] = filtered
                    new_labels = [''] + [z['label'] for z in filtered]
                    zuban_select.options = new_labels
                    zuban_select.set_value('')
                    zuban_select.update()
                    # 参考の工程図番は部番指定時のみ取る（部番なしだと6万行あり重い）
                    if buban:
                        tab1_ref_rows = await run.io_bound(load_kouteizukan_filtered, buban, match)
                        tab1_ref_table.rows = tab1_ref_rows
                        tab1_ref_table.update()
                finally:
                    btn_search_tab1.props(remove='loading')

            async def update_tab1():
                if not tab1_rows:
                    ui.notify('データがありません', color='warning')
                    return
                btn_update_tab1.props('loading')
                try:
                    await run.io_bound(db_update2, tab1_rows)
                    ui.notify('加工機・図番を更新しました', color='positive')
                    buban = buban_in.value.strip()
                    match = match_radio.value
                    ver = ver_select.value or ''
                    rows, total = await run.io_bound(load_kouteizuban, buban, match, ver)
                    tab1_rows.clear()
                    tab1_rows.extend(rows)
                    tab1_table.rows = tab1_rows
                    tab1_table.update()
                    tab1_count.set_text(f'{total} 件')
                    filtered = zuban_list_from_rows(tab1_rows)
                    tab2_state['zuban_list'] = filtered
                    new_labels = [''] + [z['label'] for z in filtered]
                    zuban_select.options = new_labels
                    zuban_select.set_value('')
                    zuban_select.update()
                except Exception as ex:
                    ui.notify(f'更新エラー: {ex}', color='negative')
                finally:
                    btn_update_tab1.props(remove='loading')

            btn_search_tab1.on_click(search_tab1)
            btn_update_tab1.on_click(update_tab1)

            async def _initial_load():
                nonlocal tab1_rows
                tab1_rows, total = await run.io_bound(load_kouteizuban)
                tab1_table.rows = tab1_rows
                tab1_table.update()
                tab1_count.set_text(f'{total} 件（50件ずつ表示）')
                filtered = zuban_list_from_rows(tab1_rows)
                tab2_state['zuban_list'] = filtered
                new_labels = [''] + [z['label'] for z in filtered]
                zuban_select.options = new_labels
                zuban_select.update()

            ui.timer(0.3, _initial_load, once=True)

        # ══════════════════════════════════════════════════════════════════
        # TAB 2: チェックシート項目 登録
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel(t2):
            ui.markdown('##### チェックシート項目　登録')

            tab2_state['zuban_list'] = []
            zuban_labels = ['']

            # ── Row 1: 図番選択 ──
            with ui.row(align_items='end').classes('gap-3 flex-wrap w-full justify-center'):
                zuban_select = ui.select(
                    zuban_labels,
                    value='',
                    label='図番選択',
                    with_input=True
                ).style('min-width:680px').props('dense')

            # ── Row 2: Ver/年月 + ボタン ──
            with ui.row(align_items='end').classes('gap-3 flex-wrap w-full justify-center mt-2'):
                ver_num = ui.number('図面Ver選択', value=1, min=1, max=99, step=1, precision=0) \
                    .style('width:150px').props('dense')
                ver_hint = ui.label('').classes('text-xs text-gray-500 self-center')
                nen_select   = ui.select(_year_list(),  value='', label='生産開始年').style('width:110px').props('dense')
                getsu_select = ui.select(_month_list(), value='', label='生産計画月').style('width:100px').props('dense')
                ui.separator().props('vertical')
                btn_update = ui.button('チェック項目更新', icon='save').props('color=green dense')

            # ── 15-item editable table (refreshable) ──
            tab2_check_table_ref = [None]

            @ui.refreshable
            def render_check_table():
                if not tab2_state['check_rows']:
                    tab2_state['check_rows'] = wide_to_tall(None)

                TAB2_COLS = [
                    {'name': 'no', 'label': 'No.', 'field': 'no', 'align': 'center', 'style': 'width:50px', 'classes': 'readonly-cell', 'headerClasses': 'readonly-cell'},
                    {'name': 'チェック項目', 'label': 'チェック項目', 'field': 'チェック項目', 'align': 'left', 'headerClasses': 'edit-first'},
                    {'name': 'チェック基準', 'label': 'チェック基準', 'field': 'チェック基準', 'align': 'left', 'headerClasses': 'edit-last'},
                ]
                t = ui.table(columns=TAB2_COLS, rows=tab2_state['check_rows'], row_key='no') \
                    .classes('w-1/2 self-center').props('dense flat bordered')
                tab2_check_table_ref[0] = t

                _tab2_edit = {'チェック項目': ('edit-first', 0), 'チェック基準': ('edit-last', 1)}
                for field, (cls, col) in _tab2_edit.items():
                    t.add_slot(f'body-cell-{field}', f'''
                        <q-td :props="props" class="{cls}">
                            <q-input v-model="props.row['{field}']"
                                :data-tab2-no="props.row.no"
                                data-tab2-col="{col}"
                                @update:model-value="$parent.$parent.$emit('tab2_cell',
                                    {{no: props.row.no, field: '{field}', value: $event}})"
                                @paste="(function(ev){{
                                    var text = ev.clipboardData ? ev.clipboardData.getData('text/plain') : '';
                                    if (text.indexOf('\\t') === -1 && text.indexOf('\\n') === -1 && text.indexOf('\\r') === -1) return;
                                    ev.preventDefault();
                                    $parent.$parent.$emit('tab2_paste', {{no: props.row.no, field: '{field}', text: text}});
                                }})($event)"
                                dense borderless style="min-width:250px" />
                        </q-td>
                    ''')

                def handle_tab2_cell(e):
                    if not e.args:
                        return
                    no = e.args.get('no')
                    field = e.args.get('field')
                    value = e.args.get('value')
                    for item in tab2_state['check_rows']:
                        if item.get('no') == no:
                            item[field] = value
                            break

                def handle_tab2_paste(e):
                    if not e.args:
                        return
                    start_no = e.args.get('no')
                    start_field = e.args.get('field')
                    text = e.args.get('text') or ''
                    fields = ['チェック項目', 'チェック基準']
                    start_col = fields.index(start_field)
                    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                    while lines and lines[-1] == '':
                        lines.pop()
                    rows = tab2_state['check_rows']
                    for r_off, line in enumerate(lines):
                        row_idx = start_no - 1 + r_off
                        if row_idx >= len(rows):
                            break
                        cells = line.split('\t')
                        for c_off, cell in enumerate(cells):
                            col = start_col + c_off
                            if col >= len(fields):
                                break
                            rows[row_idx][fields[col]] = cell
                    render_check_table.refresh()

                t.on('tab2_cell', handle_tab2_cell)
                t.on('tab2_paste', handle_tab2_paste)

            render_check_table()

            # ── 削除ボタン（表の下・右寄せ）──
            with ui.row().classes('w-1/2 self-center justify-end mt-1'):
                btn_delete = ui.button('チェック項目削除', icon='delete').props('color=red dense')

            del_confirm_row = ui.row().classes('gap-2 mt-1 w-full justify-center items-center')
            del_confirm_row.visible = False
            with del_confirm_row:
                ui.label('⚠️ 本当に削除しますか？').classes('text-red-600 self-center')
                btn_del_yes = ui.button('はい、削除します').props('color=red dense')
                btn_del_no  = ui.button('キャンセル').props('color=grey dense')


            def _load_tab2(meta, ver):
                row = load_zubancheck_row(meta['ID'], meta['工程順SUB'], int(ver))
                tab2_state['check_rows'] = wide_to_tall(row)
                render_check_table.refresh()
                # Fill year/month from existing row
                if row:
                    sm = row.get('生産開始月', '') or ''
                    if len(sm) >= 4:
                        nen_select.set_value(sm[0:4])
                    if len(sm) >= 7:
                        getsu_select.set_value(sm[5:7])

            def on_zuban_change(e):
                tab2_state['selected_label'] = e.value or ''
                tab2_state['delete_confirm'] = False
                del_confirm_row.visible = False
                if not e.value:
                    tab2_state['selected_meta'] = None
                    tab2_state['check_rows'] = wide_to_tall(None)
                    ver_hint.set_text('')
                    render_check_table.refresh()
                    render_preview.refresh()
                    return
                meta = next((z for z in tab2_state['zuban_list'] if z['label'] == e.value), None)
                tab2_state['selected_meta'] = meta
                if not meta:
                    return
                vers = get_available_versions(meta['ID'], meta['工程順SUB'])
                tab2_state['available_vers'] = vers
                latest = vers[-1] if vers else 1
                tab2_state['zumen_ver'] = latest
                ver_num.set_value(latest)
                ver_hint.set_text(f'※最新: {latest}' if vers else '※未登録')
                tab2_state['buban']     = meta['完成部番']
                tab2_state['kouteiver'] = meta['工程Ver']
                _load_tab2(meta, latest)
                render_preview.refresh()

            def on_ver_change(e):
                meta = tab2_state['selected_meta']
                if not meta:
                    return
                tab2_state['zumen_ver'] = int(e.value or 1)
                tab2_state['delete_confirm'] = False
                del_confirm_row.visible = False
                _load_tab2(meta, tab2_state['zumen_ver'])

            zuban_select.on_value_change(on_zuban_change)
            ver_num.on_value_change(on_ver_change)

            async def do_update():
                meta = tab2_state['selected_meta']
                if not meta:
                    ui.notify('図番を選択してください', color='warning')
                    return
                nen  = nen_select.value or ''
                getsu = getsu_select.value or ''
                if not nen or not getsu:
                    ui.notify('図面適用生産開始年と月は必須です', color='warning')
                    return
                nengetsu = f'{nen}年{getsu}月より'
                wide = tall_to_wide(
                    tab2_state['check_rows'],
                    {'連携ID':   meta['ID'],
                     '工程順':   meta['工程順'],
                     '工程順SUB': meta['工程順SUB'],
                     '図面Ver':  tab2_state['zumen_ver'],
                     '生産開始月': nengetsu})
                try:
                    db_update3(wide)
                    ui.notify('チェック項目を更新しました', color='positive')
                    vers = get_available_versions(meta['ID'], meta['工程順SUB'])
                    tab2_state['available_vers'] = vers
                    latest = vers[-1] if vers else tab2_state['zumen_ver']
                    ver_hint.set_text(f'※最新: {latest}')
                    render_preview.refresh()
                except Exception as ex:
                    ui.notify(f'更新エラー: {ex}', color='negative')

            async def do_delete_confirm():
                meta = tab2_state['selected_meta']
                if not meta:
                    ui.notify('図番を選択してください', color='warning')
                    return
                vers = get_available_versions(meta['ID'], meta['工程順SUB'])
                if tab2_state['zumen_ver'] not in vers:
                    ui.notify('削除対象の図面Verが存在しません', color='warning')
                    return
                tab2_state['delete_confirm'] = True
                del_confirm_row.visible = True

            async def do_delete_execute():
                meta = tab2_state['selected_meta']
                try:
                    db_update5(meta['ID'], tab2_state['zumen_ver'])
                    del_confirm_row.visible = False
                    tab2_state['delete_confirm'] = False
                    vers = get_available_versions(meta['ID'], meta['工程順SUB'])
                    tab2_state['available_vers'] = vers
                    latest = vers[-1] if vers else 1
                    tab2_state['zumen_ver'] = latest
                    ver_num.set_value(latest)
                    ver_hint.set_text(f'※最新: {latest}' if vers else '※未登録')
                    _load_tab2(meta, latest)
                    render_preview.refresh()
                    ui.notify('削除しました', color='positive')
                except Exception as ex:
                    ui.notify(f'削除エラー: {ex}', color='negative')

            def cancel_delete():
                del_confirm_row.visible = False
                tab2_state['delete_confirm'] = False

            btn_update.on_click(do_update)
            btn_delete.on_click(do_delete_confirm)
            btn_del_yes.on_click(do_delete_execute)
            btn_del_no.on_click(cancel_delete)

        # ══════════════════════════════════════════════════════════════════
        # TAB 3: チェックシートイメージの表示
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel(t3):
            ui.markdown('##### チェックシートイメージの表示')
            preview_label = ui.label('').classes('text-sm text-gray-600 mb-2')

            PREVIEW_COLS = [
                {'name': '行',         'label': '行',         'field': '行',         'align': 'right', 'style': 'width:40px'},
                {'name': '工程',       'label': '工程',       'field': '工程',       'align': 'left'},
                {'name': '加工機',     'label': '加工機',     'field': '加工機',     'align': 'left'},
                {'name': '図番',       'label': '図番',       'field': '図番',       'align': 'left'},
                {'name': 'チェック項目', 'label': 'チェック項目', 'field': 'チェック項目', 'align': 'left'},
                {'name': 'チェック基準', 'label': 'チェック基準', 'field': 'チェック基準', 'align': 'left'},
            ]

            @ui.refreshable
            def render_preview():
                buban = tab2_state.get('buban', '')
                ver   = tab2_state.get('kouteiver', '')
                if not buban or not ver:
                    preview_label.set_text('「チェックシート項目 登録」タブで図番を選択してください')
                    ui.table(columns=PREVIEW_COLS, rows=[], row_key='_id') \
                        .classes('w-full preview-table').props('dense flat bordered')
                    return
                preview_label.set_text(f'部番：{buban}　工程Ver：{ver}　※図面Verは最新のものが表示されます')
                raw = load_preview_data(buban, ver)
                disp = build_preview_display(raw)
                ui.table(columns=PREVIEW_COLS, rows=disp, row_key='_id') \
                    .classes('w-full preview-table').props('dense flat bordered')

            render_preview()

        # ══════════════════════════════════════════════════════════════════
        # TAB 4: i-Reporter発行対象管理
        # ══════════════════════════════════════════════════════════════════
        with ui.tab_panel(t4):
            ui.markdown('##### i-Reporter 発行対象管理')
            ui.markdown(
                'i-Reporterでチェックを行う部品は「ireporter管理flg」に **1** を入力してください。'
                '紙の場合は **0** です。')

            TAB4_COLS = [
                {'name': '部品名', 'label': '部品名', 'field': '部品名', 'align': 'left', 'classes': 'readonly-cell', 'headerClasses': 'readonly-cell'},
                {'name': 'ireporter管理flg',      'label': 'i-Reporter管理flg',    'field': 'ireporter管理flg',      'align': 'center'},
                {'name': 'QRコードレイアウト区分', 'label': 'QRコードレイアウト区分', 'field': 'QRコードレイアウト区分', 'align': 'center'},
                {'name': '縦横区分',              'label': '縦横区分',              'field': '縦横区分',              'align': 'center'},
            ]

            tab4_rows = load_buhin_irepo_mst()
            tab4_table = ui.table(columns=TAB4_COLS, rows=tab4_rows, row_key='部品名') \
                .classes('w-full').props('dense flat bordered')

            for field in ('ireporter管理flg', 'QRコードレイアウト区分', '縦横区分'):
                tab4_table.add_slot(f'body-cell-{field}', f'''
                    <q-td :props="props" class="text-center">
                        <q-input v-model.number="props.row['{field}']"
                            @update:model-value="$parent.$parent.$emit('tab4_cell',
                                {{buhin: props.row['部品名'], field: '{field}', value: $event}})"
                            type="number" min="0" max="9" dense borderless
                            style="width:60px;text-align:center" />
                    </q-td>
                ''')

            def handle_tab4_cell(e):
                if not e.args:
                    return
                buhin = e.args.get('buhin')
                field = e.args.get('field')
                value = e.args.get('value')
                for row in tab4_rows:
                    if row.get('部品名') == buhin:
                        row[field] = value
                        break

            tab4_table.on('tab4_cell', handle_tab4_cell)

            async def update_tab4():
                try:
                    db_update4(tab4_rows)
                    ui.notify('更新しました', color='positive')
                except Exception as ex:
                    ui.notify(f'更新エラー: {ex}', color='negative')

            ui.button('項目更新', icon='save', on_click=update_tab4).props('color=green dense').classes('mt-2')


# ── Entry point ────────────────────────────────────────────────────────────
ui.run(
    port=PORT,
    title='i-Reporterチェック項目入力',
    favicon='📋',
    storage_secret='check_input_2024',
    reload=False,
    show=False,
)
