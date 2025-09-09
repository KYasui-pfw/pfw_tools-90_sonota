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
                    機種区分 TEXT,
                    カテゴリNo INTEGER,
                    カテゴリ区分 INTEGER,
                    表示順 INTEGER,
                    チェック項目 TEXT,
                    前トグルflg INTEGER,
                    前トグル TEXT,
                    入力欄flg INTEGER,
                    Noflg INTEGER,
                    後トグルflg INTEGER,
                    後トグル TEXT,
                    チェックflg INTEGER,
                    作業者名flg INTEGER,
                    PRIMARY KEY (機種区分, カテゴリNo,カテゴリ区分, 表示順))''')

        # 帳票種別テーブルを基に更新する
        sql = f'select * from report_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df2 = df.sort_values(['帳票No'])

        # 縦列への変更
        df_category1 = df2[['機種区分', 'カテゴリ区分1']].rename(
            columns={'カテゴリ区分1': 'カテゴリ区分'})
        df_category2 = df2[['機種区分', 'カテゴリ区分2']].rename(
            columns={'カテゴリ区分2': 'カテゴリ区分'})
        df_category3 = df2[['機種区分', 'カテゴリ区分3']].rename(
            columns={'カテゴリ区分3': 'カテゴリ区分'})
        df_category4 = df2[['機種区分', 'カテゴリ区分4']].rename(
            columns={'カテゴリ区分4': 'カテゴリ区分'})
        df_category5 = df2[['機種区分', 'カテゴリ区分5']].rename(
            columns={'カテゴリ区分5': 'カテゴリ区分'})
        df_category6 = df2[['機種区分', 'カテゴリ区分6']].rename(
            columns={'カテゴリ区分6': 'カテゴリ区分'})
        df_category7 = df2[['機種区分', 'カテゴリ区分7']].rename(
            columns={'カテゴリ区分7': 'カテゴリ区分'})
        df_category8 = df2[['機種区分', 'カテゴリ区分8']].rename(
            columns={'カテゴリ区分8': 'カテゴリ区分'})
        df_category9 = df2[['機種区分', 'カテゴリ区分9']].rename(
            columns={'カテゴリ区分9': 'カテゴリ区分'})
        df_category10 = df2[['機種区分', 'カテゴリ区分10']].rename(
            columns={'カテゴリ区分10': 'カテゴリ区分'})
        df_category11 = df2[['機種区分', 'カテゴリ区分11']].rename(
            columns={'カテゴリ区分11': 'カテゴリ区分'})
        df_category12 = df2[['機種区分', 'カテゴリ区分12']].rename(
            columns={'カテゴリ区分12': 'カテゴリ区分'})
        df_category13 = df2[['機種区分', 'カテゴリ区分13']].rename(
            columns={'カテゴリ区分13': 'カテゴリ区分'})
        df_category14 = df2[['機種区分', 'カテゴリ区分14']].rename(
            columns={'カテゴリ区分14': 'カテゴリ区分'})
        df_category15 = df2[['機種区分', 'カテゴリ区分15']].rename(
            columns={'カテゴリ区分15': 'カテゴリ区分'})
        df_category16 = df2[['機種区分', 'カテゴリ区分16']].rename(
            columns={'カテゴリ区分16': 'カテゴリ区分'})
        df_category17 = df2[['機種区分', 'カテゴリ区分17']].rename(
            columns={'カテゴリ区分17': 'カテゴリ区分'})
        df_category18 = df2[['機種区分', 'カテゴリ区分18']].rename(
            columns={'カテゴリ区分18': 'カテゴリ区分'})
        df_category19 = df2[['機種区分', 'カテゴリ区分19']].rename(
            columns={'カテゴリ区分19': 'カテゴリ区分'})
        df_category20 = df2[['機種区分', 'カテゴリ区分20']].rename(
            columns={'カテゴリ区分20': 'カテゴリ区分'})
        df_category21 = df2[['機種区分', 'カテゴリ区分21']].rename(
            columns={'カテゴリ区分21': 'カテゴリ区分'})
        df_category22 = df2[['機種区分', 'カテゴリ区分22']].rename(
            columns={'カテゴリ区分22': 'カテゴリ区分'})
        df_category23 = df2[['機種区分', 'カテゴリ区分23']].rename(
            columns={'カテゴリ区分23': 'カテゴリ区分'})
        df_category24 = df2[['機種区分', 'カテゴリ区分24']].rename(
            columns={'カテゴリ区分24': 'カテゴリ区分'})
        df_category25 = df2[['機種区分', 'カテゴリ区分25']].rename(
            columns={'カテゴリ区分25': 'カテゴリ区分'})
        df_category26 = df2[['機種区分', 'カテゴリ区分26']].rename(
            columns={'カテゴリ区分26': 'カテゴリ区分'})
        df_category27 = df2[['機種区分', 'カテゴリ区分27']].rename(
            columns={'カテゴリ区分27': 'カテゴリ区分'})
        df_category28 = df2[['機種区分', 'カテゴリ区分28']].rename(
            columns={'カテゴリ区分28': 'カテゴリ区分'})
        df_category29 = df2[['機種区分', 'カテゴリ区分29']].rename(
            columns={'カテゴリ区分29': 'カテゴリ区分'})
        df_category30 = df2[['機種区分', 'カテゴリ区分30']].rename(
            columns={'カテゴリ区分30': 'カテゴリ区分'})

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
        combined_df = combined_df.sort_values(['機種区分'])
        # 更新操作
        count = 0
        for i, row in combined_df.iterrows():
            count += 1
            if count > 30:
                count = 1
            for n in range(1, 11):
                # if row["機種区分"] is not None:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO check_item_table ( 機種区分, カテゴリNo,カテゴリ区分,
                    表示順,チェック項目,前トグルflg,前トグル,入力欄flg,Noflg,後トグルflg,後トグル,
                    チェックflg,作業者名flg)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (row["機種区分"], count, n, 1,
                        "", 0, "", 0, 0, 0, "", 0, 0),
                )
        conn.commit()

    def get_selectkey():

        # # セッションステートの初期化 ここでセッションを持たないと初期化されてしまう
        # if 'selected_index1' not in st.session_state:
        #     # st.session_state.selected_index1 = 0
        #     st.rerun()
        # if 'selected_index2' not in st.session_state:
        #     # st.session_state.selected_index2 = 0
        #     st.rerun()
        # if 'selected_index3' not in st.session_state:
        #     # st.session_state.selected_index3 = 0
        #     st.rerun()

        # プレースホルダー
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            c1 = st.empty()
        with col2:
            c2 = st.empty()
        with col3:
            c3 = st.empty()

        # 各行を[No:詳細]の形式に変換してリストに追加
        select_list1 = ['SK', 'DK']
        cp = c1.selectbox('①機種区分選択', select_list1,
                          # index=st.session_state.selected_index1)
                          )

        # 帳票パターンテーブルからデータを取得する
        sql = 'SELECT * FROM model_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')

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
        # "表示順"の値が99でない行をフィルタリング
        combined_df = combined_df[combined_df['機種区分']
                                  == cp].reset_index(drop=True)
        combined_df.index = combined_df.index + 1
        category_df = combined_df[combined_df['カテゴリ名'] != ""]

        select_list2 = []
        for index, row in category_df.iterrows():
            mei = row['カテゴリ名']
            if mei == "":
                mei = "登録無し"
            if mei == " ":
                mei = "登録無し"
            if mei == "　":
                mei = "登録無し"
            select_list2.append(str(index) + "："+mei)
        if select_list2 == []:
            c2.write(" ②大項目の登録がありません")
            return cp, 999, 999
        cp2 = c2.selectbox(
            # f'②カテゴリ名選択', select_list2, index=st.session_state.selected_index2)
            f'②カテゴリ名選択', select_list2)

        # 最初の：の位置を見つける　⇒ 数字部分を切り出して整数に変換
        kugiri_index2 = cp2.find("：")
        number2 = int(cp2[:kugiri_index2])

        # カテゴリ区分
        select_list3 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        cp3 = c3.selectbox(
            # f'②カテゴリ区分', select_list3, index=st.session_state.selected_index3)
            f'②カテゴリ区分', select_list3)

        # 帳票パターンテーブルからデータを取得する
        sql = f'select * from check_item_table where 機種区分 = "{cp}" and カテゴリNo = {number2} and カテゴリ区分 = {cp3}'
        df3 = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df3 = df3.sort_values(['表示順'])
        return (df3, cp3)

    def check_data_update(edf, df):
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

        # 削除操作
        original_hyojino = set(df["表示順"])
        edited_hyojino = set(edf["表示順"])
        hyojino_to_delete = original_hyojino - edited_hyojino
        for hyojino_to_delete in hyojino_to_delete:
            cur.execute(
                f"DELETE FROM check_item_table WHERE 機種区分 = ? and カテゴリNo = ? and カテゴリ区分 = ? and 表示順 = ?", (str(df.loc[0, '機種区分']), int(df.loc[0, 'カテゴリNo']), int(df.loc[0, 'カテゴリ区分']), int(hyojino_to_delete),))
        for _, row in edf.iterrows():
            # 組立番号が既に存在するか確認
            cur.execute(
                "SELECT * FROM check_item_table WHERE 機種区分 = ? and カテゴリNo = ? and カテゴリ区分 = ? and 表示順 = ?", (str(row['機種区分']), int(row['カテゴリNo']), int(row['カテゴリ区分']), int(row['表示順']),))
            existing_records = cur.fetchall()
            if not existing_records:
                # 条件1: 組立番号が重複していない場合、INSERT
                cur.execute("""
              INSERT INTO check_item_table (機種区分, カテゴリNo,カテゴリ区分,表示順,
                    チェック項目,前トグルflg,前トグル,入力欄flg,Noflg,後トグルflg,後トグル,
                    チェックflg,作業者名flg)
                    VALUES (?,  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """,
                            (str(row['機種区分']), int(row['カテゴリNo']), int(row['カテゴリ区分']), int(row['表示順']), str(row['チェック項目']), int(row['前トグルflg']),
                             str(row['前トグル']), int(row['入力欄flg']), int(row['Noflg']), int(row['後トグルflg']), str(row['後トグル']), int(row['チェックflg']), int(row['作業者名flg'])))
            else:
                # 条件2と条件3: 組立番号が重複している場合、UPDATE
                cur.execute("""
                    UPDATE check_item_table
                    SET
                        チェック項目 = ?,
                        前トグルflg = ?,
                        前トグル = ?,
                        入力欄flg = ?,
                        Noflg = ?,
                        後トグルflg = ?,
                        後トグル = ?,
                        チェックflg = ?,
                        作業者名flg = ?
                    WHERE
                        機種区分 = ? AND カテゴリNo = ? AND カテゴリ区分 = ? AND 表示順 = ?
                """, (
                    str(row['チェック項目']), int(row['前トグルflg']),
                    str(row['前トグル']), int(row['入力欄flg']), int(row['Noflg']),
                    int(row['後トグルflg']), str(row['後トグル']), int(row['チェックflg']),
                    int(row['作業者名flg']), str(row['機種区分']), int(row['カテゴリNo']),
                    int(row['カテゴリ区分']), int(row['表示順'])
                ))

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()
        return

    def main():

        st.set_page_config(
            page_title='チェック項目登録',
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

        # セッション状態の初期化 ★これでdata_editorを強制再表示させることが可能！1/3
        if 'editor_key' not in st.session_state:
            st.session_state.editor_key = 0

        st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

        # 処理
        st.markdown('### チェック項目登録')

        # 初期データ作成処理
        db_create()

        # 画面上部表示のセレクトボックスをセット
        df, cp3 = get_selectkey()

        st.divider()
        st.write("チェック項目の編集")

        # 不要列を削除(後の結合のため,before_edited_dfを退避)
        before_edited_df = df.copy()
        df = df.drop(columns=['機種区分', 'カテゴリNo', 'カテゴリ区分'])

        # flgの置換
        df['前トグルflg'] = df['前トグルflg'].replace({1: '使用', 0: '未使用'})
        df['入力欄flg'] = df['入力欄flg'].replace({1: '使用', 0: '未使用'})
        df['Noflg'] = df['Noflg'].replace({1: '使用', 0: '未使用'})
        df['後トグルflg'] = df['後トグルflg'].replace({1: '使用', 0: '未使用'})
        df['チェックflg'] = df['チェックflg'].replace({1: '使用', 0: '未使用'})
        df['作業者名flg'] = df['作業者名flg'].replace({1: '使用', 0: '未使用'})

        # エディターを直接起動する
        kubun_list = ["使用", "未使用"]
        edited_df = st.data_editor(df.reset_index(drop=True),
                                   column_config={
            '前トグル': {'width': 200},
            '後トグル': {'width': 200},
            "表示順": st.column_config.SelectboxColumn(
                label="表示順",
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                         "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
                                                 "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]),
            "前トグルflg": st.column_config.SelectboxColumn(label="前トグルflg", options=kubun_list),
            "入力欄flg": st.column_config.SelectboxColumn(label="入力欄flg", options=kubun_list),
            "Noflg": st.column_config.SelectboxColumn(label="Noflg", options=kubun_list),
            "後トグルflg": st.column_config.SelectboxColumn(label="後トグルflg", options=kubun_list),
            "チェックflg": st.column_config.SelectboxColumn(label="チェックflg", options=kubun_list),
            "作業者名flg": st.column_config.SelectboxColumn(label="作業者名flg", options=kubun_list),
        },
            # ★これでdata_editorを強制再表示させることが可能2/3
            key=f"editor_{st.session_state.editor_key}",
            hide_index=True, num_rows="dynamic")

       # if not edited_df.empty:
        # "使用"を1、"未使用"を0に置き換える
        edited_df['前トグルflg'] = edited_df['前トグルflg'].replace(
            {'使用': 1, '未使用': 0})
        edited_df['入力欄flg'] = edited_df['入力欄flg'].replace(
            {'使用': 1, '未使用': 0})
        edited_df['Noflg'] = edited_df['Noflg'].replace(
            {'使用': 1, '未使用': 0})
        edited_df['後トグルflg'] = edited_df['後トグルflg'].replace(
            {'使用': 1, '未使用': 0})
        edited_df['チェックflg'] = edited_df['チェックflg'].replace(
            {'使用': 1, '未使用': 0})
        edited_df['作業者名flg'] = edited_df['作業者名flg'].replace(
            {'使用': 1, '未使用': 0})

        # 更新用に帳票パターンNoとカテゴリNoを整える
        edited_df.insert(0, 'カテゴリ区分', before_edited_df.loc[0, 'カテゴリ区分'])
        edited_df.insert(0, 'カテゴリNo', before_edited_df.loc[0, 'カテゴリNo'])
        edited_df.insert(0, '機種区分', before_edited_df.loc[0, '機種区分'])

        # 表示順重複チェック
        duplicates = edited_df[edited_df.duplicated(
            subset=['表示順'], keep=False)]

        # 表示順NULLチェック
        null_rows = edited_df[edited_df['表示順'].isnull()]

        # 各種flgNULLチェック
        null_flgs = edited_df[(
            (edited_df['前トグルflg'].isnull()) | (edited_df['前トグルflg'] == "") |
            (edited_df['入力欄flg'].isnull()) | (edited_df['入力欄flg'] == "") |
            (edited_df['Noflg'].isnull()) | (edited_df['Noflg'] == "") |
            (edited_df['後トグルflg'].isnull()) | (edited_df['後トグルflg'] == "") |
            (edited_df['チェックflg'].isnull()) | (edited_df['チェックflg'] == "") |
            (edited_df['作業者名flg'].isnull()) | (edited_df['作業者名flg'] == ""))]

        if st.button("更新"):
            if not duplicates.empty:
                st.write("表示順が重複しています")
            elif not null_rows.empty:
                st.write("表示順が設定されていない行があります")
            elif not null_flgs.empty:
                st.write("使用有無が設定されていないflgがあります")
            elif edited_df["作業者名flg"].sum() == 0:
                st.write("最低でも一つは作業者名flgを[使用]にしてください")
            else:
                edited_df = edited_df.fillna("")
                check_data_update(edited_df, before_edited_df)

                # キー変更でエディター再生成　★これでdata_editorを強制再表示させることが可能3/3
                st.session_state.editor_key += 1
                st.rerun()
                st.write("更新完了")

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
