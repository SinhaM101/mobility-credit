#!/usr/bin/env python3
"""
ACS 5-Year Data Profile Downloader

Downloads all 4 ACS Data Profile tables from the U.S. Census API:
- DP02: Social Characteristics (Education, Marital Status, Fertility, etc.)
- DP03: Economic Characteristics (Income, Employment, Occupation, etc.)
- DP04: Housing Characteristics (Occupancy, Housing Value, Utilities, etc.)
- DP05: Demographic Characteristics (Sex, Age, Race, Hispanic Origin, etc.)

Usage:
    python download_acs_profiles.py --state 01  # Alabama only
    python download_acs_profiles.py             # All states
"""

import requests
import pandas as pd
import os
import sys
import time
import argparse
from typing import Optional

# =============================================================================
# Configuration
# =============================================================================

# Census API base URL for ACS 5-Year Data Profiles (2024 - covers 2020-2024)
BASE_URL = "https://api.census.gov/data/2024/acs/acs5/profile"

# Output directory
OUTPUT_DIR = "./data/acs_downloads"

# Data Profile tables and their key variables
# Using curated lists of important variables to avoid API limits
PROFILE_TABLES = {
    "DP02": {
        "name": "Social",
        "variables": [
            "DP02_0001E",  # Total households
            "DP02_0059E",  # Educational attainment: Population 25+
            "DP02_0060E",  # Less than 9th grade
            "DP02_0061E",  # 9th to 12th grade, no diploma
            "DP02_0062E",  # High school graduate
            "DP02_0063E",  # Some college, no degree
            "DP02_0064E",  # Associate's degree
            "DP02_0065E",  # Bachelor's degree
            "DP02_0066E",  # Graduate or professional degree
            "DP02_0067E",  # High school graduate or higher (%)
            "DP02_0068E",  # Bachelor's degree or higher (%)
            "DP02_0011E",  # Family households
            "DP02_0012E",  # Married-couple family
            "DP02_0016E",  # Nonfamily households
            "DP02_0024E",  # Average household size
            "DP02_0025E",  # Average family size
        ]
    },
    "DP03": {
        "name": "Economic",
        "variables": [
            "DP03_0001E",  # Total population 16+
            "DP03_0002E",  # In labor force
            "DP03_0003E",  # Civilian labor force
            "DP03_0004E",  # Employed
            "DP03_0005E",  # Unemployed
            "DP03_0009E",  # Unemployment rate
            "DP03_0052E",  # Households
            "DP03_0062E",  # Median household income
            "DP03_0063E",  # Mean household income
            "DP03_0088E",  # Per capita income
            "DP03_0092E",  # Median earnings (full-time workers)
            "DP03_0119E",  # Percent below poverty level
            "DP03_0128E",  # With health insurance
            "DP03_0099E",  # With Social Security income
        ]
    },
    "DP04": {
        "name": "Housing",
        "variables": [
            "DP04_0001E",  # Total housing units
            "DP04_0002E",  # Occupied housing units
            "DP04_0003E",  # Vacant housing units
            "DP04_0046E",  # Owner-occupied units
            "DP04_0047E",  # Renter-occupied units
            "DP04_0089E",  # Median value (owner-occupied)
            "DP04_0134E",  # Median gross rent
            "DP04_0127E",  # Median monthly owner costs (with mortgage)
            "DP04_0128E",  # Median monthly owner costs (without mortgage)
            "DP04_0110E",  # Housing costs as % of income: <20%
            "DP04_0111E",  # Housing costs as % of income: 20-24.9%
            "DP04_0112E",  # Housing costs as % of income: 25-29.9%
            "DP04_0113E",  # Housing costs as % of income: 30-34.9%
            "DP04_0114E",  # Housing costs as % of income: 35%+
            "DP04_0073E",  # Utility costs: Gas
            "DP04_0074E",  # Utility costs: Electricity
        ]
    },
    "DP05": {
        "name": "Demographic",
        "variables": [
            "DP05_0001E",  # Total population
            "DP05_0002E",  # Male
            "DP05_0003E",  # Female
            "DP05_0005E",  # Under 5 years
            "DP05_0006E",  # 5 to 9 years
            "DP05_0007E",  # 10 to 14 years
            "DP05_0008E",  # 15 to 19 years
            "DP05_0009E",  # 20 to 24 years
            "DP05_0010E",  # 25 to 34 years
            "DP05_0011E",  # 35 to 44 years
            "DP05_0012E",  # 45 to 54 years
            "DP05_0013E",  # 55 to 59 years
            "DP05_0014E",  # 60 to 64 years
            "DP05_0015E",  # 65 to 74 years
            "DP05_0016E",  # 75 to 84 years
            "DP05_0017E",  # 85 years and over
            "DP05_0018E",  # Median age
            "DP05_0037E",  # White
            "DP05_0038E",  # Black or African American
            "DP05_0044E",  # Asian
            "DP05_0071E",  # Hispanic or Latino
        ]
    }
}

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
        print("WARNING: No API key set. Using API without key (rate limited).")
        print("Get a free key at: https://api.census.gov/data/key_signup.html")
    return key


