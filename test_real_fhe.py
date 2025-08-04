#!/usr/bin/env python3
"""
Quick Real FHE Test
Test real FHE computation locally to verify it works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import SEALEngine
import time

def test_real_fhe():
    """Test real FHE computation locally"""
    print("Testing Real FHE Computation")
    print("=" * 40)
    
    # Initialize real SEAL engine
    engine = SEALEngine(
        scheme='ckks',
        poly_modulus_degree=4096,
        coeff_modulus_degree=[50],
        scale_factor=30
    )
    
    # Test data
    original_data = [26, 118, 76, 80, 97.6]
    adjustment = [0, 5, 0, 0, 0]
    
    print(f"Original: {original_data}")
    print(f"Adjustment: {adjustment}")
    
    # Real FHE computation
    start_time = time.time()
    
    # Encrypt
    encrypted = engine.encrypt(original_data)
    encryption_time = (time.time() - start_time) * 1000
    
    # Add plaintext
    start_compute = time.time()
    result = engine.add_plain(encrypted, adjustment)
    compute_time = (time.time() - start_compute) * 1000
    
    # Decrypt
    start_decrypt = time.time()
    decrypted = engine.decrypt(result)
    decrypt_time = (time.time() - start_decrypt) * 1000
    
    total_time = (time.time() - start_time) * 1000
    
    print(f"\nResults:")
    print(f"Decrypted: {decrypted[:5]}")
    print(f"Expected: {[original_data[i] + adjustment[i] for i in range(5)]}")
    
    print(f"\nPerformance:")
    print(f"Encryption: {encryption_time:.2f}ms")
    print(f"Computation: {compute_time:.2f}ms")
    print(f"Decryption: {decrypt_time:.2f}ms")
    print(f"Total: {total_time:.2f}ms")
    
    # Accuracy check
    expected_systolic = original_data[1] + adjustment[1]
    actual_systolic = decrypted[1]
    error = abs(actual_systolic - expected_systolic) / expected_systolic * 100
    
    print(f"\nAccuracy:")
    print(f"Expected systolic: {expected_systolic}")
    print(f"Actual systolic: {actual_systolic}")
    print(f"Error: {error:.2f}%")
    
    if error < 1.0:
        print("✅ Real FHE working correctly!")
        return True
    else:
        print("⚠️ High error - check parameters")
        return False

if __name__ == "__main__":
    success = test_real_fhe()
    if success:
        print("\n🎉 Real FHE computation verified!")
    else:
        print("\n❌ Real FHE needs adjustment") 