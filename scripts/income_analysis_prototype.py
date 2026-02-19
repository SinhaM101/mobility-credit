"""
Big Data Project: Income Variation Analysis Across New York State
Traditional Solution Prototype (Single-threaded Python)

This prototype analyzes income variation using American Community Survey (ACS) data.
Focus: New York City income patterns

Datasets:
1. NYC Demographic ACS.csv - Population, age, sex, race data
2. NYC Economic ACS.csv - Employment, income, poverty data  
3. NYC Social ACS.csv - Households, education, language data
4. NYC Housing ACS.csv - Housing occupancy, value, rent data
"""

import pandas as pd
import time
import sys
import os

# Track execution metrics
start_time = time.time()

print("=" * 60)
print("INCOME VARIATION ANALYSIS - NEW YORK STATE")
print("Traditional Solution Prototype")
print("=" * 60)

# =============================================================================
# STEP 1: Load all datasets
# =============================================================================
print("\n[STEP 1] Loading datasets...")
step1_start = time.time()

demographic_df = pd.read_csv("NYC Demographic ACS.csv")
economic_df = pd.read_csv("NYC Economic ACS.csv")
social_df = pd.read_csv("NYC Social ACS.csv")
housing_df = pd.read_csv("NYC Housing ACS.csv")

step1_time = time.time() - step1_start
print(f"  - Demographic: {len(demographic_df)} rows, {len(demographic_df.columns)} columns")
print(f"  - Economic: {len(economic_df)} rows, {len(economic_df.columns)} columns")
print(f"  - Social: {len(social_df)} rows, {len(social_df.columns)} columns")
print(f"  - Housing: {len(housing_df)} rows, {len(housing_df.columns)} columns")
print(f"  Execution time: {step1_time:.4f} seconds")

# =============================================================================
# STEP 2: Clean and standardize column names
# =============================================================================
print("\n[STEP 2] Cleaning column names...")
step2_start = time.time()

def clean_columns(df):
    """Standardize column names across all datasets"""
    df.columns = [
        'Label', 'Estimate', 'Margin_of_Error', 'Percent', 'Percent_MOE'
    ]
    return df

demographic_df = clean_columns(demographic_df)
economic_df = clean_columns(economic_df)
social_df = clean_columns(social_df)
housing_df = clean_columns(housing_df)

step2_time = time.time() - step2_start
print(f"  Columns standardized to: {list(economic_df.columns)}")
print(f"  Execution time: {step2_time:.4f} seconds")

# =============================================================================
# STEP 3: Extract income-related data from Economic dataset
# =============================================================================
print("\n[STEP 3] Extracting income-related data...")
step3_start = time.time()

# Define income-related keywords
income_keywords = [
    'income', 'earnings', 'median', 'mean', 'poverty', 
    '$10,000', '$15,000', '$25,000', '$35,000', '$50,000',
    '$75,000', '$100,000', '$150,000', '$200,000'
]

def extract_income_rows(df, keywords):
    """Extract rows containing income-related information"""
    mask = df['Label'].str.lower().str.contains('|'.join([k.lower() for k in keywords]), na=False)
    return df[mask].copy()

income_data = extract_income_rows(economic_df, income_keywords)

step3_time = time.time() - step3_start
print(f"  Extracted {len(income_data)} income-related rows from Economic dataset")
print(f"  Execution time: {step3_time:.4f} seconds")

# =============================================================================
# STEP 4: Clean numeric values (remove commas, convert to numbers)
# =============================================================================
print("\n[STEP 4] Cleaning numeric values...")
step4_start = time.time()

def clean_numeric(value):
    """Convert string values to numeric, handling special cases"""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value in ['(X)', '*****', '-', '']:
        return None
    # Remove commas, dollar signs, percent signs
    value = value.replace(',', '').replace('$', '').replace('%', '').replace('±', '')
    try:
        return float(value)
    except ValueError:
        return None

# Apply cleaning to Estimate column
income_data['Estimate_Clean'] = income_data['Estimate'].apply(clean_numeric)
income_data['Percent_Clean'] = income_data['Percent'].apply(clean_numeric)

# Clean the Label column (remove leading spaces)
income_data['Label_Clean'] = income_data['Label'].str.strip()

step4_time = time.time() - step4_start
print(f"  Cleaned {len(income_data)} rows")
print(f"  Non-null estimates: {income_data['Estimate_Clean'].notna().sum()}")
print(f"  Execution time: {step4_time:.4f} seconds")

