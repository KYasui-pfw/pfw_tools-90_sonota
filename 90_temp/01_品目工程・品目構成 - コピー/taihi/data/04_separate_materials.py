import pandas as pd
import os

# Define input and output paths
input_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\04_分解再結合\前工程横展開_分解.csv"
output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\05_素材分離"

# Read the decomposed CSV file
try:
    df = pd.read_csv(input_file, encoding='shift_jis')
    print(f"Successfully read input file with {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
except Exception as e:
    print(f"Error reading input file: {e}")
    exit(1)

# Find the minimum No for each 完成部番
min_no_per_part = df.groupby('完成部番')['No'].min().reset_index()
min_no_per_part.columns = ['完成部番', 'MinNo']

print(f"Found minimum No for {len(min_no_per_part)} unique 完成部番")

# Merge back to original dataframe to identify which rows have minimum No
df_with_min = df.merge(min_no_per_part, on='完成部番', how='left')
df_with_min['IsMinNo'] = df_with_min['No'] == df_with_min['MinNo']

# Split into two dataframes
品目構成_df = df_with_min[df_with_min['IsMinNo'] == True].copy()
品目工程_df = df_with_min[df_with_min['IsMinNo'] == False].copy()

# Remove the helper columns
品目構成_df = 品目構成_df.drop(['MinNo', 'IsMinNo'], axis=1)
品目工程_df = 品目工程_df.drop(['MinNo', 'IsMinNo'], axis=1)

print(f"品目構成input.csv: {len(品目構成_df)} rows")
print(f"品目工程input.csv: {len(品目工程_df)} rows")
print(f"Total: {len(品目構成_df) + len(品目工程_df)} rows (should match original {len(df)})")

# Save the files
品目構成_file = os.path.join(output_dir, "品目構成input.csv")
品目工程_file = os.path.join(output_dir, "品目工程input.csv")

品目構成_df.to_csv(品目構成_file, index=False, encoding='shift_jis')
品目工程_df.to_csv(品目工程_file, index=False, encoding='shift_jis')

print(f"品目構成input.csv saved to: {品目構成_file}")
print(f"品目工程input.csv saved to: {品目工程_file}")
print("Process completed successfully!")