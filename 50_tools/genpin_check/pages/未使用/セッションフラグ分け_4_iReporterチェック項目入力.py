import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
import streamlit_authenticator as stauth
import traceback


try:

  #krdのmachinDBに接続する
  def krd_data_get(sql):
    # #DB接続定義
    db_url = 'mysql+pymysql://pfw:mejiriHoo@krd/machin?charset=utf8'

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

  #sqlite3への接続
  def sqlite_data_get(sql,filepath):
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
  
      return(df)

  #読込処理と初期DB更新処理
  @st.cache_resource
  def db_update1():

    #checksheetdbバックアップ
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    if(os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\checksheet.db')):
      shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\checksheet.db',
                  os.path.dirname(os.path.dirname(__file__))+f'\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_checksheet.db')

    #本処理（更新処理）
    dbname = 'checksheet.db'
    cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
    #conn = sqlite3.connect(cdb,isolation_level=None) #オートコミットを削除する　これが重かった原因
    conn = sqlite3.connect(cdb)

    cur = conn.cursor()

    #■テーブル作成処理 テーブル１：工程図番
    #EXIT NOTを入れているので、テーブルがあった場合はスキップする
    cur.execute('CREATE TABLE IF NOT EXISTS kouteizuban(\
                  ID integer primary key autoincrement,\
                  完成部番 TEXT,\
                  工程Ver INTEGER,\
                  工程順 INTEGER,\
                  工程 TEXT,\
                  加工機１ TEXT,\
                  図番１ TEXT, \
                  加工機２ TEXT,\
                  図番２ TEXT,\
                  未使用flg INTEGER,\
                  UNIQUE (完成部番, 工程Ver, 工程順))\
                  ')
