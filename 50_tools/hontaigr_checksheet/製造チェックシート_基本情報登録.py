################################
# 　本体グループ製造チェックシート #
# 　※編機調整報告書を元に作成     #　
# 　自動帳票作成用データ作成処理　 #
# 　手動で実行する　　　　　　　　 #
################################

# インポート
import streamlit as st
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pythoncom
from datetime import datetime, timedelta, timezone
import pandas as pd
import shutil
import sqlite3
import time
import numpy as np

try:

    pythoncom.CoInitialize()  # サーバーサイドからローカルファイルを動かすことになるので必要

    def chohyo_data_get(dt_nengetsu):
        # SQLAlchemyを使用した接続に変更
        # データベースの接続文字列を構成
        db_url = 'mssql+pyodbc://fukuharaadmin:xrTRzAJtKQ7B@production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com/chohyo?driver=ODBC+Driver+17+for+SQL+Server'

        # エンジンを作成
        engine = create_engine(db_url, echo=True)

        # セッションを作成するためのSessionクラスを生成
        Session = sessionmaker(bind=engine)
        session = Session()

        # コネクションを取得
        with engine.connect() as connection:
            # SQLクエリの実行
            sql = f"select job_cd,monthly,prs_full_path,comp_item_cd,comp_item_name from t_prs_job_cd_bom where monthly like '{
                dt_nengetsu}_'"
            df = pd.read_sql(sql, connection)

        # セッションを閉じる
        session.close()

        return (df)

    def common_data_get(dt_nengetsu):

        # SQLAlchemyを使用した接続に変更
        # データベースの接続文字列を構成
        db_url = 'mssql+pyodbc://fukuharaadmin:xrTRzAJtKQ7B@production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com/common?driver=ODBC+Driver+17+for+SQL+Server'

        # エンジンを作成
        engine = create_engine(db_url, echo=True)

        # セッションを作成するためのSessionクラスを生成
        Session = sessionmaker(bind=engine)
        session = Session()

        # コネクションを取得
        with engine.connect() as connection:
            # SQLクエリの実行
            # DEL_20241119_SKDKを取得
            # sql = f"select an_item_cd,an_item_category,an_user_name,an_country_name,an_model_name,an_inch,an_gauge,an_cut_count,an_monthly from m_items_sub_71 where an_monthly like '{dt_nengetsu}_'"
            # ADD_20241119_SKDKを取得
            sql = f"select an_item_cd,an_item_category,an_user_name,an_country_name,an_model_name,an_inch,an_gauge,an_cut_count,an_monthly,an_skdk from m_items_sub_71 where an_monthly like '{
                dt_nengetsu}_'"
            df = pd.read_sql(sql, connection)

        # セッションを閉じる
        session.close()
        return (df)

    def seiban_data_get(dt_nengetsu):

        # DB接続定義
        # データベースの接続文字列を構成
        db_url = 'mssql+pyodbc://fukuharaadmin:xrTRzAJtKQ7B@production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com/chohyo?driver=ODBC+Driver+17+for+SQL+Server'

        # エンジンを作成
        engine = create_engine(db_url, echo=True)

        # セッションを作成するためのSessionクラスを生成
        Session = sessionmaker(bind=engine)
        session = Session()

        # コネクションを取得
        with engine.connect() as connection:
            # SQLクエリの実行
            sql = f"select job_cd from t_prs_job_cd_pln where monthly like '{
                dt_nengetsu}_'"
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

    def df_merge(chohyo_df, common_df, seisan_df):

        # ①の抽出
        df1a = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-67T', na=False)]

        df1aa = df1a.query('comp_item_name=="NEEDLE"')
        df1ab = df1a.query('comp_item_name=="DIAL NEEDLE"')
        df1ac = df1a.query('comp_item_name=="SINKER"')

        df1b = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-64T', na=False)]

        df1ba = df1b[df1b['prs_full_path'].str.contains('S910', na=False)]
        df1baa = df1ba.query('comp_item_name=="NEEDLE"')
        df1bab = df1ba.query('comp_item_name=="DIAL NEEDLE"')
        df1bac = df1ba.query('comp_item_name=="SINKER"')

        df1bb = df1b[df1b['prs_full_path'].str.contains('S3662', na=False)]
        df1bba = df1bb.query('comp_item_name=="NEEDLE"')
        df1bbb = df1bb.query('comp_item_name=="DIAL NEEDLE"')
        df1bbc = df1bb.query('comp_item_name=="SINKER"')

        df1 = pd.concat([df1aa, df1ab, df1ac, df1baa, df1bab,
                        df1bac, df1bba, df1bbb, df1bbc], ignore_index=True)
        df1 = df1[~df1.duplicated(
            subset=["job_cd", "comp_item_cd"], keep='last')]
        # df1['hari_syubetsu'] = 1 この抽出条件は5番目に変更 DEL_20240904
        df1['hari_syubetsu'] = 5  # ADD_20240904

        # ②の抽出
        df2 = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-57T', na=False)]

        df2a = df2.query('comp_item_name=="NEEDLE"')
        df2b = df2.query('comp_item_name=="DIAL NEEDLE"')
        df2c = df2.query('comp_item_name=="CYLINDER NEEDLE"')

        df2 = pd.concat([df2a, df2b, df2c], ignore_index=True)
        df2 = df2[~df2.duplicated(
            subset=["job_cd", "comp_item_cd"], keep='last')]
        # df2['hari_syubetsu'] = 2 この抽出条件は1番目に変更  DEL_20240904
        df2['hari_syubetsu'] = 1  # ADD_20240904

        # ③の抽出
        df3a = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-58T', na=False)]
        df3b = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-68T', na=False)]

        df3a = df3a[df3a['comp_item_name'].str.contains('INTER', na=False)]
        df3b = df3b[df3b['comp_item_name'].str.contains('INTER', na=False)]

        df3 = pd.concat([df3a, df3b], ignore_index=True)
        df3 = df3[~df3.duplicated(
            subset=["job_cd", "comp_item_cd"], keep='last')]

        # -58T と -68T を分離することに変更 DEL_20240904
        # df3['hari_syubetsu'] = 3
        # -58T と -68T を分離することに変更 ADD_20240904
        df3['hari_syubetsu'] = ""
        df3.loc[df3['prs_full_path'].str.contains(
            '-58T', na=False), 'hari_syubetsu'] = 2
        df3.loc[df3['prs_full_path'].str.contains(
            '-68T', na=False), 'hari_syubetsu'] = 6

        # ④の抽出
        # df4a = chohyo_df[chohyo_df['prs_full_path'].str.match('....-58T.*',na=False)]#正規表現での抽出に変更 ⇒ダメフルパスしか持たないので
        # df4b = chohyo_df[chohyo_df['prs_full_path'].str.match('....-68T.*',na=False)]
        df4a = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-58T', na=False)]
        df4b = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-68T', na=False)]

        df4aa = df4a[df4a['comp_item_name'].str.contains('PATTE', na=False)]
        df4ab = df4a[df4a['comp_item_name'].str.contains('SELEC', na=False)]
        df4ba = df4b[df4b['comp_item_name'].str.contains('PATTE', na=False)]
        df4bb = df4b[df4b['comp_item_name'].str.contains('SELEC', na=False)]

        # この抽出条件は -58T と -68T を分離することに変更 DEL_20240904
        df4 = pd.concat([df4aa, df4ab, df4ba, df4bb], ignore_index=True)
        df4 = df4[~df4.duplicated(
            subset=["job_cd", "comp_item_cd"], keep='last')]

        # -58T と -68T を分離することに変更 DEL_20240904
        # df4['hari_syubetsu'] = 4
        # -58T と -68T を分離することに変更 ADD_20240904
        df4['hari_syubetsu'] = ""
        df4.loc[df4['prs_full_path'].str.contains(
            '-58T', na=False), 'hari_syubetsu'] = 3
        df4.loc[df4['prs_full_path'].str.contains(
            '-68T', na=False), 'hari_syubetsu'] = 7

        # ⑤の抽出
        df5a = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-58T', na=False)]
        df5b = chohyo_df[chohyo_df['prs_full_path'].str.contains(
            '-68T', na=False)]
        # df5a = chohyo_df[chohyo_df['prs_full_path'].str.match('....-58T.*',na=False)]#正規表現での抽出に変更 ⇒ダメ
        # df5b = chohyo_df[chohyo_df['prs_full_path'].str.match('....-68T.*',na=False)]
        df5 = pd.concat([df5a, df5b], ignore_index=True)
        df5 = df5[~df5.duplicated(
            subset=["job_cd", "comp_item_cd"],  keep='last')]

        # ③と④以外を抽出する処理
        df5c = pd.concat([df3a, df3b], ignore_index=True)
        df5d = pd.concat([df4aa, df4ab, df4ba, df4bb], ignore_index=True)
        df5 = pd.concat([df5, df5c, df5d], ignore_index=True)
        df5 = df5[~df5.duplicated(
            subset=["job_cd", "comp_item_cd"],  keep=False)]
        # さらにASSYを省く
        df5 = df5[~df5['comp_item_name'].str.contains('ASSY.', na=False)]
        df5 = df5[df5['comp_item_name'].str.contains(
            'ROCKING PIECE', na=False)]  # 追加　ROCKING PIECEを含む(その他での抽出難)
        # -58T と -68T を分離することに変更 DEL_20240904
        # df5['hari_syubetsu'] = 5
        df5['hari_syubetsu'] = ""
        df5.loc[df5['prs_full_path'].str.contains(
            '-58T', na=False), 'hari_syubetsu'] = 4
        df5.loc[df5['prs_full_path'].str.contains(
            '-68T', na=False), 'hari_syubetsu'] = 8

        # 結合
        merged_chohyo_df = pd.concat(
            [df1, df2, df3, df4, df5], ignore_index=True)

        # #組立番号を主キーに結合
        merged_df = pd.merge(seisan_df, merged_chohyo_df,
                             left_on='job_cd', right_on='job_cd', how='left')
        merged_df = pd.merge(
            merged_df, common_df, left_on='job_cd', right_on='an_item_cd', how='left')
        # merged_df = merged_df.sort_values(['job_cd','hari_syubetsu']) #DEL_20240904_sortに部番を追加
        merged_df = merged_df.sort_values(
            ['job_cd', 'hari_syubetsu', 'comp_item_cd'])  # ADD_20240904sortに部番を追加
        merged_df = merged_df[merged_df['an_item_category'].str.contains(
            '生産機', na=False)]

        return (merged_df)

    def df_edit(merged_df):

        # df1はヘッダ部
        df1 = merged_df
        df1['youto'] = "kari"
        df1['nen'] = df1['an_monthly'].str[0:2]
        df1['getsu'] = df1['an_monthly'].str[2:4]
        df1['ji'] = df1['an_monthly'].str[4:5]
        df1['syukkasaki'] = df1['an_country_name'].str.cat(
            df1['an_user_name'], sep='　　　')
        # ADD_20241119 SKDK判断、閾値設定用にDFを分離（後にmergeする）
        df3 = df1.loc[:, ['job_cd', 'an_model_name', 'an_inch', 'an_skdk']]
        # ADD_20241119 SKDK判断、閾値設定用にDFを分離（後にmergeする）
        df3 = df3[~df3.duplicated(keep='last')]
        df1 = df1.loc[:, ['youto', 'nen', 'getsu', 'ji', 'job_cd',
                          'syukkasaki', 'an_model_name', 'an_inch', 'an_gauge', 'an_cut_count']]
        df1 = df1[~df1.duplicated(keep='last')]

        # 報告書の種類の判定　LEC・SECを含むか
        mask_df = df1['an_model_name'].str.contains('LEC|SEC', na=False)
        df1.loc[mask_df, 'youto'] = '＜EK '
        mask_df = ~df1['an_model_name'].str.contains('LEC|SEC', na=False)
        df1.loc[mask_df, 'youto'] = '＜ﾉｰﾏﾙ '

        # Y付きY無を追記
        mask_df = df1['an_model_name'].str.contains('Y', na=False)
        df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "Y付き用"
        mask_df = ~df1['an_model_name'].str.contains('Y', na=False)
        df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "Y無し用"

        # ADD_20240927 ｾﾐｼﾞｬｶﾞｰﾄﾞ機の判断
        mask_df = df1['an_model_name'].str.contains('-LPJ|-JS', na=False)
        df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "　J＞"
        mask_df = ~df1['an_model_name'].str.contains('-LPJ|-JS', na=False)
        df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "＞"

        # ADD_20241023_Start
        # 存在するのは以下の６パターンのため、それぞれのパターンごとに最新の帳票IDをセット
        # EKY付、EKY無、ﾉｰﾏﾙY付、ﾉｰﾏﾙY無、ﾉｰﾏﾙY無ｾﾐｼﾞｬｶﾞｰﾄﾞ、ﾉｰﾏﾙY付ｾﾐｼﾞｬｶﾞｰﾄﾞ
        df1.insert(0, 'defTopId', '')
        # EKY付 393
        mask_df = df1['youto'].str.contains('＜EK Y付き用＞', na=False)
        sql = "select def_top_id from view_def_top where def_top_org = 393 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
        # EKY無 394
        mask_df = df1['youto'].str.contains('＜EK Y無し用＞', na=False)
        sql = "select def_top_id from view_def_top where def_top_org = 394 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
        # ﾉｰﾏﾙY付 395
        mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y付き用＞', na=False)
        sql = "select def_top_id from view_def_top where def_top_org = 395 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
        # ﾉｰﾏﾙY無 398
        mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y無し用＞', na=False)
        sql = "select def_top_id from view_def_top where def_top_org = 398 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
        # ﾉｰﾏﾙY付ｾﾐｼﾞｬｶﾞｰﾄﾞ 396
        mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y付き用　J＞', na=False)
        sql = "select def_top_id from view_def_top where def_top_org = 396 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
        # ﾉｰﾏﾙY無ｾﾐｼﾞｬｶﾞｰﾄﾞ 397
        mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y無し用　J＞', na=False)
        sql = "select def_top_id from view_def_top where def_top_org = 397 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()

        # df2明細部（針の部分）
        df2 = merged_df

        # 追加ループ71
        for idx in range(71):
            df1[f'hari{idx}'] = ""

        count = 0
        for idx in range(df2.shape[0]):

            # df1を組立番号で特定
            mask = df1['job_cd'] == df2.iloc[idx,
                                             df2.columns.get_loc('job_cd')]

            # 組立番号判定
            if df2.iloc[idx-1, df2.columns.get_loc('job_cd')] == df2.iloc[idx, df2.columns.get_loc('job_cd')]:
                count += 1
            else:
                count = 0

            # 針種別判定（直前と針種別が変わっている） or 組立番号判定（組立番号が変わっている　countで判定）
            if not df2.iloc[idx-1, df2.columns.get_loc('hari_syubetsu')] == df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] or count == 0:

                if df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 1:
                    df1.loc[mask, f'hari{count}'] = "【■シリンダー針】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 2:
                    df1.loc[mask, f'hari{count}'] = "【■中間ジャック(C)】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 3:
                    df1.loc[mask, f'hari{count}'] = "【■ ﾊﾟﾀｰﾆﾝｸﾞｼﾞｬｯｸ (C)】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 4:
                    df1.loc[mask, f'hari{count}'] = "【■ロッキングピース(C)】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 5:
                    df1.loc[mask, f'hari{count}'] = "【▼ ｼﾝｶｰ/ﾀﾞｲﾔﾙ針 】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 6:
                    df1.loc[mask, f'hari{count}'] = "【▼中間ジャック(D)】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 7:
                    df1.loc[mask, f'hari{count}'] = "【▼ ﾊﾟﾀｰﾆﾝｸﾞｼﾞｬｯｸ(D) 】"
                elif df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 8:
                    df1.loc[mask, f'hari{count}'] = "【▼ロッキングピース(D)】"
                count += 1

            # 部番を格納
            df1.loc[mask, f'hari{count}'] = df2.iloc[idx,
                                                     df2.columns.get_loc(f'comp_item_cd')]

            # シンカー／ダイヤル針、シリンダー針のときは一行空ける
            # if df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 1 or df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 2: #DEL_20240904
            # ADD_20240904
            if df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 1 or df2.iloc[idx, df2.columns.get_loc('hari_syubetsu')] == 5:
                count += 1

        # 取り込み用にデータを整える
        # 最新の帳票IDを取得
        # sql = "select def_top_id from view_def_top where def_top_org = 352 and public_status = 2" DEL_20241023処理タイミング変更（帳票分割につき）
        # irepo_df = irepo_view_get(sql) DEL_20241023処理タイミング変更（帳票分割につき）

        # ADD_20241119_SKDKによる閾値の設定
        df3['閾値開始'] = 0.08
        df3['閾値終了'] = 0.35
        mask_df = df3['an_skdk'].str.contains('SK', na=False)
        mask_df2 = df3['an_model_name'].str.contains('A3.2RE', na=False)
        combined_mask = mask_df & mask_df2
        df3a1 = df3.loc[combined_mask, :]
        df3a1.loc[df3a1['an_inch'] <= 33, '閾値開始'] = 0.12
        df3a1.loc[df3a1['an_inch'] <= 33, '閾値終了'] = 0.42
        df3a1.loc[(df3a1['an_inch'] >= 34) & (
            df3a1['an_inch'] <= 39), '閾値開始'] = 0.22
        df3a1.loc[(df3a1['an_inch'] >= 34) & (
            df3a1['an_inch'] <= 39), '閾値終了'] = 0.42
        df3a1.loc[df3a1['an_inch'] >= 40, '閾値開始'] = 0.20
        df3a1.loc[df3a1['an_inch'] >= 40, '閾値終了'] = 0.50

        mask_df2 = df3['an_model_name'].str.contains('E3.2', na=False)
        combined_mask = mask_df & mask_df2
        df3a2 = df3.loc[combined_mask, :]
        df3a2.loc[df3a2['an_inch'] <= 33, '閾値開始'] = 0.15
        df3a2.loc[df3a2['an_inch'] <= 33, '閾値終了'] = 0.30
        df3a2.loc[df3a2['an_inch'] >= 34, '閾値開始'] = 0.18
        df3a2.loc[df3a2['an_inch'] >= 34, '閾値終了'] = 0.33

        mask_df = df3['an_skdk'].str.contains('SK', na=False)
        mask_df2 = ~df3['an_model_name'].str.contains('A3.2RE', na=False)
        mask_df3 = ~df3['an_model_name'].str.contains('E3.2', na=False)
        combined_mask = mask_df & mask_df2 & mask_df3
        df3a3 = df3.loc[combined_mask, :]

        mask_df = df3['an_skdk'].str.contains('DK', na=False)
        df3b = df3.loc[mask_df, :]
        df3b.loc[df3b['an_inch'] <= 39, '閾値開始'] = 0.06
        df3b.loc[df3b['an_inch'] <= 39, '閾値終了'] = 0.35
        df3b.loc[df3b['an_inch'] >= 40, '閾値開始'] = 0.15
        df3b.loc[df3b['an_inch'] >= 40, '閾値終了'] = 0.45

        df3 = pd.concat([df3a1, df3a2, df3a3, df3b], ignore_index=True)
        df3 = df3.loc[:, ['job_cd', '閾値開始', '閾値終了', 'an_skdk']]
        df1 = pd.merge(df1, df3, left_on=['job_cd'], right_on=[
                       'job_cd'], how='left')

        # ADD_20250118_年は西暦4桁
        df1['nen'] = df1['nen'].apply(lambda x: int('20' + str(x)))

        # ※帳票IDは常に最新のものを取得する必要有
        # df1.insert(0, 'defTopId', irepo_df['def_top_id'].max()) DEL_20241023処理タイミング変更（帳票分割につき）
        df1.insert(0, 'H', 'R')
        df1.columns = ['H', 'defTopId', 'S1C0', 'S1C1', 'S1C2', 'S1C3', 'S1C4', 'S1C5', 'S1C6', 'S1C7', 'S1C8', 'S1C9', 'S1C13', 'S1C23', 'S1C33', 'S1C43', 'S1C53', 'S1C63', 'S1C73', 'S1C83', 'S1C93', 'S1C103', 'S1C113', 'S1C123', 'S1C133', 'S1C143', 'S1C153', 'S1C163', 'S1C173', 'S1C183', 'S1C193', 'S1C203', 'S1C213', 'S1C223', 'S1C233', 'S1C243', 'S1C253', 'S1C263', 'S1C273', 'S1C283', 'S1C293', 'S1C303', 'S1C313', 'S1C323',
                       'S1C333', 'S1C343', 'S1C353', 'S1C363', 'S1C373', 'S1C383', 'S1C393', 'S1C403', 'S1C413', 'S1C423', 'S1C433', 'S1C443', 'S1C453', 'S1C463', 'S1C473', 'S1C483', 'S1C493', 'S1C503', 'S1C513', 'S1C523', 'S1C533', 'S1C543', 'S1C553', 'S1C563', 'S1C573', 'S1C583', 'S1C593', 'S1C603', 'S1C613', 'S1C623', 'S1C633', 'S1C643', 'S1C653', 'S1C663', 'S1C673', 'S1C683', 'S1C693', 'S1C703', 'S1C713', 'S2C198', 'S2C199', 'S2C200']
        return (df1)

    def input_data_create(dt_nengetsu):

        # ★不要処理も多くも有るが、保守しやすいため取得するデータは編機調整報告書と同一にする
        # ※のちの共通部品化を目指す
        # WebシステムからBOM全データを取得する
        chohyo_df = chohyo_data_get(dt_nengetsu)

        # common_dfを全件取得し、生産機のみ絞り込む
        common_df = common_data_get(dt_nengetsu)

        # 針無機械のために必要
        seisan_df = seiban_data_get(dt_nengetsu)

        # 条件に従い全DFを整えてマージする
        merged_df = df_merge(chohyo_df, common_df, seisan_df)

        # 自動帳票作成csv用のdfを作成する
        jidou_df = df_edit(merged_df)

        return (jidou_df)

    def irepo_view_get(sql):

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

    def get_chohyo_pattern(kumi_no, kisyu_name):

        # SKまたはDKを取得
        skdk = ""
        if len(kumi_no) >= 4:
            skdk = kumi_no[2:4]

        # フレームと機種を定義
        frame = ""
        kisyu = ""

        # 返却する帳票パターンを定義
        chohyo_pattern = None

        # 機種名を分解してフレームと機種を取得
        kisyu_name_parts = kisyu_name.split('-')
        if len(kisyu_name_parts) >= 2:
            # ※frameの末のハイフンは不要かもしれないが、元となったエクセルマクロより引継ぎ
            frame = kisyu_name_parts[-2]+"-"
            kisyu = kisyu_name_parts[-1]
        elif len(kisyu_name_parts) == 1:
            kisyu = kisyu_name_parts[-1]

        # 直打ちで判定　いずれ外部DBに持ちたい
        if skdk == "SK":
            # 小インチセントラル　フレームが EXC 始まり
            if frame.startswith("EXC-"):
                chohyo_pattern = 101
            # 小インチ　フレームが EX 始まり
            elif frame.startswith("EX-"):
                chohyo_pattern = 102
            # ラップ　機種が WY を含む
            elif "WY" in kisyu:
                chohyo_pattern = 103
            # F型ST電柄　機種が SEC 始まりかつ、 FY を含む
            elif kisyu.startswith("SEC") and "FY" in kisyu:
                chohyo_pattern = 104
            # F型ST　機種が FY を含む
            elif "FY" in kisyu:
                chohyo_pattern = 105
            # 旧ST電柄　機種が SEC 始まりかつ、 Y を含む
            elif kisyu.startswith("SEC") and "Y" in kisyu:
                chohyo_pattern = 106
            # 旧ST　機種が RSY 始まり
            elif kisyu.startswith("RSY"):
                chohyo_pattern = 107
            # セミジャガード　機種が JS 始まり
            elif kisyu.startswith("JS"):
                chohyo_pattern = 108
            # 電柄　機種が SEC 始まり
            elif kisyu.startswith("SEC"):
                chohyo_pattern = 109
            # M2XC　フレームが M2XC- と一致
            elif frame == "M2XC-":
                chohyo_pattern = 110
            # MXC　フレームが MXC- と一致
            elif frame == "MXC-":
                chohyo_pattern = 111
            # M2X　フレームが M2X- と一致
            elif frame == "M2X-":
                chohyo_pattern = 112
            # HXC　フレームが HXC- と一致
            elif frame == "HXC-":
                chohyo_pattern = 113
        elif skdk == "DK":
            # 小インチ　フレームが E- 始まり
            if frame.startswith("E-") or frame.startswith("EAD-"):
                chohyo_pattern = 201
            # F型ST電柄　機種が LEC 始まりかつ、 Y を含む
            elif kisyu.startswith("LEC") and "Y" in kisyu:
                chohyo_pattern = 202
            # F型ST　機種が FY を含む
            elif "FY" in kisyu:
                chohyo_pattern = 203
            # セミジャガード　機種が LPJ 始まり
            elif kisyu.startswith("LPJ"):
                chohyo_pattern = 204
            # 電柄　機種が LEC 始まり
            elif kisyu.startswith("LEC"):
                chohyo_pattern = 205
            # MC　フレームが MC- 始まり
            elif frame.startswith("MC-"):
                chohyo_pattern = 206
            # M　フレームが M- 始まり
            elif frame.startswith("M-") or frame.startswith("MAD-"):
                chohyo_pattern = 207
            # SRB　機種が SRB と一致
            elif kisyu == "SRB":
                chohyo_pattern = 208
        else:
            chohyo_pattern = 999

        return (chohyo_pattern)

    def seisan_data_create(dt_nengetsu):
       # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if os.path.isfile(os.path.dirname(__file__)+'\\Database\\hontai_seizo.db'):
            shutil.copy(os.path.dirname(__file__)+'\\Database\\hontai_seizo.db',
                        os.path.dirname(__file__)+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_hontai_seizo.db")

        # 本処理（更新処理）
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(__file__)+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # ■テーブル作成処理
        # EXIT NOTを入れているので、テーブルがあった場合はスキップする（編機以外にも使用できる項目名）
        cur.execute('''CREATE TABLE IF NOT EXISTS production_machine_info(
                  組立番号 TEXT PRIMARY KEY,
                  機種名 TEXT,
                  インチ INTEGER,
                  ゲージ INTEGER,
                  年 INTEGER,
                  月 INTEGER,
                  次 INTEGER,
                  区分 TEXT DEFAULT '生産機',
                  帳票No INTEGER
                  )''')
        
        # ADD_20241210_区分カラムを既存テーブルに追加（存在しない場合のみ）
        try:
            cur.execute("ALTER TABLE production_machine_info ADD COLUMN 区分 TEXT DEFAULT '生産機'")
        except sqlite3.OperationalError:
            # カラムが既に存在する場合は無視
            pass

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()

        df = input_data_create(dt_nengetsu)

        # 更新処理
        # 付け替え
        update_df = df[['S1C4', 'S1C6', 'S1C7', 'S1C8', 'S1C1', 'S1C2', 'S1C3']].rename(
            columns={'S1C4': '組立番号', 'S1C6': '機種名', 'S1C7': 'インチ', 'S1C8': 'ゲージ', 'S1C1': '年', 'S1C2': '月', 'S1C3': '次'})

        # 各行に対して更新処理を行う
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()
        for _, row in update_df.iterrows():
            # 組立番号が既に存在するか確認
            cur.execute(
                "SELECT * FROM production_machine_info WHERE 組立番号 = ? ", (row['組立番号'],))
            existing_records = cur.fetchall()

            # ここで帳票Noの判定処理
            chohyo_pattern = get_chohyo_pattern(row['組立番号'], row['機種名'])

            if not existing_records:
                # 条件1: 組立番号が重複していない場合、INSERT
                cur.execute("""
              INSERT INTO production_machine_info (組立番号, 機種名, インチ,ゲージ,年,月,次,区分,帳票No)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) """,
                            (row['組立番号'], row['機種名'], row['インチ'], row['ゲージ'], row['年'], row['月'], row['次'], '生産機', chohyo_pattern))
            else:
                # 条件2と条件3: 組立番号が重複している場合
                cur.execute("""
                  UPDATE production_machine_info SET 機種名 = ?, インチ = ?,ゲージ = ?,年 = ?,月 = ?,次 = ?,区分 = ?,帳票No = ? WHERE 組立番号 = ?""",
                            (row['機種名'], row['インチ'], row['ゲージ'], row['年'], row['月'], row['次'], '生産機', chohyo_pattern, row['組立番号']))

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()

        return

    def seisan_data_update(edf, df):
       # バックアップ
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        if os.path.isfile(os.path.dirname(__file__)+'\\Database\\hontai_seizo.db'):
            shutil.copy(os.path.dirname(__file__)+'\\Database\\hontai_seizo.db',
                        os.path.dirname(__file__)+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_hontai_seizo.db")

        # 本処理（更新処理）
        dbname = 'hontai_seizo.db'
        cdb = os.path.dirname(__file__)+f'\\Database\\'+dbname
        conn = sqlite3.connect(cdb)
        cur = conn.cursor()

        # 削除操作
        original_ids = set(df["組立番号"])
        edited_ids = set(edf["組立番号"])
        ids_to_delete = original_ids - edited_ids
        for id_to_delete in ids_to_delete:
            cur.execute(
                f"DELETE FROM production_machine_info WHERE 組立番号 = ?", (id_to_delete,))

        for _, row in edf.iterrows():
            # 組立番号が既に存在するか確認
            cur.execute(
                "SELECT * FROM production_machine_info WHERE 組立番号 = ? ", (row['組立番号'],))
            existing_records = cur.fetchall()
            if not existing_records:
                # 条件1: 組立番号が重複していない場合、INSERT
                cur.execute("""
                INSERT INTO production_machine_info (組立番号, 機種名, インチ,ゲージ,年,月,次,区分,帳票No)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) """,
                            (row['組立番号'], row['機種名'], row['インチ'], row['ゲージ'], row['年'], row['月'], row['次'], row.get('区分', '生産機'), row['帳票No']))
            else:
                # 条件2と条件3: 組立番号が重複している場合
                cur.execute("""
                    UPDATE production_machine_info SET 機種名 = ?, インチ = ?,ゲージ = ?,年 = ?,月 = ?,次 = ?,区分 = ?,帳票No = ? WHERE 組立番号 = ?""",
                            (row['機種名'], row['インチ'], row['ゲージ'], int(row['年']), row['月'], row['次'], row.get('区分', '生産機'), row['帳票No'], row['組立番号']))

        # 変更をコミットして接続をクローズ
        conn.commit()
        conn.close()

        return

    def main():

        st.set_page_config(
            page_title='本体Gr_製造チェックシート_基本情報登録', layout="wide")

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
    """
        st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)

        # 処理
        st.write('### 生産機基本情報登録')

        # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
        dt_now = datetime.now(timezone(timedelta(hours=9))) + \
            timedelta(days=32)  # 日本時刻+32日
        dt_nen = int(dt_now.strftime('%Y'))
        dt_tsuki = int(dt_now.strftime('%m'))

        seisan_col1, seisan_col2, seisan_col3, seisan_col_, seisan_col4, seisan_col5 = st.columns([
            1, 1, 1, 0.5, 1, 2])
        with seisan_col1:
            nen = st.selectbox('生産計画年', [dt_nen-1, dt_nen, dt_nen+1], index=1)
        with seisan_col2:
            getsu = st.selectbox('生産計画月', [
                                 '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], index=dt_tsuki-1)
        with seisan_col3:
            ji = st.selectbox(
                '生産計画次', ['', '01', '02', '03', '04', '05', '06', '07', '08'])

            dt_nengetsu = str(nen)+str(getsu)
            dt_nengetsu = dt_nengetsu[2:6]  # YYMM
        with seisan_col3:
            st.write("")
        with seisan_col4:
            editflg = st.selectbox('全項目編集', ['オフ', 'オン'])
        with seisan_col5:
            st.write("")
            with st.popover("生産機情報取得"):
                st.markdown(f'''【確認】　実行年月：{str(nen)}年{str(getsu)}月''')
                st.markdown('''**※変更済の帳票が初期値に戻ります。**''')
                st.markdown('''この操作を実行してもよろしいですか？''')
                if st.button("実行"):
                    with st.spinner('生産機情報作成処理　実行中'):
                        # インプット用のデータ作成
                        seisan_data_create(dt_nengetsu)
                        st.write('生産機情報作成処理完了')
        # データフレームエディターの処理
        dbname = 'hontai_seizo.db'
        sql = f'''select * from production_machine_info where (年 = '{nen}' and  ('{
            getsu}' = '' or 月 = '{getsu}' ) and ('{ji}' = '' or 次 = '{ji}' )) '''
        filepath = os.path.dirname(__file__)+f'\\Database\\'+dbname
        df = sqlite_data_get(sql, filepath)
        df['年'] = df['年'].astype(str)
        df = df.sort_values(['組立番号'])

        # 帳票の値を取得する
        sql = f'select 帳票No,帳票名 from report_type_table'
        df_pattern = sqlite_data_get(sql, os.path.dirname(
            __file__)+'\\Database\\hontai_seizo.db')
        df_pattern = df_pattern.sort_values(['帳票No'])
        select_list = []
        for index, row in df_pattern.iterrows():
            select_list.append(row['帳票No'])

        st.divider()

        table_col1, table_col2 = st.columns([2, 1])
        with table_col1:
            st.write("帳票の編集")
            if editflg == 'オフ':
                edited_df = st.data_editor(df.reset_index(drop=True), column_config={
                    "区分": st.column_config.SelectboxColumn(
                        label="区分",
                        options=["生産機", "整備機"]),
                    "帳票No": st.column_config.SelectboxColumn(
                        label="帳票No",
                        options=select_list)},
                    disabled=["組立番号", "機種名", "インチ", "ゲージ", "年", "月", "次"],
                    column_order=["組立番号", "機種名", "インチ", "ゲージ", "年", "月", "次", "区分", "帳票No"],
                    hide_index=True, num_rows="dynamic")
            else:
                edited_df = st.data_editor(df.reset_index(drop=True), column_config={
                    "区分": st.column_config.SelectboxColumn(
                        label="区分",
                        options=["生産機", "整備機"]),
                    "帳票No": st.column_config.SelectboxColumn(
                        label="帳票No",
                        options=select_list)},
                    column_order=["組立番号", "機種名", "インチ", "ゲージ", "年", "月", "次", "区分", "帳票No"],
                    hide_index=True, num_rows="dynamic")

        # DEL_20250610
            # if st.button("更新"):
            #     seisan_data_update(edited_df, df)
            #     st.rerun()
            #     st.write("更新完了")
        # ADD_20250610
        if st.button("更新"):
            # ADD_20241210_手動追加データの区分初期値設定
            # 新規追加行（元のdfに存在しない組立番号）の区分を「整備機」に設定
            original_assembly_numbers = set(df['組立番号'].tolist()) if not df.empty else set()
            for idx, row in edited_df.iterrows():
                if row['組立番号'] not in original_assembly_numbers and pd.isna(row.get('区分', None)):
                    edited_df.at[idx, '区分'] = '整備機'
            
            error_messages = []

            # --- ① 必須項目チェック ---
            # 空白文字列をNaNに置換してから、いずれかのセルがNaN（空欄）か判定
            required_cols = ["組立番号", "機種名", "インチ",
                             "ゲージ", "年", "月", "次", "区分", "帳票No"]
            if edited_df[required_cols].replace('', np.nan).isnull().values.any():
                error_messages.append(
                    "⚠️ **エラー**: 未入力の項目があります。全ての項目を入力してください。")

            # --- ② 半角数字チェック ---
            # ADD_20241210_NaN値とfloat型の整数値を適切に処理
            numeric_cols = ["インチ", "ゲージ", "年", "月", "次"]
            for col in numeric_cols:
                # NaN値を除外して数値チェック
                non_null_data = edited_df[col].dropna()
                for val in non_null_data:
                    try:
                        # 数値に変換可能で整数値かチェック
                        float_val = float(val)
                        if float_val != int(float_val) or float_val < 0:
                            raise ValueError("正の整数値以外は無効")
                    except (ValueError, TypeError):
                        error_messages.append(
                            f"⚠️ **エラー**: 「{col}」の列に半角数字以外が入力されています。")
                        break

            # --- ③ 判定と処理の実行 ---
            if error_messages:
                # エラーリストにメッセージがあれば、全て表示
                for msg in error_messages:
                    st.error(msg)
            else:
                # エラーがなければ、更新処理を実行
                try:
                    seisan_data_update(edited_df, df)
                    st.success("✅ 更新が完了しました。")
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"更新処理中に予期せぬエラーが発生しました: {e}")

        with table_col2:
            st.write("参考：帳票テーブル")
            st.dataframe(df_pattern, hide_index=True)

    if __name__ == "__main__":
        main()

except Exception as e:
    # 簡単なエラー処理
    print(e)
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    with open(os.path.dirname(__file__)+"\\err\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
        f.write(str(e))
