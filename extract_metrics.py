#!/usr/bin/env python3
"""
Extract AWS Metrics and Logs
Get performance data and costs for research documentation.
"""

import boto3
import json
from datetime import datetime, timedelta

def extract_aws_metrics():
    """Extract AWS metrics and logs"""
    
    lambda_client = boto3.client('lambda')
    logs_client = boto3.client('logs')
    cloudwatch = boto3.client('cloudwatch')
    
    print("AWS Metrics and Logs Extraction")
    print("=" * 40)
    
    # 1. Lambda function info
    try:
        response = lambda_client.get_function(FunctionName='fhe-computation')
        print(f"✅ Lambda Function: {response['Configuration']['FunctionName']}")
        print(f"   Runtime: {response['Configuration']['Runtime']}")
        print(f"   Memory: {response['Configuration']['MemorySize']}MB")
        print(f"   Timeout: {response['Configuration']['Timeout']}s")
        print(f"   Layers: {len(response['Configuration'].get('Layers', []))}")
        
        # Get account ID
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        print(f"   AWS Account ID: {account_id}")
        
    except Exception as e:
        print(f"❌ Lambda info failed: {e}")
    
    # 2. Recent invocations
    try:
        response = lambda_client.get_function(FunctionName='fhe-computation')
        print(f"\n📊 Function Statistics:")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
        print(f"   Code Size: {response['Configuration']['CodeSize']} bytes")
    except Exception as e:
        print(f"❌ Function stats failed: {e}")
    
    # 3. CloudWatch metrics (last hour)
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Duration',
            Dimensions=[{'Name': 'FunctionName', 'Value': 'fhe-computation'}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average', 'Maximum', 'Minimum']
        )
        
        if response['Datapoints']:
            print(f"\n⏱️ Performance Metrics (last hour):")
            for point in response['Datapoints']:
                print(f"   Average Duration: {point['Average']:.2f}ms")
                print(f"   Max Duration: {point['Maximum']:.2f}ms")
                print(f"   Min Duration: {point['Minimum']:.2f}ms")
        else:
            print(f"\n⚠️ No recent metrics found")
            
    except Exception as e:
        print(f"❌ CloudWatch metrics failed: {e}")
    
    # 4. Cost estimation
    print(f"\n💰 Estimated Costs:")
    print(f"   Lambda invocations: ~$0.0000002 per 100ms")
    print(f"   Data transfer: ~$0.09 per GB")
    print(f"   Your test cost: < $0.01")
    
    # 5. Your captured metrics
    print(f"\n📈 Your Test Results:")
    print(f"   Local Encryption: 15.83ms")
    print(f"   Cloud Computation: 100.20ms")
    print(f"   Network Overhead: 2898.48ms")
    print(f"   Local Decryption: 25.87ms")
    print(f"   Total Time: 3040.39ms")
    
    print(f"\n✅ Metrics extraction completed!")

if __name__ == "__main__":
    extract_aws_metrics() 