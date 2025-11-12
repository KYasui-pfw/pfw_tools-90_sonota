import pandas as pd
import os
import cx_Oracle
from datetime import datetime

def ej_data_get(sql):
    """EJシステム（Oracle Database）に接続してSQLを実行する"""
    try:
        # EJシステム接続情報
        host = '172.17.107.102'
        port = '1521'
        service_name = 'EXPJ'
        username = 'EXPJ2'
        password = 'EXPJ2'

        # 接続文字列
        connection_string = f"{username}/{password}@{host}:{port}/{service_name}"

        # データベース接続
        connection = cx_Oracle.connect(connection_string)

        # SQLを実行してDataFrameに変換
        df = pd.read_sql(sql, connection)

        # 接続を閉じる
        connection.close()

        return df

    except Exception as e:
        print(f"EJシステムへの接続でエラーが発生しました: {str(e)}")
        raise

# ファイルパス設定
BASE_DIR = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成"
WORK_DIR = os.path.join(BASE_DIR, "work")
WORK_FILE = os.path.join(WORK_DIR, "13_品目構成work.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 出力ディレクトリ作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 13_品目構成work.csv読み込み
print("=== M0910品目仕入単価マスタ作成処理 ===")
print("13_品目構成work.csv を読み込んでいます...")
work_df = pd.read_csv(WORK_FILE, encoding='utf-8-sig')
print(f"品目構成workデータ件数: {len(work_df)}")

# 必要な前工程のみを取得するためのリスト作成
unique_zenkatei = work_df['前工程'].dropna().unique()
zenkatei_list = [str(x) for x in unique_zenkatei if str(x) != 'nan']
print(f"処理対象前工程種別: {len(zenkatei_list)}種類")

# EJシステムからSRCD用データを取得（M_PUCH_UNIT_COST）- バッチ処理
print("\n=== EJシステム（M_PUCH_UNIT_COST）データ取得 ===")
try:
    srcd_all_list = []
    if len(zenkatei_list) > 0:
        # Oracle IN句制限（1000件）に対応するためバッチ処理
        batch_size = 900  # Oracle制限より少し小さく設定
        for i in range(0, len(zenkatei_list), batch_size):
            batch = zenkatei_list[i:i + batch_size]
            zenkatei_sql_list = "','".join(batch)
            srcd_sql = f"""
            SELECT ITEM_CD, VEND_CD, UNIT_COST, EFF_PHASE_IN_DATE, PUCH_SIZE
            FROM EXPJ2.M_PUCH_UNIT_COST
            WHERE ITEM_CD IN ('{zenkatei_sql_list}')
            ORDER BY ITEM_CD, EFF_PHASE_IN_DATE DESC
            """
            batch_df = ej_data_get(srcd_sql)
            srcd_all_list.append(batch_df)
            print(f"バッチ{i//batch_size + 1}: {len(batch)}件の前工程 -> {len(batch_df)}行取得")

        # 全バッチを結合
        if srcd_all_list:
            srcd_df = pd.concat(srcd_all_list, ignore_index=True)
        else:
            srcd_df = pd.DataFrame()
        print(f"SRCD用データ取得（全バッチ合計）: {len(srcd_df)}行")
    else:
        srcd_df = pd.DataFrame()
        print("対象となる前工程がありません")

    # 全レコードを使用（日付絞り込みなし）
    srcd_all = srcd_df.copy()

    # 高速検索用辞書作成：ITEM_CDをキーとしてレコードリストを保持
    srcd_records_dict = {}
    for _, record in srcd_all.iterrows():
        item_cd = record['ITEM_CD']
        if item_cd not in srcd_records_dict:
            srcd_records_dict[item_cd] = []
        srcd_records_dict[item_cd].append(record.to_dict())

    print(f"全レコード使用: {len(srcd_all)}件（重複含む）")
    print(f"SRCD辞書作成（M_PUCH_UNIT_COST）: {len(srcd_records_dict)}種類")

    # M_PUCH_UNIT_COST_HテーブルからPUCH_PRIORITY_REF_NOを取得 - バッチ処理
    print("\n=== EJシステム（M_PUCH_UNIT_COST_H）データ取得 ===")
    try:
        cost_h_all_list = []
        if len(zenkatei_list) > 0:
            # Oracle IN句制限（1000件）に対応するためバッチ処理
            for i in range(0, len(zenkatei_list), batch_size):
                batch = zenkatei_list[i:i + batch_size]
                zenkatei_sql_list = "','".join(batch)
                cost_h_sql = f"""
                SELECT ITEM_CD, VEND_CD, PUCH_PRIORITY_REF_NO
                FROM EXPJ2.M_PUCH_UNIT_COST_H
                WHERE ITEM_CD IN ('{zenkatei_sql_list}')
                """
                batch_df = ej_data_get(cost_h_sql)
                cost_h_all_list.append(batch_df)
                print(f"バッチ{i//batch_size + 1}（M_PUCH_UNIT_COST_H）: {len(batch)}件の前工程 -> {len(batch_df)}行取得")

            # 全バッチを結合
            if cost_h_all_list:
                cost_h_df = pd.concat(cost_h_all_list, ignore_index=True)
            else:
                cost_h_df = pd.DataFrame()
            print(f"M_PUCH_UNIT_COST_Hデータ取得（全バッチ合計）: {len(cost_h_df)}行")
        else:
            cost_h_df = pd.DataFrame()
            print("対象となる前工程がありません（M_PUCH_UNIT_COST_H）")

        # ITEM_CD + VEND_CDで辞書作成
        if len(cost_h_df) > 0:
            cost_h_df['COMPOSITE_KEY'] = cost_h_df['ITEM_CD'].astype(str) + '|' + cost_h_df['VEND_CD'].astype(str)
            cost_h_dict = dict(zip(cost_h_df['COMPOSITE_KEY'], cost_h_df['PUCH_PRIORITY_REF_NO']))
        else:
            cost_h_dict = {}
        print(f"M_PUCH_UNIT_COST_H辞書作成: {len(cost_h_dict)}件")
    except Exception as e:
        print(f"M_PUCH_UNIT_COST_Hデータ取得エラー: {e}")
        cost_h_dict = {}

except Exception as e:
    print(f"SRCD用データ取得エラー: {e}")
    srcd_records_dict = {}
    cost_h_dict = {}

# フォールバック用: T_RLSD_PUCH_ODRからSRCD用データを取得 - バッチ処理
print("\n=== EJシステム（T_RLSD_PUCH_ODR）フォールバックデータ取得 ===")
try:
    fallback_all_list = []
    if len(zenkatei_list) > 0:
        # Oracle IN句制限（1000件）に対応するためバッチ処理
        for i in range(0, len(zenkatei_list), batch_size):
            batch = zenkatei_list[i:i + batch_size]
            zenkatei_sql_list = "','".join(batch)
            fallback_sql = f"""
            SELECT ITEM_CD, VEND_CD, PUCH_ODR_DLV_DATE, UNIT_COST
            FROM EXPJ2.T_RLSD_PUCH_ODR
            WHERE ITEM_CD IS NOT NULL AND VEND_CD IS NOT NULL
            AND ITEM_CD IN ('{zenkatei_sql_list}')
            ORDER BY ITEM_CD, PUCH_ODR_DLV_DATE DESC
            """
            batch_df = ej_data_get(fallback_sql)
            fallback_all_list.append(batch_df)
            print(f"バッチ{i//batch_size + 1}（T_RLSD_PUCH_ODR）: {len(batch)}件の前工程 -> {len(batch_df)}行取得")

        # 全バッチを結合
        if fallback_all_list:
            fallback_df = pd.concat(fallback_all_list, ignore_index=True)
        else:
            fallback_df = pd.DataFrame()
        print(f"フォールバック用データ取得（全バッチ合計）: {len(fallback_df)}行")
    else:
        fallback_df = pd.DataFrame()
        print("対象となる前工程がありません（T_RLSD_PUCH_ODR）")

    # 最新日付のレコードを抽出（同日付が複数ある場合はすべて保持）
    if len(fallback_df) > 0:
        fallback_max_dates = fallback_df.groupby('ITEM_CD')['PUCH_ODR_DLV_DATE'].max().reset_index()
        fallback_latest = fallback_df.merge(fallback_max_dates, on=['ITEM_CD', 'PUCH_ODR_DLV_DATE'])

        # 高速検索用辞書作成：ITEM_CDをキーとしてレコードリストを保持
        fallback_records_dict = {}
        for _, record in fallback_latest.iterrows():
            item_cd = record['ITEM_CD']
            if item_cd not in fallback_records_dict:
                fallback_records_dict[item_cd] = []
            fallback_records_dict[item_cd].append(record.to_dict())

        print(f"フォールバック最新日付で重複除去: {len(fallback_latest)}件")
        print(f"フォールバック辞書作成: {len(fallback_records_dict)}種類")
    else:
        fallback_records_dict = {}
except Exception as e:
    print(f"フォールバック用データ取得エラー: {e}")
    fallback_records_dict = {}

# 各品目構成workレコードに対してSRCD/PRICE取得処理
print("\n=== 品目構成workデータ処理開始 ===")
m0910_data = []

for idx, row in work_df.iterrows():
    zenkatei = str(row['前工程']) if pd.notna(row['前工程']) else ''

    # EJシステムから優先順位に基づくSRCD/PRICE取得
    m_puch_records = srcd_records_dict.get(zenkatei, [])
    source = "未取得"

    if m_puch_records:
        # PUCH_PRIORITY_REF_NOで最優先レコードを選定
        expanded_row = None

        for puch_record in m_puch_records:
            composite_key = f"{puch_record['ITEM_CD']}|{puch_record['VEND_CD']}"
            priority_ref = cost_h_dict.get(composite_key)

            if priority_ref is not None:
                expanded_row = puch_record.copy()
                expanded_row['PUCH_PRIORITY_REF_NO'] = priority_ref
                source = "M_PUCH_UNIT_COST_H/M_PUCH_UNIT_COST"
                break

        # M_PUCH_UNIT_COST_H連携で見つからない場合、T_RLSD_PUCH_ODRフォールバック
        if expanded_row is None:
            fallback_records = fallback_records_dict.get(zenkatei, [])
            if fallback_records:
                fallback_record = fallback_records[0]  # 最新日付レコード
                expanded_row = {
                    'ITEM_CD': fallback_record['ITEM_CD'],
                    'VEND_CD': fallback_record['VEND_CD'],
                    'UNIT_COST': fallback_record['UNIT_COST'],
                    'EFF_PHASE_IN_DATE': None,
                    'PUCH_SIZE': None,
                    'PUCH_PRIORITY_REF_NO': None
                }
                source = "T_RLSD_PUCH_ODR（フォールバック）"

        if expanded_row:
            # VALDTFの処理（03と同じロジック）：EJのEFF_PHASE_IN_DATEを使用
            valdtf_value = expanded_row.get('EFF_PHASE_IN_DATE', '')
            if valdtf_value and valdtf_value != '':
                try:
                    # 時刻部分を削除してYYYY-MM-DD形式をYYYY/MM/DD形式に変換
                    valdtf_str = str(valdtf_value)
                    if ' ' in valdtf_str:
                        valdtf_str = valdtf_str.split(' ')[0]  # 時刻部分を削除
                    if '-' in valdtf_str:
                        valdtf_formatted = valdtf_str.replace('-', '/')
                    else:
                        valdtf_formatted = valdtf_str
                except:
                    valdtf_formatted = str(valdtf_value)
            else:
                valdtf_formatted = ''

            # VALQTYの処理（03と同じロジック）：EJのPUCH_SIZEを使用、1の場合は0に変換
            valqty_value = expanded_row.get('PUCH_SIZE', 0)
            if valqty_value is not None:
                valqty_formatted = float(valqty_value)
                # 1の場合は0に変換
                if valqty_formatted == 1.0:
                    valqty_formatted = 0.0
            else:
                valqty_formatted = 0.0

            # M0910レコード作成
            m0910_record = {
                'HMCD': str(row['前工程']) if pd.notna(row['前工程']) else '',
                'BUCD': '100',
                'SRCD': str(expanded_row['VEND_CD']) if expanded_row['VEND_CD'] is not None else '',
                'UNIT': 'PC',
                'VALDTF': valdtf_formatted,
                'VALQTY': valqty_formatted,
                'PRICE': float(expanded_row['UNIT_COST']) if expanded_row['UNIT_COST'] is not None else 0.0,
                'NOTE': '',
                'SYOKAIHINKBN': '1'
            }

            m0910_data.append(m0910_record)
    else:
        # EJ未取得の場合は空値でレコード作成（03と同じロジック）
        valdtf_formatted = ''  # EJ未取得時は空文字
        valqty_formatted = 0.0  # EJ未取得時は0（変換不要）

        m0910_record = {
            'HMCD': str(row['前工程']) if pd.notna(row['前工程']) else '',
            'BUCD': '100',
            'SRCD': '',
            'UNIT': 'PC',
            'VALDTF': valdtf_formatted,
            'VALQTY': valqty_formatted,
            'PRICE': 0.0,
            'NOTE': '',
            'SYOKAIHINKBN': '1'
        }

        m0910_data.append(m0910_record)

print(f"M0910データ作成完了: {len(m0910_data)}件")

# DataFrameを作成
m0910_df = pd.DataFrame(m0910_data)

# 出力ファイルのパス
output_file = os.path.join(OUTPUT_DIR, "M0910_品目仕入単価マスタ.csv")

# CSVファイルに出力（ヘッダー付き）
m0910_df.to_csv(output_file, encoding='utf-8-sig', index=False)

print(f"出力完了: {output_file}")
print(f"出力データ: {len(m0910_df)}行")

# 出力内容のサンプルを表示
print("\n=== 出力データサンプル（最初の10行） ===")
print(m0910_df.head(10).to_string(index=False))

# 処理統計を表示
print(f"\n=== 処理統計 ===")
print(f"処理対象の品目数（HMCD）: {m0910_df['HMCD'].nunique()}件")
print(f"総レコード数: {len(m0910_df)}件")

# HMCDごとの件数を表示（上位10件）
hmcd_counts = m0910_df['HMCD'].value_counts().head(10)
print(f"\n=== HMCDごとのレコード数（上位10件） ===")
for hmcd, count in hmcd_counts.items():
    print(f"  {hmcd}: {count}件")