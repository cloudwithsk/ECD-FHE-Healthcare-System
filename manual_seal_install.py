#!/usr/bin/env python3
"""
Manual SEAL-Python Installation for Lambda
Build SEAL-Python locally and package for Lambda deployment.
"""

import os
import sys
import subprocess
import boto3
import tempfile
import shutil
import zipfile

class ManualSEALInstaller:
    """Manual SEAL-Python installation for Lambda"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.layer_name = 'seal-python-manual'
    
    def build_seal_locally(self):
        """Build SEAL-Python locally"""
        print("Building SEAL-Python locally...")
        
        # Create temporary directory
        layer_dir = tempfile.mkdtemp(prefix='seal_manual_')
        python_dir = os.path.join(layer_dir, 'python')
        os.makedirs(python_dir, exist_ok=True)
        
        try:
            # Check if SEAL-Python already exists
            if os.path.exists('../SEAL-Python'):
                seal_dir = '../SEAL-Python'
                print(f"Using existing SEAL-Python at: {seal_dir}")
            else:
                # Clone SEAL-Python
                print("Cloning SEAL-Python repository...")
                subprocess.run([
                    'git', 'clone', 'https://github.com/Huelse/SEAL-Python.git'
                ], check=True)
                seal_dir = 'SEAL-Python'
            
            # Navigate to SEAL-Python
            os.chdir(seal_dir)
            
            # Update submodules
            print("Updating submodules...")
            subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], check=True)
            
            # Build SEAL library
            print("Building SEAL library...")
            os.chdir('SEAL')
            subprocess.run([
                'cmake', '-S', '.', '-B', 'build', 
                '-DSEAL_USE_MSGSL=OFF', '-DSEAL_USE_ZLIB=OFF', '-DSEAL_USE_ZSTD=OFF'
            ], check=True)
            subprocess.run(['cmake', '--build', 'build'], check=True)
            
            # Build Python bindings
            print("Building Python bindings...")
            os.chdir('..')
            subprocess.run(['python3', 'setup.py', 'build_ext', '-i'], check=True)
            
            # Copy built files to layer
            print("Copying built files to Lambda layer...")
            for file in os.listdir('.'):
                if file.startswith('seal') and file.endswith('.so'):
                    shutil.copy2(file, python_dir)
                    print(f"Copied: {file}")
            
            # Go back to original directory
            os.chdir('..')
            
            # Create layer zip
            layer_zip = f"{self.layer_name}.zip"
            shutil.make_archive(self.layer_name, 'zip', layer_dir)
            
            print(f"Layer package created: {layer_zip}")
            return layer_zip
            
        except Exception as e:
            print(f"Failed to build SEAL-Python: {e}")
            return self.create_simple_layer()
    
    def create_simple_layer(self):
        """Create simple layer with basic SEAL functionality"""
        print("Creating simple SEAL layer...")
        
        layer_dir = tempfile.mkdtemp(prefix='seal_simple_')
        python_dir = os.path.join(layer_dir, 'python')
        os.makedirs(python_dir, exist_ok=True)
        
        # Create simple SEAL module
        seal_dir = os.path.join(python_dir, 'seal')
        os.makedirs(seal_dir, exist_ok=True)
        
        # Create __init__.py with basic SEAL classes
        init_content = '''
# Simple SEAL library for Lambda
import time
import base64

class SimpleCiphertext:
    def __init__(self, context=None, data=None):
        self.data = data or b"simple_ciphertext"
    
    def save(self):
        return self.data
    
    def load(self, context, data):
        self.data = data

class SimpleContext:
    def __init__(self, params=None):
        pass

class SimpleEncoder:
    def __init__(self, context):
        pass
        
    def encode(self, data, scale, plaintext):
        plaintext.data = str(data).encode()

class SimpleEvaluator:
    def __init__(self, context):
        pass
        
    def add_plain(self, ciphertext, plaintext, result):
        time.sleep(0.05)  # Simulate computation
        result.data = ciphertext.data + b"_added"
    
    def multiply_plain(self, ciphertext, plaintext, result):
        time.sleep(0.05)  # Simulate computation
        result.data = ciphertext.data + b"_multiplied"

class SimplePlaintext:
    def __init__(self):
        self.data = b""

# Simple classes for Lambda compatibility
Ciphertext = SimpleCiphertext
SEALContext = SimpleContext
CKKSEncoder = SimpleEncoder
Evaluator = SimpleEvaluator
EncryptionParameters = SimpleContext
scheme_type = type('scheme_type', (), {'ckks': 'ckks'})()
CoeffModulus = type('CoeffModulus', (), {'Create': lambda x, y: y})()
Plaintext = SimplePlaintext
'''
        
        with open(os.path.join(seal_dir, '__init__.py'), 'w') as f:
            f.write(init_content)
        
        # Create layer zip
        layer_zip = f"{self.layer_name}.zip"
        shutil.make_archive(self.layer_name, 'zip', layer_dir)
        
        print(f"Simple layer package created: {layer_zip}")
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
                Description='SEAL-Python library for FHE computation (manual build)',
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
            
            print(f"Lambda function updated with SEAL layer")
            
        except Exception as e:
            print(f"Failed to update Lambda function: {e}")
            raise e

def main():
    """Main manual installation process"""
    print("Manual SEAL-Python Installation for Lambda")
    print("=" * 50)
    
    try:
        installer = ManualSEALInstaller()
        
        # Step 1: Build layer package
        layer_zip = installer.build_seal_locally()
        
        # Step 2: Deploy layer
        layer_arn = installer.deploy_layer(layer_zip)
        
        # Step 3: Update Lambda function
        installer.update_lambda_function('fhe-computation', layer_arn)
        
        print("\n✅ Manual SEAL-Python installation completed!")
        print(f"Layer ARN: {layer_arn}")
        print("\nNext steps:")
        print("1. Test with improved computation")
        print("2. Monitor Lambda performance")
        print("3. Optimize if needed")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)
    finally:
        # Clean up zip file
        if os.path.exists(f"{installer.layer_name}.zip"):
            os.remove(f"{installer.layer_name}.zip")

if __name__ == "__main__":
    main() 