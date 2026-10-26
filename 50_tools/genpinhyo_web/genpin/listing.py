"""現品票の一覧（画面に出す表）を組み立てる。DB と i-Reporter を読むだけで、書き込みはしない。"""

import pandas as pd

from . import config, db, irepo, update

# 一覧の帳票発行IDが 0 ＝ i-Reporter の帳票がまだ無い。
NO_REPORT = 0


def to_version(values):
    """工程VERSION を整数にそろえる（昔の行には '1.0' や空欄が混ざっている。空欄は 0）。"""
    return pd.to_numeric(values, errors="coerce").fillna(0).astype(int)


def read_genpinhyo(month_prefix):
    """genpinhyo から、月次が month_prefix（'YYYYMM'）で始まるロットを読む。

    ⚠ excluded_lots（払出先で全行が除外になったロット）は読まない。
    """
    conn = db.connect()
    try:
        db.ensure_schema(conn)
        return pd.read_sql(
            "SELECT * FROM genpinhyo WHERE 月次 LIKE ?"
            " AND ロット番号 NOT IN (SELECT ロット番号 FROM excluded_lots)",
            conn,
            params=[month_prefix + "%"],
        )
    finally:
        conn.close()


def read_table(table):
    """genpinhyo.db のテーブルを丸ごと読む（buhin_irepo_mst・delete_mst など小さいもの用）。"""
    conn = db.connect()
    try:
        db.ensure_schema(conn)
        return pd.read_sql(f"SELECT * FROM {table}", conn)
    finally:
        conn.close()


def attach_report_ids(df, reports=None):
    """各ロットに、i-Reporter で発行済みの帳票の ID（帳票発行ID）を付ける。

    帳票が無いロットは 0。帳票を作り直したロットは、いちばん新しい（大きい）ID を使う。
    """
    if reports is None:
        reports = irepo.fetch_report_ids()
    latest = reports.groupby("ロット番号", as_index=False)["帳票発行ID"].max()
    df = df.merge(latest, on="ロット番号", how="left")
    df["帳票発行ID"] = pd.to_numeric(df["帳票発行ID"], errors="coerce").fillna(NO_REPORT).astype(int)
    return df


def build_tag_list(genpinhyo_df, parts_df, delete_df, reports_df):
    """一覧の表を作る（読み込みと分けてあるのは、テストで中身を差し替えやすくするため）。

    ・部品名ごとの設定（buhin_irepo_mst）を付ける
    ・削除フラグが 1 のロットを外す（CH始まり＝CHANGE GEAR BOX はフラグが無くても出す）
    ・組立番号が A＋数字8桁のロットを外す
    ・帳票発行IDを付ける
    """
    df = genpinhyo_df.merge(parts_df, on="部品名", how="left")

    df = df.merge(delete_df, on="ロット番号", how="left")
    is_change_gear_box = df["ロット番号"].str.startswith("CH", na=False)
    df.loc[is_change_gear_box & df["削除flg"].isna(), "削除flg"] = 0
    df = df[df["削除flg"] == 0].drop(columns=["削除flg"])

    df["組立番号"] = df["組立番号"].fillna("").astype(str).str.strip()
    df = df[~df["組立番号"].str.match(update.STOCK_ASSY_PATTERN.pattern)]

    df = attach_report_ids(df, reports_df)

    # 工程VERSION は昔の行に '1.0' や空欄が混ざっているので、整数にそろえる（空欄は 0）。
    df["工程VERSION"] = to_version(df["工程VERSION"])
    # 部品名ごとの設定が無い（buhin_irepo_mst に無い）部品は空欄のまま。
    for column in ("ireporter管理flg", "QRコードレイアウト区分", "縦横区分"):
        df[column] = df[column].map(lambda value: "" if pd.isna(value) else int(value))
    return df.fillna("").reset_index(drop=True)


def load_tag_list(month_prefix):
    """画面の一覧（月次が month_prefix で始まるロット）。"""
    return build_tag_list(
        read_genpinhyo(month_prefix),
        read_table("buhin_irepo_mst"),
        read_table("delete_mst"),
        irepo.fetch_report_ids(),
    )


def load_tag_list_for_window(months=update.DELETE_CHECK_MONTHS):
    """当月から months か月ぶんの一覧（夜間処理で i-Reporter の帳票を作る対象を探す用）。"""
    today = config.now()
    frames = [load_tag_list(prefix) for prefix in update.delete_check_prefixes(today)[:months]]
    return pd.concat(frames, ignore_index=True)


def needs_report(df):
    """i-Reporter の帳票をまだ作っていない行だけを返す。

    条件: i-Reporter 管理の部品（ireporter管理flg=1）で、QR が i-Reporter 用（QRコードレイアウト区分=0）で、
          帳票がまだ無い（帳票発行ID=0）。
    """
    return df[
        (df["ireporter管理flg"] == 1)
        & (df["QRコードレイアウト区分"] == 0)
        & (df["帳票発行ID"] == NO_REPORT)
    ]
