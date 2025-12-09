# Performance Testing - Execution Guide

This directory contains performance testing scripts and results for load, stress, and spike testing of pandas DataFrame operations.

## Prerequisites

- Python 3.11+
- Virtual environment activated
- Pandas installed (development version)
- Required packages: psutil, matplotlib

## Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install performance testing dependencies
pip install psutil matplotlib
```

## Performance Tests

### Test 1: Load Test (Sandeep Ramavath)
**Type:** Sustained concurrent load  
**Tool:** Custom Python load generator  
**Purpose:** Establish baseline performance under normal operating conditions

**Configuration:**
- 50 concurrent users
- 20 operations per user
- 10,000 rows per DataFrame
- Test duration: ~60 seconds target

### Test 2: Stress Test (Nithikesh Reddy)
**Type:** Progressive load increase to breaking point  
**Tool:** Custom Python stress test generator  
**Purpose:** Find system limits and performance degradation patterns

**Configuration:**
- Start: 5 concurrent users
- End: 40 concurrent users (or breaking point)
- Increment: 5 users per level
- Dataset size: 10,000 → 50,000 rows (scales with load)
- 10 operations per user

### Test 3: Spike Test (Mallikarjuna)
**Type:** Sudden traffic burst and recovery  
**Tool:** Custom Python spike simulator  
**Purpose:** Evaluate response to traffic spikes and recovery behavior

**Configuration:**
- Baseline: 3 users (8 seconds)
- Spike: 30 users (5 seconds) - 10x increase
- Recovery: 3 users (8 seconds)
- Dataset size: 20,000 rows

## Running Performance Tests

### Execute All Tests

```bash
# From repository root
cd /Volumes/T7Shield/SWEN777/SWEN_777_Pandas

# Activate environment
source venv/bin/activate

# Run Load Test
python pandas/tests/performance/test_load.py

# Run Stress Test
python pandas/tests/performance/test_stress.py

# Run Spike Test
python pandas/tests/performance/test_spike.py
```

### Execute Individual Tests

```bash
# Load Test only (Sandeep)
python pandas/tests/performance/test_load.py

# Stress Test only (Nithikesh)
python pandas/tests/performance/test_stress.py

# Spike Test only (Mallikarjuna)
python pandas/tests/performance/test_spike.py
```

## Expected Results

### Load Test
- **Duration:** ~6-10 seconds
- **Operations:** 1,000 (50 users × 20 ops)
- **Success Rate:** 100%
- **Throughput:** ~160-180 ops/sec
- **Avg Response:** ~0.03 seconds

### Stress Test
- **Duration:** ~15 minutes (varies based on breaking point)
- **Stress Levels:** 2-8 levels before breaking
- **Breaking Point:** ~10 concurrent users
- **Memory Growth:** Significant (GB range)

### Spike Test
- **Duration:** ~25-30 seconds (3 phases)
- **Phases:** Pre-spike, Spike, Post-spike
- **Response Degradation:** 20-30x during spike
- **Recovery:** Full recovery to baseline

## Output Files

All test results are saved in this directory:

### Load Test Results
- `load_test_results.json` - Complete metrics in JSON format
- `load_test_charts.png` - Performance visualizations

### Stress Test Results
- `stress_test_results.json` - Complete metrics in JSON format
- `stress_test_charts.png` - Degradation visualizations

### Spike Test Results
- `spike_test_results.json` - Complete metrics in JSON format
- `spike_test_charts.png` - Spike impact visualizations

## Interpreting Results

### JSON Results Structure

Each test generates a JSON file with:
- **configuration**: Test parameters (users, duration, dataset size)
- **execution**: Test execution details (duration, operations, success rate)
- **metrics**: Performance measurements (response time, throughput, CPU, memory)
- **findings**: Identified performance issues with severity levels

### Metrics Explained

**Response Time:**
- `mean`: Average response time across all operations
- `median` (p50): Middle value (50th percentile)
- `p95`: 95th percentile - 95% of requests faster than this
- `p99`: 99th percentile - worst 1% threshold
- `max`: Slowest operation

**Throughput:**
- Operations per second (ops/sec)

**Resource Usage:**
- **CPU**: Percentage utilization (0-100%)
- **Memory**: Usage in MB or GB

### Performance Findings

Results include categorized findings:
- **CRITICAL**: Severe issues requiring immediate action
- **HIGH**: Critical performance issues requiring immediate attention
- **MEDIUM**: Significant issues to address soon
- **LOW**: Minor optimizations

## Visualizations

Each test generates PNG charts showing:

**Load Test:**
- Response time distribution (histogram)
- Response time percentiles (bar chart)
- CPU usage over time (line chart)
- Memory usage over time (line chart)

**Stress Test:**
- Response time degradation (line chart)
- Throughput under stress (line chart)
- CPU utilization progression (line chart)
- Memory growth (line chart)
- Error rate progression (line chart)
- Normalized metrics comparison (multi-line chart)

**Spike Test:**
- Response time across phases (bar chart)
- Throughput across phases (bar chart)
- CPU usage across phases (grouped bar chart)
- Memory usage across phases (grouped bar chart)
- Error rate across phases (bar chart)
- Response time timeline (scatter plot)

## Troubleshooting

### Common Issues

**1. Memory Error During Stress Test**
```
MemoryError: Unable to allocate array
```
**Solution:** Reduce `DATASET_SIZE_MAX` or `MAX_USERS` in `test_stress.py`

**2. Test Takes Too Long**
```
Test exceeds expected duration
```
**Solution:** Reduce `OPERATIONS_PER_USER` or user counts in test scripts

**3. Charts Not Generated**
```
ModuleNotFoundError: No module named 'matplotlib'
```
**Solution:** `pip install matplotlib`

**4. CPU Pegged at 100%**
```
Normal behavior for pandas operations under load
```
**Observation:** This is expected - indicates CPU-bound operations

### Adjusting Test Parameters

Edit test configuration in the scripts:

**test_load.py:**
```python
NUM_USERS = 50  # Reduce for faster tests
OPERATIONS_PER_USER = 20  # Reduce for shorter duration
DATASET_SIZE = 10000  # Reduce for lower memory usage
```

**test_stress.py:**
```python
INITIAL_USERS = 5  # Starting concurrency
MAX_USERS = 40  # Reduce to finish faster
DATASET_SIZE_MAX = 50000  # Reduce for lower memory
```

**test_spike.py:**
```python
SPIKE_USERS = 30  # Reduce spike intensity
DATASET_SIZE = 20000  # Reduce for lower memory
```

## Detailed Results

Refer to `report.md` in this directory for:
- Comprehensive test analysis
- Performance findings with severity levels
- Recommendations for optimization
- Visual metrics and charts
- Group contributions

## Test Environment

Tests were executed on:
- **Platform:** macOS (Apple Silicon)
- **Python:** 3.11.14
- **Pandas:** Development branch (sandeep)
- **Memory:** System RAM
- **CPU:** Apple M-series processor
