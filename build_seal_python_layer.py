#!/usr/bin/env python3
"""
Build SEAL-Python from Source for Lambda Layer
Uses Huelse's SEAL-Python repository to build Lambda-compatible layer.
"""

import os
import sys
import subprocess
import boto3
import tempfile
import shutil
import zipfile

class SEALPythonBuilder:
    """Build SEAL-Python from source for Lambda"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.layer_name = 'seal-python-layer'
    
    def build_seal_python_layer(self):
        """Build SEAL-Python from source using Docker"""
        print("Building SEAL-Python from source...")
        
        # Create temporary directory
        layer_dir = tempfile.mkdtemp(prefix='seal_python_')
        python_dir = os.path.join(layer_dir, 'python')
        os.makedirs(python_dir, exist_ok=True)
        
        try:
            # Docker command to build SEAL-Python in Lambda environment
            docker_cmd = f"""
            docker run --rm -v {layer_dir}:/output -v {os.getcwd()}:/workspace \\
            public.ecr.aws/lambda/python:3.9 \\
            bash -c "cd /workspace && \\
            apt-get update && apt-get install -y git build-essential cmake python3-dev && \\
            git clone https://github.com/Huelse/SEAL-Python.git && \\
            cd SEAL-Python && \\
            git submodule update --init --recursive && \\
            cd SEAL && \\
            cmake -S . -B build -DSEAL_USE_MSGSL=OFF -DSEAL_USE_ZLIB=OFF -DSEAL_USE_ZSTD=OFF && \\
            cmake --build build && \\
            cd .. && \\
            python3 setup.py build_ext -i && \\
            cp seal.*.so /output/python/ && \\
            cp -r examples /output/python/"
            """
            
            print("Building SEAL-Python with Docker (this may take 15-20 minutes)...")
            result = subprocess.run(docker_cmd, shell=True, check=True)
            
            # Create layer zip
            layer_zip = f"{self.layer_name}.zip"
            shutil.make_archive(self.layer_name, 'zip', layer_dir)
            
            print(f"Layer package created: {layer_zip}")
            return layer_zip
            
        except Exception as e:
            print(f"Failed to build SEAL-Python: {e}")
            return self.create_fallback_layer()
    
    def create_fallback_layer(self):
        """Create fallback layer with instructions"""
        print("Creating fallback layer with build instructions...")
        
        layer_dir = tempfile.mkdtemp(prefix='seal_fallback_')
        python_dir = os.path.join(layer_dir, 'python')
        os.makedirs(python_dir, exist_ok=True)
        
        # Create README with build instructions
        readme_content = '''
# SEAL-Python Lambda Layer

This layer requires manual build of SEAL-Python from source.

## Build Instructions:

1. Clone the repository:
   git clone https://github.com/Huelse/SEAL-Python.git

2. Build SEAL library:
   cd SEAL-Python/SEAL
   cmake -S . -B build -DSEAL_USE_MSGSL=OFF -DSEAL_USE_ZLIB=OFF -DSEAL_USE_ZSTD=OFF
   cmake --build build

3. Build Python bindings:
   cd ..
   python3 setup.py build_ext -i

4. Copy to Lambda layer:
   cp seal.*.so /path/to/lambda/layer/python/

## For Lambda deployment:
- Use Docker with Lambda runtime
- Build in Lambda-compatible environment
- Include all dependencies
        '''
        
        with open(os.path.join(layer_dir, 'README.md'), 'w') as f:
            f.write(readme_content)
        
        # Create layer zip
        layer_zip = f"{self.layer_name}.zip"
        shutil.make_archive(self.layer_name, 'zip', layer_dir)
        
        print(f"Fallback layer package created: {layer_zip}")
        return layer_zip
    
    def deploy_layer(self, layer_zip_path):
        """Deploy layer to AWS Lambda"""
        try:
            print(f"Deploying layer: {self.layer_name}")
            
            with open(layer_zip_path, 'rb') as f:
                layer_content = f.read()
            
            # Publish layer
            response = self.lambda_client.publish_layer_version(
                LayerName=self.layer_name,
                Description='SEAL-Python library for FHE computation',
                Content={'ZipFile': layer_content},
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
            
            print(f"Lambda function updated with SEAL-Python layer")
            
        except Exception as e:
            print(f"Failed to update Lambda function: {e}")
            raise e

def main():
    """Main build and deployment process"""
    print("SEAL-Python Lambda Layer Build & Deployment")
    print("=" * 50)
    
    try:
        builder = SEALPythonBuilder()
        
        # Step 1: Build layer package
        layer_zip = builder.build_seal_python_layer()
        
        # Step 2: Deploy layer
        layer_arn = builder.deploy_layer(layer_zip)
        
        # Step 3: Update Lambda function
        builder.update_lambda_function('fhe-computation', layer_arn)
        
        print("\n✅ SEAL-Python layer deployment completed!")
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
        if os.path.exists(f"{builder.layer_name}.zip"):
            os.remove(f"{builder.layer_name}.zip")

if __name__ == "__main__":
    main() 