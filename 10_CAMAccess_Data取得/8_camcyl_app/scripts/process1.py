"""
処理1: rBOM CSVファイルコピー・加工処理

機能:
- 4つのCSVファイルをコピー
- 2ファイルは項目削除・重複削除を実施
- KakouDenpyoディレクトリに出力
"""
import os
import re
import shutil
import pandas as pd
import httpx
from dotenv import load_dotenv
from logger_config import setup_logger, cleanup_old_logs

# HMCD → SETU_F 変換: -405/-409/-410 + アルファベット + 数字のみサフィックス
# 変換ルール詳細: HMCD_to_SETU_F_変換ルール.md 参照
_HMCD_PATTERN = re.compile(r'^(\d[\d-]*-(?:405|409|410)[A-Za-z]+)(\d+)$')


def convert_hmcd_to_setu_f(value) -> str:
    """
    HMCD を SETU_F 形式に変換する。

    変換対象: -405/-409/-410 + アルファベット + 数字のみのサフィックス（桁数問わず）
    変換式: int(サフィックス) / 10 → 整数なら整数、余りが出れば小数で表現
    変換対象外: サフィックスに数字以外の文字が含まれる場合、サフィックスなし
    """
    if not isinstance(value, str) or not value:
        return value
    m = _HMCD_PATTERN.match(value)
    if not m:
        return value
    alpha, num_str = m.group(1), m.group(2)
    num_int = int(num_str)
    if num_int % 10 == 0:
        return alpha + str(num_int // 10)
    else:
        return alpha + str(num_int / 10)

# 環境変数を読み込み
load_dotenv()

# ロガー設定
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '7'))
logger = setup_logger('process1', LOG_DIR, LOG_RETENTION_DAYS)


def set_file_permissions(file_path):
    """
    ファイルのパーミッションを666に設定（全ユーザー読み書き可能）

    Args:
        file_path (str): ファイルパス
    """
    try:
        os.chmod(file_path, 0o666)
        logger.debug(f"パーミッション設定完了: {file_path} (666)")
    except Exception as e:
        logger.warning(f"パーミッション設定に失敗しました: {file_path} - {e}")


