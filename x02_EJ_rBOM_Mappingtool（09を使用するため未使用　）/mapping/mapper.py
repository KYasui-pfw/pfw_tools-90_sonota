"""
マッピングエンジン
EJシステムとrBOMシステムのデータをマッピングする
"""
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime

class MappingEngine:
    """マッピング処理エンジン"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def execute_mapping(self, ej_data: List[Dict], rbom_data: List[Dict], manual_mappings: List[Dict] = None, fixed_mappings: List[Dict] = None) -> List[Dict]:
        """
        マッピング処理を実行（手動・固定マッピング考慮版）
        
        Args:
            ej_data: EJシステムのデータリスト
            rbom_data: rBOMシステムのデータリスト
            manual_mappings: 手動マッピングデータのリスト
            fixed_mappings: 固定マッピングデータのリスト
            
        Returns:
            マッピング結果のリスト
        """
        
        # DataFrameに変換
        ej_df = pd.DataFrame(ej_data) if ej_data else pd.DataFrame()
        rbom_df = pd.DataFrame(rbom_data) if rbom_data else pd.DataFrame()
        manual_df = pd.DataFrame(manual_mappings) if manual_mappings else pd.DataFrame()
        fixed_df = pd.DataFrame(fixed_mappings) if fixed_mappings else pd.DataFrame()
        
        # マッピング結果を格納するリスト
        mapping_results = []
        
        # 1. 手動マッピングと一致するEJ・rBOMデータを除外
        if not manual_df.empty:
            if not ej_df.empty:
                manual_ej_orders = manual_df['ej_order_no'].dropna().unique()
                ej_df = ej_df[~ej_df['order_no'].isin(manual_ej_orders)]
            
            if not rbom_df.empty:
                manual_rbom_keys = manual_df[['rbom_order_no', 'rbom_line_no']].dropna()
                rbom_keys = rbom_df[['order_no', 'line_no']].apply(tuple, axis=1)
                manual_keys = manual_rbom_keys.apply(tuple, axis=1)
                rbom_df = rbom_df[~rbom_keys.isin(manual_keys)]
            
            # 手動マッピングデータをマッピング結果に追加
            for _, manual_row in manual_df.iterrows():
                result = self._create_mapping_result_from_manual(manual_row, '手動')
                mapping_results.append(result)
        
        # 2. 固定マッピングと一致するEJ・rBOMデータを除外
        if not fixed_df.empty:
            if not ej_df.empty:
                fixed_ej_orders = fixed_df['ej_order_no'].dropna().unique()
                ej_df = ej_df[~ej_df['order_no'].isin(fixed_ej_orders)]
            
            if not rbom_df.empty:
                fixed_rbom_keys = fixed_df[['rbom_order_no', 'rbom_line_no']].dropna()
                rbom_keys = rbom_df[['order_no', 'line_no']].apply(tuple, axis=1)
                fixed_keys = fixed_rbom_keys.apply(tuple, axis=1)
                rbom_df = rbom_df[~rbom_keys.isin(fixed_keys)]
            
            # 固定マッピングデータをマッピング結果に追加
            for _, fixed_row in fixed_df.iterrows():
                result = self._create_mapping_result_from_fixed(fixed_row, '自動')
                mapping_results.append(result)
        
        # EJデータとrBOMデータの対応関係を記録
        ej_matched = set()
        rbom_matched = set()
        
        # 3. 残ったデータで自動マッピング実行（品目コード + 数量）
        if not ej_df.empty and not rbom_df.empty:
            for ej_idx, ej_row in ej_df.iterrows():
                ej_item_code = ej_row.get('item_code')
                ej_quantity = ej_row.get('quantity')
                
                # NoneやNaNの場合はスキップ
                if pd.isna(ej_item_code) or pd.isna(ej_quantity):
                    continue
                
                # rBOMデータから対応するものを検索
                for rbom_idx, rbom_row in rbom_df.iterrows():
                    rbom_item_code = rbom_row.get('item_code')
                    rbom_quantity = rbom_row.get('receive_quantity')
                    
                    # NoneやNaNの場合はスキップ
                    if pd.isna(rbom_item_code) or pd.isna(rbom_quantity):
                        continue
                    
                    # 既にマッチング済みの場合はスキップ
                    if rbom_idx in rbom_matched:
                        continue
                    
                    # マッピング条件チェック：品目コード + 数量
                    if (str(ej_item_code).strip() == str(rbom_item_code).strip() and 
                        float(ej_quantity) == float(rbom_quantity)):
                        
                        # マッチング成功
                        result = self._create_mapping_result(
                            ej_row, rbom_row, '自動'
                        )
                        mapping_results.append(result)
                        
                        # マッチング済みとして記録
                        ej_matched.add(ej_idx)
                        rbom_matched.add(rbom_idx)
                        break
        
        # 4. EJのみのデータ（マッチングしなかったEJデータ）- 「自動」として表示
        if not ej_df.empty:
            for ej_idx, ej_row in ej_df.iterrows():
                if ej_idx not in ej_matched:
                    result = self._create_mapping_result(
                        ej_row, None, '自動'  # EJ_ONLYも「自動」として表示
                    )
                    mapping_results.append(result)
        
        # 5. rBOMのみのデータ（マッチングしなかったrBOMデータ）- 「自動」として表示
        if not rbom_df.empty:
            for rbom_idx, rbom_row in rbom_df.iterrows():
                if rbom_idx not in rbom_matched:
                    result = self._create_mapping_result(
                        None, rbom_row, '自動'  # rBOM_ONLYも「自動」として表示
                    )
                    mapping_results.append(result)
        
        return mapping_results
    
    def _create_mapping_result(self, ej_row, rbom_row, mapping_type: str) -> Dict:
        """
        マッピング結果レコードを作成
        
        Args:
            ej_row: EJデータの行（pandas Series or None）
            rbom_row: rBOMデータの行（pandas Series or None）
            mapping_type: マッピングタイプ（自動/手動）
            
        Returns:
            マッピング結果の辞書
        """
        
        result = {
            'mapping_type': mapping_type,
            'is_fixed': False  # デフォルトは固定なし
        }
        
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
                'rbom_quantity': rbom_row.get('receive_quantity'),
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
    
    def _create_mapping_result_from_manual(self, manual_row, mapping_type: str) -> Dict:
        """
        手動マッピングレコードからマッピング結果レコードを作成
        
        Args:
            manual_row: 手動マッピングデータの行（pandas Series）
            mapping_type: マッピングタイプ
            
        Returns:
            マッピング結果の辞書
        """
        
        result = {
            'ej_order_no': manual_row.get('ej_order_no'),
            'ej_item_code': manual_row.get('ej_item_code'),
            'ej_item_name': manual_row.get('ej_item_name'),
            'ej_quantity': manual_row.get('ej_quantity'),
            'ej_status': manual_row.get('ej_status'),
            'ej_purch_odr_typ': manual_row.get('ej_purch_odr_typ'),
            'ej_delivery_date': manual_row.get('ej_delivery_date'),
            'rbom_order_no': manual_row.get('rbom_order_no'),
            'rbom_line_no': manual_row.get('rbom_line_no'),
            'rbom_item_code': manual_row.get('rbom_item_code'),
            'rbom_item_name': manual_row.get('rbom_item_name'),
            'rbom_quantity': manual_row.get('rbom_quantity'),
            'rbom_delivery_date': manual_row.get('rbom_delivery_date'),
            'rbom_seino': manual_row.get('rbom_seino'),
            'mapping_type': mapping_type,
            'is_fixed': True  # 手動マッピングは常に固定
        }
        
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
        
        result = {
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
        
        # タイプ別カウント
        auto_count = len([r for r in mapping_results if r['mapping_type'] == '自動'])
        manual_count = len([r for r in mapping_results if r['mapping_type'] == '手動'])
        total_count = len(mapping_results)
        
        return {
            'total_count': total_count,
            'auto_count': auto_count,
            'manual_count': manual_count
        }
    
    def find_potential_matches(self, ej_data: List[Dict], rbom_data: List[Dict]) -> List[Dict]:
        """
        潜在的なマッチング候補を探す（品目コードのみ一致）
        手動マッピング用の参考情報として使用
        
        Args:
            ej_data: EJシステムのデータリスト
            rbom_data: rBOMシステムのデータリスト
            
        Returns:
            潜在的マッチングのリスト
        """
        
        potential_matches = []
        
        if not ej_data or not rbom_data:
            return potential_matches
        
        ej_df = pd.DataFrame(ej_data)
        rbom_df = pd.DataFrame(rbom_data)
        
        for ej_idx, ej_row in ej_df.iterrows():
            ej_item_code = ej_row.get('item_code')
            ej_quantity = ej_row.get('quantity')
            
            if pd.isna(ej_item_code):
                continue
            
            # 品目コードが一致するrBOMデータを検索
            matching_rbom = rbom_df[rbom_df['item_code'] == ej_item_code]
            
            for rbom_idx, rbom_row in matching_rbom.iterrows():
                rbom_quantity = rbom_row.get('receive_quantity')
                
                # 数量が異なる場合のみ潜在的マッチングとして記録
                if not pd.isna(rbom_quantity) and float(ej_quantity) != float(rbom_quantity):
                    potential_matches.append({
                        'ej_item_code': ej_item_code,
                        'ej_quantity': ej_quantity,
                        'ej_order_no': ej_row.get('order_no'),
                        'rbom_quantity': rbom_quantity,
                        'rbom_order_no': rbom_row.get('order_no'),
                        'quantity_diff': abs(float(ej_quantity) - float(rbom_quantity))
                    })
        
        # 数量差でソート（差が小さい順）
        potential_matches.sort(key=lambda x: x['quantity_diff'])
        
        return potential_matches