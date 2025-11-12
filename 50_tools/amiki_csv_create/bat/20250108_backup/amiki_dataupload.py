################################
#　編機調整報告書                #
#　簡単なDF表示のページ          #
################################
#インポート
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
import sqlite3
import os
import shutil

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
    
  def db_update(df):

      #バックアップ
      dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
      if(os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\actualtimestamp.db')):
        shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\actualtimestamp.db',
                    os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_actualtimestamp.db")

      #本処理（更新処理）
      dbname = 'actualtimestamp.db'
      cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
      conn = sqlite3.connect(cdb)
      cur = conn.cursor()
      
      #■テーブル作成処理
      #EXIT NOTを入れているので、テーブルがあった場合はスキップする（編機以外にも使用できる項目名）
      cur.execute('CREATE TABLE IF NOT EXISTS task_completion_date(\
                    ID INTEGER PRIMARY KEY,\
                    組立番号 TEXT,\
                    項目ID INTEGER,\
                    履歴番号 INTEGER,\
                    作業者 TEXT,\
                    更新日付 TEXT\
                    )')
      
      #データフレームの編集
      df1 = df[['組立番号','①ｶﾑﾎﾙﾀﾞｰ取付']].rename(columns={'①ｶﾑﾎﾙﾀﾞｰ取付':'作業者'})
      df1['項目ID'] = 1
      df2 = df[['組立番号','②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ']].rename(columns={'②ﾀｲﾐﾝｸﾞｹﾞｰﾃｨﾝｸﾞ':'作業者'})
      df2['項目ID'] = 2
      df3 = df[['組立番号','③針入れ等']].rename(columns={'③針入れ等':'作業者'})
      df3['項目ID'] = 3
      df4 = df[['組立番号','④ss_wac_act_取付']].rename(columns={'④ss_wac_act_取付':'作業者'})
      df4['項目ID'] = 4
      df5 = df[['組立番号','⑤rdsﾁｪｯｸ']].rename(columns={'⑤rdsﾁｪｯｸ':'作業者'})
      df5['項目ID'] = 5
      df6 = df[['組立番号','⑥慣らし運転']].rename(columns={'⑥慣らし運転':'作業者'})
      df6['項目ID'] = 6
      df7 = df[['組立番号','⑦電気ﾁｪｯｸ']].rename(columns={'⑦電気ﾁｪｯｸ':'作業者'})
      df7['項目ID'] = 7
      df8 = df[['組立番号','⑧ﾔｰﾝｷｬﾘｱ取付']].rename(columns={'⑧ﾔｰﾝｷｬﾘｱ取付':'作業者'})
      df8['項目ID'] = 8
      df9 = df[['組立番号','⑨巻取装置']].rename(columns={'⑨巻取装置':'作業者'})
      df9['項目ID'] = 9
      df10 = df[['組立番号','⑩幅出装置']].rename(columns={'⑩幅出装置':'作業者'})
      df10['項目ID'] = 10
      df11 = df[['組立番号','⑪編成作業']].rename(columns={'⑪編成作業':'作業者'})
      df11['項目ID'] = 11
      df12 = df[['組立番号','作業者合否入力']].rename(columns={'作業者合否入力':'作業者'})
      df12['項目ID'] = 12
      df13 = df[['組立番号','⑫取付作業']].rename(columns={'⑫取付作業':'作業者'})
      df13['項目ID'] = 13
      df14 = df[['組立番号','⑬最終確認']].rename(columns={'⑬最終確認':'作業者'})
      df14['項目ID'] = 14
      df15 = df[['組立番号','最終ﾁｪｯｸ入力']].rename(columns={'最終ﾁｪｯｸ入力':'作業者'})
      df15['項目ID'] = 15
      df16 = df[['組立番号','最終承認入力']].rename(columns={'最終承認入力':'作業者'})
      df16['項目ID'] = 16
      merged_df = pd.concat([df1,df2,df3,df4,df5,df6,df7,df8,df9,df10,
            df11,df12,df13,df14,df15,df16], ignore_index=True)
      merged_df['更新日付']=dt_now.strftime('%Y-%m-%d')

      # 各行に対して更新処理を行う
      for _, row in merged_df.iterrows():
      # 組立番号が既に存在するか確認
        cur.execute("SELECT 履歴番号, 作業者 FROM task_completion_date WHERE 組立番号 = ? AND 項目ID = ? ORDER BY 履歴番号 DESC LIMIT 1", (row['組立番号'], row['項目ID']))
        existing_records = cur.fetchall()

        if not existing_records:
            # 条件1: 組立番号が重複していない場合、INSERT
            cur.execute("""
                INSERT INTO task_completion_date (組立番号, 項目ID, 履歴番号, 作業者, 更新日付)
                VALUES (?, ?, ?, ?, ?)
            """, (row['組立番号'], row['項目ID'], 1, row['作業者'], row['更新日付']))
        else:
            # 条件2と条件3: 組立番号が重複している場合
            current_history, existing_worker = existing_records[0]  # 既存の履歴番号と作業者を取得
            #if existing_worker == row['作業者'] or existing_worker is None:
            if existing_worker != row['作業者']:
              if existing_worker is None or existing_worker=='':
                # 元の作業者がNone or 空欄の場合UPDATE
                cur.execute("""
                    UPDATE task_completion_date
                    SET 更新日付 = ? ,作業者 = ?
                    WHERE 組立番号 = ? AND 項目ID = ?
                """, (row['更新日付'], row['作業者'], row['組立番号'], row['項目ID']))
              else:
                # 作業者が異なる場合、履歴番号を+1してINSERT
                new_history_number = current_history + 1
                cur.execute("""
                    INSERT INTO task_completion_date (組立番号, 項目ID, 履歴番号, 作業者, 更新日付)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['組立番号'], row['項目ID'], new_history_number, row['作業者'], row['更新日付']))
      # 変更をコミットして接続をクローズ
      conn.commit()
      conn.close()
  
  def main():

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
            from view_report_393"
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
            from view_report_394"
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
            from view_report_395"
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
            from view_report_396"
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
            from view_report_397"
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
            from view_report_398"
    df6 = ireporter_data_get(sql)
    
    df = pd.concat([df1,df2,df3,df4,df5,df6], ignore_index=True)
    db_update(df)

  if __name__ == "__main__":
        main()

except Exception as e:
  #簡単なエラー処理
  dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
  with open(os.path.dirname(__file__)+"\\err\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
    f.write(str(e))