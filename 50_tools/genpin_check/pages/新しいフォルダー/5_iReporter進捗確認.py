################################
# 　i-Reporter進捗状況確認       #
# 　簡単なDF表示のページ          #
# 　　　　　　　　　　　　　　　　　#
################################
# インポート
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
import sqlite3
import os
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

try:

    # ireporterDB
    def ireporter_data_get(sql):

        # #DB接続定義
        db_url = 'postgresql://postgres:cimtops@ESRV10/irepodb'

        # エンジンを作成
        engine = create_engine(db_url, echo=True)

        # セッションを作成するためのSessionクラスを生成
        Session = sessionmaker(bind=engine)
        session = Session()

        # コネクションを取得
        with engine.connect() as connection:
            # SQLクエリの実行
            df = pd.read_sql(sql, connection)

        # セッションを閉じる
        session.close()

        return (df)

    # sqlite3への接続
    def sqlite_data_get(sql, filepath):
        # #DB接続定義
        db_url = f'sqlite:///{filepath}'

        # エンジンを作成
        engine = create_engine(db_url, echo=True)

        # セッションを作成するためのSessionクラスを生成
        Session = sessionmaker(bind=engine)
        session = Session()

        # コネクションを取得
        with engine.connect() as connection:
            df = pd.read_sql(sql, connection)

        # セッションを閉じる
        session.close()

        return (df)

    # 取得したデータフレームを編集してReturn
    def df_edit(df):
        # ヘッダー部付け替え
        df = df.rename(columns={'rep_top_id': '帳票ID',
                                'cluster_1_2_t': 'ロット番号',
                                'cluster_1_5_t': '組立番号',
                                'cluster_1_6_t': '機種名',
                                'top_remarks1': '部品名',
                                'cluster_1_3_t': '部番',
                                'cluster_1_7_t': 'インチ',
                                'cluster_1_8_t': 'ゲージ',
                                'top_remarks3': '年月次',
                                'cluster_1_9_t': '出荷先'})

        # 分解
        dfs = {}
        for i in range(1, 53):
            columns_to_select = [
                '帳票ID', 'ロット番号', '組立番号', '機種名', '部品名', '部番', 'インチ', 'ゲージ', '年月次', '出荷先',
                f'cluster_1_{14+(i-1)*12}_t', f'cluster_1_{22+(i-1)*12}_d',
                f'cluster_1_{23+(i-1)*12}_t', f'cluster_1_{24+(i-1)*12}_n'
            ]

            new_column_names = {
                f'cluster_1_{14+(i-1)*12}_t': '工程',
                f'cluster_1_{22+(i-1)*12}_d': '測定日',
                f'cluster_1_{23+(i-1)*12}_t': '測定者',
                f'cluster_1_{24+(i-1)*12}_n': '判定合否'
            }

            # データフレームを選択してカラム名を変更
            dfs[f'df{i}'] = df[columns_to_select].rename(
                columns=new_column_names)
            if i != 1:
                dfs[f'df{i}'] = dfs[f'df{i}'].dropna(subset=['工程'])
                dfs[f'df{i}'] = dfs[f'df{i}'][dfs[f'df{i}']['工程'] != '=====']
        combined_df = pd.concat(dfs.values(), ignore_index=True)
        combined_df['状態'] = '完了'
        combined_df['工程'] = combined_df['工程'].fillna('')
        # '工程'が空文字（''）の場合に'状態'を"未着手"に更新
        combined_df.loc[combined_df['工程'] == '', '状態'] = '未着手'
        combined_df['測定日'] = combined_df['測定日'].astype(str)
        combined_df['判定合否'] = combined_df['判定合否'].astype(str)
        combined_df = combined_df.replace(["NaT", "nan", "None"], '')
        combined_df['判定合否'] = combined_df['判定合否'].replace(
            ['1.0', '2.0'], ['合', '否'])
        combined_df = combined_df.fillna('')

        # 未着手のものはcombined_dfa、完了はcombined_dfbに分割
        # 完了はirepodbでチェックシート上に展開されている工程を利用するが、
        # 未着手のものはirepodbから取得できないため、checksheetdbから工程を展開する
        combined_dfa = combined_df[combined_df['状態'] == '未着手']
        combined_dfb = combined_df[combined_df['状態'] == '完了']

        # 以下、未着手に対する処理
        # 現品票の工程情報取得
        sql = 'SELECT ロット番号,完成部番,工程VERSION as 工程Ver FROM genpinhyo'
        filepath = os.path.dirname(os.path.dirname(
            __file__))+'\\Database\\genpinhyo.db'
        genpin_df = sqlite_data_get(sql, filepath)

        # 工程図番の工程情報取得
        sql = 'SELECT 完成部番,工程Ver,工程順, 工程 as 工程gen FROM kouteizuban'
        filepath = os.path.dirname(os.path.dirname(
            __file__))+'\\Database\\checksheet.db'
        check_df = sqlite_data_get(sql, filepath)
        # '工程Ver'列をオブジェクト型に変換
        check_df['工程Ver'] = check_df['工程Ver'].astype(str)

        gc_df = pd.merge(genpin_df, check_df,
                         on=['完成部番', '工程Ver'], how='right')
        gc_df = gc_df.sort_values(['完成部番', '工程Ver', '工程順'])
        combined_dfa = pd.merge(combined_dfa, gc_df,
                                on=['ロット番号'], how='left')
        combined_dfa['工程'] = combined_dfa['工程gen']
        combined_dfa = combined_dfa.drop(
            # columns=['完成部番', '工程Ver', '工程順', '工程gen'])
            columns=['完成部番', '工程Ver', '工程gen'])

        # 未着手と完了を縦に繋ぐ（concat)
        combined_df = pd.concat(
            [combined_dfa, combined_dfb], ignore_index=True)
        # 項目並び替え
        combined_df = combined_df[['帳票ID', 'ロット番号', '組立番号', '機種名', '部品名',
                                   '部番', 'インチ', 'ゲージ', '年月次', '出荷先', '状態',
                                   '工程', '測定日', '測定者', '判定合否', '工程順']]

        # まずは縦並びのDFが完成
        tate_df = combined_df

        # 横並び用DFを作成
        yoko_df = combined_df
        columns_to_add = {}
        for i in range(2, 11):
            columns_to_add[f'工程{i}'] = ''
            columns_to_add[f'測定日{i}'] = ''
            columns_to_add[f'測定者{i}'] = ''
            columns_to_add[f'判定合否{i}'] = ''
        yoko_df = yoko_df.assign(**columns_to_add)

        # 帳票ID順に並べ
        yoko_df = yoko_df.sort_values(['帳票ID'])

        # 2から10までループで処理
        for i in range(2, 11):
            mask = yoko_df['帳票ID'] == yoko_df['帳票ID'].shift(-i + 1)
            yoko_df.loc[mask, f'工程{i}'] = yoko_df['工程'].shift(-i + 1)
            yoko_df.loc[mask, f'測定日{i}'] = yoko_df['測定日'].shift(-i + 1)
            yoko_df.loc[mask, f'測定者{i}'] = yoko_df['測定者'].shift(-i + 1)
            yoko_df.loc[mask, f'判定合否{i}'] = yoko_df['判定合否'].shift(-i + 1)

        mask = yoko_df['帳票ID'] == yoko_df['帳票ID'].shift(1)
        yoko_df = yoko_df.loc[~mask, :]
        yoko_df = yoko_df.rename(
            columns={'工程': '工程1', '測定日': '測定日1', '測定者': '測定者1', '判定合否': '判定合否1'})

        return (tate_df, yoko_df)

    def main():

        st.set_page_config(
            page_title='i-reporter進捗確認',
            layout="wide")

        HIDE_ST_STYLE = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
                    }
                    .appview-container .main .block-container{
                                padding-top: 1rem;
                                padding-right: 3rem;
                                padding-left: 3rem;
                                padding-bottom: 1rem;
                            }
                            .reportview-container {
                                padding-top: 0rem;
                                padding-right: 3rem;
                                padding-left: 3rem;
                                padding-bottom: 0rem;
                            }
                            header[data-testid="stHeader"] {
                                z-index: -1;
                            }
                            div[data-testid="stToolbar"] {
                            z-index: 100;
                            }
                            div[data-testid="stDecoration"] {
                            z-index: 100;
                            }
                    .block-container {
                            padding-top: 0rem !important;
                            padding-bottom: 0rem !important;
                            }
                    </style>
                    </style>
    """
        st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

        # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
        dt_now = datetime.now(timezone(timedelta(hours=9))) + \
            timedelta(days=32)  # 日本時刻+32日
        dt_nen = int(dt_now.strftime('%Y'))
        dt_tsuki = int(dt_now.strftime('%m'))

        col1, col2, col3, col4, col5 = st.columns([
            1, 1, 1, 1, 1])
        with col1:
            st.markdown("""#### i-Repo進捗確認 """)
            st.write("※β版です")
        with col2:
            nen = st.selectbox(
                '生産計画年', [dt_nen-1, dt_nen, dt_nen+1], index=1)
        with col3:
            if dt_tsuki == 1:
                dt_tsuki += 1
            getsu = st.selectbox('生産計画月', [
                '', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], index=dt_tsuki-1)
        with col4:
            if getsu == '':
                ji = ''
            else:
                ji = st.selectbox(
                    '生産計画次', ['', '01', '02', '03', '04', '05', '06', '07', '08'])
        # 追加 前後１次表示 ADD_20241111
        with col5:
            c_flg = 0
            s_nenplus = 0
            s_nenminus = 0
            s_getsuplus = 0
            s_getsuminus = 0
            s_jiplus = 0
            s_jiminus = 0

            st.write("")
            st.write("")
            if st.checkbox('前後1次を表示'):
                # 条件追加
                c_flg = 1
                # 月が空欄
                if getsu == '':
                    s_nenplus = nen + 1
                    s_nenminus = nen - 1
                    s_getsuplus = '01'
                    s_getsuminus = '12'
                    s_jiplus = '01'
                    s_jiminus = '08'
                # 月が1月
                elif getsu == '01':
                    # 次が空欄
                    if ji == '':
                        s_nenplus = nen
                        s_nenminus = nen - 1
                        s_getsuplus = '02'
                        s_getsuminus = '12'
                        s_jiplus = '01'
                        s_jiminus = '08'
                    # 次が01
                    elif ji == '01':
                        s_nenplus = nen
                        s_nenminus = nen - 1
                        s_getsuplus = '01'
                        s_getsuminus = '12'
                        s_jiplus = '02'
                        s_jiminus = '08'
                    # 次が08
                    elif ji == '08':
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = '02'
                        s_getsuminus = '01'
                        s_jiplus = '01'
                        s_jiminus = '07'
                    # 次が01と08以外
                    else:
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = '01'
                        s_getsuminus = '01'
                        s_jiplus = '0'+str(int(ji)+1)
                        if len(s_jiplus) == 3:
                            s_jiplus = s_jiplus[1:]
                        s_jiminus = '0'+str(int(ji)-1)
                        if len(s_jiminus) == 3:
                            s_jiminus = s_jiminus[1:]
                elif getsu == '12':
                    if ji == '':
                        s_nenplus = nen + 1
                        s_nenminus = nen
                        s_getsuplus = '01'
                        s_getsuminus = '11'
                        s_jiplus = '01'
                        s_jiminus = '08'
                    elif ji == '01':
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = '12'
                        s_getsuminus = '11'
                        s_jiplus = '02'
                        s_jiminus = '08'
                    elif ji == '08':
                        s_nenplus = nen + 1
                        s_nenminus = nen
                        s_getsuplus = '01'
                        s_getsuminus = '12'
                        s_jiplus = '01'
                        s_jiminus = '07'
                    else:
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = '12'
                        s_getsuminus = '12'
                        s_jiplus = '0'+str(int(ji)+1)
                        if len(s_jiplus) == 3:
                            s_jiplus = s_jiplus[1:]
                        s_jiminus = '0'+str(int(ji)-1)
                        if len(s_jiminus) == 3:
                            s_jiminus = s_jiminus[1:]
                else:
                    if ji == '':
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = '0'+str(int(getsu)+1)
                        if len(s_getsuplus) == 3:
                            s_getsuplus = s_getsuplus[1:]
                        s_getsuminus = '0'+str(int(getsu)-1)
                        if len(s_getsuminus) == 3:
                            s_getsuminus = s_getsuminus[1:]
                        s_jiplus = '01'
                        s_jiminus = '08'
                    elif ji == '01':
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = getsu
                        s_getsuminus = '0'+str(int(getsu)-1)
                        if len(s_getsuminus) == 3:
                            s_getsuminus = s_getsuminus[1:]
                        s_jiplus = '02'
                        s_jiminus = '08'
                    elif ji == '08':
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = '0'+str(int(getsu)+1)
                        if len(s_getsuplus) == 3:
                            s_getsuplus = s_getsuplus[1:]
                        s_getsuminus = getsu
                        s_jiplus = '01'
                        s_jiminus = '07'
                    else:
                        s_nenplus = nen
                        s_nenminus = nen
                        s_getsuplus = getsu
                        s_getsuminus = getsu
                        s_jiplus = '0'+str(int(ji)+1)
                        if len(s_jiplus) == 3:
                            s_jiplus = s_jiplus[1:]
                        s_jiminus = '0'+str(int(ji)-1)
                        if len(s_jiminus) == 3:
                            s_jiminus = s_jiminus[1:]

                # s_nenplus = int(str(s_nenplus)[2:4])
                # s_nenminus = int(str(s_nenminus)[2:4])
                # s_getsuplus = int(s_getsuplus)
                # s_getsuminus = int(s_getsuminus)
                # s_jiplus = int(s_jiplus)
                # s_jiminus = int(s_jiminus)

                s_nenplus = str(s_nenplus)
                s_nenminus = str(s_nenminus)
                s_getsuplus = s_getsuplus
                s_getsuminus = s_getsuminus
                s_jiplus = s_jiplus
                s_jiminus = s_jiminus

        # irepoDBからデータ取得
        # snen = int(str(nen)[2:4])
        snengetsuji = ""

        snen = nen
        if getsu == '':
            sql1 = f'''select * from view_report_405 where (cluster_1_4_t LIKE '{
                str(snen)}___' )'''
            sql2 = f'''select * from view_report_406 where (cluster_1_4_t LIKE '{
                str(snen)}___' )'''
        else:
            # sgetsu = int(getsu)
            sgetsu = getsu
            if ji == '':
                sql1 = f'''select * from view_report_405 where (cluster_1_4_t LIKE '{
                    str(snen) + str(sgetsu)}_' )'''
                sql2 = f'''select * from view_report_406 where (cluster_1_4_t LIKE '{
                    str(snen) + str(sgetsu)}_' )'''
            else:
                # sji = int(ji)
                sji = str(int(ji))
                snengetsuji = str(snen) + str(sgetsu) + str(sji)
                sql1 = f'''select * from view_report_405 where (cluster_1_4_t = '{
                    snengetsuji}' )'''
                sql2 = f'''select * from view_report_406 where (cluster_1_4_t = '{
                    snengetsuji}' )'''
        if c_flg == 1:
            sql1 += f""" or
            (cluster_1_4_t = '{str(s_nenplus) + str(s_getsuplus) + str(int(s_jiplus))}') or
            (cluster_1_4_t = '{str(s_nenminus) + str(s_getsuminus) + str(int(s_jiminus))}') """
            sql2 += f""" or
            (cluster_1_4_t = '{str(s_nenplus) + str(s_getsuplus) + str(int(s_jiplus))}') or
            (cluster_1_4_t = '{str(s_nenminus) + str(s_getsuminus) + str(int(s_jiminus))}') """
        # df1は縦帳票
        df1 = ireporter_data_get(sql1)
        # df2は横帳票
        df2 = ireporter_data_get(sql2)
        # 縦横帳票データを縦結合
        df = pd.concat([df1, df2], ignore_index=True)
        # 編集用の関数に投げて、データフレームを取得
        tate_df, yoko_df = df_edit(df)
        # タブで表示を区切る
        tab_titles = ['進捗確認　', '進捗データ一覧　']
        tab1, tab2 = st.tabs(tab_titles)
        # タブ１　進捗確認
        with tab1:
            if tate_df.empty:
                st.write("表示するデータがありません")
            else:
                # 日付処理は先頭
                # '日付'をdatetime形式に変換、後の処理のために最小日・最大日を取得しておく
                tate_df['測定日'] = pd.to_datetime(tate_df['測定日'])
                tate_df["前日"] = tate_df['測定日'] - pd.Timedelta(days=1)
                # 最小日を含む月の月初・最大日を含む月の月末の取得
                min_date = tate_df['前日'].min() - pd.offsets.MonthBegin(1)
                max_date = tate_df['測定日'].max() + pd.offsets.MonthEnd(0)

                # システム日付取得
                current_date = datetime.now()
                current_month_start = pd.to_datetime(
                    current_date.strftime('%Y-%m-01'))
                current_month_end = current_month_start + \
                    pd.offsets.MonthEnd(0)

                # min_date または max_date が取得できない場合の処理
                if pd.isna(min_date):
                    min_date = current_month_start
                if pd.isna(max_date):
                    max_date = current_month_end

                with st.expander('抽出条件'):
                    cola1, cola2, cola3, cola4, cola5 = st.columns(
                        [2, 2, 2, 2, 2])
                    with cola1:
                        # 組立番号
                        kumi_list = list(set(tate_df['組立番号'].tolist()))
                        kumi_list.sort()
                        kumi_list.insert(0, "")
                        kumitate = st.selectbox('組立番号', kumi_list, index=0)
                        if kumitate != '':
                            mdf1 = tate_df[tate_df['組立番号'] == kumitate]
                        else:
                            mdf1 = tate_df
                    with cola2:
                        # 機種名
                        kisyu_list = list(set(tate_df['機種名'].tolist()))
                        kisyu_list.sort()
                        kisyu_list.insert(0, "")
                        kisyumei = st.selectbox('機種名', kisyu_list, index=0)
                        if kisyumei != '':
                            mdf2 = tate_df[tate_df['機種名'] == kisyumei]
                        else:
                            mdf2 = tate_df
                    with cola3:
                        # 部品名
                        buhin_list = list(set(tate_df['部品名'].tolist()))
                        buhin_list.sort()
                        buhin_list.insert(0, "")
                        buhinmei = st.selectbox('部品名', buhin_list, index=0)
                        if buhinmei != '':
                            mdf3 = tate_df[tate_df['部品名'] == buhinmei]
                        else:
                            mdf3 = tate_df
                    with cola4:
                        # 完成部番
                        buban = st.text_input("部番", '')
                    with cola5:
                        st.write("")
                        syubetsu2 = st.radio(
                            "検索", ("前方一致", "部分一致"),  index=1, label_visibility="collapsed")
                        # 完成部番
                        if syubetsu2 == "前方一致":
                            mdf4 = tate_df[tate_df['部番'].str.startswith(buban)]
                        elif syubetsu2 == "部分一致":
                            mdf4 = tate_df[tate_df['部番'].str.contains(buban)]

                    colb1, colb2, colb3, colb4, colb5 = st.columns(
                        [2, 2, 2, 2, 2])
                    with colb1:
                        # 期間開始
                        graph_min_date = st.date_input(
                            '表示期間開始', datetime.date(min_date))
                    with colb2:
                        # 期間開始
                        graph_max_date = st.date_input(
                            '表示期間終了', datetime.date(max_date))
                    with colb5:
                        # 画像ファイルのパスを指定
                        st.markdown("##### 色分けの区分")
                        image_path = os.path.dirname(
                            os.path.dirname(__file__)) + '/static/kubun.png'
                        st.image(image_path)
                common_df = mdf1.copy()
                # 2番目から4番目までのデータフレームと共通行を抽出
                for mdf in [mdf2, mdf3, mdf4]:
                    common_df = pd.merge(common_df, mdf, how='inner')
                tate_df = common_df.copy()

                # スケール設定用
                scale_df = tate_df[["帳票ID"]]
                scale_df = scale_df.drop_duplicates()

                # 工程毎の判断になるので、測定日の入っていない"状態"は未着手に変更
                tate_df.loc[tate_df['測定日'].isnull() | (
                    tate_df['測定日'] == ''), '状態'] = '未着手'

                # 分割し、未着手のdfのみ日付設定処理を行う
                tate_dfa = tate_df[tate_df['状態'] == '未着手']
                tate_dfb = tate_df[tate_df['状態'] == '完了']

                # 未着手の対応　仮日付のセット
                # 1から10までループで処理
                for i in range(1, 11):
                    mask = tate_dfa['帳票ID'] == tate_dfa['帳票ID'].shift(
                        -i + 1)
                    tate_dfa.loc[mask, '前日'] = pd.to_datetime(graph_min_date) + \
                        pd.Timedelta(days=(i-1))
                    tate_dfa.loc[mask, '測定日'] = pd.to_datetime(graph_min_date) + \
                        pd.Timedelta(days=i)

                # 完了の対応　日付が被ったときの対応
                # 工程が同日日に完了した場合の対応として、工程を結合する
                # 1行下の行と"帳票ID"と"測定日"が同じ行を識別するマスク
                tate_dfb = tate_dfb.sort_values(['帳票ID', '測定日'])
                for i in range(1, 11):
                    mask = (tate_dfb['帳票ID'] == tate_dfb['帳票ID'].shift(-i)
                            ) & (tate_dfb['測定日'] == tate_dfb['測定日'].shift(-i))
                    # マスクがTrueの行の'工程'列に1行下の行の'工程'を追加
                    tate_dfb.loc[mask, '工程'] = tate_dfb.loc[mask, '工程'] + \
                        ' / '+tate_dfb['工程'].shift(-i)
                # 結合後、削除
                for i in range(1, 11):
                    mask = (tate_dfb['帳票ID'] == tate_dfb['帳票ID'].shift(i)
                            ) & (tate_dfb['測定日'] == tate_dfb['測定日'].shift(i))
                    tate_dfb = tate_dfb.drop(tate_dfb[mask].index)

                # 未着手と着手を再結合
                tate_df = pd.concat(
                    [tate_dfa, tate_dfb], ignore_index=True)

                # 連番を追加
                # renban_df = tate_df[['帳票ID', 'ロット番号']]
                renban_df = tate_df[['帳票ID', 'ロット番号']]
                renban_df = renban_df.sort_values(['ロット番号', '帳票ID'])
                renban_df = renban_df.drop_duplicates()
                renban_df['連番'] = 1
                # 1から10までループで処理
                for i in range(1, 11):
                    mask = renban_df['ロット番号'] == renban_df['ロット番号'].shift(
                        i - 1)
                    renban_df.loc[mask, '連番'] = i
                tate_df = pd.merge(tate_df, renban_df,
                                   on=['帳票ID', 'ロット番号'], how='left')
                # ソート
                tate_df = tate_df.sort_values(['組立番号', 'ロット番号', '年月次'])

                # チェックシート列を追加
                tate_df['チェックシート'] = tate_df['組立番号'] + " - " + \
                    tate_df['部品名'] + " - " + "<br>" + \
                    tate_df['部番'] + " - " + tate_df['帳票ID'].astype(str) + " - " +\
                    tate_df['連番'].astype(int).astype(str)

                # datatime型を文字列型に変換する
                tate_df['前日'] = tate_df['前日'].dt.strftime('%Y-%m-%d')
                tate_df['測定日'] = tate_df['測定日'].dt.strftime('%Y-%m-%d')
                tate_df = tate_df.fillna('')
                tate_df = tate_df.sort_values(
                    ['チェックシート', '組立番号', 'ロット番号', '年月次'])

                # カスタムカラーを定義
                custom_colors = {
                    "完了": "#7fffd4",
                    "未着手": "#a9a9a9"
                }
                fig = px.timeline(tate_df, range_x=[graph_min_date, graph_max_date], x_start="前日", x_end="測定日",
                                  y="チェックシート", color="状態", text="工程",
                                  color_discrete_map=custom_colors,  # カスタムカラーを指定
                                  category_orders={"チェックシート": tate_df["チェックシート"].drop_duplicates().tolist()})
                fig.update_yaxes(showgrid=True,
                                 gridwidth=56,
                                 gridcolor='#EEFFFF')
                fig.update_layout(
                    barmode="group",
                    plot_bgcolor="#DDDDFF",
                    paper_bgcolor="#EEFFFF",
                    font=dict(family="Arial", size=12, color="black"),
                    hovermode="closest",
                    height=150 + 70 * len(scale_df),
                    xaxis=dict(dtick="D1",  # 1日ごとのティック
                               tickformat="%Y-%m-%d",  # 日付の表示形式
                               showgrid=True,
                               side='top',  # ラベルを上部に配置
                               tickangle=90,  # ラベルを縦向きに回転
                               ),
                    # legend=dict(xanchor='left',
                    #             yanchor='top',
                    #             orientation='h',
                    #             x=-15,
                    #             y=5,
                    #             )
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)

        # タブ２　一覧表示
        with tab2:
            with st.expander('抽出条件'):
                colb1, colb2, colb3, colb4, colb5 = st.columns(
                    [2, 2, 2, 2, 2])
                with colb1:
                    # 組立番号
                    kumi_list = list(set(yoko_df['組立番号'].tolist()))
                    kumi_list.sort()
                    kumi_list.insert(0, "")
                    kumitate = st.selectbox('組立番号　', kumi_list, index=0)
                    if kumitate != '':
                        mdfa1 = yoko_df[yoko_df['組立番号'] == kumitate]
                    else:
                        mdfa1 = yoko_df
                with colb2:
                    # 機種名
                    kisyu_list = list(set(yoko_df['機種名'].tolist()))
                    kisyu_list.sort()
                    kisyu_list.insert(0, "")
                    kisyumei = st.selectbox('機種名　', kisyu_list, index=0)
                    if kisyumei != '':
                        mdfa2 = yoko_df[yoko_df['機種名'] == kisyumei]
                    else:
                        mdfa2 = yoko_df
                with colb3:
                    # 部品名
                    buhin_list = list(set(yoko_df['部品名'].tolist()))
                    buhin_list.sort()
                    buhin_list.insert(0, "")
                    buhinmei = st.selectbox('部品名　', buhin_list, index=0)
                    if buhinmei != '':
                        mdfa3 = yoko_df[yoko_df['部品名'] == buhinmei]
                    else:
                        mdfa3 = yoko_df
                with colb4:
                    # 完成部番
                    buban = st.text_input("部番　", '')
                with colb5:
                    st.write("")
                    syubetsu = st.radio(
                        "検索　", ("前方一致", "部分一致"),  index=1, label_visibility="collapsed")
                    # 完成部番
                    if syubetsu == "前方一致":
                        mdfa4 = yoko_df[yoko_df['部番'].str.startswith(buban)]
                    elif syubetsu == "部分一致":
                        mdfa4 = yoko_df[yoko_df['部番'].str.contains(buban)]
            common_df = mdfa1.copy()
            # 2番目から4番目までのデータフレームと共通行を抽出
            for mdf in [mdfa2, mdfa3, mdfa4]:
                common_df = pd.merge(common_df, mdf, how='inner')
            yoko_df = common_df.copy()
            if yoko_df.empty:
                st.write("表示するデータがありません")
            else:
                yoko_df = yoko_df.sort_values(['組立番号', 'ロット番号', '年月次'])
                yoko_df = yoko_df.drop(columns=['帳票ID', '工程順'])
                st.dataframe(yoko_df, hide_index=True)
    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
