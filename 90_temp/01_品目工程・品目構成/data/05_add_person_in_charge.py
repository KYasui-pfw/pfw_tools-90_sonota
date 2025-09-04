import pandas as pd
import os

# Define input and output paths
品目構成_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\05_素材分離\品目構成input.csv"
output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\055_ヒアリング用"
output_file = os.path.join(output_dir, "担当者追加品目構成.csv")

# Original CSV files with person in charge info
original_files = [
    r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\01_加工前\前工程横展開.csv",
    r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\01_加工前\前工程横展開(C).csv",
    r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\01_加工前\前工程横展開(I).csv"
]

# Read the 品目構成input.csv file
try:
    品目構成_df = pd.read_csv(品目構成_file, encoding='shift_jis')
    print(f"Successfully read 品目構成input.csv with {len(品目構成_df)} rows")
except Exception as e:
    print(f"Error reading 品目構成input.csv: {e}")
    exit(1)

# Create a dictionary to store 完成部番 -> 担当者 mapping
担当者_mapping = {}

# Read each original file and build the mapping
for file_path in original_files:
    try:
        df = pd.read_csv(file_path, encoding='shift_jis')
        print(f"Successfully read {os.path.basename(file_path)} with {len(df)} rows")
        
        # The first column is 担当者, second column is 完成部番
        for _, row in df.iterrows():
            担当者 = row.iloc[0] if pd.notna(row.iloc[0]) else ""
            完成部番 = row.iloc[1] if pd.notna(row.iloc[1]) else ""
            
            if 完成部番 and 担当者:
                担当者_mapping[完成部番] = 担当者
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        continue

print(f"Created mapping for {len(担当者_mapping)} 完成部番-担当者 pairs")

# Add 担当者 column to 品目構成_df
品目構成_df['担当者'] = 品目構成_df['完成部番'].map(担当者_mapping).fillna("")

# Reorder columns to put 担当者 first
columns = ['担当者'] + [col for col in 品目構成_df.columns if col != '担当者']
品目構成_df = 品目構成_df[columns]

print(f"Added 担当者 column. Rows with 担当者: {(品目構成_df['担当者'] != '').sum()}")
print(f"Rows without 担当者: {(品目構成_df['担当者'] == '').sum()}")

# Save the result
品目構成_df.to_csv(output_file, index=False, encoding='shift_jis')

print(f"担当者追加品目構成.csv saved to: {output_file}")
print("Process completed successfully!")