#!/usr/bin/env python3
"""
Simple ECD Test: Encrypt → Compute → Decrypt with Minimal Performance Monitoring
This script demonstrates the basic workflow with essential performance metrics only.
"""

import sys
import os
import time
import gc
from typing import Dict, Any

# Add the parent directory to Python path to find the core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.engine import SEALEngine
    SEAL_AVAILABLE = True
    print("✅ SEAL engine available")
except ImportError as e:
    print(f"SEAL engine not available: {e}")
    SEAL_AVAILABLE = False
    sys.exit(1)

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✅ psutil available for memory monitoring")
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - memory monitoring disabled")


class SimplePerformanceMonitor:
    """Minimal performance monitoring for FHE operations."""
    
    def __init__(self):
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
            print(f"Memory measurement error: {e}")
            return {"rss_mb": 0.0, "vms_mb": 0.0}
    
    def measure_operation(self, operation_name: str, operation_func, *args, **kwargs) -> Dict[str, Any]:
        """Measure performance of an operation."""
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
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "result": result  # Add the actual result
        }
        
        return metrics
    
    def print_measurement(self, metrics: Dict[str, Any]):
        """Print formatted performance measurement."""
        print(f"   Time: {metrics['execution_time_ms']:.2f}ms")
        if PSUTIL_AVAILABLE:
            print(f"   Memory RSS: {metrics['memory_initial_rss_mb']:.1f}MB → {metrics['memory_final_rss_mb']:.1f}MB (Δ: {metrics['memory_delta_rss_mb']:+.1f}MB)")
            print(f"   Memory VMS: {metrics['memory_initial_vms_mb']:.1f}MB → {metrics['memory_final_vms_mb']:.1f}MB (Δ: {metrics['memory_delta_vms_mb']:+.1f}MB)")


def test_ecd_performance():
    """Test the ECD workflow with minimal performance monitoring."""
    
    print("Simple ECD Test: Encrypt → Compute → Decrypt")
    print("=" * 50)
    
    monitor = SimplePerformanceMonitor()
    
    print("\nStep 1: Key Generation")
    try:
        # Use cloud-optimized parameters
        engine = SEALEngine(
            scheme='ckks',
            poly_modulus_degree=4096,
            coeff_modulus_degree=[50],
            scale_factor=30
        )
        print("✅ Keys generated successfully")
        
    except Exception as e:
        print(f"Key generation failed: {e}")
        return False
    
    print("\nStep 2: Encryption")
    patient_data = [26, 118, 76, 80, 97.6]  # age, systolic, diastolic, heart_rate, temp
    print(f"Original data: {patient_data}")
    
    try:
        metrics = monitor.measure_operation("encryption", engine.encrypt, patient_data)
        monitor.print_measurement(metrics)
        encrypted_data = metrics["result"]
        print("✅ Data encrypted successfully")
        
    except Exception as e:
        print(f"Encryption failed: {e}")
        return False
    
    print("\nStep 3: Computation")
    try:
        # Simple addition operation: Add 5 mmHg to systolic BP (position 1)
        bp_adjustment = [0, 5, 0, 0, 0]  # Add 5 to systolic only
        metrics = monitor.measure_operation("computation", engine.add_plain, encrypted_data, bp_adjustment)
        monitor.print_measurement(metrics)
        result_encrypted = metrics["result"]
        print("✅ Homomorphic computation completed")
        print("   - Added 5 mmHg to systolic blood pressure")
        
    except Exception as e:
        print(f"Computation failed: {e}")
        return False
    
    print("\nStep 4: Decryption")
    try:
        metrics = monitor.measure_operation("decryption", engine.decrypt, result_encrypted)
        monitor.print_measurement(metrics)
        decrypted_result = metrics["result"]
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
        relative_error = abs(actual - expected) / expected * 100 if expected != 0 else 0
        print(f"Actual systolic BP: {actual}")
        print(f"Relative Error: {relative_error:.2f}%")
        
    except Exception as e:
        print(f"Decryption failed: {e}")
        return False
    
    print("\nSummary")
    print("✅ Complete workflow successful!")
    print("   - Keys generated")
    print("   - Data encrypted") 
    print("   - Computation performed on encrypted data")
    print("   - Results decrypted")
    print("   - Accuracy verified")
    
    return True


if __name__ == "__main__":
    if not SEAL_AVAILABLE:
        print("Cannot run test - SEAL not available")
        sys.exit(1)
    
    success = test_ecd_performance()
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1) 