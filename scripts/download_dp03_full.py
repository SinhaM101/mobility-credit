#!/usr/bin/env python3
"""
ACS 5-Year Data Profile - FULL DP03 Economic Characteristics Downloader

Downloads ALL DP03 (Economic Characteristics) variables from the U.S. Census API
for all counties in a specified state.

This includes:
- Employment Status (labor force, employed, unemployed)
- Occupation (management, service, sales, construction, production)
- Industry (agriculture, construction, manufacturing, retail, etc.)
- Class of Worker (private, government, self-employed)
- Income and Benefits (all income brackets, median, mean)
- Health Insurance Coverage
- Poverty Status
- Commuting to Work (drove alone, carpooled, public transit, walked, etc.)

Source: U.S. Census ACS 5-Year Data Profile
Table: DP03 – Selected Economic Characteristics (ALL 137 variables)
Geography: County level
Endpoint: 2024 ACS 5-Year (covers 2020-2024)

Usage:
    export CENSUS_API_KEY='your_key_here'
    python download_dp03_full.py --state 01        # Alabama
    python download_dp03_full.py                   # All states
"""

import requests
import pandas as pd
import os
import sys
import argparse
import time
from typing import Optional, List

# =============================================================================
# Configuration
# =============================================================================

API_BASE_URL = "https://api.census.gov/data/2024/acs/acs5/profile"
OUTPUT_DIR = "./data/acs_downloads"

# State FIPS codes
STATES = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "11": "DC", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa",
    "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
    "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska",
    "32": "Nevada", "33": "New_Hampshire", "34": "New_Jersey", "35": "New_Mexico",
    "36": "New_York", "37": "North_Carolina", "38": "North_Dakota", "39": "Ohio",
    "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode_Island",
    "45": "South_Carolina", "46": "South_Dakota", "47": "Tennessee", "48": "Texas",
    "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West_Virginia", "55": "Wisconsin", "56": "Wyoming"
}

# =============================================================================
# Functions
# =============================================================================

def get_api_key() -> Optional[str]:
    """Get Census API key from environment variable."""
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        print(f"Using API key: {key[:8]}...")
    else:
        print("WARNING: CENSUS_API_KEY not set. Using API without key (rate limited).")
    return key


def get_all_dp03_variables() -> dict:
    """
    Fetch ALL DP03 variable codes and their labels from the Census API.
    Returns dict mapping variable code to human-readable label.
    """
    print("Fetching DP03 variable definitions from Census API...")
    
    url = "https://api.census.gov/data/2024/acs/acs5/profile/variables.json"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        variables = {}
        for var_code, var_info in data["variables"].items():
            # Only get DP03 estimate variables (ending in E, not PE or ME)
            if (var_code.startswith("DP03_") and 
                var_code.endswith("E") and 
                not var_code.endswith("PE") and 
                not var_code.endswith("ME")):
                
                # Get the label and clean it up
                label = var_info.get("label", var_code)
                # Create a clean column name from the label
                clean_label = label.replace("Estimate!!", "").replace("!!", "_")
                clean_label = clean_label.replace(" ", "_").replace(",", "").replace("'", "")
                clean_label = clean_label.replace("(", "").replace(")", "").replace("-", "_")
                clean_label = clean_label.replace("$", "").replace("%", "pct").replace("+", "plus")
                clean_label = clean_label.lower()[:50]  # Truncate long names
                
                variables[var_code] = {
                    "label": label,
                    "clean_name": clean_label
                }
        
        print(f"  Found {len(variables)} DP03 estimate variables")
        return variables
        
    except Exception as e:
        print(f"  ERROR fetching variables: {e}")
        return {}


