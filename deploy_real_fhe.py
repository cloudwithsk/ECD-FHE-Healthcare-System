#!/usr/bin/env python3
"""
Deploy Real FHE with SEAL Library
Complete deployment and testing of real homomorphic encryption in AWS Lambda.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main deployment process"""
    print("Real FHE Deployment with SEAL")
    print("=" * 40)
    
    # Step 1: Deploy SEAL Layer
    print("\nStep 1: Deploying SEAL Lambda Layer")
    if not run_command("python deploy_seal_layer.py", "SEAL layer deployment"):
        print("❌ SEAL layer deployment failed")
        return False
    
    # Step 2: Update Lambda Function
    print("\nStep 2: Updating Lambda Function")
    if not run_command("python deploy_lambda.py", "Lambda function update"):
        print("❌ Lambda function update failed")
        return False
    
    # Step 3: Wait for deployment
    print("\nStep 3: Waiting for deployment to complete...")
    time.sleep(30)  # Wait for Lambda to update
    
    # Step 4: Test Real FHE
    print("\nStep 4: Testing Real FHE Computation")
    if not run_command("python cloud_fhe_client.py", "Real FHE test"):
        print("❌ Real FHE test failed")
        return False
    
    print("\n🎉 Real FHE deployment completed successfully!")
    print("\nExpected improvements:")
    print("- Real homomorphic computation")
    print("- Accurate results (not mock)")
    print("- Better performance metrics")
    print("- Proper error rates")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 