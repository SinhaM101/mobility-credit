#!/usr/bin/env python3
"""
Merge ACS Data Files

Merges all state-level ACS CSV files into single consolidated files per year
and creates a master file combining all years.

Output structure:
    data/acs_merged/
    ├── economic/
    │   ├── economic_2009.csv
    │   ├── economic_2010.csv
    │   ├── ...
    │   └── economic_all_years.csv
    ├── social/
    ├── housing/
    └── demographic/
"""

import pandas as pd
import os
import glob
from pathlib import Path

# Configuration
ACS_DIR = "./data/acs_downloads"
OUTPUT_DIR = "./data/acs_merged"

DATASETS = {
    "economic": {
        "source_dir": "economic",
        "file_pattern": "*_DP03_Economic_FULL.csv",
        "table": "DP03"
    },
    "social": {
        "source_dir": "social", 
        "file_pattern": "*_DP02_Social_FULL.csv",
        "table": "DP02"
    },
    "housing": {
        "source_dir": "housing",
        "file_pattern": "*_DP04_Housing_FULL.csv", 
        "table": "DP04"
    },
    "demographic": {
        "source_dir": "demographic",
        "file_pattern": "*_DP05_Demographic_FULL.csv",
        "table": "DP05"
    }
}


def merge_year_files(source_path: str, file_pattern: str, year: str) -> pd.DataFrame:
    """Merge all state files for a given year into one DataFrame."""
    year_dir = os.path.join(source_path, year)
    
    if not os.path.exists(year_dir):
        return None
    
    files = glob.glob(os.path.join(year_dir, file_pattern))
    
    if not files:
        return None
    
    dfs = []
    for f in sorted(files):
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"    Error reading {f}: {e}")
    
    if not dfs:
        return None
    
    merged = pd.concat(dfs, ignore_index=True)
    return merged


def process_dataset(name: str, config: dict):
    """Process a single dataset type (economic, social, etc.)."""
    print(f"\n{'='*70}")
    print(f"Processing: {name.upper()}")
    print(f"{'='*70}")
    
    source_path = os.path.join(ACS_DIR, config["source_dir"])
    output_path = os.path.join(OUTPUT_DIR, name)
    
    if not os.path.exists(source_path):
        print(f"  Source directory not found: {source_path}")
        return
    
    os.makedirs(output_path, exist_ok=True)
    
    # Get all year directories
    years = sorted([d for d in os.listdir(source_path) 
                   if os.path.isdir(os.path.join(source_path, d)) and d.isdigit()])
    
    if not years:
        print(f"  No year directories found in {source_path}")
        return
    
    print(f"  Found years: {years}")
    
    all_years_dfs = []
    
    for year in years:
        print(f"\n  Year {year}:")
        
        df = merge_year_files(source_path, config["file_pattern"], year)
        
        if df is None or len(df) == 0:
            print(f"    No data found")
            continue
        
        # Ensure year column exists
        if "year" not in df.columns:
            df.insert(0, "year", int(year))
        
        # Save year file
        year_file = os.path.join(output_path, f"{name}_{year}.csv")
        df.to_csv(year_file, index=False)
        print(f"    Saved: {year_file}")
        print(f"    Counties: {len(df)}, Columns: {len(df.columns)}")
        
        all_years_dfs.append(df)
    
    # Merge all years into master file
    if all_years_dfs:
        print(f"\n  Merging all years...")
        
        # Use union of all columns (outer join approach)
        master_df = pd.concat(all_years_dfs, ignore_index=True)
        
        # Reorder columns: priority columns first
        priority_cols = ["year", "county_name", "state_fips", "county_fips"]
        final_cols = [c for c in priority_cols if c in master_df.columns]
        final_cols += [c for c in master_df.columns if c not in priority_cols]
        master_df = master_df[final_cols]
        
        master_file = os.path.join(output_path, f"{name}_all_years.csv")
        master_df.to_csv(master_file, index=False)
        print(f"  Saved master file: {master_file}")
        print(f"  Total rows: {len(master_df)}, Columns: {len(master_df.columns)}")
        print(f"  Years covered: {sorted(master_df['year'].unique())}")


def main():
    print("=" * 70)
    print("ACS Data Merger")
    print("=" * 70)
    print(f"Source: {ACS_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for name, config in DATASETS.items():
        process_dataset(name, config)
    
    print("\n" + "=" * 70)
    print("Merge complete!")
    print("=" * 70)
    
    # Summary
    print("\nOutput structure:")
    for name in DATASETS.keys():
        output_path = os.path.join(OUTPUT_DIR, name)
        if os.path.exists(output_path):
            files = os.listdir(output_path)
            print(f"  {name}/: {len(files)} files")


if __name__ == "__main__":
    main()
