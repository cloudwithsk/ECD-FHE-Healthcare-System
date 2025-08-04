#!/usr/bin/env python3
"""
Quick Cloud FHE Test - Minimal Setup for Immediate Testing
This script provides a quick way to test FHE computation in the cloud.
"""

import sys
import os
import time
import json
import base64
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_local_workflow():
    """Test the local ECD workflow first"""
    print("🔍 Testing Local ECD Workflow")
    print("=" * 40)
    
    try:
        from ECD_api.ECD_fhe_new import test_ecd_performance
        success = test_ecd_performance()
        return success
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False

def test_cloud_workflow():
    """Test the cloud FHE workflow"""
    print("\n🌐 Testing Cloud FHE Workflow")
    print("=" * 40)
    
    try:
        from .cloud_fhe_client import test_cloud_fhe_workflow
        success = test_cloud_fhe_workflow()
        return success
    except Exception as e:
        print(f"❌ Cloud test failed: {e}")
        return False

def compare_performance():
    """Compare local vs cloud performance"""
    print("\n📊 Performance Comparison")
    print("=" * 40)
    
    # This would be implemented to compare local vs cloud performance
    print("Local vs Cloud Performance Analysis:")
    print("  - Local: Direct computation on your machine")
    print("  - Cloud: Network overhead + cloud computation")
    print("  - Trade-off: Privacy vs Performance")

def main():
    """Main test function"""
    print("🚀 Quick Cloud FHE Test")
    print("=" * 50)
    
    # Step 1: Test local workflow
    local_success = test_local_workflow()
    
    if not local_success:
        print("❌ Local workflow failed - cannot proceed to cloud test")
        return False
    
    # Step 2: Test cloud workflow
    cloud_success = test_cloud_workflow()
    
    # Step 3: Performance comparison
    compare_performance()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    print(f"Local ECD Workflow: {'✅ PASS' if local_success else '❌ FAIL'}")
    print(f"Cloud FHE Workflow: {'✅ PASS' if cloud_success else '❌ FAIL'}")
    
    if local_success and cloud_success:
        print("\n🎉 All tests passed!")
        print("Your FHE system is ready for cloud deployment!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ Quick test completed successfully!")
    else:
        print("\n❌ Quick test failed!")
        sys.exit(1) 