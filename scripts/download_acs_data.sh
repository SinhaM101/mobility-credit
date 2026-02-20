#!/usr/bin/env bash
# =============================================================================
# ACS 5-Year Data Profile Downloader
# Downloads economic and housing variables from U.S. Census API
# for all states and counties
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Check for Census API key in environment variable (optional but recommended)
if [ -z "$CENSUS_API_KEY" ]; then
    echo "WARNING: CENSUS_API_KEY not set. Using API without key (rate limited)."
    echo "Get a free API key at: https://api.census.gov/data/key_signup.html"
    API_KEY_PARAM=""
else
    API_KEY_PARAM="&key=${CENSUS_API_KEY}"
fi

# API base URL for ACS 5-Year Data Profiles (2022 is latest available)
BASE_URL="https://api.census.gov/data/2022/acs/acs5/profile"

# Output directory for CSV files
OUTPUT_DIR="./data/acs_downloads"
mkdir -p "$OUTPUT_DIR"

# -----------------------------------------------------------------------------
# Variables to download from DP03 (Economic) and DP04 (Housing)
# -----------------------------------------------------------------------------

# DP03: Selected Economic Characteristics
# - DP03_0062E: Median household income
# - DP03_0063E: Mean household income
# - DP03_0088E: Per capita income
# - DP03_0119PE: Percent below poverty level
# - DP03_0052PE: Percent in labor force

# DP04: Selected Housing Characteristics
# - DP04_0089E: Median value of owner-occupied units
# - DP04_0134E: Median gross rent
# - DP04_0141PE: Gross rent as percent of income (35%+ burdened)

VARIABLES="NAME,DP03_0062E,DP03_0063E,DP03_0088E,DP03_0119PE,DP03_0052PE,DP04_0089E,DP04_0134E,DP04_0141PE"

# CSV header row
HEADER="county_name,state_fips,county_fips,median_household_income,mean_household_income,per_capita_income,poverty_rate_pct,labor_force_pct,median_home_value,median_gross_rent,rent_burdened_pct"

# -----------------------------------------------------------------------------
# Function to download data for a single state
# -----------------------------------------------------------------------------
download_state_data() {
    state_fips=$1
    state_name=$2
    
    echo "Downloading data for $state_name (FIPS: $state_fips)..."
    
    # Build API URL - get all counties within the state
    url="${BASE_URL}?get=${VARIABLES}&for=county:*&in=state:${state_fips}${API_KEY_PARAM}"
    
    # Output file path
    output_file="${OUTPUT_DIR}/${state_fips}_${state_name}.csv"
    
    # Make API request and process with Python
    curl -sL "$url" | python3 -c "
import sys
import json

# CSV header
print('county_name,state_fips,county_fips,median_household_income,mean_household_income,per_capita_income,poverty_rate_pct,labor_force_pct,median_home_value,median_gross_rent,rent_burdened_pct')

try:
    data = json.load(sys.stdin)
    if isinstance(data, dict) and 'error' in data:
        print(f'API Error: {data}', file=sys.stderr)
        sys.exit(1)
    # Skip header row (first element)
    for row in data[1:]:
        # row format: [NAME, vars..., state, county]
        name = row[0].replace(',', ';')  # Escape commas in county names
        state_fips = row[-2]
        county_fips = row[-1]
        # Variables are in positions 1 through -2
        values = row[1:-2]
        # Replace None/null with empty string
        values = [str(v) if v is not None else '' for v in values]
        print(f'{name},{state_fips},{county_fips},' + ','.join(values))
except json.JSONDecodeError as e:
    print(f'JSON parse error: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" > "$output_file"
    
    if [ $? -eq 0 ]; then
        count=$(wc -l < "$output_file" | tr -d ' ')
        count=$((count - 1))  # Subtract header row
        echo "  SUCCESS: Saved $count counties to $output_file"
        return 0
    else
        echo "  ERROR: Failed to download data for $state_name"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# State FIPS codes (simple arrays for compatibility)
# -----------------------------------------------------------------------------

STATE_FIPS="01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56"
STATE_NAMES="Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware DC Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada NewHampshire NewJersey NewMexico NewYork NorthCarolina NorthDakota Ohio Oklahoma Oregon Pennsylvania RhodeIsland SouthCarolina SouthDakota Tennessee Texas Utah Vermont Virginia Washington WestVirginia Wisconsin Wyoming"

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

echo "=============================================="
echo "ACS 5-Year Data Profile Downloader"
echo "=============================================="
echo "Output directory: $OUTPUT_DIR"
echo "API Key: ${CENSUS_API_KEY:0:8}..."
echo ""

# Check if running in test mode (Alabama only)
if [ "$1" = "--test" ] || [ "$1" = "-t" ]; then
    echo "TEST MODE: Downloading Alabama only"
    echo "----------------------------------------------"
    download_state_data "01" "Alabama"
    echo ""
    echo "Test complete. Check $OUTPUT_DIR for output."
    exit 0
fi

# Download data for all states
echo "Downloading data for all 51 states/territories..."
echo "----------------------------------------------"

success_count=0
error_count=0

# Convert to arrays
fips_arr=($STATE_FIPS)
names_arr=($STATE_NAMES)

# Iterate through states
for i in "${!fips_arr[@]}"; do
    fips="${fips_arr[$i]}"
    name="${names_arr[$i]}"
    
    if download_state_data "$fips" "$name"; then
        success_count=$((success_count + 1))
    else
        error_count=$((error_count + 1))
    fi
    
    # Rate limiting: wait 0.5 seconds between requests
    sleep 0.5
done

echo ""
echo "=============================================="
echo "Download complete!"
echo "  Successful: $success_count states"
echo "  Errors: $error_count states"
echo "  Output: $OUTPUT_DIR"
echo "=============================================="
