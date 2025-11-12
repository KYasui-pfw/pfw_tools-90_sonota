################################
#　編機調整報告書                #
#　簡単なDF表示のページ          #
################################
#インポート
import streamlit as st
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd

try:
 
  #ireporterDB
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
  
      return(df)

  def main():

    st.set_page_config(
      page_title = '編機調整報告書_作業者データ一覧',
      layout="wide" ,page_icon='move.gif'
      
    )

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

    # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
    dt_now = datetime.now(timezone(timedelta(hours=9)))+ timedelta(days=32) # 日本時刻+32日
    dt_nen = int(dt_now.strftime('%Y'))
    dt_tsuki = int(dt_now.strftime('%m'))
    
    seisan_col1, seisan_col2,seisan_col3,seisan_col4,seisan_col5= st.columns([1,1,1,1,1])
    with seisan_col1:
      nen = st.selectbox('生産計画年',[dt_nen-1,dt_nen,dt_nen+1],index=1)
    with seisan_col2:
      getsu = st.selectbox('生産計画月',['','01','02','03','04','05','06','07','08','09','10','11','12'],index=dt_tsuki-1)
    with seisan_col3:
      if getsu == '':
        ji = ''
      else:
        ji = st.selectbox('生産計画次',['','01','02','03','04','05','06','07','08'])
    #追加 前後１次表示 ADD_20241111
    with seisan_col4:
      c_flg = 0
      s_nenplus = 0
      s_nenminus = 0
      s_getsuplus = 0
      s_getsuminus = 0
      s_jiplus = 0
      s_jiminus = 0

      if st.checkbox('前後1次を表示'):
        #条件追加
        c_flg = 1
        #月が空欄
        if getsu == '':
          s_nenplus = nen + 1
          s_nemminus = nen - 1
          s_getsuplus = '01'
          s_getsuminus = '12'
          s_jiplus = '01'
          s_jiminus = '08'
        #月が1月
        elif getsu == '01':
          #次が空欄
          if ji == '':
            s_nenplus = nen
            s_nenminus = nen - 1
            s_getsuplus = '02'
            s_getsuminus = '12'  
            s_jiplus = '01'
            s_jiminus = '08'      
          #次が01
          elif ji == '01':
            s_nenplus = nen
            s_nenminus = nen - 1
            s_getsuplus = '01'
            s_getsuminus = '12'  
            s_jiplus = '02'
            s_jiminus = '08'
          #次が08
          elif ji == '08':
            s_nenplus = nen 
            s_nenminus = nen
            s_getsuplus = '02'
            s_getsuminus = '01'  
            s_jiplus = '01'
            s_jiminus = '07'
          #次が01と08以外
          else:
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = '01'
            s_getsuminus = '01'
            s_jiplus = '0'+str(int(ji)+1)
            if len(s_jiplus) == 3:
              s_jiplus = s_jiplus[1:]
            s_jiminus = '0'+str(int(ji)-1)
            if len(s_jiminus) == 3:
              s_jiminus = s_jiminus[1:]
        elif getsu == '12':
          if ji == '':
            s_nenplus = nen + 1
            s_nenminus = nen
            s_getsuplus = '01'
            s_getsuminus = '11'  
            s_jiplus = '01'
            s_jiminus = '08'      
          elif ji == '01':
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = '12'
            s_getsuminus = '11'  
            s_jiplus = '02'
            s_jiminus = '08'
          elif ji == '08':
            s_nenplus = nen + 1
            s_nenminus = nen
            s_getsuplus = '01'
            s_getsuminus = '12'  
            s_jiplus = '01'
            s_jiminus = '07'
          else:
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = '12'
            s_getsuminus = '12'  
            s_jiplus = '0'+str(int(ji)+1)
            if len(s_jiplus) == 3:
              s_jiplus = s_jiplus[1:]
            s_jiminus = '0'+str(int(ji)-1)
            if len(s_jiminus) == 3:
              s_jiminus = s_jiminus[1:]        
        else:
          if ji == '':
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = '0'+str(int(getsu)+1)
            if len(s_getsuplus) == 3:
              s_getsuplus = s_getsuminus[1:]
            s_getsuminus = '0'+str(int(getsu)-1)
            if len(s_getsuminus) == 3:
              s_getsuminus = s_getsuminus[1:]      
            s_jiplus = '01'
            s_jiminus = '08'      
          elif ji == '01':
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = getsu
            s_getsuminus = '0'+str(int(getsu)-1)
            if len(s_getsuminus) == 3:
              s_getsuminus = s_getsuminus[1:]      
            s_jiplus = '02'
            s_jiminus = '08'
          elif ji == '08':
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = '0'+str(int(getsu)+1)
            if len(s_getsuplus) == 3:
              s_getsuplus = getsu
            s_getsuminus = getsu
            s_jiplus = '01'
            s_jiminus = '07'
          else:
            s_nenplus = nen
            s_nenminus = nen
            s_getsuplus = '0'+str(int(getsu)+1)
            if len(s_getsuplus) == 3:
              s_getsuplus = s_getsuminus[1:]
            s_getsuminus = '0'+str(int(getsu)-1)
            if len(s_getsuminus) == 3:
              s_getsuminus = s_getsuminus[1:]    
            s_jiplus = '0'+str(int(ji)+1)
            if len(s_jiplus) == 3:
              s_jiplus = s_jiplus[1:]
            s_jiminus = '0'+str(int(ji)-1)
            if len(s_jiminus) == 3:
              s_jiminus = s_jiminus[1:] 
     
    # 水平線
    # st.divider()  進捗確認に合わせて削除

    ##irepoDBからデータ取得
    snen = int(str(nen)[2:4])

    if getsu == '':
      sgetsu = getsu
    else:
      sgetsu = int(getsu)

    if ji == '':
      sji = ji
    else:
      sji = int(ji)
    
    #ADD_20241023分割対応
    sql = f"select top_remarks4 as 組立番号,\
            cluster_2_6_t as 機種名,\
            cluster_2_7_t as インチ,\
            cluster_2_8_t as ゲージ,\
            cluster_2_1_n as 年,\
            cluster_2_2_n as 月,\
            cluster_2_3_n as 次,\
            cluster_2_5_t as 国名出荷先,\
            cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
            cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
            cluster_2_26_t as ③針入れ等,\
            cluster_2_28_t as ④SS_WAC_ACT_取付,\
            cluster_2_30_t as ⑤RDSﾁｪｯｸ,\
            cluster_2_32_t as ⑥慣らし運転,\
            cluster_2_39_t as ⑦電気ﾁｪｯｸ,\
            cluster_2_54_t as ⑧ﾔｰﾝｷｬﾘｱ取付,\
            cluster_2_67_t as ⑨巻取装置,\
            cluster_2_71_t as ⑩幅出装置,\
            cluster_2_74_t as ⑪編成作業,\
            cluster_2_115_t as 作業者合否入力,\
            cluster_2_130_t as ⑫取付作業,\
            cluster_2_154_t as ⑬最終確認,\
            cluster_2_156_t as ⑭調整完了日時,\
            cluster_2_153_t as 最終ﾁｪｯｸ入力,\
            cluster_2_166_t as 最終承認入力\
            from view_report_393 where top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' )"
    #追加 ADD_20241111
    if c_flg == 1:
      sql += f""" or (
      (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or 
      (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}')) """
    df1 = ireporter_data_get(sql)
    sql = f"select top_remarks4 as 組立番号,\
            cluster_2_6_t as 機種名,\
            cluster_2_7_t as インチ,\
            cluster_2_8_t as ゲージ,\
            cluster_2_1_n as 年,\
            cluster_2_2_n as 月,\
            cluster_2_3_n as 次,\
            cluster_2_5_t as 国名出荷先,\
            cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
            cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
            cluster_2_26_t as ③針入れ等,\
            cluster_2_28_t as ④SS_WAC_ACT_取付,\
            cluster_2_30_t as ⑤RDSﾁｪｯｸ,\
            cluster_2_32_t as ⑥慣らし運転,\
            cluster_2_39_t as ⑦電気ﾁｪｯｸ,\
            cluster_2_54_t as ⑧ﾔｰﾝｷｬﾘｱ取付,\
            cluster_2_67_t as ⑨巻取装置,\
            cluster_2_71_t as ⑩幅出装置,\
            cluster_2_74_t as ⑪編成作業,\
            cluster_2_115_t as 作業者合否入力,\
            cluster_2_130_t as ⑫取付作業,\
            cluster_2_154_t as ⑬最終確認,\
            cluster_2_156_t as ⑭調整完了日時,\
            cluster_2_153_t as 最終ﾁｪｯｸ入力,\
            cluster_2_166_t as 最終承認入力\
            from view_report_394 where top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' )"
    #追加 ADD_20241111
    if c_flg == 1:
      sql += f""" or (
      (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or 
      (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}')) """
    df2 = ireporter_data_get(sql)

    sql = f"select top_remarks4 as 組立番号,\
            cluster_2_6_t as 機種名,\
            cluster_2_7_t as インチ,\
            cluster_2_8_t as ゲージ,\
            cluster_2_1_n as 年,\
            cluster_2_2_n as 月,\
            cluster_2_3_n as 次,\
            cluster_2_5_t as 国名出荷先,\
            cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
            cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
            cluster_2_26_t as ③針入れ等,\
            cluster_2_28_t as ④SS_WAC_ACT_取付,\
            cluster_2_30_t as ⑤RDSﾁｪｯｸ,\
            cluster_2_32_t as ⑥慣らし運転,\
            cluster_2_39_t as ⑦電気ﾁｪｯｸ,\
            cluster_2_54_t as ⑧ﾔｰﾝｷｬﾘｱ取付,\
            cluster_2_67_t as ⑨巻取装置,\
            cluster_2_71_t as ⑩幅出装置,\
            cluster_2_74_t as ⑪編成作業,\
            cluster_2_115_t as 作業者合否入力,\
            cluster_2_130_t as ⑫取付作業,\
            cluster_2_154_t as ⑬最終確認,\
            cluster_2_156_t as ⑭調整完了日時,\
            cluster_2_153_t as 最終ﾁｪｯｸ入力,\
            cluster_2_166_t as 最終承認入力\
            from view_report_395 where top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' )"
    #追加 ADD_20241111
    if c_flg == 1:
      sql += f""" or (
      (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or 
      (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}')) """
    df3 = ireporter_data_get(sql)
    sql = f"select top_remarks4 as 組立番号,\
            cluster_2_6_t as 機種名,\
            cluster_2_7_t as インチ,\
            cluster_2_8_t as ゲージ,\
            cluster_2_1_n as 年,\
            cluster_2_2_n as 月,\
            cluster_2_3_n as 次,\
            cluster_2_5_t as 国名出荷先,\
            cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
            cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
            cluster_2_26_t as ③針入れ等,\
            cluster_2_28_t as ④SS_WAC_ACT_取付,\
            cluster_2_30_t as ⑤RDSﾁｪｯｸ,\
            cluster_2_32_t as ⑥慣らし運転,\
            cluster_2_39_t as ⑦電気ﾁｪｯｸ,\
            cluster_2_54_t as ⑧ﾔｰﾝｷｬﾘｱ取付,\
            cluster_2_67_t as ⑨巻取装置,\
            cluster_2_71_t as ⑩幅出装置,\
            cluster_2_74_t as ⑪編成作業,\
            cluster_2_115_t as 作業者合否入力,\
            cluster_2_130_t as ⑫取付作業,\
            cluster_2_154_t as ⑬最終確認,\
            cluster_2_156_t as ⑭調整完了日時,\
            cluster_2_153_t as 最終ﾁｪｯｸ入力,\
            cluster_2_166_t as 最終承認入力\
            from view_report_396 where top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' )"
    #追加 ADD_20241111
    if c_flg == 1:
      sql += f""" or (
      (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or 
      (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}')) """
    df4 = ireporter_data_get(sql)

    sql = f"select top_remarks4 as 組立番号,\
            cluster_2_6_t as 機種名,\
            cluster_2_7_t as インチ,\
            cluster_2_8_t as ゲージ,\
            cluster_2_1_n as 年,\
            cluster_2_2_n as 月,\
            cluster_2_3_n as 次,\
            cluster_2_5_t as 国名出荷先,\
            cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
            cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
            cluster_2_26_t as ③針入れ等,\
            cluster_2_28_t as ④SS_WAC_ACT_取付,\
            cluster_2_30_t as ⑤RDSﾁｪｯｸ,\
            cluster_2_32_t as ⑥慣らし運転,\
            cluster_2_39_t as ⑦電気ﾁｪｯｸ,\
            cluster_2_54_t as ⑧ﾔｰﾝｷｬﾘｱ取付,\
            cluster_2_67_t as ⑨巻取装置,\
            cluster_2_71_t as ⑩幅出装置,\
            cluster_2_74_t as ⑪編成作業,\
            cluster_2_115_t as 作業者合否入力,\
            cluster_2_130_t as ⑫取付作業,\
            cluster_2_154_t as ⑬最終確認,\
            cluster_2_156_t as ⑭調整完了日時,\
            cluster_2_153_t as 最終ﾁｪｯｸ入力,\
            cluster_2_166_t as 最終承認入力\
            from view_report_397 where top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' )"
    #追加 ADD_20241111
    if c_flg == 1:
      sql += f""" or (
      (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or 
      (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}')) """
    df5 = ireporter_data_get(sql)

    sql = f"select top_remarks4 as 組立番号,\
            cluster_2_6_t as 機種名,\
            cluster_2_7_t as インチ,\
            cluster_2_8_t as ゲージ,\
            cluster_2_1_n as 年,\
            cluster_2_2_n as 月,\
            cluster_2_3_n as 次,\
            cluster_2_5_t as 国名出荷先,\
            cluster_2_11_t as ①ｶﾑﾎﾙﾀﾞｰ取付,\
            cluster_2_21_t as ②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ,\
            cluster_2_26_t as ③針入れ等,\
            cluster_2_28_t as ④SS_WAC_ACT_取付,\
            cluster_2_30_t as ⑤RDSﾁｪｯｸ,\
            cluster_2_32_t as ⑥慣らし運転,\
            cluster_2_39_t as ⑦電気ﾁｪｯｸ,\
            cluster_2_54_t as ⑧ﾔｰﾝｷｬﾘｱ取付,\
            cluster_2_67_t as ⑨巻取装置,\
            cluster_2_71_t as ⑩幅出装置,\
            cluster_2_74_t as ⑪編成作業,\
            cluster_2_115_t as 作業者合否入力,\
            cluster_2_130_t as ⑫取付作業,\
            cluster_2_154_t as ⑬最終確認,\
            cluster_2_156_t as ⑭調整完了日時,\
            cluster_2_153_t as 最終ﾁｪｯｸ入力,\
            cluster_2_166_t as 最終承認入力\
            from view_report_398 where top_remarks1 = '{snen}' and  ('{sgetsu}' = '' or top_remarks2 = '{sgetsu}' ) and ('{sji}' = '' or top_remarks3 = '{sji}' )"
    #追加 ADD_20241111
    if c_flg == 1:
      sql += f""" or (
      (top_remarks1 = '{s_nenplus}' and top_remarks2 = '{s_getsuplus}' and top_remarks3 = '{s_jiplus}') or 
      (top_remarks1 = '{s_nenminus}' and top_remarks2 = '{s_getsuminus}' and top_remarks3 = '{s_jiminus}')) """
    df6 = ireporter_data_get(sql)

    df = pd.concat([df1,df2,df3,df4,df5,df6], ignore_index=True)

    #sqlの結果が空なら抜ける
    if df.empty:
      st.write('対象月のデータがありません')
    else:
      #dataframeの加工

      #出荷先の分解　国名　　　客先名となっている
      df.insert(7, '出荷先', '')
      df.insert(7, '国名', '')
      df['国名出荷先'] = df['国名出荷先'].fillna('　　　') #Noneデータ対策
      df = df.fillna('') #Noneデータ対策
      df[['国名', '出荷先']] = df['国名出荷先'].str.split('　　　', expand=True)
      df = df.drop('国名出荷先', axis=1)
      #最終承認入力の表示変更
      #df['最終承認入力'] = df['最終承認入力'].str.replace(None, '未申請') #文字列ではないのでstrでは置き換えられない ilocでやるのが正解だが、NoneのままでOKでは？
      df['最終承認入力'] = df['最終承認入力'].str.replace('2', '申請中')
      df['最終承認入力'] = df['最終承認入力'].str.replace('4', '承認済み')
      #ソート
      df = df.sort_values(['月','次','組立番号']) #ADD_20240904sortに部番を追加

      # 処理
      #st.write('## 編機調整作業者データ') 進捗確認に合わせて削除 

      #データフレームを表示（インデックスは非表示）
      st.dataframe(df,hide_index=True)

  if __name__ == "__main__":
      main()

except Exception as e:
  #簡単なエラー処理
  st.markdown(e)
  print(e)