def download_dp03_batch(state_fips: str, var_codes: List[str], api_key: Optional[str]) -> Optional[pd.DataFrame]:
    """
    Download a batch of DP03 variables for all counties in a state.
    The Census API has URL length limits, so we batch variables.
    """
    var_string = ",".join(["NAME"] + var_codes)
    url = f"{API_BASE_URL}?get={var_string}&for=county:*&in=state:{state_fips}"
    
    if api_key:
        url += f"&key={api_key}"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and "error" in data:
            return None
        
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        return df
        
    except Exception as e:
        print(f"    Batch error: {e}")
        return None


def download_dp03_full(state_fips: str, state_name: str, variables: dict, api_key: Optional[str]) -> Optional[pd.DataFrame]:
    """
    Download ALL DP03 variables for all counties in a state.
    Makes multiple API calls in batches to avoid URL length limits.
    """
    print(f"\nDownloading FULL DP03 for {state_name} (FIPS: {state_fips})...")
    print(f"  Total variables: {len(variables)}")
    
    var_codes = sorted(variables.keys())
    
    # Batch size - Census API can handle about 50 variables per request
    BATCH_SIZE = 45
    
    # First batch includes NAME, state, county identifiers
    all_dfs = []
    
    for i in range(0, len(var_codes), BATCH_SIZE):
        batch = var_codes[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(var_codes) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} variables...")
        
        df = download_dp03_batch(state_fips, batch, api_key)
        
        if df is not None:
            all_dfs.append(df)
        else:
            print(f"    WARNING: Batch {batch_num} failed")
        
        # Rate limiting
        time.sleep(0.3)
    
    if not all_dfs:
        print("  ERROR: No data downloaded")
        return None
    
    # Merge all batches on NAME, state, county
    result = all_dfs[0]
    for df in all_dfs[1:]:
        # Drop duplicate columns (NAME, state, county) before merging
        cols_to_drop = [c for c in ["NAME", "state", "county"] if c in df.columns and c in result.columns]
        df_clean = df.drop(columns=cols_to_drop, errors='ignore')
        result = pd.concat([result, df_clean], axis=1)
    
    # Clean up
    result["NAME"] = result["NAME"].str.replace(",", ";")
    
    # Rename columns to human-readable names
    rename_map = {"NAME": "county_name", "state": "state_fips", "county": "county_fips"}
    for var_code, var_info in variables.items():
        if var_code in result.columns:
            rename_map[var_code] = var_info["clean_name"]
    
    result = result.rename(columns=rename_map)
    
    print(f"  SUCCESS: {len(result)} counties, {len(result.columns)} columns")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Download FULL ACS 5-Year DP03 Economic Characteristics data"
    )
    parser.add_argument("--state", type=str, help="State FIPS code (e.g., 01 for Alabama)")
    parser.add_argument("--output", type=str, default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()
    
    print("=" * 70)
    print("ACS 5-Year DP03 FULL Economic Characteristics Downloader")
    print("=" * 70)
    print(f"Endpoint: {API_BASE_URL}")
    print(f"Output: {args.output}")
    
    # Get API key
    api_key = get_api_key()
    
    # Get all DP03 variables
    variables = get_all_dp03_variables()
    if not variables:
        print("ERROR: Could not fetch variable definitions")
        sys.exit(1)
    
    # Determine which states to download
    if args.state:
        if args.state not in STATES:
            print(f"\nERROR: Invalid state FIPS code: {args.state}")
            sys.exit(1)
        states_to_download = {args.state: STATES[args.state]}
    else:
        states_to_download = STATES
    
    print(f"States: {len(states_to_download)}")
    print("=" * 70)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Download data
    for state_fips, state_name in states_to_download.items():
        df = download_dp03_full(state_fips, state_name, variables, api_key)
        
        if df is not None:
            filename = f"{state_fips}_{state_name}_DP03_Economic_FULL.csv"
            filepath = os.path.join(args.output, filename)
            df.to_csv(filepath, index=False)
            print(f"  Saved: {filepath}")
            print(f"  Size: {os.path.getsize(filepath) / 1024:.1f} KB")
    
    print("\n" + "=" * 70)
    print("Download complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
