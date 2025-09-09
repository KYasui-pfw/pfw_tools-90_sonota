import pandas as pd
import os

# Define input and output paths
input_file = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\03_結合後\前工程横展開_結合.csv"
output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\04_分解再結合"
output_file = os.path.join(output_dir, "前工程横展開_分解_全行.csv")

# Read the combined CSV file
try:
    df = pd.read_csv(input_file, encoding='shift_jis')
    print(f"Successfully read input file with {len(df)} rows")
except Exception as e:
    print(f"Error reading input file: {e}")
    exit(1)

# Create the new decomposed dataframe
decomposed_data = []

for index, row in df.iterrows():
    完成部番 = row.iloc[0]  # First column is 完成部番
    
    # Process each set of columns (分子, 分母, 前工程) in reverse order (6→1)
    for i in range(6, 0, -1):  # 6, 5, 4, 3, 2, 1
        no = 7 - i  # This creates: 6→1, 5→2, 4→3, 3→4, 2→5, 1→6
        
        # Calculate column indices for each set
        分子_col = 1 + (i-1) * 3  # 1, 4, 7, 10, 13, 16
        分母_col = 2 + (i-1) * 3  # 2, 5, 8, 11, 14, 17
        前工程_col = 3 + (i-1) * 3  # 3, 6, 9, 12, 15, 18
        
        if 前工程_col < len(row):
            単位数分子 = row.iloc[分子_col] if 分子_col < len(row) else ""
            単位数分母 = row.iloc[分母_col] if 分母_col < len(row) else ""
            前工程 = row.iloc[前工程_col] if 前工程_col < len(row) else ""
            
            # Include all rows, even if 前工程 is blank
            decomposed_data.append({
                '完成部番': 完成部番,
                'No': no,
                '単位数分子': 単位数分子 if pd.notna(単位数分子) else "",
                '単位数分母': 単位数分母 if pd.notna(単位数分母) else "",
                '前工程': 前工程 if pd.notna(前工程) else ""
            })

# Create DataFrame from decomposed data
decomposed_df = pd.DataFrame(decomposed_data)

# Save the decomposed file
decomposed_df.to_csv(output_file, index=False, encoding='shift_jis')

print(f"Decomposed CSV saved to: {output_file}")
print(f"Original rows: {len(df)}")
print(f"Decomposed rows: {len(decomposed_df)}")
print(f"Expected rows (6x original): {len(df) * 6}")
print("Process completed successfully!")