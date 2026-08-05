"""
処理4: CSV → FastAPI completion エンドポイント送信処理（シリンダ・ダイアル）

機能:
- Cyl_pfw_table_KaLstCyl_All.csv を読み込み（全件処理、日付フィルタリングなし）
- CAT2パターン（405/409）に応じた工程・品名マッピング
- FastAPI経由で組立番号（SEINO）を取得し、4ヶ月分のデータを検索
- 状態チェック（未完了/登録エラーのみ送信対象）
- completion エンドポイントに送信
"""
import os
import sqlite3
import httpx
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from logger_config import setup_logger, cleanup_old_logs

# 環境変数を読み込み
load_dotenv()

# ロガー設定
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '7'))
logger = setup_logger('process4', LOG_DIR, LOG_RETENTION_DAYS)

# 工程・品名マッピング定義（CAT2末尾3文字ごと）
PROCESS_MAPPING = {
    '405': {
        'resultStart': {'KTCD': 'SL1ST', 'HMNM': 'NEEDLE CYLINDER'},
        'resultEnd': {'KTCD': 'SL1', 'HMNM': 'NEEDLE CYLINDER'},
        'JOB_8': {'KTCD': 'TQT', 'HMNM': 'NEEDLE CYLINDER'},
        'JOB_1': {'KTCD': 'TY', 'HMNM': 'NEEDLE CYLINDER'},
        'JOB_2': {'KTCD': 'DQT', 'HMNM': 'NEEDLE CYLINDER'},
        'JOB_6': {'KTCD': 'BF', 'HMNM': 'UNIT CYLINDER'},
        'JOB_4': {'KTCD': 'RST', 'HMNM': 'UNIT CYLINDER'},
        'JOB_5': {'KTCD': 'G', 'HMNM': 'UNIT CYLINDER'},
        'JOB_3': {'KTCD': 'FL', 'HMNM': 'UNIT CYLINDER'},
        'JOB_7': {'KTCD': 'CYFIN', 'HMNM': 'UNIT CYLINDER'},
    },
    '409': {
        'resultStart': {'KTCD': 'SL1ST', 'HMNM': 'NEEDLE DIAL'},
        'resultEnd': {'KTCD': 'SL1', 'HMNM': 'NEEDLE DIAL'},
        'JOB_8': {'KTCD': 'TQT', 'HMNM': 'NEEDLE DIAL'},
        'JOB_1': {'KTCD': 'TY', 'HMNM': 'NEEDLE DIAL'},
        'JOB_2': {'KTCD': 'DDQT', 'HMNM': 'NEEDLE DIAL'},  # DIALはDDQT
        'JOB_6': {'KTCD': 'BF', 'HMNM': 'UNIT DIAL'},
        'JOB_4': {'KTCD': 'RST', 'HMNM': 'UNIT DIAL'},
        'JOB_5': {'KTCD': 'G', 'HMNM': 'UNIT DIAL'},
        'JOB_3': {'KTCD': 'FL', 'HMNM': 'UNIT DIAL'},
        'JOB_7': {'KTCD': 'DIFIN', 'HMNM': 'UNIT DIAL'},
    }
}

# 処理対象の日付列リスト
DATE_COLUMNS = ['resultStart', 'resultEnd', 'JOB_1', 'JOB_2', 'JOB_3', 'JOB_4', 'JOB_5', 'JOB_6', 'JOB_7', 'JOB_8']


