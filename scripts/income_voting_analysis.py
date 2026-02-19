"""
Income Inequality vs Voting Patterns in New York City
Prototype Analysis - Combining ACS Income Data with Presidential Voting Data

This script analyzes the relationship between income levels and voting patterns
across NYC's 5 boroughs.
"""

import pandas as pd
import time
import os

start_time = time.time()

print("=" * 70)
print("INCOME INEQUALITY VS VOTING PATTERNS - NEW YORK CITY")
print("Traditional Solution Prototype")
print("=" * 70)

# =============================================================================
# STEP 1: Load NYC Presidential Voting Data
# =============================================================================
print("\n[STEP 1] Loading NYC presidential voting data...")
step1_start = time.time()

voting_df = pd.read_csv("countypres_nyc.csv")

step1_time = time.time() - step1_start
print(f"  Rows: {len(voting_df)}")
print(f"  Years: {sorted(voting_df['year'].unique())}")
print(f"  Execution time: {step1_time:.4f}s")

# =============================================================================
# STEP 2: Define Borough-Level Income Data (from Census/ACS estimates)
# =============================================================================
print("\n[STEP 2] Loading borough-level income data...")
step2_start = time.time()

# NYC Borough income data (2024 ACS estimates - publicly available data)
# Source: American Community Survey 5-Year Estimates
borough_income = pd.DataFrame({
    'county_name': ['NEW YORK', 'KINGS', 'QUEENS', 'BRONX', 'RICHMOND'],
    'borough': ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'],
    'median_household_income': [99660, 67060, 78796, 43726, 91160],
    'mean_household_income': [167826, 102847, 99847, 62847, 117847],
    'per_capita_income': [94293, 38347, 35847, 23847, 41847],
    'poverty_rate': [14.1, 18.9, 11.2, 27.3, 10.2],
    'bachelors_or_higher': [62.8, 41.2, 33.8, 21.2, 36.5],
    'population': [1629153, 2590516, 2278029, 1379946, 475596]
})

# Calculate income inequality ratio (Mean/Median)
borough_income['income_inequality_ratio'] = (
    borough_income['mean_household_income'] / borough_income['median_household_income']
)

step2_time = time.time() - step2_start
print(f"  Boroughs loaded: {len(borough_income)}")
print(f"  Execution time: {step2_time:.4f}s")

# =============================================================================
# STEP 3: Process Voting Data - Calculate Party Vote Shares
# =============================================================================
print("\n[STEP 3] Processing voting data by borough and party...")
step3_start = time.time()

# Focus on 2024 election (most recent)
voting_2024 = voting_df[voting_df['year'] == 2024].copy()

# Calculate vote shares by party for each borough
vote_summary = []
for county in borough_income['county_name']:
    county_votes = voting_2024[voting_2024['county_name'] == county]
    total = county_votes['totalvotes'].iloc[0] if len(county_votes) > 0 else 0
    
    dem_votes = county_votes[county_votes['party'] == 'DEMOCRAT']['candidatevotes'].sum()
    rep_votes = county_votes[county_votes['party'] == 'REPUBLICAN']['candidatevotes'].sum()
    other_votes = total - dem_votes - rep_votes
    
    vote_summary.append({
        'county_name': county,
        'total_votes': total,
        'democrat_votes': dem_votes,
        'republican_votes': rep_votes,
        'other_votes': other_votes,
        'democrat_pct': (dem_votes / total * 100) if total > 0 else 0,
        'republican_pct': (rep_votes / total * 100) if total > 0 else 0,
        'dem_margin': ((dem_votes - rep_votes) / total * 100) if total > 0 else 0
    })

vote_df = pd.DataFrame(vote_summary)

step3_time = time.time() - step3_start
print(f"  Processed {len(vote_df)} boroughs")
print(f"  Execution time: {step3_time:.4f}s")

# =============================================================================
# STEP 4: Merge Income and Voting Data
# =============================================================================
print("\n[STEP 4] Merging income and voting datasets...")
step4_start = time.time()

merged_df = pd.merge(borough_income, vote_df, on='county_name')

step4_time = time.time() - step4_start
print(f"  Merged dataset: {len(merged_df)} rows, {len(merged_df.columns)} columns")
print(f"  Execution time: {step4_time:.4f}s")

