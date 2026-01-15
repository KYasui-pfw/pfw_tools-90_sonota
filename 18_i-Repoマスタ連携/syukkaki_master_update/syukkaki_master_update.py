import os
import csv
import pandas as pd
from datetime import datetime, timedelta, timezone
import oracledb

csv_dir_path = r"D:\CustomMaster\サービスレポート\xlsb_2019\1100_サービスレポート_出荷機マスタ\ダウンロードCSV/"
csv_up_path = r"D:\CustomMaster\CSV_UPLOAD/"


def df_csv_cnv1(df, filename='自動_'):
    # DFをcsvにコンバートして出力
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    csv_name = csv_dir_path+"\\"+filename + \
        dt_now.strftime('%Y%m%d%H%M%S')+".csv"
    df.to_csv(csv_name, index=False, encoding='CP932')


def df_csv_cnv2(df):
    # DFをcsvにコンバートして出力
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    csv_name = csv_up_path+"\\" + \
        dt_now.strftime('%Y%m%d%H%M%S')+"_出荷機マスタデータ"+".csv"
    df.to_csv(csv_name, index=False, header=False,
              encoding='CP932', quoting=csv.QUOTE_ALL)


try:

    # 現在の年月を取得
    today = datetime.today()
    kaishi = f"{today.year % 100}{today.month:02d}"

    # 翌月を計算
    next_month = today.replace(day=1) + timedelta(days=32)
    syuuryou = f"{next_month.year % 100}{next_month.month:02d}"

    # Oracle Clientの初期化
    lib_dir = r"C:\Oracle\instantclient_21_9"
    oracledb.init_oracle_client(lib_dir=lib_dir)

    # Oracle DB接続定義
    dsn_tns = oracledb.makedsn('172.17.107.102', '1521', service_name='EXPJ')
    connection = oracledb.connect(user='EXPJ2', password='EXPJ2', dsn=dsn_tns)

    # SQLクエリ
    sql = f"""SELECT V_SEISAN_KIKAI_GETSUJI_U_1.JOB_ODR_CD, V_SEISAN_KIKAI_GETSUJI_U_1.KIBAN, 
                V_SEISAN_KIKAI_GETSUJI_U_1.SHIP_DATE, V_SEISAN_KIKAI_GETSUJI_U_1.PRODUCT_MONTH, 
                V_SEISAN_KIKAI_GETSUJI_U_1.GETSUJI, V_SEISAN_KIKAI_GETSUJI_U_1.MODEL_NAME, 
                V_SEISAN_KIKAI_GETSUJI_U_1.INCH, V_SEISAN_KIKAI_GETSUJI_U_1.GAUGE, V_SEISAN_KIKAI_GETSUJI_U_1.CUT_QTY, 
                V_SEISAN_KIKAI_GETSUJI_U_1.CUST_U_CD, V_SEISAN_KIKAI_GETSUJI_U_1.CUST_U_NAME1, 
                V_SEISAN_KIKAI_GETSUJI_U_1.ADDRESS, V_SEISAN_KIKAI_GETSUJI_U_1.PUNCTUAL_SHIP_DATE, 
                V_SEISAN_KIKAI_GETSUJI_U_1.DESINATED_DLV_DATE, V_SEISAN_KIKAI_GETSUJI_U_1.CUST_SECTION_NAME, 
                V_SEISAN_KIKAI_GETSUJI_U_1.REMARKS, V_SEISAN_KIKAI_GETSUJI_U_1.CUST_ODR_NO, 
                V_SEISAN_KIKAI_GETSUJI_U_1.ODR_CMPLT_FLG FROM V_SEISAN_KIKAI_GETSUJI_U V_SEISAN_KIKAI_GETSUJI_U_1 
                WHERE V_SEISAN_KIKAI_GETSUJI_U_1.PRODUCT_MONTH BETWEEN '{kaishi}' AND '{syuuryou}'"""
    df = pd.read_sql(sql, con=connection)
    df = df[df['KIBAN'].notna() & (df['KIBAN'] != "")]  # 20250409追加
    df_csv_cnv1(df)

    # 接続を閉じる
    connection.close()

    # 取り込み用にデータを整える
    # 表示順(1固定)と、権限グループ（空欄）を追加
    df['表示順'] = 1
    df['権限グループ'] = ""
    df = df[["KIBAN", "JOB_ODR_CD", "権限グループ", "表示順",
             "MODEL_NAME", "INCH", "GAUGE", "CUST_U_CD"]]
    # 取込用の前２列を追加
    df.insert(0, 'アクション区分', 'M')
    df.insert(0, 'H', 'R')
    df.columns = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    # ヘッダー部のdfを作成
    head = [["H", "アクション区分", "マスターキー", "マスター名称", "マスター種別", "フィールド型配列", "フィールド名称配列", "画像フィールド名称配列", "本体保存可否", "ダウンロード区分", "保持期間", "有効期限", "表示順", "備考", "レコードキーヘッダ名称", "レコーバリューヘッダ名称", "権限グループ", "ラベルモード", "ラベル", "帳票定義ＩＤ", "入力帳票ＩＤ"],
            ["M", "M", "M_Shukkaki", "出荷機マスタ", "0", "text;text;text;text;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;",
                "機種名;インチ;ゲージ;客先コード;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;", "画像０１;画像０2;画像０3;;", "1", "1", "43200", "", "1100", "", "機番", "組立No", "4;6;9;11", "0", "サービスレポート", "", ""],
            ["H", "アクション区分", "レコードキー", "バリュー", "権限グループ", "表示順", "F001", "F002", "F003", "F004", "F005", "F006", "F007", "F008", "F009", "F010", "F011", "F012", "F013", "F014", "F015", "F016", "F017", "F018", "F019", "F020", "F021", "F022", "F023", "F024", "F025", "F026", "F027", "F028", "F029", "F030", "F031", "F032", "F033", "F034", "F035", "F036", "F037", "F038", "F039", "F040", "F041", "F042", "F043", "F044", "F045", "F046", "F047", "F048", "F049", "F050", "F051", "F052", "F053", "F054", "F055", "F056", "F057", "F058", "F059", "F060", "F061", "F062", "F063", "F064", "F065", "F066", "F067", "F068", "F069", "F070", "F071", "F072", "F073", "F074", "F075", "F076", "F077", "F078", "F079", "F080", "F081", "F082", "F083", "F084", "F085", "F086", "F087", "F088", "F089", "F090", "F091", "F092", "F093", "F094", "F095", "F096", "F097", "F098", "F099", "F100", "I001", "I002", "I003", "I004", "I005"]]
    dfh = pd.DataFrame(head)
    dfh.columns = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55',
                   '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110']
    # ヘッダー部と結合
    upload_df = pd.concat([dfh, df], axis=0, ignore_index=True)

    df_csv_cnv2(upload_df)

except Exception as e:
    # 簡単なエラー処理
    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    with open(os.path.dirname(__file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_err"+".txt", mode='w') as f:
        f.write(str(e))
