import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import sqlite3

try:
    def df_csv_cnv(df,filename):
      #DFをcsvにコンバートして出力
      dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
      csv_name = os.path.dirname(__file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_"+filename+".csv"
      df.to_csv(csv_name,index=False,encoding='CP932')

    #jsonデータ読み取り
    jdata = json.loads(sys.stdin.readline())
    
    #ロット番号をポップ
    lot = jdata['data'].pop()
    if lot == "":
        raise ValueError("伝票番号が空です")
    if lot.startswith("KARI"):
        raise ValueError("KARIから始まる伝票番号はヘッダーを展開できません。手入力をお願いします。")

    # #DB接続定義
    filepath = 'd:\\py\\genpin_check\\database\\genpinhyo.db'
    conn = sqlite3.connect(filepath)

    cursor = conn.cursor()
    sql = f'select * from genpinhyo where ロット番号 = "{lot}"'
    df = pd.read_sql(sql, conn)
    
    df['工程VERSION']  = df['工程VERSION'].astype(float).astype(int).astype(str) #小数点取り除き
    if df.empty:
        raise ValueError("伝票番号が無効です")
    mekki=""
    if df.iloc[0]['ﾒｯｷ']=="1.0":
        mekki = "無電解ニッケルメッキ"
    
    mappings = {"error":"","mappings":[{"item":"header_koushin","sheet":1,"cluster":1,"type":"string","value":df.iloc[0]['部品名']},
                                      {"item":"header_koushin","sheet":1,"cluster":3,"type":"string","value":df.iloc[0]['完成部番']},
                                      {"item":"header_koushin","sheet":1,"cluster":4,"type":"string","value":df.iloc[0]['月次']},
                                      {"item":"header_koushin","sheet":1,"cluster":5,"type":"string","value":df.iloc[0]['組立番号']},
                                      {"item":"header_koushin","sheet":1,"cluster":6,"type":"string","value":df.iloc[0]['機種']},
                                      {"item":"header_koushin","sheet":1,"cluster":7,"type":"string","value":df.iloc[0]['吋']},
                                      {"item":"header_koushin","sheet":1,"cluster":8,"type":"string","value":df.iloc[0]['G']},
                                      {"item":"header_koushin","sheet":1,"cluster":9,"type":"string","value":df.iloc[0]['客先名']},
                                      {"item":"header_koushin","sheet":1,"cluster":11,"type":"string","value":mekki},
                                      {"item":"header_koushin","sheet":1,"cluster":644,"type":"string","value":df.iloc[0]['工程VERSION']}]}
    print(json.dumps(mappings))

except ValueError as e:
    mappings = {"error": "エラー：" + str(e)}
    print(json.dumps(mappings))
    
   
except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