def load_lot_mapping(db_path):
    """
    lot_mapping.db から DENPYONO→INDNO マッピングを読み込む

    同一lot_numberに複数indnoがある場合、数値部分が最小のものを選択

    Args:
        db_path (str): lot_mapping.db のファイルパス

    Returns:
        dict: {lot_number: indno} のマッピング辞書
    """
    if not db_path or not os.path.exists(db_path):
        logger.warning(f"lot_mapping.db が見つかりません: {db_path}")
        return {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # mapping_results から lot_number, indno を取得
        cursor.execute("SELECT lot_number, indno FROM mapping_results")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            logger.info("lot_mapping.db にマッピングデータがありません")
            return {}

        # lot_number ごとに indno をグループ化
        lot_to_indnos = {}
        for lot_number, indno in rows:
            if lot_number not in lot_to_indnos:
                lot_to_indnos[lot_number] = []
            lot_to_indnos[lot_number].append(indno)

        # 各 lot_number について、数値部分が最小の indno を選択
        mapping = {}
        for lot_number, indnos in lot_to_indnos.items():
            if len(indnos) == 1:
                mapping[lot_number] = indnos[0]
            else:
                # indno の先頭1文字を除いた数値部分で比較して最小を選択
                def get_numeric_part(indno):
                    try:
                        return int(indno[1:])  # 先頭1文字を除いて数値化
                    except (ValueError, IndexError):
                        return float('inf')  # 変換失敗時は最大値

                min_indno = min(indnos, key=get_numeric_part)
                mapping[lot_number] = min_indno

        logger.info(f"lot_mapping.db からマッピング読み込み: {len(mapping)}件")
        return mapping

    except Exception as e:
        logger.error(f"lot_mapping.db 読み込みエラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def read_csv_file(csv_path):
    """
    CSVファイルを読み込む

    Args:
        csv_path (str): CSVファイルパス

    Returns:
        pd.DataFrame or None: DataFrameオブジェクト、失敗時はNone
    """
    try:
        if not os.path.exists(csv_path):
            logger.error(f"ファイルが見つかりません: {csv_path}")
            return None

        # 複数のエンコーディングを試行
        encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
                logger.info(f"CSVファイルを読み込みました: {csv_path} (encoding: {encoding})")
                logger.info(f"データ件数: {len(df):,}行, カラム数: {len(df.columns)}")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            logger.error(f"エンコーディングの検出に失敗しました: {csv_path}")
            return None

        return df

    except Exception as e:
        logger.error(f"CSVファイルの読み込みに失敗しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def get_cat2_pattern(cat2_value):
    """
    CAT2の末尾3文字からパターン（405/409）を判定
    例: 'S409' → '409', 'D405' → '405'

    Args:
        cat2_value (str): CAT2の値

    Returns:
        str or None: '405', '409', または None
    """
    if pd.isna(cat2_value) or not cat2_value:
        logger.debug(f"CAT2パターン判定: NULL/空 (値={cat2_value})")
        return None

    cat2_str = str(cat2_value).strip()
    if len(cat2_str) < 3:
        logger.debug(f"CAT2パターン判定: 3文字未満 (値='{cat2_str}', 長さ={len(cat2_str)})")
        return None

    suffix = cat2_str[-3:]
    if suffix in ('405', '409'):
        logger.debug(f"CAT2パターン判定: OK (値='{cat2_str}' → パターン='{suffix}')")
        return suffix

    logger.debug(f"CAT2パターン判定: 末尾不一致 (値='{cat2_str}', 末尾3文字='{suffix}')")
    return None


def filter_by_date_range(df):
    """
    resultStart列で1週間前～翌日までの8日間のデータを抽出

    ※注意: この関数は現在使用されていません（全件処理に変更）

    Args:
        df (pd.DataFrame): CSVデータ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    try:
        # resultStart列をdatetime型に変換
        df['resultStart'] = pd.to_datetime(df['resultStart'], errors='coerce')

        # 今日の日付
        today = datetime.now().date()

        # 1週間前（7日前）と翌日の日付を計算
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)

        logger.info(f"フィルタリング期間: {start_date} ～ {end_date}")

        # 日付範囲でフィルタリング（NaT値は除外）
        df_filtered = df[df['resultStart'].notna() &
                        (df['resultStart'].dt.date >= start_date) &
                        (df['resultStart'].dt.date <= end_date)]

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"フィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

        return df_filtered

    except Exception as e:
        logger.error(f"日付フィルタリングに失敗しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


async def get_seino_by_denpyono(client, api_base_url, read_api_key, denpyono):
    """
    DENPYONOから組立番号（SEINO）を取得

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        denpyono (str): 伝票番号

    Returns:
        str or None: SEINO（組立番号）、取得失敗時はNone
    """
    api_url = f"{api_base_url}/instructions/slip"
    headers = {"X-API-KEY": read_api_key}
    params = {"indno": denpyono, "lineno": 1}

    try:
        response = await client.get(api_url, headers=headers, params=params, timeout=10.0)
        response.raise_for_status()

        instructions = response.json()
        if instructions and len(instructions) > 0:
            seino = instructions[0].get('SEINO')
            return seino
        else:
            return None

    except Exception as e:
        logger.warning(f"SEINO取得エラー (DENPYONO={denpyono}): {e}")
        return None


async def get_instructions_for_4_months(client, api_base_url, read_api_key):
    """
    前月～翌々々月の5ヶ月分の指示データを取得

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー

    Returns:
        list: 指示データのリスト
    """
    api_url = f"{api_base_url}/instructions/"
    headers = {"X-API-KEY": read_api_key}

    all_instructions = []
    today = datetime.now()

    logger.info("5ヶ月分の指示データを取得中（前月～翌々々月）...")

    for offset_months in range(-1, 4):
        # 対象月を計算（-1ヶ月～+3ヶ月）
        target_date = today + timedelta(days=30 * offset_months)
        year = target_date.year
        month = target_date.month

        try:
            params = {"year": year, "month": month}
            response = await client.get(api_url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()

            instructions = response.json()
            all_instructions.extend(instructions)
            logger.info(f"  {year}年{month}月: {len(instructions):,}件")

        except Exception as e:
            logger.warning(f"  {year}年{month}月のデータ取得エラー: {e}")
            continue

    logger.info(f"5ヶ月分合計: {len(all_instructions):,}件")
    return all_instructions


def extract_parent_oyalistno(oyalistno):
    """
    OYALISTNOから親品番を抽出（末尾のハイフン以降を削除）

    Args:
        oyalistno (str): OYALISTNO値

    Returns:
        str or None: 親品番、抽出失敗時はNone

    Examples:
        "25C11-01-130-20" → "25C11-01-130"
        "25DKJ002-240-20-40-10" → "25DKJ002-240-20-40"
    """
    if not oyalistno:
        return None

    oyalistno_str = str(oyalistno).strip()
    if not oyalistno_str or '-' not in oyalistno_str:
        return None

    # 右から1回だけ分割（末尾のハイフン以降を削除）
    parts = oyalistno_str.rsplit('-', 1)
    parent = parts[0]

    logger.debug(f"OYALISTNO抽出: '{oyalistno_str}' → '{parent}'")
    return parent


def filter_instructions_by_oyalistno_prefix(instructions, parent_oyalistno, ktcd, seino):
    """
    OYALISTNO前方一致 + KTCD + SEINO でフィルタリング（SL1/SL1ST専用）

    Args:
        instructions (list): 指示データのリスト
        parent_oyalistno (str): 親品番（前方一致用）
        ktcd (str): 工程コード
        seino (str): 組立番号

    Returns:
        list: フィルタリング後の指示データ（1～3件想定）
    """
    filtered = []
    for inst in instructions:
        inst_oyalistno = str(inst.get('OYALISTNO', '')).strip()
        inst_ktcd = str(inst.get('KTCD', '')).strip()
        inst_seino = str(inst.get('SEINO', '')).strip()

        # OYALISTNO前方一致 AND KTCD一致 AND SEINO一致
        if (inst_oyalistno.startswith(parent_oyalistno) and
            inst_ktcd == str(ktcd).strip() and
            inst_seino == str(seino).strip()):
            filtered.append(inst)

    logger.debug(f"OYALISTNO前方一致フィルタ: parent='{parent_oyalistno}', KTCD='{ktcd}', SEINO='{seino}' → {len(filtered)}件")
    return filtered


def filter_instructions_by_conditions(instructions, seino, ktcd, hmnm):
    """
    指示データをSEINO・KTCD・HMNMでフィルタリング

    Args:
        instructions (list): 指示データのリスト
        seino (str): 組立番号
        ktcd (str): 工程コード
        hmnm (str): 品名

    Returns:
        list: フィルタリング後の指示データ
    """
    filtered = []
    for inst in instructions:
        if (str(inst.get('SEINO', '')).strip() == str(seino).strip() and
            str(inst.get('KTCD', '')).strip() == str(ktcd).strip() and
            str(inst.get('HMNM', '')).strip() == str(hmnm).strip()):
            filtered.append(inst)

    return filtered


def is_sendable_status(instruction):
    """
    指示データの状態が送信可能かどうかを判定
    (process3と同じロジック)

    Args:
        instruction (dict): 指示データ

    Returns:
        bool: 送信可能な場合True
    """
    status = str(instruction.get('STATUS', '')).strip()
    syorizumi = str(instruction.get('SYORIZUMIKB', '')).strip()
    edkbn = str(instruction.get('EDKBN', '')).strip()

    # 完納区分がある場合は送信不可（完了済み）
    if edkbn in ('1', '2'):
        return False

    # STATUS が完了条件に該当する場合は送信不可
    if status in ('3', '4', '8'):
        return False

    # STATUS が中止の場合は送信不可
    if status == '9':
        return False

    # 処理済区分が「実績登録中」の場合は送信不可
    if syorizumi == '1':
        return False

    # 上記以外（未完了 or 登録エラー）は送信可能
    return True


async def send_completion_record(client, api_url, api_key, payload, row_info):
    """
    completion エンドポイントにデータを送信

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_url (str): API URL
        api_key (str): API KEY
        payload (dict): 送信データ
        row_info (str): 行情報（ログ用）

    Returns:
        tuple: (bool, str) - (成功フラグ, レスポンスメッセージ)
    """
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = await client.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=10.0
        )
        response.raise_for_status()

        response_data = response.json()
        message = response_data.get('message', 'Success')
        logger.info(f"  [{row_info}] ✓ 送信成功: INDNO={payload['INDNO']}, lineno={payload['lineno']}, DATE={payload['KTEDDT']}")
        return True, message

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"  [{row_info}] ✗ 送信失敗: INDNO={payload['INDNO']}, lineno={payload['lineno']} - {error_msg}")
        return False, error_msg

    except httpx.RequestError as e:
        error_msg = f"接続エラー: {e}"
        logger.error(f"  [{row_info}] ✗ 送信失敗: INDNO={payload['INDNO']}, lineno={payload['lineno']} - {error_msg}")
        return False, error_msg

    except Exception as e:
        error_msg = f"予期しないエラー: {e}"
        logger.error(f"  [{row_info}] ✗ 送信失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, error_msg


async def process_csv_data(df, api_base_url, read_api_key, insert_api_key, lot_mapping=None):
    """
    CSVデータを処理してAPIに送信

    Args:
        df (pd.DataFrame): CSVデータ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー
        lot_mapping (dict): DENPYONO→INDNOマッピング辞書（省略可）

    Returns:
        dict: 処理結果サマリー
    """
    if lot_mapping is None:
        lot_mapping = {}
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    blocked_count = 0
    no_seino_count = 0

    logger.info(f"データ処理を開始します: 全{total_rows}件\n")

    async with httpx.AsyncClient() as client:
        # ステップ1: 5ヶ月分の指示データを一括取得（前月～翌々々月）
        all_instructions = await get_instructions_for_4_months(client, api_base_url, read_api_key)
        if not all_instructions:
            logger.error("5ヶ月分の指示データが取得できませんでした")
            return {
                'total': total_rows,
                'success': success_count,
                'skip': skip_count,
                'error': error_count,
                'blocked': blocked_count,
                'no_seino': no_seino_count
            }

        logger.info("")
        completion_url = f"{api_base_url}/completion/"

        # ステップ2: 各CSV行を処理
        for index, row in df.iterrows():
            row_number = index + 1

            # CAT2パターン判定
            cat2_value = row.get('CAT2')
            cat2_pattern = get_cat2_pattern(cat2_value)
            if not cat2_pattern:
                logger.warning(f"  [{row_number}/{total_rows}] スキップ: CAT2パターン不明 (CAT2='{cat2_value}')")
                skip_count += 1
                continue

            # DENPYONOからSEINO取得
            denpyono = str(row.get('DENPYONO', '')).strip()
            if not denpyono:
                logger.warning(f"  [{row_number}/{total_rows}] スキップ: DENPYONO が空")
                skip_count += 1
                continue

            # lot_mapping.db でDENPYONO→INDNO変換を試みる
            api_lookup_key = denpyono  # デフォルトはDENPYONOをそのまま使用
            if denpyono in lot_mapping:
                api_lookup_key = lot_mapping[denpyono]
                logger.debug(f"  [{row_number}/{total_rows}] DENPYONO→INDNO変換: {denpyono} → {api_lookup_key}")

            seino = await get_seino_by_denpyono(client, api_base_url, read_api_key, api_lookup_key)
            if not seino:
                logger.error(f"  [{row_number}/{total_rows}] ✗ エラー: SEINO取得失敗 (DENPYONO={denpyono}, API検索キー={api_lookup_key})")
                no_seino_count += 1
                continue

            # 日付列をチェックして送信
            process_mapping = PROCESS_MAPPING[cat2_pattern]
            sent_in_row = False

            for date_col in DATE_COLUMNS:
                date_value = row.get(date_col)

                # 日付が入っているかチェック
                if pd.isna(date_value) or not date_value:
                    continue

                # 日付を文字列に変換（YYYY-MM-DD形式）
                try:
                    if isinstance(date_value, pd.Timestamp):
                        kteddt = date_value.strftime('%Y-%m-%d')
                    else:
                        # 文字列からdatetimeに変換してから再フォーマット
                        date_obj = pd.to_datetime(date_value, errors='coerce')
                        if pd.isna(date_obj):
                            logger.warning(f"  [{row_number}/{total_rows}] 日付変換失敗 ({date_col}): 値='{date_value}'")
                            continue
                        kteddt = date_obj.strftime('%Y-%m-%d')
                except Exception as e:
                    logger.warning(f"  [{row_number}/{total_rows}] 日付変換エラー ({date_col}): {e}")
                    continue

                # 2026-05-31以前の日付は2026-06-01に置換
                if kteddt <= '2026-05-31':
                    logger.debug(f"  [{row_number}/{total_rows}] 日付置換: {kteddt} → 2026-06-01 ({date_col})")
                    kteddt = '2026-06-01'

                # 工程・品名マッピング取得
                if date_col not in process_mapping:
                    continue

                mapping = process_mapping[date_col]
                ktcd = mapping['KTCD']
                hmnm = mapping['HMNM']

                # SL1/SL1STの場合は特殊処理（OYALISTNO前方一致）
                if ktcd in ('SL1', 'SL1ST'):
                    # ステップ1: 基準データを取得（SEINO + KTCD + HMNM）
                    base_instructions = filter_instructions_by_conditions(all_instructions, seino, ktcd, hmnm)

                    if not base_instructions:
                        logger.warning(f"  [{row_number}/{total_rows}] 該当なし: SEINO={seino}, KTCD={ktcd}, HMNM={hmnm}, 列={date_col}")
                        continue

                    # ステップ2: 基準データからOYALISTNOを抽出
                    base_instruction = base_instructions[0]
                    oyalistno = base_instruction.get('OYALISTNO')

                    if not oyalistno:
                        # OYALISTNOがNULLの場合は従来通り（基準データのみ送信）
                        logger.info(f"  [{row_number}/{total_rows}] OYALISTNO=NULL: 従来処理 (INDNO={base_instruction.get('INDNO')}, 列={date_col})")
                        filtered_instructions = base_instructions
                    else:
                        # ステップ3: 親品番を抽出
                        parent_oyalistno = extract_parent_oyalistno(oyalistno)

                        if not parent_oyalistno:
                            # 抽出失敗の場合は従来通り
                            logger.warning(f"  [{row_number}/{total_rows}] OYALISTNO抽出失敗: '{oyalistno}' → 従来処理")
                            filtered_instructions = base_instructions
                        else:
                            # ステップ4: OYALISTNO前方一致で再検索
                            filtered_instructions = filter_instructions_by_oyalistno_prefix(
                                all_instructions, parent_oyalistno, ktcd, seino
                            )

                            if not filtered_instructions:
                                logger.warning(f"  [{row_number}/{total_rows}] OYALISTNO前方一致該当なし: parent={parent_oyalistno}, KTCD={ktcd}, 列={date_col}")
                                continue

                            logger.info(f"  [{row_number}/{total_rows}] OYALISTNO前方一致: {len(filtered_instructions)}件該当 (parent={parent_oyalistno}, 列={date_col})")
                else:
                    # 通常の工程（SEINO + KTCD + HMNM）
                    filtered_instructions = filter_instructions_by_conditions(all_instructions, seino, ktcd, hmnm)

                    if not filtered_instructions:
                        logger.warning(f"  [{row_number}/{total_rows}] 該当なし: SEINO={seino}, KTCD={ktcd}, HMNM={hmnm}, 列={date_col}")
                        continue

                # 送信可能な指示データのみ処理
                for instruction in filtered_instructions:
                    if not is_sendable_status(instruction):
                        logger.info(f"  [{row_number}/{total_rows}] 除外: 送信不可状態 (INDNO={instruction.get('INDNO')}, 列={date_col})")
                        blocked_count += 1
                        continue

                    # ペイロード作成
                    payload = {
                        "KTEDDT": kteddt,
                        "INDNO": instruction.get('INDNO'),
                        "lineno": instruction.get('LINENO'),
                        "IPTANCD": "SECT1707",
                        "prdqty": 1,
                        "ktedqty": 1
                    }

                    # API送信
                    row_info = f"{row_number}/{total_rows} 列={date_col}"
                    success, message = await send_completion_record(
                        client, completion_url, insert_api_key, payload, row_info
                    )

                    if success:
                        success_count += 1
                        sent_in_row = True
                    else:
                        error_count += 1

            if not sent_in_row and no_seino_count == 0:
                # 日付列がすべて空、または該当なし
                pass

    return {
        'total': total_rows,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'blocked': blocked_count,
        'no_seino': no_seino_count
    }


async def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("処理4: CSV → FastAPI completion エンドポイント送信処理（シリンダ・ダイアル）を開始")
    logger.info("=" * 60)

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # 環境変数から設定を読み込み
    csv_path = os.getenv('PROCESS4_CSV_PATH', '/app/output/KakouJisseki/Cyl_pfw_table_KaLstCyl_All.csv')
    api_base_url = os.getenv('FASTAPI_BASE_URL', 'http://fastapi-rbom-app:8000')
    read_api_key = os.getenv('READ_API_KEY', '')
    insert_api_key = os.getenv('INSERT_API_KEY', '')
    lot_mapping_db_path = os.getenv('LOT_MAPPING_DB_PATH', '/app/data/lot_mapping.db')

    if not read_api_key:
        logger.error("READ_API_KEY が設定されていません")
        return 1

    if not insert_api_key:
        logger.error("INSERT_API_KEY が設定されていません")
        return 1

    logger.info(f"CSV入力: {csv_path}")
    logger.info(f"API送信先: {api_base_url}")
    logger.info(f"lot_mapping.db: {lot_mapping_db_path}\n")

    # lot_mapping.db からマッピングを読み込み
    lot_mapping = load_lot_mapping(lot_mapping_db_path)

    # CSVファイルを読み込み
    df = read_csv_file(csv_path)
    if df is None or df.empty:
        logger.error("CSVデータの読み込みに失敗したか、データが空です")
        return 1

    # データを処理してAPI送信（全件処理、日付フィルタリングなし）
    result = await process_csv_data(df, api_base_url, read_api_key, insert_api_key, lot_mapping)

    # 処理結果サマリー
    logger.info("")
    logger.info("=" * 60)
    logger.info("処理4完了")
    logger.info(f"総件数: {result['total']}件")
    logger.info(f"成功: {result['success']}件")
    logger.info(f"スキップ（バリデーションエラー）: {result['skip']}件")
    logger.info(f"SEINO取得失敗: {result['no_seino']}件")
    logger.info(f"除外（送信不可状態）: {result['blocked']}件")
    logger.info(f"エラー（送信失敗）: {result['error']}件")
    logger.info("=" * 60)

    return 0 if result['error'] == 0 else 1


if __name__ == "__main__":
    import asyncio
    exit(asyncio.run(main()))
