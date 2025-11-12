################################
# 　編機調整報告書                #
# 　簡単なDF表示のページ          #
#  20241209:④SS_WAC_ACT_取付'を削除（範囲が大きいため一部コメントアウト無）
#  20250121:針並べの工程を追加（範囲が大きいため一部コメントアウト無）
################################
# インポート
import streamlit as st
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
import sqlite3
import os
import shutil
import plotly.express as px

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

    def db_update(df):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_amikityousei.db")

        # 本処理（更新処理）
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする（編機以外にも使用できる項目名）
        cur.execute('CREATE TABLE IF NOT EXISTS task_completion_date(\
                  ID INTEGER PRIMARY KEY,\
                  組立番号 TEXT,\
                  項目ID INTEGER,\
                  履歴番号 INTEGER,\
                  作業者 TEXT,\
                  更新日付 TEXT\
                  )')

        # データフレームの編集
        df1 = df[['組立番号', '①ｶﾑﾎﾙﾀﾞｰ取付']].rename(columns={'①ｶﾑﾎﾙﾀﾞｰ取付': '作業者'})
        df1['項目ID'] = 1
        df2 = df[['組立番号', '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ']].rename(
            columns={'②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ': '作業者'})
        df2['項目ID'] = 2
        df3 = df[['組立番号', '③針入れ等']].rename(columns={'③針入れ等': '作業者'})
        df3['項目ID'] = 3
        # df4 = df[['組立番号','④ss_wac_act_取付']].rename(columns={'④ss_wac_act_取付':'作業者'}) DEL_20241209
        # df4['項目ID'] = 4
        df5 = df[['組立番号', '④rdsﾁｪｯｸ']].rename(columns={'④rdsﾁｪｯｸ': '作業者'})
        df5['項目ID'] = 5
        df6 = df[['組立番号', '⑤慣らし運転']].rename(columns={'⑤慣らし運転': '作業者'})
        df6['項目ID'] = 6
        df7 = df[['組立番号', '⑥電気ﾁｪｯｸ']].rename(columns={'⑥電気ﾁｪｯｸ': '作業者'})
        df7['項目ID'] = 7
        df8 = df[['組立番号', '⑦ﾔｰﾝｷｬﾘｱ取付']].rename(columns={'⑦ﾔｰﾝｷｬﾘｱ取付': '作業者'})
        df8['項目ID'] = 8
        df9 = df[['組立番号', '⑧巻取装置']].rename(columns={'⑧巻取装置': '作業者'})
        df9['項目ID'] = 9
        df10 = df[['組立番号', '⑨幅出装置']].rename(columns={'⑨幅出装置': '作業者'})
        df10['項目ID'] = 10
        df11 = df[['組立番号', '⑩編成作業']].rename(columns={'⑩編成作業': '作業者'})
        df11['項目ID'] = 11
        df12 = df[['組立番号', '作業者合否入力']].rename(columns={'作業者合否入力': '作業者'})
        df12['項目ID'] = 12
        df13 = df[['組立番号', '⑪取付作業']].rename(columns={'⑪取付作業': '作業者'})
        df13['項目ID'] = 13
        df14 = df[['組立番号', '⑫最終確認']].rename(columns={'⑫最終確認': '作業者'})
        df14['項目ID'] = 14
        df15 = df[['組立番号', '最終ﾁｪｯｸ入力']].rename(columns={'最終ﾁｪｯｸ入力': '作業者'})
        df15['項目ID'] = 15
        df16 = df[['組立番号', '最終承認入力']].rename(columns={'最終承認入力': '作業者'})
        df16['項目ID'] = 16
        df17 = df[['組立番号', '⑬調整完了日時']].rename(columns={'⑬調整完了日時': '作業者'})
        df17['項目ID'] = 17
        df18 = df[['組立番号', '針並べ']].rename(columns={'針並べ': '作業者'})
        df18['項目ID'] = 18
        # merged_df = pd.concat([df1, df2, df3, df4, df5, df6, df7, df8, df9, df10,
        merged_df = pd.concat([df1, df2, df3, df5, df6, df7, df8, df9, df10,
                               # df11, df12, df13, df14, df15, df16, df17], ignore_index=True) DEL_20250121_針並べ追加
                               df11, df12, df13, df14, df15, df16, df17, df18], ignore_index=True)  # ADD_20250121_針並べ追加
        merged_df['更新日付'] = dt_now.strftime('%Y-%m-%d')

        # 各行に対して更新処理を行う
        for _, row in merged_df.iterrows():
            # 組立番号が既に存在するか確認
            cur.execute(
                "SELECT 履歴番号, 作業者 FROM task_completion_date WHERE 組立番号 = ? AND 項目ID = ? ORDER BY 履歴番号 DESC LIMIT 1", (row['組立番号'], row['項目ID']))
            existing_records = cur.fetchall()

            if not existing_records:
                # 条件1: 組立番号が重複していない場合、INSERT
                cur.execute("""
              INSERT INTO task_completion_date (組立番号, 項目ID, 履歴番号, 作業者, 更新日付)
              VALUES (?, ?, ?, ?, ?)
          """, (row['組立番号'], row['項目ID'], 1, row['作業者'], row['更新日付']))
            else:
                # 条件2と条件3: 組立番号が重複している場合
                # 既存の履歴番号と作業者を取得
                current_history, existing_worker = existing_records[0]
                # if existing_worker == row['作業者'] or existing_worker is None:
                if existing_worker != row['作業者']:
                    if existing_worker is None or existing_worker == '':
                        # 元の作業者がNone or 空欄の場合UPDATE
                        cur.execute("""
                  UPDATE task_completion_date
                  SET 更新日付 = ? ,作業者 = ?
                  WHERE 組立番号 = ? AND 項目ID = ?
              """, (row['更新日付'], row['作業者'], row['組立番号'], row['項目ID']))
                    else:
                        # 作業者が異なる場合、履歴番号を+1してINSERT
                        new_history_number = current_history + 1
                        cur.execute("""
                  INSERT INTO task_completion_date (組立番号, 項目ID, 履歴番号, 作業者, 更新日付)
                  VALUES (?, ?, ?, ?, ?)
              """, (row['組立番号'], row['項目ID'], new_history_number, row['作業者'], row['更新日付']))

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()

    def main():

        st.set_page_config(
            page_title='編機調整報告書_作業者データ一覧',
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
                                 '', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], index=dt_tsuki-1)
        with seisan_col3:
            if getsu == '':
                ji = ''
            else:
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
        # 水平線
        # st.divider()  進捗確認に合わせて削除

        # irepoDBからデータ取得
        # ADD_20250118_年は西暦4桁
        # snen = int(str(nen)[2:4])
        snen = int(nen)
        if getsu == '':
            sgetsu = getsu
        else:
            sgetsu = int(getsu)

        if ji == '':
            sji = ji
        else:
            sji = int(ji)

        # ADD_20241023分割対応
        sql = f"select top_remarks4 as 組立番号,\
                cluster_2_6_t as 機種名,\
                cluster_2_7_t as インチ,\
                cluster_2_8_t as ゲージ,\
                cluster_2_1_n as 年,\
                cluster_2_2_n as 月,\
                cluster_2_3_n as 次,\
                cluster_2_5_t as 国名出荷先,\
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
                from view_report_393 where (top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' ))"
        # 追加 ADD_20241111
        if c_flg == 1:
            sql += f""" or
            (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
            (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
        df1 = ireporter_data_get(sql)
        sql = f"select top_remarks4 as 組立番号,\
                cluster_2_6_t as 機種名,\
                cluster_2_7_t as インチ,\
                cluster_2_8_t as ゲージ,\
                cluster_2_1_n as 年,\
                cluster_2_2_n as 月,\
                cluster_2_3_n as 次,\
                cluster_2_5_t as 国名出荷先,\
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
                from view_report_394 where (top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' ))"
        # 追加 ADD_20241111
        if c_flg == 1:
            sql += f""" or
            (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
            (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
        df2 = ireporter_data_get(sql)

        sql = f"select top_remarks4 as 組立番号,\
                cluster_2_6_t as 機種名,\
                cluster_2_7_t as インチ,\
                cluster_2_8_t as ゲージ,\
                cluster_2_1_n as 年,\
                cluster_2_2_n as 月,\
                cluster_2_3_n as 次,\
                cluster_2_5_t as 国名出荷先,\
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
                from view_report_395 where (top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' ))"
        # 追加 ADD_20241111
        if c_flg == 1:
            sql += f""" or
            (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
            (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
        df3 = ireporter_data_get(sql)
        sql = f"select top_remarks4 as 組立番号,\
                cluster_2_6_t as 機種名,\
                cluster_2_7_t as インチ,\
                cluster_2_8_t as ゲージ,\
                cluster_2_1_n as 年,\
                cluster_2_2_n as 月,\
                cluster_2_3_n as 次,\
                cluster_2_5_t as 国名出荷先,\
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
                from view_report_396 where (top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' ))"
        # 追加 ADD_20241111
        if c_flg == 1:
            sql += f""" or
            (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
            (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
        df4 = ireporter_data_get(sql)

        sql = f"select top_remarks4 as 組立番号,\
                cluster_2_6_t as 機種名,\
                cluster_2_7_t as インチ,\
                cluster_2_8_t as ゲージ,\
                cluster_2_1_n as 年,\
                cluster_2_2_n as 月,\
                cluster_2_3_n as 次,\
                cluster_2_5_t as 国名出荷先,\
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
                from view_report_397 where (top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' ))"
        # 追加 ADD_20241111
        if c_flg == 1:
            sql += f""" or
            (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
            (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
        df5 = ireporter_data_get(sql)

        sql = f"select top_remarks4 as 組立番号,\
                cluster_2_6_t as 機種名,\
                cluster_2_7_t as インチ,\
                cluster_2_8_t as ゲージ,\
                cluster_2_1_n as 年,\
                cluster_2_2_n as 月,\
                cluster_2_3_n as 次,\
                cluster_2_5_t as 国名出荷先,\
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
                from view_report_398 where (top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' ))"
        # 追加 ADD_20241111
        if c_flg == 1:
            sql += f""" or
            (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or
            (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}') """
        df6 = ireporter_data_get(sql)

        df = pd.concat([df1, df2, df3, df4, df5, df6], ignore_index=True)

        db_update(df)

        file = os.path.dirname(os.path.dirname(__file__)) + \
            f'\\Database\\'+'amikityousei.db'
        sql = 'select * from task_completion_date'
        amikityousei_df = sqlite_data_get(sql, file)

        # sqlの結果が空なら抜ける
        if df.empty:
            st.write('対象月のデータがありません')
        else:
            # dataframeの加工

            # 出荷先の分解　国名　　　客先名となっている
            df.insert(7, '出荷先', '')
            df.insert(7, '国名', '')
            df['国名出荷先'] = df['国名出荷先'].fillna('　　　')  # Noneデータ対策
            df = df.fillna('')  # Noneデータ対策
            df[['国名', '出荷先']] = df['国名出荷先'].str.split('　　　', expand=True)
            df = df.drop('国名出荷先', axis=1)
            df['年'] = df['年'].fillna(0).astype(int).astype(str)

            # ADD_20250312_吋ゲージの数値処理追加
            mask = (df['インチ'] != '') & df['インチ'].apply(
                lambda x: float(x).is_integer() if x != '' else False)
            df.loc[mask, 'インチ'] = df.loc[mask, 'インチ'].apply(
                lambda x: str(int(float(x))))
            mask = (df['ゲージ'] != '') & df['ゲージ'].apply(
                lambda x: float(x).is_integer() if x != '' else False)
            df.loc[mask, 'ゲージ'] = df.loc[mask, 'ゲージ'].apply(
                lambda x: str(int(float(x))))

            # ADD_20250109_最終ﾁｪｯｸ入力の表示変更
            df['最終ﾁｪｯｸ入力'] = df['最終ﾁｪｯｸ入力'].str.replace('2', '申請中')
            df['最終ﾁｪｯｸ入力'] = df['最終ﾁｪｯｸ入力'].str.replace('4', '承認済み')

            # 最終承認入力の表示変更
            # df['最終承認入力'] = df['最終承認入力'].str.replace(None, '未申請') #文字列ではないのでstrでは置き換えられない ilocでやるのが正解だが、NoneのままでOKでは？
            df['最終承認入力'] = df['最終承認入力'].str.replace('2', '申請中')
            df['最終承認入力'] = df['最終承認入力'].str.replace('4', '承認済み')
            # ソート
            df = df.sort_values(['月', '次', '組立番号'])  # ADD_20240904sortに部番を追加

            # データフレームを表示（インデックスは非表示）
            # st.dataframe(df,hide_index=True)

            # 更新日付DFの作成　ADD_20241112
            # ID、組立番号、項目IDでグループ化し、履歴番号が最大の行を取得
            idx = amikityousei_df.groupby(['組立番号', '項目ID'])['履歴番号'].idxmax()
            date_df = amikityousei_df.loc[idx]
            # date_df[['①ｶﾑﾎﾙﾀﾞｰ取付_日','②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ_日','③針入れ等_日','④ss_wac_act_取付_日','⑤rdsﾁｪｯｸ_日','⑥慣らし運転_日','⑦電気ﾁｪｯｸ_日','⑧ﾔｰﾝｷｬﾘｱ取付_日','⑨巻取装置_日','⑩幅出装置_日',
            # date_df[['①ｶﾑﾎﾙﾀﾞｰ取付_日', '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ_日', '③針入れ等_日', '④rdsﾁｪｯｸ_日', '⑤慣らし運転_日', '⑥電気ﾁｪｯｸ_日', '⑦ﾔｰﾝｷｬﾘｱ取付_日', '⑧巻取装置_日', '⑨幅出装置_日',# DEL_20250121_針並べ追加
            date_df[['針並べ_日', '①ｶﾑﾎﾙﾀﾞｰ取付_日', '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ_日', '③針入れ等_日', '④rdsﾁｪｯｸ_日', '⑤慣らし運転_日', '⑥電気ﾁｪｯｸ_日', '⑦ﾔｰﾝｷｬﾘｱ取付_日', '⑧巻取装置_日', '⑨幅出装置_日',  # ADD_20250121_針並べ追加
                    # '⑩編成作業_日', '作業者合否入力_日', '⑪取付作業_日', '⑫最終確認_日', '最終ﾁｪｯｸ入力_日', '最終承認入力_日']] = ''
                     '⑩編成作業_日', '作業者合否入力_日', '⑪取付作業_日', '⑫最終確認_日', '最終ﾁｪｯｸ入力_日', '最終承認入力_日', '⑬調整完了日時_日']] = ''

            # 条件に従って date_df を更新
            for index, row in date_df.iterrows():
                if row['項目ID'] == 1 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] == row['組立番号'],
                                '①ｶﾑﾎﾙﾀﾞｰ取付_日'] = row['更新日付']
                elif row['項目ID'] == 2 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] == row['組立番号'],
                                '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ_日'] = row['更新日付']
                elif row['項目ID'] == 3 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '③針入れ等_日'] = row['更新日付']
                # elif row['項目ID'] == 4 and row['作業者'] != None:
                #  date_df.loc[date_df['組立番号'] == row['組立番号'], 'ss_wac_act_取付_日'] = row['更新日付']
                elif row['項目ID'] == 5 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] == row['組立番号'],
                                '④rdsﾁｪｯｸ_日'] = row['更新日付']
                elif row['項目ID'] == 6 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑤慣らし運転_日'] = row['更新日付']
                elif row['項目ID'] == 7 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑥電気ﾁｪｯｸ_日'] = row['更新日付']
                elif row['項目ID'] == 8 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] == row['組立番号'],
                                '⑦ﾔｰﾝｷｬﾘｱ取付_日'] = row['更新日付']
                elif row['項目ID'] == 9 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑧巻取装置_日'] = row['更新日付']
                elif row['項目ID'] == 10 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑨幅出装置_日'] = row['更新日付']
                elif row['項目ID'] == 11 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑩編成作業_日'] = row['更新日付']
                elif row['項目ID'] == 12 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '作業者合否入力_日'] = row['更新日付']
                elif row['項目ID'] == 13 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑪取付作業_日'] = row['更新日付']
                elif row['項目ID'] == 14 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑫最終確認_日'] = row['更新日付']
                elif row['項目ID'] == 15 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] == row['組立番号'],
                                '最終ﾁｪｯｸ入力_日'] = row['更新日付']
                elif row['項目ID'] == 16 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '最終承認入力_日'] = row['更新日付']
                elif row['項目ID'] == 17 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==
                                row['組立番号'], '⑬調整完了日時_日'] = row['更新日付']
                # ADD_20250121_針並べ追加
                elif row['項目ID'] == 18 and row['作業者'] != None:
                    date_df.loc[date_df['組立番号'] ==                                       # ADD_20250121_針並べ追加
                                # ADD_20250121_針並べ追加
                                row['組立番号'], '針並べ_日'] = row['更新日付']

            idx = date_df.groupby(['組立番号'])['履歴番号'].idxmax()
            date_df = date_df.loc[idx]

            merged_df = pd.merge(df, date_df, left_on=[
                                 '組立番号'], right_on=['組立番号'], how='left')

            # # merged_df = merged_df[['組立番号', '機種名', 'インチ', 'ゲージ', '年', '月', '次', '国名', '出荷先', '①ｶﾑﾎﾙﾀﾞｰ取付',# DEL_20250121_針並べ追加
            # merged_df = merged_df[['組立番号', '機種名', 'インチ', 'ゲージ', '年', '月', '次', '国名', '出荷先', '針並べ', '針並べ_日', '①ｶﾑﾎﾙﾀﾞｰ取付',  # ADD_20250121_針並べ追加
            #                       '①ｶﾑﾎﾙﾀﾞｰ取付_日', '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ', '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ_日', '③針入れ等', '③針入れ等_日',
            #                        '④rdsﾁｪｯｸ', '④rdsﾁｪｯｸ_日', '⑤慣らし運転',
            #                        '⑤慣らし運転_日', '⑥電気ﾁｪｯｸ', '⑥電気ﾁｪｯｸ_日', '⑦ﾔｰﾝｷｬﾘｱ取付', '⑦ﾔｰﾝｷｬﾘｱ取付_日', '⑧巻取装置',
            #                        '⑧巻取装置_日', '⑨幅出装置', '⑨幅出装置_日', '⑩編成作業', '⑩編成作業_日',
            #                        # '⑪取付作業', '⑪取付作業_日', '作業者合否入力', '作業者合否入力_日',  '⑫最終確認', '⑫最終確認_日', '最終ﾁｪｯｸ入力',
            #                        '⑪取付作業', '⑪取付作業_日',  '⑫最終確認', '⑫最終確認_日', '⑬調整完了日時', '⑬調整完了日時_日', '作業者合否入力', '作業者合否入力_日', '最終ﾁｪｯｸ入力',
            #                        '最終ﾁｪｯｸ入力_日', '最終承認入力', '最終承認入力_日']]
            merged_df = merged_df[['組立番号', '機種名', 'インチ', 'ゲージ', '年', '月', '次', '国名', '出荷先', '針並べ',  '①ｶﾑﾎﾙﾀﾞｰ取付',  # ADD_20250121_針並べ追加
                                   '②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ', '③針入れ等', '④rdsﾁｪｯｸ', '⑤慣らし運転', '⑥電気ﾁｪｯｸ', '⑦ﾔｰﾝｷｬﾘｱ取付', '⑧巻取装置',
                                   '⑨幅出装置', '⑩編成作業',  '⑪取付作業', '⑫最終確認', '⑬調整完了日時', '作業者合否入力', '最終ﾁｪｯｸ入力', '最終承認入力', ]]

            # データフレームを表示（インデックスは非表示）
            st.dataframe(merged_df, hide_index=True)

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