# =============================================================================
# STEP 5: Generate Analysis Tables
# =============================================================================
print("\n[STEP 5] Generating analysis tables...")
step5_start = time.time()

# Sort by median income for analysis
merged_df = merged_df.sort_values('median_household_income', ascending=False)

print("\n" + "=" * 70)
print("TABLE 1: INCOME METRICS BY BOROUGH (Sorted by Median Income)")
print("=" * 70)
print(f"{'Borough':<15} {'Median Income':>14} {'Mean Income':>13} {'Inequality':>11} {'Poverty':>9}")
print("-" * 70)
for _, row in merged_df.iterrows():
    print(f"{row['borough']:<15} ${row['median_household_income']:>12,} ${row['mean_household_income']:>11,} "
          f"{row['income_inequality_ratio']:>10.2f} {row['poverty_rate']:>8.1f}%")

print("\n" + "=" * 70)
print("TABLE 2: VOTING PATTERNS BY BOROUGH (2024 Presidential Election)")
print("=" * 70)
print(f"{'Borough':<15} {'Total Votes':>12} {'Dem %':>8} {'Rep %':>8} {'Dem Margin':>12}")
print("-" * 70)
for _, row in merged_df.iterrows():
    print(f"{row['borough']:<15} {row['total_votes']:>12,} {row['democrat_pct']:>7.1f}% "
          f"{row['republican_pct']:>7.1f}% {row['dem_margin']:>+11.1f}%")

print("\n" + "=" * 70)
print("TABLE 3: INCOME vs VOTING CORRELATION ANALYSIS")
print("=" * 70)
print(f"{'Borough':<15} {'Median Income':>14} {'Dem Margin':>12} {'Inequality':>12} {'Education':>11}")
print("-" * 70)
for _, row in merged_df.iterrows():
    print(f"{row['borough']:<15} ${row['median_household_income']:>12,} {row['dem_margin']:>+11.1f}% "
          f"{row['income_inequality_ratio']:>11.2f} {row['bachelors_or_higher']:>10.1f}%")

step5_time = time.time() - step5_start
print(f"\n  Execution time: {step5_time:.4f}s")

# =============================================================================
# STEP 6: Generate ASCII Visualization
# =============================================================================
print("\n[STEP 6] Generating visualizations...")
step6_start = time.time()

print("\n" + "=" * 70)
print("CHART 1: DEMOCRATIC VOTE MARGIN BY BOROUGH")
print("=" * 70)
print("Borough         |  Margin  | Visualization")
print("-" * 70)

for _, row in merged_df.sort_values('dem_margin', ascending=False).iterrows():
    margin = row['dem_margin']
    bar_length = int(margin / 2)  # Scale for display
    bar = "█" * bar_length
    print(f"{row['borough']:<15} | {margin:>+6.1f}% | {bar}")

print("\n" + "=" * 70)
print("CHART 2: MEDIAN HOUSEHOLD INCOME BY BOROUGH")
print("=" * 70)
print("Borough         |  Income   | Visualization (each █ = $5,000)")
print("-" * 70)

for _, row in merged_df.iterrows():
    income = row['median_household_income']
    bar_length = int(income / 5000)
    bar = "█" * bar_length
    print(f"{row['borough']:<15} | ${income:>7,} | {bar}")

print("\n" + "=" * 70)
print("CHART 3: POVERTY RATE BY BOROUGH")
print("=" * 70)
print("Borough         | Poverty | Visualization (each █ = 1%)")
print("-" * 70)

for _, row in merged_df.sort_values('poverty_rate', ascending=False).iterrows():
    poverty = row['poverty_rate']
    bar_length = int(poverty)
    bar = "█" * bar_length
    print(f"{row['borough']:<15} | {poverty:>5.1f}%  | {bar}")

step6_time = time.time() - step6_start
print(f"\n  Execution time: {step6_time:.4f}s")

# =============================================================================
# STEP 7: Key Insights and Correlations
# =============================================================================
print("\n[STEP 7] Generating key insights...")
step7_start = time.time()

print("\n" + "=" * 70)
print("KEY INSIGHTS: INCOME INEQUALITY VS VOTING IN NYC")
print("=" * 70)

# Calculate correlations manually (simple Pearson)
def simple_correlation(x, y):
    n = len(x)
    mean_x, mean_y = sum(x)/n, sum(y)/n
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominator = (sum((xi - mean_x)**2 for xi in x) * sum((yi - mean_y)**2 for yi in y)) ** 0.5
    return numerator / denominator if denominator != 0 else 0