#                  図番 TEXT)\　#ユニークキーを設定する
#                  ')
    #■テーブル作成処理 テーブル２：図番チェック
    #EXIT NOTを入れているので、テーブルがあった場合はスキップする
    cur.execute('CREATE TABLE IF NOT EXISTS zubancheck(\
                  ID integer primary key autoincrement,\
                  連携ID INTEGER,\
                  工程順 INTEGER,\
                  工程順SUB INTEGER,\
                  図面Ver INTEGER,\
                  生産開始月 TEXT,\
                  チェック項目１ TEXT,\
                  チェック基準１ TEXT,\
                  チェック項目２ TEXT,\
                  チェック基準２ TEXT,\
                  チェック項目３ TEXT,\
                  チェック基準３ TEXT,\
                  チェック項目４ TEXT,\
                  チェック基準４ TEXT,\
                  チェック項目５ TEXT,\
                  チェック基準５ TEXT,\
                  チェック項目６ TEXT,\
                  チェック基準６ TEXT,\
                  チェック項目７ TEXT,\
                  チェック基準７ TEXT,\
                  チェック項目８ TEXT,\
                  チェック基準８ TEXT,\
                  チェック項目９ TEXT,\
                  チェック基準９ TEXT,\
                  チェック項目１０ TEXT,\
                  チェック基準１０ TEXT,\
                  チェック項目１１ TEXT,\
                  チェック基準１１ TEXT,\
                  チェック項目１２ TEXT,\
                  チェック基準１２ TEXT,\
                  チェック項目１３ TEXT,\
                  チェック基準１３ TEXT,\
                  チェック項目１４ TEXT,\
                  チェック基準１４ TEXT,\
                  チェック項目１５ TEXT,\
                  チェック基準１５ TEXT,\
                  未使用flg INTEGER,\
                  UNIQUE (連携ID,工程順SUB,図面Ver))\
                  ')
  
    #krdよりプロセスコード取得 資源と結合
    sql = "SELECT FINAL_ITEM_CODE as 完成部番,VERSION AS 工程Ver,PROCESS_CODE as 工程,PROCESS_ORDER as 工程順 , RES_CODE1 as CODE FROM DATA_RES_CAPA"
    df_expanded = krd_data_get(sql)
    #資源の取得
    sql = "SELECT CODE,NAME as 加工機１ FROM MSTR_RES"
    df_res = krd_data_get(sql)
    #加工機１を結合
    df_expanded = pd.merge(df_expanded, df_res, on=['CODE'],how='left')
    df_expanded = df_expanded.drop(columns='CODE') #CODEは削除

    #データベースを更新
    try:
      # dfの全データを一括でリストに変換
      data = [tuple(row.values.tolist()) for index, row in df_expanded.iterrows()]
      # 1000件ずつ分割して処理
      batch_size = 1000
      for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]  # 1000件ずつスライス
        cur.executemany(f'REPLACE INTO kouteizuban(完成部番,工程Ver,工程,工程順,加工機１)\
                  VALUES (?, ?, ?, ?, ?)\
                  ON CONFLICT(完成部番, 工程Ver, 工程順) DO UPDATE SET\
                  工程 = excluded.工程, \
                  加工機１ = excluded.加工機１'  , batch)
      #zubancheckは同期をとる
      cur.execute('''
          INSERT INTO zubancheck (連携ID,工程順,図面Ver,工程順SUB)
          SELECT kouteizuban.ID,kouteizuban.工程順,1,1
          FROM kouteizuban
          LEFT JOIN zubancheck ON kouteizuban.ID = zubancheck.連携ID
          WHERE zubancheck.連携ID IS NULL''')
      
      # すべての挿入が完了したらコミット
      conn.commit()
    except Exception as e:
    # エラーが発生した場合、ロールバックして変更を取り消す
      conn.rollback()
      print(e)
    finally:
    # 最後にカーソルと接続を閉じる
      cur.close()
      conn.close()

  #加工機・図番項目でのDB更新処理
  def db_update2(edit_df):
    #checksheetdbバックアップ(最短で１日１回)
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    if(os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\checksheet.db')):
      shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\checksheet.db',
                  os.path.dirname(os.path.dirname(__file__))+f'\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_checksheet.db')

    #本処理（更新処理）
    dbname = 'checksheet.db'
    cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
    #conn = sqlite3.connect(cdb,isolation_level=None) #オートコミットを削除する　これが重かった原因
    conn = sqlite3.connect(cdb)

    cur = conn.cursor()

    #df更新
    edit_df = edit_df[['加工機１','図番１','加工機２','図番２','ID']]
    #データベースを更新
    try:    # mdfの全データを一括でリストに変換
      data = [tuple(row.values.tolist()) for index, row in edit_df.iterrows()]
      # 1000件ずつ分割して処理
      batch_size = 5000
      for i in range(0, len(data), batch_size):
          batch = data[i:i+batch_size]  # 5000件ずつスライス
          cur.executemany(''' UPDATE kouteizuban
                            SET 加工機１ = ?, 図番１ = ?, 加工機２ = ?, 図番２ = ?
                            WHERE ID = ?''', batch)
      conn.commit()
    except Exception as e:
    # エラーが発生した場合、ロールバックして変更を取り消す
      conn.rollback()
    finally:
    # 最後にカーソルと接続を閉じる
      cur.close()
      conn.close()

  #チェック項目でのDB更新処理
  def db_update3(edit_df):
    
    #checksheetdbバックアップ(最短で１日１回)
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    if(os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\checksheet.db')):
      shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\checksheet.db',
                  os.path.dirname(os.path.dirname(__file__))+f'\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_checksheet.db')

    #本処理（更新処理）
    dbname = 'checksheet.db'
    cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
    #conn = sqlite3.connect(cdb,isolation_level=None) #オートコミットを削除する　これが重かった原因
    conn = sqlite3.connect(cdb)

    cur = conn.cursor()
    #アップサートデータの作成
    try:
      #zubancheckは同期をとる
      data = [tuple(row.values.tolist()) for index, row in edit_df.iterrows()]
      cur.executemany('''
          INSERT INTO zubancheck (
              連携ID, 工程順, 工程順SUB, 図面Ver, 生産開始月, チェック項目１, チェック基準１, チェック項目２, チェック基準２,
              チェック項目３, チェック基準３, チェック項目４, チェック基準４, チェック項目５, チェック基準５,
              チェック項目６, チェック基準６, チェック項目７, チェック基準７, チェック項目８, チェック基準８,
              チェック項目９, チェック基準９,チェック項目１０, チェック基準１０, チェック項目１１, チェック基準１１,
              チェック項目１２, チェック基準１２, チェック項目１３, チェック基準１３, チェック項目１４, チェック基準１４,
              チェック項目１５, チェック基準１５
          )
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          ON CONFLICT(連携ID, 工程順SUB, 図面Ver) 
          DO UPDATE SET
              連携ID = excluded.連携ID,
              図面Ver = excluded.図面Ver,
              工程順SUB = excluded.工程順SUB,
              生産開始月 = excluded.生産開始月,
              チェック項目１ = excluded.チェック項目１,
              チェック基準１ = excluded.チェック基準１,
              チェック項目２ = excluded.チェック項目２,
              チェック基準２ = excluded.チェック基準２,
              チェック項目３ = excluded.チェック項目３,
              チェック基準３ = excluded.チェック基準３,
              チェック項目４ = excluded.チェック項目４,
              チェック基準４ = excluded.チェック基準４,
              チェック項目５ = excluded.チェック項目５,
              チェック基準５ = excluded.チェック基準５,
              チェック項目６ = excluded.チェック項目６,
              チェック基準６ = excluded.チェック基準６,
              チェック項目７ = excluded.チェック項目７,
              チェック基準７ = excluded.チェック基準７,
              チェック項目８ = excluded.チェック項目８,
              チェック基準８ = excluded.チェック基準８,
              チェック項目９ = excluded.チェック項目９,
              チェック基準９ = excluded.チェック基準９,
              チェック項目１０ = excluded.チェック項目１０,
              チェック基準１０ = excluded.チェック基準１０,
              チェック項目１１ = excluded.チェック項目１１,
              チェック基準１１ = excluded.チェック基準１１,
              チェック項目１２ = excluded.チェック項目１２,
              チェック基準１２ = excluded.チェック基準１２,
              チェック項目１３ = excluded.チェック項目１３,
              チェック基準１３ = excluded.チェック基準１３,
              チェック項目１４ = excluded.チェック項目１４,
              チェック基準１４ = excluded.チェック基準１４,
              チェック項目１５ = excluded.チェック項目１５,
              チェック基準１５ = excluded.チェック基準１５
            ''', data)
      # すべての挿入が完了したらコミット
      conn.commit()
    except Exception as e:
    # エラーが発生した場合、ロールバックして変更を取り消す
      conn.rollback()
      print(e)
    finally:
    # 最後にカーソルと接続を閉じる
      cur.close()
      conn.close()
  def db_update4(edit_df):
    
      #更新処理）
      dbname = 'genpinhyo.db'
      cdb =  os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
      conn = sqlite3.connect(cdb)
      cur = conn.cursor()

      #df更新
      edit_df = edit_df[['ireporter管理flg','QRコードレイアウト区分','縦横区分','部品名']]
      #データベースを更新
      try:    # mdfの全データを一括でリストに変換
        data = [tuple(row.values.tolist()) for index, row in edit_df.iterrows()]
        cur.executemany(''' UPDATE buhin_irepo_mst
                        SET ireporter管理flg = ?, QRコードレイアウト区分 = ?, 縦横区分 = ?
                        WHERE 部品名 = ?''', data)
        conn.commit()
      except Exception as e:
      # エラーが発生した場合、ロールバックして変更を取り消す
        conn.rollback()
      finally:
      # 最後にカーソルと接続を閉じる
        cur.close()
        conn.close()
   


