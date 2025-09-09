################################
# 　本体Gr製造チェックシート      #
# 　帳票テーブルの更新            #
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

    def db_get():

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
        cur.execute('''CREATE TABLE IF NOT EXISTS report_type_table(
                  帳票No INTEGER PRIMARY KEY,
                  機種区分 TEXT,
                  帳票名 TEXT,
                  行数 INTEGER,
                  カテゴリ区分1 INTEGER,
                  カテゴリ区分2 INTEGER,
                  カテゴリ区分3 INTEGER,
                  カテゴリ区分4 INTEGER,
                  カテゴリ区分5 INTEGER,
                  カテゴリ区分6 INTEGER,
                  カテゴリ区分7 INTEGER,
                  カテゴリ区分8 INTEGER,
                  カテゴリ区分9 INTEGER,
                  カテゴリ区分10 INTEGER,
                  カテゴリ区分11 INTEGER,
                  カテゴリ区分12 INTEGER,
                  カテゴリ区分13 INTEGER,
                  カテゴリ区分14 INTEGER,
                  カテゴリ区分15 INTEGER,
                  カテゴリ区分16 INTEGER,
                  カテゴリ区分17 INTEGER,
                  カテゴリ区分18 INTEGER,
                  カテゴリ区分19 INTEGER,
                  カテゴリ区分20 INTEGER,
                  カテゴリ区分21 INTEGER,
                  カテゴリ区分22 INTEGER,
                  カテゴリ区分23 INTEGER,
                  カテゴリ区分24 INTEGER,
                  カテゴリ区分25 INTEGER,
                  カテゴリ区分26 INTEGER,
                  カテゴリ区分27 INTEGER,
                  カテゴリ区分28 INTEGER,
                  カテゴリ区分29 INTEGER,
                  カテゴリ区分30 INTEGER
                  )''')

        # データベースの値を取得する
        sql = f'select 帳票No,帳票名 from report_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df = df.sort_values(['帳票No'])

        return (df)

    def db_update(edf, df):

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

        # 削除操作
        original_ids = set(zip(df["帳票No"]))
        edited_ids = set(zip(edf["帳票No"]))

        ids_to_delete = original_ids - edited_ids
        for id_to_delete in ids_to_delete:
            cur.execute(
                f"DELETE FROM report_type_table WHERE 帳票No = ?", (id_to_delete))

        # 更新操作
        model_type = ""
        for _, row in edf.iterrows():
            if row["帳票No"] < 200:
                model_type = "SK"
            else:
                model_type = "DK"
            if row["帳票No"] is not None:
                cur.execute(
                    """
                    INSERT INTO report_type_table ( 帳票No,機種区分, 帳票名,カテゴリ区分1,カテゴリ区分2,
                    カテゴリ区分3,カテゴリ区分4,カテゴリ区分5,カテゴリ区分6,カテゴリ区分7,
                    カテゴリ区分8,カテゴリ区分9,カテゴリ区分10,カテゴリ区分11,カテゴリ区分12,
                    カテゴリ区分13,カテゴリ区分14,カテゴリ区分15,カテゴリ区分16,カテゴリ区分17,
                    カテゴリ区分18,カテゴリ区分19,カテゴリ区分20,カテゴリ区分21,カテゴリ区分22,
                    カテゴリ区分23,カテゴリ区分24,カテゴリ区分25,カテゴリ区分26,カテゴリ区分27,
                    カテゴリ区分28,カテゴリ区分29,カテゴリ区分30)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(帳票No) DO UPDATE SET
                    帳票名 = excluded.帳票名
                    """,
                    (row["帳票No"], model_type, row["帳票名"], 99, 99, 99, 99, 99, 99,
                     99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99),
                )
        conn.commit()

    def main():

        st.set_page_config(
            page_title='帳票テーブル更新',
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
        st.markdown('### 帳票テーブル更新')
        st.markdown('SKは100番台、DKは200番台のNoを使用します　番号は自動採番です')
        seisan_col1, seisan_col2, seisan_col3, = st.columns([
            1, 3, 1])
        with seisan_col1:
            skdk_kubun = st.selectbox('機種区分選択', ['SK', 'DK'])

        with seisan_col2:
            # 最初にDBアップデートを行う
            df = db_get()
            df = df.sort_values(['帳票No'])
            df = df.fillna(' ')  # Noneデータ対策
            # 101～199がSK、201～299DK
            alldf = df  # デバッグ用
            if skdk_kubun == 'SK':
                df = df[(df['帳票No'] > 100) & (df['帳票No'] < 200)]
                add_num = 100
            elif skdk_kubun == 'DK':
                df = df[(df['帳票No'] > 200) & (df['帳票No'] < 300)]
                add_num = 200

            # 各行を[No:詳細]の形式に変換してリストに追加
            select_list = []
            for index, row in df.iterrows():
                select_list.append(
                    f"帳票No：{row['帳票No']}　帳票名：{row['帳票名']}")
            select_list.append('新規追加')
            cp = st.selectbox('帳票選択', select_list)

        if cp == '新規追加':
            number = len(select_list) + add_num
            chohyo_name = ""
            # 新規DFの作成
            df2 = pd.DataFrame({
                '帳票No': [number],
                '帳票名': [chohyo_name]
            })
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
            button = "更新"

        st.divider()
        st.write("帳票名の編集")
        # エディター
        edited_df = st.data_editor(df2.reset_index(drop=True),
                                   column_config={
            '帳票名': {'width': 300}
        },
            # hide_index=True, num_rows="dynamic")
            hide_index=True, disabled=["帳票No"])
        if st.button(button):
            db_update(edited_df, df2)
            st.rerun()
            st.write("更新完了")

        # # デバッグモード
        # edited_df = st.data_editor(alldf.reset_index(drop=True),
        #                            hide_index=True, num_rows="dynamic")
        # if st.button(button):
        #     db_update(edited_df, alldf)
        #     st.write("更新完了")
        st.markdown('###### ※過去データとの整合性を維持するため、追加した帳票は削除できません')

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
