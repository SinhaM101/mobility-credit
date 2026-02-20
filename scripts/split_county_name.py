#!/usr/bin/env python3
"""
Split county_name column into separate state_name and county columns.
Example: "Autauga County; Alabama" -> state_name="Alabama", county="Autauga"
"""

import pandas as pd
import os
import glob

RAW_DATA_DIR = "./data/acs_downloads/raw_data"

def main():
    print("=" * 70)
    print("Splitting county_name into state_name and county columns")
    print("=" * 70)
    
    csv_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    print(f"Found {len(csv_files)} CSV files\n")
    
    for csv_file in sorted(csv_files):
        filename = os.path.basename(csv_file)
        
        df = pd.read_csv(csv_file)
        
        # Split "Autauga County; Alabama" into county and state_name
        def extract_county(full_name):
            if pd.isna(full_name):
                return None
            parts = str(full_name).split(";")
            county = parts[0].strip()
            # Remove suffixes like "County", "Parish", "Borough", etc.
            county = county.replace(" County", "").replace(" Parish", "")
            county = county.replace(" Borough", "").replace(" Municipality", "")
            county = county.replace(" Census Area", "").replace(" city", "")
            return county
        
        def extract_state(full_name):
            if pd.isna(full_name):
                return None
            parts = str(full_name).split(";")
            if len(parts) > 1:
                return parts[1].strip()
            return None
        
        df["county"] = df["county_name"].apply(extract_county)
        df["state_name"] = df["county_name"].apply(extract_state)
        
        # Reorder columns: county_name, county_fips, state_name, county, then rest
        cols = df.columns.tolist()
        # Remove the new columns from their current position
        cols.remove("county")
        cols.remove("state_name")
        
        # Find position after county_fips (or after county_name if county_fips doesn't exist)
        if "county_fips" in cols:
            insert_pos = cols.index("county_fips") + 1
        else:
            insert_pos = cols.index("county_name") + 1
        
        # Insert state_name and county after county_fips
        cols.insert(insert_pos, "state_name")
        cols.insert(insert_pos + 1, "county")
        
        df = df[cols]
        
        # Save
        df.to_csv(csv_file, index=False)
        print(f"{filename}: added state_name and county columns")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
