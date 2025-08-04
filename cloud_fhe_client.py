#!/usr/bin/env python3
"""
Cloud FHE Client - Integrates with AWS Lambda for FHE computation
This script extends your local ECD workflow to use cloud computation.
"""

import sys
import os
import time
import base64
import json
import boto3
import io
import tempfile
from typing import Dict, Any, List

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.engine import SEALEngine
    import seal
    SEAL_AVAILABLE = True
    print("✅ SEAL engine available locally")
except ImportError as e:
    print(f"SEAL engine not available: {e}")
    SEAL_AVAILABLE = False
    sys.exit(1)

# AWS Lambda client
try:
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    AWS_AVAILABLE = True
    print("✅ AWS Lambda client available")
except Exception as e:
    print(f"AWS Lambda not available: {e}")
    AWS_AVAILABLE = False


def serialize_ciphertext(ciphertext):
    """Serialize ciphertext to bytes using temporary file"""
    # Create temporary file with .seal extension
    with tempfile.NamedTemporaryFile(delete=False, suffix='.seal') as temp_file:
        temp_filename = temp_file.name
    
    try:
        # Save ciphertext to file (SEAL requires string filename)
        ciphertext.save(temp_filename)
        
        # Read file content as bytes for transmission
        with open(temp_filename, 'rb') as f:
            encrypted_bytes = f.read()
        
        return encrypted_bytes
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)


def deserialize_ciphertext(encrypted_bytes, seal_context):
    """Deserialize bytes to ciphertext using temporary file"""
    # Write bytes to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.seal') as temp_file:
        temp_file.write(encrypted_bytes)
        temp_filename = temp_file.name
    
    try:
        # Load ciphertext from file
        ciphertext = seal.Ciphertext()
        ciphertext.load(seal_context, temp_filename)
        
        return ciphertext
    finally:
        # Clean up
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)


