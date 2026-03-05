#!/usr/bin/env python3
"""
Batch training script for running multiple experiments with different configurations.
Optimized for speed with parallel processing.
"""

import subprocess
import json
import os
import time
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_training(config_name, use_gpu=True, model_type='fast'):
    """Run a single training experiment"""
    
    print(f"\n{'='*60}")
    print(f"Starting experiment: {config_name}")
    print(f"{'='*60}")
    
    # Create command based on configuration
    if use_gpu:
        docker_cmd = [
            'docker', 'run', '--gpus', 'all',
            '-v', f'{os.getcwd()}:/app',
            '-v', f'{os.getcwd()}/logs:/app/logs',
            '-v', f'{os.getcwd()}/dataset:/app/dataset',
            '-e', 'TF_FORCE_GPU_ALLOW_GROWTH=true',
            '-e', 'TF_CPP_MIN_LOG_LEVEL=3',
            'simple-vtuber-tensorflow-gpu',
            'python3', 'train_tensorflow_gpu.py'
        ]
    else:
        docker_cmd = [
            'docker', 'run',
            '-v', f'{os.getcwd()}:/app',
            '-v', f'{os.getcwd()}/logs:/app/logs',
            '-v', f'{os.getcwd()}/dataset:/app/dataset',
            '-e', 'TF_CPP_MIN_LOG_LEVEL=3',
            'simple-vtuber-tensorflow-cpu',
            'python3', 'train_tensorflow_gpu.py'
        ]
    
    # Add model type argument
    if model_type == 'lightning':
        docker_cmd.append('--lightning')
    else:
        docker_cmd.append('--fast')
    
    # Create output directory
    output_dir = f'trained_experiments/{config_name}'
    os.makedirs(output_dir, exist_ok=True)
    
    # Add output directory to volumes
    docker_cmd.insert(-3, '-v')
    docker_cmd.insert(-3, f'{os.getcwd()}/{output_dir}:/app/trained_python_fast')
    
    # Run training
    start_time = time.time()
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        training_time = time.time() - start_time
        
        # Save results
        results = {
            'config_name': config_name,
            'use_gpu': use_gpu,
            'model_type': model_type,
            'training_time': training_time,
            'exit_code': result.returncode,
            'stdout': result.stdout[-1000:],  # Last 1000 chars
            'stderr': result.stderr[-1000:] if result.stderr else '',
            'success': result.returncode == 0
        }
        
        with open(f'{output_dir}/experiment_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        if result.returncode == 0:
            print(f"✓ Experiment {config_name} completed in {training_time:.2f}s")
            return True, config_name, training_time
        else:
            print(f"✗ Experiment {config_name} failed (code: {result.returncode})")
            return False, config_name, training_time
            
    except subprocess.TimeoutExpired:
        print(f"✗ Experiment {config_name} timed out after 1 hour")
        return False, config_name, 3600
    except Exception as e:
        print(f"✗ Experiment {config_name} error: {str(e)}")
        return False, config_name, 0

def run_experiments_parallel(experiments, max_workers=2):
    """Run experiments in parallel"""
    
    print(f"\n{'='*60}")
    print(f"Running {len(experiments)} experiments with {max_workers} parallel workers")
    print(f"{'='*60}")
    
    successful = []
    failed = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all experiments
        future_to_exp = {}
        for exp in experiments:
            future = executor.submit(
                run_training,
                exp['name'],
                exp.get('use_gpu', True),
                exp.get('model_type', 'fast')
            )
            future_to_exp[future] = exp['name']
        
        # Process results as they complete
        for future in as_completed(future_to_exp):
            exp_name = future_to_exp[future]
            try:
                success, name, training_time = future.result()
                if success:
                    successful.append((name, training_time))
                else:
                    failed.append(name)
            except Exception as e:
                print(f"✗ Exception in experiment {exp_name}: {str(e)}")
                failed.append(exp_name)
    
    return successful, failed

def create_experiment_configs():
    """Create different experiment configurations"""
    
    experiments = []
    
    # Base experiments with GPU
    experiments.append({
        'name': 'gpu_fast_32batch',
        'use_gpu': True,
        'model_type': 'fast'
    })
    
    experiments.append({
        'name': 'gpu_lightning_32batch',
        'use_gpu': True,
        'model_type': 'lightning'
    })
    
    experiments.append({
        'name': 'gpu_fast_64batch',
        'use_gpu': True,
        'model_type': 'fast'
    })
    
    # CPU experiments for comparison
    experiments.append({
        'name': 'cpu_fast_32batch',
        'use_gpu': False,
        'model_type': 'fast'
    })
    
    experiments.append({
        'name': 'cpu_lightning_32batch',
        'use_gpu': False,
        'model_type': 'lightning'
    })
    
    return experiments

def generate_report(successful, failed):
    """Generate training report"""
    
    print(f"\n{'='*60}")
    print("TRAINING REPORT")
    print(f"{'='*60}")
    
    print(f"\nSuccessful experiments: {len(successful)}")
    for name, time_taken in successful:
        print(f"  ✓ {name}: {time_taken:.2f}s")
    
    print(f"\nFailed experiments: {len(failed)}")
    for name in failed:
        print(f"  ✗ {name}")
    
    # Calculate speedup if we have both GPU and CPU results
    gpu_times = [t for n, t in successful if 'gpu' in n]
    cpu_times = [t for n, t in successful if 'cpu' in n]
    
    if gpu_times and cpu_times:
        avg_gpu = sum(gpu_times) / len(gpu_times)
        avg_cpu = sum(cpu_times) / len(cpu_times)
        speedup = avg_cpu / avg_gpu
        
        print(f"\nPerformance Summary:")
        print(f"  Average GPU time: {avg_gpu:.2f}s")
        print(f"  Average CPU time: {avg_cpu:.2f}s")
        print(f"  GPU speedup: {speedup:.1f}x faster")
    
    # Save report
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'successful': [{'name': n, 'time': t} for n, t in successful],
        'failed': failed,
        'total_experiments': len(successful) + len(failed)
    }
    
    with open('training_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: training_report.json")

def main():
    parser = argparse.ArgumentParser(description='Batch training experiments')
    parser.add_argument('--parallel', type=int, default=2,
                       help='Number of parallel experiments (default: 2)')
    parser.add_argument('--gpu-only', action='store_true',
                       help='Run only GPU experiments')
    parser.add_argument('--cpu-only', action='store_true',
                       help='Run only CPU experiments')
    parser.add_argument('--single', type=str,
                       help='Run single experiment by name')
    
    args = parser.parse_args()
    
    # Create experiments directory
    os.makedirs('trained_experiments', exist_ok=True)
    
    # Get experiment configurations
    all_experiments = create_experiment_configs()
    
    # Filter experiments based on arguments
    experiments_to_run = []
    
    if args.single:
        # Run single experiment
        for exp in all_experiments:
            if exp['name'] == args.single:
                experiments_to_run = [exp]
                break
        if not experiments_to_run:
            print(f"Error: Experiment '{args.single}' not found")
            return
    elif args.gpu_only:
        experiments_to_run = [exp for exp in all_experiments if exp.get('use_gpu', True)]
    elif args.cpu_only:
        experiments_to_run = [exp for exp in all_experiments if not exp.get('use_gpu', True)]
    else:
        experiments_to_run = all_experiments
    
    print(f"Running {len(experiments_to_run)} experiments")
    
    # Run experiments
    successful, failed = run_experiments_parallel(
        experiments_to_run,
        max_workers=args.parallel
    )
    
    # Generate report
    generate_report(successful, failed)
    
    print(f"\n{'='*60}")
    print("BATCH TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"1. Check individual experiment results in trained_experiments/")
    print(f"2. View TensorBoard: docker-compose up tensorboard")
    print(f"3. Compare models: python3 compare_models.py")

if __name__ == '__main__':
    main()