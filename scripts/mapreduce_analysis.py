#!/usr/bin/env python3
"""
MapReduce Analysis using PySpark Core RDD API

This script implements the MapReduce solution for merging ACS economic data
with presidential voting data and analyzing voting patterns by economic indicators.

Uses Spark Core RDD API (NOT DataFrame/SQL) as required.
"""

from pyspark import SparkContext, SparkConf
import time
import os

# Configuration
ECONOMIC_FILE = "./data/acs_merged/economic/economic_2020.csv"
VOTING_FILE = "./data/countypres_2000-2024.csv"
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
    winner = max(voting_records, key=lambda x: x['votes'])
    
    try:
        pop = int(float(economic_data['population'])) if economic_data['population'] else 0
    except:
        pop = 0
    
    return {
        'county_fips': economic_data['state_fips'] + economic_data['county_fips'],
        'county': economic_data['county'],
        'state': economic_data['state'],
        'population': pop,
        'winning_party': winner['party'],
        'winning_candidate': winner['candidate'],
        'winning_votes': winner['votes']
    }


def run_baseline(economic_file, voting_file):
    """Run baseline single-threaded analysis for comparison."""
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
    print("=" * 70)
    
    # Check files exist
    if not os.path.exists(ECONOMIC_FILE):
        print(f"Error: {ECONOMIC_FILE} not found")
        return
    if not os.path.exists(VOTING_FILE):
        print(f"Error: {VOTING_FILE} not found")
        return
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Run baseline
    print("\n--- BASELINE (Single-threaded Pandas) ---")
    baseline_time, baseline_result = run_baseline(ECONOMIC_FILE, VOTING_FILE)
    print(f"Execution time: {baseline_time:.3f} seconds")
    print(f"Result:\n{baseline_result}")
    
    # Run MapReduce with different parallelism levels
    results = []
    
    for num_cores in [1, 2, 4]:
        print(f"\n--- SPARK RDD (local[{num_cores}]) ---")
        
        conf = SparkConf() \
            .setAppName(f"ACS_Voting_MapReduce_{num_cores}") \
            .setMaster(f"local[{num_cores}]") \
            .set("spark.driver.memory", "4g") \
            .set("spark.ui.enabled", "false") \
            .set("spark.sql.shuffle.partitions", str(num_cores * 2))
        
        sc = SparkContext(conf=conf)
        sc.setLogLevel("ERROR")
        
        try:
            mr_time, mr_result = run_mapreduce(sc, ECONOMIC_FILE, VOTING_FILE)
            print(f"Execution time: {mr_time:.3f} seconds")
            print(f"Speedup vs baseline: {baseline_time/mr_time:.2f}x")
            print("Results by party:")
            for party, stats in mr_result:
                print(f"  {party}: {stats['county_count']} counties, "
                      f"avg pop: {stats['avg_population']:,.0f}")
            
            results.append({
                'cores': num_cores,
                'time': mr_time,
                'speedup': baseline_time / mr_time,
                'result': mr_result
            })
        finally:
            sc.stop()
    
    # Summary
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"\n{'Configuration':<25} {'Time (s)':<12} {'Speedup':<10}")
    print("-" * 50)
    print(f"{'Baseline (Pandas)':<25} {baseline_time:<12.3f} {'1.00x':<10}")
    for r in results:
        print(f"{'Spark local[' + str(r['cores']) + ']':<25} {r['time']:<12.3f} {r['speedup']:.2f}x")
    
    # Save results
    with open(os.path.join(OUTPUT_DIR, "performance_results.txt"), 'w') as f:
        f.write("MapReduce Performance Results\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Baseline (Pandas): {baseline_time:.3f}s\n\n")
        for r in results:
            f.write(f"Spark local[{r['cores']}]: {r['time']:.3f}s (speedup: {r['speedup']:.2f}x)\n")
        f.write("\nResults:\n")
        for r in results:
            if r['cores'] == 4:
                for party, stats in r['result']:
                    f.write(f"  {party}: {stats['county_count']} counties, "
                           f"avg pop: {stats['avg_population']:,.0f}\n")
    
    print(f"\nResults saved to {OUTPUT_DIR}/performance_results.txt")


if __name__ == "__main__":
    main()
