import pandas as pd
import os
import cx_Oracle

def create_ktcd(zenkatei):
    """
    前工程からKTCDを作成する関数
    03_create_item_process_master.pyと同様の処理
    """
    # 前工程からKTCDを抽出（最初のハイフンまでの文字列）
    zenkatei_str = str(zenkatei) if pd.notna(zenkatei) else ''

    if '-' in zenkatei_str:
        ktcd = zenkatei_str.split('-')[0]  # ハイフンで分割して最初の部分を取得
    else:
        ktcd = zenkatei_str  # ハイフンがない場合はそのまま

    # KTCDの変換処理
    if ktcd == "A0":
        ktcd = "AO"
    elif ktcd in ["PA1", "PA2"]:
        ktcd = "PA"

    return ktcd

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
WORK_FILE = os.path.join(WORK_DIR, "14_品目工程work.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# 出力ディレクトリ作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 14_品目工程work.csv読み込み
print("=== MK020品目仕入工程単価マスタ作成処理 ===")
print("14_品目工程work.csv を読み込んでいます...")
work_df = pd.read_csv(WORK_FILE, encoding='utf-8-sig')
print(f"品目工程workデータ件数: {len(work_df)}")

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

        print(f"フォールバック最新日付レコード抽出: {len(fallback_latest)}件（重複含む）")
        print(f"フォールバック辞書作成: {len(fallback_records_dict)}種類")
    else:
        fallback_records_dict = {}
        print("フォールバック用データなし")

except Exception as e:
    print(f"フォールバック用データ取得エラー: {e}")
    fallback_records_dict = {}

# PEFINソート.csvを読み込んでPEFIN削除対象を取得
print("\n=== PEFINソート.csv前工程情報取得 ===")
pefin_zenkatei_dict = {}
try:
    pefin_file = os.path.join(BASE_DIR, "input", "PEFINソート.csv")
    pefin_df = None
    for encoding in ['utf-8', 'shift_jis', 'cp932']:
        try:
            pefin_df = pd.read_csv(pefin_file, encoding=encoding)
            print(f"PEFINソート.csv読み込み成功 (エンコーディング: {encoding})")
            break
        except UnicodeDecodeError:
            continue

    if pefin_df is not None and len(pefin_df.columns) >= 2:
        kansei_col = pefin_df.columns[0]  # 完成部番
        zenkatei_col = pefin_df.columns[1]  # 前工程

        for _, row in pefin_df.iterrows():
            kansei_bango = str(row[kansei_col]) if pd.notna(row[kansei_col]) else ''
            zenkatei_value = row[zenkatei_col] if pd.notna(row[zenkatei_col]) else None
            if kansei_bango and zenkatei_value is not None:
                pefin_zenkatei_dict[kansei_bango] = int(zenkatei_value)

        print(f"PEFINソート前工程情報: {len(pefin_zenkatei_dict)}件")
    else:
        print("PEFINソート.csvの読み込みに失敗")
except Exception as e:
    print(f"PEFINソート.csv読み込みエラー: {e}")
    pefin_zenkatei_dict = {}

# 品目工程workデータを前工程値でSRCDを判定
print("\n=== 品目工程workデータのSRCD判定処理（前工程値ベース） ===")
ej_found_list = []
ej_not_found_list = []

excluded_count_hmcd = 0
excluded_count_pefin = 0

for idx, row in work_df.iterrows():
    zenkatei = str(row['前工程']) if pd.notna(row['前工程']) else ''
    kansei_bango = str(row['完成部番']) if pd.notna(row['完成部番']) else ''

    # 例外処理1: 特定のHMCDは処理対象外とする
    if kansei_bango in ['KS91-03006BA', 'KD64-00202BA']:
        excluded_count_hmcd += 1
        if idx < 10:
            print(f"  [除外1] {kansei_bango} - 特定HMCD除外")
        continue

    # 例外処理2: 前工程=0のPEFIN行を削除
    if zenkatei.startswith('PEFIN'):
        pefin_zenkatei = pefin_zenkatei_dict.get(kansei_bango)
        if pefin_zenkatei == 0:
            excluded_count_pefin += 1
            if idx < 10:
                print(f"  [除外2] {kansei_bango} - PEFIN行削除（前工程=0）")
            continue

    # M_PUCH_UNIT_COSTから前工程値に該当する全レコードを取得（辞書検索）
    m_puch_records = srcd_records_dict.get(zenkatei, [])

    if len(m_puch_records) > 0:
        # M_PUCH_UNIT_COSTで見つかった場合、各レコードに対して行を展開
        source = "M_PUCH_UNIT_COST"
        for puch_record in m_puch_records:
            # 元の行データをコピー
            expanded_row = row.copy()
            # M_PUCH_UNIT_COSTの情報を追加
            expanded_row['M_ITEM_CD'] = puch_record['ITEM_CD']
            expanded_row['M_EFF_PHASE_IN_DATE'] = puch_record['EFF_PHASE_IN_DATE']
            expanded_row['M_PUCH_SIZE'] = puch_record['PUCH_SIZE']
            expanded_row['M_VEND_CD'] = puch_record['VEND_CD']

            # M_PUCH_UNIT_COST_HからPUCH_PRIORITY_REF_NOを取得
            composite_key = f"{puch_record['ITEM_CD']}|{puch_record['VEND_CD']}"
            expanded_row['M_PUCH_PRIORITY_REF_NO'] = cost_h_dict.get(composite_key, '')

            # KTCDを作成（前工程から抽出）
            expanded_row['KTCD'] = create_ktcd(zenkatei)

            # UNIT_COSTを追加
            expanded_row['UNIT_COST'] = puch_record.get('UNIT_COST', 0)

            ej_found_list.append(expanded_row)

            # デバッグ用ログ（最初の10件のみ）
            if idx < 10:
                priority_ref = expanded_row['M_PUCH_PRIORITY_REF_NO']
                print(f"  {kansei_bango} - 前工程: {zenkatei} -> ITEM_CD: {puch_record['ITEM_CD']}, VEND_CD: {puch_record['VEND_CD']}, SIZE: {puch_record['PUCH_SIZE']}, PRIORITY: {priority_ref} (from {source})")
    else:
        # T_RLSD_PUCH_ODRフォールバックを確認（辞書検索）
        fallback_records = fallback_records_dict.get(zenkatei, [])

        if len(fallback_records) > 0:
            # T_RLSD_PUCH_ODRで見つかった場合、各レコードに対して行を展開
            source = "T_RLSD_PUCH_ODR"
            for fallback_record in fallback_records:
                # 元の行データをコピー
                expanded_row = row.copy()
                # M_PUCH_UNIT_COSTの情報は空欄（T_RLSD_PUCH_ODRにはPUCH_SIZEなし）
                expanded_row['M_ITEM_CD'] = ''
                expanded_row['M_EFF_PHASE_IN_DATE'] = ''
                expanded_row['M_PUCH_SIZE'] = ''
                expanded_row['M_VEND_CD'] = ''
                expanded_row['M_PUCH_PRIORITY_REF_NO'] = ''

                # KTCDを作成（前工程から抽出）
                expanded_row['KTCD'] = create_ktcd(zenkatei)

                # UNIT_COSTを追加（T_RLSD_PUCH_ODRのUNIT_COSTを使用）
                expanded_row['UNIT_COST'] = fallback_record.get('UNIT_COST', 0)

                ej_found_list.append(expanded_row)

                # デバッグ用ログ（最初の10件のみ）
                if idx < 10:
                    print(f"  {kansei_bango} - 前工程: {zenkatei} -> フォールバック取得 (from {source})")
        else:
            # どちらでも見つからない場合
            expanded_row = row.copy()
            # M_PUCH_UNIT_COSTの情報は空欄
            expanded_row['M_ITEM_CD'] = ''
            expanded_row['M_EFF_PHASE_IN_DATE'] = ''
            expanded_row['M_PUCH_SIZE'] = ''
            expanded_row['M_VEND_CD'] = ''
            expanded_row['M_PUCH_PRIORITY_REF_NO'] = ''

            # KTCDを作成（前工程から抽出）
            expanded_row['KTCD'] = create_ktcd(zenkatei)

            # UNIT_COSTを追加（見つからない場合は0）
            expanded_row['UNIT_COST'] = 0

            ej_not_found_list.append(expanded_row)

            # デバッグ用ログ（最初の10件のみ）
            if idx < 10:
                print(f"  {kansei_bango} - 前工程: {zenkatei} -> SRCD: None (from None)")

# DataFrameの変換は出力時に行う（列順序調整のため）

print(f"\n除外処理結果:")
print(f"  特定HMCD除外: {excluded_count_hmcd}件")
print(f"  PEFIN行削除: {excluded_count_pefin}件")
print(f"  合計除外: {excluded_count_hmcd + excluded_count_pefin}件")
print(f"\n前工程値ベースでEJからSRCD取得可能: {len(ej_found_list)}件")
print(f"前工程値ベースでEJからSRCD取得不可: {len(ej_not_found_list)}件")
print(f"処理対象総件数: {len(ej_found_list) + len(ej_not_found_list)}件")

# MK020品目仕入工程単価マスタ形式でデータを作成（AとBのみ：EJ取得可能データ）
print(f"\n=== MK020品目仕入工程単価マスタ作成 ===")

mk020_data = []
for record in ej_found_list:
    # 日付をYYYY/MM/DD形式に変換
    valdtf_value = record.get('M_EFF_PHASE_IN_DATE', '')
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

    # VALQTYの処理：M_PUCH_SIZEを使用、1の場合は0に変換
    valqty_value = float(record.get('M_PUCH_SIZE', 0))
    if valqty_value == 1.0:
        valqty_value = 0.0

    mk020_record = {
        'OYAHMCD': str(record.get('完成部番', '')),  # 完成部番
        'KTCD': str(record.get('KTCD', '')),  # KTCD
        'BUCD': '100',  # 固定値"100"
        'SRCD': str(record.get('M_VEND_CD', '')),  # M_VEND_CD
        'VALDTF': valdtf_formatted,  # M_EFF_PHASE_IN_DATE（YYYY/MM/DD形式）
        'VALQTY': valqty_value,  # M_PUCH_SIZE（1の場合は0に変換）
        'PRICE': float(record.get('UNIT_COST', 0)),  # UNIT_COST
        'NOTE': str(record.get('前工程', '')),  # 前工程
        'SYOKAIHINKBN': '2'  # 固定値"2"
    }
    mk020_data.append(mk020_record)

print(f"MK020データ作成: {len(mk020_data)}件")

# DataFrameを作成
mk020_df = pd.DataFrame(mk020_data)

# 出力ファイル
output_file = os.path.join(OUTPUT_DIR, "MK020_品目仕入工程単価マスタ.csv")
mk020_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n[OK] {output_file} に出力しました")
print(f"出力データ: {len(mk020_df)}行")

# サンプルデータ表示
print(f"\n=== 出力データサンプル（最初の5行） ===")
print(mk020_df.head(5).to_string(index=False))

print("\n処理完了")