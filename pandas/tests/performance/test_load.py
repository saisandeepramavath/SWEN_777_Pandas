#!/usr/bin/env python3
"""
Load Test for pandas DataFrame Operations
Test Type: Load Test
Owner: Sandeep Ramavath

This script simulates a sustained load on pandas operations to establish
baseline performance metrics under normal operating conditions.
"""

import pandas as pd
import numpy as np
import time
import psutil
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import os

# Test Configuration
NUM_USERS = 50  # Simulated concurrent users
DURATION_SECONDS = 60  # 1 minute sustained load
OPERATIONS_PER_USER = 20  # Each user performs 20 operations
DATASET_SIZE = 10000  # Rows per DataFrame

# Metrics storage
metrics = {
    "response_times": [],
    "throughput": [],
    "cpu_usage": [],
    "memory_usage": [],
    "timestamps": [],
    "errors": 0,
    "successful_operations": 0
}


def create_sample_dataframe(size=DATASET_SIZE):
    """Create a sample DataFrame for testing"""
    return pd.DataFrame({
        'id': range(size),
        'value': np.random.randn(size),
        'category': np.random.choice(['A', 'B', 'C', 'D'], size),
        'timestamp': pd.date_range('2020-01-01', periods=size, freq='1min')
    })


def pandas_operation_workflow():
    """
    Simulates a typical pandas workflow:
    1. Create DataFrame
    2. Filter data
    3. GroupBy aggregation
    4. Sort results
    5. Export to CSV
    """
    start_time = time.time()
    
    try:
        # Step 1: Create DataFrame
        df = create_sample_dataframe()
        
        # Step 2: Filter data
        filtered = df[df['value'] > 0]
        
        # Step 3: GroupBy aggregation
        grouped = filtered.groupby('category').agg({
            'value': ['mean', 'sum', 'count'],
            'id': 'count'
        })
        
        # Step 4: Sort by value
        sorted_df = filtered.sort_values('value', ascending=False)
        
        # Step 5: Export to CSV (in-memory using StringIO)
        from io import StringIO
        csv_buffer = StringIO()
        sorted_df.head(100).to_csv(csv_buffer, index=False)
        
        response_time = time.time() - start_time
        return response_time, True
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Error during operation: {e}")
        return response_time, False


def simulate_user(user_id):
    """Simulate a single user performing multiple operations"""
    user_metrics = []
    
    for op in range(OPERATIONS_PER_USER):
        response_time, success = pandas_operation_workflow()
        user_metrics.append({
            'user_id': user_id,
            'operation': op,
            'response_time': response_time,
            'success': success,
            'timestamp': time.time()
        })
        
        # Small delay between operations (0.1-0.3 seconds)
        time.sleep(np.random.uniform(0.1, 0.3))
    
    return user_metrics


def monitor_system_resources():
    """Monitor CPU and memory usage"""
    process = psutil.Process()
    return {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'timestamp': time.time()
    }


