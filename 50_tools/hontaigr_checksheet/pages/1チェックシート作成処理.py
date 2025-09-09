################################
# 　本体グループ製造チェックシート #
# 　自動帳票作成処理　　　　　　   #
# 　手動で実行する　　　　　　　　 #
#
# 　変更履歴：20250708_100帳票への変更
################################

# インポート
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

    pythoncom.CoInitialize()  # サーバーサイドからローカルファイルを動かすことになるので必要

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

    def df_edit(merged_df):

        df1 = merged_df
        df1.insert(0, 'defTopId', '')

        # ADD_20241210_区分に基づく帳票振り分けロジック追加
        # 原紙_本体Gr_製造チェックシート_2p　636（生産機）/ 747（整備機）
        # 63以下のマスク
        mask_df = df1['行数'] <= 63
        # 生産機の場合は636（区分が空やNULLの場合も生産機として扱う）
        mask_seisan = mask_df & ((df1['区分'] == '生産機') | (df1['区分'].isna()) | (df1['区分'] == ''))
        sql = "select def_top_id from view_def_top where def_top_org = 636 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_seisan, 'defTopId'] = irepo_df['def_top_id'].max()
        # 整備機の場合は747
        mask_seibi = mask_df & (df1['区分'] == '整備機')
        sql = "select def_top_id from view_def_top where def_top_org = 747 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_seibi, 'defTopId'] = irepo_df['def_top_id'].max()

        # 原紙_本体Gr_製造チェックシート_3p　637（生産機）/ 751（整備機）
        # 64以上97以下のマスク
        mask_df = (df1['行数'] >= 64) & (df1['行数'] <= 97)
        # 生産機の場合は637（区分が空やNULLの場合も生産機として扱う）
        mask_seisan = mask_df & ((df1['区分'] == '生産機') | (df1['区分'].isna()) | (df1['区分'] == ''))
        sql = "select def_top_id from view_def_top where def_top_org = 637 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_seisan, 'defTopId'] = irepo_df['def_top_id'].max()
        # 整備機の場合は751
        mask_seibi = mask_df & (df1['区分'] == '整備機')
        sql = "select def_top_id from view_def_top where def_top_org = 751 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_seibi, 'defTopId'] = irepo_df['def_top_id'].max()

        # 原紙_本体Gr_製造チェックシート_4p　638（生産機）/ 752（整備機）
        # 98以上のマスク
        mask_df = df1['行数'] >= 98
        # 生産機の場合は638（区分が空やNULLの場合も生産機として扱う）
        mask_seisan = mask_df & ((df1['区分'] == '生産機') | (df1['区分'].isna()) | (df1['区分'] == ''))
        sql = "select def_top_id from view_def_top where def_top_org = 638 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_seisan, 'defTopId'] = irepo_df['def_top_id'].max()
        # 整備機の場合は752
        mask_seibi = mask_df & (df1['区分'] == '整備機')
        sql = "select def_top_id from view_def_top where def_top_org = 752 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        df1.loc[mask_seibi, 'defTopId'] = irepo_df['def_top_id'].max()

        df1.insert(0, 'H', 'R')
        # ADD_20241210_区分列追加により12列に変更
        df1.columns = ['H', 'defTopId', 'S1C3', 'S1C4', 'S1C5',
                       'S1C6', 'S1C0', 'S1C1', 'S1C2', '区分', 'S1C10', 'S1C11']
        df1 = df1[['H', 'defTopId', 'S1C0', 'S1C1', 'S1C2', 'S1C3']]

        return (df1)

    def input_data_create(nen, getsu):

        # hontai_seizo.dbから生産機情報取得する
        sql = f'SELECT * FROM production_machine_info WHERE 年={nen} and 月={getsu}'
        filepath = os.path.dirname(os.path.dirname(
            __file__))+'\\Database\\hontai_seizo.db'
        seisan_df = sqlite_data_get(sql, filepath)

        # 以下、行数の特定処理
        sql = f'select * from report_type_table'
        report_type_df = sqlite_data_get(sql, filepath)
        report_type_df = report_type_df.sort_values(['帳票No'])
        report_type_df = report_type_df.fillna(' ')  # Noneデータ対策

        sql = f'select * from check_item_table'
        check_item_df = sqlite_data_get(sql, filepath)
        check_item_df = check_item_df.fillna(' ')  # Noneデータ対策

        # 縦列への変更
        df_category1 = report_type_df[['帳票No', 'カテゴリ区分1']].rename(
            columns={'カテゴリ区分1': 'カテゴリ区分'})
        df_category2 = report_type_df[['帳票No', 'カテゴリ区分2']].rename(
            columns={'カテゴリ区分2': 'カテゴリ区分'})
        df_category3 = report_type_df[['帳票No', 'カテゴリ区分3']].rename(
            columns={'カテゴリ区分3': 'カテゴリ区分'})
        df_category4 = report_type_df[['帳票No', 'カテゴリ区分4']].rename(
            columns={'カテゴリ区分4': 'カテゴリ区分'})
        df_category5 = report_type_df[['帳票No', 'カテゴリ区分5']].rename(
            columns={'カテゴリ区分5': 'カテゴリ区分'})
        df_category6 = report_type_df[['帳票No', 'カテゴリ区分6']].rename(
            columns={'カテゴリ区分6': 'カテゴリ区分'})
        df_category7 = report_type_df[['帳票No', 'カテゴリ区分7']].rename(
            columns={'カテゴリ区分7': 'カテゴリ区分'})
        df_category8 = report_type_df[['帳票No', 'カテゴリ区分8']].rename(
            columns={'カテゴリ区分8': 'カテゴリ区分'})
        df_category9 = report_type_df[['帳票No', 'カテゴリ区分9']].rename(
            columns={'カテゴリ区分9': 'カテゴリ区分'})
        df_category10 = report_type_df[['帳票No', 'カテゴリ区分10']].rename(
            columns={'カテゴリ区分10': 'カテゴリ区分'})
        df_category11 = report_type_df[['帳票No', 'カテゴリ区分11']].rename(
            columns={'カテゴリ区分11': 'カテゴリ区分'})
        df_category12 = report_type_df[['帳票No', 'カテゴリ区分12']].rename(
            columns={'カテゴリ区分12': 'カテゴリ区分'})
        df_category13 = report_type_df[['帳票No', 'カテゴリ区分13']].rename(
            columns={'カテゴリ区分13': 'カテゴリ区分'})
        df_category14 = report_type_df[['帳票No', 'カテゴリ区分14']].rename(
            columns={'カテゴリ区分14': 'カテゴリ区分'})
        df_category15 = report_type_df[['帳票No', 'カテゴリ区分15']].rename(
            columns={'カテゴリ区分15': 'カテゴリ区分'})
        df_category16 = report_type_df[['帳票No', 'カテゴリ区分16']].rename(
            columns={'カテゴリ区分16': 'カテゴリ区分'})
        df_category17 = report_type_df[['帳票No', 'カテゴリ区分17']].rename(
            columns={'カテゴリ区分17': 'カテゴリ区分'})
        df_category18 = report_type_df[['帳票No', 'カテゴリ区分18']].rename(
            columns={'カテゴリ区分18': 'カテゴリ区分'})
        df_category19 = report_type_df[['帳票No', 'カテゴリ区分19']].rename(
            columns={'カテゴリ区分19': 'カテゴリ区分'})
        df_category20 = report_type_df[['帳票No', 'カテゴリ区分20']].rename(
            columns={'カテゴリ区分20': 'カテゴリ区分'})
        df_category21 = report_type_df[['帳票No', 'カテゴリ区分21']].rename(
            columns={'カテゴリ区分21': 'カテゴリ区分'})
        df_category22 = report_type_df[['帳票No', 'カテゴリ区分22']].rename(
            columns={'カテゴリ区分22': 'カテゴリ区分'})
        df_category23 = report_type_df[['帳票No', 'カテゴリ区分23']].rename(
            columns={'カテゴリ区分23': 'カテゴリ区分'})
        df_category24 = report_type_df[['帳票No', 'カテゴリ区分24']].rename(
            columns={'カテゴリ区分24': 'カテゴリ区分'})
        df_category25 = report_type_df[['帳票No', 'カテゴリ区分25']].rename(
            columns={'カテゴリ区分25': 'カテゴリ区分'})
        df_category26 = report_type_df[['帳票No', 'カテゴリ区分26']].rename(
            columns={'カテゴリ区分26': 'カテゴリ区分'})
        df_category27 = report_type_df[['帳票No', 'カテゴリ区分27']].rename(
            columns={'カテゴリ区分27': 'カテゴリ区分'})
        df_category28 = report_type_df[['帳票No', 'カテゴリ区分28']].rename(
            columns={'カテゴリ区分28': 'カテゴリ区分'})
        df_category29 = report_type_df[['帳票No', 'カテゴリ区分29']].rename(
            columns={'カテゴリ区分29': 'カテゴリ区分'})
        df_category30 = report_type_df[['帳票No', 'カテゴリ区分30']].rename(
            columns={'カテゴリ区分30': 'カテゴリ区分'})

        # データフレームをリストに格納
        df_list = [
            df_category1, df_category2, df_category3, df_category4, df_category5,
            df_category6, df_category7, df_category8, df_category9, df_category10,
            df_category11, df_category12, df_category13, df_category14, df_category15,
            df_category16, df_category17, df_category18, df_category19, df_category20,
            df_category21, df_category22, df_category23, df_category24, df_category25,
            df_category26, df_category27, df_category28, df_category29, df_category30
        ]
        tate_combined_df = pd.concat(df_list, ignore_index=True)
        tate_combined_df = tate_combined_df.reset_index().sort_values(
            ['帳票No', 'index']).set_index('index')
        tate_combined_df = tate_combined_df.reset_index()
        tate_combined_df['連番'] = tate_combined_df.groupby(
            '帳票No').cumcount() + 1
        tate_combined_df['機種区分'] = tate_combined_df['帳票No'].apply(
            lambda x: 'SK' if 101 <= x <= 200 else 'DK' if 201 <= x <= 300 else 'その他')

        tate_combined_df = tate_combined_df.merge(
            check_item_df, how='left',
            left_on=['機種区分', '連番', 'カテゴリ区分'],
            right_on=['機種区分', 'カテゴリNo', 'カテゴリ区分']
        )
        tate_combined_df = tate_combined_df[tate_combined_df['カテゴリ区分'] != 99]

        # 異なるカテゴリNoを検出
        diff_mask = tate_combined_df['カテゴリNo'] != tate_combined_df['カテゴリNo'].shift(
        )
        # 追加する行を作成
        new_rows = tate_combined_df[diff_mask].copy()

        # "チェック項目" に仮に固定文言を設定
        new_rows['チェック項目'] = '【タイトル】'

        # 元のデータフレームと結合
        tate_combined_df = pd.concat([tate_combined_df, new_rows])

        # 各帳票ごとの行数を特定
        row_count_df = tate_combined_df.groupby(
            '帳票No').size().reset_index(name='行数')

        # 生産機情報に行情報を追加して返却
        merged_df = seisan_df.merge(
            row_count_df, how='left', left_on=['帳票No'], right_on=['帳票No'])

        # 自動帳票作成csv用のdfを作成する
        jidou_df = df_edit(merged_df)

        return (jidou_df)

    def data_upload(csv_name, df_len):

        # chromeのwebdriverをセット
        driver = webdriver.Chrome()
        # アドレスを指定（直接アップロード画面を指定）/1秒待機
        # driver.get("http://localhost/ConMasManager/AutoGenerate")
        driver.get("http://172.17.52.101/ConMasManager/AutoGenerate")
        time.sleep(1)

        # ユーザー名/パスワード/ログイン画面/1秒待機
        driver.find_element(
            by=By.XPATH, value='//*[@id="UserName"]').send_keys('mainte')
        driver.find_element(
            by=By.XPATH, value='//*[@id="Password"]').send_keys('@next123')
        driver.find_element(
            by=By.XPATH, value='//*[@id="image-login_btn"]').click()
        time.sleep(1)

        # ドロップダウンリストを取得（一旦テストを取得）
        driver.find_element(
            by=By.XPATH, value='//*[@id="PublicStatus"]').click()
        dropdown = driver.find_element(
            by=By.XPATH, value='//*[@id="PublicStatus"]')
        select = Select(dropdown)
        # select.select_by_value('1')  # 1番目のoptionタグを選択状態に（テスト）
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


        # ﾁｪｯｸﾎﾞｯｸｽをクリック
        time.sleep(2)  # 待機しないとエラーになる
        # driver.find_element(by=By.XPATH, value='//*[@id="Cbx"]').click()
        sql = "select def_top_id from view_def_top where def_top_org = 636 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        driver.find_element(
            by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
        time.sleep(1)  # 待機しないとエラーになる
        sql = "select def_top_id from view_def_top where def_top_org = 637 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        driver.find_element(
            by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
        time.sleep(1)  # 待機しないとエラーになる
        sql = "select def_top_id from view_def_top where def_top_org = 638 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        driver.find_element(
            by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
        # ADD_20241210_整備機用帳票（747/751/752）のチェックボックス選択を追加
        time.sleep(1)  # 待機しないとエラーになる
        sql = "select def_top_id from view_def_top where def_top_org = 747 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        driver.find_element(
            by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
        time.sleep(1)  # 待機しないとエラーになる
        sql = "select def_top_id from view_def_top where def_top_org = 751 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        driver.find_element(
            by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
        time.sleep(1)  # 待機しないとエラーになる
        sql = "select def_top_id from view_def_top where def_top_org = 752 and public_status = 2"
        irepo_df = irepo_view_get(sql)
        driver.find_element(
            by=By.XPATH, value=f'//input[@id="Cbx" and @value="{irepo_df['def_top_id'].max()}" and @name="Cbx"]').click()
        # 次へボタンクリック
        time.sleep(1)
        driver.find_element(
            by=By.XPATH, value='//*[@id="FiltersTable"]/tbody/tr/td[2]/a[2]').click()
        time.sleep(1)

        # ドロップダウンリストを取得(簡易csv）
        driver.find_element(by=By.XPATH, value='//*[@id="type"]').click()
        dropdown = driver.find_element(by=By.XPATH, value='//*[@id="type"]')
        select = Select(dropdown)
        select.select_by_value('csvSimple')  # 4番目のoptionタグを選択状態に
        time.sleep(1)

        # ドロップダウンリストを取得(1）
        driver.find_element(
            by=By.XPATH, value='//*[@id="defaultMode"]').click()
        dropdown = driver.find_element(
            by=By.XPATH, value='//*[@id="defaultMode"]')
        select = Select(dropdown)
        select.select_by_value('1')  # 1番目のoptionタグを選択状態に
        time.sleep(1)

        # ファイルアップロードボタンの要素取得
        file_upload = driver.find_element(
            by=By.XPATH, value='//*[@id="file1"]')
        time.sleep(1)

        # ファイルアップロードにcsvファイルをセット
        file_upload.send_keys(csv_name)

        # 確認ボタンクリック/1件0.7秒待機
        driver.find_element(
            by=By.XPATH, value='//*[@id="DetailSection"]/div/div[1]/input').click()
        time.sleep(int(df_len*0.7))

        # 記録のため、画面のハードコピーを取得1
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        sc1_name = dt_now.strftime(
            '%Y%m%d%H%M%S'+'_作成'+os.path.splitext(os.path.basename(csv_name))[0]+'_SC1.png')
        driver.save_screenshot(os.path.dirname(
            __file__)+"\\work\\sumi\\png\\"+sc1_name)

        # 取り込みボタンクリック/1件3秒待機
        driver.find_element(
            by=By.XPATH, value='//*[@id="DetailSection"]/div/div[2]/input').click()
        time.sleep(int(df_len*3))

        # 記録のため、画面のハードコピーを取得2
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        sc2_name = dt_now.strftime(
            '%Y%m%d%H%M%S'+'_作成'+os.path.splitext(os.path.basename(csv_name))[0]+'_SC2.png')
        driver.save_screenshot(os.path.dirname(
            __file__)+"\\work\\sumi\\png\\"+sc2_name)
        time.sleep(1)

        # インプットファイルをリネームして移動
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        backup_name = dt_now.strftime(
            '%Y%m%d%H%M%S')+'_作成'+os.path.basename(csv_name)
        shutil.move(csv_name, os.path.dirname(
            __file__)+"\\work\\sumi\\"+backup_name)
        time.sleep(1)

        # 終了処理　driverオブジェクトを開放する
        driver.quit()

    def rireki_read():
        con_df = pd.read_csv(os.path.dirname(
            os.path.dirname(__file__))+"\\config\\rireki.csv")
        nen = con_df.iat[0, 0]
        getsu = con_df.iat[0, 1]
        return (nen, getsu)

    def rireki_write(nen, getsu):
        con_df = pd.read_csv(os.path.dirname(
            os.path.dirname(__file__))+"\\config\\rireki.csv")
        con_df.iat[0, 0] = nen
        con_df.iat[0, 1] = getsu
        con_df.to_csv(os.path.dirname(os.path.dirname(__file__)) +
                      "\\config\\rireki.csv", index=False)

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

    def qr_create(nen, getsu):
        snen = int(nen)
        sgetsu = int(getsu)
        # ADD_20241023_分割対応
        sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_636 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
        qr_df1 = irepo_view_get(sql)
        sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_637 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
        qr_df2 = irepo_view_get(sql)
        sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_638 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
        qr_df3 = irepo_view_get(sql)
        # ADD_20241210_追加ビューテーブル対応（747/751/752の参照を追加）
        sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_747 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
        qr_df4 = irepo_view_get(sql)
        sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_751 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
        qr_df5 = irepo_view_get(sql)
        sql = f"select rep_top_id,top_remarks4,top_remarks1,top_remarks2,top_remarks3 from view_report_752 where top_remarks1 = '{snen}' and top_remarks2 = '{sgetsu}'"
        qr_df6 = irepo_view_get(sql)
        qr_df = pd.concat([qr_df1, qr_df2, qr_df3, qr_df4, qr_df5, qr_df6], ignore_index=True)
        qr_df = qr_df.sort_values(['top_remarks3', 'top_remarks4'])

        # 前回ファイルを削除
        for p in glob(os.path.dirname(__file__)+'\\qr_code\\*.png', recursive=True):
            if os.path.isfile(p):
                os.remove(p)

        # jp.co.cimtops.ireporter.openreport:repid=4080
        qr_list = []
        for index, row in qr_df.iterrows():
            id = row['rep_top_id']
            nen = row['top_remarks1']
            getsu = row['top_remarks2']
            ji = row['top_remarks3']
            name = row['top_remarks4']
            code = pyqrcode.create(
                f"jp.co.cimtops.ireporter.openreport:repid={id}", error='L', version=3, mode='binary')
            code.png(os.path.dirname(__file__) +
                     f'\\qr_code\\qrcode_{index}.png', scale=6)
            qr_list.append([os.path.dirname(
                __file__)+f'\\qr_code\\qrcode_{index}.png', nen, getsu, ji, name])

        return (qr_list)

    def qr_list_create(qr_list, nen, getsu):

        # 前回ファイルを削除
        for p in glob(os.path.dirname(__file__)+'\\qr_code\\*xlsx', recursive=True):
            if os.path.isfile(p):
                os.remove(p)

        # 一旦エクセルを作成して保存
        filename = f'{nen}年{getsu}月.xlsx'
        wb = os.path.dirname(__file__)+f'\\qr_code\\'+filename
        qr_wb = openpyxl.Workbook()
        qr_wb.save(wb)

        # ワークシート取得
        qr_ws = qr_wb.active

        # 各種設定
        # 余白とヘッダーフッターは全部0
        qr_ws.page_margins.left = 0
        qr_ws.page_margins.right = 0
        qr_ws.page_margins.top = 0
        qr_ws.page_margins.bottom = 0
        qr_ws.page_margins.header = 0
        qr_ws.page_margins.footer = 0
        # ページ設定を水平にする
        qr_ws.print_options.horizontalCentered = True

        # 引き渡された要素数を取得
        qr_len = len(qr_list)
        # 要素格納ループ
        for i in range(qr_len):
            # 画像を選択
            img_to_excel = openpyxl.drawing.image.Image(qr_list[i][0])

            # 指定の位置に画像を添付
            gyo = 13

            # １行目で行幅調整
            qr_ws.row_dimensions[i*gyo].height = 12

            # シート内に固定文字出力
            c = 3+(i*gyo)
            qr_ws[f"B{c}"] = "本体Gr_製造チェックシート"
            qr_ws[f"B{c}"].font = openpyxl.styles.Font(size=24)

            c = 4+(i*gyo)
            qr_ws[f"B{c}"] = "　　　カメラ起動用QRコード"
            qr_ws[f"B{c}"].font = openpyxl.styles.Font(size=18)

            c = 7+(i*gyo)
            qr_ws[f"C{c}"] = f"{qr_list[i][1]}年{qr_list[i][2]}月{qr_list[i][3]}次"
            qr_ws[f"C{c}"].font = openpyxl.styles.Font(size=18)

            c = 9+(i*gyo)
            qr_ws[f"C{c}"] = f"{qr_list[i][4]}"
            qr_ws[f"C{c}"].font = openpyxl.styles.Font(size=28)

            c = 3+(i*gyo)
            qr_ws.add_image(img_to_excel, f'H{c}')

            # 下点線
            if (i+1) % 4 != 0:
                c = (i+1)*gyo
                side = Side(style='mediumDashed', color='000000')
                border = Border(bottom=side)
                qr_ws[f'A{c}'].border = border
                qr_ws[f'B{c}'].border = border
                qr_ws[f'C{c}'].border = border
                qr_ws[f'D{c}'].border = border
                qr_ws[f'E{c}'].border = border
                qr_ws[f'F{c}'].border = border
                qr_ws[f'G{c}'].border = border
                qr_ws[f'H{c}'].border = border
                qr_ws[f'I{c}'].border = border
                qr_ws[f'J{c}'].border = border
                qr_ws[f'K{c}'].border = border

        # 保存
        qr_wb.save(wb)

        # ファイルを読み込む
        with open(wb, 'rb') as file:
            filedata = file.read()

        return (filedata, filename)

    def main():

        st.set_page_config(
            page_title='本体Gr_製造チェックシート作成', page_icon='move.gif', layout="wide")

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
        st.write('### ①生産計画年月の指定')
        rnen, rgetsu = rireki_read()
        st.write(f'※最後に実行されたのは　{rnen}年{rgetsu}月　です。')
        st.write('')

        # 年月入力欄（年と月であればプルダウンでもよいかもしれない当年前年翌年、１～１２月）
        dt_now = datetime.now(timezone(timedelta(hours=9))) + \
            timedelta(days=32)  # 日本時刻+32日
        dt_nen = int(dt_now.strftime('%Y'))
        dt_tsuki = int(dt_now.strftime('%m'))

        seisan_col1, seisan_col2, seisan_col3, seisan_col4 = st.columns(4)
        with seisan_col1:
            nen = st.selectbox(
                '生産計画年', [dt_nen-1, dt_nen, dt_nen+1], index=1)
        with seisan_col2:
            getsu = st.selectbox('生産計画月', [
                '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], index=dt_tsuki-1)

        dt_nengetsu = str(nen)+str(getsu)
        dt_nengetsu = dt_nengetsu[2:6]  # YYMM

        # 水平線
        st.divider()

        # 処理
        st.write('### ②帳票作成処理の実行')
        with st.popover("帳票作成実行"):
            st.markdown(f'''【確認】　実行年月：{str(nen)}年{str(getsu)}月  
                    **この操作を実行してもよろしいですか？**''')
            if st.button("実行"):
                if ((rnen == nen) and (int(rgetsu) >= int(getsu))) or (rnen > nen):
                    st.write('エラー：処理実行済の生産年月が指定されています。')

                elif ((rnen == nen) and ((int(getsu)-int(rgetsu)) > 1)) or ((rnen < nen) and (int(rgetsu)-int(getsu)) < 11) or ((int(nen)-int(rnen)) > 1):
                    st.write('エラー：前回の処理実行から２カ月以上先が指定されています。')
                else:
                    with st.spinner('帳票作成処理　実行中（目安：２～５分）'):
                        # インプット用のデータ作成
                        input_df = input_data_create(int(nen), int(getsu))

                        # DFをcsvにコンバートして出力
                        dt_now = datetime.now(
                            timezone(timedelta(hours=9)))  # 日本時刻
                        csv_name = os.path.dirname(
                            __file__)+"\\work\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_自動帳票作成データ"+".csv"
                        input_df.to_csv(csv_name, index=False,
                                        encoding='CP932')

                        # 履歴csvを更新
                        rireki_write(nen, getsu)

                        # CSVをアップロード
                        data_upload(csv_name, input_df.shape[0])

                        # csv作成完了
                        st.write('帳票作成処理完了')

        # 水平線
        st.divider()
        # 処理
        st.write('### ③カメラ起動用QRコード一覧作成')
        st.write('　※QRコードは何度でも再作成可能です')
        if st.button("QRコード作成処理実行"):
            with st.spinner('QRコード作成処理　実行中'):
                qr_list = qr_create(nen, getsu)
                if len(qr_list) == 0:
                    st.write(f'データ無し　{nen}年{getsu}月は帳票が作成されていません')
                else:
                    filedata, filename = qr_list_create(
                        qr_list, nen, getsu)

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
    # 簡単なエラー処理
    print(e)
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    with open(os.path.dirname(os.path.dirname(__file__))+"\\err\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
        f.write(str(e))
