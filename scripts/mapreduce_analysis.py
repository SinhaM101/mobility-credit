#!/usr/bin/env python3
"""
MapReduce Analysis using PySpark Core RDD API

This script implements the MapReduce solution for combining ACS economic data
with presidential voting data and analyzing voting patterns by economic indicators.

Uses Spark Core RDD API (NOT DataFrame/SQL) as required.
Supports both CSV and Parquet file formats.
"""

from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
import time
import os
import pandas as pd

# Configuration
ECONOMIC_PARQUET = "./data/parquet/economic/economic_2020.parquet"
VOTING_PARQUET = "./data/parquet/voting/countypres_2020.parquet"
ECONOMIC_CSV = "./data/acs_merged/economic/economic_2020.csv"
VOTING_CSV = "./data/countypres_2000-2024.csv"
# All years merged dataset (larger - ~84MB)
ECONOMIC_ALL_YEARS_CSV = "./data/acs_merged/economic/economic_all_years.csv"
OUTPUT_DIR = "./data/mapreduce_output"


def parse_economic_line(line, header_indices):
    """Parse a line from economic CSV and extract key fields."""
    try:
        fields = line.split(',')
        if len(fields) < max(header_indices.values()) + 1:
            return None
        
        # Skip header
        if fields[header_indices['year']] == 'year':
            return None
            
        year = fields[header_indices['year']]
        county = fields[header_indices['county']]
        state = fields[header_indices['state']]
        state_fips = fields[header_indices['state_fips']].zfill(2)
        county_fips = fields[header_indices['county_fips']].zfill(3)
        
        # Get population (employment_status_population_16_years_and_over)
        pop_idx = header_indices.get('population', 5)
        population = fields[pop_idx] if pop_idx < len(fields) else '0'
        
        full_fips = state_fips + county_fips
        
        return (full_fips, {
            'source': 'economic',
            'year': year,
            'county': county,
            'state': state,
            'state_fips': state_fips,
            'county_fips': county_fips,
            'population': population
        })
    except Exception as e:
        return None


def parse_voting_line(line):
    """Parse a line from voting CSV and extract key fields."""
    try:
        fields = line.split(',')
        if len(fields) < 10:
            return None
        
        # Skip header
        if fields[0] == 'year':
            return None
        
        year = fields[0]
        state = fields[1]
        county_name = fields[3]
        county_fips = fields[4].replace('.0', '').zfill(5)
        candidate = fields[6]
        party = fields[7]
        
        # Handle votes - may have quotes
        votes_str = fields[8].replace('"', '').strip()
        try:
            votes = int(float(votes_str)) if votes_str else 0
        except:
            votes = 0
        
        return (county_fips, {
            'source': 'voting',
            'year': year,
            'state': state,
            'county_name': county_name,
            'candidate': candidate,
            'party': party,
            'votes': votes
        })
    except Exception as e:
        return None


def merge_records(records):
    """Reduce function: merge economic and voting records for a county."""
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
    winner = max(voting_records, key=lambda x: x.get('votes', 0))
    
    # Handle population - may be int or string
    pop = economic_data.get('population', 0)
    try:
        pop = int(float(pop)) if pop else 0
    except:
        pop = 0
    
    return {
        'county': economic_data.get('county', ''),
        'state': economic_data.get('state', ''),
        'population': pop,
        'winning_party': winner.get('party', ''),
        'winning_votes': winner.get('votes', 0)
    }


