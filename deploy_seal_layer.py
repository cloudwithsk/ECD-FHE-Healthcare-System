#!/usr/bin/env python3
"""
Deploy SEAL Library as AWS Lambda Layer
This script packages and deploys the SEAL library for real FHE computation in Lambda.
"""

import os
import sys
import subprocess
import boto3
import json
import tempfile
import shutil
from pathlib import Path

class SEALLayerDeployer:
    """Deploy SEAL library as Lambda layer"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.layer_name = 'seal-fhe-layer'
        self.layer_version = 1
        
    def create_seal_layer_package(self):
        """Create Lambda layer package with SEAL library"""
        print("Building SEAL Lambda layer...")
        
        # Create temporary directory for layer
        layer_dir = tempfile.mkdtemp(prefix='seal_layer_')
        python_dir = os.path.join(layer_dir, 'python')
        os.makedirs(python_dir, exist_ok=True)
        
        try:
            # Install SEAL Python bindings
            print("Installing SEAL Python bindings...")
            subprocess.run([
                'pip', 'install', 'seal-python',
                '-t', python_dir,
                '--platform', 'manylinux2014_x86_64',
                '--only-binary=:all:'
            ], check=True)
            
            # Create layer zip
            layer_zip = f"{self.layer_name}.zip"
            shutil.make_archive(self.layer_name, 'zip', layer_dir)
            
            print(f"Layer package created: {layer_zip}")
            return layer_zip
            
        except Exception as e:
            print(f"Failed to create layer package: {e}")
            raise e
        finally:
            # Clean up temp directory
            shutil.rmtree(layer_dir, ignore_errors=True)
    
    def deploy_layer(self, layer_zip_path):
        """Deploy layer to AWS Lambda"""
        try:
            print(f"Deploying layer: {self.layer_name}")
            
            with open(layer_zip_path, 'rb') as f:
                layer_content = f.read()
            
            # Publish layer
            response = self.lambda_client.publish_layer_version(
                LayerName=self.layer_name,
                Description='SEAL library for FHE computation',
                Content={
                    'ZipFile': layer_content
                },
                CompatibleRuntimes=['python3.8', 'python3.9', 'python3.10', 'python3.11'],
                CompatibleArchitectures=['x86_64']
            )
            
            layer_arn = response['LayerVersionArn']
            print(f"Layer deployed successfully: {layer_arn}")
            return layer_arn
            
        except Exception as e:
            print(f"Failed to deploy layer: {e}")
            raise e
    
    def update_lambda_function(self, function_name, layer_arn):
        """Update Lambda function to use SEAL layer"""
        try:
            print(f"Updating Lambda function: {function_name}")
            
            # Get current function configuration
            response = self.lambda_client.get_function(FunctionName=function_name)
            current_layers = response['Configuration'].get('Layers', [])
            
            # Add SEAL layer
            new_layers = [layer_arn] + [layer['Arn'] for layer in current_layers]
            
            # Update function
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Layers=new_layers
            )
            
            print(f"Lambda function updated with SEAL layer")
            
        except Exception as e:
            print(f"Failed to update Lambda function: {e}")
            raise e

def main():
    """Main deployment process"""
    print("SEAL Lambda Layer Deployment")
    print("=" * 40)
    
    try:
        deployer = SEALLayerDeployer()
        
        # Step 1: Create layer package
        layer_zip = deployer.create_seal_layer_package()
        
        # Step 2: Deploy layer
        layer_arn = deployer.deploy_layer(layer_zip)
        
        # Step 3: Update Lambda function
        deployer.update_lambda_function('fhe-computation', layer_arn)
        
        print("\n✅ SEAL layer deployment completed!")
        print(f"Layer ARN: {layer_arn}")
        print("\nNext steps:")
        print("1. Test with real FHE computation")
        print("2. Monitor Lambda performance")
        print("3. Optimize if needed")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)
    finally:
        # Clean up zip file
        if os.path.exists(f"{deployer.layer_name}.zip"):
            os.remove(f"{deployer.layer_name}.zip")

if __name__ == "__main__":
    main() 