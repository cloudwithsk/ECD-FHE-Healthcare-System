"""
FHE Performance Benchmarking Module

This module provides comprehensive performance benchmarking for FHE operations
used in the healthcare system. It measures actual encryption, decryption, and
computation times to provide accurate performance metrics.
"""

import time
import statistics
import json
import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from .engine import SEALEngine


class FHEBenchmark:
    """
    Comprehensive benchmarking tool for FHE operations.
    
    Measures:
    - Encryption/Decryption times
    - Homomorphic operation times
    - Memory usage
    - Throughput metrics
    - Performance across different data sizes
    """
    
    def __init__(self, 
                 scheme: str = 'bfv',
                 poly_modulus_degree: int = 4096,
                 security_level: int = 128,
                 warmup_runs: int = 5,
                 benchmark_runs: int = 20):
        """
        Initialize the benchmark engine.
        
        Args:
            scheme: FHE scheme to benchmark ('bfv', 'ckks', 'bgv')
            poly_modulus_degree: Polynomial modulus degree
            security_level: Security level in bits
            warmup_runs: Number of warmup runs before actual benchmarking
            benchmark_runs: Number of runs for each benchmark test
        """
        self.scheme = scheme
        self.poly_modulus_degree = poly_modulus_degree
        self.security_level = security_level
        self.warmup_runs = warmup_runs
        self.benchmark_runs = benchmark_runs
        
        # Initialize SEAL engine
        self.engine = SEALEngine(
            scheme=scheme,
            poly_modulus_degree=poly_modulus_degree,
            security_level=security_level
        )
        
        # Benchmark results storage
        self.results = {}
    
    def _warmup(self):
        """Perform warmup runs to stabilize performance measurements."""
        print(f"🔄 Warming up with {self.warmup_runs} runs...")
        
        # Simple warmup operations
        test_data = [1, 2, 3, 4, 5]
        for _ in range(self.warmup_runs):
            encrypted = self.engine.encrypt(test_data)
            decrypted = self.engine.decrypt(encrypted)
            _ = self.engine.add(encrypted, encrypted)
        
        print("✅ Warmup complete")
    
    def _measure_time(self, operation_func, *args, **kwargs) -> float:
        """
        Measure execution time of an operation.
        
        Args:
            operation_func: Function to measure
            *args, **kwargs: Arguments for the function
            
        Returns:
            Execution time in milliseconds
        """
        start_time = time.perf_counter()
        result = operation_func(*args, **kwargs)
        end_time = time.perf_counter()
        
        return (end_time - start_time) * 1000  # Convert to milliseconds
    
    def benchmark_encryption_decryption(self, data_sizes: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Benchmark encryption and decryption performance.
        
        Args:
            data_sizes: List of data sizes to test (number of elements)
            
        Returns:
            Dictionary with benchmark results
        """
        if data_sizes is None:
            data_sizes = [1, 10, 50, 100, 500, 1000]
        
        print(f"🔐 Benchmarking encryption/decryption for {self.scheme.upper()}")
        print(f"   Data sizes: {data_sizes}")
        
        results = {
            'scheme': self.scheme,
            'poly_modulus_degree': self.poly_modulus_degree,
            'security_level': self.security_level,
            'data_sizes': data_sizes,
            'encryption_times': {},
            'decryption_times': {},
            'total_times': {}
        }
        
        for size in data_sizes:
            print(f"   Testing size {size}...")
            
            # Generate test data
            if self.scheme in ['bfv', 'bgv']:
                test_data = list(range(1, size + 1))
            else:  # CKKS
                test_data = [float(i) + 0.1 for i in range(1, size + 1)]
            
            encryption_times = []
            decryption_times = []
            total_times = []
            
            for _ in range(self.benchmark_runs):
                # Measure encryption
                encrypted = None
                encrypt_time = self._measure_time(self.engine.encrypt, test_data)
                encryption_times.append(encrypt_time)
                
                # Measure decryption
                encrypted = self.engine.encrypt(test_data)
                decrypt_time = self._measure_time(self.engine.decrypt, encrypted)
                decryption_times.append(decrypt_time)
                
                # Total time
                total_time = encrypt_time + decrypt_time
                total_times.append(total_time)
            
            # Calculate statistics
            results['encryption_times'][size] = {
                'mean': statistics.mean(encryption_times),
                'median': statistics.median(encryption_times),
                'min': min(encryption_times),
                'max': max(encryption_times),
                'std': statistics.stdev(encryption_times) if len(encryption_times) > 1 else 0,
                'all_times': encryption_times
            }
            
            results['decryption_times'][size] = {
                'mean': statistics.mean(decryption_times),
                'median': statistics.median(decryption_times),
                'min': min(decryption_times),
                'max': max(decryption_times),
                'std': statistics.stdev(decryption_times) if len(decryption_times) > 1 else 0,
                'all_times': decryption_times
            }
            
            results['total_times'][size] = {
                'mean': statistics.mean(total_times),
                'median': statistics.median(total_times),
                'min': min(total_times),
                'max': max(total_times),
                'std': statistics.stdev(total_times) if len(total_times) > 1 else 0,
                'all_times': total_times
            }
        
        self.results['encryption_decryption'] = results
        return results
    
    def benchmark_homomorphic_operations(self, data_size: int = 100) -> Dict[str, Any]:
        """
        Benchmark homomorphic operations performance.
        
        Args:
            data_size: Size of data to use for operations
            
        Returns:
            Dictionary with benchmark results
        """
        print(f"🔢 Benchmarking homomorphic operations for {self.scheme.upper()}")
        print(f"   Data size: {data_size}")
        
        # Generate test data
        if self.scheme in ['bfv', 'bgv']:
            a = list(range(1, data_size + 1))
            b = list(range(data_size, 0, -1))
            c = [2] * data_size
        else:  # CKKS
            a = [float(i) + 0.1 for i in range(1, data_size + 1)]
            b = [float(i) + 0.2 for i in range(data_size, 0, -1)]
            c = [2.0] * data_size
        
        # Encrypt data
        encrypted_a = self.engine.encrypt(a)
        encrypted_b = self.engine.encrypt(b)
        
        results = {
            'scheme': self.scheme,
            'data_size': data_size,
            'operations': {}
        }
        
        # Benchmark addition
        print("   Testing addition...")
        add_times = []
        for _ in range(self.benchmark_runs):
            add_time = self._measure_time(self.engine.add, encrypted_a, encrypted_b)
            add_times.append(add_time)
        
        results['operations']['addition'] = {
            'mean': statistics.mean(add_times),
            'median': statistics.median(add_times),
            'min': min(add_times),
            'max': max(add_times),
            'std': statistics.stdev(add_times) if len(add_times) > 1 else 0,
            'all_times': add_times
        }
        
        # Benchmark multiplication
        print("   Testing multiplication...")
        multiply_times = []
        for _ in range(self.benchmark_runs):
            multiply_time = self._measure_time(self.engine.multiply, encrypted_a, encrypted_b)
            multiply_times.append(multiply_time)
        
        results['operations']['multiplication'] = {
            'mean': statistics.mean(multiply_times),
            'median': statistics.median(multiply_times),
            'min': min(multiply_times),
            'max': max(multiply_times),
            'std': statistics.stdev(multiply_times) if len(multiply_times) > 1 else 0,
            'all_times': multiply_times
        }
        
        # Benchmark squaring
        print("   Testing squaring...")
        square_times = []
        for _ in range(self.benchmark_runs):
            square_time = self._measure_time(self.engine.square, encrypted_a)
            square_times.append(square_time)
        
        results['operations']['squaring'] = {
            'mean': statistics.mean(square_times),
            'median': statistics.median(square_times),
            'min': min(square_times),
            'max': max(square_times),
            'std': statistics.stdev(square_times) if len(square_times) > 1 else 0,
            'all_times': square_times
        }
        
        # Benchmark plaintext operations
        print("   Testing plaintext operations...")
        add_plain_times = []
        multiply_plain_times = []
        
        for _ in range(self.benchmark_runs):
            add_plain_time = self._measure_time(self.engine.add_plain, encrypted_a, 10)
            add_plain_times.append(add_plain_time)
            
            multiply_plain_time = self._measure_time(self.engine.multiply_plain, encrypted_a, 2)
            multiply_plain_times.append(multiply_plain_time)
        
        results['operations']['add_plain'] = {
            'mean': statistics.mean(add_plain_times),
            'median': statistics.median(add_plain_times),
            'min': min(add_plain_times),
            'max': max(add_plain_times),
            'std': statistics.stdev(add_plain_times) if len(add_plain_times) > 1 else 0,
            'all_times': add_plain_times
        }
        
        results['operations']['multiply_plain'] = {
            'mean': statistics.mean(multiply_plain_times),
            'median': statistics.median(multiply_plain_times),
            'min': min(multiply_plain_times),
            'max': max(multiply_plain_times),
            'std': statistics.stdev(multiply_plain_times) if len(multiply_plain_times) > 1 else 0,
            'all_times': multiply_plain_times
        }
        
        self.results['homomorphic_operations'] = results
        return results
    
    def benchmark_throughput(self, data_size: int = 100, duration_seconds: int = 10) -> Dict[str, Any]:
        """
        Benchmark throughput (operations per second).
        
        Args:
            data_size: Size of data to use
            duration_seconds: Duration of throughput test
            
        Returns:
            Dictionary with throughput results
        """
        print(f"⚡ Benchmarking throughput for {self.scheme.upper()}")
        print(f"   Data size: {data_size}, Duration: {duration_seconds}s")
        
        # Generate test data
        if self.scheme in ['bfv', 'bgv']:
            test_data = list(range(1, data_size + 1))
        else:  # CKKS
            test_data = [float(i) + 0.1 for i in range(1, data_size + 1)]
        
        results = {
            'scheme': self.scheme,
            'data_size': data_size,
            'duration_seconds': duration_seconds,
            'throughput': {}
        }
        
        # Test encryption throughput
        print("   Testing encryption throughput...")
        start_time = time.perf_counter()
        encryption_count = 0
        
        while time.perf_counter() - start_time < duration_seconds:
            self.engine.encrypt(test_data)
            encryption_count += 1
        
        encryption_throughput = encryption_count / duration_seconds
        
        # Test decryption throughput
        print("   Testing decryption throughput...")
        encrypted_data = self.engine.encrypt(test_data)
        start_time = time.perf_counter()
        decryption_count = 0
        
        while time.perf_counter() - start_time < duration_seconds:
            self.engine.decrypt(encrypted_data)
            decryption_count += 1
        
        decryption_throughput = decryption_count / duration_seconds
        
        # Test addition throughput
        print("   Testing addition throughput...")
        encrypted_a = self.engine.encrypt(test_data)
        encrypted_b = self.engine.encrypt(test_data)
        start_time = time.perf_counter()
        addition_count = 0
        
        while time.perf_counter() - start_time < duration_seconds:
            self.engine.add(encrypted_a, encrypted_b)
            addition_count += 1
        
        addition_throughput = addition_count / duration_seconds
        
        results['throughput'] = {
            'encryption_ops_per_second': encryption_throughput,
            'decryption_ops_per_second': decryption_throughput,
            'addition_ops_per_second': addition_throughput
        }
        
        self.results['throughput'] = results
        return results
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive benchmark suite.
        
        Returns:
            Complete benchmark results
        """
        print("🚀 Starting comprehensive FHE benchmark suite")
        print(f"   Scheme: {self.scheme.upper()}")
        print(f"   Polynomial modulus degree: {self.poly_modulus_degree}")
        print(f"   Security level: {self.security_level} bits")
        print(f"   Benchmark runs: {self.benchmark_runs}")
        print()
        
        # Warmup
        self._warmup()
        print()
        
        # Run all benchmarks
        encryption_results = self.benchmark_encryption_decryption()
        print()
        
        operation_results = self.benchmark_homomorphic_operations()
        print()
        
        throughput_results = self.benchmark_throughput()
        print()
        
        # Compile summary
        summary = self._generate_summary()
        
        complete_results = {
            'summary': summary,
            'encryption_decryption': encryption_results,
            'homomorphic_operations': operation_results,
            'throughput': throughput_results,
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'scheme': self.scheme,
                'poly_modulus_degree': self.poly_modulus_degree,
                'security_level': self.security_level,
                'benchmark_runs': self.benchmark_runs
            }
        }
        
        self.results = complete_results
        return complete_results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of benchmark results."""
        if not self.results:
            return {}
        
        # Get typical data size (100 elements)
        typical_size = 100
        
        summary = {
            'scheme': self.scheme,
            'typical_performance': {}
        }
        
        # Encryption/Decryption summary
        if 'encryption_decryption' in self.results:
            enc_dec = self.results['encryption_decryption']
            if typical_size in enc_dec['encryption_times']:
                summary['typical_performance']['encryption_time_ms'] = {
                    'mean': enc_dec['encryption_times'][typical_size]['mean'],
                    'range': f"{enc_dec['encryption_times'][typical_size]['min']:.1f}-{enc_dec['encryption_times'][typical_size]['max']:.1f}"
                }
                
                summary['typical_performance']['decryption_time_ms'] = {
                    'mean': enc_dec['decryption_times'][typical_size]['mean'],
                    'range': f"{enc_dec['decryption_times'][typical_size]['min']:.1f}-{enc_dec['decryption_times'][typical_size]['max']:.1f}"
                }
        
        # Operation summary
        if 'homomorphic_operations' in self.results:
            ops = self.results['homomorphic_operations']
            summary['typical_performance']['addition_time_ms'] = {
                'mean': ops['operations']['addition']['mean'],
                'range': f"{ops['operations']['addition']['min']:.1f}-{ops['operations']['addition']['max']:.1f}"
            }
            
            summary['typical_performance']['multiplication_time_ms'] = {
                'mean': ops['operations']['multiplication']['mean'],
                'range': f"{ops['operations']['multiplication']['min']:.1f}-{ops['operations']['multiplication']['max']:.1f}"
            }
        
        # Throughput summary
        if 'throughput' in self.results:
            throughput = self.results['throughput']['throughput']
            summary['typical_performance']['throughput'] = {
                'encryption_ops_per_second': throughput['encryption_ops_per_second'],
                'decryption_ops_per_second': throughput['decryption_ops_per_second'],
                'addition_ops_per_second': throughput['addition_ops_per_second']
            }
        
        return summary
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save benchmark results to JSON file.
        
        Args:
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"fhe_benchmark_{self.scheme}_{timestamp}.json"
        
        # Ensure results directory exists
        os.makedirs('benchmarks', exist_ok=True)
        filepath = os.path.join('benchmarks', filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"💾 Benchmark results saved to: {filepath}")
        return filepath
    
    def print_summary(self):
        """Print a formatted summary of benchmark results."""
        if not self.results or 'summary' not in self.results:
            print("No benchmark results available. Run benchmark first.")
            return
        
        summary = self.results['summary']
        print("\n" + "="*60)
        print("FHE BENCHMARK SUMMARY")
        print("="*60)
        print(f"Scheme: {summary['scheme'].upper()}")
        print(f"Polynomial Modulus Degree: {self.poly_modulus_degree}")
        print(f"Security Level: {self.security_level} bits")
        print()
        
        if 'typical_performance' in summary:
            perf = summary['typical_performance']
            
            print("📊 TYPICAL PERFORMANCE (100 data points):")
            print("-" * 40)
            
            if 'encryption_time_ms' in perf:
                print(f"🔐 Encryption: {perf['encryption_time_ms']['mean']:.1f}ms (range: {perf['encryption_time_ms']['range']}ms)")
            
            if 'decryption_time_ms' in perf:
                print(f"🔓 Decryption: {perf['decryption_time_ms']['mean']:.1f}ms (range: {perf['decryption_time_ms']['range']}ms)")
            
            if 'addition_time_ms' in perf:
                print(f"➕ Addition: {perf['addition_time_ms']['mean']:.1f}ms (range: {perf['addition_time_ms']['range']}ms)")
            
            if 'multiplication_time_ms' in perf:
                print(f"✖️ Multiplication: {perf['multiplication_time_ms']['mean']:.1f}ms (range: {perf['multiplication_time_ms']['range']}ms)")
            
            if 'throughput' in perf:
                print()
                print("⚡ THROUGHPUT:")
                print("-" * 20)
                print(f"Encryption: {perf['throughput']['encryption_ops_per_second']:.1f} ops/sec")
                print(f"Decryption: {perf['throughput']['decryption_ops_per_second']:.1f} ops/sec")
                print(f"Addition: {perf['throughput']['addition_ops_per_second']:.1f} ops/sec")
        
        print("="*60)


def run_quick_benchmark(scheme: str = 'bfv', poly_modulus_degree: int = 4096) -> Dict[str, Any]:
    """
    Run a quick benchmark for immediate results.
    
    Args:
        scheme: FHE scheme to test
        poly_modulus_degree: Polynomial modulus degree
        
    Returns:
        Benchmark results
    """
    benchmark = FHEBenchmark(
        scheme=scheme,
        poly_modulus_degree=poly_modulus_degree,
        warmup_runs=3,
        benchmark_runs=10
    )
    
    return benchmark.run_comprehensive_benchmark()


if __name__ == "__main__":
    # Example usage
    print("FHE Performance Benchmarking Tool")
    print("=" * 40)
    
    # Run benchmark for BFV
    benchmark = FHEBenchmark(scheme='bfv', poly_modulus_degree=4096)
    results = benchmark.run_comprehensive_benchmark()
    
    # Print summary
    benchmark.print_summary()
    
    # Save results
    benchmark.save_results() 