def download_table(state_fips: str, state_name: str, table: str, table_config: dict, api_key: Optional[str]) -> Optional[pd.DataFrame]:
    """
    Download a single Data Profile table for all counties in a state.
    """
    table_name = table_config["name"]
    variables = table_config["variables"]
    
    print(f"  Downloading {table} ({table_name})...")
    
    # Build API URL
    var_string = ",".join(["NAME"] + variables)
    url = f"{BASE_URL}?get={var_string}&for=county:*&in=state:{state_fips}"
    if api_key:
        url += f"&key={api_key}"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Check for API error
        if isinstance(data, dict) and "error" in data:
            print(f"    API Error: {data['error']}")
            return None
        
        # Convert to DataFrame
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # Clean up county names
        df["NAME"] = df["NAME"].str.replace(",", ";")
        
        print(f"    SUCCESS: {len(df)} counties, {len(variables)} variables")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"    ERROR: Request failed - {e}")
        return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def download_state_data(state_fips: str, state_name: str, api_key: Optional[str]) -> dict:
    """
    Download all 4 Data Profile tables for a state.
    Returns dict of DataFrames keyed by table code.
    """
    print(f"\nDownloading data for {state_name} (FIPS: {state_fips})...")
    
    results = {}
    
    for table, table_config in PROFILE_TABLES.items():
        df = download_table(state_fips, state_name, table, table_config, api_key)
        if df is not None:
            results[table] = df
        
        # Rate limiting
        time.sleep(0.5)
    
    return results


def save_state_data(state_fips: str, state_name: str, data: dict, output_dir: str):
    """
    Save downloaded data to CSV files.
    Creates one file per table: {state_fips}_{state_name}_{table}.csv
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for table, df in data.items():
        filename = f"{state_fips}_{state_name}_{table}_{PROFILE_TABLES[table]['name']}.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"  Saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Download ACS 5-Year Data Profiles")
    parser.add_argument("--state", type=str, help="State FIPS code (e.g., 01 for Alabama)")
    parser.add_argument("--output", type=str, default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()
    
    print("=" * 60)
    print("ACS 5-Year Data Profile Downloader")
    print("=" * 60)
    table_list = ', '.join([f"{k} ({v['name']})" for k, v in PROFILE_TABLES.items()])
    print(f"Tables: {table_list}")
    print(f"Output: {args.output}")
    
    # Get API key
    api_key = get_api_key()
    
    # Determine which states to download
    if args.state:
        if args.state not in STATES:
            print(f"ERROR: Invalid state FIPS code: {args.state}")
            print(f"Valid codes: {', '.join(sorted(STATES.keys()))}")
            sys.exit(1)
        states_to_download = {args.state: STATES[args.state]}
    else:
        states_to_download = STATES
    
    print(f"States: {len(states_to_download)}")
    print("=" * 60)
    
    # Download data
    success_count = 0
    error_count = 0
    
    for state_fips, state_name in states_to_download.items():
        data = download_state_data(state_fips, state_name, api_key)
        
        if data:
            save_state_data(state_fips, state_name, data, args.output)
            success_count += 1
        else:
            error_count += 1
        
        # Rate limiting between states
        if len(states_to_download) > 1:
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"  Successful: {success_count} states")
    print(f"  Errors: {error_count} states")
    print(f"  Output: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
