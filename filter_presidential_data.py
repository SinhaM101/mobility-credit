"""
Filter County Presidential Election Data
Step 1: Filter to New York State
Step 2: Filter to New York City (5 boroughs)
"""

import pandas as pd
import time

start_time = time.time()

print("=" * 60)
print("FILTERING COUNTY PRESIDENTIAL DATA")
print("=" * 60)

# =============================================================================
# STEP 1: Load the full dataset
# =============================================================================
print("\n[STEP 1] Loading county presidential data...")
step1_start = time.time()

df = pd.read_csv("countypres_2000-2024.csv")

step1_time = time.time() - step1_start
print(f"  Total rows: {len(df):,}")
print(f"  Columns: {list(df.columns)}")
print(f"  Unique states: {df['state'].nunique()}")
print(f"  Execution time: {step1_time:.4f}s")

# =============================================================================
# STEP 2: Filter to New York State
# =============================================================================
print("\n[STEP 2] Filtering to New York State...")
step2_start = time.time()

ny_df = df[df['state'] == 'NEW YORK'].copy()

step2_time = time.time() - step2_start
print(f"  New York rows: {len(ny_df):,}")
print(f"  Unique counties in NY: {ny_df['county_name'].nunique()}")
print(f"  Years covered: {sorted(ny_df['year'].unique())}")
print(f"  Execution time: {step2_time:.4f}s")

# Save New York State data
ny_df.to_csv("countypres_ny_state.csv", index=False)
print(f"  Saved: countypres_ny_state.csv")

# =============================================================================
# STEP 3: Filter to New York City (5 boroughs)
# =============================================================================
print("\n[STEP 3] Filtering to New York City (5 boroughs)...")
step3_start = time.time()

# NYC 5 boroughs and their county names:
# - Manhattan = NEW YORK (county)
# - Brooklyn = KINGS
# - Queens = QUEENS
# - Bronx = BRONX
# - Staten Island = RICHMOND

nyc_counties = ['NEW YORK', 'KINGS', 'QUEENS', 'BRONX', 'RICHMOND']

nyc_df = ny_df[ny_df['county_name'].isin(nyc_counties)].copy()

step3_time = time.time() - step3_start
print(f"  NYC rows: {len(nyc_df):,}")
print(f"  Boroughs found: {sorted(nyc_df['county_name'].unique())}")
print(f"  Execution time: {step3_time:.4f}s")

# Save NYC data
nyc_df.to_csv("countypres_nyc.csv", index=False)
print(f"  Saved: countypres_nyc.csv")

# =============================================================================
# STEP 4: Summary statistics
# =============================================================================
print("\n[STEP 4] Summary statistics...")
step4_start = time.time()

print("\n  NYC PRESIDENTIAL VOTES BY BOROUGH (Latest Year):")
print("  " + "-" * 50)

latest_year = nyc_df['year'].max()
latest_nyc = nyc_df[nyc_df['year'] == latest_year]

# Borough name mapping
borough_names = {
    'NEW YORK': 'Manhattan',
    'KINGS': 'Brooklyn', 
    'QUEENS': 'Queens',
    'BRONX': 'Bronx',
    'RICHMOND': 'Staten Island'
}

for county in nyc_counties:
    county_data = latest_nyc[latest_nyc['county_name'] == county]
    if not county_data.empty:
        total_votes = county_data['totalvotes'].iloc[0]
        borough = borough_names.get(county, county)
        print(f"  {borough:15s}: {total_votes:>12,} total votes ({latest_year})")

step4_time = time.time() - step4_start

# =============================================================================
# SUMMARY
# =============================================================================
total_time = time.time() - start_time

print("\n" + "=" * 60)
print("EXECUTION SUMMARY")
print("=" * 60)
print(f"Total execution time: {total_time:.4f}s")
print(f"\nData reduction:")
print(f"  Original:      {len(df):>10,} rows")
print(f"  NY State:      {len(ny_df):>10,} rows ({len(ny_df)/len(df)*100:.1f}%)")
print(f"  NYC only:      {len(nyc_df):>10,} rows ({len(nyc_df)/len(df)*100:.1f}%)")
print(f"\nOutput files:")
print(f"  - countypres_ny_state.csv ({len(ny_df):,} rows)")
print(f"  - countypres_nyc.csv ({len(nyc_df):,} rows)")

print("\n" + "=" * 60)
print("FILTERING COMPLETE")
print("=" * 60)
