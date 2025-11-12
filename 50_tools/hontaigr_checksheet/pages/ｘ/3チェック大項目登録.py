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
        # 編組織名テーブル作成
        cur.execute('''CREATE TABLE IF NOT EXISTS report_type_table(
                  帳票パターンNo INTEGER PRIMARY KEY,
                  帳票名 TEXT,
                  行数 INTEGER,
                  カテゴリ表示順1 INTEGER,
                  チェックカテゴリ名1 TEXT,
                  カテゴリ表示順2 INTEGER,
                  チェックカテゴリ名2 TEXT,
                  カテゴリ表示順3 INTEGER,
                  チェックカテゴリ名3 TEXT,
                  カテゴリ表示順4 INTEGER,
                  チェックカテゴリ名4 TEXT,
                  カテゴリ表示順5 INTEGER,
                  チェックカテゴリ名5 TEXT,
                  カテゴリ表示順6 INTEGER,
                  チェックカテゴリ名6 TEXT,
                  カテゴリ表示順7 INTEGER,
                  チェックカテゴリ名7 TEXT,
                  カテゴリ表示順8 INTEGER,
                  チェックカテゴリ名8 TEXT,
                  カテゴリ表示順9 INTEGER,
                  チェックカテゴリ名9 TEXT,
                  カテゴリ表示順10 INTEGER,
                  チェックカテゴリ名10 TEXT,
                  カテゴリ表示順11 INTEGER,
                  チェックカテゴリ名11 TEXT,
                  カテゴリ表示順12 INTEGER,
                  チェックカテゴリ名12 TEXT,
                  カテゴリ表示順13 INTEGER,
                  チェックカテゴリ名13 TEXT,
                  カテゴリ表示順14 INTEGER,
                  チェックカテゴリ名14 TEXT,
                  カテゴリ表示順15 INTEGER,
                  チェックカテゴリ名15 TEXT,
                  カテゴリ表示順16 INTEGER,
                  チェックカテゴリ名16 TEXT,
                  カテゴリ表示順17 INTEGER,
                  チェックカテゴリ名17 TEXT,
                  カテゴリ表示順18 INTEGER,
                  チェックカテゴリ名18 TEXT,
                  カテゴリ表示順19 INTEGER,
                  チェックカテゴリ名19 TEXT,
                  カテゴリ表示順20 INTEGER,
                  チェックカテゴリ名20 TEXT
                  )''')

        # データベースの値を取得する
        sql = f'select * from report_type_table'
        df = sqlite_data_get(sql, os.path.dirname(
            os.path.dirname(__file__))+'\\Database\\hontai_seizo.db')
        df = df.sort_values(['帳票パターンNo'])

        return (df)

    def db_update(edf):

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
        for _, row in edf.iterrows():

            if row["帳票パターンNo"] is not None:
                cur.execute(
                    """ UPDATE report_type_table SET
                        カテゴリ表示順1 = ?, チェックカテゴリ名1 = ?,
                        カテゴリ表示順2 = ?, チェックカテゴリ名2 = ?,
                        カテゴリ表示順3 = ?, チェックカテゴリ名3 = ?,
                        カテゴリ表示順4 = ?, チェックカテゴリ名4 = ?,
                        カテゴリ表示順5 = ?, チェックカテゴリ名5 = ?,
                        カテゴリ表示順6 = ?, チェックカテゴリ名6 = ?,
                        カテゴリ表示順7 = ?, チェックカテゴリ名7 = ?,
                        カテゴリ表示順8 = ?, チェックカテゴリ名8 = ?,
                        カテゴリ表示順9 = ?, チェックカテゴリ名9 = ?,
                        カテゴリ表示順10 = ?, チェックカテゴリ名10 = ?,
                        カテゴリ表示順11 = ?, チェックカテゴリ名11 = ?,
                        カテゴリ表示順12 = ?, チェックカテゴリ名12 = ?,
                        カテゴリ表示順13 = ?, チェックカテゴリ名13 = ?,
                        カテゴリ表示順14 = ?, チェックカテゴリ名14 = ?,
                        カテゴリ表示順15 = ?, チェックカテゴリ名15 = ?,
                        カテゴリ表示順16 = ?, チェックカテゴリ名16 = ?,
                        カテゴリ表示順17 = ?, チェックカテゴリ名17 = ?,
                        カテゴリ表示順18 = ?, チェックカテゴリ名18 = ?,
                        カテゴリ表示順19 = ?, チェックカテゴリ名19 = ?,
                        カテゴリ表示順20 = ?, チェックカテゴリ名20 = ?
                        WHERE 帳票パターンNo = ?
                    """,
                    (
                        row["カテゴリ表示順1"], row["チェックカテゴリ名1"],
                        row["カテゴリ表示順2"], row["チェックカテゴリ名2"],
                        row["カテゴリ表示順3"], row["チェックカテゴリ名3"],
                        row["カテゴリ表示順4"], row["チェックカテゴリ名4"],
                        row["カテゴリ表示順5"], row["チェックカテゴリ名5"],
                        row["カテゴリ表示順6"], row["チェックカテゴリ名6"],
                        row["カテゴリ表示順7"], row["チェックカテゴリ名7"],
                        row["カテゴリ表示順8"], row["チェックカテゴリ名8"],
                        row["カテゴリ表示順9"], row["チェックカテゴリ名9"],
                        row["カテゴリ表示順10"], row["チェックカテゴリ名10"],
                        row["カテゴリ表示順11"], row["チェックカテゴリ名11"],
                        row["カテゴリ表示順12"], row["チェックカテゴリ名12"],
                        row["カテゴリ表示順13"], row["チェックカテゴリ名13"],
                        row["カテゴリ表示順14"], row["チェックカテゴリ名14"],
                        row["カテゴリ表示順15"], row["チェックカテゴリ名15"],
                        row["カテゴリ表示順16"], row["チェックカテゴリ名16"],
                        row["カテゴリ表示順17"], row["チェックカテゴリ名17"],
                        row["カテゴリ表示順18"], row["チェックカテゴリ名18"],
                        row["カテゴリ表示順19"], row["チェックカテゴリ名19"],
                        row["カテゴリ表示順20"], row["チェックカテゴリ名20"],
                        row["帳票パターンNo"]
                    )
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
        st.markdown('### チェック大項目登録')
        st.markdown('チェック項目の大項目（カテゴリ名）を登録します。')
        seisan_col1, seisan_col2, seisan_col3, = st.columns([
            1, 3, 1])
        with seisan_col1:
            skdk_kubun = st.selectbox('帳票パターン選択', ['SK', 'DK'])

        with seisan_col2:
            # 最初にDBアップデートを行う
            df = db_get()
            df = df.sort_values(['帳票パターンNo'])
            df = df.fillna(' ')  # Noneデータ対策
            # 101～199がSK、201～299DK
            if skdk_kubun == 'SK':
                df = df[(df['帳票パターンNo'] > 100) & (df['帳票パターンNo'] < 200)]
            elif skdk_kubun == 'DK':
                df = df[(df['帳票パターンNo'] > 200) & (df['帳票パターンNo'] < 300)]

            # 各行を[No:詳細]の形式に変換してリストに追加
            select_list = []
            for index, row in df.iterrows():
                select_list.append(
                    f"パターンNo：{row['帳票パターンNo']}　帳票名：{row['帳票名']}")
            cp = st.selectbox('帳票パターン選択', select_list)

        # 「パターンNo：」の後の部分を抽出
        start_index = cp.find("パターンNo：") + len("パターンNo：")
        remaining_str = cp[start_index:].strip()

        # 最初の全角スペースの位置を見つける
        space_index = remaining_str.find("　")

        # 数字部分を切り出して整数に変換
        number = int(remaining_str[:space_index])
        df2 = df[df['帳票パターンNo'] == number]

        st.divider()
        st.write(f"{cp}　チェック大項目の編集")

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
        # '表示順'が99のときに'未使用'に変換 ※テストデータでなければここまで変換はいらないかもしれない
        combined_df['表示順'] = combined_df['表示順'].replace(" ", 99)
        combined_df['表示順'] = combined_df['表示順'].replace("　", 99)
        combined_df['表示順'] = combined_df['表示順'].astype(int).astype(str)
        combined_df['表示順'] = combined_df['表示順'].replace(" ", '未使用')
        combined_df['表示順'] = combined_df['表示順'].replace("　", '未使用')
        combined_df['表示順'] = combined_df['表示順'].replace("99", '未使用')
        # エディター
        selectbox_options = ["1", "2", "3",
                             "4", "5", "6", "7", "8", "9", "未使用"]
        columns_config = {col: st.column_config.SelectboxColumn(
            label=col, options=selectbox_options) for col in df.columns}

        edited_df = st.data_editor(combined_df.reset_index(drop=True),
                                   column_config={
                                   '大項目名称': {'width': 300},
                                   "表示順": st.column_config.SelectboxColumn(
                                       label="表示順",
                                       options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                                                "13", "14", "15", "16", "17", "18", "19", "20", "未使用"])
                                   },
                                   # hide_index=True, num_rows="dynamic")
                                   hide_index=True)

        edited_df['表示順'] = edited_df['表示順'].fillna('未使用')  # Noneも未使用扱いにする
        edited_df['表示順'] = edited_df['表示順'].replace('未使用', "99")
        edited_df['表示順'] = edited_df['表示順'].astype(int)
        df2['カテゴリ表示順1'] = edited_df['表示順'].iloc[0]
        df2['チェックカテゴリ名1'] = edited_df['大項目名称'].iloc[0]
        df2['カテゴリ表示順2'] = edited_df['表示順'].iloc[1]
        df2['チェックカテゴリ名2'] = edited_df['大項目名称'].iloc[1]
        df2['カテゴリ表示順3'] = edited_df['表示順'].iloc[2]
        df2['チェックカテゴリ名3'] = edited_df['大項目名称'].iloc[2]
        df2['カテゴリ表示順4'] = edited_df['表示順'].iloc[3]
        df2['チェックカテゴリ名4'] = edited_df['大項目名称'].iloc[3]
        df2['カテゴリ表示順5'] = edited_df['表示順'].iloc[4]
        df2['チェックカテゴリ名5'] = edited_df['大項目名称'].iloc[4]
        df2['カテゴリ表示順6'] = edited_df['表示順'].iloc[5]
        df2['チェックカテゴリ名6'] = edited_df['大項目名称'].iloc[5]
        df2['カテゴリ表示順7'] = edited_df['表示順'].iloc[6]
        df2['チェックカテゴリ名7'] = edited_df['大項目名称'].iloc[6]
        df2['カテゴリ表示順8'] = edited_df['表示順'].iloc[7]
        df2['チェックカテゴリ名8'] = edited_df['大項目名称'].iloc[7]
        df2['カテゴリ表示順9'] = edited_df['表示順'].iloc[8]
        df2['チェックカテゴリ名9'] = edited_df['大項目名称'].iloc[8]
        df2['カテゴリ表示順10'] = edited_df['表示順'].iloc[9]
        df2['チェックカテゴリ名10'] = edited_df['大項目名称'].iloc[9]
        df2['カテゴリ表示順11'] = edited_df['表示順'].iloc[10]
        df2['チェックカテゴリ名11'] = edited_df['大項目名称'].iloc[10]
        df2['カテゴリ表示順12'] = edited_df['表示順'].iloc[11]
        df2['チェックカテゴリ名12'] = edited_df['大項目名称'].iloc[11]
        df2['カテゴリ表示順13'] = edited_df['表示順'].iloc[12]
        df2['チェックカテゴリ名13'] = edited_df['大項目名称'].iloc[12]
        df2['カテゴリ表示順14'] = edited_df['表示順'].iloc[13]
        df2['チェックカテゴリ名14'] = edited_df['大項目名称'].iloc[13]
        df2['カテゴリ表示順15'] = edited_df['表示順'].iloc[14]
        df2['チェックカテゴリ名15'] = edited_df['大項目名称'].iloc[14]
        df2['カテゴリ表示順16'] = edited_df['表示順'].iloc[15]
        df2['チェックカテゴリ名16'] = edited_df['大項目名称'].iloc[15]
        df2['カテゴリ表示順17'] = edited_df['表示順'].iloc[16]
        df2['チェックカテゴリ名17'] = edited_df['大項目名称'].iloc[16]
        df2['カテゴリ表示順18'] = edited_df['表示順'].iloc[17]
        df2['チェックカテゴリ名18'] = edited_df['大項目名称'].iloc[17]
        df2['カテゴリ表示順19'] = edited_df['表示順'].iloc[18]
        df2['チェックカテゴリ名19'] = edited_df['大項目名称'].iloc[18]
        df2['カテゴリ表示順20'] = edited_df['表示順'].iloc[19]
        df2['チェックカテゴリ名20'] = edited_df['大項目名称'].iloc[19]

        if st.button("更新"):

            # 20以下の値でフィルタリング
            filtered_df = edited_df[edited_df['表示順'] <= 20]
            # 重複する値を検出
            duplicates = filtered_df[filtered_df.duplicated(
                subset=['表示順'], keep=False)]

            # 表示順が重複しても問題は無いですが、念のためチェック
            if not duplicates.empty:
                st.write("表示順が重複しています")
            else:
                db_update(df2)
                st.write("更新完了")

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    st.markdown(e)
    print(e)
