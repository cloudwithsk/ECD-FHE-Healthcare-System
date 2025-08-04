#!/usr/bin/env python3
"""
Fix Layer Version Conflict
Remove old layer version and keep only the new one.
"""

import boto3

def fix_layer_conflict():
    """Remove old layer version from Lambda function"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        print("Fixing layer version conflict...")
        
        # Get current function configuration
        response = lambda_client.get_function(FunctionName='fhe-computation')
        current_layers = response['Configuration'].get('Layers', [])
        
        print(f"Current layers: {[layer['Arn'] for layer in current_layers]}")
        
        # Keep only the newest layer version (version 3)
        new_layers = []
        for layer in current_layers:
            if 'seal-python-manual:3' in layer['Arn']:
                new_layers.append(layer['Arn'])
                print(f"Keeping: {layer['Arn']}")
            else:
                print(f"Removing: {layer['Arn']}")
        
        # Update function with only new layer
        lambda_client.update_function_configuration(
            FunctionName='fhe-computation',
            Layers=new_layers
        )
        
        print("✅ Layer conflict fixed!")
        print(f"Updated layers: {new_layers}")
        
    except Exception as e:
        print(f"❌ Failed to fix layer conflict: {e}")

if __name__ == "__main__":
    fix_layer_conflict() 