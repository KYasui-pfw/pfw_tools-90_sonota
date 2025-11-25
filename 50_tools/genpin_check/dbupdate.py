
# インポート
import streamlit as st
import streamlit.components.v1 as components
import os
from glob import glob
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pythoncom
from datetime import datetime, timedelta, timezone
import pandas as pd
import shutil
import pyqrcode
import openpyxl
from PIL import Image
from st_aggrid import AgGrid, JsCode, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
import sqlite3
from module.conmas_upload import data_upload
from dateutil.relativedelta import relativedelta

try:
    # df⇒SQLiteに記録（旧：CSV出力）
    def df_csv_cnv(df, filename):
        # DataFrameをSQLite genpinhyo.db の output_history テーブルに保存
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        db_path = os.path.join(os.path.dirname(__file__), 'Database', 'genpinhyo.db')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # output_history テーブルを作成（存在しない場合）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS output_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                filename TEXT NOT NULL,
                data TEXT NOT NULL
            )
        ''')

        # DataFrameをJSON形式に変換して保存
        import json
        data_json = df.to_json(orient='records', force_ascii=False)

        cursor.execute('''
            INSERT INTO output_history (created_at, filename, data)
            VALUES (?, ?, ?)
        ''', (dt_now.strftime('%Y-%m-%d %H:%M:%S'), filename, data_json))

        conn.commit()
        conn.close()

        # # 【旧版：CSV出力】コメントアウト（2025-11-22 SQLite移行）
        # csv_name = os.path.dirname(__file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_"+filename+".csv"
        # df.to_csv(csv_name, index=False, encoding='CP932')

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

    # krdのmachinDBに接続する（SQLite版）
    def krd_data_get(sql):
        # SQLite接続（KRD MySQL → SQLite同期データベース）
        # \\esrv11\krd_machine\db\krd_machine.db
        sqlite_db_path = r'\\esrv11\krd_machine\db\krd_machine.db'

        conn = sqlite3.connect(sqlite_db_path)
        df = pd.read_sql(sql, conn)
        conn.close()

        return df

    # # 【旧版：MySQL接続】コメントアウト（2025-11-22 SQLite移行）
    # def krd_data_get(sql):
    #     # #DB接続定義
    #     db_url = 'mysql+pymysql://pfw:mejiriHoo@krd/machin?charset=utf8'
    #
    #     # エンジンを作成
    #     engine = create_engine(db_url, echo=True)
    #
    #     # セッションを作成するためのSessionクラスを生成
    #     Session = sessionmaker(bind=engine)
    #     session = Session()
    #
    #     # コネクションを取得
    #     with engine.connect() as connection:
    #         # SQLクエリの実行
    #         df = pd.read_sql(sql, connection)
    #
    #     # セッションを閉じる
    #     session.close()
    #
    #     return (df)

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
            # SQLクエリの実行
            df = pd.read_sql(sql, connection)

        # セッションを閉じる
        session.close()

        return (df)

# バックアップ
    def main():
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if (os.path.isfile(os.path.dirname(__file__)+'\\Database\\genpinhyo.db')):
            shutil.copy(os.path.dirname(__file__)+'\\Database\\genpinhyo.db',
                        os.path.dirname(__file__)+f'\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_genpinhyo.db')

        # 本処理（更新処理）
        dbname = 'genpinhyo.db'
        cdb = os.path.dirname(__file__)+f'\\Database\\'+dbname
        # conn = sqlite3.connect(cdb,isolation_level=None) オートコミットを削除（重かった原因）
        conn = sqlite3.connect(cdb)

        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        cur.execute('CREATE TABLE IF NOT EXISTS genpinhyo(\
                  ロット番号 TEXT PRIMARY KEY ,\
                  月次 TEXT,\
                  組立番号 TEXT,\
                  機種 TEXT,\
                  吋 TEXT,\
                  G TEXT,\
                  完成部番 TEXT,\
                  部品名 TEXT,\
                  客先名 TEXT,\
                  国名 TEXT,\
                  B1図番 TEXT,\
                  B2図番 TEXT,\
                  F1図番 TEXT,\
                  F2図番 TEXT,\
                  L図番 TEXT,\
                  R図番 TEXT,\
                  C図番 TEXT,\
                  組立開始日 TEXT,\
                  梱包開始日 TEXT,\
                  指定納期 TEXT,\
                  必要数 TEXT,\
                  SKDK TEXT,\
                  工程 TEXT,\
                  工程VERSION TEXT,\
                  ﾒｯｷ TEXT,\
                  客先コード TEXT\
                  )')
        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        cur.execute('CREATE TABLE IF NOT EXISTS buhin_irepo_mst(\
                  部品名 TEXT PRIMARY KEY,\
                  ireporter管理flg INTEGER,\
                  QRコードレイアウト区分 INTEGER,\
                  縦横区分 INTEGER\
                  )')

        # ■テーブル作成処理 ADD_20241125
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする
        cur.execute('CREATE TABLE IF NOT EXISTS delete_mst(\
                  ロット番号 TEXT PRIMARY KEY ,\
                  削除flg INTEGER \
                  )')

        # ▼▼データの取得と結合処理開始
        # EJから出力されたASPKakouDenpyoを取得
        denpyo_df = pd.read_csv(
            r"\\172.17.107.102\PrintOutCsv\4.加工\4-03 ASPKakouDenpyo.csv", encoding='CP932')

        # ADD_20241217_0件dataなら抜ける
        if denpyo_df.empty:
            return

        # i-reporterより客先マスター取得
        sql = "SELECT record_key as 客先コード,value as 客先名m,field0001 as 国名m FROM view_mst_custom_record WHERE master_key = 'M_CUSTOMER'"
        kyakusaki_df = ireporter_data_get(sql)

        # 製番をキーに、両dfの内容を結合
        df1 = pd.merge(denpyo_df, kyakusaki_df, how='left')

        # krdより工程バージョン取得
        sql = "SELECT SLIP_NO as 伝票Ｎｏ,VERSION FROM DATA_ASP2_PUT"
        krd_df1 = krd_data_get(sql)

        # 伝票Noをキーに、両dfの内容を結合
        df2 = pd.merge(df1, krd_df1, how='left')

        # krdよりプロセスコード取得
        sql = "SELECT FINAL_ITEM_CODE as 加工部番,VERSION,PROCODESTR as 工程 FROM MSTR_PROCODESTR"
        krd_df2 = krd_data_get(sql)

        # 加工部番をキーに、両dfの内容を結合
        df3 = pd.merge(df2, krd_df2, how='left')

        # krdより図番取得
        sql = "SELECT SETU_F as 加工部番,\
            B_FIG as B1図番,\
            B2_FIG as B2図番,\
            F_FIG as F1図番,\
            F2_FIG as F2図番,\
            L_FIG as L図番,\
            R_FIG as R図番,\
            C_FIG as C図番\
            FROM DATA_KOUTEIZUKAN"
        krd_df3 = krd_data_get(sql)

        # 加工部番をキーに、両dfの内容を結合
        df4 = pd.merge(df3, krd_df3, how='left')

        # krdより無電解ニッケル電気の対応を取得
        sql = "SELECT FIN_CODE as 加工部番,METAL FROM MSTR_METAL"
        krd_df4 = krd_data_get(sql)

        # 加工部番をキーに、両dfの内容を結合
        merged_df = pd.merge(df4, krd_df4, how='left')

        # ▲▲データの取得と結合処理終了

        # ▼▼dataframeを整える
        mdf = merged_df.filter(items=['伝票Ｎｏ', '生産月次', '組立番号', '機種名', '吋', 'ゲージ', '加工部番', '部品名', '客先名m', '国名m', 'B1図番', 'B2図番',
                               'F1図番', 'F2図番', 'L図番', 'R図番', 'C図番', '組立開始日', '梱包開始日', '指定納期', '必要数', 'SKDK', '工程', 'VERSION', 'METAL', '客先コード'])

        # カラム名付け替え・編集
        mdf = mdf.rename(columns={'伝票Ｎｏ': 'ロット番号'})
        mdf = mdf.rename(columns={'生産月次': '月次'})
        mdf = mdf.rename(columns={'機種名': '機種'})
        mdf = mdf.rename(columns={'ゲージ': 'G'})
        mdf = mdf.rename(columns={'加工部番': '完成部番'})
        mdf = mdf.rename(columns={'客先名m': '客先名'})
        mdf = mdf.rename(columns={'国名m': '国名'})
        mdf = mdf.rename(columns={'VERSION': '工程VERSION'})
        mdf = mdf.rename(columns={'METAL': 'ﾒｯｷ'})
        mdf['吋'] = mdf['吋'].astype('object')
        mdf['G'] = mdf['G'].astype('object')
        mask = (mdf['吋'] != '') & mdf['吋'].apply(
            lambda x: float(x).is_integer() if x != '' else False)
        mdf.loc[mask, '吋'] = mdf.loc[mask, '吋'].apply(
            lambda x: str(int(float(x))))
        mask = (mdf['G'] != '') & mdf['G'].apply(
            lambda x: float(x).is_integer() if x != '' else False)
        mdf.loc[mask, 'G'] = mdf.loc[mask, 'G'].apply(
            lambda x: str(int(float(x))))
        mdf['月次'] = mdf['月次'].astype(str)
        mdf['月次'] = mdf['月次'].apply(
            lambda x: x + '_' if len(x) == 6 else x)  # 6文字は_を追加する
        mdf['完成部番'] = mdf['完成部番'].str.replace('　', ' ')
        mdf['組立番号'] = mdf['組立番号'].str.replace('　', ' ')
        mdf['機種'] = mdf['機種'].str.replace('　', ' ')
        mdf['国名'] = mdf['国名'].str.replace('　', ' ')
        mdf['客先名'] = mdf['客先名'].str.replace('　', ' ')
        mdf = mdf.fillna('')  # Noneデータ対策

        # 部品irepotableの更新用
        buhin_irepo_df = denpyo_df[['部品名']]  # 必要な列だけ抽出
        buhin_irepo_df['i-reporter管理flg'] = 0  # フラグの初期値設定
        buhin_irepo_df['QRコードレイアウト区分'] = 0  # フラグの初期値設定
        buhin_irepo_df['縦横区分'] = 0  # フラグの初期値設定
        buhin_irepo_df = buhin_irepo_df.drop_duplicates()  # 重複削除
        # データベースを更新
        try:    # mdfの全データを一括でリストに変換
            data = [tuple(row.values.tolist())
                    for index, row in mdf.iterrows()]
            # genpinhyoの更新　1000件ずつ分割して処理
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]  # 1000件ずつスライス
                cur.executemany('REPLACE INTO genpinhyo(ロット番号,月次,組立番号,機種,吋,G,完成部番,部品名,客先名,国名,B1図番,B2図番,F1図番,F2図番,L図番,\
                          R図番,C図番,組立開始日,梱包開始日,指定納期,必要数,SKDK,工程,工程VERSION,ﾒｯｷ,客先コード)\
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', batch)
            conn.commit()  # 20241212_コミット漏れ追加
            # buhin_irepo_mstの更新
            for index, row in buhin_irepo_df.iterrows():
                buhinmei = row['部品名']
                i_reporter_k_flg = row['i-reporter管理flg']
                qr_kubun = row['QRコードレイアウト区分']
                tateyoko_kubun = row['縦横区分']

                # 部品名が既に存在するか確認し、存在しなければ挿入
                cur.execute('''
            INSERT INTO buhin_irepo_mst (部品名, ireporter管理flg, QRコードレイアウト区分, 縦横区分)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(部品名) DO NOTHING
        ''', (buhinmei, i_reporter_k_flg, qr_kubun, tateyoko_kubun))

            conn.commit()  # 20241212_コミット漏れ追加
            # ADD_20241125_start delete_mst更新を追加
            # DB接続定義
            dbname = 'genpinhyo.db'
            filepath = os.path.dirname(__file__)+f'\\Database\\'+dbname
            db_url = f'sqlite:///{filepath}'
            engine = create_engine(db_url, echo=True)

            # セッションを作成するためのSessionクラスを生成
            Session = sessionmaker(bind=engine)
            session = Session()

            # コネクションを取得
            with engine.connect() as connection:
                # SQLクエリの実行
                del_df = pd.read_sql(f'select * from genpinhyo', connection)
            # セッションを閉じる
            session.close()

            del_df = del_df.loc[:, ['ロット番号']]

            for index, row in del_df.iterrows():

                # 部品名が既に存在するか確認し、存在しなければ挿入
                cur.execute('''
            INSERT INTO delete_mst(ロット番号,削除flg)
            VALUES (?, ?)
            ON CONFLICT(ロット番号) DO NOTHING
        ''', (row['ロット番号'], 0))
            # ADD_20241125_end

            conn.commit()
        except Exception as e:
            # エラーが発生した場合、ロールバックして変更を取り消す
            conn.rollback()
        finally:
            # 最後にカーソルと接続を閉じる
            cur.close()
            conn.close()

        # ADD_20241125_削除flg更新
        # DB接続定義 同じですが、明示します
        dbname = 'genpinhyo.db'
        filepath = os.path.dirname(__file__)+f'\\Database\\'+dbname
        db_url = f'sqlite:///{filepath}'
        engine = create_engine(db_url, echo=True)

        # セッションを作成するためのSessionクラスを生成
        Session = sessionmaker(bind=engine)
        session = Session()

        # コネクションを取得
        with engine.connect() as connection:
            # SQLクエリの実行
            df1 = pd.read_sql(f'select * from genpinhyo', connection)
            df2 = pd.read_sql(f'select * from delete_mst', connection)
        # セッションを閉じる
        session.close()

        delete_df = pd.merge(df1, df2, on=['ロット番号'], how='left')

        # 年月で絞り込み
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        next_month = dt_now + relativedelta(months=1)  # 翌月
        next2_month = dt_now + relativedelta(months=2)  # 翌翌月
        next3_month = dt_now + relativedelta(months=3)  # 翌翌翌月
        nengetsu1 = dt_now.strftime('%Y%m')
        nengetsu2 = next_month.strftime('%Y%m')
        nengetsu3 = next2_month.strftime('%Y%m')
        nengetsu4 = next3_month.strftime('%Y%m')
        dfa = delete_df[delete_df['月次'].str.startswith(nengetsu1)]
        dfb = delete_df[delete_df['月次'].str.startswith(nengetsu2)]
        dfc = delete_df[delete_df['月次'].str.startswith(nengetsu3)]
        dfd = delete_df[delete_df['月次'].str.startswith(nengetsu4)]

        delete_df = pd.concat([dfa, dfb, dfc, dfd], ignore_index=True)
        delete_df = delete_df.loc[:, ['ロット番号', '削除flg']]

        # csvを起源としたdf をdelete_df2にセット
        delete_df2 = mdf.loc[:, ['ロット番号']]
        delete_df2['削除flg2'] = 0

        # マージすることにより、削除データをあぶりだす（EJ特有の処理）
        delete_df = pd.merge(delete_df, delete_df2, on=['ロット番号'], how='left')
        delete_df = delete_df.fillna(1)  # Noneデータを1に変更

        # ADD_20241217_DEL対象の確認処理を追加
        chk_df = delete_df[delete_df['削除flg'].astype(
            int) != delete_df['削除flg2'].astype(int)]
        if not chk_df.empty:
            df_csv_cnv(chk_df, "EJ削除flg_on")

        delete_df = delete_df.drop(columns=['削除flg'])
        delete_df = delete_df.rename(columns={'削除flg2': '削除flg'})

        # 本処理（更新処理）
        dbname = 'genpinhyo.db'
        cdb = os.path.dirname(__file__)+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)

        cur = conn.cursor()

        try:    # mdfの全データを一括でリストに変換

            data = [tuple(row)
                    for row in delete_df[['削除flg', 'ロット番号']].to_numpy()]

            batch_size = 1000
            for i in range(0, len(data), batch_size):
                # 1000件ずつ分割して処理
                batch = data[i:i+batch_size]  # 1000件ずつスライス
                # 部品名が既に存在するか確認し、存在しなければ挿入
                cur.executemany('''
            UPDATE delete_mst
            SET 削除flg = ?
            WHERE ロット番号 = ?
        ''', batch)

            conn.commit()
        except Exception as e:
            # エラーが発生した場合、ロールバックして変更を取り消す
            conn.rollback()
        finally:
            # 最後にカーソルと接続を閉じる
            cur.close()
            conn.close()

        # ADD_20241126_end

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    print(e)
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    with open(os.path.dirname(__file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
        f.write(str(e))