def run_load_test():
    """Execute the load test with concurrent users"""
    print(f"{'='*70}")
    print(f"LOAD TEST - Sustained Load Simulation")
    print(f"{'='*70}")
    print(f"Configuration:")
    print(f"  - Concurrent Users: {NUM_USERS}")
    print(f"  - Test Duration: {DURATION_SECONDS} seconds")
    print(f"  - Operations per User: {OPERATIONS_PER_USER}")
    print(f"  - Dataset Size: {DATASET_SIZE:,} rows")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    all_results = []
    
    # Start resource monitoring in background
    print("Starting load test...")
    
    # Execute concurrent user operations
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        # Submit all user tasks
        futures = [executor.submit(simulate_user, i) for i in range(NUM_USERS)]
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(futures):
            user_results = future.result()
            all_results.extend(user_results)
            completed += 1
            
            # Monitor resources periodically
            if completed % 5 == 0:
                resource_metrics = monitor_system_resources()
                metrics['cpu_usage'].append(resource_metrics['cpu_percent'])
                metrics['memory_usage'].append(resource_metrics['memory_mb'])
                metrics['timestamps'].append(resource_metrics['timestamp'] - start_time)
            
            # Progress indicator
            progress = (completed / NUM_USERS) * 100
            print(f"Progress: {completed}/{NUM_USERS} users completed ({progress:.1f}%)")
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Process results
    for result in all_results:
        metrics['response_times'].append(result['response_time'])
        if result['success']:
            metrics['successful_operations'] += 1
        else:
            metrics['errors'] += 1
    
    # Calculate throughput (operations per second)
    total_operations = len(all_results)
    throughput = total_operations / total_duration
    
    # Calculate statistics
    response_times = np.array(metrics['response_times'])
    
    print(f"\n{'='*70}")
    print(f"LOAD TEST RESULTS")
    print(f"{'='*70}")
    print(f"\nTest Execution:")
    print(f"  - Total Duration: {total_duration:.2f} seconds")
    print(f"  - Total Operations: {total_operations:,}")
    print(f"  - Successful Operations: {metrics['successful_operations']:,}")
    print(f"  - Failed Operations: {metrics['errors']}")
    print(f"  - Success Rate: {(metrics['successful_operations']/total_operations)*100:.2f}%")
    
    print(f"\nResponse Time Metrics:")
    print(f"  - Mean: {response_times.mean():.4f} seconds")
    print(f"  - Median (p50): {np.percentile(response_times, 50):.4f} seconds")
    print(f"  - p95: {np.percentile(response_times, 95):.4f} seconds")
    print(f"  - p99: {np.percentile(response_times, 99):.4f} seconds")
    print(f"  - Min: {response_times.min():.4f} seconds")
    print(f"  - Max: {response_times.max():.4f} seconds")
    
    print(f"\nThroughput:")
    print(f"  - Average: {throughput:.2f} operations/second")
    
    print(f"\nResource Usage:")
    print(f"  - Average CPU: {np.mean(metrics['cpu_usage']):.2f}%")
    print(f"  - Peak CPU: {np.max(metrics['cpu_usage']) if metrics['cpu_usage'] else 0:.2f}%")
    print(f"  - Average Memory: {np.mean(metrics['memory_usage']):.2f} MB")
    print(f"  - Peak Memory: {np.max(metrics['memory_usage']) if metrics['memory_usage'] else 0:.2f} MB")
    
    # Identify performance findings
    print(f"\n{'='*70}")
    print(f"PERFORMANCE FINDINGS")
    print(f"{'='*70}")
    
    findings = []
    
    # Finding 1: Response time analysis
    if response_times.mean() > 0.5:
        findings.append({
            "finding": "High average response time",
            "details": f"Mean response time of {response_times.mean():.4f}s exceeds 0.5s threshold",
            "severity": "MEDIUM"
        })
    
    # Finding 2: p95/p99 tail latency
    p95 = np.percentile(response_times, 95)
    p99 = np.percentile(response_times, 99)
    if p99 > p95 * 2:
        findings.append({
            "finding": "Significant tail latency",
            "details": f"p99 ({p99:.4f}s) is {(p99/p95):.2f}x higher than p95 ({p95:.4f}s)",
            "severity": "MEDIUM"
        })
    
    # Finding 3: CPU utilization
    avg_cpu = np.mean(metrics['cpu_usage']) if metrics['cpu_usage'] else 0
    if avg_cpu > 70:
        findings.append({
            "finding": "High CPU utilization under load",
            "details": f"Average CPU usage of {avg_cpu:.2f}% indicates potential CPU bottleneck",
            "severity": "HIGH"
        })
    
    # Finding 4: Memory growth
    if len(metrics['memory_usage']) > 1:
        memory_growth = metrics['memory_usage'][-1] - metrics['memory_usage'][0]
        if memory_growth > 100:  # More than 100 MB growth
            findings.append({
                "finding": "Memory usage growth detected",
                "details": f"Memory grew by {memory_growth:.2f} MB during test",
                "severity": "MEDIUM"
            })
    
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['finding']} [{finding['severity']}]")
        print(f"   {finding['details']}")
    
    if not findings:
        print("\n✓ No performance issues detected under sustained load")
        print("  System performed within acceptable thresholds")
    
    # Save results to JSON
    results_data = {
        "test_type": "Load Test",
        "owner": "Sandeep Ramavath",
        "configuration": {
            "concurrent_users": NUM_USERS,
            "duration_seconds": DURATION_SECONDS,
            "operations_per_user": OPERATIONS_PER_USER,
            "dataset_size": DATASET_SIZE
        },
        "execution": {
            "total_duration": total_duration,
            "total_operations": total_operations,
            "successful_operations": metrics['successful_operations'],
            "failed_operations": metrics['errors'],
            "success_rate": (metrics['successful_operations']/total_operations)*100
        },
        "metrics": {
            "response_time": {
                "mean": float(response_times.mean()),
                "median": float(np.percentile(response_times, 50)),
                "p95": float(np.percentile(response_times, 95)),
                "p99": float(np.percentile(response_times, 99)),
                "min": float(response_times.min()),
                "max": float(response_times.max())
            },
            "throughput": throughput,
            "cpu_usage": {
                "average": float(np.mean(metrics['cpu_usage'])) if metrics['cpu_usage'] else 0,
                "peak": float(np.max(metrics['cpu_usage'])) if metrics['cpu_usage'] else 0
            },
            "memory_usage_mb": {
                "average": float(np.mean(metrics['memory_usage'])) if metrics['memory_usage'] else 0,
                "peak": float(np.max(metrics['memory_usage'])) if metrics['memory_usage'] else 0
            }
        },
        "findings": findings,
        "timestamp": datetime.now().isoformat()
    }
    
    output_dir = "courseProjectDocs/performance-testing"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/load_test_results.json", 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}/load_test_results.json")
    print(f"{'='*70}\n")
    
    # Generate visualization
    generate_charts(metrics, total_duration, output_dir)
    
    return results_data