# =============================================================================
# STEP 5: Analyze key income metrics
# =============================================================================
print("\n[STEP 5] Analyzing key income metrics...")
step5_start = time.time()

# Extract key income statistics
key_metrics = {}

# Find median household income
median_hh = income_data[income_data['Label'].str.contains('Median household income', na=False)]
if not median_hh.empty:
    key_metrics['Median Household Income'] = median_hh['Estimate_Clean'].values[0]

# Find mean household income
mean_hh = income_data[income_data['Label'].str.contains('Mean household income', na=False)]
if not mean_hh.empty:
    key_metrics['Mean Household Income'] = mean_hh['Estimate_Clean'].values[0]

# Find per capita income
per_capita = income_data[income_data['Label'].str.contains('Per capita income', na=False)]
if not per_capita.empty:
    key_metrics['Per Capita Income'] = per_capita['Estimate_Clean'].values[0]

# Find median family income
median_fam = income_data[income_data['Label'].str.contains('Median family income', na=False)]
if not median_fam.empty:
    key_metrics['Median Family Income'] = median_fam['Estimate_Clean'].values[0]

# Find poverty rate
poverty = economic_df[economic_df['Label'].str.contains('All people', na=False) & 
                      economic_df['Label'].str.contains('poverty', case=False, na=False)]

step5_time = time.time() - step5_start

print("\n  KEY INCOME METRICS FOR NEW YORK STATE:")
print("  " + "-" * 45)
for metric, value in key_metrics.items():
    if value:
        print(f"  {metric}: ${value:,.0f}")
print(f"\n  Execution time: {step5_time:.4f} seconds")

# =============================================================================
# STEP 6: Analyze income distribution (household income brackets)
# =============================================================================
print("\n[STEP 6] Analyzing income distribution...")
step6_start = time.time()

# Extract household income brackets directly from economic_df (not filtered income_data)
# These are in the "INCOME AND BENEFITS" section starting around row 57
income_section = economic_df[
    (economic_df.index >= 57) & (economic_df.index <= 68)
].copy()

# Clean the data
income_section['Estimate_Clean'] = income_section['Estimate'].apply(clean_numeric)
income_section['Percent_Clean'] = income_section['Percent'].apply(clean_numeric)

print("\n  HOUSEHOLD INCOME DISTRIBUTION:")
print("  " + "-" * 50)

distribution_data = []
for idx, row in income_section.iterrows():
    label = row['Label'].strip()
    count = row['Estimate_Clean']
    pct = row['Percent_Clean']
    if count and pct and '$' in label:
        distribution_data.append({
            'Bracket': label,
            'Households': count,
            'Percent': pct
        })
        print(f"  {label:25s}: {count:>12,.0f} ({pct:>5.1f}%)")

step6_time = time.time() - step6_start
print(f"\n  Execution time: {step6_time:.4f} seconds")

# =============================================================================
# STEP 7: Cross-dataset analysis (Variety - combining multiple data sources)
# =============================================================================
print("\n[STEP 7] Cross-dataset analysis (demonstrating data variety)...")
step7_start = time.time()

# Extract education data from Social dataset
education_data = social_df[social_df['Label'].str.contains("Bachelor's degree or higher|High school graduate or higher", na=False)]
education_data = education_data.copy()
education_data['Percent_Clean'] = education_data['Percent'].apply(clean_numeric)

# Extract housing value data from Housing dataset
housing_value = housing_df[housing_df['Label'].str.contains('Median \\(dollars\\)', na=False, regex=True)]
housing_value = housing_value.copy()
housing_value['Estimate_Clean'] = housing_value['Estimate'].apply(clean_numeric)

# Extract poverty data from Economic dataset
poverty_data = economic_df[economic_df['Label'].str.contains('All people', na=False)]
poverty_data = poverty_data.copy()
poverty_data['Percent_Clean'] = poverty_data['Percent'].apply(clean_numeric)

print("\n  CROSS-DATASET INSIGHTS:")
print("  " + "-" * 50)

# Education attainment
for idx, row in education_data.iterrows():
    label = row['Label'].strip()
    pct = row['Percent_Clean']
    if pct:
        print(f"  Education - {label}: {pct:.1f}%")

