################################
# 　自動帳票作成の共通モジュール　　#
################################
# インポート
import os
import csv
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import pandas as pd
import sqlite3
import shutil

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


def master_4005file_create():

    # バックアップ
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    if (os.path.isfile(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db')):
        shutil.copy(os.path.dirname(os.path.dirname(__file__))+'\\Database\\amikityousei.db',
                    os.path.dirname(os.path.dirname(__file__))+f"\\Database\\backup\\{dt_now.strftime('%Y%m%d')}_amikityousei.db")

    # 本処理
    dbname = 'amikityousei.db'
    cdb = os.path.dirname(os.path.dirname(__file__))+f'\\Database\\'+dbname
    conn = sqlite3.connect(cdb)
    cur = conn.cursor()

    # csvファイルの作成
    # データベースの値を取得する
    sql = f'select * from hakensyain'
    df = pd.read_sql(sql, con=conn)

    # 取り込み用にデータを整える
    # 表示順(1固定)と、権限グループ（空欄）を追加
    df['表示順'] = 99
    df['権限グループ'] = ""
    df['所属コード'] = 4005
    df = df[["社員コード", "社員氏名", "権限グループ", "表示順", "所属コード", "削除flg"]]
    # 取込用の前２列を追加
    df.insert(0, 'アクション区分', 'M')
    df.insert(0, 'H', 'R')
    # 削除flgが1のレコードは変換
    df.loc[df['削除flg'] == 1, 'アクション区分'] = 'D'
    df = df.drop(columns=['削除flg'])
    df.columns = ['0', '1', '2', '3', '4', '5', '6']

    # ヘッダー部のdfを作成
    head = [["H", "アクション区分", "マスターキー", "マスター名称", "マスター種別", "フィールド型配列", "フィールド名称配列", "画像フィールド名称配列", "本体保存可否", "ダウンロード区分", "保持期間", "有効期限", "表示順", "備考", "レコードキーヘッダ名称", "レコーバリューヘッダ名称", "権限グループ", "ラベルモード", "ラベル", "帳票定義ＩＤ", "入力帳票ＩＤ"],
            ["M", "M", "M_EMPLOYEE", "社員マスタ", "0", "text;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;",
                "所属コード;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;", ";;;;", "1", "0", "0", "", "9000", "社員を管理するマスタです", "番号", "社員名", "4;5;6;9;11", "", "共通マスタ"],
            ["H", "アクション区分", "レコードキー", "バリュー", "権限グループ", "表示順", "F001", "F002", "F003", "F004", "F005", "F006", "F007", "F008", "F009", "F010", "F011", "F012", "F013", "F014", "F015", "F016", "F017", "F018", "F019", "F020", "F021", "F022", "F023", "F024", "F025", "F026", "F027", "F028", "F029", "F030", "F031", "F032", "F033", "F034", "F035", "F036", "F037", "F038", "F039", "F040", "F041", "F042", "F043", "F044", "F045", "F046", "F047", "F048", "F049", "F050", "F051", "F052", "F053", "F054", "F055", "F056", "F057", "F058", "F059", "F060", "F061", "F062", "F063", "F064", "F065", "F066", "F067", "F068", "F069", "F070", "F071", "F072", "F073", "F074", "F075", "F076", "F077", "F078", "F079", "F080", "F081", "F082", "F083", "F084", "F085", "F086", "F087", "F088", "F089", "F090", "F091", "F092", "F093", "F094", "F095", "F096", "F097", "F098", "F099", "F100", "I001", "I002", "I003", "I004", "I005"]]
    dfh = pd.DataFrame(head)
    dfh.columns = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55',
                   '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110']
    # ヘッダー部と結合
    upload_df = pd.concat([dfh, df], axis=0, ignore_index=True)

    # DFをcsvにコンバートして出力
    csv_up_path = r"D:\CustomMaster\CSV_UPLOAD/"
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    csv_name = csv_up_path+"\\" + \
        dt_now.strftime('%Y%m%d%H%M%S')+"_4005派遣社員マスタデータ"+".csv"
    upload_df.to_csv(csv_name, index=False, header=False,
                     encoding='CP932', quoting=csv.QUOTE_ALL)

    # 削除操作ファイルを作成した後、削除flgが1の人は削除する
    cur.execute(f"DELETE FROM hakensyain WHERE 削除flg = ?", (1,))

    conn.commit()


def main():
    master_4005file_create()


if __name__ == '__main__':
    main()
