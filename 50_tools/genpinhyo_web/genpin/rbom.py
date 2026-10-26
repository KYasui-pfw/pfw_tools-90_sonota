"""rBOM を FastAPI（http://pfw-api の /query）経由で読む。書き込みはしない。

いまは CHANGE GEAR BOX（時限処理・2026-05-26 追加）のためだけに使っている。
⚠ 以前は Oracle に直接つないでいた（パスワードがコードに書かれていた）。
  2026-10 の作り直しで、ほかのツールと同じ FastAPI 経由に変えた。
"""

import json
import urllib.error
import urllib.request

from . import config

# /query の1回の上限件数。IN 句は最大1000個（Oracle の制限）なので、製番は分けて送る。
_QUERY_LIMIT = 10000
_IN_CHUNK = 900


class RbomApiError(Exception):
    """rBOM（FastAPI）の呼び出しに失敗した。"""


def query(table, columns, where):
    """FastAPI の /query で1つのテーブルを読み、行の辞書のリストを返す。"""
    payload = {"table": table, "columns": columns, "where": where, "limit": _QUERY_LIMIT}
    request = urllib.request.Request(
        config.RBOM_API_BASE.rstrip("/") + "/query",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-KEY": config.RBOM_API_KEY},
    )
    try:
        with urllib.request.urlopen(request, timeout=config.RBOM_API_TIMEOUT_SEC) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise RbomApiError(f"rBOM（{table}）を読めませんでした: {error}") from error

    rows = body.get("rows", [])
    if len(rows) >= _QUERY_LIMIT:
        # 上限に届いた＝取りこぼしがある。黙って続けない。
        raise RbomApiError(f"rBOM（{table}）の件数が上限 {_QUERY_LIMIT} 件に届きました")
    return rows


def fetch_change_gear_boxes():
    """CHANGE GEAR BOX の引当（D3520）に、製番台帳（D3010）の日付と月次を付けて返す。

    戻り値: 辞書のリスト。キーは SEINO / HMCD / ALCQTY / TDPLNDT / SPPLDT / ASPLDT / GETSUJI。
            製番台帳に無い製番は SPPLDT・ASPLDT・GETSUJI が None。
            日付は FastAPI が返す ISO 形式の文字列（例 '2026-03-12T00:00:00'）のまま。
    """
    allocations = query(
        "D3520",
        ["SEINO", "HMCD", "ALCQTY", "TDPLNDT"],
        {"HMNM": {"eq": "CHANGE GEAR BOX"}},
    )

    seinos = sorted({row["SEINO"] for row in allocations if row.get("SEINO")})
    ledger = {}
    for start in range(0, len(seinos), _IN_CHUNK):
        chunk = seinos[start:start + _IN_CHUNK]
        for row in query("D3010", ["SEINO", "SPPLDT", "ASPLDT", "GETSUJI"], {"SEINO": {"in": chunk}}):
            ledger[row["SEINO"]] = row

    result = []
    for row in allocations:
        merged = dict(row)
        info = ledger.get(row.get("SEINO"), {})
        for key in ("SPPLDT", "ASPLDT", "GETSUJI"):
            merged[key] = info.get(key)
        result.append(merged)
    return result
