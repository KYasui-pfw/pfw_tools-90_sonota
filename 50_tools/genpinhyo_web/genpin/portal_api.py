"""業務ポータル（Django）の読み取りAPIを呼ぶ。

    加工伝票の一覧＋VER・工程・メッキ  fetch_denpyo           GET  /machining-schedule/api/genpinhyo/denpyo/
    ロットごとの VER・工程・メッキ      fetch_lots             POST /machining-schedule/api/genpinhyo/lots/
    工程文字列                          fetch_process_strings  GET  /machining-schedule/api/genpinhyo/process-strings/
    品目工程マスタ＋加工機名            fetch_process_master   GET  /machining-schedule/api/genpinhyo/process-master/
    図番                                fetch_drawings         POST /kouteizu/api/genpinhyo/drawings/
    図番の検索                          search_drawings        GET  /kouteizu/api/genpinhyo/drawings/

・ログインも API キーも不要（読み取り専用）。
・⚠ 標準ライブラリだけで書く。check_input（NiceGUI）は pandas の無い venv で動いていて、ここを import するため。
・失敗したら PortalApiError を投げる。呼び出し側は「空のデータで上書きしない」こと。
・API の仕様は Django 側の apps/machining_schedule/Document/仕様書.md「現品票システム向けAPI」。
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from . import config

# 図番：API の項目名 → genpinhyo の列名。
# 印字・QR に使うのは先頭の7つだけ。手書き（末尾が @ の図番）と予備（7つの枠からあふれた図番）は保存と参考表示のみ。
DRAWING_COLUMNS = {
    "B1": "B1図番",
    "B2": "B2図番",
    "F1": "F1図番",
    "F2": "F2図番",
    "L": "L図番",
    "R": "R図番",
    "C": "C図番",
    "handwritten": "手書き図番",
    "spare1": "予備図番1",
    "spare2": "予備図番2",
    "spare3": "予備図番3",
    "spare4": "予備図番4",
}


class PortalApiError(Exception):
    """業務ポータルの API 呼び出しに失敗した。"""


def _request(path, params=None, payload=None):
    """API を呼んで、返ってきた JSON（辞書）を返す。payload があれば POST、無ければ GET。"""
    url = config.PORTAL_API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    if payload is None:
        request = urllib.request.Request(url, method="GET")
    else:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )

    try:
        with urllib.request.urlopen(request, timeout=config.PORTAL_API_TIMEOUT_SEC) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        # API が返したエラー文があれば添える。
        detail = ""
        try:
            detail = json.loads(error.read().decode("utf-8")).get("error", "")
        except Exception:
            pass
        raise PortalApiError(f"{path} が HTTP {error.code} を返しました {detail}".strip()) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise PortalApiError(f"{path} に接続できませんでした: {error}") from error

    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        raise PortalApiError(f"{path} の返答が JSON として読めません") from error


def fetch_denpyo():
    """加工伝票の一覧（伝票単位・払出先で絞る前）に VER・工程文字列・メッキを付けて取る。

    戻り値: 辞書のリスト。キーは denpyo_no / getsuji / hmcd / part_name / required_qty / seino /
            assy_no / srcd / model_name / inch / gauge / customer_cd / customer_name / skdk /
            seiban_kbn / assy_start / konpo_start / due_date / is_mckr_copy /
            version / version_source / process_str / is_plating
    ⚠ 0件のときは API が 503 を返す＝PortalApiError になる（一覧から消えた伝票を
      削除扱いにする処理があるので、空の一覧で進めてはいけない）。
    """
    rows = _request("/machining-schedule/api/genpinhyo/denpyo/")["rows"]
    if not rows:
        raise PortalApiError("加工伝票が0件でした")
    return rows


def fetch_lots(lots):
    """ロットごとの VER・工程文字列・メッキを取る（加工伝票に無いロット＝CHANGE GEAR BOX 用）。

    lots: [(ロット番号, 品目CD), ...]
          ⚠ 品目CDは **rBOM の品目CDのまま（変換前）**。加工伝票の「加工部番」は変換済みなので、
            それを送ると API 側でもう一度変換されて引けなくなる（加工伝票は fetch_denpyo を使う）。
    戻り値: [{"lot_no", "hmcd", "setu_f", "version", "version_source", "process_str", "is_plating"}, ...]
            送った順・送った件数どおり。
    """
    payload = {"lots": [{"lot_no": str(lot_no), "hmcd": str(hmcd)} for lot_no, hmcd in lots]}
    if not payload["lots"]:
        return []
    return _request("/machining-schedule/api/genpinhyo/lots/", payload=payload)["rows"]


def fetch_process_strings(item=""):
    """品目CD×VER ごとの工程文字列を取る。

    item: 品目CD（変換後の形＝現品票に印字している完成部番。省略すると全件）
    戻り値: [{"final_item_code", "version", "process_str"}, ...]
    """
    params = {"item": item} if item else None
    return _request("/machining-schedule/api/genpinhyo/process-strings/", params=params)["rows"]


def fetch_process_master():
    """品目工程マスタ＋加工機名を全件取る。

    戻り値: [{"final_item_code", "version", "process_order", "process_code", "res_code1", "res_name1"}, ...]
    ⚠ 0件のときは API が 503 を返す＝PortalApiError になる（空の一覧で全削除しないため）。
    """
    rows = _request("/machining-schedule/api/genpinhyo/process-master/")["rows"]
    if not rows:
        raise PortalApiError("品目工程マスタが0件でした")
    return rows


def fetch_drawings(items):
    """加工部番のリストから図番を取る。

    items: 加工部番のリスト
    戻り値: [{"item", "matched_by", "B1", ..., "C", "handwritten", "spare1".."spare4"}, ...]
            送った順・送った件数どおり。見つからない品目は matched_by="none"・図番は全部空。
    """
    items = [str(item) for item in items]
    if not items:
        return []
    return _request("/kouteizu/api/genpinhyo/drawings/", payload={"items": items})["rows"]


def search_drawings(q, match="prefix"):
    """品目CDの一部で図番を探す（チェック項目入力の部番検索用）。

    match: "prefix"（前方一致）か "contains"（部分一致）
    戻り値: (rows, truncated)。rows の形は fetch_drawings と同じ。truncated は1,000件で打ち切ったか。
    """
    result = _request("/kouteizu/api/genpinhyo/drawings/", params={"q": q, "match": match})
    return result["rows"], result.get("truncated", False)
