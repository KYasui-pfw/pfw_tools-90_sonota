################################
# 　本体Gr製造チェックシート      #
# 　表示パターンの登録            #
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
import time

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

    def model_type_table_get():

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db'):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_hontai_seizo.db")

        # 本処理（更新処理）
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        # 編組織名テーブル作成
        cur.execute('''CREATE TABLE IF NOT EXISTS model_type_table(
                  機種区分 TEXT PRIMARY KEY,
                  カテゴリ名1 TEXT,
                  カテゴリ名2 TEXT,
                  カテゴリ名3 TEXT,
                  カテゴリ名4 TEXT,
                  カテゴリ名5 TEXT,
                  カテゴリ名6 TEXT,
                  カテゴリ名7 TEXT,
                  カテゴリ名8 TEXT,
                  カテゴリ名9 TEXT,
                  カテゴリ名10 TEXT,
                  カテゴリ名11 TEXT,
                  カテゴリ名12 TEXT,
                  カテゴリ名13 TEXT,
                  カテゴリ名14 TEXT,
                  カテゴリ名15 TEXT,
                  カテゴリ名16 TEXT,
                  カテゴリ名17 TEXT,
                  カテゴリ名18 TEXT,
                  カテゴリ名19 TEXT,
                  カテゴリ名20 TEXT,
                  カテゴリ名21 TEXT,
                  カテゴリ名22 TEXT,
                  カテゴリ名23 TEXT,
                  カテゴリ名24 TEXT,
                  カテゴリ名25 TEXT,
                  カテゴリ名26 TEXT,
                  カテゴリ名27 TEXT,
                  カテゴリ名28 TEXT,
                  カテゴリ名29 TEXT,
                  カテゴリ名30 TEXT
                  )''')
        # データベースの値を取得する
        sql = f'select * from model_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')

        # 初期データセットアップ
        if df.empty:
            # 更新操作
            model_type_list = ["SK", "DK"]
            for item in model_type_list:
                cur.execute(
                    """
                            INSERT INTO model_type_table (
                                機種区分, カテゴリ名1, カテゴリ名2, カテゴリ名3, カテゴリ名4,
                                カテゴリ名5, カテゴリ名6, カテゴリ名7, カテゴリ名8, カテゴリ名9,
                                カテゴリ名10, カテゴリ名11, カテゴリ名12, カテゴリ名13, カテゴリ名14,
                                カテゴリ名15, カテゴリ名16, カテゴリ名17, カテゴリ名18, カテゴリ名19,
                                カテゴリ名20, カテゴリ名21, カテゴリ名22, カテゴリ名23, カテゴリ名24,
                                カテゴリ名25, カテゴリ名26, カテゴリ名27, カテゴリ名28, カテゴリ名29, カテゴリ名30
                            ) VALUES (
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                            )
                        """,
                    (item, '', '', '', '', '', '', '', '', '', '',
                     '', '', '', '', '', '', '', '', '', '',
                     '', '', '', '', '', '', '', '', '', ''),
                )
            conn.commit()

        # 縦列への変更
        df_category1 = df[['機種区分', 'カテゴリ名1']].rename(
            columns={'カテゴリ名1': 'カテゴリ名'})
        df_category2 = df[['機種区分', 'カテゴリ名2']].rename(
            columns={'カテゴリ名2': 'カテゴリ名'})
        df_category3 = df[['機種区分', 'カテゴリ名3']].rename(
            columns={'カテゴリ名3': 'カテゴリ名'})
        df_category4 = df[['機種区分', 'カテゴリ名4']].rename(
            columns={'カテゴリ名4': 'カテゴリ名'})
        df_category5 = df[['機種区分', 'カテゴリ名5']].rename(
            columns={'カテゴリ名5': 'カテゴリ名'})
        df_category6 = df[['機種区分', 'カテゴリ名6']].rename(
            columns={'カテゴリ名6': 'カテゴリ名'})
        df_category7 = df[['機種区分', 'カテゴリ名7']].rename(
            columns={'カテゴリ名7': 'カテゴリ名'})
        df_category8 = df[['機種区分', 'カテゴリ名8']].rename(
            columns={'カテゴリ名8': 'カテゴリ名'})
        df_category9 = df[['機種区分', 'カテゴリ名9']].rename(
            columns={'カテゴリ名9': 'カテゴリ名'})
        df_category10 = df[['機種区分', 'カテゴリ名10']].rename(
            columns={'カテゴリ名10': 'カテゴリ名'})
        df_category11 = df[['機種区分', 'カテゴリ名11']].rename(
            columns={'カテゴリ名11': 'カテゴリ名'})
        df_category12 = df[['機種区分', 'カテゴリ名12']].rename(
            columns={'カテゴリ名12': 'カテゴリ名'})
        df_category13 = df[['機種区分', 'カテゴリ名13']].rename(
            columns={'カテゴリ名13': 'カテゴリ名'})
        df_category14 = df[['機種区分', 'カテゴリ名14']].rename(
            columns={'カテゴリ名14': 'カテゴリ名'})
        df_category15 = df[['機種区分', 'カテゴリ名15']].rename(
            columns={'カテゴリ名15': 'カテゴリ名'})
        df_category16 = df[['機種区分', 'カテゴリ名16']].rename(
            columns={'カテゴリ名16': 'カテゴリ名'})
        df_category17 = df[['機種区分', 'カテゴリ名17']].rename(
            columns={'カテゴリ名17': 'カテゴリ名'})
        df_category18 = df[['機種区分', 'カテゴリ名18']].rename(
            columns={'カテゴリ名18': 'カテゴリ名'})
        df_category19 = df[['機種区分', 'カテゴリ名19']].rename(
            columns={'カテゴリ名19': 'カテゴリ名'})
        df_category20 = df[['機種区分', 'カテゴリ名20']].rename(
            columns={'カテゴリ名20': 'カテゴリ名'})
        df_category21 = df[['機種区分', 'カテゴリ名21']].rename(
            columns={'カテゴリ名21': 'カテゴリ名'})
        df_category22 = df[['機種区分', 'カテゴリ名22']].rename(
            columns={'カテゴリ名22': 'カテゴリ名'})
        df_category23 = df[['機種区分', 'カテゴリ名23']].rename(
            columns={'カテゴリ名23': 'カテゴリ名'})
        df_category24 = df[['機種区分', 'カテゴリ名24']].rename(
            columns={'カテゴリ名24': 'カテゴリ名'})
        df_category25 = df[['機種区分', 'カテゴリ名25']].rename(
            columns={'カテゴリ名25': 'カテゴリ名'})
        df_category26 = df[['機種区分', 'カテゴリ名26']].rename(
            columns={'カテゴリ名26': 'カテゴリ名'})
        df_category27 = df[['機種区分', 'カテゴリ名27']].rename(
            columns={'カテゴリ名27': 'カテゴリ名'})
        df_category28 = df[['機種区分', 'カテゴリ名28']].rename(
            columns={'カテゴリ名28': 'カテゴリ名'})
        df_category29 = df[['機種区分', 'カテゴリ名29']].rename(
            columns={'カテゴリ名29': 'カテゴリ名'})
        df_category30 = df[['機種区分', 'カテゴリ名30']].rename(
            columns={'カテゴリ名30': 'カテゴリ名'})

        # データフレームをリストに格納
        df_list = [
            df_category1, df_category2, df_category3, df_category4, df_category5,
            df_category6, df_category7, df_category8, df_category9, df_category10,
            df_category11, df_category12, df_category13, df_category14, df_category15,
            df_category16, df_category17, df_category18, df_category19, df_category20,
            df_category21, df_category22, df_category23, df_category24, df_category25,
            df_category26, df_category27, df_category28, df_category29, df_category30
        ]

        # データフレームを縦に連結
        combined_df = pd.concat(df_list, ignore_index=True)
        # 置換を行う
        combined_df['カテゴリ名'] = combined_df['カテゴリ名'].replace(
            [None, ' ', '　'], '')
        return (combined_df)

    def model_type_update(edf, model_type):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        for i, row in edf.iterrows():
            cur.execute(f""" UPDATE model_type_table SET
                カテゴリ名{i} = ? WHERE 機種区分 = ?
                """, (row["カテゴリ名"], model_type))
        conn.commit()

    def report_type_table_get():
        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db'):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_hontai_seizo.db")

        # 本処理（更新処理）
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # データベースの値を取得する
        sql = '''SELECT
                帳票No,
                機種区分,
                帳票名,
                カテゴリ区分1 AS カテゴリ名1,
                カテゴリ区分2 AS カテゴリ名2,
                カテゴリ区分3 AS カテゴリ名3,
                カテゴリ区分4 AS カテゴリ名4,
                カテゴリ区分5 AS カテゴリ名5,
                カテゴリ区分6 AS カテゴリ名6,
                カテゴリ区分7 AS カテゴリ名7,
                カテゴリ区分8 AS カテゴリ名8,
                カテゴリ区分9 AS カテゴリ名9,
                カテゴリ区分10 AS カテゴリ名10,
                カテゴリ区分11 AS カテゴリ名11,
                カテゴリ区分12 AS カテゴリ名12,
                カテゴリ区分13 AS カテゴリ名13,
                カテゴリ区分14 AS カテゴリ名14,
                カテゴリ区分15 AS カテゴリ名15,
                カテゴリ区分16 AS カテゴリ名16,
                カテゴリ区分17 AS カテゴリ名17,
                カテゴリ区分18 AS カテゴリ名18,
                カテゴリ区分19 AS カテゴリ名19,
                カテゴリ区分20 AS カテゴリ名20,
                カテゴリ区分21 AS カテゴリ名21,
                カテゴリ区分22 AS カテゴリ名22,
                カテゴリ区分23 AS カテゴリ名23,
                カテゴリ区分24 AS カテゴリ名24,
                カテゴリ区分25 AS カテゴリ名25,
                カテゴリ区分26 AS カテゴリ名26,
                カテゴリ区分27 AS カテゴリ名27,
                カテゴリ区分28 AS カテゴリ名28,
                カテゴリ区分29 AS カテゴリ名29,
                カテゴリ区分30 AS カテゴリ名30
                from report_type_table'''
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        return (df)

    def koumokutenkai():
        seisan_col1, seisan_col2, seisan_col3, = st.columns([
            1, 3, 1])
        with seisan_col1:
            skdk_kubun = st.selectbox('機種区分選択', ['SK', 'DK'])

        with seisan_col2:
            # 帳票を取得
            dbname = 'hontai_seizo.db'
            cdb = os.path.dirname(os.path.dirname(
                __file__))+f'\\Database\\'+dbname
            conn = sqlite3.connect(cdb)
            sql = f'select 帳票No,帳票名 from report_type_table'
            df = sqlite_data_get(sql, os.path.dirname(
                os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
            df = df.sort_values(['帳票No'])
            df = df.fillna(' ')  # Noneデータ対策
            # 101～199がSK、201～299DK
            if skdk_kubun == 'SK':
                df = df[(df['帳票No'] > 100) & (df['帳票No'] < 200)]
            elif skdk_kubun == 'DK':
                df = df[(df['帳票No'] > 200) & (df['帳票No'] < 300)]
            select_list = []
            for index, row in df.iterrows():
                select_list.append(
                    f"帳票No：{row['帳票No']}　帳票名：{row['帳票名']}")
            cp = st.selectbox('帳票選択', select_list)
            if cp == '新規追加':
                button = "新規登録"
            else:

                # 「パターンNo：」の後の部分を抽出
                start_index = cp.find("帳票No：") + len("帳票No：")
                remaining_str = cp[start_index:].strip()

                # 最初の全角スペースの位置を見つける
                space_index = remaining_str.find("　")

                # 数字部分を切り出して整数に変換
                number = int(remaining_str[:space_index])
                df2 = df[df['帳票No'] == number]

        # ②帳票種別テーブルから取得
        sql2 = f'select * from report_type_table where 帳票No = "{number}"'
        df2 = pd.read_sql(sql2, conn)
        if df2.empty:
            st.write(f"帳票No：{number}の情報が存在しません")

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
        df5['入力欄'] = ""
        df5['No'] = ""
        df5['チェック'] = ""
        df5['作業者名'] = ""
        df5.loc[df5["前トグルflg"] == 0, "前トグル"] = "-"
        df5.loc[df5["入力欄flg"] == 0, "入力欄"] = "-"
        df5.loc[df5["Noflg"] == 0, "No"] = "-"
        df5.loc[df5["後トグルflg"] == 0, "後トグル"] = "-"
        df5.loc[df5["チェックflg"] == 0, "チェック"] = "-"
        df5.loc[df5["チェックflg"] == 1, "チェック"] = "□"
        df5.loc[df5["作業者名flg"] == 0, "作業者名"] = "-"
        df5.loc[df5["作業者名flg"] == 1, "作業者名"] = "選択"
        df5 = df5.drop(columns=['機種区分', 'カテゴリNo', 'カテゴリ区分', '表示順',
                       '前トグルflg', '入力欄flg', 'Noflg', '後トグルflg', 'チェックflg', '作業者名flg'])
        df5 = df5[["チェック項目", "前トグル", "入力欄", "No", "後トグル", "チェック", "作業者名"]]
        df5 = df5.reset_index(drop=True)
        df5.index = df5.index + 1

        sd_pages = []  # 分割結果を格納するリスト
        for i in range(0, len(df5), 34):
            chunk = df5[i:i + 34]  # 部分データフレームを作成
            sd_pages.append(chunk)  # リストに追加

        for i, chunk in enumerate(sd_pages):
            st.divider()
            st.write(f"{i+1}ページ")
            edited_df = st.data_editor(chunk,
                                       column_config={
                                           'チェック項目': {'width': 270},
                                           '前トグル': {'width': 150},
                                           '入力欄': {'width': 200},
                                           'No': {'width': 100},
                                           '後トグル': {'width': 130},
                                           'チェック': {'width': 100},
                                           '作業者名': {'width': 120}},
                                       disabled=["チェック項目", "前トグル", "入力欄",
                                                 "No", "後トグル", "チェック", "作業者名"],
                                       hide_index=False, height=1230)

    def report_type_update(edf):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        for i, row in edf.iterrows():
            cur.execute(f""" UPDATE report_type_table SET
                    カテゴリ区分1 = ?,カテゴリ区分2 = ?,
                    カテゴリ区分3 = ?,カテゴリ区分4 = ?,
                    カテゴリ区分5 = ?,カテゴリ区分6 = ?,
                    カテゴリ区分7 = ?,カテゴリ区分8 = ?,
                    カテゴリ区分9 = ?,カテゴリ区分10 = ?,
                    カテゴリ区分11 = ?,カテゴリ区分12 = ?,
                    カテゴリ区分13 = ?,カテゴリ区分14 = ?,
                    カテゴリ区分15 = ?,カテゴリ区分16 = ?,
                    カテゴリ区分17 = ?,カテゴリ区分18 = ?,
                    カテゴリ区分19 = ?,カテゴリ区分20 = ?,
                    カテゴリ区分21 = ?,カテゴリ区分22 = ?,
                    カテゴリ区分23 = ?,カテゴリ区分24 = ?,
                    カテゴリ区分25 = ?,カテゴリ区分26 = ?,
                    カテゴリ区分27 = ?,カテゴリ区分28 = ?,
                    カテゴリ区分29 = ?,カテゴリ区分30 = ?
                    WHERE
                         帳票No = ?
                """, (
                        int(row[edf.columns[0]]), int(row[edf.columns[1]]), int(
                            row[edf.columns[2]]), int(row[edf.columns[3]]), int(row[edf.columns[4]]),
                        int(row[edf.columns[5]]), int(row[edf.columns[6]]), int(
                            row[edf.columns[7]]), int(row[edf.columns[8]]), int(row[edf.columns[9]]),
                        int(row[edf.columns[10]]), int(row[edf.columns[11]]), int(
                            row[edf.columns[12]]), int(row[edf.columns[13]]), int(row[edf.columns[14]]),
                        int(row[edf.columns[15]]), int(row[edf.columns[16]]), int(
                            row[edf.columns[17]]), int(row[edf.columns[18]]), int(row[edf.columns[19]]),
                        int(row[edf.columns[20]]), int(row[edf.columns[21]]), int(
                            row[edf.columns[22]]), int(row[edf.columns[23]]), int(row[edf.columns[24]]),
                        int(row[edf.columns[25]]), int(row[edf.columns[26]]), int(
                            row[edf.columns[27]]), int(row[edf.columns[28]]), int(row[edf.columns[29]]),
                        row.name  # インデックス名を使用
                        ))
        conn.commit()

    # --- 進捗確認データベース関連関数（別画面から引っ越し） ---
    # --- 定数定義 (英語カラム名に変更) ---
    DB_DIR = os.path.join(".", "Database")
    DB_PATH = os.path.join(DB_DIR, "hontai_seizo.db")
    TABLE_NAME = "progress_check_targets"
    COL_DIVISION = "機種区分"
    COL_YEAR = "年"
    COL_MONTH = "月"
    CATEGORY_COLS_PREFIX = "カテゴリNo_"
    CATEGORY_COLS = [f"{CATEGORY_COLS_PREFIX}{i}" for i in range(1, 31)]
    ALL_COLUMNS = [COL_DIVISION, COL_YEAR, COL_MONTH] + CATEGORY_COLS

    def get_db_connection():
        """データベース接続を取得する"""
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        """データベースとテーブルを初期化する"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'")
        table_exists = cursor.fetchone()

        if not table_exists:
            category_cols_sql = ", ".join(
                [f'"{col}" INTEGER' for col in CATEGORY_COLS])
            create_table_sql = f"""
            CREATE TABLE "{TABLE_NAME}" (
                "{COL_DIVISION}" TEXT NOT NULL,
                "{COL_YEAR}" INTEGER NOT NULL,
                "{COL_MONTH}" INTEGER NOT NULL,
                {category_cols_sql},
                PRIMARY KEY ("{COL_DIVISION}", "{COL_YEAR}", "{COL_MONTH}")
            )
            """
            cursor.execute(create_table_sql)

            initial_year = 2000
            initial_month = 1
            default_category_values = {col: None for col in CATEGORY_COLS}

            cols_for_insert = f'"{COL_DIVISION}", "{COL_YEAR}", "{COL_MONTH}", {", ".join([f'"{col}"' for col in CATEGORY_COLS])}'

            cursor.execute(f"""
                INSERT INTO "{TABLE_NAME}" ({cols_for_insert})
                VALUES (?, ?, ?, {", ".join(["?"] * len(CATEGORY_COLS))})
            """, ("SK", initial_year, initial_month, *default_category_values.values()))

            cursor.execute(f"""
                INSERT INTO "{TABLE_NAME}" ({cols_for_insert})
                VALUES (?, ?, ?, {", ".join(["?"] * len(CATEGORY_COLS))})
            """, ("DK", initial_year, initial_month, *default_category_values.values()))

            conn.commit()
            st.success(
                f"データベース '{DB_PATH}' とテーブル '{TABLE_NAME}' を作成し、初期データを投入しました。")

        conn.close()

    def get_distinct_year_months(conn):
        """データベースから既存の生産年月のリストを取得する"""
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT DISTINCT "{COL_YEAR}", "{COL_MONTH}" FROM "{TABLE_NAME}" ORDER BY "{COL_YEAR}" DESC, "{COL_MONTH}" DESC')
        year_months = cursor.fetchall()
        return [f"{row[COL_YEAR]}年{str(row[COL_MONTH]).zfill(2)}月" for row in year_months]

    def load_data_from_db(conn, year, month):
        """指定された年月のデータをデータベースから読み込む"""
        cursor = conn.cursor()
        placeholders = ", ".join([f'"{col}"' for col in ALL_COLUMNS])
        sql = f'SELECT {placeholders} FROM "{TABLE_NAME}" WHERE "{COL_YEAR}" = ? AND "{COL_MONTH}" = ? AND "{COL_DIVISION}" IN (?, ?)'
        cursor.execute(sql, (year, month, "SK", "DK"))
        data = cursor.fetchall()
        if not data:
            return create_default_dataframe(year, month)

        data_dict_list = [dict(row) for row in data]
        df = pd.DataFrame(data_dict_list, columns=ALL_COLUMNS)

        df[COL_DIVISION] = pd.Categorical(df[COL_DIVISION], categories=[
            "SK", "DK"], ordered=True)
        df = df.sort_values(COL_DIVISION)
        return df

    def create_default_dataframe(year, month):
        """指定された年月でSK行とDK行の空のDataFrameを作成する"""
        data = []
        for division_val in ["SK", "DK"]:
            row = {
                COL_DIVISION: division_val,
                COL_YEAR: year,
                COL_MONTH: month,
            }
            for cat_col in CATEGORY_COLS:
                row[cat_col] = None
            data.append(row)
        return pd.DataFrame(data, columns=ALL_COLUMNS)

    def save_data_to_db(conn, edited_df):
        """編集されたDataFrameをデータベースに保存する (INSERT OR REPLACE)"""
        cursor = conn.cursor()

        for index, row_series in edited_df.iterrows():
            values_to_insert = []
            for col_name in ALL_COLUMNS:
                val = row_series[col_name]
                if pd.isna(val):  # pandasのNAやNaNをNoneに
                    values_to_insert.append(None)
                elif isinstance(val, str) and val.strip() == "":  # 空文字列もNoneとして扱う
                    values_to_insert.append(None)
                # Ensure NaN floats are not converted to int
                elif isinstance(val, (int, float)) and not pd.isna(val):
                    values_to_insert.append(int(val))  # カテゴリは整数型で保存
                else:  # 文字列など
                    values_to_insert.append(val)

            cols_for_sql = ", ".join([f'"{col}"' for col in ALL_COLUMNS])
            placeholders = ", ".join(["?"] * len(ALL_COLUMNS))
            sql = f'INSERT OR REPLACE INTO "{TABLE_NAME}" ({cols_for_sql}) VALUES ({placeholders})'

            try:
                cursor.execute(sql, tuple(values_to_insert))
            except sqlite3.Error as e:
                st.error(f"データベース保存エラー ({row_series[COL_DIVISION]}行): {e}")
                conn.rollback()
                return False

        conn.commit()
        return True

    def delete_data_from_db(conn, year, month):
        """指定された年月のデータをデータベースから削除する"""
        cursor = conn.cursor()
        try:
            cursor.execute(
                f'DELETE FROM "{TABLE_NAME}" WHERE "{COL_YEAR}" = ? AND "{COL_MONTH}" = ?', (year, month))
            conn.commit()
            return True
        except sqlite3.Error as e:
            st.error(f"データベース削除エラー: {e}")
            conn.rollback()
            return False

    # --- バリデーション関数 ---

    def validate_categories(row_series):
        """表示カテゴリの行内重複をチェックする (修正版)"""
        category_values = []
        for col in CATEGORY_COLS:
            val = row_series.get(col)  # .get() を使うことでキーが存在しない場合のエラーを避ける
            if pd.notna(val) and str(val).strip() != '':
                try:
                    category_values.append(int(val))  # 数値として扱う
                except ValueError:
                    # 数値に変換できないものは無視するか、エラーとして扱う (ここでは無視)
                    pass

        if not category_values:  # 全て空欄または無効な値ならOK
            return True
        return len(category_values) == len(set(category_values))

    def main():

        st.set_page_config(
            page_title='チェック大項目登録',
            layout="wide")

        HIDE_ST_STYLE = """
                    <style>
                    div[data-testid="stToolbar"],
                    div[data-testid="stDecoration"],
                    #MainMenu,
                    header,
                    footer {
                        display: none !important; /* 強制的に非表示にし、スペースも占有しない */
                        height: 0px !important; /* 念のため高さも0に */
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

        # 機種区分テーブル取得
        model_type_df = model_type_table_get()

        # 帳票種別テーブル取得
        report_type_df = report_type_table_get()

        # タブで表示を区切る
        tab_titles = ['表示パターン登録　', '帳票イメージ確認　', '機種区分修正', '進捗確認項目更新']
        tab1, tab2, tab3, tab4 = st.tabs(tab_titles)
        with tab1:
            t1_col1, t1_col2 = st.columns([1, 3])
            with t1_col1:
                select_list_t1 = ['SK', 'DK']
                model_type_t1 = st.selectbox(
                    '機種区分選択', select_list_t1, key='t1_select')
            with t1_col2:
                st.write("")
            st.divider()
            # データフレームの調整１　機種区分テーブル
            model_type_df_t1 = model_type_df[model_type_df['機種区分']
                                             == model_type_t1]
            model_type_df_t1 = model_type_df_t1.drop(columns=['機種区分'])
            model_type_df_t1 = model_type_df_t1.reset_index(drop=True)

            # データフレームの調整２　帳票種別テーブル取得
            report_type_df_t1 = report_type_df[report_type_df['機種区分']
                                               == model_type_t1]
            report_type_df_t1['帳票No_帳票名'] = report_type_df_t1['帳票No'].astype(
                str) + '_' + report_type_df_t1['帳票名']
            report_type_df_t1 = report_type_df_t1.drop(
                columns=['機種区分', '帳票No', '帳票名'])

            # 行列逆転
            report_type_df_t1_2 = report_type_df_t1.T
            # 最終行を先頭に移動
            last_row = report_type_df_t1_2.iloc[[-1]]
            rest_of_df = report_type_df_t1_2.iloc[:-1]
            report_type_df_t1_2 = pd.concat(
                # [last_row, rest_of_df]).reset_index(drop=True)
                [last_row, rest_of_df])
            # 帳票種別テーブルのindexを機種区分テーブルの登録名称に置き換える
            new_index = report_type_df_t1_2.index[:1].tolist(
            ) + model_type_df_t1['カテゴリ名'].tolist()
            report_type_df_t1_2.index = new_index
            # カラム名を付け替える（付け替え元の行は削除）
            report_type_df_t1_2.columns = report_type_df_t1_2.iloc[0]
            report_type_df_t1_2 = report_type_df_t1_2.drop(
                report_type_df_t1_2.index[0])

            # プルダウンを空白含OKとするため、一旦文字列化する
            report_type_df_t1_2 = report_type_df_t1_2.fillna(
                99).applymap(int).applymap(str)

            # 全ての列に対して'99'を '　' に置き換える
            report_type_df_t1_2 = report_type_df_t1_2.replace('99', '　')

            # エディター用のプルダウン
            selectbox_options = ['1', '2', '3',
                                 '4', '5', '6', '7', '8', '9', '　']
            columns_config = {col: st.column_config.SelectboxColumn(
                label=col, options=selectbox_options) for col in report_type_df_t1_2.columns}
            columns_config["_index"] = {'width': 250}

            # エディター
            report_type_edited_df = st.data_editor(report_type_df_t1_2,
                                                   column_config=columns_config,
                                                   disabled=["_index"],
                                                   hide_index=False)

            if st.button("更新", key='t1button'):
                # 数値に戻す
                report_type_edited_df = report_type_edited_df.replace(
                    "　", '99')
                report_type_edited_df = report_type_edited_df.fillna(99).applymap(
                    float).applymap(int)

                # カラム名を帳票番号に戻す
                new_columns = []
                for col in report_type_edited_df.columns:
                    # カラム名をアンダースコアで分割し、最初の要素を取得
                    new_col = col.split('_')[0]
                    new_columns.append(new_col)
                report_type_edited_df.columns = new_columns

                # インデックスを連番に戻してから行列逆転
                report_type_edited_df = report_type_edited_df.reset_index(
                    drop=True)
                report_type_edited_df = report_type_edited_df.T
                report_type_update(report_type_edited_df)
                time.sleep(3)
                st.write("更新完了")
                st.rerun()

        with tab2:
            t2 = st.empty()
            koumokutenkai()
        with tab3:
            t3_col1, t3_col2 = st.columns([1, 3])
            with t3_col1:
                select_list = ['SK', 'DK']
                model_type_t3 = st.selectbox('機種区分選択', select_list, key='t3')
            with t3_col2:
                st.write("")
            st.divider()
            # データフレームの調整
            model_type_df_t3 = model_type_df[model_type_df['機種区分']
                                             == model_type_t3]
            model_type_df_t3 = model_type_df_t3.drop(columns=['機種区分'])
            model_type_df_t3 = model_type_df_t3.reset_index(drop=True)
            model_type_df_t3.index = model_type_df_t3.index + 1
            # エディター
            model_type_edited_df = st.data_editor(model_type_df_t3,
                                                  column_config={
                                                      'カテゴリ名': {'width': 400}},
                                                  hide_index=False)
            if st.button("更新"):
                # 置換を行う
                model_type_edited_df['カテゴリ名'] = model_type_edited_df['カテゴリ名'].replace([
                    None, ' ', '　'], '')
                model_type_edited_df = model_type_edited_df.sort_index()
                model_type_update(model_type_edited_df, model_type_t3)
                st.rerun()
                st.write("更新完了")
        with tab4:

            # st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)
            # st.title("進捗確認設定")

            init_db()
            conn = get_db_connection()

            if 'selected_year_month_str' not in st.session_state:
                st.session_state.selected_year_month_str = None
            if 'confirm_delete_tuple' not in st.session_state:
                st.session_state.confirm_delete_tuple = None
            if 'new_entry_year' not in st.session_state:
                st.session_state.new_entry_year = datetime.now().year
            if 'new_entry_month' not in st.session_state:
                st.session_state.new_entry_month = datetime.now().month

            year_month_options_db = get_distinct_year_months(conn)
            year_month_options = ["新規追加"] + year_month_options_db

            default_index = 0
            if len(year_month_options) > 1:
                default_index = 1

            if st.session_state.selected_year_month_str in year_month_options:
                current_selection_index = year_month_options.index(
                    st.session_state.selected_year_month_str)
            else:
                current_selection_index = default_index
                if len(year_month_options) > default_index:
                    st.session_state.selected_year_month_str = year_month_options[default_index]

            select_col, spacer1_col, new_year_col, new_month_col, spacer2_col = st.columns([
                1, 1, 1, 1, 1])

            with select_col:
                selected_year_month_str = st.selectbox(
                    "生産年月を選択してください:",
                    year_month_options,
                    index=current_selection_index,
                    key="sb_year_month"
                )
            st.session_state.selected_year_month_str = selected_year_month_str

            is_new_entry_mode = (selected_year_month_str == "新規追加")
            current_year, current_month = None, None

            if is_new_entry_mode:
                with new_year_col:
                    new_year = st.number_input("生産年", min_value=1900, max_value=2100,
                                               value=st.session_state.new_entry_year, key="ni_new_year")
                with new_month_col:
                    new_month = st.number_input(
                        "生産月", min_value=1, max_value=12, value=st.session_state.new_entry_month, key="ni_new_month")

                st.session_state.new_entry_year = new_year
                st.session_state.new_entry_month = new_month
                current_year, current_month = new_year, new_month

                check_conn = get_db_connection()
                cursor = check_conn.cursor()
                cursor.execute(
                    f'SELECT 1 FROM "{TABLE_NAME}" WHERE "{COL_YEAR}" = ? AND "{COL_MONTH}" = ? LIMIT 1', (current_year, current_month))
                exists = cursor.fetchone()
                check_conn.close()
                if exists:
                    st.warning(
                        f"{current_year}年{str(current_month).zfill(2)}月のデータは既に存在します。既存データを選択するか、異なる年月を入力してください。")
                    df_to_edit = load_data_from_db(
                        conn, current_year, current_month)
                else:
                    df_to_edit = create_default_dataframe(
                        current_year, current_month)
            else:
                if selected_year_month_str and selected_year_month_str != "新規追加":
                    try:
                        year_str, month_str_with_suffix = selected_year_month_str.split(
                            "年")
                        month_str = month_str_with_suffix.replace("月", "")
                        current_year, current_month = int(
                            year_str), int(month_str)
                        df_to_edit = load_data_from_db(
                            conn, current_year, current_month)
                    except ValueError:
                        st.error(
                            f"選択された年月「{selected_year_month_str}」の形式が正しくありません。")
                        df_to_edit = pd.DataFrame(columns=ALL_COLUMNS)
                else:
                    df_to_edit = pd.DataFrame(columns=ALL_COLUMNS)

            editor_placeholder = st.empty()

            if not df_to_edit.empty and current_year is not None and current_month is not None:
                category_options = [None] + list(range(1, 31))  # Noneを許容
                column_config = {
                    COL_DIVISION: st.column_config.TextColumn("SK/DK", disabled=True, help="SKまたはDK", width="small"),
                    COL_YEAR: st.column_config.NumberColumn("生産年", disabled=True, format="%d", width="small"),
                    COL_MONTH: st.column_config.NumberColumn("生産月", disabled=True, format="%02d", width="small"),
                }
                for i, cat_col_en in enumerate(CATEGORY_COLS):
                    display_name = f"表示{i+1}"
                    column_config[cat_col_en] = st.column_config.SelectboxColumn(
                        display_name,
                        options=category_options,
                        required=False,  # 空欄を許容
                        width="small"
                    )

                editor_key = f"data_editor_{current_year}_{current_month}_{is_new_entry_mode}"

                with editor_placeholder.container():
                    st.subheader(
                        f"データ編集: {current_year}年{str(current_month).zfill(2)}月")
                    # data_editorでNoneを正しく扱うために、DataFrameの該当列をobject型にしておく
                    for col in CATEGORY_COLS:
                        if col in df_to_edit.columns:
                            df_to_edit[col] = df_to_edit[col].astype(object)

                    edited_df = st.data_editor(
                        df_to_edit,
                        column_config=column_config,
                        num_rows="fixed",
                        hide_index=True,
                        key=editor_key,
                        height=115
                    )

                    btn_cols = st.columns(3)
                    with btn_cols[0]:
                        if st.button("更新", key=f"update_btn_{editor_key}"):
                            valid_data = True
                            error_messages = []
                            if len(edited_df) != 2 or not all(edited_df[COL_DIVISION].isin(["SK", "DK"])):
                                error_messages.append("SK行とDK行の2行が必要です。")
                                valid_data = False

                            if not all(edited_df[COL_YEAR] == current_year) or not all(edited_df[COL_MONTH] == current_month):
                                error_messages.append(
                                    f"データ内の年月が編集中に変更されました。{current_year}年{current_month}月のデータとして保存されます。")
                                edited_df[COL_YEAR] = current_year
                                edited_df[COL_MONTH] = current_month

                            for index, row_series in edited_df.iterrows():
                                # 修正されたバリデーション関数を使用
                                if not validate_categories(row_series):
                                    error_messages.append(
                                        f"{row_series[COL_DIVISION]}行で表示カテゴリの数値が重複しています。")
                                    valid_data = False

                            if valid_data:
                                if save_data_to_db(conn, edited_df):
                                    st.success(
                                        f"{current_year}年{str(current_month).zfill(2)}月のデータを更新しました。")
                                    if is_new_entry_mode:
                                        st.session_state.selected_year_month_str = f"{current_year}年{str(current_month).zfill(2)}月"
                                    time.sleep(3)
                                    st.rerun()  # st.experimental_rerun() から変更
                                else:
                                    st.error("データの更新に失敗しました。")
                            else:
                                for msg in error_messages:
                                    st.error(msg)

                    with btn_cols[1]:
                        if not is_new_entry_mode:
                            if st.button("削除", key=f"delete_btn_{editor_key}", type="secondary"):
                                st.session_state.confirm_delete_tuple = (
                                    current_year, current_month)
                                time.sleep(3)
                                st.rerun()  # st.experimental_rerun() から変更

            if st.session_state.confirm_delete_tuple:
                delete_year, delete_month = st.session_state.confirm_delete_tuple
                st.warning(
                    f"{delete_year}年{str(delete_month).zfill(2)}月のデータを本当に削除しますか？この操作は元に戻せません。")

                confirm_col1, confirm_col2, _ = st.columns([1, 1, 3])
                with confirm_col1:
                    if st.button("はい、削除します", key="confirm_delete_yes", type="primary"):
                        if delete_data_from_db(conn, delete_year, delete_month):
                            st.success(
                                f"{delete_year}年{str(delete_month).zfill(2)}月のデータを削除しました。")
                            st.session_state.confirm_delete_tuple = None
                            if st.session_state.selected_year_month_str == f"{delete_year}年{str(delete_month).zfill(2)}月":
                                st.session_state.selected_year_month_str = None
                            time.sleep(3)
                            st.rerun()  # st.experimental_rerun() から変更
                        else:
                            st.error("データの削除に失敗しました。")
                            st.session_state.confirm_delete_tuple = None
                            time.sleep(3)
                            st.rerun()  # st.experimental_rerun() から変更
                with confirm_col2:
                    if st.button("キャンセル", key="confirm_delete_no"):
                        st.session_state.confirm_delete_tuple = None
                        time.sleep(3)
                        st.rerun()  # st.experimental_rerun() から変更

            conn.close()

    if __name__ == "__main__":
        main()


except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
