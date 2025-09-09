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
import csv
import pandas as pd
from datetime import datetime, timedelta, timezone
import oracledb

try:
    def df_csv_cnv1(df, filename='自動_'):
        csv_dir_path = r"D:\py\hontaigr_checksheet\work\spec"
        # DFをcsvにコンバートして出力
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        csv_name = csv_dir_path+"\\"+filename + \
            dt_now.strftime('%Y%m%d%H%M%S')+".csv"
        df.to_csv(csv_name, index=False, encoding='CP932')

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
    spec_df = spec_df.dropna(subset=["M1MNO"])

    # EJに接続
    # Oracle Clientの初期化
    lib_dir = r"C:\Oracle\instantclient_21_9"
    oracledb.init_oracle_client(lib_dir=lib_dir)

    # Oracle DB接続定義
    dsn_tns = oracledb.makedsn('172.17.107.102', '1521', service_name='EXPJ')
    connection = oracledb.connect(user='EXPJ2', password='EXPJ2', dsn=dsn_tns)
    cursor = connection.cursor()
    # SQLクエリ
    sql = f"""SELECT JOB_ODR_CD,KIBAN,AGENT_CD FROM T_ODR """
    EJ_df = pd.read_sql(sql, con=connection)

    # データフレームの結合（inner join）
    spec_df['M1MNO'] = spec_df['M1MNO'].astype(str)
    EJ_df['KIBAN'] = EJ_df['KIBAN'].astype(str)
    merged_df = pd.merge(spec_df, EJ_df, left_on="M1MNO",
                         right_on="KIBAN", how="inner")
    df_csv_cnv1(merged_df, "merged_df")

except Exception as e:
    # 簡単なエラー処理
    with open(r"D:\py\hontaigr_checksheet\bat\err_log", mode='w') as f:
        f.write(str(e))
