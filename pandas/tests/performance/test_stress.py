#!/usr/bin/env python3
"""
Stress Test for pandas DataFrame Operations
Test Type: Stress Test
Owner: Nithikesh Reddy

This script pushes pandas operations beyond normal load limits to find
the breaking point and identify system behavior under extreme conditions.
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
import gc

# Stress Test Configuration
INITIAL_USERS = 5
MAX_USERS = 40  # Gradually increase to this level
USER_INCREMENT = 5  # Add users in steps
DATASET_SIZE_START = 10000  # Start with 10K rows
DATASET_SIZE_MAX = 50000  # Scale up to 50K rows
OPERATIONS_PER_USER = 10
RAMP_UP_INTERVAL = 2  # seconds between increments

# Metrics storage
metrics = {
    "user_levels": [],
    "response_times_by_level": {},
    "throughput_by_level": {},
    "cpu_usage_by_level": {},
    "memory_usage_by_level": {},
    "error_rates": {},
    "breaking_point": None,
    "timestamps": []
}


def create_large_dataframe(size):
    """Create a large DataFrame for stress testing"""
    return pd.DataFrame({
        'id': range(size),
        'value1': np.random.randn(size),
        'value2': np.random.randn(size),
        'value3': np.random.randn(size),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], size),
        'subcategory': np.random.choice([f'S{i}' for i in range(20)], size),
        'timestamp': pd.date_range('2020-01-01', periods=size, freq='1min'),
        'text': [f'text_{i}' for i in range(size)]
    })


def stress_operation_workflow(dataset_size):
    """
    Memory and CPU intensive pandas operations:
    1. Create large DataFrame
    2. Multiple filter operations
    3. Complex groupby with multiple aggregations
    4. Merge with another large DataFrame
    5. Pivot table creation
    6. Heavy sorting
    """
    start_time = time.time()
    
    try:
        # Step 1: Create large DataFrame
        df1 = create_large_dataframe(dataset_size)
        
        # Step 2: Multiple filters
        filtered = df1[
            (df1['value1'] > 0) & 
            (df1['value2'] < 1) & 
            (df1['category'].isin(['A', 'B', 'C']))
        ]
        
        # Step 3: Complex GroupBy with multiple aggregations
        grouped = filtered.groupby(['category', 'subcategory']).agg({
            'value1': ['mean', 'std', 'min', 'max'],
            'value2': ['sum', 'count'],
            'value3': ['median', 'var'],
            'id': 'count'
        })
        
        # Step 4: Create second DataFrame and merge
        df2 = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], dataset_size // 2),
            'extra_value': np.random.randn(dataset_size // 2)
        })
        merged = df1.merge(df2, on='category', how='inner')
        
        # Step 5: Pivot table
        pivot = filtered.pivot_table(
            values='value1',
            index='category',
            columns='subcategory',
            aggfunc=['mean', 'sum']
        )
        
        # Step 6: Heavy sorting
        sorted_df = merged.sort_values(['category', 'value1', 'value2'])
        
        response_time = time.time() - start_time
        
        # Force garbage collection
        del df1, df2, filtered, grouped, merged, pivot, sorted_df
        gc.collect()
        
        return response_time, True
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Error during stress operation: {e}")
        return response_time, False


def simulate_stressed_user(user_id, dataset_size):
    """Simulate a user under stress conditions"""
    user_metrics = []
    
    for op in range(OPERATIONS_PER_USER):
        response_time, success = stress_operation_workflow(dataset_size)
        user_metrics.append({
            'user_id': user_id,
            'operation': op,
            'response_time': response_time,
            'success': success,
            'dataset_size': dataset_size
        })
        
        # Minimal delay under stress
        time.sleep(0.05)
    
    return user_metrics


def monitor_system_resources():
    """Monitor CPU and memory usage"""
    process = psutil.Process()
    return {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'memory_percent': process.memory_percent(),
        'timestamp': time.time()
    }


def run_stress_level(num_users, dataset_size):
    """Run stress test at a specific user level"""
    print(f"\nTesting with {num_users} concurrent users, dataset size: {dataset_size:,} rows...")
    
    start_time = time.time()
    all_results = []
    errors = 0
    successes = 0
    resource_samples = []
    
    # Monitor initial resources
    initial_resources = monitor_system_resources()
    resource_samples.append(initial_resources)
    
    try:
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_stressed_user, i, dataset_size) 
                      for i in range(num_users)]
            
            for future in as_completed(futures):
                try:
                    user_results = future.result(timeout=120)  # 2 minute timeout
                    all_results.extend(user_results)
                    
                    # Monitor resources
                    resource_samples.append(monitor_system_resources())
                    
                except Exception as e:
                    print(f"  User thread failed: {e}")
                    errors += num_users * OPERATIONS_PER_USER
        
        # Process results
        response_times = []
        for result in all_results:
            response_times.append(result['response_time'])
            if result['success']:
                successes += 1
            else:
                errors += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate metrics
        total_ops = len(all_results)
        throughput = total_ops / duration if duration > 0 else 0
        error_rate = (errors / (successes + errors) * 100) if (successes + errors) > 0 else 100
        
        # Resource metrics
        cpu_values = [r['cpu_percent'] for r in resource_samples]
        memory_values = [r['memory_mb'] for r in resource_samples]
        
        level_metrics = {
            'num_users': num_users,
            'dataset_size': dataset_size,
            'duration': duration,
            'total_operations': total_ops,
            'successful': successes,
            'errors': errors,
            'error_rate': error_rate,
            'response_time': {
                'mean': np.mean(response_times) if response_times else 0,
                'median': np.median(response_times) if response_times else 0,
                'p95': np.percentile(response_times, 95) if response_times else 0,
                'max': np.max(response_times) if response_times else 0
            },
            'throughput': throughput,
            'cpu': {
                'avg': np.mean(cpu_values),
                'peak': np.max(cpu_values)
            },
            'memory': {
                'avg': np.mean(memory_values),
                'peak': np.max(memory_values)
            }
        }
        
        print(f"  Completed: {successes} successes, {errors} errors ({error_rate:.1f}% error rate)")
        print(f"  Avg response time: {level_metrics['response_time']['mean']:.4f}s")
        print(f"  Throughput: {throughput:.2f} ops/sec")
        print(f"  Peak CPU: {level_metrics['cpu']['peak']:.1f}%")
        print(f"  Peak Memory: {level_metrics['memory']['peak']:.1f} MB")
        
        # Determine if this is the breaking point
        is_broken = error_rate > 20 or level_metrics['response_time']['mean'] > 30
        
        return level_metrics, is_broken
        
    except Exception as e:
        print(f"  CRITICAL: Stress level {num_users} users failed: {e}")
        return None, True


def run_stress_test():
    """Execute the stress test with gradual load increase"""
    print(f"{'='*70}")
    print(f"STRESS TEST - Progressive Load Increase to Breaking Point")
    print(f"{'='*70}")
    print(f"Configuration:")
    print(f"  - Starting Users: {INITIAL_USERS}")
    print(f"  - Maximum Users: {MAX_USERS}")
    print(f"  - User Increment: {USER_INCREMENT}")
    print(f"  - Dataset Size Range: {DATASET_SIZE_START:,} to {DATASET_SIZE_MAX:,} rows")
    print(f"  - Operations per User: {OPERATIONS_PER_USER}")
    print(f"{'='*70}\n")
    
    test_start = time.time()
    all_level_metrics = []
    breaking_point = None
    
    # Gradually increase load
    current_users = INITIAL_USERS
    current_dataset_size = DATASET_SIZE_START
    
    while current_users <= MAX_USERS:
        # Increase dataset size proportionally
        size_ratio = (current_users - INITIAL_USERS) / (MAX_USERS - INITIAL_USERS)
        current_dataset_size = int(DATASET_SIZE_START + 
                                   (DATASET_SIZE_MAX - DATASET_SIZE_START) * size_ratio)
        
        level_metrics, is_broken = run_stress_level(current_users, current_dataset_size)
        
        if level_metrics:
            all_level_metrics.append(level_metrics)
            metrics['user_levels'].append(current_users)
        
        # Check if we've reached breaking point
        if is_broken:
            breaking_point = current_users
            print(f"\n⚠️  BREAKING POINT REACHED at {current_users} concurrent users!")
            break
        
        # Ramp up
        current_users += USER_INCREMENT
        time.sleep(RAMP_UP_INTERVAL)
    
    test_end = time.time()
    total_test_duration = test_end - test_start
    
    # Analyze results
    print(f"\n{'='*70}")
    print(f"STRESS TEST RESULTS")
    print(f"{'='*70}")
    print(f"\nTest Execution:")
    print(f"  - Total Test Duration: {total_test_duration:.2f} seconds")
    print(f"  - Stress Levels Tested: {len(all_level_metrics)}")
    print(f"  - Breaking Point: {breaking_point if breaking_point else 'Not reached'} concurrent users")
    
    if all_level_metrics:
        print(f"\nPerformance Degradation:")
        first_level = all_level_metrics[0]
        last_level = all_level_metrics[-1]
        
        response_degradation = (last_level['response_time']['mean'] / 
                               first_level['response_time']['mean'])
        throughput_degradation = (first_level['throughput'] / 
                                 last_level['throughput']) if last_level['throughput'] > 0 else 0
        
        print(f"  - Response Time: {first_level['response_time']['mean']:.4f}s → "
              f"{last_level['response_time']['mean']:.4f}s ({response_degradation:.2f}x slower)")
        print(f"  - Throughput: {first_level['throughput']:.2f} → "
              f"{last_level['throughput']:.2f} ops/sec ({throughput_degradation:.2f}x degradation)")
        print(f"  - Peak CPU: {last_level['cpu']['peak']:.1f}%")
        print(f"  - Peak Memory: {last_level['memory']['peak']:.1f} MB")
    
    # Identify performance findings
    print(f"\n{'='*70}")
    print(f"PERFORMANCE FINDINGS")
    print(f"{'='*70}")
    
    findings = []
    
    if breaking_point:
        findings.append({
            "finding": "System breaking point identified",
            "details": f"System fails at {breaking_point} concurrent users with dataset sizes up to {DATASET_SIZE_MAX:,} rows",
            "severity": "HIGH"
        })
    
    if all_level_metrics:
        # Check for performance cliff
        for i in range(1, len(all_level_metrics)):
            prev = all_level_metrics[i-1]
            curr = all_level_metrics[i]
            
            response_increase = curr['response_time']['mean'] / prev['response_time']['mean']
            if response_increase > 2.0:
                findings.append({
                    "finding": "Performance cliff detected",
                    "details": f"Response time jumped {response_increase:.2f}x when increasing from {prev['num_users']} to {curr['num_users']} users",
                    "severity": "HIGH"
                })
                break
        
        # Check memory growth
        memory_growth = last_level['memory']['peak'] - first_level['memory']['avg']
        if memory_growth > 500:  # More than 500 MB growth
            findings.append({
                "finding": "Excessive memory growth under stress",
                "details": f"Memory usage increased by {memory_growth:.2f} MB from baseline to peak load",
                "severity": "HIGH"
            })
        
        # Check CPU saturation
        if last_level['cpu']['peak'] > 90:
            findings.append({
                "finding": "CPU saturation reached",
                "details": f"CPU utilization peaked at {last_level['cpu']['peak']:.1f}% under maximum stress",
                "severity": "MEDIUM"
            })
        
        # Check error rate progression
        high_error_levels = [m for m in all_level_metrics if m['error_rate'] > 5]
        if high_error_levels:
            findings.append({
                "finding": "Error rate increases under stress",
                "details": f"Error rate exceeded 5% at {len(high_error_levels)} stress levels, max: {max(m['error_rate'] for m in high_error_levels):.1f}%",
                "severity": "MEDIUM"
            })
    
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['finding']} [{finding['severity']}]")
        print(f"   {finding['details']}")
    
    if not findings:
        print("\n✓ System handled all stress levels successfully")
        print("  No breaking point found within test parameters")
    
    # Save results
    results_data = {
        "test_type": "Stress Test",
        "owner": "Nithikesh Reddy",
        "configuration": {
            "initial_users": INITIAL_USERS,
            "max_users": MAX_USERS,
            "user_increment": USER_INCREMENT,
            "dataset_size_range": [DATASET_SIZE_START, DATASET_SIZE_MAX],
            "operations_per_user": OPERATIONS_PER_USER
        },
        "execution": {
            "total_duration": total_test_duration,
            "stress_levels_tested": len(all_level_metrics),
            "breaking_point": breaking_point
        },
        "level_metrics": all_level_metrics,
        "findings": findings,
        "timestamp": datetime.now().isoformat()
    }
    
    output_dir = "courseProjectDocs/performance-testing"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/stress_test_results.json", 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}/stress_test_results.json")
    print(f"{'='*70}\n")
    
    # Generate visualization
    if all_level_metrics:
        generate_charts(all_level_metrics, output_dir)
    
    return results_data


def generate_charts(all_metrics, output_dir):
    """Generate stress test performance charts"""
    print("Generating stress test charts...")
    
    user_levels = [m['num_users'] for m in all_metrics]
    response_times = [m['response_time']['mean'] for m in all_metrics]
    throughputs = [m['throughput'] for m in all_metrics]
    cpu_peaks = [m['cpu']['peak'] for m in all_metrics]
    memory_peaks = [m['memory']['peak'] for m in all_metrics]
    error_rates = [m['error_rate'] for m in all_metrics]
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Stress Test Performance Degradation', fontsize=16, fontweight='bold')
    
    # Chart 1: Response Time vs Users
    axes[0, 0].plot(user_levels, response_times, marker='o', linewidth=2, color='red')
    axes[0, 0].set_xlabel('Concurrent Users')
    axes[0, 0].set_ylabel('Avg Response Time (seconds)')
    axes[0, 0].set_title('Response Time Degradation')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Chart 2: Throughput vs Users
    axes[0, 1].plot(user_levels, throughputs, marker='s', linewidth=2, color='blue')
    axes[0, 1].set_xlabel('Concurrent Users')
    axes[0, 1].set_ylabel('Throughput (ops/sec)')
    axes[0, 1].set_title('Throughput Under Stress')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Chart 3: CPU Usage vs Users
    axes[0, 2].plot(user_levels, cpu_peaks, marker='^', linewidth=2, color='green')
    axes[0, 2].axhline(80, color='orange', linestyle='--', label='Warning (80%)')
    axes[0, 2].axhline(90, color='red', linestyle='--', label='Critical (90%)')
    axes[0, 2].set_xlabel('Concurrent Users')
    axes[0, 2].set_ylabel('Peak CPU Usage (%)')
    axes[0, 2].set_title('CPU Utilization Under Stress')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)
    
    # Chart 4: Memory Usage vs Users
    axes[1, 0].plot(user_levels, memory_peaks, marker='D', linewidth=2, color='purple')
    axes[1, 0].set_xlabel('Concurrent Users')
    axes[1, 0].set_ylabel('Peak Memory (MB)')
    axes[1, 0].set_title('Memory Growth Under Stress')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Chart 5: Error Rate vs Users
    axes[1, 1].plot(user_levels, error_rates, marker='x', linewidth=2, color='darkred')
    axes[1, 1].axhline(5, color='orange', linestyle='--', label='Warning (5%)')
    axes[1, 1].axhline(20, color='red', linestyle='--', label='Critical (20%)')
    axes[1, 1].set_xlabel('Concurrent Users')
    axes[1, 1].set_ylabel('Error Rate (%)')
    axes[1, 1].set_title('Error Rate Progression')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # Chart 6: Multi-metric comparison (normalized)
    norm_response = np.array(response_times) / response_times[0]
    norm_throughput = np.array(throughputs) / throughputs[0]
    norm_cpu = np.array(cpu_peaks) / cpu_peaks[0]
    
    axes[1, 2].plot(user_levels, norm_response, marker='o', label='Response Time', linewidth=2)
    axes[1, 2].plot(user_levels, norm_throughput, marker='s', label='Throughput', linewidth=2)
    axes[1, 2].plot(user_levels, norm_cpu, marker='^', label='CPU Usage', linewidth=2)
    axes[1, 2].axhline(1.0, color='black', linestyle='--', alpha=0.5)
    axes[1, 2].set_xlabel('Concurrent Users')
    axes[1, 2].set_ylabel('Normalized Metrics (baseline=1.0)')
    axes[1, 2].set_title('Normalized Performance Metrics')
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_path = f"{output_dir}/stress_test_charts.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"Charts saved to: {chart_path}\n")
    plt.close()


if __name__ == "__main__":
    run_stress_test()
