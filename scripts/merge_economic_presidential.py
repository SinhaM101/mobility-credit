#!/usr/bin/env python3
"""
Merge Alabama DP03 Economic Data with County Presidential Election Data

This script:
1. Loads the full DP03 economic data for Alabama
2. Loads county presidential election data and filters to Alabama
3. Drops columns: office, version, mode
4. Merges on county FIPS code
5. Saves the merged dataset
"""

import pandas as pd
import os

# =============================================================================
# Configuration
# =============================================================================

DATA_DIR = "./data"
ACS_DIR = "./data/acs_downloads"

# Input files
ECONOMIC_FILE = os.path.join(ACS_DIR, "01_Alabama_DP03_Economic_FULL.csv")
PRESIDENTIAL_FILE = os.path.join(DATA_DIR, "countypres_2000-2024.csv")

# Output file
OUTPUT_FILE = os.path.join(DATA_DIR, "alabama_economic_presidential_merged.csv")

# Columns to drop from presidential data
COLUMNS_TO_DROP = ["office", "version", "mode"]

# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Merging Alabama Economic Data with Presidential Election Data")
    print("=" * 70)
    
    # Load economic data
    print("\n1. Loading Alabama DP03 Economic data...")
    econ_df = pd.read_csv(ECONOMIC_FILE)
    print(f"   Loaded: {len(econ_df)} counties, {len(econ_df.columns)} columns")
    
    # Load presidential data
    print("\n2. Loading County Presidential Election data...")
    pres_df = pd.read_csv(PRESIDENTIAL_FILE)
    print(f"   Loaded: {len(pres_df)} rows total")
    
    # Filter to Alabama only
    print("\n3. Filtering presidential data to Alabama...")
    pres_alabama = pres_df[pres_df["state"] == "ALABAMA"].copy()
    print(f"   Alabama rows: {len(pres_alabama)}")
    
    # Drop unwanted columns
    print(f"\n4. Dropping columns: {COLUMNS_TO_DROP}")
    pres_alabama = pres_alabama.drop(columns=COLUMNS_TO_DROP, errors='ignore')
    print(f"   Remaining columns: {list(pres_alabama.columns)}")
    
    # Prepare for merge
    # Economic data has county_fips as 3-digit string (e.g., "001")
    # Presidential data has county_fips as integer (e.g., 1001 for state+county)
    print("\n5. Preparing FIPS codes for merge...")
    
    # Create a full 5-digit FIPS in economic data (state_fips + county_fips)
    econ_df["full_fips"] = econ_df["state_fips"].astype(str).str.zfill(2) + econ_df["county_fips"].astype(str).str.zfill(3)
    econ_df["full_fips"] = econ_df["full_fips"].astype(int)
    
    # Presidential data already has county_fips as full FIPS
    pres_alabama["full_fips"] = pres_alabama["county_fips"].astype(int)
    
    print(f"   Economic FIPS sample: {econ_df['full_fips'].head(3).tolist()}")
    print(f"   Presidential FIPS sample: {pres_alabama['full_fips'].head(3).tolist()}")
    
    # Merge
    print("\n6. Merging datasets on full_fips...")
    merged = pres_alabama.merge(
        econ_df,
        on="full_fips",
        how="left",
        suffixes=("_pres", "_econ")
    )
    print(f"   Merged: {len(merged)} rows, {len(merged.columns)} columns")
    
    # Check for unmatched (use economic county_name column)
    econ_county_col = "county_name_econ" if "county_name_econ" in merged.columns else "county_name"
    unmatched = merged[merged[econ_county_col].isna()]
    if len(unmatched) > 0:
        print(f"   WARNING: {len(unmatched)} rows did not match")
    
    # Save
    print(f"\n7. Saving merged data to: {OUTPUT_FILE}")
    merged.to_csv(OUTPUT_FILE, index=False)
    file_size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"   File size: {file_size:.1f} KB")
    
    # Summary
    print("\n" + "=" * 70)
    print("Merge complete!")
    print("=" * 70)
    print(f"   Total rows: {len(merged)}")
    print(f"   Total columns: {len(merged.columns)}")
    print(f"   Unique counties: {merged['full_fips'].nunique()}")
    print(f"   Years: {sorted(merged['year'].unique())}")
    print(f"   Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
