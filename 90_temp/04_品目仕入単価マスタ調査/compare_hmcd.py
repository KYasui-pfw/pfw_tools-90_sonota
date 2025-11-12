import pandas as pd
import os
from datetime import datetime

# 入力ファイルパス
master_file = 'M0910_品目仕入単価マスタ.csv'
source_file = '仕入単価_元.csv'

# 出力フォルダ
output_dir = '比較結果'
os.makedirs(output_dir, exist_ok=True)

# CSVファイルを読み込み
print(f'Reading {master_file}...')
master_df = pd.read_csv(master_file, encoding='utf-8-sig')
print(f'  Records: {len(master_df)}')

print(f'Reading {source_file}...')
# エンコーディングを自動判定して読み込み
try:
    source_df = pd.read_csv(source_file, encoding='utf-8-sig')
except UnicodeDecodeError:
    print('  UTF-8 failed, trying Shift-JIS (cp932)...')
    source_df = pd.read_csv(source_file, encoding='cp932')
print(f'  Records: {len(source_df)}')

# HMCDのセットを作成
master_hmcd_set = set(master_df['HMCD'].unique())
source_hmcd_set = set(source_df['HMCD'].unique())

print(f'\nMaster unique HMCD count: {len(master_hmcd_set)}')
print(f'Source unique HMCD count: {len(source_hmcd_set)}')

# 一致するHMCDと一致しないHMCDを抽出
matched_hmcd = master_hmcd_set & source_hmcd_set
master_only_hmcd = master_hmcd_set - source_hmcd_set
source_only_hmcd = source_hmcd_set - master_hmcd_set

print(f'\nMatched HMCD count: {len(matched_hmcd)}')
print(f'Master only HMCD count: {len(master_only_hmcd)}')
print(f'Source only HMCD count: {len(source_only_hmcd)}')

# データを振り分け
master_matched = master_df[master_df['HMCD'].isin(matched_hmcd)]
master_unmatched = master_df[master_df['HMCD'].isin(master_only_hmcd)]
source_matched = source_df[source_df['HMCD'].isin(matched_hmcd)]
source_unmatched = source_df[source_df['HMCD'].isin(source_only_hmcd)]

# 結果を出力
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

master_matched_file = os.path.join(output_dir, f'01_master_matched_{timestamp}.csv')
master_unmatched_file = os.path.join(output_dir, f'02_master_unmatched_{timestamp}.csv')
source_matched_file = os.path.join(output_dir, f'03_source_matched_{timestamp}.csv')
source_unmatched_file = os.path.join(output_dir, f'04_source_unmatched_{timestamp}.csv')

print(f'\nWriting results...')
master_matched.to_csv(master_matched_file, index=False, encoding='utf-8-sig')
print(f'  {master_matched_file}: {len(master_matched)} records')

master_unmatched.to_csv(master_unmatched_file, index=False, encoding='utf-8-sig')
print(f'  {master_unmatched_file}: {len(master_unmatched)} records')

source_matched.to_csv(source_matched_file, index=False, encoding='utf-8-sig')
print(f'  {source_matched_file}: {len(source_matched)} records')

source_unmatched.to_csv(source_unmatched_file, index=False, encoding='utf-8-sig')
print(f'  {source_unmatched_file}: {len(source_unmatched)} records')

# サマリーレポート作成
summary_file = os.path.join(output_dir, f'00_summary_{timestamp}.txt')
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write('=== HMCD比較結果サマリー ===\n\n')
    f.write(f'処理日時: {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n\n')
    f.write(f'入力ファイル:\n')
    f.write(f'  マスタファイル: {master_file} ({len(master_df)} records)\n')
    f.write(f'  元ファイル: {source_file} ({len(source_df)} records)\n\n')
    f.write(f'HMCD統計:\n')
    f.write(f'  マスタ側ユニークHMCD数: {len(master_hmcd_set)}\n')
    f.write(f'  元側ユニークHMCD数: {len(source_hmcd_set)}\n')
    f.write(f'  一致したHMCD数: {len(matched_hmcd)}\n')
    f.write(f'  マスタのみのHMCD数: {len(master_only_hmcd)}\n')
    f.write(f'  元のみのHMCD数: {len(source_only_hmcd)}\n\n')
    f.write(f'出力ファイル:\n')
    f.write(f'  01_master_matched: {len(master_matched)} records\n')
    f.write(f'  02_master_unmatched: {len(master_unmatched)} records\n')
    f.write(f'  03_source_matched: {len(source_matched)} records\n')
    f.write(f'  04_source_unmatched: {len(source_unmatched)} records\n')

print(f'\n  {summary_file}: Summary report created')
print('\nProcessing completed successfully!')