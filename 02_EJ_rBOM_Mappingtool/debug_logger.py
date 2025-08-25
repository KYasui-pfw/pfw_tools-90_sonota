"""
デバッグログ出力モジュール
"""
import os
from datetime import datetime
import pandas as pd

class DebugLogger:
    def __init__(self, log_file="debug.log"):
        self.log_file = log_file
        self.init_log()
    
    def init_log(self):
        """ログファイルに新しいセッション開始を記録"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== 新しいセッション開始 {datetime.now()} ===\n\n")
    
    def log(self, message):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
        # print(f"[DEBUG] {message}")  # コンソール出力を無効化
    
    def log_dataframe_info(self, df, name):
        """DataFrameの詳細情報をログ出力"""
        self.log(f"=== {name} DataFrame情報 ===")
        self.log(f"Shape: {df.shape}")
        self.log(f"Columns: {list(df.columns)}")
        
        # pandas.NA の存在チェック
        na_info = []
        for col in df.columns:
            na_count = df[col].isna().sum()
            if na_count > 0:
                na_info.append(f"  {col}: {na_count} NA values")
        
        if na_info:
            self.log("pandas.NA 存在:")
            for info in na_info:
                self.log(info)
        else:
            self.log("pandas.NA は存在しません")
        
        # サンプルデータ
        if not df.empty:
            self.log("サンプルデータ (最初の3行):")
            for i, (_, row) in enumerate(df.head(3).iterrows()):
                self.log(f"  行{i}: {dict(row)}")
        
        self.log("")  # 空行
    
    def log_value_details(self, value, name):
        """値の詳細情報をログ出力"""
        self.log(f"{name}: {repr(value)} (type: {type(value)}, is_na: {pd.isna(value)})")
    
    def log_dict_details(self, data_dict, name):
        """辞書の詳細情報をログ出力（pandas.NA検出付き）"""
        self.log(f"=== {name} 辞書情報 ===")
        na_keys = []
        for key, value in data_dict.items():
            if pd.isna(value):
                na_keys.append(f"  {key}: {repr(value)} (type: {type(value)})")
        
        if na_keys:
            self.log("pandas.NA が検出されたキー:")
            for na_key in na_keys:
                self.log(na_key)
        else:
            self.log("pandas.NA は検出されませんでした")
        
        # 重要なキーの詳細表示
        important_keys = ['ej_order_no', 'ej_item_code', 'ej_item_name', 'ej_quantity', 'ej_delivery_date',
                         'rbom_order_no', 'rbom_line_no', 'is_fixed', 'is_fixed_edited']
        self.log("重要なキーの値:")
        for key in important_keys:
            if key in data_dict:
                value = data_dict[key]
                self.log(f"  {key}: {repr(value)} (type: {type(value)}, is_na: {pd.isna(value)})")
        
        self.log("")  # 空行

# グローバルロガーインスタンス
debug_logger = DebugLogger()