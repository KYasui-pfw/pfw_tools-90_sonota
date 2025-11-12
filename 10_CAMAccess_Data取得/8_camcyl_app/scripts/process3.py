"""
処理3: CSV → FastAPI completion エンドポイント送信処理

機能:
- EJデータマスター_CAMFIN_LOG_ALL.csv を読み込み
- DATEが1週間前～翌日までの8日間のデータを抽出
- FastAPI経由で状態チェック（未完了/登録エラーのみ送信対象）
- 各行をFastAPI completion エンドポイントに送信
- 送信結果をログに記録
"""
import os
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
logger = setup_logger('process3', LOG_DIR, LOG_RETENTION_DAYS)


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


def filter_by_date_range(df):
    """
    DATEカラムで1週間前～翌日までの8日間のデータを抽出

    Args:
        df (pd.DataFrame): CSVデータ

    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    try:
        # DATE列をdatetime型に変換
        df['DATE'] = pd.to_datetime(df['DATE'])

        # 今日の日付
        today = datetime.now().date()

        # 1週間前（7日前）と翌日の日付を計算
        start_date = today - timedelta(days=7)
        end_date = today + timedelta(days=1)

        logger.info(f"フィルタリング期間: {start_date} ～ {end_date}")

        # 日付範囲でフィルタリング
        df_filtered = df[(df['DATE'].dt.date >= start_date) & (df['DATE'].dt.date <= end_date)]

        original_count = len(df)
        filtered_count = len(df_filtered)
        logger.info(f"フィルタリング結果: {original_count:,}行 → {filtered_count:,}行 ({original_count - filtered_count:,}行除外)")

        return df_filtered

    except Exception as e:
        logger.error(f"日付フィルタリングに失敗しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


def validate_row_data(row):
    """
    行データのバリデーション

    Args:
        row (pd.Series): 1行分のデータ

    Returns:
        tuple: (bool, str) - (バリデーション結果, エラーメッセージ)
    """
    # 必須フィールドの確認
    required_fields = ['DATE', 'SRNO', 'FINUM']

    for field in required_fields:
        if field not in row or pd.isna(row[field]) or row[field] == '':
            return False, f"必須フィールド '{field}' が空です"

    return True, ""


def convert_row_to_payload(row):
    """
    DataFrameの行をAPI送信用のペイロードに変換

    項目マッピング:
    - KTEDDT ← DATE
    - INDNO ← SRNO
    - lineno ← 固定値 1
    - IPTANCD ← 固定値 "SECT1836"
    - prdqty ← FINUM
    - ktedqty ← FINUM

    Args:
        row (pd.Series): 1行分のデータ

    Returns:
        dict: API送信用のペイロード
    """
    # DATE を YYYY-MM-DD 形式の文字列に変換
    if isinstance(row['DATE'], pd.Timestamp):
        kteddt = row['DATE'].strftime('%Y-%m-%d')
    else:
        # 文字列からdatetimeに変換してから再フォーマット
        date_obj = pd.to_datetime(row['DATE'], errors='coerce')
        if pd.isna(date_obj):
            kteddt = str(row['DATE'])[:10]  # フォールバック
        else:
            kteddt = date_obj.strftime('%Y-%m-%d')

    payload = {
        "KTEDDT": kteddt,
        "INDNO": str(row['SRNO']).strip(),
        "lineno": 1,  # 固定値
        "IPTANCD": "SECT1836",  # 固定値
        "prdqty": float(row['FINUM']) if not pd.isna(row['FINUM']) else 0.0,
        "ktedqty": float(row['FINUM']) if not pd.isna(row['FINUM']) else 0.0,
    }

    return payload


def is_sendable_status(instruction):
    """
    指示データの状態が送信可能かどうかを判定

    判定ルール（NiceGUI work_record_page.py の get_row_status と同じ）:
    - 完了（EDKBN='1'/'2', STATUS='3'/'4'/'8'）→ 送信不可
    - 中止（STATUS='9'）→ 送信不可
    - 実績登録中（SYORIZUMIKB='1'）→ 送信不可
    - 登録エラー（SYORIZUMIKB='3'）→ 送信可能
    - 未完了（その他）→ 送信可能

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