def run_baseline_csv(economic_file, voting_file):
    """Run baseline single-threaded analysis using CSV files."""
    import pandas as pd
    
    start = time.time()
    
    # Load data
    econ = pd.read_csv(economic_file)
    pres = pd.read_csv(voting_file)
    
    # Filter to 2020
    pres_2020 = pres[pres['year'] == 2020].copy()
    
    # Create FIPS
    econ['full_fips'] = econ['state_fips'].astype(str).str.zfill(2) + econ['county_fips'].astype(str).str.zfill(3)
    pres_2020['full_fips'] = pres_2020['county_fips'].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    
    # Find winners
    winner_idx = pres_2020.groupby('full_fips')['candidatevotes'].idxmax()
    winners = pres_2020.loc[winner_idx][['full_fips', 'party']].copy()
    winners.columns = ['full_fips', 'winning_party']
    
    # Merge
    analysis = pd.merge(econ, winners, on='full_fips', how='inner')
    
    # Aggregate
    pop_col = [c for c in econ.columns if 'population_16' in c][0]
    analysis[pop_col] = pd.to_numeric(analysis[pop_col], errors='coerce')
    
    result = analysis.groupby('winning_party').agg({
        pop_col: ['mean', 'sum'],
        'full_fips': 'count'
    })
    
    elapsed = time.time() - start
    
    return elapsed, result


def run_baseline_parquet(economic_parquet, voting_parquet):
    """Run baseline single-threaded analysis using Parquet files."""
    import pandas as pd
    
    start = time.time()
    
    # Load Parquet data (faster than CSV)
    econ = pd.read_parquet(economic_parquet)
    pres = pd.read_parquet(voting_parquet)
    
    # Create FIPS
    econ['full_fips'] = econ['state_fips'].astype(str).str.zfill(2) + econ['county_fips'].astype(str).str.zfill(3)
    pres['full_fips'] = pres['county_fips'].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
    
    # Find winners
    winner_idx = pres.groupby('full_fips')['candidatevotes'].idxmax()
    winners = pres.loc[winner_idx][['full_fips', 'party']].copy()
    winners.columns = ['full_fips', 'winning_party']
    
    # Merge
    analysis = pd.merge(econ, winners, on='full_fips', how='inner')
    
    # Aggregate
    pop_col = [c for c in econ.columns if 'population_16' in c][0]
    analysis[pop_col] = pd.to_numeric(analysis[pop_col], errors='coerce')
    
    result = analysis.groupby('winning_party').agg({
        pop_col: ['mean', 'sum'],
        'full_fips': 'count'
    })
    
    elapsed = time.time() - start
    
    return elapsed, result


