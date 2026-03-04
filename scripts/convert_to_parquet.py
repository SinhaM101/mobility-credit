#!/usr/bin/env python3
"""
Convert CSV files to Parquet format for better MapReduce performance.
Parquet is a columnar storage format optimized for analytics workloads.
"""

import pandas as pd
import os

# Configuration
ACS_MERGED_DIR = "./data/acs_merged"
VOTING_FILE = "./data/countypres_2000-2024.csv"
OUTPUT_DIR = "./data/parquet"

def convert_acs_to_parquet():
    """Convert ACS merged CSV files to Parquet."""
    categories = ["economic", "social", "housing", "demographic"]
    
    for category in categories:
        csv_path = os.path.join(ACS_MERGED_DIR, category, f"{category}_all_years.csv")
        
        if not os.path.exists(csv_path):
            print(f"  Skipping {category}: file not found")
            continue
        
        print(f"  Converting {category}...")
        df = pd.read_csv(csv_path)
        
        # Create output directory
        parquet_dir = os.path.join(OUTPUT_DIR, category)
        os.makedirs(parquet_dir, exist_ok=True)
        
        # Save as Parquet
        parquet_path = os.path.join(parquet_dir, f"{category}_all_years.parquet")
        df.to_parquet(parquet_path, index=False)
        
        print(f"    Saved: {parquet_path}")
        print(f"    Rows: {len(df):,}, Columns: {len(df.columns)}")
        
        # Also save 2020 only for faster analysis
        if 'year' in df.columns:
            df_2020 = df[df['year'] == 2020]
            parquet_2020 = os.path.join(parquet_dir, f"{category}_2020.parquet")
            df_2020.to_parquet(parquet_2020, index=False)
            print(f"    Saved 2020: {parquet_2020} ({len(df_2020):,} rows)")

def convert_voting_to_parquet():
    """Convert voting CSV to Parquet."""
    print("  Converting voting data...")
    
    df = pd.read_csv(VOTING_FILE)
    
    parquet_dir = os.path.join(OUTPUT_DIR, "voting")
    os.makedirs(parquet_dir, exist_ok=True)
    
    # Full dataset
    parquet_path = os.path.join(parquet_dir, "countypres_all_years.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"    Saved: {parquet_path}")
    print(f"    Rows: {len(df):,}, Columns: {len(df.columns)}")
    
    # 2020 only
    df_2020 = df[df['year'] == 2020]
    parquet_2020 = os.path.join(parquet_dir, "countypres_2020.parquet")
    df_2020.to_parquet(parquet_2020, index=False)
    print(f"    Saved 2020: {parquet_2020} ({len(df_2020):,} rows)")

def main():
    print("=" * 60)
    print("Converting CSV to Parquet")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\nACS Data:")
    convert_acs_to_parquet()
    
    print("\nVoting Data:")
    convert_voting_to_parquet()
    
    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)
    
    # Show file sizes
    print("\nFile sizes:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for f in files:
            path = os.path.join(root, f)
            size_mb = os.path.getsize(path) / 1024 / 1024
            print(f"  {path}: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
