"""
M0820（事業部別品目マスタ）・M0840（品目工程マスタ）から SUPCD='L' の最新データを抽出し、
旧ファイル/ の Excel と同じレイアウトで出力する。

- 抽出・列定義・略称(M0710.HTRRNM)の差し込み・連番は 10_tancd/02_extract_xlsx.py を流用
- 品目コードの右隣に品目名（M0810.HMNM）を追加（ひな形には無い列なので B列に挿入し、列幅・非表示・枠固定を1列ずらす）
- 見出し・列幅・非表示列・ウィンドウ枠・黄色セル・罫線は 旧ファイル/ の xlsx をひな形にして引き継ぐ
  （ひな形のデータ行を消して、最新データを同じ書式で流し込む）

実行: $PYTHON 01_extract_xlsx.py
出力: 事業部別品目マスタ.xlsx / 品目工程マスタ.xlsx
"""

import importlib.util
import warnings
from copy import copy
from pathlib import Path

import openpyxl

BASE = Path(__file__).parent
TEMPLATE_DIR = BASE / "旧ファイル"

# 既存の抽出ロジックを読み込む（ファイル名が数字始まりなので importlib で読む）
_spec = importlib.util.spec_from_file_location(
    "extract_xlsx", BASE.parent / "10_tancd" / "02_extract_xlsx.py"
)
ext = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ext)


ITEM_NAME_HEADER = "品目名"
ITEM_NAME_WIDTH = 40  # 品目名列の幅（新規挿入列のためひな形に幅の定義がない）
IN_CHUNK = 500  # WHERE IN の1回あたりの件数（Oracle の IN 句上限1000に対する余裕）


def load_item_names(rows: list[dict]) -> dict[str, str]:
    """M0810（品目マスタ）から、対象行の HMCD に対応する {品目コード: 品目名(HMNM)} を作る。"""
    hmcds = sorted({r["HMCD"] for r in rows if r.get("HMCD")})
    names: dict[str, str] = {}
    for i in range(0, len(hmcds), IN_CHUNK):
        chunk = hmcds[i : i + IN_CHUNK]
        for r in ext.fetch_all("M0810", {"HMCD": {"in": chunk}}, ["HMCD"]):
            names[r["HMCD"]] = r.get("HMNM") or ""
    return names


def build_rows(
    rows: list[dict],
    columns: list[tuple[str, str]],
    vendor_names: dict[str, str],
    item_names: dict[str, str],
) -> list[list]:
    """1行分の値リストを作る（HMCD の右隣に品目名、SRCD の右隣に略称、末尾に連番）。"""
    out = []
    for number, row in enumerate(rows, start=1):
        values = []
        for physical_name, _ in columns:
            values.append(ext.to_cell_value(row.get(physical_name)))
            if physical_name == "HMCD":
                hmcd = row.get("HMCD")
                values.append(item_names.get(hmcd, "") if hmcd else "")
            if physical_name == "SRCD":
                srcd = row.get("SRCD")
                values.append(vendor_names.get(srcd, "") if srcd else "")
        values.append(number)
        out.append(values)
    return out


def write_with_template(filename: str, data: list[list]) -> None:
    """ひな形の書式を引き継いで、データ行だけ最新に差し替えて保存する。"""
    warnings.filterwarnings("ignore")  # ひな形のヘッダー/フッター解析警告を抑止
    wb = openpyxl.load_workbook(TEMPLATE_DIR / filename)
    ws = wb.active
    ncol_tpl = ws.max_column
    old_last = ws.max_row

    # 書式見本: 先頭データ行 / 途中の行 / 最終行（最終行だけ下罫線が太い）
    # 品目名列（B列）はひな形に無いので、品目コード（A列）の書式を複製して差し込む
    def sample(row: int) -> list:
        styles = [copy(ws.cell(row, c)._style) for c in range(1, ncol_tpl + 1)]
        styles.insert(1, copy(styles[0]))
        return styles

    first_style = sample(2)
    mid_style = sample(3)
    last_style = sample(old_last)
    last_height = ws.row_dimensions[old_last].height

    # 列幅・非表示は列位置に紐づくので、B列挿入前に1列ずつに展開しておく
    # （ひな形は H:I のように複数列をまとめて定義している）
    col_dims = {}
    for dim in ws.column_dimensions.values():
        for idx in range(dim.min, (dim.max or dim.min) + 1):
            col_dims[idx] = (dim.width, dim.hidden)
    freeze = ws.freeze_panes

    ws.delete_rows(2, old_last)
    for r in list(ws.row_dimensions):
        if r >= 2:
            del ws.row_dimensions[r]

    # B列に「品目名」を挿入（見出し行はこの時点で1行だけなので軽い）
    ws.insert_cols(2)
    ws.cell(1, 2, ITEM_NAME_HEADER)._style = copy(ws.cell(1, 1)._style)
    ncol = ws.max_column
    assert ncol == ncol_tpl + 1, f"列数が想定と違う: ひな形{ncol_tpl} → {ncol}"

    # 列幅・非表示を1列ずつ右にずらして設定し直す（新しいB列は幅固定・表示）
    for key in list(ws.column_dimensions):
        del ws.column_dimensions[key]
    for idx in range(1, ncol + 1):
        letter = openpyxl.utils.get_column_letter(idx)
        if idx == 2:
            ws.column_dimensions[letter].width = ITEM_NAME_WIDTH
            continue
        width, hidden = col_dims.get(idx if idx < 2 else idx - 1, (None, False))
        if width:
            ws.column_dimensions[letter].width = width
        ws.column_dimensions[letter].hidden = bool(hidden)

    # ウィンドウ枠（G2 → H2 のように1列右へ）
    if freeze:
        cell = ws[freeze]
        ws.freeze_panes = ws.cell(cell.row, cell.column + 1).coordinate

    n = len(data)
    for i, values in enumerate(data):
        assert len(values) == ncol, f"データ列数({len(values)})とひな形の列数({ncol})が不一致"
        r = i + 2
        styles = first_style if i == 0 else (last_style if i == n - 1 else mid_style)
        for c, v in enumerate(values, start=1):
            cell = ws.cell(r, c, v)
            cell._style = copy(styles[c - 1])
    if last_height:
        ws.row_dimensions[n + 1].height = last_height

    if ws.auto_filter.ref:
        ws.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(ncol)}{n + 1}"

    wb.save(BASE / filename)
    print(f"  出力: {BASE / filename}（{n}件 / {ncol}列）")


def main() -> None:
    where = {"SUPCD": {"eq": ext.TARGET_SUPCD}}
    vendor_names = ext.load_vendor_names()

    print(f"M0820（事業部別品目マスタ）SUPCD='{ext.TARGET_SUPCD}' を抽出中...")
    rows = ext.fetch_all("M0820", where, ["HMCD", "KNRBUCD"])
    item_names = load_item_names(rows)
    write_with_template("事業部別品目マスタ.xlsx", build_rows(rows, ext.M0820_COLUMNS, vendor_names, item_names))

    print(f"M0840（品目工程マスタ）SUPCD='{ext.TARGET_SUPCD}' を抽出中...")
    rows = ext.fetch_all("M0840", where, ["HMCD", "SEQ"])
    item_names = load_item_names(rows)
    write_with_template("品目工程マスタ.xlsx", build_rows(rows, ext.M0840_COLUMNS, vendor_names, item_names))


if __name__ == "__main__":
    main()
