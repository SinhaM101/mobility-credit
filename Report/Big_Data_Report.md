# Socioeconomic Factors in Voting Patterns

**Author:** Monish Sinha  
**Course:** Big Data, University College Dublin  
**Professor:** Dr. Dylan-Ennis  
**Code Repository:** https://github.com/SinhaM101/mobility-credit

---

## Section 1. Introduction (1 page)

This project draws on two primary data sources that together provide a rich longitudinal view of socioeconomic conditions and political outcomes across the United States. Our first source is the U.S. Census American Community Survey (ACS) 5-Year Data Profiles, which cover social, economic, housing, and demographic characteristics for more than 3,100 U.S. counties from 2009 to 2023. These data consist of over 3,060 CSV files totaling approximately 150 MB across four profile tables (DP02–DP05), with more than 500 variables per county capturing detailed measures of income, employment, education, housing, and population composition. Our second source is a county-level presidential election dataset spanning elections from 2000 to 2024, comprising 94,019 records across seven election cycles and reporting vote counts by candidate and party.

### Volume

We process a substantial volume of structured data drawn primarily from the ACS and U.S. presidential election results. The ACS component comprises approximately 150 MB distributed across 3,060 CSV files (51 states × 15 years × 4 tables), including four Data Profile tables: Economic characteristics (DP03, ~40 MB with 141 variables per county), Social characteristics (DP02, ~35 MB with 158 variables), Demographic characteristics (DP05, ~20 MB with 94 variables), and Housing characteristics (DP04, ~25 MB with 145 variables). We combine these data with presidential voting records totaling 8.9 MB and 94,019 rows, resulting in approximately 160 MB of structured data overall. Our merged dataset spans more than 3,143 U.S. counties over 15 years and four ACS profiles, yielding 47,141 county-year observations with up to 400 columns each. All data processing is conducted on a macOS system (MacBook Air M4, 24 GB RAM) using Python 3.9.6 and Pandas 2.3.3.

### Variety

We integrate two datasets with fundamentally different structures and analytical roles, demonstrating meaningful data variety. The ACS Data Profiles (DP02, DP03, DP04, and DP05) are stored in a wide format with hundreds of variables per county, allowing us to capture detailed socioeconomic indicators such as income, employment, education, housing conditions, and demographic composition. In contrast, the presidential voting dataset is organized in a long format with many rows, reporting election outcomes by county, candidate, party affiliation, and vote counts across multiple election cycles. These structural differences reflect distinct purposes: the ACS data provide rich contextual and explanatory variables, while the voting data represent political outcomes. Together, they enable us to conduct correlation and regression analyses that link socioeconomic conditions to electoral behavior.

### Objective and Value

Our objective is to analyze how county-level economic conditions correlate with voting patterns in U.S. presidential elections from 2000 to 2024. By examining relationships between factors such as income inequality, employment rates, and electoral outcomes, we aim to better understand how socioeconomic conditions shape political behavior at a granular geographic level. This analysis adds value by helping us identify underserved communities and regional disparities, while also informing policy discussions by highlighting which economic indicators most strongly predict political preferences across diverse U.S. counties.

---

## Section 2. Traditional Solution (2 pages)

Before developing the big data pipeline, we built a single-threaded Python prototype to validate the processing logic and establish performance baselines. This prototype uses no parallelism and processes data using the Pandas library.

### Step 1: Load ACS Economic Data

Load the consolidated ACS DP03 economic data for 2020 containing employment, income, and poverty statistics for all U.S. counties.

**Code:**
```python
import pandas as pd
import time
import tracemalloc

tracemalloc.start()
start = time.time()

econ = pd.read_csv('data/acs_merged/economic/economic_2020.csv')

step1_time = time.time() - start
print(f"Rows: {len(econ):,}, Columns: {len(econ.columns)}")
print(f"Time: {step1_time:.4f}s, Memory: {tracemalloc.get_traced_memory()[1]/1024/1024:.1f} MB")
```

**Execution Results:**
| Metric | Value |
|--------|-------|
| Rows | 3,143 |
| Columns | 144 |
| Execution Time | 0.024 seconds |
| Memory Usage | 12.8 MB |

### Step 2: Load Presidential Voting Data

Load county-level presidential election results containing vote counts by candidate and party for all elections from 2000-2024.

**Code:**
```python
start = time.time()
pres = pd.read_csv('data/countypres_2000-2024.csv')
step2_time = time.time() - start

print(f"Rows: {len(pres):,}, Columns: {len(pres.columns)}")
print(f"Time: {step2_time:.4f}s")
```

**Execution Results:**
| Metric | Value |
|--------|-------|
| Rows | 94,019 |
| Columns | 13 |
| Execution Time | 0.045 seconds |
| Memory Usage | 39.1 MB (cumulative) |

### Step 3: Filter and Clean Data

Filter presidential data to match the economic data year (2020) and create standardized 5-digit FIPS codes for merging. FIPS codes are county identifiers consisting of a 2-digit state code and 3-digit county code.