# Housing values
for idx, row in housing_value.iterrows():
    val = row['Estimate_Clean']
    if val:
        print(f"  Median Home Value: ${val:,.0f}")
        break  # Just get the first one (owner-occupied)

# Poverty rate
for idx, row in poverty_data.iterrows():
    pct = row['Percent_Clean']
    if pct:
        print(f"  Poverty Rate (All people): {pct:.1f}%")
        break

# Rent burden from Housing dataset
rent_burden = housing_df[housing_df['Label'].str.contains('35.0 percent or more', na=False)]
rent_burden = rent_burden.copy()
rent_burden['Percent_Clean'] = rent_burden['Percent'].apply(clean_numeric)
for idx, row in rent_burden.iterrows():
    pct = row['Percent_Clean']
    if pct and 'GRAPI' not in str(housing_df.iloc[idx-1]['Label'] if idx > 0 else ''):
        print(f"  Rent-Burdened Households (>35% income): {pct:.1f}%")
        break

step7_time = time.time() - step7_start
print(f"\n  Execution time: {step7_time:.4f} seconds")

# =============================================================================
# STEP 8: Generate summary statistics for reporting
# =============================================================================
print("\n[STEP 8] Generating summary statistics...")
step8_start = time.time()

summary_stats = {
    'Total Population': 19852366,  # From demographic data
    'Total Households': 7722646,   # From economic data
    'Median Household Income': key_metrics.get('Median Household Income', 0),
    'Mean Household Income': key_metrics.get('Mean Household Income', 0),
    'Per Capita Income': key_metrics.get('Per Capita Income', 0),
    'Income Inequality Ratio': key_metrics.get('Mean Household Income', 0) / key_metrics.get('Median Household Income', 1) if key_metrics.get('Median Household Income') else 0
}

print("\n  SUMMARY STATISTICS:")
print("  " + "-" * 50)
for stat, value in summary_stats.items():
    if 'Ratio' in stat:
        print(f"  {stat}: {value:.2f}")
    elif 'Income' in stat:
        print(f"  {stat}: ${value:,.0f}")
    else:
        print(f"  {stat}: {value:,}")

# Income inequality indicator: Mean/Median ratio > 1 indicates right-skewed distribution
print(f"\n  Note: Income Inequality Ratio > 1 indicates income inequality")
print(f"        (Mean > Median suggests high earners pulling up the average)")

step8_time = time.time() - step8_start
print(f"\n  Execution time: {step8_time:.4f} seconds")

# =============================================================================
# SUMMARY: Execution metrics
# =============================================================================
total_time = time.time() - start_time

print("\n" + "=" * 60)
print("EXECUTION SUMMARY")
print("=" * 60)
print(f"Total execution time: {total_time:.4f} seconds")
print(f"\nStep breakdown:")
print(f"  Step 1 (Load data):        {step1_time:.4f}s")
print(f"  Step 2 (Clean columns):    {step2_time:.4f}s")
print(f"  Step 3 (Extract income):   {step3_time:.4f}s")
print(f"  Step 4 (Clean values):     {step4_time:.4f}s")
print(f"  Step 5 (Key metrics):      {step5_time:.4f}s")
print(f"  Step 6 (Distribution):     {step6_time:.4f}s")
print(f"  Step 7 (Cross-dataset):    {step7_time:.4f}s")
print(f"  Step 8 (Summary stats):    {step8_time:.4f}s")

# Memory usage
print(f"\nMemory usage:")
print(f"  Demographic dataset: {demographic_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
print(f"  Economic dataset:    {economic_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
print(f"  Social dataset:      {social_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
print(f"  Housing dataset:     {housing_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
total_memory = (demographic_df.memory_usage(deep=True).sum() + 
                economic_df.memory_usage(deep=True).sum() +
                social_df.memory_usage(deep=True).sum() +
                housing_df.memory_usage(deep=True).sum()) / 1024
print(f"  Total:               {total_memory:.2f} KB")

print(f"\nSystem info:")
print(f"  Python version: {sys.version.split()[0]}")
print(f"  Pandas version: {pd.__version__}")

# Save cleaned income data for further analysis
income_data.to_csv("cleaned_income_data.csv", index=False)
print(f"\nOutput: cleaned_income_data.csv saved with {len(income_data)} rows")

print("\n" + "=" * 60)
print("PROTOTYPE COMPLETE")
print("=" * 60)
