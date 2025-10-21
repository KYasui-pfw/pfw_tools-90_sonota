"""
マッピングエンジン
EJシステムとrBOMシステムのデータをマッピングする
"""
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MappingEngine:
    """マッピング処理エンジン"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def execute_mapping(self, ej_data: List[Dict], rbom_data: List[Dict], manual_mappings: List[Dict] = None,
                       fixed_mappings: List[Dict] = None,
                       ej_after_rbom_days: int = None, ej_before_rbom_days: int = None,
                       enable_quantity_diff: bool = False) -> List[Dict]:
        """
        マッピング処理を実行（手動マッピング優先 + 固定マッピング考慮版 + 納期条件 + 数量差分処理）

        Args:
            ej_data: EJシステムのデータリスト
            rbom_data: rBOMシステムのデータリスト
            manual_mappings: 手動マッピングデータのリスト（EJ発注番号とrBOM発注番号+行番号の対応）
            fixed_mappings: 固定マッピングデータのリスト
            ej_after_rbom_days: EJ納期がrBOM納期より遅い許容日数（Noneの場合は制限なし）
            ej_before_rbom_days: EJ納期がrBOM納期より早い許容日数（Noneの場合は制限なし）
            enable_quantity_diff: 数量差分処理を有効にするか（Trueの場合、連番を増やして差分行を追加）

        Returns:
            マッピング結果のリスト
        """
        logger.info(f"マッピングエンジン開始 - EJ: {len(ej_data) if ej_data else 0}件, rBOM: {len(rbom_data) if rbom_data else 0}件, 手動: {len(manual_mappings) if manual_mappings else 0}件, 固定: {len(fixed_mappings) if fixed_mappings else 0}件")
        logger.info(f"納期条件 - EJ≧rBOM: {ej_after_rbom_days if ej_after_rbom_days is not None else '制限なし'}日, EJ≦rBOM: {ej_before_rbom_days if ej_before_rbom_days is not None else '制限なし'}日")
        logger.info(f"数量差分処理: {'有効' if enable_quantity_diff else '無効'}")

        # DataFrameに変換
        start_time = datetime.now()
        ej_df = pd.DataFrame(ej_data) if ej_data else pd.DataFrame()
        rbom_df = pd.DataFrame(rbom_data) if rbom_data else pd.DataFrame()
        manual_df = pd.DataFrame(manual_mappings) if manual_mappings else pd.DataFrame()
        fixed_df = pd.DataFrame(fixed_mappings) if fixed_mappings else pd.DataFrame()
        logger.debug(f"DataFrame変換完了 ({(datetime.now() - start_time).total_seconds():.3f}秒)")

        # マッピング結果を格納するリスト
        mapping_results = []

        # 手動マッピングの統計情報
        manual_mapping_success_count = 0
        manual_mapping_failed_count = 0
        manual_mapping_failed_details = []  # 失敗した手動マッピングの詳細リスト

        # 1. 手動マッピング処理（最優先）
        if not manual_df.empty and not ej_df.empty and not rbom_df.empty:
            logger.info(f"【フェーズ1】手動マッピング処理開始")
            start_time = datetime.now()

            original_ej_count = len(ej_df)
            original_rbom_count = len(rbom_df)

            # 手動マッピングに基づいてEJとrBOMをマッピング
            for _, manual_row in manual_df.iterrows():
                ej_order_no = manual_row.get('ej_order_no')
                rbom_order_no = manual_row.get('rbom_order_no')
                rbom_line_no = manual_row.get('rbom_line_no')

                # EJデータを検索
                ej_match = ej_df[ej_df['order_no'] == ej_order_no]
                if ej_match.empty:
                    logger.warning(f"  手動マッピング: EJ発注番号 {ej_order_no} が見つかりません")
                    manual_mapping_failed_count += 1
                    manual_mapping_failed_details.append({
                        'ej_order_no': ej_order_no,
                        'rbom_order_no': rbom_order_no,
                        'rbom_line_no': rbom_line_no,
                        'reason': 'EJ発注番号が見つかりません'
                    })
                    continue

                # rBOMデータを検索（発注番号+行番号で一致）
                rbom_match = rbom_df[
                    (rbom_df['order_no'] == rbom_order_no) &
                    (rbom_df['line_no'] == int(rbom_line_no))
                ]
                if rbom_match.empty:
                    logger.warning(f"  手動マッピング: rBOM発注番号 {rbom_order_no}+{rbom_line_no} が見つかりません")
                    manual_mapping_failed_count += 1
                    manual_mapping_failed_details.append({
                        'ej_order_no': ej_order_no,
                        'rbom_order_no': rbom_order_no,
                        'rbom_line_no': rbom_line_no,
                        'reason': 'rBOM発注番号+行番号が見つかりません'
                    })
                    continue

                # マッピングしたデータをマッピング結果に追加（EJ/rBOM両方に数量差分処理対応）
                ej_row = ej_match.iloc[0]
                rbom_row = rbom_match.iloc[0]

                # 数量を取得
                ej_qty = ej_row['quantity']
                rbom_qty = rbom_row['order_quantity']

                if enable_quantity_diff and pd.notna(ej_qty) and pd.notna(rbom_qty):
                    # 数量差分処理が有効で、両方の数量が有効な場合
                    ej_qty_num = float(ej_qty)
                    rbom_qty_num = float(rbom_qty)

                    # マッピング数量 = min(EJ数量, rBOM数量)
                    mapping_qty = min(ej_qty_num, rbom_qty_num)

                    # EJ/rBOMの現在の連番を取得
                    ej_current_sequence = 1
                    rbom_current_sequence = 1

                    # 同じEJ発注番号の既存の連番を確認
                    existing_ej_sequences = [r.get('ej_m_sequence') for r in mapping_results
                                            if r.get('ej_order_no') == ej_order_no and r.get('ej_m_sequence') is not None]
                    if existing_ej_sequences:
                        ej_current_sequence = max(existing_ej_sequences) + 1

                    # 同じrBOM発注番号+行番号の既存の連番を確認
                    existing_rbom_sequences = [r.get('rbom_m_sequence') for r in mapping_results
                                              if r.get('rbom_order_no') == rbom_order_no
                                              and r.get('rbom_line_no') == rbom_line_no
                                              and r.get('rbom_m_sequence') is not None]
                    if existing_rbom_sequences:
                        rbom_current_sequence = max(existing_rbom_sequences) + 1

                    # マッピング結果を作成
                    ej_series = pd.Series({
                        'order_no': ej_row['order_no'],
                        'item_code': ej_row['item_code'],
                        'item_name': ej_row['item_name'],
                        'quantity': mapping_qty,
                        'status': ej_row['status'],
                        'purch_odr_typ': ej_row['purch_odr_typ'],
                        'delivery_date': ej_row['delivery_date']
                    })

                    rbom_series = pd.Series({
                        'order_no': rbom_row['order_no'],
                        'line_no': rbom_row['line_no'],
                        'item_code': rbom_row['item_code'],
                        'item_name': rbom_row['item_name'],
                        'order_quantity': mapping_qty,
                        'delivery_date': rbom_row['delivery_date'],
                        'seino': rbom_row['seino']
                    })

                    result = self._create_mapping_result(ej_series, rbom_series, '自動',
                                                         ej_m_sequence=ej_current_sequence,
                                                         rbom_m_sequence=rbom_current_sequence)
                    result['is_manual_mapping'] = True  # 手動マッピングフラグ
                    mapping_results.append(result)
                    logger.debug(f"  手動マッピング適用: EJ={ej_order_no}(連番{ej_current_sequence}) ↔ rBOM={rbom_order_no}+{rbom_line_no}(連番{rbom_current_sequence}), 数量={mapping_qty}")

                    # EJ/rBOMの残数を計算
                    ej_remaining = ej_qty_num - mapping_qty
                    rbom_remaining = rbom_qty_num - mapping_qty

                    # EJの数量をDataFrame上で更新（残数がある場合）または除外（残数ゼロの場合）
                    if ej_remaining > 0:
                        ej_df.loc[ej_df['order_no'] == ej_order_no, 'quantity'] = ej_remaining
                        logger.debug(f"  EJ数量更新: {ej_order_no} → 残数={ej_remaining}")
                    else:
                        ej_df = ej_df[ej_df['order_no'] != ej_order_no]
                        logger.debug(f"  EJ完全除外: {ej_order_no} (残数なし)")

                    # rBOMの数量をDataFrame上で更新（残数がある場合）または除外（残数ゼロの場合）
                    if rbom_remaining > 0:
                        rbom_df.loc[(rbom_df['order_no'] == rbom_order_no) &
                                   (rbom_df['line_no'] == int(rbom_line_no)), 'order_quantity'] = rbom_remaining
                        logger.debug(f"  rBOM数量更新: {rbom_order_no}+{rbom_line_no} → 残数={rbom_remaining}")
                    else:
                        rbom_df = rbom_df[~((rbom_df['order_no'] == rbom_order_no) & (rbom_df['line_no'] == int(rbom_line_no)))]
                        logger.debug(f"  rBOM完全除外: {rbom_order_no}+{rbom_line_no} (残数なし)")

                else:
                    # 数量差分処理が無効、または数量がNoneの場合は通常マッピング
                    ej_series = pd.Series({
                        'order_no': ej_row['order_no'],
                        'item_code': ej_row['item_code'],
                        'item_name': ej_row['item_name'],
                        'quantity': ej_qty,
                        'status': ej_row['status'],
                        'purch_odr_typ': ej_row['purch_odr_typ'],
                        'delivery_date': ej_row['delivery_date']
                    })

                    rbom_series = pd.Series({
                        'order_no': rbom_row['order_no'],
                        'line_no': rbom_row['line_no'],
                        'item_code': rbom_row['item_code'],
                        'item_name': rbom_row['item_name'],
                        'order_quantity': rbom_qty,
                        'delivery_date': rbom_row['delivery_date'],
                        'seino': rbom_row['seino']
                    })

                    result = self._create_mapping_result(ej_series, rbom_series, '自動')
                    result['is_manual_mapping'] = True  # 手動マッピングフラグ
                    mapping_results.append(result)
                    logger.debug(f"  手動マッピング適用: EJ={ej_order_no} ↔ rBOM={rbom_order_no}+{rbom_line_no}, is_manual_mapping={result.get('is_manual_mapping')}")

                    # 数量差分処理無効の場合は完全除外
                    ej_df = ej_df[ej_df['order_no'] != ej_order_no]
                    rbom_df = rbom_df[~((rbom_df['order_no'] == rbom_order_no) & (rbom_df['line_no'] == int(rbom_line_no)))]
                    logger.debug(f"  EJ/rBOM完全除外: {ej_order_no}, {rbom_order_no}+{rbom_line_no}")

                manual_mapping_success_count += 1

            logger.debug(f"  EJ除外: {original_ej_count}件 → {len(ej_df)}件 (除外: {original_ej_count - len(ej_df)}件)")
            logger.debug(f"  rBOM除外: {original_rbom_count}件 → {len(rbom_df)}件 (除外: {original_rbom_count - len(rbom_df)}件)")
            logger.info(f"手動マッピング処理完了: {len(manual_df)}件処理、成功{manual_mapping_success_count}件、失敗{manual_mapping_failed_count}件 ({(datetime.now() - start_time).total_seconds():.3f}秒)")
        elif not manual_df.empty:
            # 手動マッピングデータが存在するが、EJまたはrBOMデータが空の場合
            manual_mapping_failed_count = len(manual_df)
            for _, manual_row in manual_df.iterrows():
                manual_mapping_failed_details.append({
                    'ej_order_no': manual_row.get('ej_order_no'),
                    'rbom_order_no': manual_row.get('rbom_order_no'),
                    'rbom_line_no': manual_row.get('rbom_line_no'),
                    'reason': 'EJまたはrBOMデータが空です'
                })
            logger.warning(f"手動マッピング処理スキップ: EJまたはrBOMデータが空です（手動マッピング登録: {len(manual_df)}件）")

        # 2. 固定マッピングと一致するEJ・rBOMデータを除外
        if not fixed_df.empty:
            logger.info(f"【フェーズ2】固定マッピング除外処理開始")
            start_time = datetime.now()

            original_ej_count = len(ej_df) if not ej_df.empty else 0
            original_rbom_count = len(rbom_df) if not rbom_df.empty else 0

            if not ej_df.empty:
                fixed_ej_orders = fixed_df['ej_order_no'].dropna().unique()
                ej_df = ej_df[~ej_df['order_no'].isin(fixed_ej_orders)]
                logger.debug(f"  EJ除外: {original_ej_count}件 → {len(ej_df)}件 (除外: {original_ej_count - len(ej_df)}件)")

            if not rbom_df.empty:
                fixed_rbom_keys = fixed_df[['rbom_order_no', 'rbom_line_no']].dropna()
                rbom_keys = rbom_df[['order_no', 'line_no']].apply(tuple, axis=1)
                fixed_keys = fixed_rbom_keys.apply(tuple, axis=1)
                rbom_df = rbom_df[~rbom_keys.isin(fixed_keys)]
                logger.debug(f"  rBOM除外: {original_rbom_count}件 → {len(rbom_df)}件 (除外: {original_rbom_count - len(rbom_df)}件)")

            # 固定マッピングデータをマッピング結果に追加
            for _, fixed_row in fixed_df.iterrows():
                result = self._create_mapping_result_from_fixed(fixed_row, '自動')
                mapping_results.append(result)

            logger.info(f"固定マッピング除外完了: {len(mapping_results)}件追加 ({(datetime.now() - start_time).total_seconds():.3f}秒)")
        
        # EJデータとrBOMデータの対応関係を記録
        ej_matched = set()
        rbom_matched = set()

        # 3. 残ったデータで自動マッピング実行（品目コード→納期の順でソートマッピング）
        if not ej_df.empty and not rbom_df.empty:
            logger.info(f"【フェーズ3】自動マッピング実行開始 - EJ: {len(ej_df)}件 × rBOM: {len(rbom_df)}件")
            start_time = datetime.now()

            # データ準備とソート
            sort_start = datetime.now()
            ej_df_sorted = ej_df.copy()
            ej_df_sorted['item_code_clean'] = ej_df_sorted['item_code'].astype(str).str.strip()
            ej_df_sorted['delivery_date_dt'] = pd.to_datetime(ej_df_sorted['delivery_date'], errors='coerce')
            ej_df_sorted['ej_original_idx'] = ej_df_sorted.index

            rbom_df_sorted = rbom_df.copy()
            rbom_df_sorted['item_code_clean'] = rbom_df_sorted['item_code'].astype(str).str.strip()
            rbom_df_sorted['delivery_date_dt'] = pd.to_datetime(rbom_df_sorted['delivery_date'], errors='coerce')
            rbom_df_sorted['rbom_original_idx'] = rbom_df_sorted.index

            # 品目コード（昇順）→納期（昇順）でソート
            # NaT（日付なし）を最後に配置するため、NaTを最大値として扱う
            ej_df_sorted = ej_df_sorted.sort_values(
                by=['item_code_clean', 'delivery_date_dt'],
                ascending=[True, True],
                na_position='last'
            )
            rbom_df_sorted = rbom_df_sorted.sort_values(
                by=['item_code_clean', 'delivery_date_dt'],
                ascending=[True, True],
                na_position='last'
            )
            logger.debug(f"  データソート完了 ({(datetime.now() - sort_start).total_seconds():.3f}秒)")

            # 品目コード別にグループ化してマッピング
            mapping_start = datetime.now()
            match_count = 0

            # EJ側の品目コードでグループ化
            ej_groups = ej_df_sorted.groupby('item_code_clean', sort=False)
            rbom_groups = rbom_df_sorted.groupby('item_code_clean', sort=False)

            # 各品目コードごとにマッピング
            for item_code, ej_group in ej_groups:
                # 同じ品目コードのrBOMグループを取得
                if item_code not in rbom_groups.groups:
                    continue  # rBOM側に該当品目コードがない場合はスキップ

                rbom_group = rbom_groups.get_group(item_code)

                if enable_quantity_diff:
                    # 数量差分処理が有効な場合：EJ発注ごとに複数rBOM行を消化
                    ej_idx = 0
                    rbom_idx = 0
                    # rBOM残数を管理する辞書 ((order_no, line_no) -> 残数量) - 品目コードグループ全体で共有
                    rbom_remaining_map = {}

                    while ej_idx < len(ej_group) and rbom_idx < len(rbom_group):
                        ej_row = ej_group.iloc[ej_idx]

                        # 納期条件に合うrBOM行を探す
                        rbom_row = None
                        temp_rbom_idx = rbom_idx
                        while temp_rbom_idx < len(rbom_group):
                            candidate_rbom = rbom_group.iloc[temp_rbom_idx]
                            delivery_date_ok = self._check_delivery_date_condition(
                                ej_row['delivery_date_dt'],
                                candidate_rbom['delivery_date_dt'],
                                ej_after_rbom_days,
                                ej_before_rbom_days
                            )
                            if delivery_date_ok:
                                rbom_row = candidate_rbom
                                rbom_idx = temp_rbom_idx
                                break
                            temp_rbom_idx += 1

                        if rbom_row is None:
                            # 納期条件に合うrBOM行がない場合、次のEJへ
                            ej_idx += 1
                            continue

                        # EJ/rBOM数量を取得
                        ej_qty = ej_row['quantity']
                        rbom_qty = rbom_row['order_quantity']

                        if pd.notna(ej_qty) and pd.notna(rbom_qty):
                            ej_remaining = float(ej_qty)
                            ej_order_no = ej_row['order_no']

                            # 既存の連番を確認してEJ連番を初期化（手動マッピングの連番を引き継ぐ）
                            existing_ej_sequences = [r.get('ej_m_sequence') for r in mapping_results
                                                    if r.get('ej_order_no') == ej_order_no and r.get('ej_m_sequence') is not None]
                            ej_sequence = max(existing_ej_sequences) + 1 if existing_ej_sequences else 1

                            # デバッグログ追加
                            if ej_order_no == 'E8857378':
                                logger.info(f"[連番DEBUG] EJ発注番号={ej_order_no}")
                                logger.info(f"[連番DEBUG] mapping_results総数={len(mapping_results)}")
                                logger.info(f"[連番DEBUG] 同じEJ発注番号のエントリ数={len([r for r in mapping_results if r.get('ej_order_no') == ej_order_no])}")
                                logger.info(f"[連番DEBUG] existing_ej_sequences={existing_ej_sequences}")
                                logger.info(f"[連番DEBUG] 決定した連番={ej_sequence}")
                                # mapping_resultsの最初の10件をサンプル出力
                                logger.info(f"[連番DEBUG] mapping_resultsサンプル（最初10件）:")
                                for i, r in enumerate(mapping_results[:10]):
                                    logger.info(f"  [{i}] ej_order_no={r.get('ej_order_no')}, ej_m_sequence={r.get('ej_m_sequence')}, is_manual={r.get('is_manual_mapping')}")

                            # EJ残数量を複数rBOM行に順次割り当て

                            while ej_remaining > 0 and rbom_idx < len(rbom_group):
                                rbom_row = rbom_group.iloc[rbom_idx]

                                # 納期条件チェック
                                delivery_date_ok = self._check_delivery_date_condition(
                                    ej_row['delivery_date_dt'],
                                    rbom_row['delivery_date_dt'],
                                    ej_after_rbom_days,
                                    ej_before_rbom_days
                                )

                                if not delivery_date_ok:
                                    # 納期条件に合わない場合は次のrBOM行へ
                                    rbom_idx += 1
                                    continue

                                # rBOMデータのバリデーション
                                if pd.notna(rbom_row['order_no']) and pd.notna(rbom_row['line_no']):
                                    rbom_order_no_str = rbom_row['order_no']
                                    rbom_line_no_int = rbom_row['line_no']
                                    rbom_original_idx = rbom_row['rbom_original_idx']
                                    rbom_key = (rbom_order_no_str, rbom_line_no_int)

                                    # DEBUG: キーと辞書の内容を確認
                                    logger.debug(f"  [DEBUG] rbom_key={rbom_key} (型: {type(rbom_key[0])}, {type(rbom_key[1])})")
                                    logger.debug(f"  [DEBUG] rbom_remaining_map keys={list(rbom_remaining_map.keys())}")
                                    logger.debug(f"  [DEBUG] rbom_key in map? {rbom_key in rbom_remaining_map}")

                                    # rBOM数量を取得（残数がある場合は残数を使用）
                                    if rbom_key in rbom_remaining_map:
                                        rbom_qty_num = rbom_remaining_map[rbom_key]
                                        logger.debug(f"  [DEBUG] 残数マップから取得: {rbom_qty_num}")
                                    else:
                                        rbom_qty_num = float(rbom_row['order_quantity'])
                                        logger.debug(f"  [DEBUG] 元数量から取得: {rbom_qty_num}")

                                    # 既存の連番を確認してrBOM連番を取得（手動マッピングの連番を引き継ぐ）
                                    existing_rbom_sequences = [r.get('rbom_m_sequence') for r in mapping_results
                                                              if r.get('rbom_order_no') == rbom_order_no_str
                                                              and r.get('rbom_line_no') == rbom_line_no_int
                                                              and r.get('rbom_m_sequence') is not None]
                                    rbom_sequence = max(existing_rbom_sequences) + 1 if existing_rbom_sequences else 1

                                    # デバッグログ追加（rBOM側）
                                    logger.debug(f"[rBOM連番DEBUG] rBOM発注番号+行番号={rbom_order_no_str}+{rbom_line_no_int}")
                                    logger.debug(f"[rBOM連番DEBUG] existing_rbom_sequences={existing_rbom_sequences}")
                                    logger.debug(f"[rBOM連番DEBUG] 決定した連番={rbom_sequence}")

                                    # マッピング数量を決定（min(EJ残数, rBOM数量)）
                                    mapping_qty = min(ej_remaining, rbom_qty_num)

                                    # EJ側のSeriesを作成
                                    ej_series = pd.Series({
                                        'order_no': ej_order_no,
                                        'item_code': ej_row['item_code'],
                                        'item_name': ej_row['item_name'],
                                        'quantity': mapping_qty,
                                        'status': ej_row['status'],
                                        'purch_odr_typ': ej_row['purch_odr_typ'],
                                        'delivery_date': ej_row['delivery_date']
                                    })

                                    # rBOM側のSeriesを作成
                                    rbom_series = pd.Series({
                                        'order_no': rbom_order_no_str,
                                        'line_no': rbom_line_no_int,
                                        'item_code': rbom_row['item_code'],
                                        'item_name': rbom_row['item_name'],
                                        'order_quantity': mapping_qty,
                                        'delivery_date': rbom_row['delivery_date'],
                                        'seino': rbom_row['seino']
                                    })

                                    # マッピング結果を追加（EJ/rBOM両方の連番を指定）
                                    result = self._create_mapping_result(ej_series, rbom_series, '自動',
                                                                         ej_m_sequence=ej_sequence,
                                                                         rbom_m_sequence=rbom_sequence)
                                    mapping_results.append(result)

                                    # マッピング済みとして記録
                                    ej_matched.add(ej_row['ej_original_idx'])
                                    rbom_matched.add(rbom_original_idx)
                                    match_count += 1

                                    logger.debug(f"  数量消化: EJ({ej_order_no}, 連番{ej_sequence}) x rBOM({rbom_order_no_str}+{rbom_line_no_int}, 連番{rbom_sequence}) - マッピング量{mapping_qty}, 元数量{float(rbom_row['order_quantity'])}, 使用数量{rbom_qty_num}")

                                    # 残数量を更新
                                    ej_remaining -= mapping_qty
                                    rbom_remaining = rbom_qty_num - mapping_qty

                                    # rBOM残数がある場合、残数マップに保存（次のループで再利用）
                                    if rbom_remaining > 0:
                                        rbom_remaining_map[rbom_key] = rbom_remaining
                                        logger.debug(f"  rBOM残数保存: rBOM({rbom_order_no_str}+{rbom_line_no_int}) - 残数{rbom_remaining} (次のマッピングで再利用)")
                                        logger.debug(f"  [DEBUG] 残数保存後のマップ: {dict(rbom_remaining_map)}")
                                        # 同じrBOM行を再度処理するため、rbom_idxを進めない
                                    else:
                                        # rBOM数量が完全に消化された場合のみ次の行へ
                                        rbom_idx += 1
                                        # 残数マップから削除（既に消化済み）
                                        rbom_remaining_map.pop(rbom_key, None)
                                        logger.debug(f"  rBOM完全消化: rBOM({rbom_order_no_str}+{rbom_line_no_int}) - 次の行へ")
                                        logger.debug(f"  [DEBUG] 完全消化後のマップ: {dict(rbom_remaining_map)}")

                                    ej_sequence += 1
                                else:
                                    # rBOMデータが無効な場合はスキップ
                                    rbom_idx += 1

                            # EJ残数量がある場合、EJ_ONLYとして追加
                            if ej_remaining > 0:
                                ej_series = pd.Series({
                                    'order_no': ej_order_no,
                                    'item_code': ej_row['item_code'],
                                    'item_name': ej_row['item_name'],
                                    'quantity': ej_remaining,
                                    'status': ej_row['status'],
                                    'purch_odr_typ': ej_row['purch_odr_typ'],
                                    'delivery_date': ej_row['delivery_date']
                                })
                                result = self._create_mapping_result(ej_series, None, '自動', ej_m_sequence=ej_sequence)
                                mapping_results.append(result)
                                ej_matched.add(ej_row['ej_original_idx'])
                                logger.debug(f"  EJ未消化残: {ej_order_no} 連番{ej_sequence} 残{ej_remaining}")
                        else:
                            # 数量がNoneの場合は通常マッピング
                            ej_series = pd.Series({
                                'order_no': ej_row['order_no'],
                                'item_code': ej_row['item_code'],
                                'item_name': ej_row['item_name'],
                                'quantity': ej_qty,
                                'status': ej_row['status'],
                                'purch_odr_typ': ej_row['purch_odr_typ'],
                                'delivery_date': ej_row['delivery_date']
                            })
                            rbom_series = pd.Series({
                                'order_no': rbom_row['order_no'],
                                'line_no': rbom_row['line_no'],
                                'item_code': rbom_row['item_code'],
                                'item_name': rbom_row['item_name'],
                                'order_quantity': rbom_qty,
                                'delivery_date': rbom_row['delivery_date'],
                                'seino': rbom_row['seino']
                            })
                            result = self._create_mapping_result(ej_series, rbom_series, '自動')
                            mapping_results.append(result)
                            ej_matched.add(ej_row['ej_original_idx'])
                            rbom_matched.add(rbom_row['rbom_original_idx'])
                            match_count += 1
                            rbom_idx += 1

                        ej_idx += 1

                    # 品目コードグループのEJ処理完了後、rbom_remaining_mapに残っている残数をrBOM_ONLYとして追加
                    logger.debug(f"  品目コード={item_code} のEJ処理完了、rbom_remaining_map残存確認")
                    for (rbom_order_no_str, rbom_line_no_int), rbom_remaining_qty in rbom_remaining_map.items():
                        # 残数マップに残っているエントリをrBOM_ONLYとして追加
                        # rbom_groupから元のデータを取得
                        rbom_row_data = rbom_group[
                            (rbom_group['order_no'] == rbom_order_no_str) &
                            (rbom_group['line_no'] == rbom_line_no_int)
                        ]

                        if not rbom_row_data.empty:
                            rbom_row = rbom_row_data.iloc[0]
                            rbom_original_idx = rbom_row['rbom_original_idx']

                            # 既存の連番を確認してrBOM連番を取得
                            existing_rbom_sequences = [r.get('rbom_m_sequence') for r in mapping_results
                                                      if r.get('rbom_order_no') == rbom_order_no_str
                                                      and r.get('rbom_line_no') == rbom_line_no_int
                                                      and r.get('rbom_m_sequence') is not None]
                            rbom_sequence = max(existing_rbom_sequences) + 1 if existing_rbom_sequences else 1

                            # rBOM_ONLY行を作成
                            rbom_series = pd.Series({
                                'order_no': rbom_order_no_str,
                                'line_no': rbom_line_no_int,
                                'item_code': rbom_row['item_code'],
                                'item_name': rbom_row['item_name'],
                                'order_quantity': rbom_remaining_qty,
                                'delivery_date': rbom_row['delivery_date'],
                                'seino': rbom_row['seino']
                            })

                            result = self._create_mapping_result(None, rbom_series, '自動', rbom_m_sequence=rbom_sequence)
                            mapping_results.append(result)
                            rbom_matched.add(rbom_original_idx)
                            logger.debug(f"  rBOM残数出力: rBOM({rbom_order_no_str}+{rbom_line_no_int}, 連番{rbom_sequence}) - 残数{rbom_remaining_qty}")

                else:
                    # 差分処理無効時：1対1の通常マッピング
                    min_count = min(len(ej_group), len(rbom_group))

                    for i in range(min_count):
                        ej_row = ej_group.iloc[i]
                        rbom_row = rbom_group.iloc[i]

                        # 納期条件チェック
                        delivery_date_ok = self._check_delivery_date_condition(
                            ej_row['delivery_date_dt'],
                            rbom_row['delivery_date_dt'],
                            ej_after_rbom_days,
                            ej_before_rbom_days
                        )

                        if not delivery_date_ok:
                            continue

                        # rBOMデータのバリデーション
                        if pd.notna(rbom_row['order_no']) and pd.notna(rbom_row['line_no']):
                            ej_series = pd.Series({
                                'order_no': ej_row['order_no'],
                                'item_code': ej_row['item_code'],
                                'item_name': ej_row['item_name'],
                                'quantity': ej_row['quantity'],
                                'status': ej_row['status'],
                                'purch_odr_typ': ej_row['purch_odr_typ'],
                                'delivery_date': ej_row['delivery_date']
                            })
                            rbom_series = pd.Series({
                                'order_no': rbom_row['order_no'],
                                'line_no': rbom_row['line_no'],
                                'item_code': rbom_row['item_code'],
                                'item_name': rbom_row['item_name'],
                                'order_quantity': rbom_row['order_quantity'],
                                'delivery_date': rbom_row['delivery_date'],
                                'seino': rbom_row['seino']
                            })
                            result = self._create_mapping_result(ej_series, rbom_series, '自動')
                            mapping_results.append(result)
                            ej_matched.add(ej_row['ej_original_idx'])
                            rbom_matched.add(rbom_row['rbom_original_idx'])
                            match_count += 1

            logger.debug(f"  品目コード別マッピング完了 ({(datetime.now() - mapping_start).total_seconds():.3f}秒)")
            logger.info(f"自動マッピング完了: {match_count}件マッピング (合計: {(datetime.now() - start_time).total_seconds():.3f}秒)")

        # 4. EJのみのデータ（マッピングしなかったEJデータ）- 「自動」として表示（ベクトル化）
        ej_only_count = 0
        if not ej_df.empty:
            logger.info(f"【フェーズ4】EJ_ONLY処理開始")
            start_time = datetime.now()

            # 未マッピングのEJデータを一括抽出
            ej_only_df = ej_df[~ej_df.index.isin(ej_matched)]
            logger.debug(f"  未マッピングEJデータ抽出: {len(ej_only_df)}件")

            # to_dict('records')でリスト化して一括処理
            for ej_record in ej_only_df.to_dict('records'):
                ej_series = pd.Series(ej_record)

                # 既存の連番を確認（手動マッピングや自動マッピングで使用済みの連番を引き継ぐ）
                ej_order_no = ej_series.get('order_no')
                existing_ej_sequences = [r.get('ej_m_sequence') for r in mapping_results
                                        if r.get('ej_order_no') == ej_order_no and r.get('ej_m_sequence') is not None]
                ej_sequence = max(existing_ej_sequences) + 1 if existing_ej_sequences else 1

                result = self._create_mapping_result(
                    ej_series, None, '自動', ej_m_sequence=ej_sequence  # EJ_ONLYも「自動」として表示
                )
                mapping_results.append(result)
                ej_only_count += 1

            logger.info(f"EJ_ONLY追加完了: {ej_only_count}件 ({(datetime.now() - start_time).total_seconds():.3f}秒)")

        # 5. rBOMのみのデータ（マッピングしなかったrBOMデータ）- 「自動」として表示（ベクトル化）
        rbom_only_count = 0
        if not rbom_df.empty:
            logger.info(f"【フェーズ5】rBOM_ONLY処理開始")
            start_time = datetime.now()

            # 未マッピングのrBOMデータを一括抽出
            rbom_only_df = rbom_df[~rbom_df.index.isin(rbom_matched)]
            logger.debug(f"  未マッピングrBOMデータ抽出: {len(rbom_only_df)}件")

            # to_dict('records')でリスト化して一括処理
            for rbom_record in rbom_only_df.to_dict('records'):
                # rBOMデータのバリデーション：order_noとline_noが有効な場合のみ追加
                if pd.notna(rbom_record.get('order_no')) and pd.notna(rbom_record.get('line_no')):
                    rbom_series = pd.Series(rbom_record)
                    result = self._create_mapping_result(
                        None, rbom_series, '自動'  # rBOM_ONLYも「自動」として表示
                    )
                    mapping_results.append(result)
                    rbom_only_count += 1
                else:
                    logger.warning(f"rBOM_ONLYデータが無効（order_no={rbom_record.get('order_no')}, line_no={rbom_record.get('line_no')}）- スキップ")

            logger.info(f"rBOM_ONLY追加完了: {rbom_only_count}件 ({(datetime.now() - start_time).total_seconds():.3f}秒)")

        logger.info(f"マッピングエンジン完了 - 総結果: {len(mapping_results)}件")

        # 結果と統計情報を返す
        return {
            'mapping_results': mapping_results,
            'manual_mapping_success_count': manual_mapping_success_count,
            'manual_mapping_failed_count': manual_mapping_failed_count,
            'manual_mapping_failed_details': manual_mapping_failed_details
        }
    
    def _create_mapping_result(self, ej_row, rbom_row, mapping_type: str,
                               ej_m_sequence: int = None, rbom_m_sequence: int = None) -> Dict:
        """
        マッピング結果レコードを作成

        Args:
            ej_row: EJデータの行（pandas Series or None）
            rbom_row: rBOMデータの行（pandas Series or None）
            mapping_type: マッピングタイプ（常に'自動'）
            ej_m_sequence: EJ連番（指定がある場合のみ使用）
            rbom_m_sequence: rBOM連番（指定がある場合のみ使用）

        Returns:
            マッピング結果の辞書
        """

        result = {
            'mapping_type': mapping_type,
            'is_fixed': False,  # デフォルトは固定なし
            'ej_m_sequence': ej_m_sequence,  # 連番を保存（Noneの場合はdb_manager側でデフォルト処理）
            'rbom_m_sequence': rbom_m_sequence
        }

        # 統一品目コード（マッピング時はEJ/rBOM共通、未マッピング時は存在する側の品目コード）
        item_code = None
        if ej_row is not None and rbom_row is not None:
            # マッピング済み：EJの品目コードを使用
            item_code = ej_row.get('item_code')
        elif ej_row is not None:
            # EJ_ONLY
            item_code = ej_row.get('item_code')
        elif rbom_row is not None:
            # rBOM_ONLY
            item_code = rbom_row.get('item_code')

        result['item_code'] = item_code

        # EJ側データ
        if ej_row is not None:
            result.update({
                'ej_order_no': ej_row.get('order_no'),
                'ej_item_code': ej_row.get('item_code'),
                'ej_item_name': ej_row.get('item_name'),
                'ej_quantity': ej_row.get('quantity'),
                'ej_status': ej_row.get('status'),
                'ej_purch_odr_typ': ej_row.get('purch_odr_typ'),
                'ej_delivery_date': ej_row.get('delivery_date')
            })
        else:
            # EJ側データがない場合は空値
            result.update({
                'ej_order_no': None,
                'ej_item_code': None,
                'ej_item_name': None,
                'ej_quantity': None,
                'ej_status': None,
                'ej_purch_odr_typ': None,
                'ej_delivery_date': None
            })

        # rBOM側データ
        if rbom_row is not None:
            result.update({
                'rbom_order_no': rbom_row.get('order_no'),
                'rbom_line_no': rbom_row.get('line_no'),
                'rbom_item_code': rbom_row.get('item_code'),
                'rbom_item_name': rbom_row.get('item_name'),
                'rbom_quantity': rbom_row.get('order_quantity'),
                'rbom_delivery_date': rbom_row.get('delivery_date'),
                'rbom_seino': rbom_row.get('seino')
            })
        else:
            # rBOM側データがない場合は空値
            result.update({
                'rbom_order_no': None,
                'rbom_line_no': None,
                'rbom_item_code': None,
                'rbom_item_name': None,
                'rbom_quantity': None,
                'rbom_delivery_date': None,
                'rbom_seino': None
            })

        return result

    def _create_mapping_result_from_fixed(self, fixed_row, mapping_type: str) -> Dict:
        """
        固定マッピングレコードからマッピング結果レコードを作成
        
        Args:
            fixed_row: 固定マッピングデータの行（pandas Series）
            mapping_type: マッピングタイプ
            
        Returns:
            マッピング結果の辞書
        """
        
        # 統一品目コード（固定マッピングから取得）
        item_code = fixed_row.get('item_code')
        if item_code is None:
            # item_codeが保存されていない場合はej_item_codeまたはrbom_item_codeから取得
            item_code = fixed_row.get('ej_item_code') or fixed_row.get('rbom_item_code')

        result = {
            'item_code': item_code,
            'ej_order_no': fixed_row.get('ej_order_no'),
            'ej_item_code': fixed_row.get('ej_item_code'),
            'ej_item_name': fixed_row.get('ej_item_name'),
            'ej_quantity': fixed_row.get('ej_quantity'),
            'ej_status': fixed_row.get('ej_status'),
            'ej_purch_odr_typ': fixed_row.get('ej_purch_odr_typ'),
            'ej_delivery_date': fixed_row.get('ej_delivery_date'),
            'rbom_order_no': fixed_row.get('rbom_order_no'),
            'rbom_line_no': fixed_row.get('rbom_line_no'),
            'rbom_item_code': fixed_row.get('rbom_item_code'),
            'rbom_item_name': fixed_row.get('rbom_item_name'),
            'rbom_quantity': fixed_row.get('rbom_quantity'),
            'rbom_delivery_date': fixed_row.get('rbom_delivery_date'),
            'rbom_seino': fixed_row.get('rbom_seino'),
            'mapping_type': mapping_type,
            'is_fixed': True  # 固定マッピングは常に固定
        }

        return result

    def _check_delivery_date_condition(self, ej_date, rbom_date, ej_after_rbom_days, ej_before_rbom_days) -> bool:
        """
        納期条件をチェック

        Args:
            ej_date: EJ納期（pandas Timestamp or NaT）
            rbom_date: rBOM納期（pandas Timestamp or NaT）
            ej_after_rbom_days: EJ≧rBOM許容日数（Noneの場合は制限なし）
            ej_before_rbom_days: EJ≦rBOM許容日数（Noneの場合は制限なし）

        Returns:
            True: 条件を満たす, False: 条件を満たさない
        """
        # 両方の納期がNaT（日付なし）の場合は条件なしでマッピング許可
        if pd.isna(ej_date) or pd.isna(rbom_date):
            return True

        # 両方の条件がNone（制限なし）の場合は全て許可
        if ej_after_rbom_days is None and ej_before_rbom_days is None:
            return True

        # 日数差を計算（EJ - rBOM）
        days_diff = (ej_date - rbom_date).days

        # EJ≧rBOMの条件チェック（EJがrBOMより遅い場合）
        if ej_after_rbom_days is not None and days_diff > 0:
            # EJの方が遅い場合、許容日数以内かチェック
            if days_diff > ej_after_rbom_days:
                return False

        # EJ≦rBOMの条件チェック（EJがrBOMより早い場合）
        if ej_before_rbom_days is not None and days_diff < 0:
            # EJの方が早い場合、許容日数以内かチェック
            if abs(days_diff) > ej_before_rbom_days:
                return False

        return True

    def get_mapping_statistics(self, mapping_results: List[Dict]) -> Dict:
        """
        マッピング統計情報を取得
        
        Args:
            mapping_results: マッピング結果のリスト
            
        Returns:
            統計情報の辞書
        """
        
        if not mapping_results:
            return {
                'total_count': 0,
                'matched_count': 0,
                'ej_only_count': 0,
                'rbom_only_count': 0,
                'match_rate': 0.0
            }
        
        # カウント（全て自動マッピング）
        total_count = len(mapping_results)

        return {
            'total_count': total_count
        }