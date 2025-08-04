#!/usr/bin/env python3
"""
Detailed Cost Analysis for FHE Cloud Computation
Calculate actual costs based on your metrics.
"""

def calculate_costs():
    """Calculate detailed cost breakdown"""
    
    print("FHE Cloud Computation Cost Analysis")
    print("=" * 50)
    
    # Your actual metrics
    lambda_duration_ms = 100.20  # Your cloud computation time
    lambda_memory_mb = 512       # Lambda memory allocation
    data_transfer_mb = 0.1       # Estimated encrypted data size
    
    # AWS Lambda pricing (us-east-1)
    lambda_price_per_100ms = 0.0000002083  # $0.0000002083 per 100ms
    lambda_memory_price = 0.0000166667     # $0.0000166667 per GB-second
    
    # Data transfer pricing
    data_transfer_price_per_gb = 0.09      # $0.09 per GB
    
    # Calculate Lambda compute cost
    lambda_compute_seconds = lambda_duration_ms / 1000
    lambda_compute_cost = (lambda_compute_seconds * lambda_price_per_100ms * 10)  # Convert to per-100ms
    lambda_memory_cost = (lambda_compute_seconds * lambda_memory_mb / 1024 * lambda_memory_price)
    total_lambda_cost = lambda_compute_cost + lambda_memory_cost
    
    # Calculate data transfer cost
    data_transfer_cost = (data_transfer_mb / 1024) * data_transfer_price_per_gb
    
    # Total cost
    total_cost = total_lambda_cost + data_transfer_cost
    
    print(f"📊 Cost Breakdown:")
    print(f"   Lambda Duration: {lambda_duration_ms:.2f}ms")
    print(f"   Lambda Memory: {lambda_memory_mb}MB")
    print(f"   Data Transfer: {data_transfer_mb:.2f}MB")
    
    print(f"\n💰 Lambda Compute Cost:")
    print(f"   Compute Time Cost: ${lambda_compute_cost:.8f}")
    print(f"   Memory Cost: ${lambda_memory_cost:.8f}")
    print(f"   Total Lambda Cost: ${total_lambda_cost:.8f}")
    
    print(f"\n📡 Data Transfer Cost:")
    print(f"   Transfer Cost: ${data_transfer_cost:.8f}")
    
    print(f"\n💵 Total Cost per Operation:")
    print(f"   Total: ${total_cost:.8f}")
    
    # Cost for multiple operations
    operations = [1, 10, 100, 1000]
    print(f"\n📈 Cost Scaling:")
    for op in operations:
        cost = total_cost * op
        print(f"   {op} operations: ${cost:.6f}")
    
    # Comparison with other services
    print(f"\n🔍 Cost Comparison:")
    print(f"   Lambda FHE operation: ${total_cost:.8f}")
    print(f"   Traditional server (1 hour): ~$0.10")
    print(f"   Your test cost: < $0.01")
    
    # Budget analysis
    aws_credits = 50  # Your $50 AWS Academy credits
    operations_possible = aws_credits / total_cost
    
    print(f"\n🎯 Budget Analysis:")
    print(f"   AWS Credits: ${aws_credits}")
    print(f"   Operations possible: {operations_possible:,.0f}")
    print(f"   Cost per 1000 operations: ${total_cost * 1000:.6f}")
    
    return total_cost

if __name__ == "__main__":
    cost = calculate_costs()
    print(f"\n✅ Cost analysis completed!")
    print(f"   Each FHE cloud operation costs: ${cost:.8f}") 