"""
t_prs_job_cd_bom テーブル出力スクリプト（HMBUNCD=6版）
AWS RDS SQL Server (chohyo DB) からデータを取得
rBOM API M0810マスタとcomp_item_cdで紐づけ、HMBUNCD=6のデータを抽出
"""
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import os
import httpx

# rBOM API設定
API_BASE_URL = "http://pfw-api"
QUERY_ENDPOINT = "/query"
READ_API_KEY = "oG5^Ls%#20yq"


def fetch_data(table: str, columns: list[str], where: dict = None, limit: int = 10000, offset: int = 0) -> dict:
    """汎用データ取得関数"""
    headers = {"X-API-KEY": READ_API_KEY, "Content-Type": "application/json"}

    request_body = {
        "table": table,
        "columns": columns,
        "limit": limit,
        "offset": offset
    }
    if where:
        request_body["where"] = where

    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            f"{API_BASE_URL}{QUERY_ENDPOINT}",
            headers=headers,
            json=request_body
        )
        response.raise_for_status()
        return response.json()


def fetch_all_data(table: str, columns: list[str], where: dict = None) -> list[dict]:
    """全データをページネーションで取得"""
    all_rows = []
    offset = 0
    limit = 10000

    print(f"{table}テーブルからデータを取得中...")

    while True:
        print(f"  取得中: offset={offset}, limit={limit}")
        result = fetch_data(table, columns, where, limit, offset)
        rows = result.get("rows", [])

        if not rows:
            break

        all_rows.extend(rows)
        print(f"  取得済み: {len(all_rows)}件")

        if len(rows) < limit:
            break

        offset += limit

    print(f"データ取得完了: 合計 {len(all_rows)}件")
    return all_rows


def get_hmbuncd6_hmcd_dict() -> dict:
    """M0810からHMBUNCD='6'の品目コード(HMCD)とHMBUNCDの辞書を取得"""
    print("\n===== M0810品目マスタからHMBUNCD=6の品目を取得 =====")

    rows = fetch_all_data(
        table="M0810",
        columns=["HMCD", "HMBUNCD"],
        where={"HMBUNCD": "6"}
    )

    hmcd_dict = {row["HMCD"]: row.get("HMBUNCD", "") for row in rows if row.get("HMCD")}
    print(f"HMBUNCD=6の品目数: {len(hmcd_dict)}件")
    return hmcd_dict


def get_m0840_data() -> dict:
    """M0840からHMCD, KTSEQ, KTCDを取得し、HMCDをキーにした辞書を返す"""
    print("\n===== M0840品目工程マスタからデータを取得 =====")

    rows = fetch_all_data(
        table="M0840",
        columns=["HMCD", "KTSEQ", "KTCD"]
    )

    # HMCDをキーにした辞書（複数行ある場合は最初の1行のみ使用）
    m0840_dict = {}
    for row in rows:
        hmcd = row.get("HMCD")
        if hmcd and hmcd not in m0840_dict:
            m0840_dict[hmcd] = {
                "KTSEQ": row.get("KTSEQ", ""),
                "KTCD": row.get("KTCD", "")
            }

    print(f"M0840ユニーク品目数: {len(m0840_dict)}件")
    return m0840_dict


def get_t_prs_job_cd_bom_data():
    """t_prs_job_cd_bom テーブルからデータを取得（日本時間で3か月先以降）"""
    print("\n===== t_prs_job_cd_bom テーブルからデータを取得 =====")

    # 日本時間で現在日時を取得し、3か月先の年月を計算
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    target_date = now_jst + relativedelta(months=3)
    target_year = target_date.year
    target_month = target_date.month
    print(f"対象期間: {target_year}年{target_month}月以降")

    # データベース接続文字列
    db_url = 'mssql+pyodbc://fukuharaadmin:xrTRzAJtKQ7B@production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com/chohyo?driver=SQL+Server'

    # エンジンを作成
    engine = create_engine(db_url, echo=False)

    # コネクションを取得してクエリ実行
    with engine.connect() as connection:
        sql = f"""
        SELECT
            prs_depth,
            job_cd,
            item_cls,
            item_name,
            prs_full_path,
            prs_job_cd_year,
            prs_job_cd_month,
            monthly,
            pac_date,
            top_assy,
            parent_item_cd,
            comp_item_cd,
            parent_item_cls,
            comp_item_cls,
            comp_item_name,
            comp_version,
            comp_state_name,
            comp_cat,
            comp_heat_treatment,
            comp_surface_treatment,
            comp_material,
            comp_weight,
            comp_section,
            sum_qty,
            gross_qty,
            parent_issue_space,
            parent_ws_cd,
            parent_srvg_instrctn_cls,
            parent_product_type,
            parent_mrp_deply_cls,
            comp_issue_space,
            comp_ws_cd,
            comp_srvg_instrctn_cls,
            comp_product_type,
            comp_mrp_deply_ccomp_ls,
            comp_real_issue_space,
            del_flag,
            prs_update_lock_flag,
            data_type,
            unit_molecule,
            unit_denominator,
            is_leaf,
            created_date,
            created_by,
            created_prg_nm,
            updated_date,
            updated_by,
            updated_prg_nm
        FROM t_prs_job_cd_bom
        WHERE (prs_job_cd_year > {target_year})
           OR (prs_job_cd_year = {target_year} AND prs_job_cd_month >= {target_month})
        """
        df = pd.read_sql(sql, connection)

    print(f"t_prs_job_cd_bom取得件数: {len(df):,}件")
    return df


