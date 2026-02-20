#!/usr/bin/env python3
"""
Add county_fips column to all raw data CSVs.
Uses countypres data to map state + county_name to county_fips.
"""

import pandas as pd
import os
import glob

# =============================================================================
# Configuration
# =============================================================================

RAW_DATA_DIR = "./data/acs_downloads/raw_data"
COUNTYPRES_FILE = "./data/countypres_2000-2024.csv"

# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Adding county_fips to all raw data CSVs")
    print("=" * 70)
    
    # Load countypres to get state-county FIPS mapping
    print("\n1. Loading county FIPS mapping from countypres...")
    pres_df = pd.read_csv(COUNTYPRES_FILE)
    
    # Create unique mapping: state + county_name -> county_fips
    # county_name in countypres is uppercase (e.g., "AUTAUGA")
    # county_name in raw data is "Autauga County; Alabama"
    fips_map = pres_df[["state", "county_name", "county_fips"]].drop_duplicates()
    fips_map = fips_map.set_index(["state", "county_name"])["county_fips"].to_dict()
    print(f"   Unique state-county mappings: {len(fips_map)}")
    
    # Get all raw data CSV files
    csv_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    print(f"\n2. Found {len(csv_files)} raw data CSV files")
    
    # State name mapping for files with underscores
    state_name_map = {
        "New_Hampshire": "NEW HAMPSHIRE",
        "New_Jersey": "NEW JERSEY", 
        "New_Mexico": "NEW MEXICO",
        "New_York": "NEW YORK",
        "North_Carolina": "NORTH CAROLINA",
        "North_Dakota": "NORTH DAKOTA",
        "Rhode_Island": "RHODE ISLAND",
        "South_Carolina": "SOUTH CAROLINA",
        "South_Dakota": "SOUTH DAKOTA",
        "West_Virginia": "WEST VIRGINIA",
    }
    
    # Process each file
    print("\n3. Processing files...")
    for csv_file in sorted(csv_files):
        filename = os.path.basename(csv_file)
        
        # Extract state name from filename (e.g., "01_Alabama_DP03_Economic_FULL.csv")
        parts = filename.split("_")
        state_fips_code = parts[0]
        # Handle multi-word state names (check if parts[2] is "DP03" or part of state name)
        state_raw = parts[1]
        if len(parts) > 5 and parts[2] not in ["DP03"]:  # Has underscore in state name like "New_York"
            state_raw = parts[1] + "_" + parts[2]
        state_name = state_name_map.get(state_raw, state_raw.upper())
        
        # Load the CSV
        df = pd.read_csv(csv_file)
        
        # If county_fips column already exists and is empty, drop it first
        if "county_fips" in df.columns:
            df = df.drop(columns=["county_fips"])
        
        # Extract county name from county_name column
        # Format: "Autauga County; Alabama" -> "AUTAUGA"
        def extract_county(full_name):
            if pd.isna(full_name):
                return None
            full_name = str(full_name)
            # Remove state suffix and "County" suffix
            county = full_name.split(";")[0].strip()
            county = county.replace(" County", "").replace(" Parish", "").replace(" Borough", "")
            county = county.replace(" Municipality", "").replace(" Census Area", "").replace(" city", "")
            return county.upper()
        
        df["county_match"] = df["county_name"].apply(extract_county)
        
        # Map to county_fips
        def get_fips(row):
            key = (state_name, row["county_match"])
            return fips_map.get(key, None)
        
        df["county_fips"] = df.apply(get_fips, axis=1)
        
        # Drop the temporary column
        df = df.drop(columns=["county_match"])
        
        # Move county_fips to be the second column (after county_name)
        cols = df.columns.tolist()
        cols.remove("county_fips")
        cols.insert(1, "county_fips")
        df = df[cols]
        
        # Count matches
        matched = df["county_fips"].notna().sum()
        total = len(df)
        
        # Save
        df.to_csv(csv_file, index=False)
        print(f"   {filename}: {matched}/{total} counties matched")
    
    print("\n" + "=" * 70)
    print("Done! county_fips column added to all raw data CSVs")
    print("=" * 70)


if __name__ == "__main__":
    main()
