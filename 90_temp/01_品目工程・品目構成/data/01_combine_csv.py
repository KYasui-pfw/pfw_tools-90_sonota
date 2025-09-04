import pandas as pd
import os

# Define input and output directories
input_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\02_加工後"
output_dir = r"C:\Dev\90_tools\90_temp\01_品目工程・品目構成\data\03_結合後"

# CSV files to combine
csv_files = [
    "前工程横展開.csv",
    "前工程横展開(C).csv", 
    "前工程横展開(I).csv"
]

# Read all CSV files and combine them
combined_df = pd.DataFrame()

for i, filename in enumerate(csv_files):
    file_path = os.path.join(input_dir, filename)
    try:
        # Try different encodings
        for encoding in ['shift_jis', 'cp932', 'utf-8']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"Successfully read {filename} with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        else:
            print(f"Could not read {filename} with any encoding")
            continue
            
        # For the first file, include header
        if i == 0:
            combined_df = df
        else:
            # For subsequent files, append without header (skip first row)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
            
        print(f"Added {len(df)} rows from {filename}")
        
    except Exception as e:
        print(f"Error reading {filename}: {e}")

# Save the combined file
output_file = os.path.join(output_dir, "前工程横展開_結合.csv")
combined_df.to_csv(output_file, index=False, encoding='shift_jis')

print(f"Combined CSV saved to: {output_file}")
print(f"Total rows: {len(combined_df)}")