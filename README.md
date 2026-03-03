# Income Inequality and Voting Patterns Analysis

Big Data Project: Analyzing income inequality and voting patterns across all U.S. states and counties using American Community Survey (ACS) data and presidential election results.

---

## Project Overview

**Objective:** How do county-level economic, demographic, social, and housing conditions correlate with voting patterns in the United States?

**Value:** Understanding income inequality patterns and their correlation with political behavior helps inform policy decisions, identify underserved communities, and reveal socioeconomic-political relationships.

**Current Status:** Full national dataset with ACS data (economic, social, housing, demographic) for 2009-2020 and presidential voting data 2000-2024

---

## Big Data Justification

### Volume
- **3,143+ counties** across all 51 states (including DC)
- **500+ variables** per county across 4 ACS Data Profile tables
- **93 MB** ACS data (2,053 files) + **8.9 MB** presidential voting data (94,019 rows)
- **12 years** of ACS data (2009-2020) + **7 election cycles** (2000-2024)

### Variety
Multiple data sources with different structures:
| Dataset | Format | Variables | Content Focus |
|---------|--------|-----------|---------------|
| ACS DP02 Social | Wide | 158 | Households, education, language, ancestry |
| ACS DP03 Economic | Wide | 141 | Employment, income, poverty, commuting |
| ACS DP04 Housing | Wide | 145 | Occupancy, structure, value, rent |
| ACS DP05 Demographic | Wide | 93 | Age, sex, race, population |
| Presidential Voting | Long | 12 | County-level election results by candidate |

### Value
- Income inequality measurement across all U.S. counties
- Voting pattern analysis by economic indicators
- Cross-dataset correlations (income ↔ voting behavior)
- Policy-relevant insights at national scale

---

## Datasets

### ACS 5-Year Data Profiles (2009-2020)

Downloaded via Census API for all U.S. counties:

| Table | Name | Variables | Description |
|-------|------|-----------|-------------|
| DP02 | Social Characteristics | 158 | Households, education, language, ancestry |
| DP03 | Economic Characteristics | 141 | Employment, income, poverty, commuting |
| DP04 | Housing Characteristics | 145 | Occupancy, structure, value, rent |
| DP05 | Demographic Characteristics | 93 | Age, sex, race, population |

### Presidential Election Data

- **countypres_2000-2024.csv** - County-level presidential election results (2000-2024)
- Includes: state, county, year, candidate, party, votes, total votes

---

## Data Download Scripts

### Download ACS Data

```bash
# Set your Census API key
export CENSUS_API_KEY='your_key_here'

# Download all years (2009-2020) for all states
python3 scripts/download_dp02_full.py   # Social
python3 scripts/download_dp03_full.py   # Economic
python3 scripts/download_dp04_full.py   # Housing
python3 scripts/download_dp05_full.py   # Demographic

# Download single year
python3 scripts/download_dp03_full.py --year 2020
```

### Merge State Files

```bash
# Merge all state files into consolidated datasets
python3 scripts/merge_acs_data.py
```

**Output:** `data/acs_merged/{category}/{category}_all_years.csv`

### MapReduce Analysis (Spark RDD)

```bash
# Run MapReduce performance comparison
python3 scripts/mapreduce_analysis.py
```

**Output:** `data/mapreduce_output/performance_results.txt`

---

## MapReduce Performance Results

| Configuration | Time (s) | Speedup |
|---------------|----------|---------|
| Baseline (Pandas) | 0.103 | 1.00× |
| Spark local[1] | 1.311 | 0.08× |
| Spark local[2] | 0.550 | 0.19× |
| Spark local[4] | 0.523 | 0.20× |

**Key Finding:** For small datasets (<100 MB), Spark overhead exceeds computation time. MapReduce benefits emerge at >1 GB scale.

---

## Installation & Usage

### Requirements
```bash
pip install pandas requests pyspark
```

### Get a Census API Key
1. Visit: https://api.census.gov/data/key_signup.html
2. Register for a free key
3. Set environment variable: `export CENSUS_API_KEY='your_key'`

---

## System Specifications

| Component | Value |
|-----------|-------|
| Machine | MacBook Air |
| Chip | Apple M4 (10 cores: 4 performance + 6 efficiency) |
| RAM | 24 GB |
| OS | macOS 26.2 (Build 25C56) |
| Python | 3.9.6 |
| Pandas | 2.3.3 |

---

## Repository Structure

```
mobility-credit/
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
├── data/
│   ├── countypres_2000-2024.csv        # Presidential voting data (2000-2024)
│   ├── acs_downloads/                  # Raw ACS data by state/year
│   │   ├── economic/                   # DP03 (51 states × 12 years)
│   │   ├── social/                     # DP02 (51 states × 12 years)
│   │   ├── housing/                    # DP04 (51 states × 7 years)
│   │   └── demographic/                # DP05 (51 states × 12 years)
│   └── acs_merged/                     # Consolidated ACS data
│       ├── economic/
│       │   ├── economic_2009.csv       # All counties, single year
│       │   ├── economic_2020.csv
│       │   └── economic_all_years.csv  # 37,577 rows, 769 columns
│       ├── social/
│       │   └── social_all_years.csv    # 37,710 rows, 453 columns
│       ├── housing/
│       │   └── housing_all_years.csv   # 18,798 rows, 392 columns
│       └── demographic/
│           └── demographic_all_years.csv # 37,710 rows, 261 columns
├── scripts/
│   ├── download_dp02_full.py           # Download DP02 Social data
│   ├── download_dp03_full.py           # Download DP03 Economic data
│   ├── download_dp04_full.py           # Download DP04 Housing data
│   ├── download_dp05_full.py           # Download DP05 Demographic data
│   ├── merge_acs_data.py               # Merge state files into master CSVs
│   └── mapreduce_analysis.py           # Spark RDD MapReduce analysis
└── Report/
    └── main.tex                        # LaTeX report
```

---

## License

This project uses publicly available American Community Survey data from the U.S. Census Bureau.