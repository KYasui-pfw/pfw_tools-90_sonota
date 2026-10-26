"""i-Reporter のチェックシート（帳票）を ConMas Manager の自動帳票作成で作る。

ConMas Manager には API が無いので、ブラウザ（Chrome）を Selenium で動かして
CSV をアップロードしている。待ち時間は件数に比例して長くなる（1件あたり約4秒）。

⚠ 画面の部品の位置（XPath）は ConMas Manager の画面に合わせてある。
  ConMas を更新して画面が変わったら、ここを直す必要がある。
"""

import shutil
import time

import pandas as pd

from . import config, irepo
from .tag_excel import is_plating

# CSV の列（i-Reporter の帳票のクラスター番号）。
#   H=R（データ行の印）, defTopId=帳票定義, S1C1=部品名, S1C2=ロット番号, S1C3=完成部番, S1C4=月次,
#   S1C5=組立番号, S1C6=機種, S1C7=吋, S1C8=G, S1C9=客先名, S1C11=メッキ, S1C644=工程VERSION, S1C643=作成日
CSV_COLUMNS = ["H", "defTopId", "S1C1", "S1C2", "S1C3", "S1C4", "S1C5", "S1C6",
               "S1C7", "S1C8", "S1C9", "S1C11", "S1C644", "S1C643"]
SOURCE_COLUMNS = ["部品名", "ロット番号", "完成部番", "月次", "組立番号", "機種", "吋", "G",
                  "客先名", "ﾒｯｷ", "工程VERSION"]

# 縦横区分（buhin_irepo_mst）。1 = 縦レイアウト（405）、0 = 横レイアウト（406）。
TATE = 1

# 待ち時間（秒）。少ないと取り込みが終わる前に次へ進んでしまう。
WAIT_STEP = 1
WAIT_CONFIRM_PER_ROW = 0.7
WAIT_IMPORT_PER_ROW = 3.3


def estimate_seconds(count):
    """作成にかかるおおよその秒数（画面に目安を出す用）。"""
    return count * 4 + 15


def build_csv(rows):
    """帳票作成用の CSV（DataFrame）を作る。rows は一覧の行（DataFrame）。"""
    def_top_ids = irepo.fetch_latest_def_top_ids()

    df = rows[SOURCE_COLUMNS].copy()
    df.insert(0, "defTopId", [
        def_top_ids[irepo.DEF_TOP_ORG_TATE] if value == TATE else def_top_ids[irepo.DEF_TOP_ORG_YOKO]
        for value in rows["縦横区分"]
    ])
    df["ﾒｯｷ"] = ["メッキ" if is_plating(value) else "" for value in df["ﾒｯｷ"]]
    df["作成日"] = f"{config.now():%Y%m%d}"
    df.insert(0, "H", "R")
    df.columns = CSV_COLUMNS
    return df


def create_reports(rows):
    """一覧の行（DataFrame）から i-Reporter の帳票を作る。0行なら何もしない。

    Returns:
        作った帳票の数
    """
    if rows.empty:
        return 0

    config.CSV_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = config.CSV_DIR / f"{config.now():%Y%m%d%H%M%S}_自動帳票作成データ.csv"
    build_csv(rows).to_csv(csv_path, index=False, encoding="cp932")
    upload_csv(csv_path, len(rows))
    return len(rows)


def upload_csv(csv_path, row_count):
    """ConMas Manager に CSV をアップロードして帳票を作る（Chrome を自動操作する）。

    終わったら、画面の記録（スクリーンショット）を work/sumi/png に、
    CSV を csv/sumi に移す（あとで「何を作ったか」を追えるように）。
    """
    # 画面操作の部品は使うときだけ読み込む（夜間処理以外では Selenium が要らないため）。
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.select import Select

    def click(xpath):
        driver.find_element(By.XPATH, xpath).click()

    def choose(xpath, value):
        element = driver.find_element(By.XPATH, xpath)
        element.click()
        Select(element).select_by_value(value)

    def screenshot(suffix):
        config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        name = f"{config.now():%Y%m%d%H%M%S}_作成{csv_path.stem}_{suffix}.png"
        driver.save_screenshot(str(config.SCREENSHOT_DIR / name))

    def_top_ids = irepo.fetch_latest_def_top_ids()
    driver = webdriver.Chrome()
    try:
        # ログイン（自動帳票作成の画面を直接開く）
        driver.get(config.CONMAS_URL)
        time.sleep(WAIT_STEP)
        driver.find_element(By.XPATH, '//*[@id="UserName"]').send_keys(config.CONMAS_USER)
        driver.find_element(By.XPATH, '//*[@id="Password"]').send_keys(config.CONMAS_PASSWORD)
        click('//*[@id="image-login_btn"]')
        time.sleep(WAIT_STEP)

        # 公開中の帳票定義だけを出し、縦・横の最新の定義にチェックを付ける
        choose('//*[@id="PublicStatus"]', "2")
        time.sleep(WAIT_STEP * 3)
        for org in (irepo.DEF_TOP_ORG_TATE, irepo.DEF_TOP_ORG_YOKO):
            click(f'//input[@id="Cbx" and @value="{def_top_ids[org]}" and @name="Cbx"]')
            time.sleep(WAIT_STEP)

        # 次へ → 簡易CSV・モード1 を選んで CSV を渡す
        click('//*[@id="FiltersTable"]/tbody/tr/td[2]/a[2]')
        time.sleep(WAIT_STEP)
        choose('//*[@id="type"]', "csvSimple")
        time.sleep(WAIT_STEP)
        choose('//*[@id="defaultMode"]', "1")
        time.sleep(WAIT_STEP)
        driver.find_element(By.XPATH, '//*[@id="file1"]').send_keys(str(csv_path))
        time.sleep(WAIT_STEP)

        # 確認 → 取り込み。件数に比例して待つ
        click('//*[@id="DetailSection"]/div/div[1]/input')
        time.sleep(int(row_count * WAIT_CONFIRM_PER_ROW))
        screenshot("SC1")
        click('//*[@id="DetailSection"]/div/div[2]/input')
        time.sleep(int(row_count * WAIT_IMPORT_PER_ROW))
        screenshot("SC2")
        time.sleep(WAIT_STEP)
    finally:
        driver.quit()

    config.CSV_DONE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(csv_path), str(config.CSV_DONE_DIR / f"{config.now():%Y%m%d%H%M%S}_作成{csv_path.name}"))


def rows_for_single_report(values):
    """1件ぶんの帳票作成用の行（DataFrame）を作る（手入力発行・チェックシート再作成）。"""
    return pd.DataFrame([values])