**Code:**
```python
start = time.time()

# Filter to 2020 election
pres_2020 = pres[pres['year'] == 2020].copy()

# Create standardized 5-digit FIPS codes
econ['full_fips'] = (econ['state_fips'].astype(str).str.zfill(2) + 
                     econ['county_fips'].astype(str).str.zfill(3))

pres_2020['full_fips'] = (pres_2020['county_fips'].astype(str)
                          .str.replace('.0', '', regex=False)
                          .str.zfill(5))

step3_time = time.time() - start
print(f"Filtered rows: {len(pres_2020):,}, Time: {step3_time:.4f}s")
```

**Execution Results:**
| Metric | Value |
|--------|-------|
| Filtered Rows | 22,093 |
| Execution Time | 0.012 seconds |

### Step 4: Merge Datasets

Join the economic data with presidential voting data on the county FIPS code, creating a unified dataset for analysis.

**Code:**
```python
start = time.time()

merged = pd.merge(
    econ, 
    pres_2020[['full_fips', 'party', 'candidatevotes', 'totalvotes']], 
    on='full_fips', 
    how='inner'
)

step4_time = time.time() - start
print(f"Merged rows: {len(merged):,}, Columns: {len(merged.columns)}")
print(f"Time: {step4_time:.4f}s, Memory: {tracemalloc.get_traced_memory()[1]/1024/1024:.1f} MB")
```

**Execution Results:**
| Metric | Value |
|--------|-------|
| Merged Rows | 21,894 |
| Merged Columns | 148 |
| Execution Time | 0.008 seconds |
| Memory Usage | 67.0 MB (cumulative) |

### Step 5: Aggregate and Analyze

Determine the winning party per county (highest vote count) and calculate average economic indicators grouped by winning party.

**Code:**
```python
start = time.time()

# Find winner per county (candidate with most votes)
winner_idx = pres_2020.groupby('full_fips')['candidatevotes'].idxmax()
winners = pres_2020.loc[winner_idx][['full_fips', 'party']].copy()
winners.columns = ['full_fips', 'winning_party']

# Merge with economic data
analysis = pd.merge(econ, winners, on='full_fips', how='inner')

# Find population column and aggregate by winning party
pop_col = [c for c in analysis.columns if 'population_16' in c][0]
result = analysis.groupby('winning_party').agg({
    pop_col: ['mean', 'sum', 'count']
}).round(0)

step5_time = time.time() - start
print(f"Time: {step5_time:.4f}s")
print(result)
```

**Execution Results:**
| Metric | Value |
|--------|-------|
| Execution Time | 0.008 seconds |

**Analysis Results (2020 Election):**
| Winning Party | County Count | Total Population | Avg Population |
|---------------|--------------|------------------|----------------|
| DEMOCRAT | 546 | 157,753,458 | 288,926 |
| REPUBLICAN | 2,569 | 103,559,736 | 40,311 |

### Execution Summary

| Step | Description | Time (s) | % of Total |
|------|-------------|----------|------------|
| 1 | Load Economic Data | 0.024 | 27% |
| 2 | Load Presidential Data | 0.045 | 51% |
| 3 | Filter & Clean | 0.012 | 13% |
| 4 | Merge Datasets | 0.008 | 9% |
| 5 | Aggregate & Analyze | 0.008 | - |
| **Total** | | **0.089** | **100%** |

**Peak Memory Usage:** 67.0 MB

**Key Finding:** Step 2 (Load Presidential Data) consumes 51% of total execution time, making it the primary candidate for MapReduce optimization.

---

## Section 3. MapReduce Optimisation (2 pages)

### Identifying Bottlenecks

From the baseline analysis in Section 2, we identified two time-consuming steps suitable for MapReduce optimization:

1. **Step 2: Load Presidential Voting Data** (0.045s, 51% of total time)
2. **Step 4: Merge Datasets** (0.008s, 9% of total time)

### Why MapReduce is Suitable

These steps are suitable for parallel processing because:

1. **Data Loading (Map Phase):** Each CSV file is independent and can be read in parallel. There are no dependencies between files—this is an "embarrassingly parallel" pattern where each mapper can process a separate file or partition.

2. **Merge/Join (Reduce Phase):** The merge operation groups records by county FIPS code. This is a classic reduce operation where all records with the same key are collected and combined. The shuffle phase naturally groups data by key, and the reduce phase performs the join.

**Expected Improvement:** We expected a 4–8× speedup on a multi-core system, with linear scaling as data size increases beyond memory capacity.

### MapReduce Solution

We implemented the MapReduce solution using PySpark Core RDD API (not DataFrame/SQL) as required.

#### Map Function for Economic Data

```python
def map_economic(line, header_indices):
    """Map: Parse economic CSV line and emit (fips, record) pair"""
    fields = line.split(',')
    if len(fields) < 5 or fields[0] == 'year':
        return None
    
    state_fips = fields[header_indices['state_fips']].zfill(2)
    county_fips = fields[header_indices['county_fips']].zfill(3)
    full_fips = state_fips + county_fips
    
    return (full_fips, {
        'source': 'economic',
        'year': fields[header_indices['year']],
        'county': fields[header_indices['county']],
        'state': fields[header_indices['state']],
        'population': fields[header_indices.get('population', 5)]
    })
```

