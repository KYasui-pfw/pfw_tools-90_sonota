################################
# 　編機調整報告書              #
# 　編組織名、使用糸入力のページ   #
################################
# インポート
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
import sqlite3
import os
import shutil

try:
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

    def db_set1():

        # 本処理（更新処理）
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        # 編組織名テーブル作成
        cur.execute('''CREATE TABLE IF NOT EXISTS shiteigara(
                  ID INTEGER PRIMARY KEY,
                  表示順 INTEGER ,
                  編組織名 TEXT,
                  詳細 TEXT,
                  UNIQUE (編組織名,詳細)
                  )''')

        # データベースの値を取得する
        sql1 = f'select * from shiteigara'
        df1 = sqlite_data_get(sql1, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\amikityousei.db')

        # 表示順（とID）で並び替え
        df1 = df1.sort_values(['表示順', 'ID'])

        return (df1)

    def db_set2():

        # 本処理（更新処理）
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        # 編組織名に紐づくパターンテーブルを作成
        cur.execute('''CREATE TABLE IF NOT EXISTS shiteigara_pattern(
                  ID INTEGER PRIMARY KEY,
                  rID INTEGER,
                  表示順 INTEGER ,
                  編組織パターン TEXT,
                  UNIQUE (編組織パターン)
                  )''')

        # データベースの値を取得する
        sql2 = f'select * from shiteigara_pattern'
        df2 = sqlite_data_get(sql2, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\amikityousei.db')

        # 表示順（とID）で並び替え
        df2 = df2.sort_values(['表示順', 'ID'])

        return (df2)

    def db_set3():

        # 本処理（更新処理）
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        # 使用糸テーブルを作成
        cur.execute('''CREATE TABLE IF NOT EXISTS shiyouito(
                  ID INTEGER PRIMARY KEY,
                  表示順 INTEGER ,
                  使用糸 TEXT,
                  UNIQUE (使用糸)
                  )''')

        # データベースの値を取得する
        sql3 = f'select * from shiyouito'
        df3 = sqlite_data_get(sql3, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\amikityousei.db')

        # 表示順（とID）で並び替え
        df3 = df3.sort_values(['表示順', 'ID'])

        return (df3)

    def db_update1(edf, df, tablename):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_amikityousei.db")

        # 本処理
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 削除操作
        original_ids = set(zip(df["編組織名"],df["詳細"]))
        edited_ids = set(zip(edf["編組織名"],df["詳細"]))
        
        ids_to_delete = original_ids - edited_ids
        for id_to_delete1,id_to_delete2 in ids_to_delete:
            cur.execute(f"DELETE FROM {tablename} WHERE 編組織名 = ? AND 詳細 = ?", (id_to_delete1,id_to_delete2))

        # 更新操作
        for _, row in edf.iterrows():

            if row["詳細"] is not None:
                shousai = row["詳細"]
            else:
                shousai = "　"
                
            if row["編組織名"] is not None:
                cur.execute(
                    """
                    INSERT INTO shiteigara ( 表示順, 編組織名,詳細)
                    VALUES (?, ?, ?)
                    ON CONFLICT(編組織名,詳細) DO UPDATE SET
                    表示順 = excluded.表示順,
                    編組織名 = excluded.編組織名,
                    詳細 = excluded.詳細
                    """,
                    (row["表示順"], row["編組織名"], shousai),
                )
        conn.commit()

    def db_update2(edf, df, rid, tablename):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_amikityousei.db")

        # 本処理
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 削除操作
        df = df[df['rID'] == rid]
        original_ids = set(df["編組織パターン"])
        edited_ids = set(edf["編組織パターン"])
        ids_to_delete = original_ids - edited_ids
        for id_to_delete in ids_to_delete:
            cur.execute(f"DELETE FROM {
                        tablename} WHERE 編組織パターン = ?", (id_to_delete,))

        # 更新操作
        edf['rID'] = rid
        for _, row in edf.iterrows():
            if row["編組織パターン"] is not None:
                cur.execute(
                    """
                    INSERT INTO shiteigara_pattern (rID, 表示順, 編組織パターン)
                    VALUES ( ?,?, ?)
                    ON CONFLICT(編組織パターン) DO UPDATE SET
                    表示順 = excluded.表示順,
                    rID = excluded.rID,
                    編組織パターン = excluded.編組織パターン
                    """,
                    (row["rID"], row["表示順"], row["編組織パターン"]),
                )
        conn.commit()

    def db_update3(edf, df, tablename):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_amikityousei.db")

        # 本処理
        dbname = 'amikityousei.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 削除操作
        original_ids = set(df["使用糸"])
        edited_ids = set(edf["使用糸"])
        ids_to_delete = original_ids - edited_ids
        for id_to_delete in ids_to_delete:
            cur.execute(f"DELETE FROM {
                        tablename} WHERE 使用糸 = ?", (id_to_delete,))

        # 更新操作
        for _, row in edf.iterrows():
            if row["使用糸"] is not None:
                cur.execute(
                    """
                    INSERT INTO shiyouito ( 表示順, 使用糸)
                    VALUES ( ?, ?)
                    ON CONFLICT(使用糸) DO UPDATE SET
                    表示順 = excluded.表示順,
                    使用糸 = excluded.使用糸
                    """,
                    (row["表示順"], row["使用糸"]),
                )
        conn.commit()

    def main():

        st.set_page_config(
            page_title='編機調整報告書_DB選択項目入力',
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

        # タブを作成
        # tab_titles = ['編組織名　', '編組織パターン　',
        #               '使用糸　']
        # tab1, tab2, tab3 = st.tabs(tab_titles)
        tab_titles = ['編組織名　', '使用糸　']
        tab1, tab2 = st.tabs(tab_titles)

        with tab1:
            dfa = st.empty()
            bt1 = st.empty()
        with tab2:
            # DEL_20250115_パターンは削除
            #     sb2 = st.empty()
            #     dfb = st.empty()
            #     bt2 = st.empty()
            # with tab3:
            dfc = st.empty()
            bt3 = st.empty()

        # 編組織名
        # データベースを参照
        df1 = db_set1()
        # 受け取ったDFの表示
        edited_bt1 = dfa.data_editor(df1.drop(columns=['ID']).reset_index(drop=True),
                                     column_config={
                                         '表示順': {"sortable": False, 'width': 120},
                                         '編組織名': {'width': 200, "sortable": False},
                                         '詳細': {'width': 300, "sortable": False}
        },
            hide_index=True, num_rows="dynamic")
        # 更新処理
        # DEL_20250115_編組織パターンの削除により、関係する処理は削除
        if bt1.button("編組織名更新"):
            db_update1(edited_bt1, df1, 'shiteigara')
            # df1a = db_set1()
            # shiteigara_value1 = df1a['編組織名'].tolist()
            # shiteigara_value1 = list(dict.fromkeys(shiteigara_value1))
            # sel = sb2.selectbox('編組織名選択', shiteigara_value1, index=0)
            # filtered_id = df1a[df1a['編組織名'] == sel]['ID']
            # df2 = db_set2()
            # filtered_id が空でない場合の処理
            # if not filtered_id.empty:
            # df2 = df2[df2['rID'] == filtered_id.iloc[0]]
            # st.write("更新完了")
            st.write("更新完了")  # ADD_20250115
        # else:
            # shiteigara_value2 = df1['編組織名'].tolist()
            # shiteigara_value2 = list(dict.fromkeys(shiteigara_value2))
            # sel = sb2.selectbox('編組織名選択', shiteigara_value2, index=0)
            # filtered_id = df1[df1['編組織名'] == sel]['ID']
            # df2 = db_set2()
            # filtered_id が空でない場合の処理
            # if not filtered_id.empty:
            #    df2 = df2[df2['rID'] == filtered_id.iloc[0]]

        # # 編組織パターン
        # edited_bt2 = dfb.data_editor(df2.drop(columns=['ID', 'rID']).reset_index(drop=True),
        #                              column_config={
        #                                  '表示順': {"sortable": False, 'width': 120},
        #                                  '編組織パターン': {'width': 300, "sortable": False}
        # },
        #     hide_index=True, num_rows="dynamic")
        # if bt2.button("編組織パターン更新"):
        #     db_update2(edited_bt2, df2,
        #                filtered_id.iloc[0], 'shiteigara_pattern')
        #     st.write("更新完了")

        # 使用糸
        df3 = db_set3()
        edited_bt3 = dfc.data_editor(df3.drop(columns=['ID']).reset_index(drop=True),
                                     column_config={
                                         '表示順': {"sortable": False, 'width': 120},
                                         '使用糸': {'width': 300, "sortable": False}},
                                     hide_index=True, num_rows="dynamic")
        if bt3.button("使用糸更新"):
            db_update3(edited_bt3, df3, 'shiyouito')
            st.write("更新完了")

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
