# Income Inequality and Voting Patterns Analysis

Big Data Project: Analyzing income inequality and voting patterns across all U.S. states and counties using American Community Survey (ACS) data and presidential election results.

---

## Project Overview

**Objective:** How do county-level economic conditions correlate with voting patterns in the United States?

**Value:** Understanding income inequality patterns and their correlation with political behavior helps inform policy decisions, identify underserved communities, and reveal socioeconomic-political relationships.

**Current Status:** Full national dataset with ACS economic data and presidential voting data

---

## Big Data Justification

### Volume
- **3,143+ counties** across all 51 states (including DC)
- **137 economic variables** per county from ACS DP03
- **2.9 MB** ACS economic data + **94,019 rows** presidential voting data
- **7 election cycles** (2000-2024) of voting data

### Variety
Multiple data sources with different focuses:
| Dataset | Scope | Content Focus |
|---------|-------|---------------|
| ACS DP03 Economic | 51 states, 3,143+ counties | Employment, income, poverty, commuting |
| Presidential Voting | 2000-2024 | County-level election results by candidate |

### Value
- Income inequality measurement across all U.S. counties
- Voting pattern analysis by economic indicators
- Cross-dataset correlations (income ↔ voting behavior)
- Policy-relevant insights at national scale

---

## Datasets

### ACS 5-Year Data Profiles (2024 vintage, covers 2020-2024)

Downloaded via Census API for all U.S. counties:

| Table | Name | Variables | Description |
|-------|------|-----------|-------------|
| DP03 | Economic Characteristics | 137 | Employment, occupation, industry, income, poverty, health insurance, commuting |

### Presidential Election Data

- **countypres_2000-2024.csv** - County-level presidential election results (2000-2024)
- Includes: state, county, year, candidate, party, votes, total votes

---

## Data Download Scripts

### Download ACS DP03 Economic Data

```bash
# Set your Census API key
export CENSUS_API_KEY='your_key_here'

# Download for a single state (e.g., Alabama = 01)
python3 scripts/download_dp03_full.py --state 01

# Download for ALL states (51 states, ~3 minutes)
python3 scripts/download_dp03_full.py
```

**Output:** `data/acs_downloads/{state_fips}_{state_name}_DP03_Economic_FULL.csv`

### Key DP03 Economic Variables

| Category | Variables |
|----------|-----------|
| Employment | Labor force, employed, unemployed, unemployment rate |
| Occupation | Management, service, sales, construction, production |
| Industry | Agriculture, manufacturing, retail, healthcare, etc. |
| Income | All brackets ($0-$200k+), median, mean household income |
| Per Capita | Per capita income, median earnings |
| Poverty | Poverty rate, health insurance coverage |
| Commuting | Drove alone, carpooled, public transit, work from home |

### Merge Economic + Voting Data

```bash
python3 scripts/merge_economic_presidential.py
```

**Output:** `data/alabama_economic_presidential_merged.csv`

---

## Installation & Usage

### Requirements
```bash
pip install pandas requests
```

### Get a Census API Key
1. Visit: https://api.census.gov/data/key_signup.html
2. Register for a free key
3. Set environment variable: `export CENSUS_API_KEY='your_key'`

---

## System Specifications

| Component | Value |
|-----------|-------|
| Python Version | 3.9.6 |
| Pandas Version | 2.3.3 |
| OS | macOS |

---

## Repository Structure

```
mobility-credit/
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
├── project_qa.txt                      # Weekly progress Q&A
├── data/
│   ├── countypres_2000-2024.csv        # Presidential voting data (2000-2024)
│   ├── alabama_economic_presidential_merged.csv  # Merged AL data
│   └── acs_downloads/                  # ACS economic data (all states)
│       ├── 01_Alabama_DP03_Economic_FULL.csv
│       ├── 06_California_DP03_Economic_FULL.csv
│       ├── 36_New_York_DP03_Economic_FULL.csv
│       ├── 48_Texas_DP03_Economic_FULL.csv
│       └── ... (51 state files total)
├── scripts/
│   ├── download_dp03_full.py           # Download ALL DP03 economic data
│   ├── download_dp03_economic.py       # Download curated DP03 variables
│   ├── download_acs_profiles.py        # Download all 4 ACS profile tables
│   ├── merge_economic_presidential.py  # Merge economic + voting data
│   └── filter_presidential_data.py     # Filter voting data by state
└── Report/
    └── main.tex                        # LaTeX report
```

---

## License

This project uses publicly available American Community Survey data from the U.S. Census Bureau.