def run_mapreduce_parquet(sc, economic_parquet, voting_parquet):
    """
    Run MapReduce analysis using Spark Core RDD API with Parquet files.
    
    This uses pure RDD operations (map, filter, groupByKey, reduceByKey)
    NOT DataFrame or SparkSQL.
    """
    start = time.time()
    
    # Load Parquet files using pandas, then parallelize to RDD
    # This is the RDD-compatible way to read Parquet
    econ_pdf = pd.read_parquet(economic_parquet)
    voting_pdf = pd.read_parquet(voting_parquet)
    
    # Find population column - handle different naming conventions
    pop_col = None
    for col in econ_pdf.columns:
        if 'population_16' in col.lower() or 'population_16_years' in col.lower():
            pop_col = col
            break
    if pop_col is None:
        # Try alternative patterns
        for col in econ_pdf.columns:
            if 'employment_status_population' in col.lower():
                pop_col = col
                break
    if pop_col is None:
        pop_col = econ_pdf.columns[5]  # Fallback to 6th column
    
    # MAP PHASE: Convert economic DataFrame rows to (fips, record) pairs
    def map_economic_row(row):
        try:
            state_fips = str(int(row['state_fips'])).zfill(2)
            county_fips_val = str(int(row['county_fips'])).zfill(3)
            full_fips = state_fips + county_fips_val
            
            # Access pandas Series values directly (not with .get())
            pop_value = row[pop_col] if pop_col in row.index else 0
            try:
                population = int(float(pop_value)) if pd.notna(pop_value) else 0
            except:
                population = 0
            
            county_val = row['county'] if 'county' in row.index else ''
            state_val = row['state'] if 'state' in row.index else ''
            
            return (full_fips, {
                'source': 'economic',
                'county': county_val,
                'state': state_val,
                'population': population
            })
        except:
            return None
    
    # MAP PHASE: Convert voting DataFrame rows to (fips, record) pairs
    def map_voting_row(row):
        try:
            county_fips_val = str(row['county_fips']).replace('.0', '').zfill(5)
            
            votes = row['candidatevotes'] if 'candidatevotes' in row.index else 0
            try:
                votes = int(float(votes)) if pd.notna(votes) else 0
            except:
                votes = 0
            
            party_val = row['party'] if 'party' in row.index else ''
            
            return (county_fips_val, {
                'source': 'voting',
                'party': party_val,
                'votes': votes
            })
        except:
            return None
    
    # Create RDDs from DataFrames using map operations
    economic_records = [map_economic_row(row) for _, row in econ_pdf.iterrows()]
    voting_records = [map_voting_row(row) for _, row in voting_pdf.iterrows()]
    
    # Filter out None values
    economic_records = [r for r in economic_records if r is not None]
    voting_records = [r for r in voting_records if r is not None]
    
    # Parallelize to RDDs
    economic_rdd = sc.parallelize(economic_records)
    voting_rdd = sc.parallelize(voting_records)
    
    # SHUFFLE & REDUCE PHASE: Union and group by key (FIPS code)
    merged_rdd = economic_rdd.union(voting_rdd) \
        .groupByKey() \
        .mapValues(merge_records) \
        .filter(lambda x: x[1] is not None)
    
    # AGGREGATE: Count and sum by winning party using reduceByKey
    party_stats = merged_rdd \
        .map(lambda x: (x[1]['winning_party'], (x[1]['population'], 1))) \
        .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
        .map(lambda x: (x[0], {
            'total_population': x[1][0],
            'county_count': x[1][1],
            'avg_population': x[1][0] / x[1][1] if x[1][1] > 0 else 0
        })) \
        .collect()
    
    elapsed = time.time() - start
    
    return elapsed, party_stats


def run_mapreduce(sc, economic_file, voting_file):
    """Run MapReduce analysis using Spark RDD API."""
    start = time.time()
    
    # Read economic header to get column indices
    with open(economic_file, 'r') as f:
        header = f.readline().strip().split(',')
    
    header_indices = {
        'year': header.index('year') if 'year' in header else 0,
        'county': header.index('county') if 'county' in header else 1,
        'state': header.index('state') if 'state' in header else 2,
        'state_fips': header.index('state_fips') if 'state_fips' in header else 3,
        'county_fips': header.index('county_fips') if 'county_fips' in header else 4,
    }
    # Find population column
    for i, col in enumerate(header):
        if 'population_16' in col.lower():
            header_indices['population'] = i
            break
    
    # MAP PHASE: Load and parse economic data
    economic_rdd = sc.textFile(economic_file) \
        .map(lambda line: parse_economic_line(line, header_indices)) \
        .filter(lambda x: x is not None)
    
    # MAP PHASE: Load and parse voting data (filter to 2020)
    voting_rdd = sc.textFile(voting_file) \
        .map(parse_voting_line) \
        .filter(lambda x: x is not None) \
        .filter(lambda x: x[1]['year'] == '2020')
    
    # SHUFFLE & REDUCE PHASE: Union and group by key
    merged_rdd = economic_rdd.union(voting_rdd) \
        .groupByKey() \
        .mapValues(merge_records) \
        .filter(lambda x: x[1] is not None)
    
    # AGGREGATE: Count and sum by winning party
    party_stats = merged_rdd \
        .map(lambda x: (x[1]['winning_party'], (x[1]['population'], 1))) \
        .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
        .map(lambda x: (x[0], {
            'total_population': x[1][0],
            'county_count': x[1][1],
            'avg_population': x[1][0] / x[1][1] if x[1][1] > 0 else 0
        })) \
        .collect()
    
    elapsed = time.time() - start
    
    return elapsed, party_stats


