#!/usr/bin/env python3
"""
ACS 5-Year Data Profile - DP03 Economic Characteristics Downloader

Downloads DP03 (Economic Characteristics) data from the U.S. Census API
for all counties in a specified state.

Source: U.S. Census ACS 5-Year Data Profile
Table: DP03 – Selected Economic Characteristics
Geography: County level
Endpoint: 2024 ACS 5-Year (covers 2020-2024)

Usage:
    export CENSUS_API_KEY='your_key_here'
    python download_dp03_economic.py --state 01        # Alabama
    python download_dp03_economic.py --state 36        # New York
    python download_dp03_economic.py                   # All states
"""

import requests
import pandas as pd
import os
import sys
import argparse
from typing import Optional

# =============================================================================
# Configuration
# =============================================================================

# Census API endpoint for ACS 5-Year Data Profiles (2024 vintage = 2020-2024 data)
# Format: https://api.census.gov/data/{year}/acs/acs5/profile
API_BASE_URL = "https://api.census.gov/data/2024/acs/acs5/profile"

# Output directory
OUTPUT_DIR = "./data/acs_downloads"

# -----------------------------------------------------------------------------
# DP03 Variable Codes and Their Meanings
# -----------------------------------------------------------------------------
# The Census API uses coded variable names. Here are the key DP03 variables:
#
# EMPLOYMENT STATUS
#   DP03_0001E = Population 16 years and over (total)
#   DP03_0002E = In labor force
#   DP03_0003E = Civilian labor force
#   DP03_0004E = Employed
#   DP03_0005E = Unemployed
#   DP03_0009E = Unemployment rate (percent)
#
# INCOME
#   DP03_0051E = Total households
#   DP03_0052E = Less than $10,000
#   DP03_0053E = $10,000 to $14,999
#   DP03_0054E = $15,000 to $24,999
#   DP03_0055E = $25,000 to $34,999
#   DP03_0056E = $35,000 to $49,999
#   DP03_0057E = $50,000 to $74,999
#   DP03_0058E = $75,000 to $99,999
#   DP03_0059E = $100,000 to $149,999
#   DP03_0060E = $150,000 to $199,999
#   DP03_0061E = $200,000 or more
#   DP03_0062E = Median household income (dollars)
#   DP03_0063E = Mean household income (dollars)
#
# PER CAPITA & EARNINGS
#   DP03_0088E = Per capita income (dollars)
#   DP03_0092E = Median earnings for full-time workers
#
# POVERTY
#   DP03_0119E = Percent below poverty level (all people)
#   DP03_0128E = Percent with health insurance coverage
#
# SOCIAL SECURITY & RETIREMENT
#   DP03_0099E = Households with Social Security income
#   DP03_0108E = Households with retirement income
# -----------------------------------------------------------------------------