def fetch_oyalistno_from_api(df, indno_col='伝票No', lineno_col='行番号'):
    """
    FastAPI の /instructions/slip/batch エンドポイントから OYALISTNO を取得

    Args:
        df (pd.DataFrame): 処理対象のDataFrame
        indno_col (str): INDNO に対応するカラム名
        lineno_col (str): LINENO に対応するカラム名

    Returns:
        pd.DataFrame: OYALISTNO カラムが追加されたDataFrame
    """
    # 環境変数からAPI設定を取得
    api_base_url = os.getenv('FASTAPI_BASE_URL', 'http://fastapi-rbom-app:8000')
    read_api_key = os.getenv('READ_API_KEY', '')

    if not read_api_key:
        logger.error("READ_API_KEY が設定されていません")
        df['OYALISTNO'] = None
        return df

    # API呼び出し用のキーリストを作成
    slip_keys = []
    for _, row in df.iterrows():
        indno = row.get(indno_col)
        lineno = row.get(lineno_col)
        if pd.notna(indno) and pd.notna(lineno):
            slip_keys.append({
                "indno": str(indno),
                "lineno": int(lineno)
            })

    if not slip_keys:
        logger.warning("API呼び出し用のキーが見つかりませんでした")
        df['OYALISTNO'] = None
        return df

    # バッチサイズ（100件ずつ処理）
    batch_size = 100
    total_keys = len(slip_keys)

    logger.info(f"  FastAPI に {total_keys} 件のデータをリクエスト中...")
    logger.info(f"  {batch_size}件ずつのバッチ処理を実行します")

    # API呼び出し（バッチ処理）
    headers = {
        "X-API-KEY": read_api_key,
        "Content-Type": "application/json"
    }

    api_data = []

    try:
        import time
        overall_start = time.time()

        with httpx.Client(timeout=120.0) as client:
            # バッチ処理
            for i in range(0, total_keys, batch_size):
                batch_keys = slip_keys[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_keys + batch_size - 1) // batch_size

                logger.info(f"    バッチ {batch_num}/{total_batches}: {len(batch_keys)}件を処理開始...")

                batch_start = time.time()

                response = client.post(
                    f"{api_base_url}/instructions/slip/batch",
                    headers=headers,
                    json=batch_keys
                )

                batch_elapsed = time.time() - batch_start

                response.raise_for_status()
                batch_data = response.json()
                api_data.extend(batch_data)

                logger.info(f"      → 完了: {len(batch_data)}件取得, 所要時間: {batch_elapsed:.2f}秒")

                # 10バッチごとに進捗サマリーを表示
                if batch_num % 10 == 0:
                    progress_elapsed = time.time() - overall_start
                    avg_time_per_batch = progress_elapsed / batch_num
                    remaining_batches = total_batches - batch_num
                    estimated_remaining = avg_time_per_batch * remaining_batches
                    logger.info(f"    【進捗】{batch_num}/{total_batches}バッチ完了 | "
                              f"経過: {progress_elapsed:.1f}秒 | "
                              f"平均: {avg_time_per_batch:.2f}秒/バッチ | "
                              f"推定残り: {estimated_remaining:.1f}秒")

        overall_elapsed = time.time() - overall_start
        avg_per_batch = overall_elapsed / total_batches if total_batches > 0 else 0
        logger.info(f"  全バッチ処理完了: 総所要時間 {overall_elapsed:.2f}秒 (平均 {avg_per_batch:.2f}秒/バッチ)")

        logger.info(f"  FastAPI から {len(api_data)} 件のデータを取得完了")

        # API結果をマッピング用の辞書に変換
        # 注意: FastAPIはalias（大文字）でレスポンスを返すため、大文字キーを使用
        oyalistno_map = {}
        invalid_count = 0
        invalid_indno_list = []  # linenoがNoneのindnoを記録
        invalid_lineno_list = []  # indnoがNoneのlinenoを記録

        for item in api_data:
            indno = item.get('INDNO')
            lineno = item.get('LINENO')

            # indnoとlinenoが有効な値か確認
            if indno is None or lineno is None:
                invalid_count += 1

                # linenoがNoneの場合、indnoを記録
                if lineno is None and indno is not None:
                    if len(invalid_indno_list) < 10:  # 最初の10件まで記録
                        invalid_indno_list.append(str(indno))

                # indnoがNoneの場合、linenoを記録
                if indno is None and lineno is not None:
                    if len(invalid_lineno_list) < 10:
                        invalid_lineno_list.append(str(lineno))

                # 最初の3件のみ詳細ログ出力
                if invalid_count <= 3:
                    logger.warning(f"  不正なデータをスキップ: INDNO={indno}, LINENO={lineno}")
                continue

            try:
                key = (str(indno), int(lineno))
                oyalistno_map[key] = item.get('OYALISTNO')
            except (ValueError, TypeError) as e:
                invalid_count += 1
                if invalid_count <= 3:
                    logger.warning(f"  データ変換エラーをスキップ: indno={indno}, lineno={lineno}, error={e}")
                continue

        # 不正データのサマリーをログ出力
        if invalid_count > 0:
            logger.warning(f"  不正なデータ: {invalid_count}件をスキップしました")

            if invalid_indno_list:
                logger.warning(f"    └ linenoがNoneのINDNO（最初の{len(invalid_indno_list)}件）: {', '.join(invalid_indno_list)}")

            if invalid_lineno_list:
                logger.warning(f"    └ indnoがNoneのLINENO（最初の{len(invalid_lineno_list)}件）: {', '.join(invalid_lineno_list)}")

        logger.info(f"  マッピング辞書作成: {len(oyalistno_map)}件")

        # DataFrameにOYALISTNOを追加
        def get_oyalistno(row):
            try:
                indno_val = row[indno_col]
                lineno_val = row[lineno_col]
                if pd.isna(indno_val) or pd.isna(lineno_val):
                    return None
                key = (str(indno_val), int(lineno_val))
                return oyalistno_map.get(key, None)
            except (ValueError, TypeError, KeyError):
                return None

        df['OYALISTNO'] = df.apply(get_oyalistno, axis=1)

        # OYALISTNOの追加と統計情報
        oyalistno_added = df['OYALISTNO'].notna().sum()
        oyalistno_none = df['OYALISTNO'].isna().sum()
        logger.info(f"  OYALISTNO 追加結果: 取得={oyalistno_added}件, 未取得(None)={oyalistno_none}件")

        # OYALISTNOがNoneのデータのサンプルを出力（最初の10件）
        if oyalistno_none > 0:
            none_samples = df[df['OYALISTNO'].isna()][[indno_col, lineno_col]].head(10)
            logger.warning(f"  OYALISTNOが取得できなかったデータ（最初の{min(10, oyalistno_none)}件）:")
            for idx, row in none_samples.iterrows():
                logger.warning(f"    INDNO={row[indno_col]}, LINENO={row[lineno_col]}")

        # デバッグ: OYALISTNO のユニーク数を確認
        unique_oyalistno = df['OYALISTNO'].nunique(dropna=False)
        unique_oyalistno_without_none = df['OYALISTNO'].nunique(dropna=True)
        logger.info(f"  OYALISTNO のユニーク数: {unique_oyalistno}種類 (Noneを除く: {unique_oyalistno_without_none}種類)")

        # OYALISTNOの分布確認（上位5件）
        if unique_oyalistno_without_none > 0:
            oyalistno_counts = df['OYALISTNO'].value_counts(dropna=True).head(5)
            logger.info(f"  OYALISTNO 上位5件の分布:")
            for oyano, count in oyalistno_counts.items():
                logger.info(f"    {oyano}: {count}件")

        return df

    except httpx.RequestError as e:
        logger.error(f"  API接続エラー: {e}")
        logger.error(f"  エラー種別: {type(e).__name__}")
        if hasattr(e, 'request'):
            logger.error(f"  リクエストURL: {e.request.url if e.request else 'N/A'}")
        df['OYALISTNO'] = None
        return df
    except httpx.HTTPStatusError as e:
        logger.error(f"  APIエラー: {e.response.status_code} - {e.response.text}")
        logger.error(f"  リクエストURL: {e.request.url if e.request else 'N/A'}")
        df['OYALISTNO'] = None
        return df
    except Exception as e:
        logger.error(f"  予期せぬエラー: {e}")
        logger.error(f"  エラー種別: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        df['OYALISTNO'] = None
        return df


def filter_qty_zero_from_api(df, indno_col='伝票No', lineno_col='行番号'):
    """
    D3420→D3110を参照し、QTY=0の行をフィルタリング（除外）

    処理フロー:
    1. D3420に INDNO + LINENO で問い合わせ、LISTNO を取得
    2. D3110に LISTNO で問い合わせ、VERNO が最大の行を取得
    3. QTY = 0 の行を除外対象とする

    Args:
        df (pd.DataFrame): 処理対象のDataFrame
        indno_col (str): INDNO に対応するカラム名
        lineno_col (str): LINENO に対応するカラム名

    Returns:
        pd.DataFrame: QTY=0の行を除外したDataFrame
    """
    # 環境変数からAPI設定を取得
    api_base_url = os.getenv('FASTAPI_BASE_URL', 'http://fastapi-rbom-app:8000')
    read_api_key = os.getenv('READ_API_KEY', '')

    if not read_api_key:
        logger.error("READ_API_KEY が設定されていません（QTY=0フィルタリングをスキップ）")
        return df

    original_rows = len(df)
    logger.info(f"  QTY=0フィルタリング開始: {original_rows:,}行")

    # ユニークな(INDNO, LINENO)ペアを取得
    unique_keys = []
    for _, row in df.iterrows():
        indno = row.get(indno_col)
        lineno = row.get(lineno_col)
        if pd.notna(indno) and pd.notna(lineno):
            unique_keys.append((str(indno), int(lineno)))

    unique_keys = list(set(unique_keys))
    logger.info(f"    ユニークキー数: {len(unique_keys)}件")

    if not unique_keys:
        logger.warning("    フィルタリング用のキーが見つかりませんでした")
        return df

    headers = {
        "X-API-KEY": read_api_key,
        "Content-Type": "application/json"
    }

    # 除外対象の(INDNO, LINENO)ペアを格納
    exclude_keys = set()

    try:
        import time
        overall_start = time.time()

        with httpx.Client(timeout=120.0) as client:
            # バッチ処理（100件ずつ）
            batch_size = 100
            total_batches = (len(unique_keys) + batch_size - 1) // batch_size

            for batch_num, i in enumerate(range(0, len(unique_keys), batch_size), start=1):
                batch_keys = unique_keys[i:i + batch_size]

                # D3420からLISTNOを取得
                indno_list = [k[0] for k in batch_keys]
                lineno_list = [k[1] for k in batch_keys]

                # D3420クエリ（INDNO IN (...) で一括取得）
                d3420_query = {
                    "table": "D3420",
                    "columns": ["INDNO", "LINENO", "LISTNO"],
                    "where": {
                        "and": [
                            {"INDNO": {"in": indno_list}}
                        ]
                    },
                    "limit": 10000
                }

                response = client.post(
                    f"{api_base_url}/query",
                    headers=headers,
                    json=d3420_query
                )
                response.raise_for_status()
                d3420_response = response.json()

                # レスポンス形式: {"table": "...", "columns": [...], "rows": [...], "row_count": N}
                d3420_data = d3420_response.get('rows', [])

                # (INDNO, LINENO) → LISTNO のマッピングを作成
                listno_map = {}
                for item in d3420_data:
                    indno = item.get('INDNO')
                    lineno = item.get('LINENO')
                    listno = item.get('LISTNO')
                    if indno and lineno is not None and listno:
                        key = (str(indno), int(lineno))
                        if key in [(str(k[0]), int(k[1])) for k in batch_keys]:
                            listno_map[key] = listno

                if not listno_map:
                    logger.debug(f"    バッチ {batch_num}/{total_batches}: D3420からLISTNOが取得できませんでした")
                    continue

                # ユニークなLISTNOを収集
                unique_listnos = list(set(listno_map.values()))

                # D3110クエリ（LISTNO IN (...) で一括取得）
                d3110_query = {
                    "table": "D3110",
                    "columns": ["LISTNO", "VERNO", "QTY"],
                    "where": {
                        "and": [
                            {"LISTNO": {"in": unique_listnos}}
                        ]
                    },
                    "limit": 10000
                }

                response = client.post(
                    f"{api_base_url}/query",
                    headers=headers,
                    json=d3110_query
                )
                response.raise_for_status()
                d3110_response = response.json()

                # レスポンス形式: {"table": "...", "columns": [...], "rows": [...], "row_count": N}
                d3110_data = d3110_response.get('rows', [])

                # LISTNO → (max VERNO の QTY) マッピングを作成
                listno_qty_map = {}
                for item in d3110_data:
                    listno = item.get('LISTNO')
                    verno = item.get('VERNO')
                    qty = item.get('QTY')
                    if listno and verno is not None:
                        if listno not in listno_qty_map or verno > listno_qty_map[listno]['verno']:
                            listno_qty_map[listno] = {'verno': verno, 'qty': qty}

                # QTY=0のキーを除外対象に追加
                for key, listno in listno_map.items():
                    if listno in listno_qty_map:
                        qty_info = listno_qty_map[listno]
                        if qty_info['qty'] == 0:
                            exclude_keys.add(key)

                # 10バッチごとに進捗表示
                if batch_num % 10 == 0:
                    elapsed = time.time() - overall_start
                    logger.info(f"    【進捗】{batch_num}/{total_batches}バッチ完了 | 除外対象: {len(exclude_keys)}件 | 経過: {elapsed:.1f}秒")

        overall_elapsed = time.time() - overall_start
        logger.info(f"    D3420/D3110クエリ完了: {overall_elapsed:.2f}秒")

        # 除外対象の行をフィルタリング
        if exclude_keys:
            def should_exclude(row):
                indno = row.get(indno_col)
                lineno = row.get(lineno_col)
                if pd.isna(indno) or pd.isna(lineno):
                    return False
                key = (str(indno), int(lineno))
                return key in exclude_keys

            mask = df.apply(should_exclude, axis=1)
            df_filtered = df[~mask]

            excluded_count = len(df) - len(df_filtered)
            logger.info(f"  QTY=0フィルタリング完了: {excluded_count:,}行除外 → {len(df_filtered):,}行")

            # 除外されたキーのサンプルを表示（最初の5件）
            if excluded_count > 0:
                sample_keys = list(exclude_keys)[:5]
                logger.info(f"    除外キーサンプル（最初の{min(5, excluded_count)}件）:")
                for key in sample_keys:
                    logger.info(f"      INDNO={key[0]}, LINENO={key[1]}")

            return df_filtered
        else:
            logger.info(f"  QTY=0フィルタリング完了: 除外対象なし（{original_rows:,}行維持）")
            return df

    except httpx.RequestError as e:
        logger.error(f"  QTY=0フィルタリング API接続エラー: {e}")
        logger.error(f"  エラー種別: {type(e).__name__}")
        return df
    except httpx.HTTPStatusError as e:
        logger.error(f"  QTY=0フィルタリング APIエラー: {e.response.status_code} - {e.response.text}")
        return df
    except Exception as e:
        logger.error(f"  QTY=0フィルタリング 予期せぬエラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return df


def deduplicate_with_oyalistno(df, indno_col='伝票No', oyalistno_col='OYALISTNO', qty_col='必要数'):
    """
    2段階重複削除ロジック

    1段階目: INDNO → OYALISTNO の順でグループ化し、各グループの1行目のみを保持
    2段階目: 同じINDNOで異なるOYALISTNOの行がある場合、必要数を合計して1行に集約

    Args:
        df (pd.DataFrame): 処理対象のDataFrame
        indno_col (str): INDNO に対応するカラム名
        oyalistno_col (str): OYALISTNO カラム名
        qty_col (str): 必要数カラム名

    Returns:
        pd.DataFrame: 重複削除後のDataFrame
    """
    original_rows = len(df)

    # 1段階目: INDNO → OYALISTNO でグループ化し、各グループの1行目のみを保持
    df_sorted = df.sort_values([indno_col, oyalistno_col])
    df_stage1 = df_sorted.drop_duplicates(subset=[indno_col, oyalistno_col], keep='first')

    stage1_removed = original_rows - len(df_stage1)
    if stage1_removed > 0:
        logger.info(f"  1段階目重複削除: {stage1_removed:,}行削除 → {len(df_stage1):,}行")

    # デバッグ: 1段階目後のINDNOとOYALISTNOのユニーク数
    logger.info(f"  1段階目後のINDNOユニーク数: {df_stage1[indno_col].nunique()}")
    logger.info(f"  1段階目後のOYALISTNOユニーク数: {df_stage1[oyalistno_col].nunique(dropna=False)}")

    # 2段階目: 同じINDNOで異なるOYALISTNOがある場合、必要数を合計
    # まず、INDNOでグループ化し、複数のOYALISTNOがあるかチェック
    indno_groups = df_stage1.groupby(indno_col)

    result_rows = []
    stage2_removed = 0
    stage2_aggregated_count = 0

    for indno, group in indno_groups:
        if len(group) == 1:
            # OYALISTNOが1つだけの場合はそのまま
            result_rows.append(group.iloc[0])
        else:
            # 複数のOYALISTNOがある場合
            # 必要数を合計
            total_qty = group[qty_col].sum()

            # デバッグ: 集約の詳細をログ出力（最初の3件のみ）
            if stage2_aggregated_count < 3:
                oyalistno_list = group[oyalistno_col].tolist()
                qty_list = group[qty_col].tolist()
                logger.info(f"    2段階目集約例: INDNO={indno}")
                logger.info(f"      OYALISTNOリスト: {oyalistno_list}")
                logger.info(f"      必要数リスト: {qty_list} → 合計: {total_qty}")

            # 1行目を基準に、必要数だけ上書き
            first_row = group.iloc[0].copy()
            first_row[qty_col] = total_qty
            result_rows.append(first_row)

            stage2_removed += len(group) - 1
            stage2_aggregated_count += 1

    df_final = pd.DataFrame(result_rows).reset_index(drop=True)

    if stage2_removed > 0:
        logger.info(f"  2段階目重複削除: {stage2_removed:,}行削除（必要数を集約） → {len(df_final):,}行")
        logger.info(f"  2段階目で集約されたINDNO数: {stage2_aggregated_count}件")

    # OYALISTNOカラムを削除（作業用なので出力に含めない）
    if oyalistno_col in df_final.columns:
        df_final = df_final.drop(columns=[oyalistno_col])

    total_removed = original_rows - len(df_final)
    logger.info(f"  合計重複削除: {total_removed:,}行削除 → {len(df_final):,}行")
    logger.info(f"  INDNOがユニークになりました: {df_final[indno_col].nunique()}件")

    return df_final


def read_csv_files():
    """環境変数からCSVファイルパスを読み込む"""
    csv_files = {
        'csv1': os.getenv('CSV1_PATH'),  # CAMKakouDenpyou.csv
        'csv2': os.getenv('CSV2_PATH'),  # CONV.csv
        'csv3': os.getenv('CSV3_PATH'),  # SEISANKI.csv
        'csv4': os.getenv('CSV4_PATH'),  # ASPKakouDenpyo.csv
    }

    # パスの存在確認
    for key, path in csv_files.items():
        if not path:
            logger.error(f"環境変数が設定されていません: {key.upper()}_PATH")
            return None

    return csv_files


def copy_simple_file(source_path, output_dir, output_filename=None):
    """
    CSVファイルをそのままコピー

    Args:
        source_path (str): ソースファイルパス
        output_dir (str): 出力先ディレクトリ
        output_filename (str, optional): 出力ファイル名（指定しない場合は元のファイル名）

    Returns:
        bool: 成功したらTrue
    """
    source_filename = os.path.basename(source_path)
    filename = output_filename if output_filename else source_filename

    try:
        if not os.path.exists(source_path):
            logger.error(f"ファイルが見つかりません: {source_path}")
            return False

        # 出力先ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        # ファイルをコピー
        dest_path = os.path.join(output_dir, filename)
        shutil.copy2(source_path, dest_path)

        # パーミッションを666に設定
        set_file_permissions(dest_path)

        file_size = os.path.getsize(dest_path)
        logger.info(f"✓ コピー完了: {filename} ({file_size:,} bytes)")
        return True

    except Exception as e:
        logger.error(f"✗ コピー失敗: {filename} - {e}")
        return False


def process_and_copy_file(source_path, output_dir, delete_columns=None, output_filename=None, rename_columns=None, filter_zero_columns=None, reorder_columns=None, use_advanced_deduplication=False, convert_kakoububan=False):
    """
    CSVファイルを加工してコピー（項目削除・重複削除・カラム名変更・0行フィルタ・カラム並び替え）

    Args:
        source_path (str): ソースファイルパス
        output_dir (str): 出力先ディレクトリ
        delete_columns (list): 削除対象カラムのリスト
        output_filename (str, optional): 出力ファイル名（指定しない場合は元のファイル名）
        rename_columns (dict, optional): カラム名変更マッピング（旧名: 新名）
        filter_zero_columns (list, optional): 指定カラムが全て0の行を削除
        reorder_columns (list, optional): カラムの並び順リスト
        use_advanced_deduplication (bool, optional): 高度な重複削除を使用（API呼び出し + 2段階削除）

    Returns:
        bool: 成功したらTrue
    """
    source_filename = os.path.basename(source_path)
    filename = output_filename if output_filename else source_filename

    try:
        if not os.path.exists(source_path):
            logger.error(f"ファイルが見つかりません: {source_path}")
            return False

        # CSVファイルを読み込み（エンコーディング自動検出）
        logger.info(f"読み込み中: {filename}")

        # 複数のエンコーディングを試行
        encodings = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis', 'latin1']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(source_path, encoding=encoding)
                logger.info(f"  エンコーディング: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            logger.error(f"  ✗ エンコーディングの検出に失敗しました")
            return False

        original_rows = len(df)
        logger.info(f"  元データ: {original_rows:,}行, {len(df.columns)}列")

        # 高度な重複削除を使用する場合、API呼び出しを先に実行（項目削除前）
        if use_advanced_deduplication:
            logger.info(f"  高度な重複削除モード: API呼び出しを実行")

            # QTY=0フィルタリング（D3420→D3110でQTY=0の行を除外）
            df = filter_qty_zero_from_api(df, indno_col='伝票No', lineno_col='行番号')

            # OYALISTNO取得
            df = fetch_oyalistno_from_api(df, indno_col='伝票No', lineno_col='行番号')

        # 項目削除
        if delete_columns:
            existing_columns = [col for col in delete_columns if col in df.columns]
            if existing_columns:
                df = df.drop(columns=existing_columns)
                logger.info(f"  項目削除: {len(existing_columns)}列削除 → {len(df.columns)}列")

        # カラム名変更
        if rename_columns:
            existing_renames = {old: new for old, new in rename_columns.items() if old in df.columns}
            if existing_renames:
                df = df.rename(columns=existing_renames)
                logger.info(f"  カラム名変更: {len(existing_renames)}列変更")
                for old, new in existing_renames.items():
                    logger.info(f"    '{old}' → '{new}'")

        # 重複行削除（高度な重複削除 or 通常の重複削除）
        if use_advanced_deduplication:
            # 2段階重複削除（INDNO → OYALISTNO、必要数の集約）
            df = deduplicate_with_oyalistno(df, indno_col='伝票No', oyalistno_col='OYALISTNO', qty_col='必要数')
        else:
            # 通常の重複削除（全カラムで判定）
            df_deduplicated = df.drop_duplicates()
            duplicates_removed = original_rows - len(df_deduplicated)
            if duplicates_removed > 0:
                logger.info(f"  重複削除: {duplicates_removed:,}行削除 → {len(df_deduplicated):,}行")
                df = df_deduplicated

        # 0行フィルタ（指定カラムが全て0の行を削除）
        if filter_zero_columns:
            existing_filter_columns = [col for col in filter_zero_columns if col in df.columns]
            if len(existing_filter_columns) == len(filter_zero_columns):
                # 全てのカラムが0の行を特定
                rows_before_filter = len(df)
                mask = (df[existing_filter_columns] == 0).all(axis=1)
                df = df[~mask]
                rows_filtered = rows_before_filter - len(df)
                if rows_filtered > 0:
                    logger.info(f"  0行フィルタ: {rows_filtered:,}行削除（{', '.join(existing_filter_columns)}が全て0） → {len(df):,}行")
            else:
                missing_columns = [col for col in filter_zero_columns if col not in df.columns]
                logger.warning(f"  0行フィルタ: スキップ（カラムが見つかりません: {', '.join(missing_columns)}）")

        # 数値列をint型に変換（空欄は空欄のまま）
        def convert_to_int(value):
            if pd.isna(value) or value == '':
                return ''
            try:
                return int(float(value))  # float経由でintに変換（202501.0 → 202501）
            except (ValueError, TypeError):
                return value  # 変換できない場合はそのまま

        # 「生産月次」列の変換
        if '生産月次' in df.columns:
            df['生産月次'] = df['生産月次'].apply(convert_to_int)
            logger.info(f"  生産月次列をint型に変換（空欄は保持）")

        # 「払出先」列の変換
        if '払出先' in df.columns:
            df['払出先'] = df['払出先'].apply(convert_to_int)
            logger.info(f"  払出先列をint型に変換（空欄は保持）")

        # 加工部番の HMCD → SETU_F 変換
        if convert_kakoububan and '加工部番' in df.columns:
            before = df['加工部番'].copy()
            df['加工部番'] = df['加工部番'].apply(convert_hmcd_to_setu_f)
            changed = (before != df['加工部番']).sum()
            logger.info(f"  加工部番変換（HMCD→SETU_F）: {changed:,}件変換")

        # カラムの並び替え
        if reorder_columns:
            # 指定されたカラムが全て存在するか確認
            existing_reorder_columns = [col for col in reorder_columns if col in df.columns]
            missing_columns = [col for col in reorder_columns if col not in df.columns]
            extra_columns = [col for col in df.columns if col not in reorder_columns]

            if missing_columns:
                logger.warning(f"  カラム並び替え: 指定されたカラムが見つかりません: {', '.join(missing_columns)}")

            if extra_columns:
                logger.warning(f"  カラム並び替え: 並び替え指定にないカラムがあります: {', '.join(extra_columns)}")

            # 指定された順番でカラムを並び替え（存在しないカラムは無視）
            if existing_reorder_columns:
                # 指定された順番のカラム + 指定されていない残りのカラム
                new_column_order = existing_reorder_columns + extra_columns
                df = df[new_column_order]
                logger.info(f"  カラム並び替え: {len(existing_reorder_columns)}列を指定順に並び替え")

        # 出力先ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        # CSVとして出力（Shift_JIS）
        dest_path = os.path.join(output_dir, filename)
        df.to_csv(dest_path, index=False, encoding='cp932')

        # パーミッションを666に設定
        set_file_permissions(dest_path)

        file_size = os.path.getsize(dest_path)
        logger.info(f"✓ 加工完了: {filename} ({file_size:,} bytes, encoding=cp932)")
        return True

    except Exception as e:
        logger.error(f"✗ 加工失敗: {filename} - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("処理1: rBOM CSVファイルコピー・加工処理を開始")
    logger.info("=" * 60)

    # 古いログファイルのクリーンアップ
    cleanup_old_logs(LOG_DIR, LOG_RETENTION_DAYS)

    # 環境変数からパスを取得
    csv_files = read_csv_files()
    if not csv_files:
        logger.error("環境変数の読み込みに失敗しました")
        return 1

    output_dir = os.getenv('OUTPUT_DIR_DENPYO', '/app/output/KakouDenpyo')
    logger.info(f"出力先: {output_dir}\n")

    # 加工対象ファイル名と削除カラム設定
    process_file1 = os.getenv('PROCESS_FILE1', 'CAMKakouDenpyou.csv')
    process_file2 = os.getenv('PROCESS_FILE2', 'ASPKakouDenpyo.csv')

    # 出力ファイル名の設定（半角スペースを含む名前に対応）
    output_file1 = os.getenv('OUTPUT_FILE1', '4-01 CAMKakouDenpyo.csv')
    output_file2 = os.getenv('OUTPUT_FILE2', '4-03 ASPKakouDenpyo.csv')

    # 削除カラムの取得（カンマ区切り）
    delete_columns_file1_str = os.getenv('DELETE_COLUMNS_FILE1', '')
    delete_columns_file2_str = os.getenv('DELETE_COLUMNS_FILE2', '')

    delete_columns_file1 = [col.strip() for col in delete_columns_file1_str.split(',') if col.strip()]
    delete_columns_file2 = [col.strip() for col in delete_columns_file2_str.split(',') if col.strip()]

    # カラム名変更マッピングの取得（形式: "旧名1:新名1,旧名2:新名2"）
    rename_columns_file1_str = os.getenv('RENAME_COLUMNS_FILE1', '')
    rename_columns_file2_str = os.getenv('RENAME_COLUMNS_FILE2', '')

    rename_columns_file1 = {}
    if rename_columns_file1_str:
        for pair in rename_columns_file1_str.split(','):
            if ':' in pair:
                old, new = pair.split(':', 1)
                rename_columns_file1[old.strip()] = new.strip()

    rename_columns_file2 = {}
    if rename_columns_file2_str:
        for pair in rename_columns_file2_str.split(','):
            if ':' in pair:
                old, new = pair.split(':', 1)
                rename_columns_file2[old.strip()] = new.strip()

    # カラム並び替え順序の取得（形式: "カラム1,カラム2,カラム3,..."）
    reorder_columns_file1_str = os.getenv('REORDER_COLUMNS_FILE1', '')
    reorder_columns_file2_str = os.getenv('REORDER_COLUMNS_FILE2', '')

    reorder_columns_file1 = [col.strip() for col in reorder_columns_file1_str.split(',') if col.strip()]
    reorder_columns_file2 = [col.strip() for col in reorder_columns_file2_str.split(',') if col.strip()]

    success_count = 0
    error_count = 0

    # 各ファイルを処理
    for key, source_path in csv_files.items():
        filename = os.path.basename(source_path)

        logger.info(f"[{success_count + error_count + 1}/{len(csv_files)}] 処理中: {filename}")

        # 加工対象ファイルかどうか判定
        if filename == process_file1:
            # CAMKakouDenpyou.csv - 項目削除・重複削除・カラム名変更・カラム並び替え
            if delete_columns_file1:
                logger.info(f"  削除対象カラム: {', '.join(delete_columns_file1)}")
            if reorder_columns_file1:
                logger.info(f"  カラム並び替え: {len(reorder_columns_file1)}列指定")
            logger.info(f"  出力ファイル名: {output_file1}")
            result = process_and_copy_file(source_path, output_dir, delete_columns_file1, output_file1, rename_columns_file1, None, reorder_columns_file1)
        elif filename == process_file2:
            # ASPKakouDenpyo.csv - 項目削除・高度な重複削除・カラム名変更・カラム並び替え
            if delete_columns_file2:
                logger.info(f"  削除対象カラム: {', '.join(delete_columns_file2)}")
            if reorder_columns_file2:
                logger.info(f"  カラム並び替え: {len(reorder_columns_file2)}列指定")
            logger.info(f"  出力ファイル名: {output_file2}")
            logger.info(f"  高度な重複削除: 有効（API呼び出し + 2段階削除 + 必要数集約）")
            result = process_and_copy_file(source_path, output_dir, delete_columns_file2, output_file2, rename_columns_file2, None, reorder_columns_file2, use_advanced_deduplication=True, convert_kakoububan=True)
        elif filename == 'CONV.csv':
            # CONV.csv - 0行フィルタ（数量・セットアップ・スペアが全て0の行を削除）
            logger.info(f"  0行フィルタ: 数量, セットアップ, スペアが全て0の行を削除")
            result = process_and_copy_file(source_path, output_dir, filter_zero_columns=['数量', 'セットアップ', 'スペア'])
        elif filename == 'SEISANKI.csv':
            # SEISANKI.csv - 0行フィルタ（数量・セットアップ・スペアが全て0の行を削除）
            logger.info(f"  0行フィルタ: 数量, セットアップ, スペアが全て0の行を削除")
            result = process_and_copy_file(source_path, output_dir, filter_zero_columns=['数量', 'セットアップ', 'スペア'])
        else:
            # その他のファイル - そのままコピー
            result = copy_simple_file(source_path, output_dir)

        if result:
            success_count += 1
        else:
            error_count += 1

        logger.info("")

    # 処理結果サマリー
    logger.info("=" * 60)
    logger.info("処理1完了")
    logger.info(f"成功: {success_count}ファイル")
    logger.info(f"失敗: {error_count}ファイル")
    logger.info("=" * 60)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    exit(main())