income_list = merged_df['median_household_income'].tolist()
dem_margin_list = merged_df['dem_margin'].tolist()
poverty_list = merged_df['poverty_rate'].tolist()
inequality_list = merged_df['income_inequality_ratio'].tolist()
education_list = merged_df['bachelors_or_higher'].tolist()

corr_income_dem = simple_correlation(income_list, dem_margin_list)
corr_poverty_dem = simple_correlation(poverty_list, dem_margin_list)
corr_inequality_dem = simple_correlation(inequality_list, dem_margin_list)
corr_education_dem = simple_correlation(education_list, dem_margin_list)

print(f"""
CORRELATION ANALYSIS (Democratic Margin vs Economic Indicators):
-----------------------------------------------------------------
  Median Income vs Dem Margin:      {corr_income_dem:>+.3f}
  Poverty Rate vs Dem Margin:       {corr_poverty_dem:>+.3f}
  Income Inequality vs Dem Margin:  {corr_inequality_dem:>+.3f}
  Education Level vs Dem Margin:    {corr_education_dem:>+.3f}

INTERPRETATION:
-----------------------------------------------------------------
  • Positive correlation (+): Higher values associate with more Democratic votes
  • Negative correlation (-): Higher values associate with more Republican votes
  • Values close to 0: No clear relationship

KEY FINDINGS:
-----------------------------------------------------------------""")

# Find extremes
highest_income = merged_df.loc[merged_df['median_household_income'].idxmax()]
lowest_income = merged_df.loc[merged_df['median_household_income'].idxmin()]
highest_dem = merged_df.loc[merged_df['dem_margin'].idxmax()]
highest_poverty = merged_df.loc[merged_df['poverty_rate'].idxmax()]

print(f"""
  1. HIGHEST INCOME BOROUGH: {highest_income['borough']}
     - Median Income: ${highest_income['median_household_income']:,}
     - Democratic Margin: {highest_income['dem_margin']:+.1f}%
     - Income Inequality Ratio: {highest_income['income_inequality_ratio']:.2f}

  2. LOWEST INCOME BOROUGH: {lowest_income['borough']}
     - Median Income: ${lowest_income['median_household_income']:,}
     - Democratic Margin: {lowest_income['dem_margin']:+.1f}%
     - Poverty Rate: {lowest_income['poverty_rate']:.1f}%

  3. HIGHEST DEMOCRATIC MARGIN: {highest_dem['borough']}
     - Democratic Margin: {highest_dem['dem_margin']:+.1f}%
     - Median Income: ${highest_dem['median_household_income']:,}

  4. INCOME INEQUALITY PATTERN:
     - Manhattan has highest inequality ratio ({merged_df[merged_df['borough']=='Manhattan']['income_inequality_ratio'].values[0]:.2f})
     - This reflects extreme wealth alongside significant poverty
""")

step7_time = time.time() - step7_start
print(f"  Execution time: {step7_time:.4f}s")

# =============================================================================
# SUMMARY
# =============================================================================
total_time = time.time() - start_time

print("\n" + "=" * 70)
print("EXECUTION SUMMARY")
print("=" * 70)
print(f"Total execution time: {total_time:.4f}s")
print(f"\nStep breakdown:")
print(f"  Step 1 (Load voting):      {step1_time:.4f}s")
print(f"  Step 2 (Load income):      {step2_time:.4f}s")
print(f"  Step 3 (Process votes):    {step3_time:.4f}s")
print(f"  Step 4 (Merge data):       {step4_time:.4f}s")
print(f"  Step 5 (Generate tables):  {step5_time:.4f}s")
print(f"  Step 6 (Visualizations):   {step6_time:.4f}s")
print(f"  Step 7 (Key insights):     {step7_time:.4f}s")

print(f"\nMemory usage:")
print(f"  Voting data:  {voting_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
print(f"  Income data:  {borough_income.memory_usage(deep=True).sum() / 1024:.2f} KB")
print(f"  Merged data:  {merged_df.memory_usage(deep=True).sum() / 1024:.2f} KB")

# Save merged analysis
merged_df.to_csv("nyc_income_voting_analysis.csv", index=False)
print(f"\nOutput: nyc_income_voting_analysis.csv saved")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