# Variables to download (with human-readable names for CSV header)
DP03_VARIABLES = {
    # Employment
    "DP03_0001E": "population_16_plus",
    "DP03_0002E": "in_labor_force",
    "DP03_0003E": "civilian_labor_force",
    "DP03_0004E": "employed",
    "DP03_0005E": "unemployed",
    "DP03_0009E": "unemployment_rate_pct",
    
    # Income Distribution
    "DP03_0051E": "total_households",
    "DP03_0052E": "income_less_10k",
    "DP03_0053E": "income_10k_15k",
    "DP03_0054E": "income_15k_25k",
    "DP03_0055E": "income_25k_35k",
    "DP03_0056E": "income_35k_50k",
    "DP03_0057E": "income_50k_75k",
    "DP03_0058E": "income_75k_100k",
    "DP03_0059E": "income_100k_150k",
    "DP03_0060E": "income_150k_200k",
    "DP03_0061E": "income_200k_plus",
    "DP03_0062E": "median_household_income",
    "DP03_0063E": "mean_household_income",
    
    # Per Capita & Earnings
    "DP03_0088E": "per_capita_income",
    "DP03_0092E": "median_earnings_fulltime",
    
    # Poverty
    "DP03_0119E": "poverty_rate_pct",
    
    # Health Insurance
    "DP03_0128E": "health_insurance_pct",
    
    # Social Security & Retirement
    "DP03_0099E": "households_social_security",
    "DP03_0108E": "households_retirement_income",
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
    """
    Get Census API key from environment variable.
    The API works without a key but is rate-limited.
    Get a free key at: https://api.census.gov/data/key_signup.html
    """
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        print(f"Using API key: {key[:8]}...")
    else:
        print("WARNING: CENSUS_API_KEY not set. Using API without key (rate limited).")
        print("Get a free key at: https://api.census.gov/data/key_signup.html")
    return key


def download_dp03_for_state(state_fips: str, state_name: str, api_key: Optional[str]) -> Optional[pd.DataFrame]:
    """
    Download DP03 Economic Characteristics for all counties in a state.
    
    How the Census API call works:
    - Base URL: https://api.census.gov/data/2024/acs/acs5/profile
    - ?get=NAME,VAR1,VAR2,...  : Variables to retrieve (NAME = county name)
    - &for=county:*           : Get all counties (wildcard)
    - &in=state:XX            : Within state FIPS code XX
    - &key=YOUR_KEY           : API key (optional but recommended)
    
    Example URL:
    https://api.census.gov/data/2024/acs/acs5/profile?get=NAME,DP03_0062E&for=county:*&in=state:01
    """
    print(f"Downloading DP03 for {state_name} (FIPS: {state_fips})...")
    
    # Build the list of variables to request
    var_codes = list(DP03_VARIABLES.keys())
    var_string = ",".join(["NAME"] + var_codes)
    
    # Construct the API URL
    # for=county:* means "all counties"
    # in=state:XX means "within state with FIPS code XX"
    url = f"{API_BASE_URL}?get={var_string}&for=county:*&in=state:{state_fips}"
    
    # Add API key if available
    if api_key:
        url += f"&key={api_key}"
    
    try:
        # Make the API request
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Parse JSON response
        # Response format: [[header_row], [data_row1], [data_row2], ...]
        data = response.json()
        
        # Check for API error response
        if isinstance(data, dict) and "error" in data:
            print(f"  API Error: {data['error']}")
            return None
        
        # Convert to DataFrame
        # First row is headers, remaining rows are data
        headers = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # Rename columns from codes to human-readable names
        rename_map = {"NAME": "county_name", "state": "state_fips", "county": "county_fips"}
        rename_map.update(DP03_VARIABLES)
        df = df.rename(columns=rename_map)
        
        # Clean county names (remove commas that could break CSV)
        df["county_name"] = df["county_name"].str.replace(",", ";")
        
        # Reorder columns: county info first, then data
        cols = ["county_name", "state_fips", "county_fips"] + list(DP03_VARIABLES.values())
        df = df[cols]
        
        print(f"  SUCCESS: {len(df)} counties downloaded")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Request failed - {e}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Download ACS 5-Year DP03 Economic Characteristics data"
    )
    parser.add_argument(
        "--state", 
        type=str, 
        help="State FIPS code (e.g., 01 for Alabama, 36 for New York)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=OUTPUT_DIR, 
        help="Output directory for CSV files"
    )
    args = parser.parse_args()
    
    # Print header
    print("=" * 70)
    print("ACS 5-Year DP03 Economic Characteristics Downloader")
    print("=" * 70)
    print(f"Endpoint: {API_BASE_URL}")
    print(f"Variables: {len(DP03_VARIABLES)} economic indicators")
    print(f"Output: {args.output}")
    
    # Get API key
    api_key = get_api_key()
    
    # Determine which states to download
    if args.state:
        if args.state not in STATES:
            print(f"\nERROR: Invalid state FIPS code: {args.state}")
            print(f"Valid codes: {', '.join(sorted(STATES.keys()))}")
            sys.exit(1)
        states_to_download = {args.state: STATES[args.state]}
    else:
        states_to_download = STATES
    
    print(f"States: {len(states_to_download)}")
    print("=" * 70)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Download data for each state
    for state_fips, state_name in states_to_download.items():
        df = download_dp03_for_state(state_fips, state_name, api_key)
        
        if df is not None:
            # Save to CSV
            filename = f"{state_fips}_{state_name}_DP03_Economic.csv"
            filepath = os.path.join(args.output, filename)
            df.to_csv(filepath, index=False)
            print(f"  Saved: {filepath}")
    
    print("\n" + "=" * 70)
    print("Download complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