def main():
    print("=" * 70)
    print("MapReduce Analysis: ACS Economic + Presidential Voting")
    print("Using Spark Core RDD API (NOT DataFrame/SQL)")
    print("=" * 70)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check for Parquet files first, fall back to CSV
    use_parquet = os.path.exists(ECONOMIC_PARQUET) and os.path.exists(VOTING_PARQUET)
    
    if use_parquet:
        print(f"\nUsing Parquet files:")
        print(f"  Economic: {ECONOMIC_PARQUET}")
        print(f"  Voting: {VOTING_PARQUET}")
    else:
        print(f"\nParquet files not found, using CSV:")
        print(f"  Economic: {ECONOMIC_CSV}")
        print(f"  Voting: {VOTING_CSV}")
    
    results = {}
    
    # Run baseline with CSV
    print("\n--- BASELINE: Pandas + CSV ---")
    if os.path.exists(ECONOMIC_CSV) and os.path.exists(VOTING_CSV):
        csv_time, csv_result = run_baseline_csv(ECONOMIC_CSV, VOTING_CSV)
        print(f"Execution time: {csv_time:.3f} seconds")
        print(f"Result:\n{csv_result}")
        results['Pandas CSV'] = csv_time
    
    # Run Spark Core RDD MapReduce with Parquet
    if use_parquet:
        for num_cores in [1, 2, 4]:
            print(f"\n--- SPARK RDD + Parquet (local[{num_cores}]) ---")
            
            conf = SparkConf() \
                .setAppName(f"ACS_Voting_RDD_{num_cores}") \
                .setMaster(f"local[{num_cores}]") \
                .set("spark.driver.memory", "4g") \
                .set("spark.ui.enabled", "false")
            
            sc = SparkContext(conf=conf)
            sc.setLogLevel("ERROR")
            
            try:
                mr_time, mr_result = run_mapreduce_parquet(sc, ECONOMIC_PARQUET, VOTING_PARQUET)
                print(f"Execution time: {mr_time:.3f} seconds")
                baseline = results.get('Pandas CSV', mr_time)
                print(f"Speedup vs Pandas CSV: {baseline/mr_time:.2f}x")
                print("Results by party:")
                for party, stats in mr_result:
                    print(f"  {party}: {stats['county_count']} counties, "
                          f"avg pop: {stats['avg_population']:,.0f}")
                
                results[f'Spark RDD local[{num_cores}]'] = mr_time
            except Exception as e:
                print(f"Error: {e}")
            finally:
                sc.stop()
    
    # Also run with CSV for comparison
    if os.path.exists(ECONOMIC_CSV) and os.path.exists(VOTING_CSV):
        print(f"\n--- SPARK RDD + CSV (local[4]) ---")
        
        conf = SparkConf() \
            .setAppName("ACS_Voting_RDD_CSV") \
            .setMaster("local[4]") \
            .set("spark.driver.memory", "4g") \
            .set("spark.ui.enabled", "false")
        
        sc = SparkContext(conf=conf)
        sc.setLogLevel("ERROR")
        
        try:
            mr_time, mr_result = run_mapreduce(sc, ECONOMIC_CSV, VOTING_CSV)
            print(f"Execution time: {mr_time:.3f} seconds")
            baseline = results.get('Pandas CSV', mr_time)
            print(f"Speedup vs Pandas CSV: {baseline/mr_time:.2f}x")
            print("Results by party:")
            for party, stats in mr_result:
                print(f"  {party}: {stats['county_count']} counties, "
                      f"avg pop: {stats['avg_population']:,.0f}")
            
            results['Spark RDD CSV local[4]'] = mr_time
        except Exception as e:
            print(f"Error: {e}")
        finally:
            sc.stop()
    
    # Run ALL YEARS merged dataset (larger ~84MB) to demonstrate scaling
    print("\n" + "=" * 70)
    print("LARGE DATASET TEST: All Years Merged (~84MB)")
    print("=" * 70)
    
    if os.path.exists(ECONOMIC_ALL_YEARS_CSV):
        # Baseline with Pandas
        print("\n--- BASELINE: Pandas + All Years CSV ---")
        import pandas as pd_local
        start = time.time()
        econ_all = pd_local.read_csv(ECONOMIC_ALL_YEARS_CSV, low_memory=False)
        pres = pd_local.read_csv(VOTING_CSV)
        
        # Create FIPS and merge with all election years
        econ_all['full_fips'] = econ_all['state_fips'].astype(str).str.zfill(2) + econ_all['county_fips'].astype(str).str.zfill(3)
        pres['full_fips'] = pres['county_fips'].astype(str).str.replace('.0', '', regex=False).str.zfill(5)
        
        # Find winners per county-year
        winner_idx = pres.groupby(['full_fips', 'year'])['candidatevotes'].idxmax()
        winners = pres.loc[winner_idx][['full_fips', 'year', 'party']].copy()
        winners.columns = ['full_fips', 'election_year', 'winning_party']
        
        # Merge and aggregate
        analysis = pd_local.merge(econ_all, winners, on='full_fips', how='inner')
        pop_col = [c for c in econ_all.columns if 'population_16' in c.lower()][0]
        analysis[pop_col] = pd_local.to_numeric(analysis[pop_col], errors='coerce')
        result = analysis.groupby('winning_party').agg({pop_col: ['mean', 'count']})
        
        pandas_all_time = time.time() - start
        print(f"Rows processed: {len(econ_all):,}")
        print(f"Execution time: {pandas_all_time:.3f} seconds")
        results['Pandas All Years'] = pandas_all_time
        
        # Spark RDD with all years
        for num_cores in [1, 4]:
            print(f"\n--- SPARK RDD + All Years (local[{num_cores}]) ---")
            
            conf = SparkConf() \
                .setAppName(f"ACS_Voting_AllYears_{num_cores}") \
                .setMaster(f"local[{num_cores}]") \
                .set("spark.driver.memory", "4g") \
                .set("spark.ui.enabled", "false")
            
            sc = SparkContext(conf=conf)
            sc.setLogLevel("ERROR")
            
            try:
                mr_time, mr_result = run_mapreduce(sc, ECONOMIC_ALL_YEARS_CSV, VOTING_CSV)
                print(f"Execution time: {mr_time:.3f} seconds")
                print(f"Speedup vs Pandas All Years: {pandas_all_time/mr_time:.2f}x")
                print("Results by party:")
                for party, stats in mr_result:
                    print(f"  {party}: {stats['county_count']} counties, "
                          f"avg pop: {stats['avg_population']:,.0f}")
                
                results[f'Spark RDD All Years local[{num_cores}]'] = mr_time
            except Exception as e:
                print(f"Error: {e}")
            finally:
                sc.stop()
    
    # Summary
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    
    baseline = results.get('Pandas CSV', 1.0)
    
    print(f"\n{'Configuration':<35} {'Time (s)':<12} {'Speedup':<10}")
    print("-" * 60)
    for config, t in results.items():
        speedup = baseline / t
        print(f"{config:<35} {t:<12.3f} {speedup:.2f}x")
    
    # Save results
    with open(os.path.join(OUTPUT_DIR, "performance_results.txt"), 'w') as f:
        f.write("MapReduce Performance Results\n")
        f.write("Using Spark Core RDD API\n")
        f.write("=" * 50 + "\n\n")
        for config, t in results.items():
            speedup = baseline / t
            f.write(f"{config}: {t:.3f}s (speedup: {speedup:.2f}x)\n")
    
    print(f"\nResults saved to {OUTPUT_DIR}/performance_results.txt")


if __name__ == "__main__":
    main()
