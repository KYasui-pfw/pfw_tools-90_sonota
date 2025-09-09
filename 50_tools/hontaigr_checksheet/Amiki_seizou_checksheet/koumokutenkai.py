import sys
import json
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import pyodbc
import sqlite3
import unicodedata

try:

    # デバッグ用
    def df_csv_cnv(df, filename):
        # DFをcsvにコンバートして出力
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        csv_name = os.path.dirname(
            __file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_"+filename+".csv"
        # df.to_csv(csv_name,index=False,encoding='CP932')
        df.to_csv(csv_name, index=True, encoding='CP932')

    def text_output(t):
        with open(os.path.dirname(__file__)+"\\"+'output.txt', 'w') as f:
            f.write(str(t))

    # ADD_20250423_付属品関係の取り付け、仕様別部品の取付け確認　への対応

    def fuzoku_shiyoubetu_set(value, kumino, dft1, dft2):

        r = ""  # 返却用変数
        if value == "[オイルミスト]":
            r = dft1.iloc[0]['an_oiling_device']

        if value == "[ロゴマーク]":
            str_agent_sjis = dft1.iloc[0]['an_agent_name'].encode(
                "shift-jis")  # 一旦byte型へ
            str_agent = str_agent_sjis.decode("shift-jis")  # SJISへ
            str_narrow = unicodedata.normalize('NFKC', str_agent)  # 全角→半角
            str_upper = str_narrow.upper()  # 大文字変換
            if "MONARCH" in str_upper:  # "MONARCH" が含まれているか判定
                r = "MONARCH"
            else:
                r = "FUKUHARA"

        if value == "[CEマーク]":
            # 設計熊谷さんより "MUK"ならCEマークが必要（欧州規格のため）
            if dft1.iloc[0]['an_agent_code'] == "MUK":
                r = "要"
            else:
                r = "不要"

        if value == "[IRO用タイミングベルト]":
            if dft2.empty:
                r = "不要"
            else:
                r = "要"

        if value == "[オートオイラー]":
            r = "オートオイラー5"

        if value == "[ダストクリーナー]":
            r = dft1.iloc[0]['an_needleblower_type']

        if value == "[ファブリックリング]":
            r = "ファブリックリング7"

        return r
    # クラスターセット

    def cluster_set(sheet, count, sai_gyo, df, mapping_work, kumino):
        if not df.empty:

            # DBからの取得処理（ループ前に行っておく）
            # 共通の接続処理(m_items_sub_71)
            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com;"
                "DATABASE=common;"
                "UID=fukuharaadmin;"
                "PWD=xrTRzAJtKQ7B")
            # SQLクエリを定義
            sql = f"""SELECT an_oiling_device,an_agent_code,an_agent_name,an_needleblower_type FROM m_items_sub_71
                    WHERE an_item_cd = '{kumino}'"""
            dft1 = pd.read_sql(sql, conn)

            # 共通の接続処理(t_prs_job_cd_bom)
            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com;"
                "DATABASE=chohyo;"
                "UID=fukuharaadmin;"
                "PWD=xrTRzAJtKQ7B")
            # SQLクエリを定義
            sql = f"""SELECT job_cd,comp_item_cd FROM t_prs_job_cd_bom
                    WHERE job_cd = '{kumino}'
                    AND (comp_item_cd LIKE 'TB-300%'
                        OR comp_item_cd LIKE 'TB-310%'
                        OR comp_item_cd LIKE 'TB-340%'
                        OR comp_item_cd LIKE 'TB-350%')"""
            dft2 = pd.read_sql(sql, conn)

            gyo = 0  # 再展開チェック用
            for i, row in df.iterrows():

                # 再設定行未満はスキップ
                gyo += 1
                if sai_gyo > gyo:
                    count += 13
                    continue

                # チェック項目
                mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                    "cluster": count, "type": "string", "value": str(row['チェック項目'])})
                count += 7
                # 前トグルflg
                # ADD_20250423_特殊ケースの対応（付属品関係の取り付けと仕様別部品の取付け確認は別システムから取得する）
                values = ["[オイルミスト]", "[ロゴマーク]", "[CEマーク]",
                          "[IRO用タイミングベルト]", "[オートオイラー]", "[ダストクリーナー]", "[ファブリックリング]"]
                if row['前トグルflg'] == 0:
                    mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                        "cluster": count, "type": "string", "value": str(row['前トグルflg'])})
                else:
                    mapping_work.append(
                        {"item": "syokaienkai", "sheet": sheet, "cluster": count, "type": "string", "value": ""})

                    # ADD_20250423_特殊ケース用の分岐追加
                    toggle1 = []
                    if any(v in str(row['前トグル']) for v in values):
                        # 個別のケースに合わせて処理
                        item = fuzoku_shiyoubetu_set(
                            str(row['前トグル']), kumino, dft1, dft2)
                        if item == "":
                            item = "　"
                        toggle1.append(
                            {"item": str(item), "label": str(item), "selected": False})
                        mapping_work.append({"item": "toggle1", "sheet": sheet, "cluster": int(
                            count-6), "type": "SetItemsToSelect", "value": item, "selectItems": toggle1})
                    else:
                        # トグルの作成
                        list1 = str(row['前トグル']).split(',')
                        if len(list1) > 1:
                            item2 = ""  # 何かマークを付けるときはここを使う
                        else:
                            item2 = ""
                        for item in list1:
                            if item == "":
                                item = "　"
                            toggle1.append(
                                {"item": str(item), "label": item2+str(item), "selected": False})
                            mapping_work.append({"item": "toggle1", "sheet": sheet, "cluster": int(
                                count-6), "type": "SetItemsToSelect", "value": str(list1[0]), "selectItems": toggle1})

                count += 1
                # 入力欄flg
                if row['入力欄flg'] == 0:
                    mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                        "cluster": count, "type": "string", "value": str(row['入力欄flg'])})
                else:
                    mapping_work.append(
                        {"item": "syokaienkai", "sheet": sheet, "cluster": count, "type": "string", "value": ""})
                count += 1
                # Noflg
                if row['Noflg'] == 0:
                    mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                        "cluster": count, "type": "string", "value": str(row['Noflg'])})
                else:
                    mapping_work.append(
                        {"item": "syokaienkai", "sheet": sheet, "cluster": count, "type": "string", "value": ""})
                count += 1
                # 後トグルflg
                if row['後トグルflg'] == 0:
                    mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                        "cluster": count, "type": "string", "value": str(row['後トグルflg'])})
                else:
                    mapping_work.append(
                        {"item": "syokaienkai", "sheet": sheet, "cluster": count, "type": "string", "value": ""})
                    # トグルの作成
                    list2 = str(row['後トグル']).split(',')
                    toggle2 = []
                    for item in list2:
                        if item == "":
                            item = "　"
                        toggle2.append(
                            {"item": str(item), "label": str(item), "selected": False})
                    mapping_work.append({"item": "toggle2", "sheet": sheet, "cluster": int(
                        count-6), "type": "SetItemsToSelect", "value": str(list2[0]), "selectItems": toggle2})
                count += 1
                # チェックflg
                if row['チェックflg'] == 0:
                    mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                        "cluster": count, "type": "string", "value": str(row['チェックflg'])})
                else:
                    mapping_work.append(
                        {"item": "syokaienkai", "sheet": sheet, "cluster": count, "type": "string", "value": ""})
                count += 1
                # 作業者名flg
                if row['作業者名flg'] == 0:
                    mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                        "cluster": count, "type": "string", "value": str(row['作業者名flg'])})
                else:
                    mapping_work.append(
                        {"item": "syokaienkai", "sheet": sheet, "cluster": count, "type": "string", "value": ""})
                count += 1
        else:
            mapping_work.append({"item": "syokaienkai", "sheet": sheet,
                                "cluster": count, "type": "string", "value": "チェック無し"})
        return (mapping_work)

    # jsonデータ読み取り
    jdata = json.loads(sys.stdin.readline())

    # 初回と再展開が共通のため、使用しないクラスターも読み取る
    kumino = jdata['data'][0]  # 組立番号
    button_flg = int(jdata['data'][1])  # ボタンflg 1は初回展開、2は再展開
    sai_gyo = 1  # 再展開用行
    if jdata['data'][2] != '':
        sai_gyo = int(jdata['data'][2])
    tenkai_sumi = jdata['data'][3]  # 展開flg
    page = int(jdata['data'][4])  # 処理ページ
    page1 = int(jdata['data'][5])  # 1ページ行数
    page2 = int(jdata['data'][6])+page1  # 2ページ行数
    page3 = int(jdata['data'][7])+page2  # 3ページ行数
    page4 = int(jdata['data'][8])+page3  # 4ページ行数

    # エラーキャッチ
    if kumino == "":
        raise ValueError("組立番号がありません")
    if tenkai_sumi != "" and button_flg == 1:
        raise ValueError("初回項目展開済です")
    if tenkai_sumi == "" and button_flg == 2:
        raise ValueError("初回展開を行ってください")
    if sai_gyo == 0 and button_flg == 2:
        raise ValueError("再展開用の[行No]を入力してください")

    # #DB接続定義
    filepath = 'D:\\py\hontaigr_checksheet\\Database\\hontai_seizo.db'
    conn = sqlite3.connect(filepath)
    cursor = conn.cursor()

    # ①生産機基本情報テーブルから取得
    sql1 = f'select * from production_machine_info where 組立番号 = "{kumino}"'
    df1 = pd.read_sql(sql1, conn)
    if df1.empty:
        raise ValueError("組立番号の登録がありません")

    # ②帳票種別テーブルから取得
    chohyo_no = df1.at[0, "帳票No"]
    sql2 = f'select * from report_type_table where 帳票No = "{chohyo_no}"'
    df2 = pd.read_sql(sql2, conn)

    if df2.empty:
        raise ValueError(f"帳票No：{chohyo_no}の情報が存在しません")

    # ③機種区分テーブルから取得
    kisyu_kubun = df2.at[0, "機種区分"]
    sql3 = f'select * from model_type_table where 機種区分 = "{kisyu_kubun}"'
    df3 = pd.read_sql(sql3, conn)

    # マージする
    df4 = pd.merge(df2, df3, on="機種区分")

    # 縦列への変更
    df_category1 = df4[['機種区分', 'カテゴリ区分1', 'カテゴリ名1']].rename(
        columns={'カテゴリ区分1': 'カテゴリ区分', 'カテゴリ名1': 'カテゴリ名'})
    df_category2 = df4[['機種区分', 'カテゴリ区分2', 'カテゴリ名2']].rename(
        columns={'カテゴリ区分2': 'カテゴリ区分', 'カテゴリ名2': 'カテゴリ名'})
    df_category3 = df4[['機種区分', 'カテゴリ区分3', 'カテゴリ名3']].rename(
        columns={'カテゴリ区分3': 'カテゴリ区分', 'カテゴリ名3': 'カテゴリ名'})
    df_category4 = df4[['機種区分', 'カテゴリ区分4', 'カテゴリ名4']].rename(
        columns={'カテゴリ区分4': 'カテゴリ区分', 'カテゴリ名4': 'カテゴリ名'})
    df_category5 = df4[['機種区分', 'カテゴリ区分5', 'カテゴリ名5']].rename(
        columns={'カテゴリ区分5': 'カテゴリ区分', 'カテゴリ名5': 'カテゴリ名'})
    df_category6 = df4[['機種区分', 'カテゴリ区分6', 'カテゴリ名6']].rename(
        columns={'カテゴリ区分6': 'カテゴリ区分', 'カテゴリ名6': 'カテゴリ名'})
    df_category7 = df4[['機種区分', 'カテゴリ区分7', 'カテゴリ名7']].rename(
        columns={'カテゴリ区分7': 'カテゴリ区分', 'カテゴリ名7': 'カテゴリ名'})
    df_category8 = df4[['機種区分', 'カテゴリ区分8', 'カテゴリ名8']].rename(
        columns={'カテゴリ区分8': 'カテゴリ区分', 'カテゴリ名8': 'カテゴリ名'})
    df_category9 = df4[['機種区分', 'カテゴリ区分9', 'カテゴリ名9']].rename(
        columns={'カテゴリ区分9': 'カテゴリ区分', 'カテゴリ名9': 'カテゴリ名'})
    df_category10 = df4[['機種区分', 'カテゴリ区分10', 'カテゴリ名10']].rename(
        columns={'カテゴリ区分10': 'カテゴリ区分', 'カテゴリ名10': 'カテゴリ名'})
    df_category11 = df4[['機種区分', 'カテゴリ区分11', 'カテゴリ名11']].rename(
        columns={'カテゴリ区分11': 'カテゴリ区分', 'カテゴリ名11': 'カテゴリ名'})
    df_category12 = df4[['機種区分', 'カテゴリ区分12', 'カテゴリ名12']].rename(
        columns={'カテゴリ区分12': 'カテゴリ区分', 'カテゴリ名12': 'カテゴリ名'})
    df_category13 = df4[['機種区分', 'カテゴリ区分13', 'カテゴリ名13']].rename(
        columns={'カテゴリ区分13': 'カテゴリ区分', 'カテゴリ名13': 'カテゴリ名'})
    df_category14 = df4[['機種区分', 'カテゴリ区分14', 'カテゴリ名14']].rename(
        columns={'カテゴリ区分14': 'カテゴリ区分', 'カテゴリ名14': 'カテゴリ名'})
    df_category15 = df4[['機種区分', 'カテゴリ区分15', 'カテゴリ名15']].rename(
        columns={'カテゴリ区分15': 'カテゴリ区分', 'カテゴリ名15': 'カテゴリ名'})
    df_category16 = df4[['機種区分', 'カテゴリ区分16', 'カテゴリ名16']].rename(
        columns={'カテゴリ区分16': 'カテゴリ区分', 'カテゴリ名16': 'カテゴリ名'})
    df_category17 = df4[['機種区分', 'カテゴリ区分17', 'カテゴリ名17']].rename(
        columns={'カテゴリ区分17': 'カテゴリ区分', 'カテゴリ名17': 'カテゴリ名'})
    df_category18 = df4[['機種区分', 'カテゴリ区分18', 'カテゴリ名18']].rename(
        columns={'カテゴリ区分18': 'カテゴリ区分', 'カテゴリ名18': 'カテゴリ名'})
    df_category19 = df4[['機種区分', 'カテゴリ区分19', 'カテゴリ名19']].rename(
        columns={'カテゴリ区分19': 'カテゴリ区分', 'カテゴリ名19': 'カテゴリ名'})
    df_category20 = df4[['機種区分', 'カテゴリ区分20', 'カテゴリ名20']].rename(
        columns={'カテゴリ区分20': 'カテゴリ区分', 'カテゴリ名20': 'カテゴリ名'})
    df_category21 = df4[['機種区分', 'カテゴリ区分21', 'カテゴリ名21']].rename(
        columns={'カテゴリ区分21': 'カテゴリ区分', 'カテゴリ名21': 'カテゴリ名'})
    df_category22 = df4[['機種区分', 'カテゴリ区分22', 'カテゴリ名22']].rename(
        columns={'カテゴリ区分22': 'カテゴリ区分', 'カテゴリ名22': 'カテゴリ名'})
    df_category23 = df4[['機種区分', 'カテゴリ区分23', 'カテゴリ名23']].rename(
        columns={'カテゴリ区分23': 'カテゴリ区分', 'カテゴリ名23': 'カテゴリ名'})
    df_category24 = df4[['機種区分', 'カテゴリ区分24', 'カテゴリ名24']].rename(
        columns={'カテゴリ区分24': 'カテゴリ区分', 'カテゴリ名24': 'カテゴリ名'})
    df_category25 = df4[['機種区分', 'カテゴリ区分25', 'カテゴリ名25']].rename(
        columns={'カテゴリ区分25': 'カテゴリ区分', 'カテゴリ名25': 'カテゴリ名'})
    df_category26 = df4[['機種区分', 'カテゴリ区分26', 'カテゴリ名26']].rename(
        columns={'カテゴリ区分26': 'カテゴリ区分', 'カテゴリ名26': 'カテゴリ名'})
    df_category27 = df4[['機種区分', 'カテゴリ区分27', 'カテゴリ名27']].rename(
        columns={'カテゴリ区分27': 'カテゴリ区分', 'カテゴリ名27': 'カテゴリ名'})
    df_category28 = df4[['機種区分', 'カテゴリ区分28', 'カテゴリ名28']].rename(
        columns={'カテゴリ区分28': 'カテゴリ区分', 'カテゴリ名28': 'カテゴリ名'})
    df_category29 = df4[['機種区分', 'カテゴリ区分29', 'カテゴリ名29']].rename(
        columns={'カテゴリ区分29': 'カテゴリ区分', 'カテゴリ名29': 'カテゴリ名'})
    df_category30 = df4[['機種区分', 'カテゴリ区分30', 'カテゴリ名30']].rename(
        columns={'カテゴリ区分30': 'カテゴリ区分', 'カテゴリ名30': 'カテゴリ名'})

    # データフレームをリストに格納
    df_list = [
        df_category1, df_category2, df_category3, df_category4, df_category5,
        df_category6, df_category7, df_category8, df_category9, df_category10,
        df_category11, df_category12, df_category13, df_category14, df_category15,
        df_category16, df_category17, df_category18, df_category19, df_category20,
        df_category21, df_category22, df_category23, df_category24, df_category25,
        df_category26, df_category27, df_category28, df_category29, df_category30
    ]

    # 表示を編集
    tate_combined_df = pd.concat(df_list, ignore_index=True)
    tate_combined_df.reset_index(drop=True, inplace=True)
    tate_combined_df = tate_combined_df[tate_combined_df['カテゴリ区分'] != 99]
    tate_combined_df.index = tate_combined_df.index + 1
    tate_combined_df = tate_combined_df.reset_index()

    # 各カテゴリ名に"【】"を追加
    for index in range(len(tate_combined_df)):
        current_value = tate_combined_df.loc[index, 'カテゴリ名']
        new_value = '【' + current_value + '】'
        tate_combined_df.loc[index, 'カテゴリ名'] = new_value

    # concatするために編集
    tate_combined_df = tate_combined_df.rename(
        columns={'カテゴリ名': 'チェック項目', 'index': 'カテゴリNo'})
    tate_combined_df = tate_combined_df.reindex(
        columns=['機種区分', 'カテゴリNo', 'カテゴリ区分', '表示順', 'チェック項目', '前トグルflg', '前トグル', '入力欄flg', 'Noflg', '後トグルflg', '後トグル', 'チェックflg', '作業者名flg'])

    # flg等をセット
    tate_combined_df['表示順'] = 0
    tate_combined_df['前トグルflg'] = 0
    tate_combined_df['前トグル'] = ""
    tate_combined_df['入力欄flg'] = 0
    tate_combined_df['Noflg'] = 0
    tate_combined_df['後トグルflg'] = 0
    tate_combined_df['後トグル'] = ""
    tate_combined_df['チェックflg'] = 0
    tate_combined_df['作業者名flg'] = 0

    # ④チェック項目テーブルから取得
    kisyu_kubun = df2.at[0, "機種区分"]
    sql4 = f'select * from check_item_table where 機種区分 = "{kisyu_kubun}"'
    df4 = pd.read_sql(sql4, conn)

    # 今回の対象のチェック項目のみ抽出
    df4 = pd.merge(df4, tate_combined_df[['カテゴリNo', 'カテゴリ区分']], on=[
                   'カテゴリNo', 'カテゴリ区分'], how='inner')

    # 各カテゴリ名の頭に全角スペースを２つ追加
    for index in range(len(df4)):
        current_value = df4.loc[index, 'チェック項目']
        new_value = '　　' + current_value
        df4.loc[index, 'チェック項目'] = new_value

    # concatして結合、ソートする
    df5 = pd.concat([tate_combined_df, df4], ignore_index=True)
    df5 = df5.sort_values(['機種区分', 'カテゴリNo', 'カテゴリ区分', '表示順'])

    # 空欄行を作成する
    # 行数が131未満の場合、空の行で埋める

    if len(df5) < page4:
        empty_rows = page4 - len(df5)
        empty_df = pd.DataFrame([{}]*empty_rows)
        empty_df['チェック項目'] = "　"
        empty_df.loc[0, 'チェック項目'] = "　　=== 以下空白 ==="
        empty_df['入力欄'] = "　"
        empty_df['前トグルflg'] = 0
        empty_df['入力欄flg'] = 0
        empty_df['Noflg'] = 0
        empty_df['後トグルflg'] = 0
        empty_df['チェックflg'] = 0
        empty_df['作業者名flg'] = 0
        df5 = pd.concat([df5, empty_df], ignore_index=True)

    # i-reporterへの返却処理
    mapping_work = []

    # header部
    mapping_work.append({"item": "syokaienkai", "sheet": 1, "cluster": 0,
                        "type": "string", "value": str(df1.loc[0, '年'])})
    mapping_work.append({"item": "syokaienkai", "sheet": 1, "cluster": 1,
                        "type": "string", "value": str(df1.loc[0, '月'])})
    mapping_work.append({"item": "syokaienkai", "sheet": 1, "cluster": 2,
                        "type": "string", "value": str(df1.loc[0, '次'])})
    mapping_work.append({"item": "syokaienkai", "sheet": 1, "cluster": 4,
                        "type": "string", "value": str(df1.loc[0, '機種名'])})
    mapping_work.append({"item": "syokaienkai", "sheet": 1, "cluster": 5,
                        "type": "string", "value": str(df1.loc[0, 'インチ'])})
    mapping_work.append({"item": "syokaienkai", "sheet": 1, "cluster": 6,
                        "type": "string", "value": str(df1.loc[0, 'ゲージ'])})
    if button_flg == 1:
        mapping_work.append({"item": "syokaienkai", "sheet": 1,
                            "cluster": 14, "type": "string", "value": str(1)})

    # 1ページ目
    if page <= 1:
        page1_df = df5.iloc[0:page1]
        mapping_work = cluster_set(
            1, 22, sai_gyo, page1_df, mapping_work, kumino)
        sai_gyo = 1  # 再設定用行をリセット
    # 2ページ目
    if page <= 2:
        page2_df = df5.iloc[page1:page2]
        mapping_work = cluster_set(
            2, 12, sai_gyo, page2_df, mapping_work, kumino)
        sai_gyo = 1  # 再設定用行をリセット
    # 3ページ目
    if page <= 3:
        page3_df = df5.iloc[page2:page3]
        mapping_work = cluster_set(
            3, 12, sai_gyo, page3_df, mapping_work, kumino)
        sai_gyo = 1  # 再設定用行をリセット
    # 4ページ目
    if page <= 4:
        page4_df = df5.iloc[page3:page4]
        mapping_work = cluster_set(
            4, 12, sai_gyo, page4_df, mapping_work, kumino)

    # フォーカスの移動 結局使わなかったが、備忘のためコメントアウトする
    # if button_flg == 1:
    #    mapping_work.append({"item":"syokaienkai","sheet": 1,"cluster": 8,"type": "SetFocus"})
    # if button_flg == 2:
    #    mapping_work.append({"item":"syokaienkai","sheet": 1,"cluster": 10,"type": "SetFocus"})
    mappings = {"error": "", "mappings": mapping_work}

    print(json.dumps(mappings))
except ValueError as e:
    mappings = {"error": "エラー：" + str(e)}
    print(json.dumps(mappings))
except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
