#!/usr/bin/env python3
"""
AWS Lambda Handler for FHE Computation
This Lambda function receives encrypted data, performs homomorphic operations,
and returns encrypted results without ever seeing the plaintext data.
"""

import json
import base64
import time
import sys
import os
from typing import Dict, Any, List

# Lambda layer will contain the SEAL library
try:
    from seal import *
    SEAL_AVAILABLE = True
except ImportError:
    SEAL_AVAILABLE = False
    print("SEAL not available in Lambda - using mock mode")

def lambda_handler(event, context):
    """
    AWS Lambda handler for FHE computation
    
    Expected event format:
    {
        "operation": "add_plain",
        "encrypted_data": "base64_encoded_ciphertext",
        "plaintext_data": [0, 5, 0, 0, 0],
        "context_params": {
            "scheme": "ckks",
            "poly_modulus_degree": 4096,
            "coeff_modulus_degree": [50],
            "scale_factor": 30
        }
    }
    """
    
    print(f"🔐 FHE Lambda Handler Started")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Parse the request
    try:
        operation = event.get('operation', 'add_plain')
        encrypted_data_b64 = event.get('encrypted_data')
        plaintext_data = event.get('plaintext_data', [0, 5, 0, 0, 0])
        context_params = event.get('context_params', {
            'scheme': 'ckks',
            'poly_modulus_degree': 4096,
            'coeff_modulus_degree': [50],
            'scale_factor': 30
        })
        
        if not encrypted_data_b64:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing encrypted_data parameter'})
            }
            
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Invalid request format: {str(e)}'})
        }
    
    # Initialize SEAL context
    try:
        if SEAL_AVAILABLE:
            # Create SEAL context with provided parameters
            context = create_seal_context(context_params)
            print("✅ SEAL context created successfully")
        else:
            print("⚠️ Using mock mode - SEAL not available")
            context = None
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to initialize SEAL: {str(e)}'})
        }
    
    # Perform FHE computation
    try:
        start_time = time.time()
        
        if SEAL_AVAILABLE:
            # Decode base64 encrypted data
            encrypted_data_bytes = base64.b64decode(encrypted_data_b64)
            
            # Perform real FHE computation
            result_b64 = real_fhe_computation(context, encrypted_data_bytes, plaintext_data, operation)
            
        else:
            # Mock computation for testing
            result_b64 = mock_computation(encrypted_data_b64, plaintext_data, operation)
        
        computation_time = (time.time() - start_time) * 1000  # Convert to ms
        
        print(f"✅ Computation completed in {computation_time:.2f}ms")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'result': result_b64,
                'computation_time_ms': computation_time,
                'operation': operation,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'lambda_memory_mb': context.memory_limit_in_mb if context else 0,
                'lambda_timeout_ms': context.get_remaining_time_in_millis() if context else 0
            })
        }
        
    except Exception as e:
        print(f"❌ Computation failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Computation failed: {str(e)}'})
        }

def create_seal_context(params: Dict[str, Any]):
    """Create SEAL context with specified parameters"""
    poly_modulus_degree = params.get('poly_modulus_degree', 4096)
    coeff_modulus_degree = params.get('coeff_modulus_degree', [50])
    scale_factor = params.get('scale_factor', 30)
    
    # Create encryption parameters
    parms = EncryptionParameters(scheme_type.ckks)
    parms.set_poly_modulus_degree(poly_modulus_degree)
    
    # Set coefficient modulus
    coeff_modulus = CoeffModulus.Create(poly_modulus_degree, coeff_modulus_degree)
    parms.set_coeff_modulus(coeff_modulus)
    
    # Set scale
    parms.set_scale(2**scale_factor)
    
    # Create context
    context = SEALContext(parms)
    return context

def add_plain_computation(context, ciphertext, plaintext_data):
    """Add plaintext to encrypted data"""
    # Create encoder
    encoder = CKKSEncoder(context)
    
    # Create evaluator
    evaluator = Evaluator(context)
    
    # Encode plaintext data
    plaintext = Plaintext()
    encoder.encode(plaintext_data, 2**30, plaintext)
    
    # Add plaintext to ciphertext
    result = Ciphertext()
    evaluator.add_plain(ciphertext, plaintext, result)
    
    return result

def multiply_plain_computation(context, ciphertext, plaintext_data):
    """Multiply encrypted data by plaintext"""
    # Create encoder
    encoder = CKKSEncoder(context)
    
    # Create evaluator
    evaluator = Evaluator(context)
    
    # Encode plaintext data
    plaintext = Plaintext()
    encoder.encode(plaintext_data, 2**30, plaintext)
    
    # Multiply ciphertext by plaintext
    result = Ciphertext()
    evaluator.multiply_plain(ciphertext, plaintext, result)
    
    return result

def mock_computation(encrypted_data_b64: str, plaintext_data: List[float], operation: str) -> str:
    """Mock computation for testing when SEAL is not available"""
    print(f"🔧 Mock computation: {operation} with {plaintext_data}")
    
    # Simulate computation time
    time.sleep(0.1)
    
    # Return mock result (just echo back the input for testing)
    return encrypted_data_b64


def real_fhe_computation(context, encrypted_data_bytes, plaintext_data, operation):
    """Perform real FHE computation with SEAL"""
    try:
        print(f"🔐 Real FHE computation: {operation}")
        
        # Load ciphertext from bytes
        ciphertext = Ciphertext()
        ciphertext.load(context, encrypted_data_bytes)
        
        # Perform the requested operation
        if operation == 'add_plain':
            result_ciphertext = add_plain_computation(context, ciphertext, plaintext_data)
        elif operation == 'multiply_plain':
            result_ciphertext = multiply_plain_computation(context, ciphertext, plaintext_data)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
        # Serialize result to bytes
        result_bytes = result_ciphertext.save()
        result_b64 = base64.b64encode(result_bytes).decode('utf-8')
        
        return result_b64
        
    except Exception as e:
        print(f"❌ Real FHE computation failed: {e}")
        raise e

# Test function for local development
if __name__ == "__main__":
    # Test event
    test_event = {
        "operation": "add_plain",
        "encrypted_data": "dGVzdF9kYXRh",  # base64 encoded "test_data"
        "plaintext_data": [0, 5, 0, 0, 0],
        "context_params": {
            "scheme": "ckks",
            "poly_modulus_degree": 4096,
            "coeff_modulus_degree": [50],
            "scale_factor": 30
        }
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}") 