# セレクトボックス1が変更されたときに他のボックスをリセットする関数
  def reset_select2():
    del st.session_state["innum2"]
  def reset_select3(nen):
    if "select3" in st.session_state:
      del st.session_state["select3"]
    if 'select3' not in st.session_state:
      st.session_state.select3 = nen
    if "select3_a" in st.session_state:
      del st.session_state["select3_a"]
    if 'select3_a' not in st.session_state:
      st.session_state.select3_a = nen
  def reset_select4(getsu):
    if "select4" in st.session_state:
      del st.session_state["select4"]
    if 'select4' not in st.session_state:
      st.session_state.select4 = getsu
    if "select4_a" in st.session_state:
      del st.session_state["select4_a"]
    if 'select4_a' not in st.session_state:
      st.session_state.select4_a = getsu
  def change_kirikae_flg(kirikae_flg):
    if kirikae_flg == 0:
      st.session_state.kirikae_flg = 1
    else:
      st.session_state.kirikae_flg = 0
    

  def main():
    # # セレクトボックスの初期値をセッションステートで管理
    if 'select1' not in st.session_state:
      st.session_state.select1 = ''
    if 'innum2' not in st.session_state:
      st.session_state.innum2 = 1
    if 'select3' not in st.session_state:
      st.session_state.select3 = ''
    if 'select4' not in st.session_state:
      st.session_state.select4 = ''
    if 'innum2_a' not in st.session_state:
      st.session_state.innum2_a = 1
    if 'select3_a' not in st.session_state:
      st.session_state.select3_a = ''
    if 'select4_a' not in st.session_state:
      st.session_state.select4_a = ''
    if 'kirikae_flg' not in st.session_state:
      st.session_state.kirikae_flg = 0

    st.set_page_config(
    page_title = 'i-Reporterチェック項目入力',
      layout="wide" )
    HIDE_ST_STYLE = """
    <style>
        div[data-testid="stToolbar"] {
            visibility: hidden;
            height: 0px;
            position: fixed;
        }
        div[data-testid="stDecoration"] {
            visibility: hidden;
            height: 0px;
            position: fixed;
        }
        #MainMenu {
            visibility: hidden;
        }
        header {
            visibility: hidden;
            height: 0px;
            position: fixed;
        }
        footer {
            visibility: hidden;
            height: 0px;
            position: fixed;
        }
        .appview-container .main .block-container {
            padding-top: 1rem;
            padding-right: 3rem;
            padding-left: 3rem;
            padding-bottom: 1rem;
        }
        .reportview-container {
            padding-top: 0px;
            padding-right: 3rem;
            padding-left: 3rem;
            padding-bottom: 0px;
        }
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }
        header[data-testid="stHeader"] {
            display: none;
        }
        div[data-testid="stToolbar"] {
            z-index: 100;
        }
        div[data-testid="stDecoration"] {
            z-index: 100;
        }
    </style>
    """
    st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)
    
     
    # 認証パスワード
    PASSWORD = "pfwpass"

    # セッション状態を利用して認証状態を保持
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False


    # 認証されていない場合、パスワード入力フィールドを表示
    if not st.session_state.authenticated:
        st.markdown("# i-Reporter_チェック登録")
        password = st.text_input("パスワードを入力してください", type="password")
        if st.button("ログイン"):
            if password == PASSWORD:
                st.session_state.authenticated = True
                st.success("認証OK！　もう一度ログインボタンを押下してログインしてください")
            else:
                st.error("パスワードが間違っています")
    else:
        # 認証済みの場合、メインコンテンツを表示
        main_page()
        # 水平線
        st.divider()
        # ログアウトボタン
        if st.button("ログアウト"):
            st.session_state.authenticated = False


  def main_page():

    # 全読込み
    db_update1() #まずは更新
    file = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+'checksheet.db'
    sql = 'select * from kouteizuban'
    df_kouteizuban = sqlite_data_get(sql,file)
    sql = 'select * from zubancheck'
    df_zubancheck = sqlite_data_get(sql,file)
    df_kouteizuban = df_kouteizuban.fillna('なし') #Noneデータ対策　なしにもバージョンを付けるので、なしと表記
    df_kouteizuban = df_kouteizuban.drop(columns='未使用flg') #今は削除
    df_zubancheck['図面Ver'] = df_zubancheck['図面Ver'].fillna(1) #Noneデータ対策　なしにもバージョンを付けるので、なしと表記
    df_zubancheck = df_zubancheck.fillna('なし') #Noneデータ対策　なしにもバージョンを付けるので、なしと表記
    df_zubancheck = df_zubancheck.drop(columns='未使用flg') #今は削除
    
    #空のデータフレームを一旦仮作成
    check_df = pd.DataFrame(columns=['完成部番','工程Ver']) 
    check_df.loc[0]=["",""]

    # タブを作成
    tab_titles = ['加工機・図番　登録', 'チェックシート項目　登録', 'チェックシートイメージの表示','i-Reporter発行対象管理']
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)
    
    with tab1:      
    #colh1,colh2= st.columns([1,1])
    #with colh1:      
      st.markdown("##### 加工機・図番　登録")
      col1,col2,col3,col4= st.columns([1,1,0.5,1])
      with col1:
        buban = st.text_input("完成部番",'')
      with col2:
        st.write("")
        st.write("")
        syubetsu = st.radio("検索", ("前方一致", "部分一致"), horizontal=True,label_visibility="collapsed")
        #完成部番
        if syubetsu == "前方一致":
          df_kouteizuban = df_kouteizuban[df_kouteizuban['完成部番'].str.startswith(buban)]
        elif syubetsu == "部分一致":
          df_kouteizuban = df_kouteizuban[df_kouteizuban['完成部番'].str.contains(buban)]
      with col3:
        v_values = df_kouteizuban['工程Ver'].value_counts()[df_kouteizuban['工程Ver'].value_counts() > 1].index.tolist()
        v_values.sort()
        v_values.insert(0, "")
        kouteiv = st.selectbox('工程Ver',v_values)
        #工程VERSIORN
        if kouteiv != "":
          df_kouteizuban = df_kouteizuban[df_kouteizuban['工程Ver']==kouteiv]
      
      df_kouteizuban = df_kouteizuban.sort_values(['完成部番','工程Ver','工程順'])
      # '完成部番' カラムがNoneまたは空欄の行を削除する
      df_kouteizuban = df_kouteizuban.dropna(subset=['完成部番']).replace('', float('NaN')).dropna(subset=['完成部番'])
      edited_df = st.data_editor(df_kouteizuban.drop(columns='ID'),hide_index=True,
                                    column_config={
                                      '加工機１': {'width': 130},
                                      '図番１': {'width': 150}, 
                                      '加工機２': {'width': 130},
                                      '図番２': {'width': 150}
                                      },disabled=["ID", "完成部番","工程Ver","工程順","工程","加工機１"]) # 
      
      df_kouteizuban = df_kouteizuban.drop(columns=['加工機１','図番１','加工機２','図番２'])

      #編集後dfにIDを復活させる
      df_kouteizuban = pd.merge(df_kouteizuban, edited_df, on=['完成部番','工程Ver','工程順','工程'],how='left')
      #加工機と図番を２段にして、リネーム　加工機２と図番２は両方ともなしならドロップ
      df_kouteizuban1 = df_kouteizuban[['ID','完成部番','工程Ver','工程順','工程','加工機１','図番１']]
      df_kouteizuban1 = df_kouteizuban1.rename(columns={'加工機１': '加工機','図番１': '図番',})
      df_kouteizuban2 = df_kouteizuban[['ID','完成部番','工程Ver','工程順','工程','加工機２','図番２']]
      df_kouteizuban2 = df_kouteizuban2.rename(columns={'加工機２': '加工機','図番２': '図番',})
      df_kouteizuban2 = df_kouteizuban2[~((df_kouteizuban2['加工機'] == 'なし') & (df_kouteizuban2['図番'] == 'なし'))]
      #復活したIDを元に図番チェックテーブルと結合df IDと工程順でsort （不要？）
      df_zubancheck = df_zubancheck.rename(columns={'ID': 'CID'})
      df_zubancheck = df_zubancheck.drop(columns=['工程順'])
      df_zubancheck1 = df_zubancheck[df_zubancheck['工程順SUB'] == 1]
      merged_df1 = pd.merge(df_kouteizuban1, df_zubancheck1, left_on=['ID'],right_on=['連携ID'],how='left')
      #df_zubancheck2 = df_zubancheck[(df_zubancheck['工程順SUB'] == 2) | (df_zubancheck['工程順SUB'].isnull())]
      df_zubancheck2 = df_zubancheck[df_zubancheck['工程順SUB'] == 2]
      #工程順SUB2と結びつかいないデータ（新規に工程順2が登録されたデータ）への対応
      merged_df2 = pd.merge(df_kouteizuban2, df_zubancheck2, left_on=['ID'],right_on=['連携ID'],how='left')
      merged_df3 = pd.concat([merged_df1,merged_df2], ignore_index=True)
      merged_df3 = merged_df3.sort_values(['ID','工程順']) 
      merged_df3.loc[merged_df3['工程順SUB'].isnull(),'工程順SUB'] = 2
      merged_df3.loc[merged_df3['図面Ver'].isnull(),'図面Ver'] = 1
      merged_df3.loc[merged_df3['生産開始月'].isnull(),'生産開始月'] = 'なし'
      merged_df3.loc[merged_df3['連携ID'].isnull(),'連携ID'] = merged_df3['連携ID'].shift(1)
      merged_df3 = merged_df3.fillna('なし') 
      
      #merged_df3['工程順'] = merged_df3.groupby(['完成部番','工程Ver']).cumcount() + 1 #工程順ふり直し
      merged_df3 = merged_df3.sort_values(['完成部番','工程Ver','工程順','図面Ver']) 
      merged_df3['工程順SUB'] = merged_df3.groupby(['完成部番','工程Ver','工程順','工程','図面Ver']).cumcount() + 1 
      #生産開始月が入っている図面バージョン最新+1
      merged_df3['図番選択'] = merged_df3['図番']+'　【'+merged_df3['完成部番']+'　工程：'+merged_df3['工程']+'　工程順：'+merged_df3['工程順'].astype(str)+'　加工機：'+merged_df3['加工機']+'　工程Ver：'+merged_df3['工程Ver'].astype(str)+'】'
      zubansentaku_values = merged_df3['図番選択'].tolist()
      zubansentaku_values= list(dict.fromkeys(zubansentaku_values)) #重複削除　merged_df3は図番が増えたときは重複してしまうため
      zubansentaku_values.insert(0, "")
      if st.button("加工機・図番更新"):
        db_update2(df_kouteizuban) 
    with tab2:  #★
    #with colh2:  #★
      st.markdown("##### チェックシート項目　登録")
      #図番を選択
      zumensentakuv = st.selectbox('図番選択',zubansentaku_values,key='select1')
      merged_df4 = merged_df3[merged_df3['図番選択']==zumensentakuv]
      if not merged_df4.empty:
        update_df = merged_df3[merged_df3['完成部番']==merged_df4['完成部番'].iloc[0]] #更新用dataframeはここで取得しておく
        #check_df = update_df
        check_df = merged_df4
        zubanversion_values = merged_df4['図面Ver'].tolist()
      else:
        zubanversion_values=[1,1]
      col1,col2,col3= st.columns([1,1,1])
      # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
      dt_now = datetime.now(timezone(timedelta(hours=9)))+ timedelta(days=32) # 日本時刻+32日
      dt_nen = int(dt_now.strftime('%Y'))
      
      #切り替えフラグで管理
      #※セッション管理がうまく出来なかったため、更新ボタンが押されるたびに同じ画面を切り替えるようにして回避
      if st.session_state.kirikae_flg == 0:
        with col1:
          #選択した行から図面バージョンを抽出して編集
          zumenv = 0
          zumenv = st.number_input(f'図面Ver選択　※最新：{str(int(zubanversion_values[-1]))}', min_value=1, max_value=99,value=int(zubanversion_values[-1]) ,step=1,key='innum2')

          if not merged_df4.empty:
            production_start_month = merged_df4.loc[merged_df4['図面Ver'] == zumenv, '生産開始月'].values
          else:
            production_start_month = 'なし'
        with col2:
          nen_list = ["",str(dt_nen+1),str(dt_nen),str(dt_nen-1),str(dt_nen-2),str(dt_nen-3),str(dt_nen-4),str(dt_nen-5),str(dt_nen-6),str(dt_nen-7),str(dt_nen-8),str(dt_nen-9),str(dt_nen-10)]
          if merged_df4.empty or len(production_start_month) == 0 or production_start_month[0] == 'なし' or production_start_month[0] == '年月より':
            nen = st.selectbox('図面適用生産開始年',nen_list,index=0,key='select3')
            reset_select3(nen)
          else:
            dfnen = production_start_month[0][0:4]
            nen = st.selectbox('図面適用生産開始年',nen_list,index=nen_list.index(dfnen),key='select3')
        with col3:
          tuki_list = ["",'01','02','03','04','05','06','07','08','09','10','11','12']
          if merged_df4.empty or len(production_start_month) == 0 or production_start_month[0] == 'なし' or production_start_month[0] == '年月より':
            getsu = st.selectbox('図面適用生産計画月',tuki_list,index=0,key='select4')
            reset_select4(getsu)
          else:
            dfgetsu = production_start_month[0][-5:-3] if production_start_month[0][-5:-3] in tuki_list else ""
            getsu = st.selectbox('図面適用生産計画月',tuki_list,index=tuki_list.index(str(dfgetsu)),key='select4')
        if not merged_df4.empty:
          kouteijun = merged_df4['工程順'].iloc[0]
          kouteijun_sub = merged_df4['工程順SUB'].iloc[0]
        else:
          kouteijun = 1
      else:
        with col1:
          #選択した行から図面バージョンを抽出して編集
          zumenv = 0
          zumenv = st.number_input(f'図面Ver選択　※最新：{str(int(zubanversion_values[-1]))}', min_value=1, max_value=99,value=int(zubanversion_values[-1]) ,step=1,key='innum2_a')

          if not merged_df4.empty:
            production_start_month = merged_df4.loc[merged_df4['図面Ver'] == zumenv, '生産開始月'].values
          else:
            production_start_month = 'なし'
        with col2:
          nen_list = ["",str(dt_nen+1),str(dt_nen),str(dt_nen-1),str(dt_nen-2),str(dt_nen-3),str(dt_nen-4),str(dt_nen-5),str(dt_nen-6),str(dt_nen-7),str(dt_nen-8),str(dt_nen-9),str(dt_nen-10)]
          if merged_df4.empty or len(production_start_month) == 0 or production_start_month[0] == 'なし' or production_start_month[0] == '年月より':
            nen = st.selectbox('図面適用生産開始年',nen_list,index=0,key='select3_a')
            reset_select3(nen)
          else:
            dfnen = production_start_month[0][0:4]
            nen = st.selectbox('図面適用生産開始年',nen_list,index=nen_list.index(dfnen),key='select3_a')
        with col3:
          tuki_list = ["",'01','02','03','04','05','06','07','08','09','10','11','12']
          if merged_df4.empty or len(production_start_month) == 0 or production_start_month[0] == 'なし' or production_start_month[0] == '年月より':
            getsu = st.selectbox('図面適用生産計画月',tuki_list,index=0,key='select4_a')
            reset_select4(getsu)
          else:
            dfgetsu = production_start_month[0][-5:-3] if production_start_month[0][-5:-3] in tuki_list else ""
            getsu = st.selectbox('図面適用生産計画月',tuki_list,index=tuki_list.index(str(dfgetsu)),key='select4_a')
        if not merged_df4.empty:
          kouteijun = merged_df4['工程順'].iloc[0]
          kouteijun_sub = merged_df4['工程順SUB'].iloc[0]
        else:
          kouteijun = 1
      nengetsu = f'{nen}年{getsu}月より'
      if zumensentakuv != "" and str(zumenv) !="":
        #図面verで取得
        if not merged_df4.empty: #セッション管理のため、物理的に切り替える
          merged_df5 = merged_df4[merged_df4['図面Ver'] == zumenv]
          if merged_df5.empty:
            #空なら新規採番
            data ={
              'CID':[],'連携ID':[],'工程順':[],'工程順SUB':[],'図面Ver':[],'生産開始月':[],'チェック項目１':[],'チェック基準１':[],'チェック項目２':[],'チェック基準２':[],
              'チェック項目３':[],'チェック基準３':[],'チェック項目４':[],'チェック基準４':[],'チェック項目５':[],'チェック基準５':[],
              'チェック項目６':[],'チェック基準６':[],'チェック項目７':[],'チェック基準７':[],'チェック項目８':[],'チェック基準８':[],
              'チェック項目９':[],'チェック基準９':[],'チェック項目１０':[],'チェック基準１０':[],'チェック項目１１':[],'チェック基準１１':[],
              'チェック項目１２':[],'チェック基準１２':[],'チェック項目１３':[],'チェック基準１３':[],'チェック項目１４':[],'チェック基準１４':[],
              'チェック項目１５':[],'チェック基準１５':[]
            }
            new_df = pd.DataFrame(data)
            new_df['連携ID'] = merged_df4['連携ID']
            new_df['図面Ver'] = zumenv
            new_df['生産開始月'] = nengetsu
            new_df = new_df.fillna('なし') #Noneデータ対策　なしにもバージョンを付けるので、なしと表記
            df_zubancheck1 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１','チェック基準１']].rename(columns={'チェック項目１': 'チェック項目','チェック基準１': 'チェック基準'})
            df_zubancheck2 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目２','チェック基準２']].rename(columns={'チェック項目２': 'チェック項目','チェック基準２': 'チェック基準'})
            df_zubancheck3 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目３','チェック基準３']].rename(columns={'チェック項目３': 'チェック項目','チェック基準３': 'チェック基準'})
            df_zubancheck4 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目４','チェック基準４']].rename(columns={'チェック項目４': 'チェック項目','チェック基準４': 'チェック基準'})
            df_zubancheck5 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目５','チェック基準５']].rename(columns={'チェック項目５': 'チェック項目','チェック基準５': 'チェック基準'})
            df_zubancheck6 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目６','チェック基準６']].rename(columns={'チェック項目６': 'チェック項目','チェック基準６': 'チェック基準'})
            df_zubancheck7 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目７','チェック基準７']].rename(columns={'チェック項目７': 'チェック項目','チェック基準７': 'チェック基準'})
            df_zubancheck8 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目８','チェック基準８']].rename(columns={'チェック項目８': 'チェック項目','チェック基準８': 'チェック基準'})
            df_zubancheck9 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目９','チェック基準９']].rename(columns={'チェック項目９': 'チェック項目','チェック基準９': 'チェック基準'})
            df_zubancheck10 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１０','チェック基準１０']].rename(columns={'チェック項目１０': 'チェック項目','チェック基準１０': 'チェック基準'})
            df_zubancheck11 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１１','チェック基準１１']].rename(columns={'チェック項目１１': 'チェック項目','チェック基準１１': 'チェック基準'})
            df_zubancheck12 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１２','チェック基準１２']].rename(columns={'チェック項目１２': 'チェック項目','チェック基準１２': 'チェック基準'})
            df_zubancheck13 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１３','チェック基準１３']].rename(columns={'チェック項目１３': 'チェック項目','チェック基準１３': 'チェック基準'})
            df_zubancheck14 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１４','チェック基準１４']].rename(columns={'チェック項目１４': 'チェック項目','チェック基準１４': 'チェック基準'})
            df_zubancheck15 = new_df[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１５','チェック基準１５']].rename(columns={'チェック項目１５': 'チェック項目','チェック基準１５': 'チェック基準'})
          else:
            df_zubancheck1 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１','チェック基準１']].rename(columns={'チェック項目１': 'チェック項目','チェック基準１': 'チェック基準'})
            df_zubancheck2 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目２','チェック基準２']].rename(columns={'チェック項目２': 'チェック項目','チェック基準２': 'チェック基準'})
            df_zubancheck3 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目３','チェック基準３']].rename(columns={'チェック項目３': 'チェック項目','チェック基準３': 'チェック基準'})
            df_zubancheck4 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目４','チェック基準４']].rename(columns={'チェック項目４': 'チェック項目','チェック基準４': 'チェック基準'})
            df_zubancheck5 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目５','チェック基準５']].rename(columns={'チェック項目５': 'チェック項目','チェック基準５': 'チェック基準'})
            df_zubancheck6 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目６','チェック基準６']].rename(columns={'チェック項目６': 'チェック項目','チェック基準６': 'チェック基準'})
            df_zubancheck7 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目７','チェック基準７']].rename(columns={'チェック項目７': 'チェック項目','チェック基準７': 'チェック基準'})
            df_zubancheck8 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目８','チェック基準８']].rename(columns={'チェック項目８': 'チェック項目','チェック基準８': 'チェック基準'})
            df_zubancheck9 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目９','チェック基準９']].rename(columns={'チェック項目９': 'チェック項目','チェック基準９': 'チェック基準'})
            df_zubancheck10 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１０','チェック基準１０']].rename(columns={'チェック項目１０': 'チェック項目','チェック基準１０': 'チェック基準'})
            df_zubancheck11 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１１','チェック基準１１']].rename(columns={'チェック項目１１': 'チェック項目','チェック基準１１': 'チェック基準'})
            df_zubancheck12 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１２','チェック基準１２']].rename(columns={'チェック項目１２': 'チェック項目','チェック基準１２': 'チェック基準'})
            df_zubancheck13 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１３','チェック基準１３']].rename(columns={'チェック項目１３': 'チェック項目','チェック基準１３': 'チェック基準'})
            df_zubancheck14 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１４','チェック基準１４']].rename(columns={'チェック項目１４': 'チェック項目','チェック基準１４': 'チェック基準'})
            df_zubancheck15 = merged_df5[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１５','チェック基準１５']].rename(columns={'チェック項目１５': 'チェック項目','チェック基準１５': 'チェック基準'})
          #物理セッション分け
          if st.session_state.kirikae_flg == 0:
            merged_zubancheckdf1 = pd.concat([df_zubancheck1,df_zubancheck2,df_zubancheck3,df_zubancheck4,df_zubancheck5,
                                      df_zubancheck6,df_zubancheck7,df_zubancheck8,df_zubancheck9,df_zubancheck10,
                                      df_zubancheck11,df_zubancheck12,df_zubancheck13,df_zubancheck14,df_zubancheck15], ignore_index=True)
            edited_merged_zubancheckdf = st.data_editor(merged_zubancheckdf1.drop(columns=['CID','連携ID','図面Ver','生産開始月','工程順','工程順SUB']),
                                      column_config={
                                      'チェック項目': {'width': 300}, 
                                      'チェック基準': {'width': 301},
                                      })
          else:
            merged_zubancheckdf2 = pd.concat([df_zubancheck1,df_zubancheck2,df_zubancheck3,df_zubancheck4,df_zubancheck5,
                                      df_zubancheck6,df_zubancheck7,df_zubancheck8,df_zubancheck9,df_zubancheck10,
                                      df_zubancheck11,df_zubancheck12,df_zubancheck13,df_zubancheck14,df_zubancheck15], ignore_index=True)
            edited_merged_zubancheckdf = st.data_editor(merged_zubancheckdf2.drop(columns=['CID','連携ID','図面Ver','生産開始月','工程順','工程順SUB']),
                                    column_config={
                                      'チェック項目': {'width': 301}, 
                                      'チェック基準': {'width': 300},
                                      })
          if st.button("チェック項目更新"):
            if nen == "" or getsu == "":
              st.write("図面適用生産開始年と図面適用生産開始月は入力必須です！")
            else:
              #update用データの作成 力技での実装
              if st.session_state.kirikae_flg == 0:
                merged_zubancheckdf1 = merged_zubancheckdf1.drop(columns=['チェック項目', 'チェック基準'])
                edited_df2 = merged_zubancheckdf1.join(edited_merged_zubancheckdf)
              else:
                merged_zubancheckdf2 = merged_zubancheckdf2.drop(columns=['チェック項目', 'チェック基準'])
                edited_df2 = merged_zubancheckdf2.join(edited_merged_zubancheckdf)

              edited_df2['生産開始月'] = nengetsu
              edited_df2['工程順'] = kouteijun
              edited_df2['工程順SUB'] = kouteijun_sub
              edited_df2['チェック項目１'] = edited_df2['チェック項目'].iloc[0]
              edited_df2['チェック基準１'] = edited_df2['チェック基準'].iloc[0]
              edited_df2['チェック項目２'] = edited_df2['チェック項目'].iloc[1]
              edited_df2['チェック基準２'] = edited_df2['チェック基準'].iloc[1]
              edited_df2['チェック項目３'] = edited_df2['チェック項目'].iloc[2]
              edited_df2['チェック基準３'] = edited_df2['チェック基準'].iloc[2]
              edited_df2['チェック項目４'] = edited_df2['チェック項目'].iloc[3]
              edited_df2['チェック基準４'] = edited_df2['チェック基準'].iloc[3]
              edited_df2['チェック項目５'] = edited_df2['チェック項目'].iloc[4]
              edited_df2['チェック基準５'] = edited_df2['チェック基準'].iloc[4]
              edited_df2['チェック項目６'] = edited_df2['チェック項目'].iloc[5]
              edited_df2['チェック基準６'] = edited_df2['チェック基準'].iloc[5]
              edited_df2['チェック項目７'] = edited_df2['チェック項目'].iloc[6]
              edited_df2['チェック基準７'] = edited_df2['チェック基準'].iloc[6]
              edited_df2['チェック項目８'] = edited_df2['チェック項目'].iloc[7]
              edited_df2['チェック基準８'] = edited_df2['チェック基準'].iloc[7]
              edited_df2['チェック項目９'] = edited_df2['チェック項目'].iloc[8]
              edited_df2['チェック基準９'] = edited_df2['チェック基準'].iloc[8]
              edited_df2['チェック項目１０'] = edited_df2['チェック項目'].iloc[9]
              edited_df2['チェック基準１０'] = edited_df2['チェック基準'].iloc[9]
              edited_df2['チェック項目１１'] = edited_df2['チェック項目'].iloc[10]
              edited_df2['チェック基準１１'] = edited_df2['チェック基準'].iloc[10]
              edited_df2['チェック項目１２'] = edited_df2['チェック項目'].iloc[11]
              edited_df2['チェック基準１２'] = edited_df2['チェック基準'].iloc[11]
              edited_df2['チェック項目１３'] = edited_df2['チェック項目'].iloc[12]
              edited_df2['チェック基準１３'] = edited_df2['チェック基準'].iloc[12]
              edited_df2['チェック項目１４'] = edited_df2['チェック項目'].iloc[13]
              edited_df2['チェック基準１４'] = edited_df2['チェック基準'].iloc[13]
              edited_df2['チェック項目１５'] = edited_df2['チェック項目'].iloc[14]
              edited_df2['チェック基準１５'] = edited_df2['チェック基準'].iloc[14]          
              edited_df2 = edited_df2.drop(columns=['CID','チェック項目', 'チェック基準']).head(1)
              update_df = update_df[['連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１','チェック基準１','チェック項目２','チェック基準２',
                  'チェック項目３','チェック基準３','チェック項目４','チェック基準４','チェック項目５','チェック基準５',
                  'チェック項目６','チェック基準６','チェック項目７','チェック基準７','チェック項目８','チェック基準８',
                  'チェック項目９','チェック基準９','チェック項目１０','チェック基準１０','チェック項目１１','チェック基準１１',
                  'チェック項目１２','チェック基準１２','チェック項目１３','チェック基準１３','チェック項目１４','チェック基準１４',
                  'チェック項目１５','チェック基準１５']]
              update_df = update_df.merge(edited_df2[['連携ID', '工程順','工程順SUB', '図面Ver']], on=['連携ID', '工程順','工程順SUB', '図面Ver'], how='left', indicator=True)
              update_df = update_df[update_df['_merge'] == 'left_only'].drop(columns=['_merge'])
              update_df = pd.concat([update_df,edited_df2], ignore_index=True)
              st.cache_resource.clear()
              db_update2(df_kouteizuban) #加工機も更新する（矛盾データを作らないため）
              db_update3(update_df)
              change_kirikae_flg(st.session_state.kirikae_flg)
              st.session_state.clear()
              st.write("更新完了")
      else:
        st.write("図番と図面Verを選択してください")

    # 水平線
    #st.divider()
    with tab3:

      #空のデータフレームを作成
      st.markdown("##### チェックシートイメージの表示")
      df = pd.DataFrame(columns=['工程','加工機','図番','図面Ver','チェック項目','チェック基準','生産開始月'])
      df.loc[0]=["無し","登録なし","登録無し","","","",""]
      buban = check_df['完成部番'].iloc[0]
      kouteiver = check_df['工程Ver'].iloc[0]

      if buban != "" and kouteiver != "":
        file = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+'checksheet.db'
        sql1 = f'select * from kouteizuban where 完成部番 = "{buban}"and 工程Ver = "{kouteiver}"'
        df1 = sqlite_data_get(sql1,file)
        sql2 = f'select * from zubancheck'
        df2 = sqlite_data_get(sql2,file)

        #空チェック
        if df1.empty or df2.empty:
          df.loc[0]=["無し","登録なし","登録無し","","","",""]
        else:
            #kouteizubanテーブル
          df1_1 = df1[['ID','完成部番','工程Ver','工程順','工程','加工機１','図番１']]
          df1_1 = df1_1.rename(columns={'加工機１': '加工機','図番１': '図番',})
          df1_2 = df1[['ID','完成部番','工程Ver','工程順','工程','加工機２','図番２']]
          df1_2 = df1_2.rename(columns={'加工機２': '加工機','図番２': '図番',})
          df1_2 = df1_2[~((df1_2['加工機'] == 'なし') & (df1_2['図番'] == 'なし'))]

          #zubancheckテーブル
          df2 = df2.rename(columns={'ID': 'CID'})
          df2 = df2.drop(columns=['工程順'])
          df2_1 = df2[df2['工程順SUB'] == 1]
          merged_df1 = pd.merge(df1_1, df2_1, left_on=['ID'],right_on=['連携ID'],how='left')

          df2_2 = df2[df2['工程順SUB'] == 2]
          merged_df2 = pd.merge(df1_2, df2_2, left_on=['ID'],right_on=['連携ID'],how='left')
          merged_df3 = pd.concat([merged_df1,merged_df2], ignore_index=True)
          merged_df3 = merged_df3.sort_values(['ID','工程順'])
          merged_df3['図面Ver'] = merged_df3['図面Ver'].astype(str) #ここで変換しておくとfloatにならない
          
          #最新の図面Verのデータを抽出
          merged_df4 = merged_df3.loc[merged_df3.groupby(['工程順', '工程順SUB'])['図面Ver'].idxmax()]

          #分解
          df_zubancheck1 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１','チェック基準１']].rename(columns={'チェック項目１': 'チェック項目','チェック基準１': 'チェック基準'})
          df_zubancheck2 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目２','チェック基準２']].rename(columns={'チェック項目２': 'チェック項目','チェック基準２': 'チェック基準'})
          df_zubancheck3 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目３','チェック基準３']].rename(columns={'チェック項目３': 'チェック項目','チェック基準３': 'チェック基準'})
          df_zubancheck4 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目４','チェック基準４']].rename(columns={'チェック項目４': 'チェック項目','チェック基準４': 'チェック基準'})
          df_zubancheck5 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目５','チェック基準５']].rename(columns={'チェック項目５': 'チェック項目','チェック基準５': 'チェック基準'})
          df_zubancheck6 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目６','チェック基準６']].rename(columns={'チェック項目６': 'チェック項目','チェック基準６': 'チェック基準'})
          df_zubancheck7 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目７','チェック基準７']].rename(columns={'チェック項目７': 'チェック項目','チェック基準７': 'チェック基準'})
          df_zubancheck8 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目８','チェック基準８']].rename(columns={'チェック項目８': 'チェック項目','チェック基準８': 'チェック基準'})
          df_zubancheck9 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目９','チェック基準９']].rename(columns={'チェック項目９': 'チェック項目','チェック基準９': 'チェック基準'})
          df_zubancheck10 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１０','チェック基準１０']].rename(columns={'チェック項目１０': 'チェック項目','チェック基準１０': 'チェック基準'})
          df_zubancheck11 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１１','チェック基準１１']].rename(columns={'チェック項目１１': 'チェック項目','チェック基準１１': 'チェック基準'})
          df_zubancheck12 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１２','チェック基準１２']].rename(columns={'チェック項目１２': 'チェック項目','チェック基準１２': 'チェック基準'})
          df_zubancheck13 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１３','チェック基準１３']].rename(columns={'チェック項目１３': 'チェック項目','チェック基準１３': 'チェック基準'})
          df_zubancheck14 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１４','チェック基準１４']].rename(columns={'チェック項目１４': 'チェック項目','チェック基準１４': 'チェック基準'})
          df_zubancheck15 = merged_df4[['CID','連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１５','チェック基準１５']].rename(columns={'チェック項目１５': 'チェック項目','チェック基準１５': 'チェック基準'})
  
          merged_df5 = pd.concat([df_zubancheck1,df_zubancheck2,df_zubancheck3,df_zubancheck4,df_zubancheck5,
                                  df_zubancheck6,df_zubancheck7,df_zubancheck8,df_zubancheck9,df_zubancheck10,
                                  df_zubancheck11,df_zubancheck12,df_zubancheck13,df_zubancheck14,df_zubancheck15], ignore_index=True)

          #並び替え、チェック入力のない項目は削除
          merged_df5 = merged_df5.sort_values(['工程順','工程順SUB'])
          merged_df5 = merged_df5[~((merged_df5['チェック項目'] == 'なし') & (merged_df5['チェック基準'] == 'なし'))]
          merged_df5 = merged_df5.fillna('')
          merged_df5 = merged_df5[~((merged_df5['チェック項目'] == '') & (merged_df5['チェック基準'] == ''))]

          #チェック入力がない工程の復活処理
          merged_df4 = merged_df4[['工程','工程順','工程順SUB','加工機','図番']]
          merged_df6 = pd.merge(merged_df4, merged_df5, left_on=['工程順','工程順SUB'],right_on=['工程順','工程順SUB'],how='left')

          #不要項目の削除
          mask = (merged_df6['工程'] == merged_df6['工程'].shift(1)) &(merged_df6['工程順SUB'] != merged_df6['工程順SUB'].shift(1))&(merged_df6['工程順SUB'] != 1) #工程が同じで工程順SUBが違う（元の工程順は同じ）なら工程を空欄にする
          merged_df6.loc[mask, ['工程']] = ""
          mask = (merged_df6[['工程順','工程順SUB']] == merged_df6[['工程順','工程順SUB']].shift(1)).all(axis=1)
          merged_df6.loc[mask, ['工程','加工機','図番','図面Ver']] = ""
          merged_df6 = merged_df6[['工程','加工機','図番','図面Ver','チェック項目','チェック基準','生産開始月']]

          #空欄行の挿入
          #indices = merged_df6.index[(merged_df6['工程'] != '') & ((merged_df6['工程'].shift(1) == '') | (merged_df6['工程'].shift(1) != merged_df6['工程']))]
          indices = merged_df6.index[(merged_df6['工程'] != '')]
          for index in sorted(indices, reverse=True):
            if index != 0:
              # 空白行と横線行を挿入
              blank_row = pd.Series([''] * len(merged_df6.columns), index=merged_df6.columns)
              line_row = pd.Series(['=====','=============','========================','=====','=======================','===================',""], index=merged_df6.columns)
              merged_df6 = pd.concat([merged_df6.iloc[:index], pd.DataFrame([blank_row, line_row]), merged_df6.iloc[index:]]).reset_index(drop=True)
          #加工機2 図番2 の対応
          #indices2 = merged_df6.index[(merged_df6['工程'] == '') & (merged_df6['図番'] != '')]
          indices2 = merged_df6.index[(merged_df6['工程'] == '') & (merged_df6['図番'] != '')& (merged_df6['図番'].shift(1) != '')]
          for index in sorted(indices2, reverse=True):
            if index != 0:
              # 空白行を挿入
              blank_row = pd.Series([''] * len(merged_df6.columns), index=merged_df6.columns)
              merged_df6 = pd.concat([merged_df6.iloc[:index], pd.DataFrame([blank_row]), merged_df6.iloc[index:]]).reset_index(drop=True)

          # 空白行を gyo の数だけ追加
          blank_row = pd.Series([''] * len(merged_df6.columns), index=merged_df6.columns)
          #blank_gyo = gyo - merged_df6.shape[0]
          blank_gyo = 1
          for i in range(blank_gyo):
            merged_df6 = pd.concat([merged_df6, pd.DataFrame([blank_row])], ignore_index=True)

          #図面Verを図番の下段に追加
          mask = (merged_df6['図番'].shift(1).fillna('') != "") & (~merged_df6['図番'].shift(1).fillna('').str.contains('='))
          merged_df6.loc[mask, '図番'] = "Ver:" + merged_df6['図面Ver'].shift(1).fillna('').astype(str).str.cat(merged_df6['生産開始月'].shift(1).fillna('').astype(str), sep='　')
  
          df = merged_df6
          df = df.drop('生産開始月', axis=1)
          df = df.drop('図面Ver', axis=1) #変更ボタンなので
          df = df.fillna('')
          if (df.iloc[-1] == '').all():
            df = df.iloc[:-1]
          if df.empty:
            df.loc[0]=["無し","登録なし","登録無し","","","",""]
          
          
          st.write(f'部番：{buban}　工程Ver:{kouteiver}　※図面Verは最新のものが表示されます')
          colck1,colck2= st.columns([2,1])
          with colck1:
          #df[['測定値','測定器','加工日','測定者','判定合否']] =""
            st.table(df)
      else:
        st.write('「チェックシート項目　登録」タブで「図番選択」から選択してください')

    with tab4:
      
        st.markdown("##### i-Reporter_発行対象管理")
        st.markdown("i-Reporterの各種ランニングチェックシートは現品票を発行する時点で作成されます。  \n \
                    ここでは部品毎にi-Reporterでのチェック対象とするか管理します。")
        
        sql = 'SELECT * FROM buhin_irepo_mst'
        filepath = os.path.dirname(os.path.dirname(__file__))+'\\Database\\genpinhyo.db'
        buhin_irepo_df = sqlite_data_get(sql,filepath)
        buhin_irepo_df = buhin_irepo_df.sort_values(['部品名'])
        
        col1,col2 = st.columns([2,1])
        with col1:
          edited_mst_df = st.data_editor(buhin_irepo_df,hide_index=True,
                                  column_config={
                                    '部品名': {'width': 180},
                                    'ireporter管理flg': {'width': 160} ,
                                    'QRコードレイアウト区分': {'width': 200} ,
                                    '縦横区分': {'width': 110} 
                                    },disabled=["部品名"])          
        with col2:
          st.markdown('i-reporterでチェックを行う部品は「ireporter管理flg」に 1 を入力してください。  \n \
                      紙でチェックを行う場合は 0 を入力してください。')
          st.markdown('「QRコードレイアウト」は カムリング、ダイヤルキャップカムリングは 1 を入力してください。  \n \
                      上記以外は 0 を入力してください。（旧レイアウト対応用）')
          st.markdown('「縦横管理」は、縦レイアウトのチェックシートを使用する場合は 1 を入力してください  \n \
                      横レイアウトを使用する場合は 0 を入力してください。')
          if st.button("項目更新"):
            db_update4(edited_mst_df)
            st.write('更新完了')
  if __name__ == "__main__":
    main()

except Exception as e:
  #簡単なエラー処理
  print(e)
  dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
  with open(os.path.dirname(os.path.dirname(__file__))+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
    f.write(str(e))
