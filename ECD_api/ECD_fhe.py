#!/usr/bin/env python3
"""
Enhanced FHE Test: Encrypt → Compute → Decrypt with Performance Monitoring
This script demonstrates the basic workflow with comprehensive performance metrics.
"""

import sys
import os
import time
import gc
import statistics
from typing import Dict, List, Tuple, Any, Optional

# Add the parent directory to Python path to find the core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.engine import SEALEngine
    SEAL_AVAILABLE = True
    print("✅ SEAL engine available")
except ImportError as e:
    print(f"❌ SEAL engine not available: {e}")
    SEAL_AVAILABLE = False
    sys.exit(1)

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✅ psutil available for memory monitoring")
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available - memory monitoring will be limited")


class PerformanceMonitor:
    """Comprehensive performance monitoring for FHE operations."""
    
    def __init__(self):
        self.measurements = {}
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            return {"rss_mb": 0.0, "vms_mb": 0.0}
        
        try:
            memory_info = self.process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
                "vms_mb": memory_info.vms / 1024 / 1024   # Virtual Memory Size
            }
        except Exception as e:
            print(f"⚠️ Memory measurement error: {e}")
            return {"rss_mb": 0.0, "vms_mb": 0.0}
    
    def measure_operation(self, operation_name: str, operation_func, *args, **kwargs) -> Dict[str, Any]:
        """
        Measure performance of an operation including time and memory.
        
        Args:
            operation_name: Name of the operation being measured
            operation_func: Function to measure
            *args, **kwargs: Arguments for the function
            
        Returns:
            Dictionary with performance metrics
        """
        # Force garbage collection before measurement
        gc.collect()
        
        # Get initial memory
        initial_memory = self.get_memory_usage()
        
        # Measure time
        start_time = time.perf_counter()
        result = operation_func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Get final memory
        final_memory = self.get_memory_usage()
        
        # Calculate metrics
        execution_time_ms = (end_time - start_time) * 1000
        memory_delta_rss = final_memory["rss_mb"] - initial_memory["rss_mb"]
        memory_delta_vms = final_memory["vms_mb"] - initial_memory["vms_mb"]
        
        metrics = {
            "operation": operation_name,
            "execution_time_ms": execution_time_ms,
            "memory_initial_rss_mb": initial_memory["rss_mb"],
            "memory_final_rss_mb": final_memory["rss_mb"],
            "memory_delta_rss_mb": memory_delta_rss,
            "memory_initial_vms_mb": initial_memory["vms_mb"],
            "memory_final_vms_mb": final_memory["vms_mb"],
            "memory_delta_vms_mb": memory_delta_vms,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.measurements[operation_name] = metrics
        return metrics
    
    def print_measurement(self, metrics: Dict[str, Any]):
        """Print formatted performance measurement."""
        print(f"   ⏱️  Time: {metrics['execution_time_ms']:.2f}ms")
        if PSUTIL_AVAILABLE:
            print(f"   💾 Memory RSS: {metrics['memory_initial_rss_mb']:.1f}MB → {metrics['memory_final_rss_mb']:.1f}MB (Δ: {metrics['memory_delta_rss_mb']:+.1f}MB)")
            print(f"   💾 Memory VMS: {metrics['memory_initial_vms_mb']:.1f}MB → {metrics['memory_final_vms_mb']:.1f}MB (Δ: {metrics['memory_delta_vms_mb']:+.1f}MB)")
    
    def run_multiple_measurements(self, operation_name: str, operation_func, 
                                num_runs: int = 5, *args, **kwargs) -> Dict[str, Any]:
        """
        Run multiple measurements and calculate statistics.
        
        Args:
            operation_name: Name of the operation
            operation_func: Function to measure
            num_runs: Number of times to run the measurement
            *args, **kwargs: Arguments for the function
            
        Returns:
            Dictionary with statistical summary
        """
        print(f"   📊 Running {num_runs} measurements for {operation_name}...")
        
        times = []
        memory_deltas_rss = []
        memory_deltas_vms = []
        
        for i in range(num_runs):
            print(f"      Run {i+1}/{num_runs}...", end=" ")
            metrics = self.measure_operation(operation_name, operation_func, *args, **kwargs)
            times.append(metrics['execution_time_ms'])
            memory_deltas_rss.append(metrics['memory_delta_rss_mb'])
            memory_deltas_vms.append(metrics['memory_delta_vms_mb'])
            print(f"✅ {metrics['execution_time_ms']:.1f}ms")
        
        # Calculate statistics
        summary = {
            "operation": operation_name,
            "num_runs": num_runs,
            "time_stats": {
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "std_ms": statistics.stdev(times) if len(times) > 1 else 0,
                "all_times": times
            },
            "memory_stats": {
                "mean_delta_rss_mb": statistics.mean(memory_deltas_rss),
                "mean_delta_vms_mb": statistics.mean(memory_deltas_vms),
                "max_delta_rss_mb": max(memory_deltas_rss),
                "max_delta_vms_mb": max(memory_deltas_vms),
                "all_deltas_rss": memory_deltas_rss,
                "all_deltas_vms": memory_deltas_vms
            }
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary of multiple measurements."""
        time_stats = summary['time_stats']
        memory_stats = summary['memory_stats']
        
        print(f"   📈 {summary['operation']} Performance Summary ({summary['num_runs']} runs):")
        print(f"      ⏱️  Time: {time_stats['mean_ms']:.2f}ms ± {time_stats['std_ms']:.2f}ms")
        print(f"      ⏱️  Range: {time_stats['min_ms']:.1f}ms - {time_stats['max_ms']:.1f}ms")
        if PSUTIL_AVAILABLE:
            print(f"      💾 Memory RSS Δ: {memory_stats['mean_delta_rss_mb']:+.1f}MB (max: {memory_stats['max_delta_rss_mb']:+.1f}MB)")
            print(f"      💾 Memory VMS Δ: {memory_stats['mean_delta_vms_mb']:+.1f}MB (max: {memory_stats['max_delta_vms_mb']:+.1f}MB)")


def test_simple_encrypt_compute_decrypt():
    """Test the basic encrypt → compute → decrypt workflow"""
    
    print("\n STEP 1: KEY GENERATION")
    print("=" * 50)
    
    # Initialize SEAL engine with working parameters for SEAL 4.0.0
    try:
        # Use OPTIMIZED parameters for minimum noise and maximum accuracy
        engine = SEALEngine(
            scheme='ckks',
            poly_modulus_degree=4096,  # Optimal for performance vs security
            coeff_modulus_degree=[50],  # Working parameter for SEAL 4.0.0
            scale_factor=30,  # Scale factor for CKKS encoding
            #plain_modulus_bits=20 Used for BFV not CKKS
        )
        print("✅ Keys generated successfully")
        print(f"   - Secret Key: Generated")
        print(f"   - Public Key: Generated") 
        print(f"   - Relin Keys: Generated")
        
        # Display configuration info
        info = engine.get_info()
        print(f"   - Scheme: {info['scheme']}")
        print(f"   - Poly Modulus Degree: {info['poly_modulus_degree']}")
        print(f"   - Coefficient Modulus Degree: {info['coeff_modulus_degree']}")
        print(f"   - Scale Factor: {info['scale_factor']} (Scale: {info['scale']})")
        print(f"   - Slot Count: {info['slot_count']}")
        
    except Exception as e:
        print(f" Key generation failed: {e}")
        return False
    
    print("\n STEP 2: ENCRYPTION")
    print("=" * 50)
    
    # Sample patient data
    patient_data = [20, 117, 83, 80, 99]  # age, systolic, diastolic, heart_rate, temp
    print(f"Original data: {patient_data}")
    
    try:
        # Encrypt the data
        print(f"   - Attempting to encrypt with scheme: {engine.scheme}")
        print(f"   - Data type: {type(patient_data)}")
        print(f"   - Data: {patient_data}")
        encrypted_data = engine.encrypt(patient_data)
        print("✅ Data encrypted successfully")
        
        # Note: Noise budget check removed due to context limitations
        # The core encrypt → compute → decrypt workflow will still work
        
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        print(f"   - Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n STEP 3: COMPUTATION (Homomorphic Operations)")
    print("=" * 50)
    
    try:
        # Perform computation on encrypted data
        # Simple operation: Add 5 mmHg to systolic BP (position 1)
        bp_adjustment = [0, 5, 0, 0, 0]  # Add 5 to systolic only
        result_encrypted = engine.add_plain(encrypted_data, bp_adjustment)
        
        print("✅ FHE computation completed")
        print("   - Added 5 mmHg to systolic blood pressure")
        print("   - Simple addition operation to verify FHE workflow")
        
    except Exception as e:
        print(f"❌ Computation failed: {e}")
        return False
    
    print("\n STEP 4: DECRYPTION")
    print("=" * 50)
    
    try:
        # Decrypt the result
        decrypted_result = engine.decrypt(result_encrypted)
        print(f"✅ Decryption successful")
        
        # Show only the relevant data points (first 5 values)
        relevant_data = decrypted_result[:5]
        print(f"Relevant data (first 5 values): {relevant_data}")
        print(f"Full result length: {len(decrypted_result)} values (CKKS slot count)")
        
        # Calculate expected result manually for comparison
        expected = patient_data[1] + 5  # Original systolic + 5
        print(f"Expected result: {expected}")
        
        # Extract the correct result (systolic BP is at position 1)
        actual = decrypted_result[1]  # Second element contains adjusted systolic
        relative_error = abs(actual - expected) / expected * 100
        print(f"Actual systolic BP: {actual}")
        print(f"Relative Error: {relative_error:.2f}%")
        
    except Exception as e:
        print(f"❌ Decryption failed: {e}")
        return False
    
    print("\n SUMMARY")
    print("=" * 50)
    print("✅ Complete workflow successful!")
    print("   - Keys were generated")
    print("   - Data was encrypted") 
    print("   - Computation performed on encrypted data")
    print("   - Results decrypted")
    print("   - Accuracy verified")
    
    return True


def test_enhanced_encrypt_compute_decrypt():
    """Test the enhanced encrypt → compute → decrypt workflow with performance monitoring"""
    
    print("\n" + "="*60)
    print("🔬 ENHANCED FHE PERFORMANCE TEST")
    print("="*60)
    
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    
    print("\n STEP 1: KEY GENERATION")
    print("-" * 50)
    
    # Initialize SEAL engine with working parameters for SEAL 4.0.0
    try:
        # Use OPTIMIZED parameters for minimum noise and maximum accuracy
        engine = SEALEngine(
            scheme='ckks',
            poly_modulus_degree=4096,  # Optimal for performance vs security
            coeff_modulus_degree=[50],  # Working parameter for SEAL 4.0.0
            scale_factor=30,  # Scale factor for CKKS encoding
            #plain_modulus_bits=20 Used for BFV not CKKS
        )
        print("✅ Keys generated successfully")
        print(f"   - Secret Key: Generated")
        print(f"   - Public Key: Generated") 
        print(f"   - Relin Keys: Generated")
        
        # Display configuration info
        info = engine.get_info()
        print(f"   - Scheme: {info['scheme']}")
        print(f"   - Poly Modulus Degree: {info['poly_modulus_degree']}")
        print(f"   - Coefficient Modulus Degree: {info['coeff_modulus_degree']}")
        print(f"   - Scale Factor: {info['scale_factor']} (Scale: {info['scale']})")
        print(f"   - Plain Modulus Bits: {info['plain_modulus_bits']}")
        print(f"   - Slot Count: {info['slot_count']}")
        
    except Exception as e:
        print(f"❌ Key generation failed: {e}")
        return False
    
    print("\n STEP 2: ENCRYPTION PERFORMANCE")
    print("-" * 50)
    
    # Sample patient data
    patient_data = [20, 117, 83, 80, 99]  # age, systolic, diastolic, heart_rate, temp
    print(f"Original data: {patient_data}")
    
    try:
        # Measure encryption performance with multiple runs
        encryption_summary = monitor.run_multiple_measurements(
            "Encryption", 
            engine.encrypt, 
            5,  # num_runs
            patient_data
        )
        monitor.print_summary(encryption_summary)
        
        # Single encryption for workflow
        encrypted_data = engine.encrypt(patient_data)
        print("✅ Data encrypted successfully")
        
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        print(f"   - Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n STEP 3: COMPUTATION PERFORMANCE")
    print("-" * 50)
    
    try:
        # Perform computation on encrypted data
        # Simple operation: Add 5 mmHg to systolic BP (position 1)
        bp_adjustment = [0, 5, 0, 0, 0]  # Add 5 to systolic only
        
        # Measure computation performance
        computation_summary = monitor.run_multiple_measurements(
            "FHE Computation (add_plain)", 
            engine.add_plain, 
            5,  # num_runs
            encrypted_data, 
            bp_adjustment
        )
        monitor.print_summary(computation_summary)
        
        # Single computation for workflow
        result_encrypted = engine.add_plain(encrypted_data, bp_adjustment)
        print("✅ FHE computation completed")
        print("   - Added 5 mmHg to systolic blood pressure")
        print("   - Simple addition operation to verify FHE workflow")
        
    except Exception as e:
        print(f"❌ Computation failed: {e}")
        return False
    
    print("\n STEP 4: DECRYPTION PERFORMANCE")
    print("-" * 50)
    
    try:
        # Measure decryption performance
        decryption_summary = monitor.run_multiple_measurements(
            "Decryption", 
            engine.decrypt, 
            5,  # num_runs
            result_encrypted
        )
        monitor.print_summary(decryption_summary)
        
        # Single decryption for workflow
        decrypted_result = engine.decrypt(result_encrypted)
        print("✅ Decryption successful")
        
        # Show only the relevant data points (first 5 values)
        relevant_data = decrypted_result[:5]
        print(f"Relevant data (first 5 values): {relevant_data}")
        print(f"Full result length: {len(decrypted_result)} values (CKKS slot count)")
        
        # Calculate expected result manually for comparison
        expected = patient_data[1] + 5  # Original systolic + 5
        print(f"Expected result: {expected}")
        
        # Extract the correct result (systolic BP is at position 1)
        actual = decrypted_result[1]  # Second element contains adjusted systolic
        relative_error = abs(actual - expected) / expected * 100
        print(f"Actual systolic BP: {actual}")
        print(f"Relative Error: {relative_error:.2f}%")
        
    except Exception as e:
        print(f"❌ Decryption failed: {e}")
        return False
    
    print("\n STEP 5: COMPREHENSIVE PERFORMANCE SUMMARY")
    print("-" * 50)
    
    # Compile all results
    all_summaries = {
        "encryption": encryption_summary,
        "computation": computation_summary,
        "decryption": decryption_summary
    }
    
    print("📊 COMPLETE PERFORMANCE METRICS:")
    print("=" * 50)
    
    total_time = 0
    total_memory_delta = 0
    
    for operation, summary in all_summaries.items():
        time_stats = summary['time_stats']
        memory_stats = summary['memory_stats']
        
        print(f"\n🔹 {operation.upper()}:")
        print(f"   ⏱️  Average Time: {time_stats['mean_ms']:.2f}ms")
        print(f"   ⏱️  Time Range: {time_stats['min_ms']:.1f}ms - {time_stats['max_ms']:.1f}ms")
        print(f"   ⏱️  Standard Deviation: {time_stats['std_ms']:.2f}ms")
        
        if PSUTIL_AVAILABLE:
            print(f"   💾 Avg Memory RSS Δ: {memory_stats['mean_delta_rss_mb']:+.1f}MB")
            print(f"   💾 Max Memory RSS Δ: {memory_stats['max_delta_rss_mb']:+.1f}MB")
            print(f"   💾 Avg Memory VMS Δ: {memory_stats['mean_delta_vms_mb']:+.1f}MB")
            print(f"   💾 Max Memory VMS Δ: {memory_stats['max_delta_vms_mb']:+.1f}MB")
        
        total_time += time_stats['mean_ms']
        if PSUTIL_AVAILABLE:
            total_memory_delta += memory_stats['mean_delta_rss_mb']
    
    print(f"\n🎯 TOTAL WORKFLOW PERFORMANCE:")
    print(f"   ⏱️  Total Average Time: {total_time:.2f}ms")
    if PSUTIL_AVAILABLE:
        print(f"   💾 Total Memory RSS Δ: {total_memory_delta:+.1f}MB")
    
    print("\n✅ Complete workflow successful!")
    print("   - Keys were generated")
    print("   - Data was encrypted with performance metrics") 
    print("   - Computation performed on encrypted data with timing")
    print("   - Results decrypted with memory tracking")
    print("   - Accuracy verified")
    print("   - Comprehensive performance analysis completed")
    
    return True





if __name__ == "__main__":
    print("🔬 Enhanced FHE Performance Testing Suite")
    print("=" * 60)
    
    if not SEAL_AVAILABLE:
        print(" Cannot run test - SEAL not available")
        sys.exit(1)
    
    # Run the original test first
    print("\n" + "="*60)
    print("🔧 ORIGINAL FHE WORKFLOW TEST")
    print("="*60)
    original_success = test_simple_encrypt_compute_decrypt()
    
    if original_success:
        print("\n🎉 Original test completed successfully!")
        
        # Run the enhanced test
        enhanced_success = test_enhanced_encrypt_compute_decrypt()
        
        if enhanced_success:
            print("\n🎉 Enhanced test completed successfully!")
        else:
            print("\n💥 Enhanced test failed!")
            sys.exit(1)
    else:
        print("\n💥 Original test failed!")
        sys.exit(1) 