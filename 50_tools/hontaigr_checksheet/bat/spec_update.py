###################################################
# 本体Grチェックシート用に、テーブルを作成、更新する
#
###################################################

import sys
import os
import glob
import openpyxl
import pyexcel
import datetime
import shutil
import pandas as pd
from datetime import datetime, timedelta, timezone
import oracledb
import sqlite3

try:
    def df_csv_cnv1(df, filename='自動_'):
        csv_dir_path = r"D:\py\hontaigr_checksheet\work\spec"
        # DFをcsvにコンバートして出力
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        csv_name = csv_dir_path+"\\"+filename + \
            dt_now.strftime('%Y%m%d%H%M%S')+".csv"
        df.to_csv(csv_name, index=False, encoding='CP932')

    def seisan_data_create(df):
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
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする（編機以外にも使用できる項目名）
        cur.execute('''CREATE TABLE IF NOT EXISTS autooiler_agent_info(
                  KUMINO TEXT PRIMARY KEY,
                  M1ATO INTEGER,
                  AGENT_CD TEXT
                  )''')

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()

        # 各行に対して更新処理を行う
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()
        for _, row in df.iterrows():
            # 組立番号が既に存在するか確認
            cur.execute(
                "SELECT * FROM autooiler_agent_info WHERE KUMINO = ? ", (row['KUMINO'],))
            existing_records = cur.fetchall()

            if not existing_records:
                # 条件1: 組立番号が重複していない場合、INSERT
                cur.execute("""
              INSERT INTO autooiler_agent_info (KUMINO, M1ATO, AGENT_CD)
              VALUES (?, ?, ?) """,
                            (row['KUMINO'], row['M1ATO'], row['AGENT_CD']))
            else:
                # 条件2と条件3: 組立番号が重複している場合
                cur.execute("""
                  UPDATE autooiler_agent_info SET M1ATO = ?, AGENT_CD = ? WHERE KUMINO = ?""",
                            (row['M1ATO'], row['AGENT_CD'], row['KUMINO']))

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()

        return

    # インプットフォルダ
    dir_path = r"D:\py\hontaigr_checksheet\work\spec"
    file_list1 = glob.glob(os.path.join(dir_path, "*.xls"))

    # openpyxlはxls未対応なので一旦xlsxに変換
    # エクセルファイルは複数は無い想定だが、念のためリストで処理
    for file in file_list1:
        pyexcel.save_book_as(file_name=file, dest_file_name=file+'x')

    # xlsxを取得し直して処理
    file_list2 = glob.glob(os.path.join(dir_path, "*.xlsx"))
    df_list = []  # データフレームを格納するリスト

    for file in file_list2:
        # エクセルファイルを開く
        in_wb = openpyxl.load_workbook(file)
        # 指定のシートの取得
        in_sheet = in_wb.worksheets[0]
        # シートのデータをDataFrameに変換
        df = pd.DataFrame(in_sheet.values)

        df.columns = df.iloc[0]  # 最初の行をヘッダーにする
        df = df[1:]  # 1行目を削除
        # データフレームをリストに追加
        df_list.append(df)

    # すべてのデータフレームを結合（必要なら）
    spec_df = pd.concat(df_list, ignore_index=True)
    # spec_df = spec_df[["M1MNO", "M1ATO"]]
    spec_df = spec_df.dropna(subset=["M1ANO"])

    # EJに接続
    # Oracle Clientの初期化
    lib_dir = r"C:\Oracle\instantclient_21_9"
    oracledb.init_oracle_client(lib_dir=lib_dir)

    # Oracle DB接続定義
    dsn_tns = oracledb.makedsn('172.17.107.102', '1521', service_name='EXPJ')
    connection = oracledb.connect(user='EXPJ2', password='EXPJ2', dsn=dsn_tns)
    cursor = connection.cursor()
    # SQLクエリ
    sql = f"""SELECT JOB_ODR_CD,AGENT_CD,DEL_FLG FROM T_ODR """
    EJ_df = pd.read_sql(sql, con=connection)

    # データフレームの結合（inner join）
    spec_df['KUMINO'] = spec_df['M1DYM'].astype(str).str[1:3] + \
        spec_df['M1SKDK'].astype(str) + spec_df['M1ANO'].astype(str)
    spec_df = spec_df[['KUMINO', 'M1ATO']]

    EJ_df['JOB_ODR_CD'] = EJ_df['JOB_ODR_CD'].astype(str)
    EJ_df = EJ_df[EJ_df['DEL_FLG'] != 1]  # DEL_FLG が 1 の行を除外M1ATO

    merged_df = pd.merge(spec_df, EJ_df, left_on="KUMINO",
                         right_on="JOB_ODR_CD", how="inner")
    merged_df = merged_df[['KUMINO', 'M1ATO', 'AGENT_CD']]
    seisan_data_create(merged_df)
    # df_csv_cnv1(merged_df, "merged_df")
    # df_csv_cnv1(spec_df, "spec_df")


except Exception as e:
    # 簡単なエラー処理
    with open(r"D:\py\hontaigr_checksheet\bat\err_log", mode='w') as f:
        f.write(str(e))
