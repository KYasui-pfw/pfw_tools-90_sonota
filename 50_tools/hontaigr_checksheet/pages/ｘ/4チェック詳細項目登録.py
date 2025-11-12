################################
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
import numpy as np

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

    def db_create():

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
        cur.execute('''CREATE TABLE IF NOT EXISTS check_item_table(
                  帳票パターンNo INTEGER,
                  カテゴリNo INTEGER,
                  項目No INTEGER,
                  項目表示順 INTEGER,
                  チェック項目 TEXT,
                  前トグルflg INTEGER,
                  前トグル TEXT,
                  入力欄flg INTEGER,
                  入力欄 TEXT,
                  Noflg INTEGER,
                  No TEXT,
                  後トグルflg INTEGER,
                  後トグル TEXT,
                  チェックflg INTEGER,
                  チェック TEXT,
                  作業者名flg INTEGER,
                  作業者名 TEXT,
                  Del_flg INTEGER,
                  PRIMARY KEY (帳票パターンNo, カテゴリNo, 項目No)
                  )''')

        # 帳票種別テーブルを基に更新する
        sql = f'select * from report_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df2 = df.sort_values(['帳票パターンNo'])

        # 縦列への変更
        df_category1 = df2[['帳票パターンNo', 'カテゴリ表示順1', 'チェックカテゴリ名1']].rename(
            columns={'カテゴリ表示順1': '表示順', 'チェックカテゴリ名1': '大項目名称'})
        df_category2 = df2[['帳票パターンNo', 'カテゴリ表示順2', 'チェックカテゴリ名2']].rename(
            columns={'カテゴリ表示順2': '表示順', 'チェックカテゴリ名2': '大項目名称'})
        df_category3 = df2[['帳票パターンNo', 'カテゴリ表示順3', 'チェックカテゴリ名3']].rename(
            columns={'カテゴリ表示順3': '表示順', 'チェックカテゴリ名3': '大項目名称'})
        df_category4 = df2[['帳票パターンNo', 'カテゴリ表示順4', 'チェックカテゴリ名4']].rename(
            columns={'カテゴリ表示順4': '表示順', 'チェックカテゴリ名4': '大項目名称'})
        df_category5 = df2[['帳票パターンNo', 'カテゴリ表示順5', 'チェックカテゴリ名5']].rename(
            columns={'カテゴリ表示順5': '表示順', 'チェックカテゴリ名5': '大項目名称'})
        df_category6 = df2[['帳票パターンNo', 'カテゴリ表示順6', 'チェックカテゴリ名6']].rename(
            columns={'カテゴリ表示順6': '表示順', 'チェックカテゴリ名6': '大項目名称'})
        df_category7 = df2[['帳票パターンNo', 'カテゴリ表示順7', 'チェックカテゴリ名7']].rename(
            columns={'カテゴリ表示順7': '表示順', 'チェックカテゴリ名7': '大項目名称'})
        df_category8 = df2[['帳票パターンNo', 'カテゴリ表示順8', 'チェックカテゴリ名8']].rename(
            columns={'カテゴリ表示順8': '表示順', 'チェックカテゴリ名8': '大項目名称'})
        df_category9 = df2[['帳票パターンNo', 'カテゴリ表示順9', 'チェックカテゴリ名9']].rename(
            columns={'カテゴリ表示順9': '表示順', 'チェックカテゴリ名9': '大項目名称'})
        df_category10 = df2[['帳票パターンNo', 'カテゴリ表示順10', 'チェックカテゴリ名10']].rename(
            columns={'カテゴリ表示順10': '表示順', 'チェックカテゴリ名10': '大項目名称'})
        df_category11 = df2[['帳票パターンNo', 'カテゴリ表示順11', 'チェックカテゴリ名11']].rename(
            columns={'カテゴリ表示順11': '表示順', 'チェックカテゴリ名11': '大項目名称'})
        df_category12 = df2[['帳票パターンNo', 'カテゴリ表示順12', 'チェックカテゴリ名12']].rename(
            columns={'カテゴリ表示順12': '表示順', 'チェックカテゴリ名12': '大項目名称'})
        df_category13 = df2[['帳票パターンNo', 'カテゴリ表示順13', 'チェックカテゴリ名13']].rename(
            columns={'カテゴリ表示順13': '表示順', 'チェックカテゴリ名13': '大項目名称'})
        df_category14 = df2[['帳票パターンNo', 'カテゴリ表示順14', 'チェックカテゴリ名14']].rename(
            columns={'カテゴリ表示順14': '表示順', 'チェックカテゴリ名14': '大項目名称'})
        df_category15 = df2[['帳票パターンNo', 'カテゴリ表示順15', 'チェックカテゴリ名15']].rename(
            columns={'カテゴリ表示順15': '表示順', 'チェックカテゴリ名15': '大項目名称'})
        df_category16 = df2[['帳票パターンNo', 'カテゴリ表示順16', 'チェックカテゴリ名16']].rename(
            columns={'カテゴリ表示順16': '表示順', 'チェックカテゴリ名16': '大項目名称'})
        df_category17 = df2[['帳票パターンNo', 'カテゴリ表示順17', 'チェックカテゴリ名17']].rename(
            columns={'カテゴリ表示順17': '表示順', 'チェックカテゴリ名17': '大項目名称'})
        df_category18 = df2[['帳票パターンNo', 'カテゴリ表示順18', 'チェックカテゴリ名18']].rename(
            columns={'カテゴリ表示順18': '表示順', 'チェックカテゴリ名18': '大項目名称'})
        df_category19 = df2[['帳票パターンNo', 'カテゴリ表示順19', 'チェックカテゴリ名19']].rename(
            columns={'カテゴリ表示順19': '表示順', 'チェックカテゴリ名19': '大項目名称'})
        df_category20 = df2[['帳票パターンNo', 'カテゴリ表示順20', 'チェックカテゴリ名20']].rename(
            columns={'カテゴリ表示順20': '表示順', 'チェックカテゴリ名20': '大項目名称'})

        # データフレームをリストに格納
        df_list = [
            df_category1, df_category2, df_category3, df_category4, df_category5,
            df_category6, df_category7, df_category8, df_category9, df_category10,
            df_category11, df_category12, df_category13, df_category14, df_category15,
            df_category16, df_category17, df_category18, df_category19, df_category20
        ]
        # データフレームを縦に連結
        combined_df = pd.concat(df_list, ignore_index=True)
        combined_df = combined_df.sort_values(['帳票パターンNo'])
        # 更新操作
        count = 0
        for i, row in combined_df.iterrows():
            count += 1
            if count > 20:
                count = 1

            if row["帳票パターンNo"] is not None:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
                    チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
                    チェックflg,チェック,作業者名flg,作業者名,Del_flg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                    """,
                    (row["帳票パターンNo"], count, 1, 1, "", 1, "", 1,
                     "", 1, "", 1, "", 1, "", 1, "", 0),
                )
        conn.commit()

        # データベースの値を取得する
        sql = f'select * from check_item_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df = df.sort_values(['帳票パターンNo', 'カテゴリNo', '項目表示順'])

    def get_selectkey():

        # セッションステートの初期化 ここでセッションを持たないと初期化されてしまう
        if 'selected_index1' not in st.session_state:
            st.session_state.selected_index1 = 0
        if 'selected_index2' not in st.session_state:
            st.session_state.selected_index2 = 0
        if 'selected_index3' not in st.session_state:
            st.session_state.selected_index3 = 0

        # プレースホルダー
        col1, col2 = st.columns([1, 1])
        with col1:
            c1 = st.empty()
        with col2:
            c2 = st.empty()
        c3 = st.empty()

        # 各種処理
        # 帳票パターンテーブルからデータを取得する
        sql = f'select 帳票パターンNo,帳票名 from report_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df = df.sort_values(['帳票パターンNo'])

        # 各行を[No:詳細]の形式に変換してリストに追加
        select_list1 = []
        for index, row in df.iterrows():
            select_list1.append(
                f"パターンNo：{row['帳票パターンNo']}　帳票名：{row['帳票名']}")
        cp = c1.selectbox('①帳票パターン選択', select_list1,
                          index=st.session_state.selected_index1)
        # # 選択したindex番号をセッションに入れておく（戻らないようにする）
        # if st.session_state.selected_index1 != select_list1.index(cp):
        #     del st.session_state["selected_index2"]
        #     del st.session_state["selected_index3"]

       # st.session_state.selected_index1 = select_list1.index(cp)

        # 「パターンNo：」の後の部分を抽出
        start_index = cp.find("パターンNo：") + len("パターンNo：")
        remaining_str = cp[start_index:].strip()

        # 最初の全角スペースの位置を見つける
        space_index = remaining_str.find("　")

        # 数字部分を切り出して整数に変換
        pattern_no = int(remaining_str[:space_index])

        # 帳票パターンテーブルからデータを取得する
        sql = f'select * from report_type_table where 帳票パターンNo = {pattern_no}'
        df2 = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')

        # 縦列への変更
        df_category1 = df2[['カテゴリ表示順1', 'チェックカテゴリ名1']].rename(
            columns={'カテゴリ表示順1': '表示順', 'チェックカテゴリ名1': '大項目名称'})
        df_category2 = df2[['カテゴリ表示順2', 'チェックカテゴリ名2']].rename(
            columns={'カテゴリ表示順2': '表示順', 'チェックカテゴリ名2': '大項目名称'})
        df_category3 = df2[['カテゴリ表示順3', 'チェックカテゴリ名3']].rename(
            columns={'カテゴリ表示順3': '表示順', 'チェックカテゴリ名3': '大項目名称'})
        df_category4 = df2[['カテゴリ表示順4', 'チェックカテゴリ名4']].rename(
            columns={'カテゴリ表示順4': '表示順', 'チェックカテゴリ名4': '大項目名称'})
        df_category5 = df2[['カテゴリ表示順5', 'チェックカテゴリ名5']].rename(
            columns={'カテゴリ表示順5': '表示順', 'チェックカテゴリ名5': '大項目名称'})
        df_category6 = df2[['カテゴリ表示順6', 'チェックカテゴリ名6']].rename(
            columns={'カテゴリ表示順6': '表示順', 'チェックカテゴリ名6': '大項目名称'})
        df_category7 = df2[['カテゴリ表示順7', 'チェックカテゴリ名7']].rename(
            columns={'カテゴリ表示順7': '表示順', 'チェックカテゴリ名7': '大項目名称'})
        df_category8 = df2[['カテゴリ表示順8', 'チェックカテゴリ名8']].rename(
            columns={'カテゴリ表示順8': '表示順', 'チェックカテゴリ名8': '大項目名称'})
        df_category9 = df2[['カテゴリ表示順9', 'チェックカテゴリ名9']].rename(
            columns={'カテゴリ表示順9': '表示順', 'チェックカテゴリ名9': '大項目名称'})
        df_category10 = df2[['カテゴリ表示順10', 'チェックカテゴリ名10']].rename(
            columns={'カテゴリ表示順10': '表示順', 'チェックカテゴリ名10': '大項目名称'})
        df_category11 = df2[['カテゴリ表示順11', 'チェックカテゴリ名11']].rename(
            columns={'カテゴリ表示順11': '表示順', 'チェックカテゴリ名11': '大項目名称'})
        df_category12 = df2[['カテゴリ表示順12', 'チェックカテゴリ名12']].rename(
            columns={'カテゴリ表示順12': '表示順', 'チェックカテゴリ名12': '大項目名称'})
        df_category13 = df2[['カテゴリ表示順13', 'チェックカテゴリ名13']].rename(
            columns={'カテゴリ表示順13': '表示順', 'チェックカテゴリ名13': '大項目名称'})
        df_category14 = df2[['カテゴリ表示順14', 'チェックカテゴリ名14']].rename(
            columns={'カテゴリ表示順14': '表示順', 'チェックカテゴリ名14': '大項目名称'})
        df_category15 = df2[['カテゴリ表示順15', 'チェックカテゴリ名15']].rename(
            columns={'カテゴリ表示順15': '表示順', 'チェックカテゴリ名15': '大項目名称'})
        df_category16 = df2[['カテゴリ表示順16', 'チェックカテゴリ名16']].rename(
            columns={'カテゴリ表示順16': '表示順', 'チェックカテゴリ名16': '大項目名称'})
        df_category17 = df2[['カテゴリ表示順17', 'チェックカテゴリ名17']].rename(
            columns={'カテゴリ表示順17': '表示順', 'チェックカテゴリ名17': '大項目名称'})
        df_category18 = df2[['カテゴリ表示順18', 'チェックカテゴリ名18']].rename(
            columns={'カテゴリ表示順18': '表示順', 'チェックカテゴリ名18': '大項目名称'})
        df_category19 = df2[['カテゴリ表示順19', 'チェックカテゴリ名19']].rename(
            columns={'カテゴリ表示順19': '表示順', 'チェックカテゴリ名19': '大項目名称'})
        df_category20 = df2[['カテゴリ表示順20', 'チェックカテゴリ名20']].rename(
            columns={'カテゴリ表示順20': '表示順', 'チェックカテゴリ名20': '大項目名称'})

        # データフレームをリストに格納
        df_list = [
            df_category1, df_category2, df_category3, df_category4, df_category5,
            df_category6, df_category7, df_category8, df_category9, df_category10,
            df_category11, df_category12, df_category13, df_category14, df_category15,
            df_category16, df_category17, df_category18, df_category19, df_category20
        ]
        # データフレームを縦に連結
        combined_df = pd.concat(df_list, ignore_index=True)
        # "表示順"の値が99でない行をフィルタリング
        category_df = combined_df[combined_df['表示順'] != 99]
        select_list2 = []
        for index, row in category_df.iterrows():
            mei = row['大項目名称']
            if mei == "":
                mei = "登録無し"
            if mei == " ":
                mei = "登録無し"
            if mei == "　":
                mei = "登録無し"
            select_list2.append(
                f"カテゴリ表示順：{row['表示順']}　カテゴリ名：{mei}")

        if select_list2 == []:
            c2.write(" ②大項目の登録がありません")
            return pattern_no, 999, 999
        cp2 = c2.selectbox(
            f'②大項目選択 （{cp}）', select_list2, index=st.session_state.selected_index2)
        # 選択したindex番号をセッションに入れておく（戻らないようにする）
        # if st.session_state.selected_index2 != select_list2.index(cp2):
        #     del st.session_state["selected_index3"]
        # st.session_state.selected_index2 = select_list2.index(cp2)

        start_index2 = cp2.find("カテゴリ表示順：") + len("カテゴリ表示順：")
        remaining_str2 = cp2[start_index2:].strip()

        # 最初の全角スペースの位置を見つける
        space_index2 = remaining_str2.find("　")

        # 数字部分を切り出して整数に変換
        number2 = int(remaining_str2[:space_index2])
        # インデックスを取得
        category_no = combined_df.index[combined_df['表示順'] == number2][0]
        category_no += 1

        # 帳票パターンテーブルからデータを取得する
        sql = f'select * from check_item_table where 帳票パターンNo = {pattern_no} and カテゴリNo = {category_no} and Del_flg <> 1 '
        df3 = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df3 = df3.sort_values(['項目表示順'])
        # 各行を[No:詳細]の形式に変換してリストに追加
        select_list3 = []
        select_dict3 = {}
        for index, row in df3.iterrows():
            mei = row['チェック項目']
            if mei == "":
                mei = "未使用"
            if mei == " ":
                mei = "未使用"
            if mei == "　":
                mei = "未使用"
            mae = row['前トグル']
            if row['前トグルflg'] == 1:
                mae = "未使用"

            nyuuryoku = row['入力欄']
            if row['入力欄flg'] == 1:
                nyuuryoku = "未使用"
            no = row['No']
            if row['Noflg'] == 1:
                no = "未使用"
            ato = row['後トグル']
            if row['後トグルflg'] == 1:
                ato = "未使用"
            ck = row['チェック']
            if row['チェックflg'] == 1:
                ck = "未使用"
            sagyousya = row['作業者名']
            if row['作業者名flg'] == 1:
                sagyousya = "未使用"
            checktext = f'''表示順：{row['項目表示順']}　チェック項目：{mei}　前トグル：{mae}　'''
            select_list3.append(checktext)
            select_dict3[row['項目No']] = checktext
        select_list3.append(f"新規追加")
        select_dict3[df3['項目No'].max() + 1] = "新規追加"

        cp3 = c3.selectbox('③チェック項目選択', select_list3,
                           index=st.session_state.selected_index3)
        # 選択したindex番号をセッションに入れておく（戻らないようにする）
        st.session_state.selected_index3 = select_list3.index(cp3)
        print(select_dict3.items)

        # 取得した値を元に辞書のkey（項目No）を取得
        koumoku_no = None
        for key, value in select_dict3.items():
            if value == cp3:
                koumoku_no = key
                break

        # 項目表示順の最大値もここで返却しておく
        hyoji_max = df3['項目表示順'].max() + 1

        # 全ての主キー＋表示順の最大+1を返却
        return (pattern_no, category_no, koumoku_no, hyoji_max)

    def get_table(pattern_no, category_no, koumoku_no, hyoji_no):

        # チェック項目テーブルからデータを取得
        sql = f'select * from check_item_table where 帳票パターンNo = {pattern_no} and カテゴリNo = {category_no} and 項目No = {koumoku_no}'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')

        # 空の時は新規登録
        if df.empty:
            shinki = pd.DataFrame({'帳票パターンNo': [pattern_no], 'カテゴリNo': [category_no], '項目No': [koumoku_no], '項目表示順': [hyoji_no],
                                   'チェック項目': [''], '前トグルflg': [1], '前トグル': [''], '入力欄flg': [1], '入力欄': [''], 'Noflg': [1], 'No': [''],
                                   '後トグルflg': [1], '後トグル': [''], 'チェックflg': [1], 'チェック': [''], '作業者名flg': [1], '作業者名': ['']})
            df = pd.concat([df, shinki], ignore_index=True)
        return (df)

    def db_delete0(pattern_no, category_no, koumoku_no):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0 )
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            Del_flg = 1
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, ""),
        )
        conn.commit()

    def db_update0(pattern_no, category_no, koumoku_no, hyouji):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? , ?)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            項目表示順 = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), int(hyouji), "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", 0, int(hyouji)),
        )
        conn.commit()

    def db_update1(pattern_no, category_no, koumoku_no, flg1, in1):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            チェック項目 = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", str(in1)),
        )
        conn.commit()

    def db_update2(pattern_no, category_no, koumoku_no, flg2, in2):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            前トグルflg = ?,
            前トグル = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", int(flg2), str(in2)),
        )
        conn.commit()

    def db_update3(pattern_no, category_no, koumoku_no, flg3):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            入力欄flg = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", int(flg3)),
        )
        conn.commit()

    def db_update4(pattern_no, category_no, koumoku_no, flg4):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            Noflg = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", int(flg4)),
        )
        conn.commit()

    def db_update5(pattern_no, category_no, koumoku_no, flg5, in5):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            後トグルflg = ?,
            後トグル = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", int(flg5), str(in5)),
        )
        conn.commit()

    def db_update6(pattern_no, category_no, koumoku_no, flg6):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            チェックflg = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", int(flg6)),
        )
        conn.commit()

    def db_update7(pattern_no, category_no, koumoku_no, flg7):

        # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')):
            shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\hontai_seizo.db',
                        os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}hontai_seizo.db")

        # 本処理
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 更新操作
        cur.execute(
            """
            INSERT INTO check_item_table ( 帳票パターンNo, カテゴリNo,項目No,項目表示順,
            チェック項目,前トグルflg,前トグル,入力欄flg,入力欄,Noflg,No,後トグルflg,後トグル,
            チェックflg,チェック,作業者名flg,作業者名,Del_flg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,0)
            ON CONFLICT(帳票パターンNo,カテゴリNo,項目No) DO UPDATE SET
            作業者名flg = ?,
            Del_flg = 0
            """,
            # intへのキャストを噛まさないとBLOB形式になる
            (int(pattern_no), int(category_no), int(koumoku_no), 1, "", 1, "", 1,
             "", 1, "", 1, "", 1, "", 1, "", int(flg7)),
        )
        conn.commit()

    def main():

        st.set_page_config(
            page_title='チェック大項目登録',
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

        # 処理
        st.markdown('### チェック詳細項目登録')
        st.markdown('チェック項目の詳細項目を登録します。')

        # 初期データ作成処理
        db_create()

        # 画面上部表示のセレクトボックスをセット
        pattern_no, category_no, koumoku_no, hyoji_no = get_selectkey()

        # Noneは数値でリセット
        if np.isnan(koumoku_no):
            koumoku_no = 1
        if np.isnan(hyoji_no):
            hyoji_no = 1
        # セレクトボックスを基に編集対象のテーブルをゲット
        df = get_table(pattern_no, category_no, koumoku_no, hyoji_no)

        # タブで表示を区切る
        tab_titles = ['　表示順編集　', '　チェック項目　', '　　前トグル　　',
                      '　　入力欄　　', '　　　No　　　', '　　後トグル　　', '　　チェック　　', '　　作業者名　　']
        tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_titles)
        # タブ0　表示非表示
        # 項目削除と表示順変更
        with tab0:
            col01, col02, col03, col04 = st.columns([2, 0.3, 2, 1])
            with col01:
                input0 = st.empty()  # 入力欄(表示順変更　numinputで良いと思う)
                up0 = st.empty()  # 更新ボタン
            with col02:
                st.write("")
            with col03:
                st.write("")
                st.write("")
                tc0 = st.empty()  # 削除ﾁｪｯｸﾎﾞｯｸｽ
                del0 = st.empty()  # 削除ボタン
        # タブ１　チェック項目
        with tab1:
            tc1 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input1 = st.empty()  # 入力欄
            up1 = st.empty()  # 更新ボタン

        with tab2:
            # タブ２　前トグル
            tc2 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input2 = st.empty()  # 入力欄
            up2 = st.empty()  # 更新ボタン
        # タブ３　入力欄
        with tab3:
            tc3 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input3 = st.empty()  # 入力欄（入力初期値）
            up3 = st.empty()  # 更新ボタン
        # タブ４　No
        with tab4:
            tc4 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input4 = st.empty()  # 入力欄
            up4 = st.empty()  # 更新ボタン
        # タブ５　後トグル
        with tab5:
            tc5 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input5 = st.empty()  # 入力欄
            up5 = st.empty()  # 更新ボタン
        # タブ６　チェック
        with tab6:
            tc6 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input6 = st.empty()  # 入力欄
            up6 = st.empty()  # 更新ボタン
        # タブ７　作業者名
        with tab7:
            tc7 = st.empty()  # 使用有無ﾁｪｯｸﾎﾞｯｸｽ
            input7 = st.empty()  # 入力欄
            up7 = st.empty()  # 更新ボタン

        # 処理0
        # セッションステートの初期化 ここでセッションを持たないと初期化されてしまう
        if 'delete_value' not in st.session_state:
            st.session_state.delete_value = 0

        a = st.session_state.delete_value
        if tc0.checkbox('このチェック項目を削除する', value=st.session_state.delete_value, key="delete_value"):
            # 削除ボタン
            if del0.button("★項目削除★", key="button00"):
                db_delete0(pattern_no, category_no, koumoku_no)
                # st.session_state.clear()
                del st.session_state["delete_value"]
                st.session_state.clear()
                st.rerun()
                st.write("削除しました")
        hyouji = input0.number_input(
            f"表示順変更（現在の表示順：{df.at[0, '項目表示順']}）", value=df.at[0, '項目表示順'], min_value=1, max_value=99, step=1)
        # 更新ボタン
        # if up0.button("更新", key="button01"):
        #     # 更新項目が多く、データフレームの再取得が面倒なため個別に更新処理を作成
        #     db_update0(pattern_no, category_no, koumoku_no, hyouji)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理1
        if df.at[0, 'チェック項目'] == "":
            flg1 = 0
        else:
            flg1 = 1
        if tc1.checkbox('"チェック項目"欄を使用する', value=flg1):
            in1 = input1.text_input("チェック項目名", value=df.at[0, 'チェック項目'])
            flg1 = 0
        else:
            in1 = ""  # チェック項目は全角スペースを入れておく
            flg1 = 1
          # 更新ボタン
        # if up1.button("更新", key="button1"):
        #     db_update1(pattern_no, category_no, koumoku_no, flg1, in1)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理2
        if tc2.checkbox('"前トグル"欄を使用する', value=df.at[0, '前トグルflg']):

            # 文字列をリストに変換
            string_list = df.at[0, '前トグル']
            list_data = string_list.strip("[]").split(",")

            # リストをDataFrameに変換
            tg2_df = pd.DataFrame(list_data, columns=["前トグル"])

            # データフレームエディター
            in2_df = input2.data_editor(
                tg2_df.reset_index(drop=True), num_rows="dynamic")

            # データフレームをリストに変換し文字列に変換
            list_data = in2_df['前トグル'].dropna().tolist()
            in2 = "[" + ",".join(list_data) + "]"
            flg2 = 0
        else:
            in2 = ""
            flg2 = 1
        # # 更新ボタン
        # if up2.button("更新", key="button2"):
        #     db_update2(pattern_no, category_no, koumoku_no, flg2, in2)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理3
        if tc3.checkbox('"入力欄"欄を使用する', value=df.at[0, '入力欄flg']):
            # in3 = input3.text_input("入力欄", "") #入力欄はINPUT無し
            flg3 = 0
        else:
            flg3 = 1
        # 更新ボタン
        # if up3.button("更新", key="button3"):
        #     db_update3(pattern_no, category_no, koumoku_no, flg3)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理4
        if tc4.checkbox('"No"欄を使用する',):
            # in4 = input4.text_input("No", df.at[0, 'No'])
            flg4 = 0
        else:
            # in4 = ""
            flg4 = 1

          # 更新ボタン
        # if up4.button("更新", key="button4"):
        #     db_update4(pattern_no, category_no, koumoku_no, flg4)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理5
        if tc5.checkbox('"後トグル"欄を使用する', value=df.at[0, '後トグルflg']):
            # 文字列をリストに変換
            string_list2 = df.at[0, '後トグル']
            list_data2 = string_list2.strip("[]").split(",")

            # リストをDataFrameに変換
            tg5_df = pd.DataFrame(list_data2, columns=["後トグル"])

            # データフレームエディター
            in5_df = input5.data_editor(
                tg5_df.reset_index(drop=True), num_rows="dynamic")

            # データフレームをリストに変換し文字列に変換
            list_data = in5_df['後トグル'].dropna().tolist()
            in5 = "[" + ",".join(list_data) + "]"
            flg5 = 0
        else:
            in5 = ""
            flg5 = 1
          # 更新ボタン
        # if up5.button("更新", key="button5"):
        #     db_update5(pattern_no, category_no, koumoku_no, flg5, in5)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理6
        if tc6.checkbox('"チェック"欄を使用する', value=df.at[0, 'チェックflg']):
            flg6 = 0
        else:
            flg6 = 1
          # 更新ボタン
        # if up6.button("更新", key="button6"):
        #     db_update6(pattern_no, category_no, koumoku_no, flg6)
        #     st.rerun()
        #     st.write("更新完了")

        # 処理7
        if tc7.checkbox('"作業者名"欄を使用する', value=df.at[0, '作業者名flg']):
            # in7 = input7.text_input("作業者名", "")
            flg7 = 0
        else:
            flg7 = 1
          # 更新ボタン
        # if up7.button("更新", key="button7"):
        #     db_update7(pattern_no, category_no, koumoku_no, flg7)
        #     st.rerun()
        #     st.write("更新完了")
        st.divider()
        st.write("")
        st.write("")
        if st.button("更新", key="buttonX"):
            db_update0(pattern_no, category_no, koumoku_no, hyouji)
            db_update1(pattern_no, category_no, koumoku_no, flg1, in1)
            db_update2(pattern_no, category_no, koumoku_no, flg2, in2)
            db_update3(pattern_no, category_no, koumoku_no, flg3)
            db_update4(pattern_no, category_no, koumoku_no, flg4)
            db_update5(pattern_no, category_no, koumoku_no, flg5, in5)
            db_update6(pattern_no, category_no, koumoku_no, flg6)
            db_update7(pattern_no, category_no, koumoku_no, flg7)
            st.rerun()

        st.write("")
        st.write("")
        st.write("")
        df

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