def generate_charts(metrics, duration, output_dir):
    """Generate performance charts"""
    print("Generating performance charts...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Load Test Performance Metrics', fontsize=16, fontweight='bold')
    
    # Chart 1: Response Time Distribution
    axes[0, 0].hist(metrics['response_times'], bins=50, color='skyblue', edgecolor='black')
    axes[0, 0].axvline(np.mean(metrics['response_times']), color='red', 
                       linestyle='dashed', linewidth=2, label=f'Mean: {np.mean(metrics["response_times"]):.4f}s')
    axes[0, 0].set_xlabel('Response Time (seconds)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Response Time Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Chart 2: Response Time Percentiles
    percentiles = [50, 75, 90, 95, 99]
    percentile_values = [np.percentile(metrics['response_times'], p) for p in percentiles]
    axes[0, 1].bar([f'p{p}' for p in percentiles], percentile_values, color='coral', edgecolor='black')
    axes[0, 1].set_xlabel('Percentile')
    axes[0, 1].set_ylabel('Response Time (seconds)')
    axes[0, 1].set_title('Response Time Percentiles')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(percentile_values):
        axes[0, 1].text(i, v + 0.01, f'{v:.4f}s', ha='center', va='bottom', fontweight='bold')
    
    # Chart 3: CPU Usage Over Time
    if metrics['timestamps'] and metrics['cpu_usage']:
        axes[1, 0].plot(metrics['timestamps'], metrics['cpu_usage'], 
                       color='green', marker='o', linewidth=2)
        axes[1, 0].axhline(np.mean(metrics['cpu_usage']), color='red', 
                          linestyle='dashed', linewidth=2, label=f'Avg: {np.mean(metrics["cpu_usage"]):.2f}%')
        axes[1, 0].set_xlabel('Time (seconds)')
        axes[1, 0].set_ylabel('CPU Usage (%)')
        axes[1, 0].set_title('CPU Usage Over Time')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
    
    # Chart 4: Memory Usage Over Time
    if metrics['timestamps'] and metrics['memory_usage']:
        axes[1, 1].plot(metrics['timestamps'], metrics['memory_usage'], 
                       color='purple', marker='s', linewidth=2)
        axes[1, 1].axhline(np.mean(metrics['memory_usage']), color='red', 
                          linestyle='dashed', linewidth=2, label=f'Avg: {np.mean(metrics["memory_usage"]):.2f} MB')
        axes[1, 1].set_xlabel('Time (seconds)')
        axes[1, 1].set_ylabel('Memory Usage (MB)')
        axes[1, 1].set_title('Memory Usage Over Time')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_path = f"{output_dir}/load_test_charts.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"Charts saved to: {chart_path}\n")
    plt.close()


if __name__ == "__main__":
    run_load_test()
