################################
#　新現品票追加作成　　　　　　　     #
################################
#インポート
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
import shutil
import pyqrcode
import openpyxl
from PIL import Image
from datetime import datetime, timedelta, timezone
import pythoncom
import random
import sqlite3

try:
  pythoncom.CoInitialize() #サーバーサイドからローカルファイルを動かすときに必要
  
 
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
        # SQLクエリの実行
        df = pd.read_sql(sql, connection)
  
      # セッションを閉じる
      session.close()   
  
      return(df)

  def db_update(edit_df):
    
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

  def main():

    st.set_page_config(
    page_title = 'i-Reporter_発行対象管理',
      layout="wide" )

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
    sql = 'SELECT * FROM buhin_irepo_mst'
    filepath = os.path.dirname(os.path.dirname(__file__))+'\\Database\\genpinhyo.db'
    buhin_irepo_df = sqlite_data_get(sql,filepath)
    buhin_irepo_df = buhin_irepo_df.sort_values(['部品名'])
    
    
    st.markdown("### i-Reporter_発行対象管理")
    st.markdown("i-Reporterの各種ランニングチェックシートは現品票を発行する時点で作成されます。  \n \
                ここでは部品毎にi-Reporterでのチェック対象とするか管理します。　（管理者：マシニング課）")
    # 水平線
    st.divider()
    col1,col2 = st.columns([2,1])
    with col1:
      edited_df = st.data_editor(buhin_irepo_df,hide_index=True,
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
        db_update(edited_df)
        st.write('更新完了')
  if __name__ == "__main__":
    main()

except Exception as e:
  #簡単なエラー処理
  print(e)
  dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
  with open(os.path.dirname(__file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
    f.write(str(e))