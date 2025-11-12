################################
# 　編機調整報告書                　　　　　　　　　　　　　　　　　　　　　　　
# 　簡易な進捗確認のページ
#  20241209:④SS_WAC_ACT_取付'を削除（範囲が大きいため一部コメントアウト無）
#  20250121:針並べの工程を追加（範囲が大きいため一部コメントアウト無）
################################

# インポート
import streamlit as st
import time
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
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

    # 奇数行と偶数行に対して異なる処理を適用
    def process_row(row):
        row_index = row.name  # 行のインデックスを取得

        # '最終承認入力'が文字列の"2"の場合、数値の2を設定
        if '最終承認入力' in row and row['最終承認入力'] == "2":

            # 奇数行の場合 (0-based indexなのでindex+1が奇数の時)
            if (row_index + 1) % 2 != 0:
                row = row.apply(lambda x: 1 if pd.notnull(x) else 0.05)
            # 偶数行の場合
            else:
                row = row.apply(lambda x: 0.8 if pd.notnull(x) else 0)

            row['最終承認入力'] = 2  # 数値の2をセット

        elif '最終ﾁｪｯｸ入力' in row and row['最終ﾁｪｯｸ入力'] == "2":

           # 奇数行の場合 (0-based indexなのでindex+1が奇数の時)
            if (row_index + 1) % 2 != 0:
                row = row.apply(lambda x: 1 if pd.notnull(x) else 0.05)
            # 偶数行の場合
            else:
                row = row.apply(lambda x: 0.8 if pd.notnull(x) else 0)

            row['最終ﾁｪｯｸ入力'] = 2  # 数値の2をセット

        else:

            # 奇数行の場合 (0-based indexなのでindex+1が奇数の時)
            if (row_index + 1) % 2 != 0:
                row = row.apply(lambda x: 1 if pd.notnull(x) else 0.05)
            # 偶数行の場合
            else:
                row = row.apply(lambda x: 0.8 if pd.notnull(x) else 0)

        return row
    # 奇数行と偶数行に対して異なる処理を適用

    def main():

        st.set_page_config(
            page_title='編機調整報告書_進捗状況確認',
            layout="wide", page_icon='move.gif'
        )

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
    """
        st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

        # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
        dt_now = datetime.now(timezone(timedelta(hours=9))) + \
            timedelta(days=32)  # 日本時刻+32日
        dt_nen = int(dt_now.strftime('%Y'))
        dt_tsuki = int(dt_now.strftime('%m'))

        seisan_col1, seisan_col2, seisan_col3, seisan_col4, seisan_col5 = st.columns([
                                                                                     1, 1, 1, 1, 1])
        with seisan_col1:
            nen = st.selectbox('生産計画年', [dt_nen-1, dt_nen, dt_nen+1], index=1)
        with seisan_col2:
            getsu = st.selectbox('生産計画月', [
                                 '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], index=dt_tsuki-1)
        with seisan_col3:
            ji = st.selectbox(
                '生産計画次', ['', '01', '02', '03', '04', '05', '06', '07', '08'])
        # 追加 前後１次表示 ADD_20241111
        with seisan_col4:
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

                # ADD_20250118_年は西暦4桁
                # s_nenplus = int(str(s_nenplus)[2:4])
                # s_nenminus = int(str(s_nenminus)[2:4])
                s_nenplus = int(s_nenplus)
                s_nenminus = int(s_nenminus)
                s_getsuplus = int(s_getsuplus)
                s_getsuminus = int(s_getsuminus)
                s_jiplus = int(s_jiplus)
                s_jiminus = int(s_jiminus)
        with seisan_col5:
            muki = st.selectbox('進捗向き', ['横', '縦'], index=0)

        # 水平線　自動リフレッシュ時のスクロール戻りを回避できないため、上幅を削減するため削除

        # 更新頻度（５分）
        interval = 300
        placeholder = st.empty()
        fig = go.Figure()

        while True:
            with placeholder.container():
                # irepoDBからデータ取得
                # ADD_20250118_年は西暦4桁
                # snen = int(str(nen)[2:4])
                snen = int(nen)
                sgetsu = int(getsu)
                sji = ji
                if ji == '':
                    sji = ji
                else:
                    sji = int(ji)

        # ADD_20241023分割対応
                sql = f"select top_remarks4 as 組立番号,\
                        cluster_1_11_t as 針並べ,\
                        cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
                        cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
                        cluster_2_26_t as ③針入れ等,\
                        cluster_2_30_t as ④RDSﾁｪｯｸ,\
                        cluster_2_32_t as ⑤慣らし運転,\
                        cluster_2_39_t as ⑥電気ﾁｪｯｸ,\
                        cluster_2_54_t as ⑦ﾔｰﾝｷｬﾘｱ取付,\
                        cluster_2_57_t as ⑧巻取装置,\
                        cluster_2_71_t as ⑨幅出装置,\
                        cluster_2_74_t as ⑩編成作業,\
                        cluster_2_115_t as 作業者合否入力,\
                        cluster_2_130_t as ⑪取付作業,\
                        cluster_2_154_t as ⑫最終確認,\
                        cluster_2_156_t as ⑬調整完了日時,\
                        cluster_2_165_t as 最終ﾁｪｯｸ入力,\
                        cluster_2_166_t as 最終承認入力\
                        from view_report_393 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}' and ('{sji}' = '' or top_remarks3 = '{sji}' )"
                # 追加 ADD_20241111
                if c_flg == 1:
                    sql += f""" or
                    (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
                    (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
                dfs1 = ireporter_data_get(sql)
                sql = f"select top_remarks4 as 組立番号,\
                        cluster_1_11_t as 針並べ,\
                        cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
                        cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
                        cluster_2_26_t as ③針入れ等,\
                        cluster_2_30_t as ④RDSﾁｪｯｸ,\
                        cluster_2_32_t as ⑤慣らし運転,\
                        cluster_2_39_t as ⑥電気ﾁｪｯｸ,\
                        cluster_2_54_t as ⑦ﾔｰﾝｷｬﾘｱ取付,\
                        cluster_2_57_t as ⑧巻取装置,\
                        cluster_2_71_t as ⑨幅出装置,\
                        cluster_2_74_t as ⑩編成作業,\
                        cluster_2_115_t as 作業者合否入力,\
                        cluster_2_130_t as ⑪取付作業,\
                        cluster_2_154_t as ⑫最終確認,\
                        cluster_2_156_t as ⑬調整完了日時,\
                        cluster_2_165_t as 最終ﾁｪｯｸ入力,\
                        cluster_2_166_t as 最終承認入力\
                        from view_report_394 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}' and ('{sji}' = '' or top_remarks3 = '{sji}' )"
                # 追加 ADD_20241111
                if c_flg == 1:
                    sql += f""" or
                    (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
                    (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
                dfs2 = ireporter_data_get(sql)
                sql = f"select top_remarks4 as 組立番号,\
                        cluster_1_11_t as 針並べ,\
                        cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
                        cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
                        cluster_2_26_t as ③針入れ等,\
                        cluster_2_30_t as ④RDSﾁｪｯｸ,\
                        cluster_2_32_t as ⑤慣らし運転,\
                        cluster_2_39_t as ⑥電気ﾁｪｯｸ,\
                        cluster_2_54_t as ⑦ﾔｰﾝｷｬﾘｱ取付,\
                        cluster_2_57_t as ⑧巻取装置,\
                        cluster_2_71_t as ⑨幅出装置,\
                        cluster_2_74_t as ⑩編成作業,\
                        cluster_2_115_t as 作業者合否入力,\
                        cluster_2_130_t as ⑪取付作業,\
                        cluster_2_154_t as ⑫最終確認,\
                        cluster_2_156_t as ⑬調整完了日時,\
                        cluster_2_165_t as 最終ﾁｪｯｸ入力,\
                        cluster_2_166_t as 最終承認入力\
                        from view_report_395 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}' and ('{sji}' = '' or top_remarks3 = '{sji}' )"
                # 追加 ADD_20241111
                if c_flg == 1:
                    sql += f""" or
                    (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
                    (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
                dfs3 = ireporter_data_get(sql)
                sql = f"select top_remarks4 as 組立番号,\
                        cluster_1_11_t as 針並べ,\
                        cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
                        cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
                        cluster_2_26_t as ③針入れ等,\
                        cluster_2_30_t as ④RDSﾁｪｯｸ,\
                        cluster_2_32_t as ⑤慣らし運転,\
                        cluster_2_39_t as ⑥電気ﾁｪｯｸ,\
                        cluster_2_54_t as ⑦ﾔｰﾝｷｬﾘｱ取付,\
                        cluster_2_57_t as ⑧巻取装置,\
                        cluster_2_71_t as ⑨幅出装置,\
                        cluster_2_74_t as ⑩編成作業,\
                        cluster_2_115_t as 作業者合否入力,\
                        cluster_2_130_t as ⑪取付作業,\
                        cluster_2_154_t as ⑫最終確認,\
                        cluster_2_156_t as ⑬調整完了日時,\
                        cluster_2_165_t as 最終ﾁｪｯｸ入力,\
                        cluster_2_166_t as 最終承認入力\
                        from view_report_396 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}' and ('{sji}' = '' or top_remarks3 = '{sji}' )"
                # 追加 ADD_20241111
                if c_flg == 1:
                    sql += f""" or
                    (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
                    (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
                dfs4 = ireporter_data_get(sql)
                sql = f"select top_remarks4 as 組立番号,\
                        cluster_1_11_t as 針並べ,\
                        cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
                        cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
                        cluster_2_26_t as ③針入れ等,\
                        cluster_2_30_t as ④RDSﾁｪｯｸ,\
                        cluster_2_32_t as ⑤慣らし運転,\
                        cluster_2_39_t as ⑥電気ﾁｪｯｸ,\
                        cluster_2_54_t as ⑦ﾔｰﾝｷｬﾘｱ取付,\
                        cluster_2_57_t as ⑧巻取装置,\
                        cluster_2_71_t as ⑨幅出装置,\
                        cluster_2_74_t as ⑩編成作業,\
                        cluster_2_115_t as 作業者合否入力,\
                        cluster_2_130_t as ⑪取付作業,\
                        cluster_2_154_t as ⑫最終確認,\
                        cluster_2_156_t as ⑬調整完了日時,\
                        cluster_2_165_t as 最終ﾁｪｯｸ入力,\
                        cluster_2_166_t as 最終承認入力\
                        from view_report_397 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}' and ('{sji}' = '' or top_remarks3 = '{sji}' )"
                # 追加 ADD_20241111
                if c_flg == 1:
                    sql += f""" or
                    (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
                    (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
                dfs5 = ireporter_data_get(sql)
                sql = f"select top_remarks4 as 組立番号,\
                        cluster_1_11_t as 針並べ,\
                        cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
                        cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
                        cluster_2_26_t as ③針入れ等,\
                        cluster_2_30_t as ④RDSﾁｪｯｸ,\
                        cluster_2_32_t as ⑤慣らし運転,\
                        cluster_2_39_t as ⑥電気ﾁｪｯｸ,\
                        cluster_2_54_t as ⑦ﾔｰﾝｷｬﾘｱ取付,\
                        cluster_2_57_t as ⑧巻取装置,\
                        cluster_2_71_t as ⑨幅出装置,\
                        cluster_2_74_t as ⑩編成作業,\
                        cluster_2_115_t as 作業者合否入力,\
                        cluster_2_130_t as ⑪取付作業,\
                        cluster_2_154_t as ⑫最終確認,\
                        cluster_2_156_t as ⑬調整完了日時,\
                        cluster_2_165_t as 最終ﾁｪｯｸ入力,\
                        cluster_2_166_t as 最終承認入力\
                        from view_report_398 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}' and ('{sji}' = '' or top_remarks3 = '{sji}' )"
                # 追加 ADD_20241111
                if c_flg == 1:
                    sql += f""" or
                    (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
                    (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
                dfs6 = ireporter_data_get(sql)

                df = pd.concat(
                    [dfs1, dfs2, dfs3, dfs4, dfs5, dfs6], ignore_index=True)
                df = df[['組立番号', '針並べ', '①ｶﾑﾎﾙﾀﾞｰ取付', '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ', '③針入れ等', '④rdsﾁｪｯｸ', '⑤慣らし運転', '⑥電気ﾁｪｯｸ', '⑦ﾔｰﾝｷｬﾘｱ取付',
                         '⑧巻取装置', '⑨幅出装置', '⑩編成作業',  '⑪取付作業', '⑫最終確認', '⑬調整完了日時', '作業者合否入力', '最終ﾁｪｯｸ入力', '最終承認入力']]

                # sqlの結果が空なら抜ける
                if df.empty:
                    st.write('対象月のデータがありません')
                    break

                # ソートするならここになる
                df = df.sort_values(['組立番号'])  # ADD_20240904sortに部番を追加

                # 進捗確認は逆順（縦の場合は元の順番）
                if muki == '横':
                    # ADD_20240904sortに部番を追加
                    df = df.sort_values(['組立番号'], ascending=False)
                df = df.reset_index()  # インデックスを振り直しておく

                # 組立番号配列
                array_A = df['組立番号'].to_numpy().tolist()
                # 作業工程配列
                # array_B = ['①ｶﾑﾎﾙﾀﾞｰ取付','②ﾀｲﾐﾝｸﾞ/ｹﾞｰﾃｨﾝｸﾞ','③針入れ等','④SS_WAC_ACT_取付','⑤RDSﾁｪｯｸ','⑥慣らし運転','⑦電気ﾁｪｯｸ','⑧ﾔｰﾝｷｬﾘｱ取付','⑨巻取装置','⑩幅出装置','⑪編成作業','作業者合否入力','⑫取付作業','⑬最終確認','⑭調整完了日時','最終ﾁｪｯｸ入力','最終承認入力']
                # array_B = ['①ｶﾑﾎﾙﾀﾞｰ取付', '②ﾀｲﾐﾝｸﾞ/ｹﾞｰﾃｨﾝｸﾞ', '③針入れ等', '④RDSﾁｪｯｸ', '⑤慣らし運転', '⑥電気ﾁｪｯｸ', '⑦ﾔｰﾝｷｬﾘｱ取付', ADD_20250121_針並べ追加
                array_B = ['針並べ', '①ｶﾑﾎﾙﾀﾞｰ取付', '②ﾀｲﾐﾝｸﾞ/ｹﾞｰﾃｨﾝｸﾞ', '③針入れ等', '④RDSﾁｪｯｸ', '⑤慣らし運転', '⑥電気ﾁｪｯｸ', '⑦ﾔｰﾝｷｬﾘｱ取付',
                           # '⑧巻取装置', '⑨幅出装置', '⑩編成作業', '作業者合否入力', '⑪取付作業', '⑫最終確認', '⑬調整完了日時', '最終ﾁｪｯｸ入力', '最終承認入力']　#DEL_20250109_表示順入れ替え
                           # ADD_20250109_表示順入れ替え
                           '⑧巻取装置', '⑨幅出装置', '⑩編成作業',  '⑪取付作業', '⑫最終確認', '⑬調整完了日時', '作業者合否入力', '最終ﾁｪｯｸ入力', '最終承認入力']

                # apply関数を行方向に適用 nullは0か0.05，値有りは1か0.8が格納される。
                df1 = df.apply(process_row, axis=1)

                # ラベル数を取得
                A_labels = len(array_A)
                B_labels = len(array_B)

                # 図の表示タイトル
                dt_now = datetime.now(timezone(timedelta(hours=9)))
                if ji == '':
                    graph_ji = '全次'
                else:
                    graph_ji = str(int(ji)) + '次'

                if muki == '縦':
                    # 縦表示
                    header = array_A
                    rows = array_B
                    values = [df1['針並べ'].to_numpy().tolist(),  # ADD_20250121_針並べ追加
                              df1['①ｶﾑﾎﾙﾀﾞｰ取付'].to_numpy().tolist(),
                              df1['②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ'].to_numpy().tolist(),
                              df1['③針入れ等'].to_numpy().tolist(),
                              # df1['④ss_wac_act_取付'].to_numpy().tolist(), #小文字でないとエラーになる
                              # 小文字でないとエラーになる
                              df1['④rdsﾁｪｯｸ'].to_numpy().tolist(),
                              df1['⑤慣らし運転'].to_numpy().tolist(),
                              df1['⑥電気ﾁｪｯｸ'].to_numpy().tolist(),
                              df1['⑦ﾔｰﾝｷｬﾘｱ取付'].to_numpy().tolist(),
                              df1['⑧巻取装置'].to_numpy().tolist(),
                              df1['⑨幅出装置'].to_numpy().tolist(),
                              df1['⑩編成作業'].to_numpy().tolist(),
                              # df1['作業者合否入力'].to_numpy().tolist(), #DEL_20250109_表示順入れ替え
                              df1['⑪取付作業'].to_numpy().tolist(),
                              df1['⑫最終確認'].to_numpy().tolist(),
                              df1['⑬調整完了日時'].to_numpy().tolist(),
                              # ADD_20250109_表示順入れ替え
                              df1['作業者合否入力'].to_numpy().tolist(),
                              df1['最終ﾁｪｯｸ入力'].to_numpy().tolist(),
                              df1['最終承認入力'].to_numpy().tolist()]
                    # 縦マトリクス図を作成
                    fig = go.Figure(data=go.Heatmap(
                        z=values,
                        x=header,
                        y=rows,
                        # colorscale='Blues',
                        colorscale=[
                            [0, '#F7FbFF'],   # 0: 白
                            [1/3, '#09306B'],  # 1: 青
                            [2/3, '#F4D800'],  # 2: 薄黄色
                            [1, '#808080']    # 3: 灰色
                        ],
                        showscale=False,  # カラーバーを非表示にする
                        zmin=0,         # 重要　最小値を固定で設定
                        # zmax=1,          # 重要　最大値を固定で設定
                        zmax=3,          # 重要　最大値を固定で設定
                        xgap=0,  # X軸のセル間に隙間を追加
                        ygap=4   # Y軸のセル間に隙間を追加
                    ))

                    fig.update_layout(title=f'{nen}年{getsu}月{graph_ji}　最終更新時：' + dt_now.strftime('%Y年%m月%d日　%H時%M分'),
                                      autosize=False,  # 自動サイズ調整を無効化)
                                      width=A_labels*1000,        # 図の幅を調整
                                      height=B_labels*25+200        # 図の高さを調整
                                      )
                    # fig.update_xaxes(tickangle=90)

                elif muki == '横':
                    # 横表示
                    header = array_B
                    rows = array_A
                    values = []

                    for n, row in df1.iterrows():
                        l = df1.iloc[n].to_numpy().tolist()  # 行をリストとして取得
                        l.pop(0)  # 最初はふり直したインデックスなので不要（popして削除）
                        l.pop(0)  # 次は組番なので不要（popして削除）
                        values.append(l)

                    # 横マトリクス図を作成
                    fig = go.Figure(data=go.Heatmap(
                        z=values,
                        x=header,
                        y=rows,
                        # colorscale='Blues',
                        colorscale=[
                            [0, '#F7FbFF'],   # 0: 白
                            [1/3, '#09306B'],  # 1: 青
                            [2/3, '#F4D800'],  # 2: 薄黄色
                            [1, '#808080']    # 3: 灰色
                        ],
                        showscale=False,  # カラーバーを非表示にする
                        zmin=0,         # 重要　最小値を固定で設定
                        # zmax=1,          # 重要　最大値を固定で設定
                        zmax=3,          # 重要　最大値を固定で設定
                        xgap=4,  # X軸のセル間に隙間を追加
                        ygap=0   # Y軸のセル間に隙間を追加
                    ))

                    fig.update_layout(title=f'{nen}年{getsu}月{graph_ji}　最終更新時：' + dt_now.strftime('%Y年%m月%d日　%H時%M分'),
                                      autosize=False,  # 自動サイズ調整を無効化)
                                      width=B_labels*1000,        # 図の幅を調整
                                      height=A_labels*25+200        # 図の高さを調整
                                      )
                    # fig.update_xaxes(tickangle=90)

                # 処理
                # st.write('## 編機調整作業進捗状況') 自動リフレッシュ時のスクロール戻りを回避できないため、上幅を削減するため削除

                # Streamlit上で表示
                # コンテナ幅を自動調整 不要？
                st.plotly_chart(fig, use_container_width=True)

                st.write('※５分に１度自動更新')

                # 5分待機
                time.sleep(interval)

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
