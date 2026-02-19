# Income Variation Analysis - New York State

Big Data Project: Analyzing income variation across New York State using American Community Survey (ACS) data.

---

## Project Overview

**Objective:** Analyze how income varies across New York State by examining household income distribution, key income metrics, and their relationship to education, housing, and poverty indicators.

**Value:** Understanding income inequality patterns helps inform policy decisions, identify underserved communities, and reveal correlations between socioeconomic factors.

**Current Status:** Traditional solution prototype (single-threaded Python)

**Next Phase:** Big data pipeline with parallel processing

---

## Big Data Justification

### Volume
- **590 total data entries** across 4 datasets
- **~46 KB** raw CSV data (prototype scale)
- **19.8 million population** represented in New York State
- Scalable to full ACS microdata (millions of records, GB-scale)

### Variety
Four distinct structured datasets with different focuses:
| Dataset | Rows | Content Focus |
|---------|------|---------------|
| Demographic | 113 | Population, age, sex, race |
| Economic | 145 | Employment, income, poverty |
| Social | 172 | Households, education, language |
| Housing | 160 | Occupancy, value, rent |

### Value
- Income inequality measurement (Mean/Median ratio: 1.49)
- Cross-dataset correlations (income ↔ education, housing, poverty)
- Policy-relevant insights for New York State

---

## Datasets

All data sourced from **American Community Survey (ACS)** for New York State:

1. **NYC Demographic ACS.csv** - Population demographics, age distribution, sex ratios, race/ethnicity
2. **NYC Economic ACS.csv** - Employment status, income brackets, poverty levels, health insurance
3. **NYC Social ACS.csv** - Household types, education attainment, language, citizenship
4. **NYC Housing ACS.csv** - Housing occupancy, home values, rent, mortgage costs

---

## Traditional Solution (Prototype)

### Eight-Step Processing Pipeline

| Step | Description | Execution Time |
|------|-------------|----------------|
| 1 | Load all 4 datasets | ~0.007s |
| 2 | Clean and standardize column names | ~0.0001s |
| 3 | Extract income-related data | ~0.003s |
| 4 | Clean numeric values (remove commas, handle special values) | ~0.001s |
| 5 | Analyze key income metrics | ~0.002s |
| 6 | Analyze income distribution (10 brackets) | ~0.002s |
| 7 | Cross-dataset analysis (education, housing, poverty) | ~0.004s |
| 8 | Generate summary statistics | ~0.0001s |

**Total Execution Time:** ~0.02 seconds  
**Total Memory Usage:** ~224 KB

### Key Findings

#### Income Metrics (New York State)
| Metric | Value |
|--------|-------|
| Median Household Income | $85,974 |
| Mean Household Income | $128,247 |
| Per Capita Income | $50,712 |
| Median Family Income | $106,873 |
| Income Inequality Ratio | 1.49 |

#### Income Distribution
| Bracket | Households | Percent |
|---------|------------|---------|
| Less than $10,000 | 448,836 | 5.8% |
| $10,000 - $14,999 | 304,684 | 3.9% |
| $15,000 - $24,999 | 483,327 | 6.3% |
| $25,000 - $34,999 | 475,794 | 6.2% |
| $35,000 - $49,999 | 686,990 | 8.9% |
| $50,000 - $74,999 | 1,051,347 | 13.6% |
| $75,000 - $99,999 | 883,133 | 11.4% |
| $100,000 - $149,999 | 1,287,671 | 16.7% |
| $150,000 - $199,999 | 782,846 | 10.1% |
| $200,000 or more | 1,318,018 | 17.1% |

#### Cross-Dataset Insights
- **High School Graduate or Higher:** 88.0%
- **Bachelor's Degree or Higher:** 40.2%
- **Median Home Value:** $423,800
- **Poverty Rate:** 14.0%
- **Rent-Burdened Households (>35% income):** 26.2%

---

## Installation & Usage

### Requirements
```bash
pip install -r requirements.txt
```

### Run the Prototype
```bash
python3 income_analysis_prototype.py
```

### Output
- Console output with step-by-step analysis
- `cleaned_income_data.csv` - Extracted income data (23 rows)

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
├── README.md                        # Project documentation
├── requirements.txt                 # Python dependencies
├── project_qa.txt                   # Weekly progress Q&A
├── data/
│   ├── NYC Demographic ACS.csv      # Dataset: demographics
│   ├── NYC Economic ACS.csv         # Dataset: economic indicators
│   ├── NYC Social ACS.csv           # Dataset: social characteristics
│   ├── NYC Housing ACS.csv          # Dataset: housing data
│   ├── countypres_2000-2024.csv     # Dataset: presidential voting (full)
│   ├── countypres_ny_state.csv      # Dataset: NY State voting (filtered)
│   └── countypres_nyc.csv           # Dataset: NYC voting (filtered)
├── scripts/
│   ├── income_analysis_prototype.py # Traditional solution prototype
│   ├── filter_presidential_data.py  # Filter voting data to NYC
│   ├── income_voting_analysis.py    # Income vs voting analysis
│   └── create_graphs.py             # Generate visualizations
├── output/
│   ├── cleaned_income_data.csv      # Extracted income data
│   ├── nyc_income_voting_analysis.csv # Merged analysis data
│   ├── nyc_income_voting_graphs.png # Visualization: graphs
│   └── nyc_summary_table.png        # Visualization: summary table
└── Report/
    └── main_simple.tex              # LaTeX report
```

---

## License

This project uses publicly available American Community Survey data from the U.S. Census Bureau.