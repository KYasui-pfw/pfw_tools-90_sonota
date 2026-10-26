"""i-Reporter の PostgreSQL（ESRV10/irepodb）を読む。書き込みはしない。

    客先マスタ         fetch_customers
    発行済みの帳票     fetch_report_ids
    帳票定義の最新ID   fetch_latest_def_top_ids
"""

import pandas as pd
from sqlalchemy import create_engine

from . import config

# 帳票定義の元番号（view_def_top.def_top_org）。
# 現品票のチェックシートは「縦レイアウト＝405」「横レイアウト＝406」の2種類。
DEF_TOP_ORG_TATE = 405
DEF_TOP_ORG_YOKO = 406

_engine = None


def _get_engine():
    """接続の元（エンジン）を1つだけ作って使い回す。毎回作ると接続が増えて遅くなる。"""
    global _engine
    if _engine is None:
        _engine = create_engine(config.IREPORTER_DB_URL, pool_pre_ping=True)
    return _engine


def read_sql(sql):
    """SQL を実行して DataFrame で返す。"""
    with _get_engine().connect() as connection:
        return pd.read_sql(sql, connection)


def fetch_customers():
    """客先マスタ（客先コード・客先名・国名）。"""
    return read_sql(
        "SELECT record_key AS 客先コード, value AS 客先名, field0001 AS 国名"
        " FROM view_mst_custom_record WHERE master_key = 'M_CUSTOMER'"
    )


def fetch_report_ids():
    """発行済みの帳票（帳票発行ID とロット番号）。縦・横の両方をまとめて返す。

    戻り値の列: 帳票発行ID（rep_top_id）・ロット番号（cluster_1_2_t＝帳票の1ページ目のロット番号欄）
    ⚠ 同じロットで帳票を作り直していると、1ロットに複数行ある。
    """
    yoko = read_sql("SELECT rep_top_id, cluster_1_2_t FROM view_report_406")
    tate = read_sql("SELECT rep_top_id, cluster_1_2_t FROM view_report_405")
    reports = pd.concat([yoko, tate], ignore_index=True)
    return reports.rename(columns={"rep_top_id": "帳票発行ID", "cluster_1_2_t": "ロット番号"})


def fetch_latest_def_top_ids():
    """公開中の帳票定義のうち、縦・横それぞれいちばん新しい ID を返す。

    戻り値: {405: 縦の ID, 406: 横の ID}
    """
    result = {}
    for org in (DEF_TOP_ORG_TATE, DEF_TOP_ORG_YOKO):
        df = read_sql(
            "SELECT def_top_id FROM view_def_top"
            f" WHERE def_top_org = {org} AND public_status = 2"
        )
        result[org] = df["def_top_id"].max()
    return result
