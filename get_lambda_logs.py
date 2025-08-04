#!/usr/bin/env python3
"""
Get Real Lambda Logs from AWS Academy
Extract actual execution logs from your Lambda function.
"""

import boto3
import json
from datetime import datetime, timedelta

def get_lambda_logs():
    """Get real Lambda execution logs"""
    
    logs_client = boto3.client('logs')
    
    print("Real Lambda Logs from AWS Academy")
    print("=" * 40)
    
    try:
        # Get log group info
        log_group_name = "/aws/lambda/fhe-computation"
        
        print(f"📋 Log Group: {log_group_name}")
        
        # Get recent log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        print(f"\n📊 Recent Log Streams:")
        for stream in response['logStreams']:
            print(f"   Stream: {stream['logStreamName']}")
            print(f"   Last Event: {stream.get('lastEventTimestamp', 'N/A')}")
            print(f"   Events: {stream.get('storedBytes', 0)} bytes")
        
        # Get recent log events (last hour)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        print(f"\n📝 Recent Log Events:")
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=20
        )
        
        if response['events']:
            for event in response['events']:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"\n⏰ {timestamp}:")
                print(f"   Message: {event['message'][:200]}...")
        else:
            print("   No recent log events found")
        
        # Get function metrics
        lambda_client = boto3.client('lambda')
        response = lambda_client.get_function(FunctionName='fhe-computation')
        
        print(f"\n🔧 Function Details:")
        print(f"   Last Modified: {response['Configuration']['LastModified']}")
        print(f"   Code Size: {response['Configuration']['CodeSize']} bytes")
        print(f"   Memory: {response['Configuration']['MemorySize']}MB")
        
        print(f"\n✅ Log extraction completed!")
        
    except Exception as e:
        print(f"❌ Failed to get logs: {e}")

if __name__ == "__main__":
    get_lambda_logs() 