async def check_instructions_status(client, api_base_url, read_api_key, slip_keys):
    """
    複数の指示番号+行番号の状態を一括チェック

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        slip_keys (list): [{"indno": "...", "lineno": 1}, ...] のリスト

    Returns:
        dict: {(indno, lineno): is_sendable, ...} の辞書
    """
    if not slip_keys:
        return {}

    api_url = f"{api_base_url}/instructions/slip/batch"
    headers = {
        "X-API-KEY": read_api_key,
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"状態チェック開始: {len(slip_keys)}件の指示データを問い合わせ中...")

        response = await client.post(
            api_url,
            headers=headers,
            json=slip_keys,
            timeout=30.0
        )
        response.raise_for_status()

        instructions = response.json()
        logger.info(f"状態チェック完了: {len(instructions)}件のデータを取得")

        # 各INDNOについて、送信可否を判定
        # 同じINDNOで複数行ある場合、1つでも送信不可があれば全て不可
        indno_sendability = {}  # {indno: is_sendable}

        for instruction in instructions:
            indno = instruction.get('INDNO', '')
            lineno = instruction.get('LINENO', 1)

            is_sendable = is_sendable_status(instruction)

            key = (indno, lineno)

            # 既存エントリがある場合、ANDで判定（1つでもFalseなら全体がFalse）
            if key in indno_sendability:
                indno_sendability[key] = indno_sendability[key] and is_sendable
            else:
                indno_sendability[key] = is_sendable

        # 送信可能/不可の集計
        sendable_count = sum(1 for v in indno_sendability.values() if v)
        blocked_count = len(indno_sendability) - sendable_count

        logger.info(f"送信可能: {sendable_count}件, 送信不可: {blocked_count}件")

        return indno_sendability

    except httpx.HTTPStatusError as e:
        logger.error(f"状態チェックAPI呼び出しエラー: HTTP {e.response.status_code} - {e.response.text}")
        return {}
    except httpx.RequestError as e:
        logger.error(f"状態チェック接続エラー: {e}")
        return {}
    except Exception as e:
        logger.error(f"状態チェック予期しないエラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


async def send_completion_record(client, api_url, api_key, payload, row_index):
    """
    completion エンドポイントにデータを送信

    Args:
        client (httpx.AsyncClient): HTTPクライアント
        api_url (str): API URL
        api_key (str): API KEY
        payload (dict): 送信データ
        row_index (int): 行番号

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
        logger.info(f"  [{row_index}] ✓ 送信成功: INDNO={payload['INDNO']}, DATE={payload['KTEDDT']}, QTY={payload['ktedqty']} - {message}")
        return True, message

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        logger.error(f"  [{row_index}] ✗ 送信失敗: INDNO={payload['INDNO']}, DATE={payload['KTEDDT']} - {error_msg}")
        return False, error_msg

    except httpx.RequestError as e:
        error_msg = f"接続エラー: {e}"
        logger.error(f"  [{row_index}] ✗ 送信失敗: INDNO={payload['INDNO']}, DATE={payload['KTEDDT']} - {error_msg}")
        return False, error_msg

    except Exception as e:
        error_msg = f"予期しないエラー: {e}"
        logger.error(f"  [{row_index}] ✗ 送信失敗: INDNO={payload['INDNO']}, DATE={payload['KTEDDT']} - {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        return False, error_msg


async def process_csv_data(df, api_base_url, read_api_key, insert_api_key):
    """
    CSVデータを処理してAPIに送信

    Args:
        df (pd.DataFrame): CSVデータ
        api_base_url (str): API ベースURL
        read_api_key (str): READ用APIキー
        insert_api_key (str): INSERT用APIキー

    Returns:
        dict: 処理結果サマリー
    """
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    blocked_count = 0  # 状態チェックで除外された件数

    logger.info(f"データ処理を開始します: 全{total_rows}件")

    async with httpx.AsyncClient() as client:
        # ステップ1: 事前チェック - INDNO+linenoのユニークキーリストを作成
        slip_keys = []
        valid_rows = []

        for index, row in df.iterrows():
            # バリデーション
            is_valid, error_message = validate_row_data(row)
            if not is_valid:
                logger.warning(f"  [{index + 1}/{total_rows}] バリデーションエラー: {error_message}")
                skip_count += 1
                continue

            indno = str(row['SRNO']).strip()
            lineno = 1  # 固定値

            slip_keys.append({"indno": indno, "lineno": lineno})
            valid_rows.append((index + 1, row))

        if not slip_keys:
            logger.warning("バリデーション通過データが0件です。処理を終了します。")
            return {
                'total': total_rows,
                'success': success_count,
                'skip': skip_count,
                'error': error_count,
                'blocked': blocked_count
            }

        # ステップ2: 状態チェック（FastAPI経由で一括取得）
        logger.info("")
        sendability_map = await check_instructions_status(
            client, api_base_url, read_api_key, slip_keys
        )
        logger.info("")

        # ステップ3: 送信可能なデータのみAPIに送信
        completion_url = f"{api_base_url}/completion/"
        logger.info(f"データ送信を開始します: {len(valid_rows)}件")

        for row_number, row in valid_rows:
            indno = str(row['SRNO']).strip()
            lineno = 1
            key = (indno, lineno)

            # 状態チェック結果を確認
            if key not in sendability_map:
                logger.error(f"  [{row_number}/{total_rows}] ✗ エラー: rBOMシステムにデータが存在しません (INDNO={indno})")
                logger.warning(f"  [{row_number}/{total_rows}] スキップ: 状態チェック結果なし (INDNO={indno})")
                skip_count += 1
                continue

            if not sendability_map[key]:
                logger.info(f"  [{row_number}/{total_rows}] 除外: 送信不可状態（完了/中止/実績登録中） (INDNO={indno})")
                blocked_count += 1
                continue

            # ペイロード変換
            try:
                payload = convert_row_to_payload(row)
            except Exception as e:
                logger.error(f"  [{row_number}/{total_rows}] ペイロード変換エラー: {e}")
                error_count += 1
                continue

            # API送信
            success, message = await send_completion_record(
                client, completion_url, insert_api_key, payload, f"{row_number}/{total_rows}"
            )

            if success:
                success_count += 1
            else:
                error_count += 1

    return {
        'total': total_rows,
        'success': success_count,
        'skip': skip_count,
        'error': error_count,
        'blocked': blocked_count
    }


async def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("処理3: CSV → FastAPI completion エンドポイント送信処理を開始")
    logger.info("=" * 60)

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # 環境変数から設定を読み込み
    csv_path = os.getenv('PROCESS3_CSV_PATH', '/app/output/KakouJisseki/EJデータマスター_CAMFIN_LOG_ALL.csv')
    api_base_url = os.getenv('FASTAPI_BASE_URL', 'http://fastapi-rbom-app:8000')
    read_api_key = os.getenv('READ_API_KEY', '')
    insert_api_key = os.getenv('INSERT_API_KEY', '')

    if not read_api_key:
        logger.error("READ_API_KEY が設定されていません")
        return 1

    if not insert_api_key:
        logger.error("INSERT_API_KEY が設定されていません")
        return 1

    logger.info(f"CSV入力: {csv_path}")
    logger.info(f"API送信先: {api_base_url}\n")

    # CSVファイルを読み込み
    df = read_csv_file(csv_path)
    if df is None or df.empty:
        logger.error("CSVデータの読み込みに失敗したか、データが空です")
        return 1

    # 日付範囲でフィルタリング（1週間前～翌日までの8日間）
    df_filtered = filter_by_date_range(df)
    if df_filtered.empty:
        logger.warning("フィルタリング後のデータが0件です。処理を終了します。")
        return 0

    # データを処理してAPI送信
    result = await process_csv_data(df_filtered, api_base_url, read_api_key, insert_api_key)

    # 処理結果サマリー
    logger.info("")
    logger.info("=" * 60)
    logger.info("処理3完了")
    logger.info(f"総件数: {result['total']}件")
    logger.info(f"成功: {result['success']}件")
    logger.info(f"スキップ（バリデーションエラー・rBOM未登録）: {result['skip']}件")
    logger.info(f"除外（送信不可状態）: {result['blocked']}件")
    logger.info(f"エラー（送信失敗）: {result['error']}件")
    logger.info("=" * 60)

    return 0 if result['error'] == 0 else 1


if __name__ == "__main__":
    import asyncio
    exit(asyncio.run(main()))