#### Map Function for Voting Data

```python
def map_voting(line):
    """Map: Parse voting CSV line and emit (fips, record) pair"""
    fields = line.split(',')
    if len(fields) < 10 or fields[0] == 'year':
        return None
    
    county_fips = fields[4].replace('.0', '').zfill(5)
    votes = int(float(fields[8])) if fields[8].strip() else 0
    
    return (county_fips, {
        'source': 'voting',
        'year': fields[0],
        'party': fields[7],
        'votes': votes
    })
```

#### Reduce Function

```python
def reduce_merge(records):
    """Reduce: Merge economic and voting records for a county"""
    records_list = list(records)
    
    economic_data = None
    voting_records = []
    
    for record in records_list:
        if record['source'] == 'economic':
            economic_data = record
        else:
            voting_records.append(record)
    
    if economic_data is None or not voting_records:
        return None
    
    # Find winner (candidate with most votes)
    winner = max(voting_records, key=lambda x: x['votes'])
    
    return {
        'county': economic_data['county'],
        'state': economic_data['state'],
        'population': int(float(economic_data['population'])),
        'winning_party': winner['party']
    }
```

#### Spark RDD Implementation

```python
from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("ACS_Voting_MapReduce").setMaster("local[4]")
sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")

# MAP PHASE: Load and parse economic data
economic_rdd = sc.textFile("data/acs_merged/economic/economic_2020.csv") \
    .map(lambda line: map_economic(line, header_indices)) \
    .filter(lambda x: x is not None)

# MAP PHASE: Load and parse voting data (filter to 2020)
voting_rdd = sc.textFile("data/countypres_2000-2024.csv") \
    .map(map_voting) \
    .filter(lambda x: x is not None) \
    .filter(lambda x: x[1]['year'] == '2020')

# SHUFFLE & REDUCE PHASE: Union and group by key
merged_rdd = economic_rdd.union(voting_rdd) \
    .groupByKey() \
    .mapValues(reduce_merge) \
    .filter(lambda x: x[1] is not None)

# AGGREGATE: Count by winning party
party_counts = merged_rdd \
    .map(lambda x: (x[1]['winning_party'], (x[1]['population'], 1))) \
    .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
    .collect()

sc.stop()
```

### MapReduce Results

| Configuration | Time (s) | Speedup vs Baseline |
|---------------|----------|---------------------|
| Baseline (Pandas) | 0.089 | 1.00× |
| Spark local[1] | 1.365 | 0.07× |
| Spark local[2] | 0.558 | 0.16× |
| Spark local[4] | 0.537 | 0.17× |

**Analysis Results (identical to baseline):**
| Winning Party | County Count | Avg Population |
|---------------|--------------|----------------|
| DEMOCRAT | 546 | 288,926 |
| REPUBLICAN | 2,569 | 40,311 |

### Why Results Deviate from Expectations

**Expected:** 4–8× speedup with parallel processing  
**Actual:** 0.07–0.17× (6–14× *slower* than baseline)

#### Reasons for Deviation:

1. **JVM Startup Overhead:** Spark requires 1–2 seconds to initialize the JVM, load classes, and set up the execution environment. For a job that completes in 0.089 seconds with Pandas, this overhead is 10–15× the actual computation time.

2. **Dataset Size Too Small:** Our dataset (~67 MB) is below the threshold where MapReduce provides benefit:
   - < 100 MB: Single-threaded processing is faster
   - 100 MB – 10 GB: Local parallelism may help
   - > 10 GB: MapReduce/Spark provides clear benefit

3. **Serialization Overhead:** PySpark must serialize Python objects to JVM and back, adding latency for each record. This overhead is amortized over large datasets but dominates for small ones.

4. **Task Scheduling Overhead:** Spark's task scheduler adds overhead for dividing work among executors, which is not justified for sub-second jobs.

### Projected Performance at Scale

| Dataset Size | Pandas (est.) | Spark 4-core (est.) | Speedup |
|--------------|---------------|---------------------|---------|
| 67 MB | 0.089s | 0.537s | 0.17× |
| 670 MB | 0.89s | 0.8s | 1.11× |
| 6.7 GB | 8.9s | 3.5s | 2.5× |
| 67 GB | 89s | 15s | 5.9× |

### Conclusion

The MapReduce implementation is **correct and functional**, producing identical results to the baseline. However, the current dataset is too small to benefit from parallel processing—the overhead of Spark's distributed computing framework exceeds the computation time.

For production use with larger datasets (>1 GB), the MapReduce approach would provide significant speedup, especially on a multi-node cluster where data can be distributed across machines.

**Key Findings:**
- Democratic-winning counties: **546 counties**, avg population **288,926** (urban areas)
- Republican-winning counties: **2,569 counties**, avg population **40,311** (rural areas)
- This quantifies the **urban-rural political divide** in the 2020 U.S. presidential election

---

*Code Repository: https://github.com/SinhaM101/mobility-credit*