def main():
    print("=" * 60)
    print("t_prs_job_cd_bom × M0810(HMBUNCD=6) × M0840 マッチングデータ出力")
    print("=" * 60)

    # 出力ディレクトリ
    script_dir = os.path.dirname(os.path.abspath(__file__))
    work_dir = os.path.join(script_dir, "work")
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 1. rBOM API M0810からHMBUNCD=6の品目コード辞書を取得
    hmbuncd6_hmcd_dict = get_hmbuncd6_hmcd_dict()

    if not hmbuncd6_hmcd_dict:
        print("HMBUNCD=6の品目が見つかりませんでした。")
        return

    # 2. rBOM API M0840からデータを取得
    m0840_dict = get_m0840_data()

    # 3. SQL Serverからt_prs_job_cd_bomデータを取得
    df = get_t_prs_job_cd_bom_data()

    if df.empty:
        print("t_prs_job_cd_bomデータが取得できませんでした。")
        return

    # 4. comp_item_cdがHMBUNCD=6のセットに含まれるデータを抽出
    print("\n===== M0810マッチング処理 =====")
    hmbuncd6_hmcd_set = set(hmbuncd6_hmcd_dict.keys())
    df_matched = df[df['comp_item_cd'].isin(hmbuncd6_hmcd_set)].copy()
    print(f"M0810マッチした件数: {len(df_matched):,}件")

    if df_matched.empty:
        print("マッチするデータがありませんでした。")
        return

    # 5. M0810のHMBUNCDを追加
    df_matched['M0810_HMBUNCD'] = df_matched['comp_item_cd'].apply(
        lambda x: hmbuncd6_hmcd_dict.get(x, "")
    )

    # 6. M0840とLEFT JOIN（comp_item_cd = HMCD）
    print("\n===== M0840 LEFT JOIN処理 =====")

    def get_ktseq(comp_item_cd):
        if comp_item_cd in m0840_dict:
            return m0840_dict[comp_item_cd]["KTSEQ"]
        return "工程登録無"

    def get_ktcd(comp_item_cd):
        if comp_item_cd in m0840_dict:
            return m0840_dict[comp_item_cd]["KTCD"]
        return "工程登録無"

    df_matched['M0840_KTSEQ'] = df_matched['comp_item_cd'].apply(get_ktseq)
    df_matched['M0840_KTCD'] = df_matched['comp_item_cd'].apply(get_ktcd)

    # マッチ/非マッチ件数を集計
    matched_m0840 = (df_matched['M0840_KTSEQ'] != "工程登録無").sum()
    unmatched_m0840 = (df_matched['M0840_KTSEQ'] == "工程登録無").sum()
    print(f"M0840マッチ: {matched_m0840:,}件")
    print(f"M0840非マッチ（工程登録無）: {unmatched_m0840:,}件")

    # 7. 全カラムCSV出力（workディレクトリ）
    output_file_full = os.path.join(work_dir, "05_t_prs_job_cd_bom_hmbuncd6.csv")
    df_matched.to_csv(output_file_full, index=False, encoding='utf-8-sig')
    print(f"\n全カラム出力完了: {output_file_full}")
    print(f"ファイルサイズ: {os.path.getsize(output_file_full) / 1024 / 1024:.2f} MB")

    # 8. サマリーCSV出力（outputディレクトリ）- 指定カラムのみ
    df_summary = df_matched[['job_cd', 'comp_item_cd', 'comp_item_name', 'M0810_HMBUNCD', 'M0840_KTSEQ', 'M0840_KTCD']].copy()
    output_file_summary = os.path.join(output_dir, "05_部品表調査サマリー_HMBUNCD6.csv")
    df_summary.to_csv(output_file_summary, index=False, encoding='utf-8-sig')
    print(f"\nサマリー出力完了: {output_file_summary}")
    print(f"ファイルサイズ: {os.path.getsize(output_file_summary) / 1024:.2f} KB")

    # データプレビュー
    print("\n--- サマリーデータプレビュー (先頭5件) ---")
    print(df_summary.head())

    # サマリー
    print("\n========== 処理結果サマリー ==========")
    print(f"M0810 HMBUNCD=6品目数: {len(hmbuncd6_hmcd_dict):,}件")
    print(f"M0840品目数: {len(m0840_dict):,}件")
    print(f"t_prs_job_cd_bom総行数: {len(df):,}件")
    print(f"M0810マッチした出力行数: {len(df_matched):,}件")
    print(f"  - M0840マッチ: {matched_m0840:,}件")
    print(f"  - M0840非マッチ（工程登録無）: {unmatched_m0840:,}件")

    return df_matched


if __name__ == "__main__":
    main()
