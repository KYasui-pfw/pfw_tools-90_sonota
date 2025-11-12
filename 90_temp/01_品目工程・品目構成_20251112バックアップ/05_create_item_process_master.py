import pandas as pd
import os
from datetime import datetime
import cx_Oracle

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

def main():
    """
    14_品目工程work.csvを読み込んで、M0840品目工程マスタのレイアウトでCSV出力する
    """
    # ディレクトリパスの設定
    input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\work"
    output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\output"
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=== 品目工程マスタ(M0840)出力処理 ===")
    
    # 入力ファイルのパス
    input_file = os.path.join(input_dir, "14_品目工程work.csv")
    
    # ファイル存在確認
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません - {input_file}")
        return
    
    # CSVファイルを読み込み
    print(f"読み込み中: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"入力データ: {len(df)}行")
    
    # M0410工程マスタを読み込み
    print("\n=== M0410工程マスタ読み込み ===")
    m0410_file = os.path.join(r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input", "M0410_工程マスタ.csv")
    try:
        m0410_df = pd.read_csv(m0410_file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        m0410_df = pd.read_csv(m0410_file, encoding='shift_jis')
    valid_ktcd_set = set(m0410_df['KTCD'].astype(str))
    print(f"有効KTCD数: {len(valid_ktcd_set)}件")
    
    # EJシステムからSRCD/SRPRICE統合データを取得（M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COST結合）
    print("\n=== EJシステム（M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COST）統合データ取得 ===")
    try:
        # M_PUCH_UNIT_COST_HとM_PUCH_UNIT_COSTを結合して一貫データ取得
        srcd_srprice_sql = """
        SELECT h.ITEM_CD, h.VEND_CD, h.PUCH_PRIORITY_REF_NO,
               c.UNIT_COST, c.EFF_PHASE_IN_DATE, c.PUCH_SIZE
        FROM EXPJ2.M_PUCH_UNIT_COST_H h
        INNER JOIN EXPJ2.M_PUCH_UNIT_COST c
        ON h.ITEM_CD = c.ITEM_CD AND h.VEND_CD = c.VEND_CD
        WHERE h.PUCH_PRIORITY_REF_NO IS NOT NULL
        AND c.EFF_PHASE_IN_DATE < TO_DATE('2025-12-01', 'YYYY-MM-DD')
        ORDER BY h.ITEM_CD, h.PUCH_PRIORITY_REF_NO ASC, c.EFF_PHASE_IN_DATE DESC, c.PUCH_SIZE ASC
        """
        combined_df = ej_data_get(srcd_srprice_sql)
        print(f"統合データ取得: {len(combined_df)}行")

        # ITEM_CD（前工程）ごとに最優先レコード1行のみ選定
        srcd_srprice_dict = {}
        for _, record in combined_df.iterrows():
            item_cd = record['ITEM_CD']
            if item_cd not in srcd_srprice_dict:
                # 最初に見つかったレコード（ORDER BY条件により最優先）を採用
                srcd_srprice_dict[item_cd] = {
                    'SRCD': record['VEND_CD'],
                    'SRPRICE': record['UNIT_COST'],
                    'EFF_PHASE_IN_DATE': record['EFF_PHASE_IN_DATE'],
                    'PUCH_SIZE': record['PUCH_SIZE'],
                    'PRIORITY': record['PUCH_PRIORITY_REF_NO']
                }

        print(f"1行選定辞書作成: {len(srcd_srprice_dict)}件")
    except Exception as e:
        print(f"統合データ取得エラー: {e}")
        srcd_srprice_dict = {}

    # フォールバック用: T_RLSD_PUCH_ODRからSRCD/SRPRICE用データを取得
    print("\n=== EJシステム（T_RLSD_PUCH_ODR）フォールバックデータ取得 ===")
    try:
        fallback_sql = """
        SELECT ITEM_CD, VEND_CD, UNIT_COST, PUCH_ODR_DLV_DATE
        FROM EXPJ2.T_RLSD_PUCH_ODR
        WHERE ITEM_CD IS NOT NULL AND VEND_CD IS NOT NULL
        ORDER BY ITEM_CD, PUCH_ODR_DLV_DATE DESC
        """
        fallback_df = ej_data_get(fallback_sql)
        print(f"フォールバック用データ取得: {len(fallback_df)}行")

        # 最新日付のレコードのみを抽出
        fallback_latest = fallback_df.groupby('ITEM_CD').first().reset_index()
        print(f"フォールバック最新日付で重複除去: {len(fallback_latest)}件")
        fallback_srcd_dict = dict(zip(fallback_latest['ITEM_CD'], fallback_latest['VEND_CD']))
        fallback_srprice_dict = dict(zip(fallback_latest['ITEM_CD'], fallback_latest['UNIT_COST']))
        print(f"フォールバックSRCD辞書作成: {len(fallback_srcd_dict)}件")
        print(f"フォールバックSRPRICE辞書作成: {len(fallback_srprice_dict)}件")
    except Exception as e:
        print(f"フォールバック用データ取得エラー: {e}")
        fallback_srcd_dict = {}
        fallback_srprice_dict = {}
    
    # EJシステムからLDTIME用データを取得
    print("\n=== EJシステム（M_ITEM）データ取得 ===")
    try:
        ldtime_sql = """
        SELECT ITEM_CD, PUCH_FIXED_LT
        FROM EXPJ2.M_ITEM
        """
        ldtime_df = ej_data_get(ldtime_sql)
        print(f"LDTIME用データ取得: {len(ldtime_df)}行")

        ldtime_dict = dict(zip(ldtime_df['ITEM_CD'], ldtime_df['PUCH_FIXED_LT']))
        print(f"LDTIME辞書作成: {len(ldtime_dict)}件")
    except Exception as e:
        print(f"LDTIME用データ取得エラー: {e}")
        ldtime_dict = {}

    # PEFINソート.csvを読み込んで前工程情報を取得
    print("\n=== PEFINソート.csv前工程情報取得 ===")
    pefin_zenkatei_dict = {}
    try:
        pefin_file = os.path.join(r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\input", "PEFINソート.csv")
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
    
    # 完成部番でグループ化してSEQとKTSEQを計算
    output_data = []
    
    # 完成部番でグループ化
    grouped = df.groupby('完成部番')
    
    for hmcd, group in grouped:
        # 例外処理：特定のHMCDは処理対象外とする
        if str(hmcd) in ['KS91-03006BA', 'KD64-00202BA']:
            print(f"処理対象外: {hmcd}")
            continue

        # PEFINソート.csvの前工程値を取得
        hmcd_str = str(hmcd)
        pefin_zenkatei = pefin_zenkatei_dict.get(hmcd_str)

        # 各行のデータを準備
        group_data = []
        pefin_row_data = None

        for _, row in group.iterrows():
            # 前工程からKTCDを抽出（最初のハイフンまでの文字列）
            zenkatei = str(row['前工程']) if pd.notna(row['前工程']) else ''
            if '-' in zenkatei:
                ktcd = zenkatei.split('-')[0]
            else:
                ktcd = zenkatei  # ハイフンがない場合はそのまま

            # KTCDの変換処理
            if ktcd == "A0":
                ktcd = "AO"
            elif ktcd in ["PA1", "PA2"]:
                ktcd = "PA"

            row_data = {
                'original_row': row,
                'ktcd': ktcd,
                'zenkatei': zenkatei
            }

            # PEFIN行を特別に保存
            if ktcd == 'PEFIN':
                pefin_row_data = row_data
            else:
                group_data.append(row_data)

        # PEFINソート.csvの前工程値に基づいてSEQ順序を決定
        ordered_data = []

        if pefin_zenkatei is not None and pefin_row_data is not None:
            # PEFINソート.csvで指定された位置にPEFIN工程を配置
            if pefin_zenkatei == 1:
                # 前工程=1: PEFIN工程を最初（SEQ=1）に配置
                ordered_data.append(pefin_row_data)
                ordered_data.extend(group_data)
            elif pefin_zenkatei == 2 and len(group_data) >= 1:
                # 前工程=2: PEFIN工程を2番目（SEQ=2）に配置
                ordered_data.append(group_data[0])
                ordered_data.append(pefin_row_data)
                ordered_data.extend(group_data[1:])
            elif pefin_zenkatei == 3 and len(group_data) >= 2:
                # 前工程=3: PEFIN工程を3番目（SEQ=3）に配置
                ordered_data.extend(group_data[:2])
                ordered_data.append(pefin_row_data)
                ordered_data.extend(group_data[2:])
            else:
                # 想定外のケース：元の順序を維持
                ordered_data.extend(group_data)
                if pefin_row_data:
                    ordered_data.append(pefin_row_data)
        else:
            # PEFINソート.csvにない場合：元の順序を維持
            ordered_data.extend(group_data)
            if pefin_row_data:
                ordered_data.append(pefin_row_data)

        # 同一HMCDに対してSEQを付与
        for idx, row_data in enumerate(ordered_data, 1):
            row = row_data['original_row']
            ktcd = row_data['ktcd']
            zenkatei = row_data['zenkatei']
            
            # 前工程をキーにしてSRCD/SRPRICE/LDTIMEを統合取得
            zenkatei_key = str(row['前工程']) if pd.notna(row['前工程']) else ''

            # 統合辞書からSRCD/SRPRICE一貫取得
            record_data = srcd_srprice_dict.get(zenkatei_key, {})
            srcd_value = record_data.get('SRCD', '')
            srprice_value = record_data.get('SRPRICE', 0)

            # 統合辞書で見つからない場合、T_RLSD_PUCH_ODRからフォールバック取得
            if not srcd_value:
                srcd_value = fallback_srcd_dict.get(zenkatei_key, "")
                srprice_value = fallback_srprice_dict.get(zenkatei_key, 0)
                if srcd_value:  # フォールバックで見つかった場合のログ
                    print(f"フォールバック取得: {zenkatei_key} -> SRCD: {srcd_value}, SRPRICE: {srprice_value}")

            # LDTIMEを前工程キーで取得（完成部番ではなく前工程をキーにする）
            ldtime_value = ldtime_dict.get(zenkatei_key, 0)
            
            # SUPCLSCDの決定: KTCDがAO（AO（無）を含む）の場合は"6"、それ以外は"5"
            supclscd_value = '6' if ktcd.startswith('AO') else '5'
            
            # KTCDがPEFINの場合の例外処理
            if ktcd == 'PEFIN':
                # PEFINの場合の特別な値設定
                ldtime_final = 0  # 固定で0
                srprice_final = 0.0  # 固定で0
                csbcd_final = '10'  # 13ではなく10
                rcvtstkbn_final = '2'  # 1ではなく2
                rcvchkkbn_final = '2'  # 1ではなく2
            else:
                # 通常の処理
                ldtime_final = int(ldtime_value) if ldtime_value is not None else 0
                srprice_final = float(srprice_value) if srprice_value is not None else 0.0
                csbcd_final = '13'  # 固定値"13"
                rcvtstkbn_final = '1'  # 固定値"1"
                rcvchkkbn_final = '1'  # 固定値"1"
            
            # M0840のレイアウトに従ってデータを変換
            record = {
                'HMCD': str(hmcd) if pd.notna(hmcd) else '',  # 完成部番
                'SEQ': idx,  # 同じHMCDの場合、1単位で連番
                'KTSEQ': idx * 10,  # 同じHMCDの場合、10単位で連番
                'KTCD': ktcd,  # 前工程の最初のハイフンまでの文字列（存在チェック済）
                'SRCD': str(srcd_value) if srcd_value else '',  # EJ M_PUCH_UNIT_COSTから取得（無しは空欄）
                'SGNCD': '',  # 空欄
                'DDTIME': 0,  # 固定値"0"
                'SGTIME': 0,  # 固定値"0"
                'LDTIME': ldtime_final,  # EJ M_ITEMから取得（PEFINの場合は0）
                'SRPRICE': srprice_final,  # EJ M_PUCH_UNIT_COSTから取得（PEFINの場合は0）
                'CSBCD': csbcd_final,  # 通常"13"、PEFINの場合"10"
                'SUPCLSCD': supclscd_value,  # KTCDがAOの場合は"6"、それ以外は"5"
                'SUPCD': '',  # 空欄
                'RCVTSTKBN': rcvtstkbn_final,  # 固定値"1"
                'RCVCHKKBN': rcvchkkbn_final  # 固定値"1"
            }
            
            output_data.append(record)
    
    # DataFrameを作成
    output_df = pd.DataFrame(output_data)

    # 指示33: PEFINソート.csvに基づくSEQ/KTSEQ編集処理
    # 注意: 上記で既にPEFINソート.csvに基づいて正しいSEQ順序を設定済みのため、
    # 指示33の編集処理は基本的に不要となりました。
    # ただし、前工程=0（PEFIN行削除）のみ実行します。

    print("\n=== 指示33: 前工程=0のPEFIN行削除処理 ===")

    try:
        # 前工程=0の場合のみPEFIN行を削除
        for hmcd_str, zenkatei_value in pefin_zenkatei_dict.items():
            if zenkatei_value == 0:
                # 該当するHMCDの行を取得
                hmcd_mask = output_df['HMCD'] == hmcd_str
                if hmcd_mask.any():
                    pefin_mask = (hmcd_mask) & (output_df['KTCD'] == 'PEFIN')

                    if pefin_mask.any():
                        print(f"処理中: {hmcd_str}, 前工程値: {zenkatei_value}")
                        # PEFIN行を削除
                        output_df = output_df[~pefin_mask]
                        print(f"  PEFIN行を削除: {hmcd_str}")

                        # SEQ/KTSEQを再計算（削除後の行のみ）
                        remaining_mask = output_df['HMCD'] == hmcd_str
                        remaining_rows = output_df[remaining_mask]

                        for new_seq, idx in enumerate(remaining_rows.index, 1):
                            output_df.at[idx, 'SEQ'] = new_seq
                            output_df.at[idx, 'KTSEQ'] = new_seq * 10

                        print(f"  SEQ/KTSEQ繰り上げ完了: {hmcd_str}")

        print("前工程=0のPEFIN行削除処理完了")

    except Exception as e:
        print(f"PEFIN行削除処理エラー: {e}")

    # 出力ファイルのパス
    output_file = os.path.join(output_dir, "M0840_品目工程マスタ.csv")

    # CSVファイルに出力（ヘッダー付き）
    output_df.to_csv(output_file, encoding='utf-8-sig', index=False)
    
    print(f"出力完了: {output_file}")
    print(f"出力データ: {len(output_df)}行")
    
    # 出力内容のサンプルを表示
    print("\n=== 出力データサンプル（最初の10行） ===")
    print(output_df.head(10).to_string(index=False))
    
    print("\n=== フィールドマッピング確認 ===")
    print("HMCD (品目コード) ← 14_品目工程work.csvの「完成部番」")
    print("SEQ (番号) ← 同じHMCDの場合、1単位で連番")
    print("KTSEQ (工順) ← 同じHMCDの場合、10単位で連番") 
    print("KTCD (工程コード) ← 14_品目工程work.csvの「前工程」の最初のハイフンまでの文字列（存在チェック済）")
    print("SRCD (仕入先コード) ← EJ M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COST結合（前工程キー、PUCH_PRIORITY_REF_NO最小値、同値時はEFF_PHASE_IN_DATE最新、さらに同値時はPUCH_SIZE最小値優先、2025/12/1以降除く）")
    print("                      ↓ 見つからない場合、EJ T_RLSD_PUCH_ODRテーブルのVEND_CD（発注納期優先）")
    print("SRPRICE (購入単価) ← 同一レコードからUNIT_COST一貫取得（SRCD選定と同じレコード）")
    print("                    ↓ 見つからない場合、EJ T_RLSD_PUCH_ODRテーブルのUNIT_COST（発注納期優先）")
    print("LDTIME (リードタイム) ← EJ M_ITEMテーブルのPUCH_FIXED_LT（前工程キー）")
    print("固定値: SGNCD='空欄', DDTIME=0, SGTIME=0, CSBCD='13', RCVTSTKBN='1', RCVCHKKBN='1'")
    print("条件値: SUPCLSCD=KTCDがAO（AO（無）を含む）の場合は'6'、それ以外は'5'")
    print("PEFIN例外処理: KTCD=PEFINの場合、LDTIME=0, SRPRICE=0, CSBCD='10', RCVTSTKBN='2', RCVCHKKBN='2'")
    print("空欄: SGNCD, SUPCD")
    
    # 処理統計を表示
    print(f"\n=== 処理統計 ===")
    print(f"処理対象の品目数（HMCD）: {output_df['HMCD'].nunique()}件")
    print(f"総工程数: {len(output_df)}件")
    
    # HMCDごとの工程数を表示（上位10件）
    hmcd_counts = output_df['HMCD'].value_counts().head(10)
    print(f"\n=== HMCDごとの工程数（上位10件） ===")
    for hmcd, count in hmcd_counts.items():
        print(f"  {hmcd}: {count}工程")

if __name__ == "__main__":
    main()