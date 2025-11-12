import pandas as pd
import sys
import codecs

# UTF-8出力設定
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# CSVファイル読み込み
df = pd.read_csv('MK020_差分比較結果.csv', encoding='utf-8-sig')

# 値が変更された行を抽出
modified = df[df['差分状態'] == '値が変更'].head(5)

print('【値が変更された例】')
for i, row in modified.iterrows():
    print(f'\n{i+1}. {row["OYAHMCD"]} - {row["KTCD"]}')
    diff = str(row["差分詳細"])
    if len(diff) > 300:
        print(f'   差分: {diff[:300]}...')
    else:
        print(f'   差分: {diff}')
