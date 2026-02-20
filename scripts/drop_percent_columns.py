#!/usr/bin/env python3
"""
Drop all percentage columns from raw data CSVs.
"""

import pandas as pd
import os
import glob

RAW_DATA_DIR = "./data/acs_downloads/raw_data"

def main():
    print("=" * 70)
    print("Dropping percentage columns from raw data CSVs")
    print("=" * 70)
    
    csv_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    print(f"Found {len(csv_files)} CSV files\n")
    
    for csv_file in sorted(csv_files):
        filename = os.path.basename(csv_file)
        
        df = pd.read_csv(csv_file)
        original_cols = len(df.columns)
        
        # Find columns containing "percent" (case-insensitive)
        percent_cols = [col for col in df.columns if "percent" in col.lower()]
        
        # Drop percentage columns
        df = df.drop(columns=percent_cols, errors='ignore')
        
        new_cols = len(df.columns)
        dropped = original_cols - new_cols
        
        # Save
        df.to_csv(csv_file, index=False)
        print(f"{filename}: dropped {dropped} columns ({original_cols} -> {new_cols})")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
