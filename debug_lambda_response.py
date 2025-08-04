#!/usr/bin/env python3
"""
Debug Lambda Response
Check what the Lambda function is actually returning.
"""

import json
import boto3

def debug_lambda_response():
    """Debug Lambda response to see what's being returned"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Test payload
    test_payload = {
        "operation": "add_plain",
        "encrypted_data": "dGVzdF9kYXRh",  # base64 test data
        "plaintext_data": [0, 5, 0, 0, 0],
        "context_params": {
            "scheme": "ckks",
            "poly_modulus_degree": 4096,
            "coeff_modulus_degree": [50],
            "scale_factor": 30
        }
    }
    
    try:
        print("Testing Lambda function...")
        print(f"Payload: {json.dumps(test_payload, indent=2)}")
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName='fhe-computation',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        print(f"\nLambda Response Status: {response['StatusCode']}")
        
        # Read response payload
        response_payload = json.loads(response['Payload'].read())
        print(f"\nFull Response Payload:")
        print(json.dumps(response_payload, indent=2))
        
        # Check for 'body' field
        if 'body' in response_payload:
            print(f"\nBody content:")
            body_content = json.loads(response_payload['body'])
            print(json.dumps(body_content, indent=2))
            
            # Check for 'result' field
            if 'result' in body_content:
                print(f"\n✅ Result field found: {body_content['result'][:50]}...")
            else:
                print(f"\n❌ No 'result' field in body")
                print(f"Available fields: {list(body_content.keys())}")
        else:
            print(f"\n❌ No 'body' field in response")
            print(f"Available fields: {list(response_payload.keys())}")
        
    except Exception as e:
        print(f"❌ Lambda invocation failed: {e}")

if __name__ == "__main__":
    debug_lambda_response() 