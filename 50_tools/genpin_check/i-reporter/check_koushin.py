####
#更新用追加1と更新用追加2以外は、check_tenkaiと同じ処理内容とする
#→図面番号が重複するケースがあったため、一部処理を変更した
####
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
    
    #行数をポップ
    gyo = int(jdata['data'].pop())

    #更新用追加１
     #最初の2要素を除いたリスト
    data_trimmed = jdata['data'][2:]

     #リストを2つずつに分割し、df化、更新対象のdfを抽出
    #data_pairs = [data_trimmed[i:i + 2] for i in range(0, len(data_trimmed), 2)] 3分割に変更
    #kousin_df = pd.DataFrame(data_pairs, columns=['K図番', 'K図面Ver'])
    #data_pairs = [data_trimmed[i:i + 3] for i in range(0, len(data_trimmed), 3)]
    data_pairs = []
    value_to_add = 1  # 初期値
    # 0から len(data_trimmed) までの範囲で 3 ずつインクリメント
    for i in range(0, len(data_trimmed), 3):
        # 3つずつのスライスを取得
        slice = data_trimmed[i:i + 3]
        if slice[0] == "=============":
          value_to_add += 1  # 数値を1加算
        slice.append(int(value_to_add))
    
        # スライスを data_pairs に追加
        data_pairs.append(slice)
        
    #kousin_df = pd.DataFrame(data_pairs, columns=['K加工機','K図番', 'K図面Ver'])
    kousin_df = pd.DataFrame(data_pairs, columns=['K加工機','K図番', 'K図面Ver','K工程順'])
    kousin_df = kousin_df[((kousin_df['K図番'] != '') & (kousin_df['K図面Ver'] != '')& (kousin_df['K図面Ver'] != '0'))]
    
    #空のデータフレームを作成
    df = pd.DataFrame(columns=['工程','加工機','図番','図面Ver','チェック項目','チェック基準','生産開始月'])
    df.loc[0]=["無し","登録なし","登録無し","","","",""]
    blank_row = pd.Series([''] * len(df.columns), index=df.columns)
    blank_gyo = gyo - 1
    for i in range(blank_gyo):
      df = pd.concat([df, pd.DataFrame([blank_row])], ignore_index=True)

    if jdata['data'][0] != "" and jdata['data'][1] != "":
   
      buban = jdata["data"][0] #(jsonの中身はdataという固定名称の配列)
      kouteiver = jdata["data"][1] #(jsonの中身はdataという固定名称の配列)

      # #DB接続定義
      filepath = 'd:\\py\\genpin_check\\database\\checksheet.db'
      conn = sqlite3.connect(filepath)
      
      cursor = conn.cursor()
      sql1 = f'select * from kouteizuban where 完成部番 = "{buban}"and 工程Ver = "{kouteiver}"'
      df1 = pd.read_sql(sql1, conn)

      sql2 = f'select * from zubancheck'
      df2 = pd.read_sql(sql2, conn)

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
          merged_df3['図面Ver'] = merged_df3['図面Ver'].astype(str)

          #更新用追加２
          if not kousin_df.empty:
             
             kousin_df['K図面Ver'] = kousin_df['K図面Ver'].astype(str)
             #merged_df3 = pd.merge(merged_df3, kousin_df, left_on=['図番'],right_on=['K図番'],how='left') 3分割に変更
             #merged_df3 = pd.merge(merged_df3, kousin_df, left_on=['加工機','図番'],right_on=['K加工機','K図番'],how='left')
             merged_df3 = pd.merge(merged_df3, kousin_df, left_on=['工程順','図番'],right_on=['K工程順','K図番'],how='left')

             # 条件の定義
             #mask = (merged_df3['図番'] == merged_df3['K図番']) & (merged_df3['図面Ver'] != merged_df3['K図面Ver']) 3分割に変更
             #mask = (merged_df3['加工機'] == merged_df3['K加工機']) & (merged_df3['図番'] == merged_df3['K図番']) & (merged_df3['図面Ver'] != merged_df3['K図面Ver'])　加工機では重複する可能性があるため、工程順で判定
             mask = (merged_df3['工程順'] == merged_df3['K工程順']) & (merged_df3['図番'] == merged_df3['K図番']) & (merged_df3['図面Ver'] != merged_df3['K図面Ver'])

             # 条件を満たす行を削除
             merged_df3 = merged_df3[~mask].reset_index(drop=True)             
          
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
          indices2 = merged_df6.index[(merged_df6['工程'] == '') & (merged_df6['図番'] != '')& (merged_df6['図番'].shift(1) != '')]
          for index in sorted(indices2, reverse=True):
            if index != 0:
              # 空白行を挿入
              blank_row = pd.Series([''] * len(merged_df6.columns), index=merged_df6.columns)
              merged_df6 = pd.concat([merged_df6.iloc[:index], pd.DataFrame([blank_row]), merged_df6.iloc[index:]]).reset_index(drop=True)

          # 空白行を gyo の数だけ追加
          blank_row = pd.Series([''] * len(merged_df6.columns), index=merged_df6.columns)
          blank_gyo = gyo - merged_df6.shape[0]
          for i in range(blank_gyo):
            merged_df6 = pd.concat([merged_df6, pd.DataFrame([blank_row])], ignore_index=True)

          #図面Verを図番の下段に追加
          mask = (merged_df6['図番'].shift(1).fillna('') != "") & (~merged_df6['図番'].shift(1).fillna('').str.contains('='))
          merged_df6.loc[mask, '図番'] = "　　　Ver:" + merged_df6['図面Ver'].shift(1).fillna('').astype(str).str.cat(merged_df6['生産開始月'].shift(1).fillna('').astype(str), sep='　')
  
          df = merged_df6

          if df.empty:
            df.loc[0]=["無し","登録なし","登録無し","","","",""]
            blank_row = pd.Series([''] * len(df.columns), index=df.columns)
            blank_gyo = gyo - 1
            for i in range(blank_gyo):
              df = pd.concat([df, pd.DataFrame([blank_row])], ignore_index=True)

    #値の格納ループ
    df = df.fillna('')
    mapping_work = []
    for index, row in df.iterrows():
       if index == gyo:
         cluster = 11
         value ="※項目数超過：チェック項目数超過！　グループリーダーに問い合わせてください"
         ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
         mapping_work.append(ck_dict)
         break
       #工程
       cluster =14 + index*12
       value =row['工程']
       ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       #ADD_20250109_加工機が登録されている場合はチェック対象（主にオイルミスト）
       if value == "" and row['加工機'] != "":
           ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":"　"}
       mapping_work.append(ck_dict)
       #加工機
       cluster =15 + index*12
       value =row['加工機']
       ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       mapping_work.append(ck_dict)
       #図番
       cluster =16 + index*12
       value =row['図番']
       ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       mapping_work.append(ck_dict)
       #図面Ver
       cluster =17 + index*12
       #value =str(int(row['図面Ver']))
       value =row['図面Ver']
       if value != '' and value != '=====':
           value =str(int(row['図面Ver']))
       ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       #mapping_work.append(ck_dict)
       #チェック項目
       cluster =18 + index*12
       value =row['チェック項目']
       ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       mapping_work.append(ck_dict)
       #チェック基準
       cluster =19 + index*12
       value =row['チェック基準']
       ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       mapping_work.append(ck_dict)

       #if row['工程'] == '=====':
       #    #測定値
       #    cluster =20 + index*12
       #    value = '=========='
       #    ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       #    mapping_work.append(ck_dict)
       #    
       #    #測定器
       #    cluster =21 + index*12
       #    value = '=========='
       #    ck_dict = {"item":"check_tenkai","sheet":1,"cluster":cluster,"type":"string","value":value}
       #    mapping_work.append(ck_dict)  
    #dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    #f = open(os.path.dirname(__file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_"+"myfile.txt", 'w')
    #f.write(str(jdata))
    #f.close()       
    
    mappings = {"error":"","mappings":mapping_work}
    print(json.dumps(mappings))

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
