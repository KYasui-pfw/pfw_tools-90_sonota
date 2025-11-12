################################
#　編機調整報告書　　　　　　　   #
#　自動帳票作成処理　　　　　　   #
#　手動で実行する　　　　　　　　 #
# 　変更履歴：20250708_100帳票への変更
################################

#インポート
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
import time
import os
from glob import glob
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pythoncom
from datetime import datetime, timedelta, timezone
import pandas as pd
import shutil
import pyqrcode
import openpyxl
from openpyxl.styles.borders import Border, Side

try:
  
  pythoncom.CoInitialize() #サーバーサイドからローカルファイルを動かすことになるので必要 

  def chohyo_data_get(dt_nengetsu):
    #SQLAlchemyを使用した接続に変更
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
      sql = f"select job_cd,monthly,prs_full_path,comp_item_cd,comp_item_name from t_prs_job_cd_bom where monthly like '{dt_nengetsu}_'"
      df = pd.read_sql(sql, connection)
 
    # セッションを閉じる
    session.close()   
 
    return(df)

  def common_data_get(dt_nengetsu):
     
    # #DB接続定義
    # SERVER = 'production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com'
    # DATABASE = 'common'
    # USERNAME = 'fukuharaadmin'
    # PASSWORD = 'xrTRzAJtKQ7B'

    # connectionString = f'DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
    # conn = pyodbc.connect(connectionString) 
    # cursor = conn.cursor()
    # query = f"select an_item_cd,an_item_category,an_user_name,an_country_name,an_model_name,an_inch,an_gauge,an_cut_count,an_monthly from m_items_sub_71 where an_monthly like '{dt_nengetsu}_'"
    
    #SQLAlchemyを使用した接続に変更
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
      #DEL_20241119_SKDKを取得
      #sql = f"select an_item_cd,an_item_category,an_user_name,an_country_name,an_model_name,an_inch,an_gauge,an_cut_count,an_monthly from m_items_sub_71 where an_monthly like '{dt_nengetsu}_'"
      #ADD_20241119_SKDKを取得
      sql = f"select an_item_cd,an_item_category,an_user_name,an_country_name,an_model_name,an_inch,an_gauge,an_cut_count,an_monthly,an_skdk from m_items_sub_71 where an_monthly like '{dt_nengetsu}_'"
      df = pd.read_sql(sql, connection)
 
    # セッションを閉じる
    session.close()   
    return(df)
  
  def seiban_data_get(dt_nengetsu):

    #DB接続定義
    # SERVER = 'production-fukuhara-sqlserver.cqbwred3ieat.ap-northeast-1.rds.amazonaws.com'
    # DATABASE = 'chohyo'
    # USERNAME = 'fukuharaadmin'
    # PASSWORD = 'xrTRzAJtKQ7B'

    # connectionString = f'DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
    # conn = pyodbc.connect(connectionString) 
    # cursor = conn.cursor()
   
    # query = f"select job_cd from t_prs_job_cd_pln where monthly like '{dt_nengetsu}_'"
    # #取得したデータをdataframeに格納
    # df = pd.read_sql(query, conn)

    #SQLAlchemyを使用した接続に変更
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
      sql = f"select job_cd from t_prs_job_cd_pln where monthly like '{dt_nengetsu}_'"
      df = pd.read_sql(sql, connection)
 
    # セッションを閉じる
    session.close()   

    return(df)
  
  def df_merge(chohyo_df,common_df,seisan_df):

    #①の抽出
    df1a = chohyo_df[chohyo_df['prs_full_path'].str.contains('-67T',na=False)]

    df1aa = df1a.query('comp_item_name=="NEEDLE"')
    df1ab = df1a.query('comp_item_name=="DIAL NEEDLE"')
    df1ac = df1a.query('comp_item_name=="SINKER"')

    df1b = chohyo_df[chohyo_df['prs_full_path'].str.contains('-64T',na=False)]

    df1ba = df1b[df1b['prs_full_path'].str.contains('S910',na=False)]
    df1baa = df1ba.query('comp_item_name=="NEEDLE"')
    df1bab = df1ba.query('comp_item_name=="DIAL NEEDLE"')
    df1bac = df1ba.query('comp_item_name=="SINKER"')

    df1bb = df1b[df1b['prs_full_path'].str.contains('S3662',na=False)]
    df1bba = df1bb.query('comp_item_name=="NEEDLE"')
    df1bbb = df1bb.query('comp_item_name=="DIAL NEEDLE"')
    df1bbc = df1bb.query('comp_item_name=="SINKER"')

    df1 = pd.concat([df1aa,df1ab,df1ac,df1baa,df1bab,df1bac,df1bba,df1bbb,df1bbc], ignore_index=True)
    df1 = df1[~df1.duplicated(subset=["job_cd", "comp_item_cd"], keep='last')]
    #df1['hari_syubetsu'] = 1 この抽出条件は5番目に変更 DEL_20240904
    df1['hari_syubetsu'] = 5 #ADD_20240904

    #②の抽出
    df2 = chohyo_df[chohyo_df['prs_full_path'].str.contains('-57T',na=False)]

    df2a = df2.query('comp_item_name=="NEEDLE"')
    df2b = df2.query('comp_item_name=="DIAL NEEDLE"')
    df2c = df2.query('comp_item_name=="CYLINDER NEEDLE"')

    df2 = pd.concat([df2a,df2b,df2c], ignore_index=True)
    df2 = df2[~df2.duplicated(subset=["job_cd", "comp_item_cd"], keep='last')]
    #df2['hari_syubetsu'] = 2 この抽出条件は1番目に変更  DEL_20240904
    df2['hari_syubetsu'] = 1 #ADD_20240904

    #③の抽出
    df3a = chohyo_df[chohyo_df['prs_full_path'].str.contains('-58T',na=False)]
    df3b = chohyo_df[chohyo_df['prs_full_path'].str.contains('-68T',na=False)]

    df3a = df3a[df3a['comp_item_name'].str.contains('INTER',na=False)]
    df3b = df3b[df3b['comp_item_name'].str.contains('INTER',na=False)]

    df3 = pd.concat([df3a,df3b], ignore_index=True)
    df3 = df3[~df3.duplicated(subset=["job_cd", "comp_item_cd"], keep='last')]
    
    #-58T と -68T を分離することに変更 DEL_20240904
    # df3['hari_syubetsu'] = 3
    #-58T と -68T を分離することに変更 ADD_20240904
    df3['hari_syubetsu'] = ""
    df3.loc[df3['prs_full_path'].str.contains('-58T',na=False), 'hari_syubetsu'] = 2
    df3.loc[df3['prs_full_path'].str.contains('-68T',na=False), 'hari_syubetsu'] = 6

    #④の抽出
    #df4a = chohyo_df[chohyo_df['prs_full_path'].str.match('....-58T.*',na=False)]#正規表現での抽出に変更 ⇒ダメフルパスしか持たないので
    #df4b = chohyo_df[chohyo_df['prs_full_path'].str.match('....-68T.*',na=False)]
    df4a = chohyo_df[chohyo_df['prs_full_path'].str.contains('-58T',na=False)] 
    df4b = chohyo_df[chohyo_df['prs_full_path'].str.contains('-68T',na=False)]
    
    df4aa = df4a[df4a['comp_item_name'].str.contains('PATTE',na=False)]
    df4ab = df4a[df4a['comp_item_name'].str.contains('SELEC',na=False)]
    df4ba = df4b[df4b['comp_item_name'].str.contains('PATTE',na=False)]
    df4bb = df4b[df4b['comp_item_name'].str.contains('SELEC',na=False)]

    #この抽出条件は -58T と -68T を分離することに変更 DEL_20240904
    df4 = pd.concat([df4aa,df4ab,df4ba,df4bb], ignore_index=True)
    df4 = df4[~df4.duplicated(subset=["job_cd", "comp_item_cd"], keep='last')]
    
    #-58T と -68T を分離することに変更 DEL_20240904
    # df4['hari_syubetsu'] = 4
    #-58T と -68T を分離することに変更 ADD_20240904
    df4['hari_syubetsu'] = ""
    df4.loc[df4['prs_full_path'].str.contains('-58T',na=False), 'hari_syubetsu'] = 3
    df4.loc[df4['prs_full_path'].str.contains('-68T',na=False), 'hari_syubetsu'] = 7
    

    #⑤の抽出
    df5a = chohyo_df[chohyo_df['prs_full_path'].str.contains('-58T',na=False)] 
    df5b = chohyo_df[chohyo_df['prs_full_path'].str.contains('-68T',na=False)]
    #df5a = chohyo_df[chohyo_df['prs_full_path'].str.match('....-58T.*',na=False)]#正規表現での抽出に変更 ⇒ダメ
    #df5b = chohyo_df[chohyo_df['prs_full_path'].str.match('....-68T.*',na=False)]
    df5 = pd.concat([df5a,df5b], ignore_index=True)
    df5 = df5[~df5.duplicated(subset=["job_cd", "comp_item_cd"],  keep='last')]

    #③と④以外を抽出する処理
    df5c = pd.concat([df3a,df3b], ignore_index=True)
    df5d = pd.concat([df4aa,df4ab,df4ba,df4bb], ignore_index=True)
    df5 = pd.concat([df5,df5c,df5d], ignore_index=True)
    df5 = df5[~df5.duplicated(subset=["job_cd", "comp_item_cd"],  keep=False)]
    #さらにASSYを省く
    df5 = df5[~df5['comp_item_name'].str.contains('ASSY.',na=False)]
    df5 = df5[df5['comp_item_name'].str.contains('ROCKING PIECE',na=False)] #追加　ROCKING PIECEを含む(その他での抽出難)
    #-58T と -68T を分離することに変更 DEL_20240904
    #df5['hari_syubetsu'] = 5
    df5['hari_syubetsu'] = ""
    df5.loc[df5['prs_full_path'].str.contains('-58T',na=False), 'hari_syubetsu'] = 4
    df5.loc[df5['prs_full_path'].str.contains('-68T',na=False), 'hari_syubetsu'] = 8

    #結合
    merged_chohyo_df = pd.concat([df1,df2,df3,df4,df5], ignore_index=True)

    # #組立番号を主キーに結合
    merged_df = pd.merge(seisan_df, merged_chohyo_df, left_on='job_cd', right_on='job_cd',how='left')
    merged_df = pd.merge(merged_df, common_df, left_on='job_cd', right_on='an_item_cd',how='left')
    #merged_df = merged_df.sort_values(['job_cd','hari_syubetsu']) #DEL_20240904_sortに部番を追加
    merged_df = merged_df.sort_values(['job_cd','hari_syubetsu','comp_item_cd']) #ADD_20240904sortに部番を追加
    merged_df = merged_df[merged_df['an_item_category'].str.contains('生産機',na=False)]

    return(merged_df)

  def df_edit(merged_df):

    #df1はヘッダ部
    df1 = merged_df    
    df1['youto']="kari"
    df1['nen']=df1['an_monthly'].str[0:2]
    df1['getsu']=df1['an_monthly'].str[2:4]
    df1['ji']=df1['an_monthly'].str[4:5]
    df1['syukkasaki'] = df1['an_country_name'].str.cat(df1['an_user_name'], sep='　　　')
    df3 = df1.loc[:,['job_cd','an_model_name','an_inch','an_skdk']] #ADD_20241119 SKDK判断、閾値設定用にDFを分離（後にmergeする）
    df3 = df3[~df3.duplicated(keep='last')] #ADD_20241119 SKDK判断、閾値設定用にDFを分離（後にmergeする）
    df1 = df1.loc[:,['youto','nen','getsu','ji','job_cd','syukkasaki','an_model_name','an_inch','an_gauge','an_cut_count']]
    df1 = df1[~df1.duplicated(keep='last')]

    #報告書の種類の判定　LEC・SECを含むか
    mask_df = df1['an_model_name'].str.contains('LEC|SEC',na=False)
    df1.loc[mask_df, 'youto'] = '＜EK '
    mask_df = ~df1['an_model_name'].str.contains('LEC|SEC',na=False)
    df1.loc[mask_df, 'youto'] = '＜ﾉｰﾏﾙ '

    #Y付きY無を追記
    mask_df = df1['an_model_name'].str.contains('Y',na=False)
    df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "Y付き用"
    mask_df = ~df1['an_model_name'].str.contains('Y',na=False)
    df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "Y無し用"

    #ADD_20240927 ｾﾐｼﾞｬｶﾞｰﾄﾞ機の判断
    mask_df = df1['an_model_name'].str.contains('-LPJ|-JS',na=False)
    df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "　J＞"
    mask_df = ~df1['an_model_name'].str.contains('-LPJ|-JS',na=False)
    df1.loc[mask_df, 'youto'] = df1.loc[mask_df, 'youto'] + "＞"

    ##ADD_20241023_Start
    # 存在するのは以下の６パターンのため、それぞれのパターンごとに最新の帳票IDをセット
    # EKY付、EKY無、ﾉｰﾏﾙY付、ﾉｰﾏﾙY無、ﾉｰﾏﾙY無ｾﾐｼﾞｬｶﾞｰﾄﾞ、ﾉｰﾏﾙY付ｾﾐｼﾞｬｶﾞｰﾄﾞ
    df1.insert(0, 'defTopId', '') 
    # EKY付 393
    mask_df = df1['youto'].str.contains('＜EK Y付き用＞',na=False)
    sql = "select def_top_id from view_def_top where def_top_org = 393 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
    # EKY無 394
    mask_df = df1['youto'].str.contains('＜EK Y無し用＞',na=False)
    sql = "select def_top_id from view_def_top where def_top_org = 394 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
    # ﾉｰﾏﾙY付 395
    mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y付き用＞',na=False)
    sql = "select def_top_id from view_def_top where def_top_org = 395 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
    # ﾉｰﾏﾙY無 398
    mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y無し用＞',na=False)
    sql = "select def_top_id from view_def_top where def_top_org = 398 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
    # ﾉｰﾏﾙY付ｾﾐｼﾞｬｶﾞｰﾄﾞ 396
    mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y付き用　J＞',na=False)
    sql = "select def_top_id from view_def_top where def_top_org = 396 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()
    # ﾉｰﾏﾙY無ｾﾐｼﾞｬｶﾞｰﾄﾞ 397
    mask_df = df1['youto'].str.contains('＜ﾉｰﾏﾙ Y無し用　J＞',na=False)
    sql = "select def_top_id from view_def_top where def_top_org = 397 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    df1.loc[mask_df, 'defTopId'] = irepo_df['def_top_id'].max()

    #df2明細部（針の部分）
    df2 = merged_df

    #追加ループ71
    for idx in range(71):
      df1[f'hari{idx}'] = ""

    count = 0
    for idx in range(df2.shape[0]):

      #df1を組立番号で特定
      mask = df1['job_cd'] == df2.iloc[idx,df2.columns.get_loc('job_cd')]

      #組立番号判定
      if df2.iloc[idx-1,df2.columns.get_loc('job_cd')] == df2.iloc[idx,df2.columns.get_loc('job_cd')]:
        count += 1
      else:
        count = 0
      
      #針種別判定（直前と針種別が変わっている） or 組立番号判定（組立番号が変わっている　countで判定）
      if not df2.iloc[idx-1,df2.columns.get_loc('hari_syubetsu')] == df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] or count==0:

        #針種別の考え方変更に伴い、つけ直し　DEL_20240904
        # if df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 1:
        #   df1.loc[mask,f'hari{count}'] = "【■シンカー／ダイヤル針■】"
        # elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 2:
        #   df1.loc[mask,f'hari{count}'] = "【■シリンダー針■】"
        # elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 3:
        #   df1.loc[mask,f'hari{count}'] = "【■中間ジャック■】"
        # elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 4:
        #   df1.loc[mask,f'hari{count}'] = "【■パターニングジャック■】"
        # elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 5:
        #   df1.loc[mask,f'hari{count}'] = "【■ロッキングピース■】"
        
        #針種別の考え方変更に伴い、つけ直し　ADD_20240904
        if df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 1:
          df1.loc[mask,f'hari{count}'] = "【■シリンダー針】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 2:
          df1.loc[mask,f'hari{count}'] = "【■中間ジャック(C)】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 3:
          df1.loc[mask,f'hari{count}'] = "【■ ﾊﾟﾀｰﾆﾝｸﾞｼﾞｬｯｸ (C)】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 4:
          df1.loc[mask,f'hari{count}'] = "【■ロッキングピース(C)】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 5:
          df1.loc[mask,f'hari{count}'] = "【▼ ｼﾝｶｰ/ﾀﾞｲﾔﾙ針 】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 6:
          df1.loc[mask,f'hari{count}'] = "【▼中間ジャック(D)】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 7:
          df1.loc[mask,f'hari{count}'] = "【▼ ﾊﾟﾀｰﾆﾝｸﾞｼﾞｬｯｸ(D) 】"
        elif df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 8:
          df1.loc[mask,f'hari{count}'] = "【▼ロッキングピース(D)】"
        count += 1
          
      #部番を格納
      df1.loc[mask,f'hari{count}'] = df2.iloc[idx,df2.columns.get_loc(f'comp_item_cd')]
      
      #シンカー／ダイヤル針、シリンダー針のときは一行空ける
      #if df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 1 or df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 2: #DEL_20240904
      if df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 1 or df2.iloc[idx,df2.columns.get_loc('hari_syubetsu')] == 5: #ADD_20240904
        count += 1

    #取り込み用にデータを整える
    #最新の帳票IDを取得
    #sql = "select def_top_id from view_def_top where def_top_org = 352 and public_status = 2" DEL_20241023処理タイミング変更（帳票分割につき）
    #irepo_df = irepo_view_get(sql) DEL_20241023処理タイミング変更（帳票分割につき）

    #ADD_20241119_SKDKによる閾値の設定
    df3['閾値開始'] = 0.08
    df3['閾値終了'] = 0.35
    mask_df = df3['an_skdk'].str.contains('SK',na=False)
    mask_df2 = df3['an_model_name'].str.contains('A3.2RE',na=False)
    combined_mask = mask_df & mask_df2
    df3a1 = df3.loc[combined_mask, :]
    df3a1.loc[df3a1['an_inch'] <= 33,'閾値開始'] = 0.12
    df3a1.loc[df3a1['an_inch'] <= 33,'閾値終了'] = 0.42
    df3a1.loc[(df3a1['an_inch'] >= 34) & (df3a1['an_inch'] <= 39), '閾値開始'] = 0.22
    df3a1.loc[(df3a1['an_inch'] >= 34) & (df3a1['an_inch'] <= 39), '閾値終了'] = 0.42
    df3a1.loc[df3a1['an_inch'] >= 40,'閾値開始'] = 0.20
    df3a1.loc[df3a1['an_inch'] >= 40,'閾値終了'] = 0.50
    
    mask_df2 = df3['an_model_name'].str.contains('E3.2',na=False)
    combined_mask = mask_df & mask_df2
    df3a2 = df3.loc[combined_mask, :]
    df3a2.loc[df3a2['an_inch'] <= 33,'閾値開始'] = 0.15
    df3a2.loc[df3a2['an_inch'] <= 33,'閾値終了'] = 0.30
    df3a2.loc[df3a2['an_inch'] >= 34,'閾値開始'] = 0.18
    df3a2.loc[df3a2['an_inch'] >= 34,'閾値終了'] = 0.33

    mask_df = df3['an_skdk'].str.contains('SK',na=False)
    mask_df2 = ~df3['an_model_name'].str.contains('A3.2RE',na=False)
    mask_df3 = ~df3['an_model_name'].str.contains('E3.2',na=False)
    combined_mask = mask_df & mask_df2 & mask_df3
    df3a3 = df3.loc[combined_mask, :]

    
    mask_df = df3['an_skdk'].str.contains('DK',na=False)
    df3b = df3.loc[mask_df, :]
    df3b.loc[df3b['an_inch'] <= 39,'閾値開始'] = 0.06
    df3b.loc[df3b['an_inch'] <= 39,'閾値終了'] = 0.35
    df3b.loc[df3b['an_inch'] >= 40,'閾値開始'] = 0.15
    df3b.loc[df3b['an_inch'] >= 40,'閾値終了'] = 0.45

    df3 = pd.concat([df3a1,df3a2,df3a3,df3b], ignore_index=True)
    df3 = df3.loc[:,['job_cd','閾値開始','閾値終了','an_skdk']]
    df1 = pd.merge(df1, df3, left_on=['job_cd'],right_on=['job_cd'],how='left')
    
    # ADD_20250118_年は西暦4桁
    df1['nen'] = df1['nen'].apply(lambda x: int('20' + str(x)))

    # ADD_20250312_吋ゲージの数値処理追加
    mask = (df1['an_inch'] != '') & df1['an_inch'].apply(
        lambda x: float(x).is_integer() if x != '' else False)
    df1.loc[mask, 'an_inch'] = df1.loc[mask, 'an_inch'].apply(
        lambda x: str(int(float(x))))
    mask = (df1['an_gauge'] != '') & df1['an_gauge'].apply(
        lambda x: float(x).is_integer() if x != '' else False)
    df1.loc[mask, 'an_gauge'] = df1.loc[mask, 'an_gauge'].apply(
        lambda x: str(int(float(x))))

    #※帳票IDは常に最新のものを取得する必要有
    #df1.insert(0, 'defTopId', irepo_df['def_top_id'].max()) DEL_20241023処理タイミング変更（帳票分割につき）
    df1.insert(0, 'H', 'R')
    #df1.columns = ['H','defTopId','S1C0','S1C1','S1C2','S1C3','S1C4','S1C5','S1C6','S1C7','S1C8','S1C9','S1C14','S1C31','S1C48','S1C65','S1C82','S1C99','S1C116','S1C133','S1C150','S1C167','S1C184','S1C201','S1C218','S1C235','S1C252','S1C269','S1C286','S1C303','S1C320','S1C337','S1C354','S1C371','S1C388','S1C405','S1C422','S1C439','S1C456','S1C473','S1C490','S1C507','S1C524','S1C541','S1C558','S1C575','S1C592','S1C609','S1C626','S1C643','S1C660','S1C677','S1C694','S1C711','S1C728','S1C745','S1C762','S1C779','S1C796','S1C813','S1C830','S1C847','S1C864','S1C881','S1C898','S1C915','S1C932','S1C949','S1C966','S1C983','S1C1000','S1C1017','S1C1034','S1C1051','S1C1068','S1C1085','S1C1102','S1C1119','S1C1136','S1C1153','S1C1170','S1C1187','S1C1204']
    #df1.columns = ['H','defTopId','S1C0','S1C1','S1C2','S1C3','S1C4','S1C5','S1C6','S1C7','S1C8','S1C9','S1C13','S1C23','S1C33','S1C43','S1C53','S1C63','S1C73','S1C83','S1C93','S1C103','S1C113','S1C123','S1C133','S1C143','S1C153','S1C163','S1C173','S1C183','S1C193','S1C203','S1C213','S1C223','S1C233','S1C243','S1C253','S1C263','S1C273','S1C283','S1C293','S1C303','S1C313','S1C323','S1C333','S1C343','S1C353','S1C363','S1C373','S1C383','S1C393','S1C403','S1C413','S1C423','S1C433','S1C443','S1C453','S1C463','S1C473','S1C483','S1C493','S1C503','S1C513','S1C523','S1C533','S1C543','S1C553','S1C563','S1C573','S1C583','S1C593','S1C603','S1C613','S1C623','S1C633','S1C643','S1C653','S1C663','S1C673','S1C683','S1C693','S1C703','S1C713'] DEL_20241119_基準値とSKDKの追加
    df1.columns = ['H','defTopId','S1C0','S1C1','S1C2','S1C3','S1C4','S1C5','S1C6','S1C7','S1C8','S1C9','S1C13','S1C23','S1C33','S1C43','S1C53','S1C63','S1C73','S1C83','S1C93','S1C103','S1C113','S1C123','S1C133','S1C143','S1C153','S1C163','S1C173','S1C183','S1C193','S1C203','S1C213','S1C223','S1C233','S1C243','S1C253','S1C263','S1C273','S1C283','S1C293','S1C303','S1C313','S1C323','S1C333','S1C343','S1C353','S1C363','S1C373','S1C383','S1C393','S1C403','S1C413','S1C423','S1C433','S1C443','S1C453','S1C463','S1C473','S1C483','S1C493','S1C503','S1C513','S1C523','S1C533','S1C543','S1C553','S1C563','S1C573','S1C583','S1C593','S1C603','S1C613','S1C623','S1C633','S1C643','S1C653','S1C663','S1C673','S1C683','S1C693','S1C703','S1C713','S2C198','S2C199','S2C200']
    return(df1)

  def input_data_create(dt_nengetsu):

    #WebシステムからBOM全データを取得する 
    chohyo_df = chohyo_data_get(dt_nengetsu)

    #common_dfを全件取得し、生産機のみ絞り込む
    common_df = common_data_get(dt_nengetsu)

    #針無機械のために必要
    seisan_df = seiban_data_get(dt_nengetsu)

    #条件に従い全DFを整えてマージする
    merged_df = df_merge(chohyo_df,common_df,seisan_df)

    #自動帳票作成csv用のdfを作成する
    jidou_df = df_edit(merged_df)

    return(jidou_df)
  
  def data_upload(csv_name,df_len):

    #chromeのwebdriverをセット
    driver = webdriver.Chrome()
    #アドレスを指定（直接アップロード画面を指定）/1秒待機
    #driver.get("http://localhost/ConMasManager/AutoGenerate")
    driver.get("http://172.17.52.101/ConMasManager/AutoGenerate")
    time.sleep(1)

    #ユーザー名/パスワード/ログイン画面/1秒待機
    driver.find_element(by=By.XPATH, value='//*[@id="UserName"]').send_keys('mainte')
    driver.find_element(by=By.XPATH, value='//*[@id="Password"]').send_keys('@next123')
    driver.find_element(by=By.XPATH, value='//*[@id="image-login_btn"]').click()
    time.sleep(1)

    #ドロップダウンリストを取得（一旦テストを取得）
    driver.find_element(by=By.XPATH, value='//*[@id="PublicStatus"]').click()
    dropdown = driver.find_element(by=By.XPATH, value='//*[@id="PublicStatus"]')
    select = Select(dropdown)
    #select.select_by_value('1')  # 1番目のoptionタグを選択状態に（テスト）
    select.select_by_value('2')  # 2番目のoptionタグを選択状態に（公開）
    time.sleep(2)

    # ADD_20250708_100帳票への変更
    #ドロップダウンリストを取得（一旦テストを取得）
    driver.find_element(
        by=By.XPATH, value='//*[@id="PageSize"]').click()
    dropdown = driver.find_element(
        by=By.XPATH, value='//*[@id="PageSize"]')
    select = Select(dropdown)
    select.select_by_value('100')  # 100を選ぶ
    time.sleep(2)

    #ﾁｪｯｸﾎﾞｯｸｽをクリック
    time.sleep(1) #待機しないとエラーになる
    #driver.find_element(by=By.XPATH, value='//*[@id="Cbx"]').click()
    sql = "select def_top_id from view_def_top where def_top_org = 393 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる
    sql = "select def_top_id from view_def_top where def_top_org = 394 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる
    sql = "select def_top_id from view_def_top where def_top_org = 395 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる
    sql = "select def_top_id from view_def_top where def_top_org = 396 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる
    sql = "select def_top_id from view_def_top where def_top_org = 397 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる
    sql = "select def_top_id from view_def_top where def_top_org = 398 and public_status = 2"
    irepo_df = irepo_view_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    #次へボタンクリック
    time.sleep(1)
    driver.find_element(by=By.XPATH, value='//*[@id="FiltersTable"]/tbody/tr/td[2]/a[2]').click()
    time.sleep(1)

    #ドロップダウンリストを取得(簡易csv）
    driver.find_element(by=By.XPATH, value='//*[@id="type"]').click()
    dropdown = driver.find_element(by=By.XPATH, value='//*[@id="type"]')
    select = Select(dropdown)
    select.select_by_value('csvSimple')  # 4番目のoptionタグを選択状態に
    time.sleep(1)

    #ドロップダウンリストを取得(1）
    driver.find_element(by=By.XPATH, value='//*[@id="defaultMode"]').click()
    dropdown = driver.find_element(by=By.XPATH, value='//*[@id="defaultMode"]')
    select = Select(dropdown)
    select.select_by_value('1')  # 1番目のoptionタグを選択状態に
    time.sleep(1)


    #ファイルアップロードボタンの要素取得
    file_upload = driver.find_element(by=By.XPATH, value='//*[@id="file1"]')
    time.sleep(1)

    #ファイルアップロードにcsvファイルをセット
    file_upload.send_keys(csv_name)

    #確認ボタンクリック/1件0.7秒待機
    driver.find_element(by=By.XPATH, value='//*[@id="DetailSection"]/div/div[1]/input').click()
    time.sleep(int(df_len*0.7))

    #記録のため、画面のハードコピーを取得1
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    sc1_name = dt_now.strftime('%Y%m%d%H%M%S'+'_作成'+os.path.splitext(os.path.basename(csv_name))[0]+'_SC1.png')
    driver.save_screenshot(os.path.dirname(__file__)+"\\work\\sumi\\png\\"+sc1_name)  

    #取り込みボタンクリック/1件4.7秒待機
    driver.find_element(by=By.XPATH, value='//*[@id="DetailSection"]/div/div[2]/input').click()
    time.sleep(int(df_len*4.7))

    #記録のため、画面のハードコピーを取得2
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    sc2_name = dt_now.strftime('%Y%m%d%H%M%S'+'_作成'+os.path.splitext(os.path.basename(csv_name))[0]+'_SC2.png')
    driver.save_screenshot(os.path.dirname(__file__)+"\\work\\sumi\\png\\"+sc2_name)  
    time.sleep(1)

    #インプットファイルをリネームして移動
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    backup_name = dt_now.strftime('%Y%m%d%H%M%S')+'_作成'+os.path.basename(csv_name)
    shutil.move(csv_name,os.path.dirname(__file__)+"\\work\\sumi\\"+backup_name)
    time.sleep(1)

    #終了処理　driverオブジェクトを開放する
    driver.quit()

  def rireki_read():    
    con_df = pd.read_csv(os.path.dirname(__file__)+"\\config\\rireki.csv")
    nen = con_df.iat[0,0]
    getsu = con_df.iat[0,1]
    return(nen,getsu)

  def rireki_write(nen,getsu):    
    con_df = pd.read_csv(os.path.dirname(__file__)+"\\config\\rireki.csv")
    con_df.iat[0,0] = nen
    con_df.iat[0,1] = getsu
    con_df.to_csv(os.path.dirname(__file__)+"\\config\\rireki.csv", index = False)

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
 
    return(df)

  def qr_create(nen,getsu):
    # ADD_20250118_年は西暦4桁
    #snen = int(str(nen)[2:4])
    snen = int(nen)
    sgetsu = int(getsu)
    #sql = f"select rep_top_id,rep_top_name,top_remarks1,top_remarks2,top_remarks3 from view_report_352 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'" DEL_20241023_分割により削除
    #qr_df = irepo_view_get(sql) DEL_20241023_分割により削除
    #ADD_20241023_分割対応
    sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_393 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
    qr_df1 = irepo_view_get(sql)
    sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_394 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
    qr_df2 = irepo_view_get(sql)
    sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_395 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
    qr_df3 = irepo_view_get(sql)
    sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_396 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
    qr_df4 = irepo_view_get(sql)
    sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_397 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
    qr_df5 = irepo_view_get(sql)
    sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_398 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
    qr_df6 = irepo_view_get(sql)
    qr_df = pd.concat([qr_df1,qr_df2,qr_df3,qr_df4,qr_df5,qr_df6], ignore_index=True)
    qr_df = qr_df.sort_values(['top_remarks3','top_remarks4'])


    #前回ファイルを削除
    for p in glob(os.path.dirname(__file__)+'\\qr_code\\*.png', recursive=True):
      if os.path.isfile(p):
        os.remove(p)

    #jp.co.cimtops.ireporter.openreport:repid=4080
    qr_list =[]
    for index, row in qr_df.iterrows():
      id = row['rep_top_id']
      nen = row['top_remarks1']
      getsu = row['top_remarks2']
      ji = row['top_remarks3']
      name = row['top_remarks4']
      code = pyqrcode.create(f"jp.co.cimtops.ireporter.openreport:repid={id}", error='L', version=3, mode='binary')
      code.png(os.path.dirname(__file__)+f'\\qr_code\\qrcode_{index}.png', scale=6)
      qr_list.append([os.path.dirname(__file__)+f'\\qr_code\\qrcode_{index}.png',nen,getsu,ji,name])

    return(qr_list)

  def qr_list_create(qr_list,nen,getsu):
    
    #前回ファイルを削除
    for p in glob(os.path.dirname(__file__)+'\\qr_code\\*xlsx', recursive=True):
      if os.path.isfile(p):
        os.remove(p)

    #一旦エクセルを作成して保存
    filename = f'{nen}年{getsu}月.xlsx'
    wb = os.path.dirname(__file__)+f'\\qr_code\\'+filename
    qr_wb = openpyxl.Workbook()
    qr_wb.save(wb)

    #ワークシート取得
    qr_ws = qr_wb.active

    #各種設定
    # 余白とヘッダーフッターは全部0
    qr_ws.page_margins.left = 0
    qr_ws.page_margins.right = 0
    qr_ws.page_margins.top = 0
    qr_ws.page_margins.bottom = 0
    qr_ws.page_margins.header = 0
    qr_ws.page_margins.footer = 0
    #ページ設定を水平にする
    qr_ws.print_options.horizontalCentered = True

    #引き渡された要素数を取得
    qr_len = len(qr_list)
    #要素格納ループ
    for i in range(qr_len):
      #画像を選択
      #img_to_excel = openpyxl.drawing.image.Image(os.path.dirname(__file__)+f'\\qr_code\\qrcode_{i}.png')
      img_to_excel = openpyxl.drawing.image.Image(qr_list[i][0])

      #指定の位置に画像を添付
      gyo = 13
      
      #１行目で行幅調整
      #qr_ws.row_dimensions[i*gyo].height = 10
      qr_ws.row_dimensions[i*gyo].height = 12

      #シート内に固定文字出力
      c = 3+(i*gyo)
      qr_ws[f"B{c}"] = "編機調整報告書"
      qr_ws[f"B{c}"].font = openpyxl.styles.Font(size = 24)

      c = 4+(i*gyo)
      qr_ws[f"B{c}"] = "　　　カメラ起動用QRコード"
      qr_ws[f"B{c}"].font = openpyxl.styles.Font(size = 18)

      c = 7+(i*gyo)
      qr_ws[f"C{c}"] = f"{qr_list[i][1]}年{qr_list[i][2]}月{qr_list[i][3]}次"
      qr_ws[f"C{c}"].font = openpyxl.styles.Font(size = 18)
      
      c = 9+(i*gyo)
      qr_ws[f"C{c}"] = f"{qr_list[i][4]}"
      qr_ws[f"C{c}"].font = openpyxl.styles.Font(size = 28)

      c= 3+(i*gyo)
      qr_ws.add_image(img_to_excel, f'H{c}')

      #下点線
      if (i+1)%4 != 0:
        c = (i+1)*gyo
        side = Side(style='mediumDashed', color='000000')
        border = Border(bottom=side)
        qr_ws[f'A{c}'].border = border
        qr_ws[f'B{c}'].border  = border
        qr_ws[f'C{c}'].border  = border
        qr_ws[f'D{c}'].border  = border
        qr_ws[f'E{c}'].border  = border
        qr_ws[f'F{c}'].border  = border
        qr_ws[f'G{c}'].border  = border
        qr_ws[f'H{c}'].border  = border
        qr_ws[f'I{c}'].border  = border
        qr_ws[f'J{c}'].border  = border
        qr_ws[f'K{c}'].border  = border

    #保存
    qr_wb.save(wb)

    # ファイルを読み込む
    with open(wb, 'rb') as file:
      filedata = file.read()

    return(filedata,filename)

  def main():

    st.set_page_config(
    page_title = '編機調整報告書',page_icon='move.gif')

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

    # メイン画面
    #st.title('編機調整報告書_作成処理')

    # 水平線
    #st.divider()
    
    # 処理
    st.write('### ①生産計画年月の指定')
    rnen,rgetsu = rireki_read()
    st.write(f'※最後に実行されたのは　{rnen}年{rgetsu}月　です。')
    st.write('')

    # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
    dt_now = datetime.now(timezone(timedelta(hours=9)))+ timedelta(days=32) # 日本時刻+32日
    dt_nen = int(dt_now.strftime('%Y'))
    dt_tsuki = int(dt_now.strftime('%m'))
    
    seisan_col1, seisan_col2,seisan_col3,seisan_col4= st.columns(4)
    with seisan_col1:
      nen = st.selectbox('生産計画年',[dt_nen-1,dt_nen,dt_nen+1],index=1)
    with seisan_col2:
      getsu = st.selectbox('生産計画月',['01','02','03','04','05','06','07','08','09','10','11','12'],index=dt_tsuki-1)
    
    dt_nengetsu = str(nen)+str(getsu)
    dt_nengetsu = dt_nengetsu[2:6] #YYMM
    
    # 水平線
    st.divider()
    
    # 処理
    st.write('### ②帳票作成処理の実行')
    with st.popover("帳票作成実行"):
        st.markdown(f'''【確認】　実行年月：{str(nen)}年{str(getsu)}月  
                      **この操作を実行してもよろしいですか？**''')   
        if st.button("実行"):
          if ((rnen==nen) and (int(rgetsu)>=int(getsu))) or (rnen>nen):
            st.write('エラー：処理実行済の生産年月が指定されています。')
            
          elif ((rnen==nen) and ((int(getsu)-int(rgetsu))>1)) or ((rnen<nen) and (int(rgetsu)-int(getsu))<11) or ((int(nen)-int(rnen))>1):
            st.write('エラー：前回の処理実行から２カ月以上先が指定されています。')
          else:
            with st.spinner('帳票作成処理　実行中（目安：７～１０分）'):
              #インプット用のデータ作成
              input_df = input_data_create(dt_nengetsu)

              #DFをcsvにコンバートして出力
              dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
              csv_name = os.path.dirname(__file__)+"\\work\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_自動帳票作成データ"+".csv"
              input_df.to_csv(csv_name,index=False,encoding='CP932')
              #input_df.head(3).to_csv(csv_name,index=False,encoding='CP932')

              # 履歴csvを更新
              rireki_write(nen,getsu)

              # #CSVをアップロード
              data_upload(csv_name,input_df.shape[0])

              #csv作成完了
              st.write('帳票作成処理完了')

    # 水平線
    st.divider()
    # 処理
    st.write('### ③カメラ起動用QRコード一覧作成')
    st.write('　※QRコードは何度でも再作成可能です')
    if st.button("QRコード作成処理実行"):
      with st.spinner('QRコード作成処理　実行中'):
        qr_list = qr_create(nen,getsu)
        if len(qr_list) == 0:
          st.write(f'データ無し　{nen}年{getsu}月は帳票が作成されていません')
        else:
          filedata,filename = qr_list_create(qr_list,nen,getsu)

          # ダウンロードボタンの表示
          st.markdown('処理終了：処理結果のエクセルを以下からダウンロードしてください')

          st.download_button(
            label='処理結果ダウンロード',
            data=filedata,
            file_name=filename,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          )        
  if __name__ == "__main__":
      main()
      
except Exception as e:
  #簡単なエラー処理
  print(e)
  dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
  with open(os.path.dirname(__file__)+"\\err\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
    f.write(str(e))
