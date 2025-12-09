#!/usr/bin/env python3
"""
Spike Test for pandas DataFrame Operations
Test Type: Spike Test
Owner: Mallikarjuna

This script simulates sudden, extreme spikes in load to test pandas'
ability to handle unexpected traffic bursts and recovery behavior.
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

# Spike Test Configuration
BASELINE_USERS = 3  # Normal load
SPIKE_USERS = 30  # Sudden spike
SPIKE_DURATION = 5  # seconds at peak
PRE_SPIKE_DURATION = 8  # seconds before spike
POST_SPIKE_DURATION = 8  # seconds after spike (recovery)
DATASET_SIZE = 20000  # Dataset for spike
OPERATIONS_PER_USER = 5

# Metrics storage
metrics = {
    "phases": [],  # pre-spike, spike, post-spike
    "response_times": [],
    "timestamps": [],
    "cpu_usage": [],
    "memory_usage": [],
    "error_counts": [],
    "throughput": [],
    "active_users": []
}


def create_spike_dataframe(size=DATASET_SIZE):
    """Create DataFrame for spike testing"""
    return pd.DataFrame({
        'id': range(size),
        'value': np.random.randn(size),
        'category': np.random.choice(['A', 'B', 'C', 'D'], size),
        'subcategory': np.random.choice([f'Sub{i}' for i in range(10)], size),
        'timestamp': pd.date_range('2020-01-01', periods=size, freq='1min'),
        'text_field': [f'data_{i}_{j}' for i, j in zip(range(size), np.random.randint(0, 1000, size))]
    })


def spike_operation_workflow():
    """
    Intensive pandas operations during spike:
    1. Create large DataFrame
    2. Complex filtering
    3. Multi-level groupby
    4. Join with another DataFrame
    5. Statistical computations
    """
    start_time = time.time()
    
    try:
        # Step 1: Create large DataFrame
        df1 = create_spike_dataframe()
        
        # Step 2: Complex filtering
        filtered = df1[
            (df1['value'] > -1) & 
            (df1['value'] < 1) & 
            (df1['category'].isin(['A', 'B']))
        ]
        
        # Step 3: Multi-level groupby with aggregations
        grouped = filtered.groupby(['category', 'subcategory']).agg({
            'value': ['mean', 'std', 'min', 'max', 'count'],
            'id': ['first', 'last', 'count']
        })
        
        # Step 4: Create and join another DataFrame
        df2 = create_spike_dataframe(size=DATASET_SIZE // 2)
        merged = df1.merge(df2[['id', 'value']], on='id', how='left', suffixes=('_1', '_2'))
        
        # Step 5: Statistical computations
        correlation = merged[['value_1', 'value_2']].corr()
        rolling = merged['value_1'].rolling(window=100).mean()
        
        # Step 6: Sorting large dataset
        sorted_df = merged.sort_values(['category', 'value_1'])
        
        response_time = time.time() - start_time
        
        # Cleanup
        del df1, df2, filtered, grouped, merged, correlation, rolling, sorted_df
        gc.collect()
        
        return response_time, True
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Error in spike operation: {e}")
        return response_time, False


def simulate_spike_user(user_id, phase):
    """Simulate a user during spike test"""
    user_metrics = []
    
    for op in range(OPERATIONS_PER_USER):
        response_time, success = spike_operation_workflow()
        user_metrics.append({
            'user_id': user_id,
            'phase': phase,
            'operation': op,
            'response_time': response_time,
            'success': success,
            'timestamp': time.time()
        })
        
        # Minimal delay during spike
        time.sleep(0.05 if phase == 'spike' else 0.2)
    
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


def run_phase(phase_name, num_users, duration):
    """Run a single phase of the spike test"""
    print(f"\n{'='*60}")
    print(f"Phase: {phase_name.upper()}")
    print(f"Users: {num_users} | Duration: {duration}s")
    print(f"{'='*60}")
    
    phase_start = time.time()
    all_results = []
    errors = 0
    
    # Calculate how many user batches we need
    ops_per_user_in_phase = int((duration / OPERATIONS_PER_USER) * num_users)
    
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        # Submit user tasks
        futures = [executor.submit(simulate_spike_user, i, phase_name) 
                  for i in range(num_users)]
        
        # Monitor resources during phase
        resource_samples = []
        while time.time() - phase_start < duration:
            resource_samples.append(monitor_system_resources())
            time.sleep(0.5)
        
        # Collect results
        for future in as_completed(futures, timeout=duration + 10):
            try:
                user_results = future.result(timeout=5)
                all_results.extend(user_results)
            except Exception as e:
                print(f"  User failed: {e}")
                errors += OPERATIONS_PER_USER
    
    phase_end = time.time()
    phase_duration = phase_end - phase_start
    
    # Process phase results
    successful_ops = sum(1 for r in all_results if r['success'])
    failed_ops = len(all_results) - successful_ops + errors
    
    response_times = [r['response_time'] for r in all_results]
    throughput = len(all_results) / phase_duration if phase_duration > 0 else 0
    
    phase_metrics = {
        'phase': phase_name,
        'duration': phase_duration,
        'num_users': num_users,
        'total_operations': len(all_results),
        'successful': successful_ops,
        'failed': failed_ops,
        'error_rate': (failed_ops / (successful_ops + failed_ops) * 100) if (successful_ops + failed_ops) > 0 else 0,
        'response_time': {
            'mean': np.mean(response_times) if response_times else 0,
            'median': np.median(response_times) if response_times else 0,
            'p95': np.percentile(response_times, 95) if response_times else 0,
            'p99': np.percentile(response_times, 99) if response_times else 0,
            'max': np.max(response_times) if response_times else 0
        },
        'throughput': throughput,
        'cpu': {
            'avg': np.mean([r['cpu_percent'] for r in resource_samples]) if resource_samples else 0,
            'peak': np.max([r['cpu_percent'] for r in resource_samples]) if resource_samples else 0
        },
        'memory': {
            'avg': np.mean([r['memory_mb'] for r in resource_samples]) if resource_samples else 0,
            'peak': np.max([r['memory_mb'] for r in resource_samples]) if resource_samples else 0
        },
        'resource_samples': resource_samples,
        'response_times': response_times
    }
    
    print(f"\nPhase Results:")
    print(f"  Operations: {len(all_results)} ({successful_ops} success, {failed_ops} failed)")
    print(f"  Avg Response: {phase_metrics['response_time']['mean']:.4f}s")
    print(f"  p95 Response: {phase_metrics['response_time']['p95']:.4f}s")
    print(f"  Throughput: {throughput:.2f} ops/sec")
    print(f"  Peak CPU: {phase_metrics['cpu']['peak']:.1f}%")
    print(f"  Peak Memory: {phase_metrics['memory']['peak']:.1f} MB")
    print(f"  Error Rate: {phase_metrics['error_rate']:.2f}%")
    
    return phase_metrics


def run_spike_test():
    """Execute the complete spike test"""
    print(f"{'='*70}")
    print(f"SPIKE TEST - Sudden Load Burst and Recovery Analysis")
    print(f"{'='*70}")
    print(f"Configuration:")
    print(f"  - Baseline Load: {BASELINE_USERS} users")
    print(f"  - Spike Load: {SPIKE_USERS} users")
    print(f"  - Dataset Size: {DATASET_SIZE:,} rows")
    print(f"  - Pre-Spike Duration: {PRE_SPIKE_DURATION}s")
    print(f"  - Spike Duration: {SPIKE_DURATION}s")
    print(f"  - Post-Spike (Recovery) Duration: {POST_SPIKE_DURATION}s")
    print(f"{'='*70}\n")
    
    test_start = time.time()
    
    # Phase 1: Pre-Spike (Baseline)
    print("Starting Phase 1: PRE-SPIKE (Baseline)...")
    pre_spike_metrics = run_phase('pre-spike', BASELINE_USERS, PRE_SPIKE_DURATION)
    
    # Phase 2: Spike
    print("\nStarting Phase 2: SPIKE (Sudden Load Burst)...")
    spike_metrics = run_phase('spike', SPIKE_USERS, SPIKE_DURATION)
    
    # Phase 3: Post-Spike (Recovery)
    print("\nStarting Phase 3: POST-SPIKE (Recovery)...")
    post_spike_metrics = run_phase('post-spike', BASELINE_USERS, POST_SPIKE_DURATION)
    
    test_end = time.time()
    total_duration = test_end - test_start
    
    # Analyze spike impact and recovery
    print(f"\n{'='*70}")
    print(f"SPIKE TEST ANALYSIS")
    print(f"{'='*70}")
    
    print(f"\nTest Execution:")
    print(f"  - Total Test Duration: {total_duration:.2f} seconds")
    
    print(f"\nSpike Impact Analysis:")
    spike_response_increase = (spike_metrics['response_time']['mean'] / 
                               pre_spike_metrics['response_time']['mean'])
    spike_throughput_drop = (1 - (spike_metrics['throughput'] / 
                                  pre_spike_metrics['throughput'])) * 100
    spike_cpu_increase = spike_metrics['cpu']['peak'] - pre_spike_metrics['cpu']['avg']
    spike_memory_increase = spike_metrics['memory']['peak'] - pre_spike_metrics['memory']['avg']
    
    print(f"  - Response Time Increase: {spike_response_increase:.2f}x")
    print(f"  - Throughput Drop: {spike_throughput_drop:.1f}%")
    print(f"  - CPU Increase: +{spike_cpu_increase:.1f}%")
    print(f"  - Memory Increase: +{spike_memory_increase:.1f} MB")
    print(f"  - Error Rate During Spike: {spike_metrics['error_rate']:.2f}%")
    
    print(f"\nRecovery Analysis:")
    recovery_response_ratio = (post_spike_metrics['response_time']['mean'] / 
                               pre_spike_metrics['response_time']['mean'])
    recovery_throughput_ratio = (post_spike_metrics['throughput'] / 
                                 pre_spike_metrics['throughput'])
    memory_after_spike = post_spike_metrics['memory']['avg']
    memory_baseline = pre_spike_metrics['memory']['avg']
    memory_retained = memory_after_spike - memory_baseline
    
    print(f"  - Response Time vs Baseline: {recovery_response_ratio:.2f}x")
    print(f"  - Throughput vs Baseline: {recovery_throughput_ratio:.2f}x")
    print(f"  - Memory Retained After Spike: {memory_retained:.1f} MB")
    
    recovered = (0.9 <= recovery_response_ratio <= 1.1 and 
                0.9 <= recovery_throughput_ratio <= 1.1)
    print(f"  - System Recovered: {'✓ YES' if recovered else '✗ NO'}")
    
    # Identify performance findings
    print(f"\n{'='*70}")
    print(f"PERFORMANCE FINDINGS")
    print(f"{'='*70}")
    
    findings = []
    
    # Finding 1: Spike impact severity
    if spike_response_increase > 5:
        findings.append({
            "finding": "Severe performance degradation during spike",
            "details": f"Response time increased {spike_response_increase:.2f}x during spike from {pre_spike_metrics['response_time']['mean']:.4f}s to {spike_metrics['response_time']['mean']:.4f}s",
            "severity": "HIGH"
        })
    elif spike_response_increase > 2:
        findings.append({
            "finding": "Moderate performance degradation during spike",
            "details": f"Response time increased {spike_response_increase:.2f}x during spike",
            "severity": "MEDIUM"
        })
    
    # Finding 2: Throughput collapse
    if spike_throughput_drop > 50:
        findings.append({
            "finding": "Throughput collapse during spike",
            "details": f"Throughput dropped by {spike_throughput_drop:.1f}% (from {pre_spike_metrics['throughput']:.2f} to {spike_metrics['throughput']:.2f} ops/sec)",
            "severity": "HIGH"
        })
    
    # Finding 3: Error rate during spike
    if spike_metrics['error_rate'] > 10:
        findings.append({
            "finding": "High error rate during traffic spike",
            "details": f"Error rate reached {spike_metrics['error_rate']:.2f}% during spike",
            "severity": "HIGH"
        })
    elif spike_metrics['error_rate'] > 5:
        findings.append({
            "finding": "Elevated error rate during spike",
            "details": f"Error rate was {spike_metrics['error_rate']:.2f}% during spike",
            "severity": "MEDIUM"
        })
    
    # Finding 4: Recovery issues
    if not recovered:
        findings.append({
            "finding": "Incomplete system recovery after spike",
            "details": f"System did not return to baseline (response: {recovery_response_ratio:.2f}x, throughput: {recovery_throughput_ratio:.2f}x)",
            "severity": "HIGH"
        })
    
    # Finding 5: Memory leak detection
    if memory_retained > 100:  # More than 100 MB not released
        findings.append({
            "finding": "Potential memory leak or inefficient garbage collection",
            "details": f"System retained {memory_retained:.1f} MB after spike recovery period",
            "severity": "MEDIUM"
        })
    
    # Finding 6: CPU spike
    if spike_metrics['cpu']['peak'] > 90:
        findings.append({
            "finding": "CPU saturation during spike",
            "details": f"CPU peaked at {spike_metrics['cpu']['peak']:.1f}% during traffic burst",
            "severity": "MEDIUM"
        })
    
    # Finding 7: P99 latency spike
    p99_increase = spike_metrics['response_time']['p99'] / pre_spike_metrics['response_time']['p99']
    if p99_increase > 10:
        findings.append({
            "finding": "Extreme tail latency during spike",
            "details": f"P99 latency increased {p99_increase:.1f}x (from {pre_spike_metrics['response_time']['p99']:.4f}s to {spike_metrics['response_time']['p99']:.4f}s)",
            "severity": "HIGH"
        })
    
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['finding']} [{finding['severity']}]")
        print(f"   {finding['details']}")
    
    if not findings:
        print("\n✓ System handled traffic spike gracefully")
        print("  Performance degradation was minimal and recovery was complete")
    
    # Save results
    results_data = {
        "test_type": "Spike Test",
        "owner": "Mallikarjuna",
        "configuration": {
            "baseline_users": BASELINE_USERS,
            "spike_users": SPIKE_USERS,
            "dataset_size": DATASET_SIZE,
            "pre_spike_duration": PRE_SPIKE_DURATION,
            "spike_duration": SPIKE_DURATION,
            "post_spike_duration": POST_SPIKE_DURATION
        },
        "execution": {
            "total_duration": total_duration
        },
        "phase_metrics": {
            "pre_spike": pre_spike_metrics,
            "spike": spike_metrics,
            "post_spike": post_spike_metrics
        },
        "analysis": {
            "spike_impact": {
                "response_time_increase": f"{spike_response_increase:.2f}x",
                "throughput_drop": f"{spike_throughput_drop:.1f}%",
                "cpu_increase": f"+{spike_cpu_increase:.1f}%",
                "memory_increase": f"+{spike_memory_increase:.1f} MB",
                "error_rate": f"{spike_metrics['error_rate']:.2f}%"
            },
            "recovery": {
                "response_ratio": f"{recovery_response_ratio:.2f}x",
                "throughput_ratio": f"{recovery_throughput_ratio:.2f}x",
                "memory_retained_mb": memory_retained,
                "recovered": recovered
            }
        },
        "findings": findings,
        "timestamp": datetime.now().isoformat()
    }
    
    output_dir = "courseProjectDocs/performance-testing"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/spike_test_results.json", 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}/spike_test_results.json")
    print(f"{'='*70}\n")
    
    # Generate visualization
    generate_charts(pre_spike_metrics, spike_metrics, post_spike_metrics, output_dir)
    
    return results_data


def generate_charts(pre_spike, spike, post_spike, output_dir):
    """Generate spike test visualization"""
    print("Generating spike test charts...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Spike Test - Traffic Burst Impact and Recovery', fontsize=16, fontweight='bold')
    
    phases = ['Pre-Spike\n(Baseline)', 'Spike\n(Burst)', 'Post-Spike\n(Recovery)']
    phase_data = [pre_spike, spike, post_spike]
    
    # Chart 1: Response Time Comparison
    response_means = [p['response_time']['mean'] for p in phase_data]
    response_p95 = [p['response_time']['p95'] for p in phase_data]
    
    x = np.arange(len(phases))
    width = 0.35
    axes[0, 0].bar(x - width/2, response_means, width, label='Mean', color='skyblue', edgecolor='black')
    axes[0, 0].bar(x + width/2, response_p95, width, label='p95', color='coral', edgecolor='black')
    axes[0, 0].set_ylabel('Response Time (seconds)')
    axes[0, 0].set_title('Response Time Across Phases')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(phases)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # Chart 2: Throughput Comparison
    throughputs = [p['throughput'] for p in phase_data]
    axes[0, 1].bar(phases, throughputs, color=['green', 'red', 'yellow'], edgecolor='black')
    axes[0, 1].set_ylabel('Throughput (ops/sec)')
    axes[0, 1].set_title('Throughput Across Phases')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(throughputs):
        axes[0, 1].text(i, v + max(throughputs)*0.02, f'{v:.1f}', ha='center', fontweight='bold')
    
    # Chart 3: CPU Usage Comparison
    cpu_avgs = [p['cpu']['avg'] for p in phase_data]
    cpu_peaks = [p['cpu']['peak'] for p in phase_data]
    
    x = np.arange(len(phases))
    axes[0, 2].bar(x - width/2, cpu_avgs, width, label='Average', color='lightgreen', edgecolor='black')
    axes[0, 2].bar(x + width/2, cpu_peaks, width, label='Peak', color='darkgreen', edgecolor='black')
    axes[0, 2].axhline(80, color='orange', linestyle='--', alpha=0.7, label='Warning')
    axes[0, 2].set_ylabel('CPU Usage (%)')
    axes[0, 2].set_title('CPU Usage Across Phases')
    axes[0, 2].set_xticks(x)
    axes[0, 2].set_xticklabels(phases)
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3, axis='y')
    
    # Chart 4: Memory Usage Comparison
    memory_avgs = [p['memory']['avg'] for p in phase_data]
    memory_peaks = [p['memory']['peak'] for p in phase_data]
    
    axes[1, 0].bar(x - width/2, memory_avgs, width, label='Average', color='lightblue', edgecolor='black')
    axes[1, 0].bar(x + width/2, memory_peaks, width, label='Peak', color='darkblue', edgecolor='black')
    axes[1, 0].set_ylabel('Memory Usage (MB)')
    axes[1, 0].set_title('Memory Usage Across Phases')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(phases)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Chart 5: Error Rate Comparison
    error_rates = [p['error_rate'] for p in phase_data]
    colors = ['green' if e < 5 else 'orange' if e < 10 else 'red' for e in error_rates]
    axes[1, 1].bar(phases, error_rates, color=colors, edgecolor='black')
    axes[1, 1].axhline(5, color='orange', linestyle='--', alpha=0.7, label='Warning (5%)')
    axes[1, 1].axhline(10, color='red', linestyle='--', alpha=0.7, label='Critical (10%)')
    axes[1, 1].set_ylabel('Error Rate (%)')
    axes[1, 1].set_title('Error Rate Across Phases')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    # Chart 6: Time-series view of a metric (Response Time)
    # Combine all response times with phase markers
    all_times = []
    all_phases = []
    
    for phase_name, phase in [('Pre-Spike', pre_spike), ('Spike', spike), ('Post-Spike', post_spike)]:
        times = phase.get('response_times', [])
        all_times.extend(times)
        all_phases.extend([phase_name] * len(times))
    
    if all_times:
        # Create scatter plot with color coding
        phase_colors = {'Pre-Spike': 'green', 'Spike': 'red', 'Post-Spike': 'blue'}
        for phase_name in ['Pre-Spike', 'Spike', 'Post-Spike']:
            phase_indices = [i for i, p in enumerate(all_phases) if p == phase_name]
            phase_times = [all_times[i] for i in phase_indices]
            axes[1, 2].scatter(phase_indices, phase_times, c=phase_colors[phase_name], 
                             label=phase_name, alpha=0.6, s=20)
        
        axes[1, 2].set_xlabel('Operation Sequence')
        axes[1, 2].set_ylabel('Response Time (seconds)')
        axes[1, 2].set_title('Response Time Timeline')
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_path = f"{output_dir}/spike_test_charts.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"Charts saved to: {chart_path}\n")
    plt.close()


if __name__ == "__main__":
    run_spike_test()
