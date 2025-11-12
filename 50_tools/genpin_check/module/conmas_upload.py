################################
#　自動帳票作成の共通モジュール　　#
################################
#インポート
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

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

def data_upload(csv_name,df_len):

    #chromeのwebdriverをセット
    driver = webdriver.Chrome()
    #アドレスを指定（直接アップロード画面を指定）/1秒待機
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
    select.select_by_value('2')  # 2番目のoptionタグを選択状態に（公開）
    time.sleep(2)

    #ﾁｪｯｸﾎﾞｯｸｽをクリック
    time.sleep(1) #待機しないとエラーになる
    #driver.find_element(by=By.XPATH, value='//*[@id="Cbx"]').click()
    sql = "select def_top_id from view_def_top where def_top_org = 405 and public_status = 2"
    irepo_df = ireporter_data_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる
    sql = "select def_top_id from view_def_top where def_top_org = 406 and public_status = 2"
    irepo_df = ireporter_data_get(sql)
    driver.find_element(by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
    time.sleep(1) #待機しないとエラーになる

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
    driver.save_screenshot(os.path.dirname(os.path.dirname(__file__))+"\\work\\sumi\\png\\"+sc1_name)  

    #取り込みボタンクリック/1件4.7秒待機
    driver.find_element(by=By.XPATH, value='//*[@id="DetailSection"]/div/div[2]/input').click()
    time.sleep(int(df_len*3.3))

    #記録のため、画面のハードコピーを取得2
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    sc2_name = dt_now.strftime('%Y%m%d%H%M%S'+'_作成'+os.path.splitext(os.path.basename(csv_name))[0]+'_SC2.png')
    driver.save_screenshot(os.path.dirname(os.path.dirname(__file__))+"\\work\\sumi\\png\\"+sc2_name)  
    time.sleep(1)

    #インプットファイルをリネームして移動
    dt_now = datetime.now(timezone(timedelta(hours=9))) # 日本時刻
    backup_name = dt_now.strftime('%Y%m%d%H%M%S')+'_作成'+os.path.basename(csv_name)
    shutil.move(csv_name,os.path.dirname(os.path.dirname(__file__))+"\\csv\\sumi\\"+backup_name)
    time.sleep(1)

    #終了処理　driverオブジェクトを開放する
    driver.quit()

def main():
  data_upload()

if __name__ == '__main__':
  main()