class CloudFHEProcessor:
    """Process FHE operations using AWS Lambda"""
    
    def __init__(self, lambda_function_name='fhe-computation'):
        self.lambda_function_name = lambda_function_name
        self.local_engine = None
        self.setup_local_engine()
    
    def setup_local_engine(self):
        """Setup local SEAL engine for encryption/decryption"""
        try:
            self.local_engine = SEALEngine(
                scheme='ckks',
                poly_modulus_degree=2048,
                coeff_modulus_degree=[40],
                scale_factor=20
            )
            print("✅ Local SEAL engine initialized")
        except Exception as e:
            print(f"❌ Failed to initialize local engine: {e}")
            raise e
    
    def encrypt_for_cloud(self, data: List[float]) -> str:
        """Encrypt data locally and prepare for cloud transmission"""
        try:
            # Encrypt data using local engine
            encrypted_data = self.local_engine.encrypt(data)
            
            # Serialize to base64 for transmission using file-based approach
            encrypted_bytes = serialize_ciphertext(encrypted_data)
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            print(f"✅ Data encrypted for cloud transmission")
            return encrypted_b64
            
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            raise e
    
    def send_to_cloud(self, encrypted_data_b64: str, operation: str, plaintext_data: List[float]) -> Dict[str, Any]:
        """Send encrypted data to AWS Lambda for computation"""
        if not AWS_AVAILABLE:
            raise Exception("AWS Lambda not available")
        
        try:
            # Prepare payload for Lambda
            payload = {
                "operation": operation,
                "encrypted_data": encrypted_data_b64,
                "plaintext_data": plaintext_data,
                "context_params": {
                    "scheme": "ckks",
                    "poly_modulus_degree": 2048,
                    "coeff_modulus_degree": [40],
                    "scale_factor": 20
                }
            }
            
            print(f"🚀 Sending to AWS Lambda: {operation} operation")
            
            # Invoke Lambda function
            response = lambda_client.invoke(
                FunctionName=self.lambda_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                print(f"✅ Cloud computation completed")
                # Lambda returns {'statusCode': 200, 'body': json_string}
                if 'body' in response_payload:
                    return json.loads(response_payload['body'])
                else:
                    return response_payload
            else:
                raise Exception(f"Lambda invocation failed: {response_payload}")
                
        except Exception as e:
            print(f"❌ Cloud computation failed: {e}")
            raise e
    
    def decrypt_from_cloud(self, encrypted_result_b64: str) -> List[float]:
        """Decrypt result from cloud computation"""
        try:
            # Decode base64 result
            encrypted_bytes = base64.b64decode(encrypted_result_b64)
            
            # Load ciphertext using file-based approach
            ciphertext = deserialize_ciphertext(encrypted_bytes, self.local_engine.context)
            
            # Decrypt using local engine
            decrypted_result = self.local_engine.decrypt(ciphertext)
            
            print(f"✅ Result decrypted from cloud")
            return decrypted_result
            
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            raise e
    
    def process_cloud_fhe(self, data: List[float], operation: str, plaintext_data: List[float]) -> Dict[str, Any]:
        """Complete cloud FHE workflow: Encrypt → Cloud Compute → Decrypt"""
        
        print(f"\n🌐 Cloud FHE Workflow: {operation}")
        print("=" * 50)
        
        # Step 1: Encrypt locally
        start_time = time.time()
        encrypted_b64 = self.encrypt_for_cloud(data)
        encryption_time = (time.time() - start_time) * 1000
        
        # Step 2: Send to cloud for computation
        cloud_start = time.time()
        cloud_result = self.send_to_cloud(encrypted_b64, operation, plaintext_data)
        cloud_time = (time.time() - cloud_start) * 1000
        
        # Step 3: Decrypt result locally
        decrypt_start = time.time()
        decrypted_result = self.decrypt_from_cloud(cloud_result['result'])
        decryption_time = (time.time() - decrypt_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        # Compile results
        results = {
            'original_data': data,
            'operation': operation,
            'plaintext_operand': plaintext_data,
            'decrypted_result': decrypted_result,
            'performance': {
                'encryption_time_ms': encryption_time,
                'cloud_computation_time_ms': cloud_result.get('computation_time_ms', 0),
                'network_time_ms': cloud_time - cloud_result.get('computation_time_ms', 0),
                'decryption_time_ms': decryption_time,
                'total_time_ms': total_time
            },
            'cloud_metrics': cloud_result
        }
        
        return results


def test_cloud_fhe_workflow():
    """Test the complete cloud FHE workflow"""
    
    print("🌐 Cloud FHE Test: Local Encrypt → Cloud Compute → Local Decrypt")
    print("=" * 60)
    
    if not AWS_AVAILABLE:
        print("❌ AWS Lambda not available - cannot test cloud workflow")
        return False
    
    try:
        # Initialize cloud processor
        processor = CloudFHEProcessor()
        
        # Test data (same as your ECD_fhe_new.py)
        patient_data = [45, 120, 80, 72, 98.6]  # age, systolic, diastolic, heart_rate, temp
        bp_adjustment = [0, 5, 0, 0, 0]  # Add 5 to systolic BP
        
        # SEAL parameters
        seal_params = {
            "scheme": "ckks",
            "poly_modulus_degree": 2048,
            "coeff_modulus_degree": [40],
            "scale_factor": 20
        }
        
        print(f"🔧 SEAL Parameters:")
        print(f"   Scheme: {seal_params['scheme']}")
        print(f"   Poly Modulus Degree: {seal_params['poly_modulus_degree']}")
        print(f"   Coeff Modulus: {seal_params['coeff_modulus_degree']}")
        print(f"   Scale Factor: {seal_params['scale_factor']}")
        print(f"\n📊 Test Data:")
        print(f"   Original patient data: {patient_data}")
        print(f"   Operation: Add {bp_adjustment} to encrypted data")
        
        # Process in cloud
        results = processor.process_cloud_fhe(
            data=patient_data,
            operation='add_plain',
            plaintext_data=bp_adjustment
        )
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Original: {results['original_data']}")
        print(f"   Operation: {results['operation']} with {results['plaintext_operand']}")
        print(f"   Result: {results['decrypted_result'][:5]} (first 5 values)")
        
        # Save parameters for recording
        print(f"\n📝 Parameters Used:")
        print(f"   SEAL Scheme: {seal_params['scheme']}")
        print(f"   Poly Modulus Degree: {seal_params['poly_modulus_degree']}")
        print(f"   Coeff Modulus: {seal_params['coeff_modulus_degree']}")
        print(f"   Scale Factor: {seal_params['scale_factor']}")
        print(f"   Test Data: {patient_data}")
        print(f"   Operation: {bp_adjustment}")
        
        # Performance analysis
        perf = results['performance']
        print(f"\n⏱️ Performance Metrics:")
        print(f"   Local Encryption: {perf['encryption_time_ms']:.2f}ms")
        print(f"   Cloud Computation: {perf['cloud_computation_time_ms']:.2f}ms")
        print(f"   Network Overhead: {perf['network_time_ms']:.2f}ms")
        print(f"   Local Decryption: {perf['decryption_time_ms']:.2f}ms")
        print(f"   Total Time: {perf['total_time_ms']:.2f}ms")
        
        # Accuracy verification
        expected_systolic = patient_data[1] + bp_adjustment[1]  # 118 + 5 = 123
        actual_systolic = results['decrypted_result'][1]
        relative_error = abs(actual_systolic - expected_systolic) / expected_systolic * 100
        
        print(f"\n🎯 Accuracy Check:")
        print(f"   Expected systolic BP: {expected_systolic}")
        print(f"   Actual systolic BP: {actual_systolic}")
        print(f"   Relative Error: {relative_error:.2f}%")
        
        if relative_error < 1.0:
            print("✅ Accuracy within acceptable range (< 1% error)")
        else:
            print("⚠️ Higher than expected error - check parameters")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloud FHE test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_cloud_fhe_workflow()
    
    if success:
        print("\n🎉 Cloud FHE test completed successfully!")
    else:
        print("\n❌ Cloud FHE test failed!")
        sys.exit(1) 