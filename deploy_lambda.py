#!/usr/bin/env python3
"""
AWS Lambda Deployment Script for FHE Computation
This script packages and deploys the FHE Lambda function to AWS.
"""

import boto3
import json
import zipfile
import os
import subprocess
import shutil
from botocore.exceptions import ClientError

class LambdaDeployer:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
    def get_lambda_role_arn(self):
        """Get the LabRole ARN for AWS Academy"""
        account_id = self.get_account_id()
        lambda_role_arn = f"arn:aws:iam::{account_id}:role/LabRole"
        
        # Verify the role exists and has Lambda permissions
        try:
            # Test if we can describe the role (this will fail if role doesn't exist)
            self.iam_client.get_role(RoleName='LabRole')
            print(f"Using existing LabRole: {lambda_role_arn}")
            return lambda_role_arn
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"ERROR: LabRole not found in account {account_id}")
                print("Please ensure LabRole exists and has Lambda execution permissions")
                raise e
            else:
                print(f"ERROR: Cannot access LabRole: {e}")
                raise e
    
    def get_account_id(self):
        """Get AWS account ID"""
        sts_client = boto3.client('sts', region_name=self.region)
        return sts_client.get_caller_identity()['Account']
    
    def create_deployment_package(self):
        """Create deployment package for Lambda"""
        print("Creating deployment package...")
        
        # Create temporary directory
        deploy_dir = 'lambda_deployment'
        if os.path.exists(deploy_dir):
            shutil.rmtree(deploy_dir)
        os.makedirs(deploy_dir)
        
        # Copy Lambda handler
        shutil.copy(os.path.join(os.path.dirname(__file__), 'lambda_fhe_handler.py'), os.path.join(deploy_dir, 'lambda_function.py'))
        
        # Create requirements file for Lambda
        lambda_requirements = [
            'numpy==1.24.3',
            'requests==2.31.0'
        ]
        
        with open(os.path.join(deploy_dir, 'requirements.txt'), 'w') as f:
            f.write('\n'.join(lambda_requirements))
        
        # Install dependencies
        print("Installing dependencies...")
        subprocess.run([
            'pip', 'install', '-r', os.path.join(deploy_dir, 'requirements.txt'),
            '-t', deploy_dir, '--platform', 'manylinux2014_x86_64', '--only-binary=:all:'
        ], check=True)
        
        # Create ZIP file
        zip_filename = 'fhe_lambda_deployment.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(deploy_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, deploy_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Deployment package created: {zip_filename}")
        return zip_filename
    
    def deploy_lambda_function(self, zip_filename, role_arn):
        """Deploy Lambda function"""
        function_name = 'fhe-computation'
        
        try:
            # Read deployment package
            with open(zip_filename, 'rb') as f:
                zip_content = f.read()
            
            # Create or update Lambda function
            try:
                # Try to create new function
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_content},
                    Description='FHE computation Lambda function',
                    Timeout=30,
                    MemorySize=512,
                    Environment={
                        'Variables': {
                            'SEAL_MODE': 'mock'  # Use mock mode for now
                        }
                    }
                )
                print(f"Lambda function created: {function_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceConflictException':
                    # Function exists, update it
                    response = self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_content
                    )
                    print(f"Lambda function updated: {function_name}")
                else:
                    raise e
            
            return function_name
            
        except Exception as e:
            print(f"Lambda deployment failed: {e}")
            raise e
    
    def test_lambda_function(self, function_name):
        """Test the deployed Lambda function"""
        print("Testing Lambda function...")
        
        # Test payload
        test_payload = {
            "operation": "add_plain",
            "encrypted_data": "dGVzdF9kYXRh",  # base64 "test_data"
            "plaintext_data": [0, 5, 0, 0, 0],
            "context_params": {
                "scheme": "ckks",
                "poly_modulus_degree": 4096,
                "coeff_modulus_degree": [50],
                "scale_factor": 30
            }
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            
            if response['StatusCode'] == 200:
                print("Lambda function test successful!")
                print(f"Response: {json.dumps(response_payload, indent=2)}")
                return True
            else:
                print(f"Lambda function test failed: {response_payload}")
                return False
                
        except Exception as e:
            print(f"Lambda function test failed: {e}")
            return False
    
    def deploy(self):
        """Complete deployment process"""
        print("Starting Lambda deployment...")
        
        try:
            # Step 1: Get existing LabRole ARN
            role_arn = self.get_lambda_role_arn()
            
            # Step 2: Create deployment package
            zip_filename = self.create_deployment_package()
            
            # Step 3: Deploy Lambda function
            function_name = self.deploy_lambda_function(zip_filename, role_arn)
            
            # Step 4: Test the function
            test_success = self.test_lambda_function(function_name)
            
            # Cleanup
            os.remove(zip_filename)
            shutil.rmtree('lambda_deployment')
            
            if test_success:
                print(f"\nLambda deployment successful!")
                print(f"Function name: {function_name}")
                print(f"Region: {self.region}")
                print(f"Role ARN: {role_arn}")
                print(f"\nYou can now test with: python cloud_fhe_client.py")
                return True
            else:
                print(f"\nLambda deployment failed!")
                return False
                
        except Exception as e:
            print(f"Deployment failed: {e}")
            return False


def main():
    """Main deployment function"""
    print("FHE Lambda Deployment")
    print("=" * 40)
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
        print("AWS credentials configured")
    except Exception as e:
        print(f"AWS credentials not configured: {e}")
        print("Please run: aws configure")
        return False
    
    # Deploy
    deployer = LambdaDeployer()
    success = deployer.deploy()
    
    return success


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\nDeployment completed successfully!")
    else:
        print("\nDeployment failed!")
        exit(1) 