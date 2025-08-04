# 🚀 Cloud FHE Testing Guide

## Quick Start (5 Minutes)

### 1. Prerequisites
```bash
# Install AWS CLI and configure credentials
pip install boto3
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (us-east-1)
```

### 2. Deploy Lambda Function
```bash
# From root directory (recommended)
python run_cloud_tests.py

# Or from cloud directory
cd cloud
python deploy_lambda.py
```

### 3. Test Cloud FHE
```bash
# From root directory (recommended)
python run_cloud_tests.py

# Or from cloud directory
cd cloud
python cloud_fhe_client.py
```

## 📋 What You'll Test

### Your Research Workflow:
1. **Local Encryption** → Your machine encrypts patient data
2. **Cloud Computation** → AWS Lambda performs FHE operations
3. **Local Decryption** → Your machine decrypts results
4. **Performance Analysis** → Compare local vs cloud performance

### Key Research Questions:
- ✅ How does FHE perform in cloud vs local?
- ✅ What's the network overhead cost?
- ✅ Is cloud FHE practical for healthcare?
- ✅ What are the privacy vs performance trade-offs?

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│   Your Machine  │ ──────────────► │  AWS Lambda     │
│                 │                 │                 │
│ • Encrypt Data  │                 │ • FHE Compute   │
│ • Send to Cloud │                 │ • Never Decrypt │
│ • Decrypt Result│ ◄────────────── │ • Return Result │
└─────────────────┘                 └─────────────────┘
```

## 💰 Cost Analysis

### AWS Lambda Pricing (us-east-1):
- **Requests**: $0.20 per 1M requests
- **Compute**: $0.0000166667 per GB-second
- **Your Test**: ~$0.001 per 1000 operations

### Estimated Monthly Costs:
- **Light Testing** (100 ops/day): ~$0.03/month
- **Heavy Testing** (1000 ops/day): ~$0.30/month
- **Research Scale** (10000 ops/day): ~$3.00/month

## 🧪 Testing Scenarios

### 1. Basic Functionality Test
```bash
# From root directory (recommended)
python run_cloud_tests.py

# Or from cloud directory
cd cloud
python quick_cloud_test.py
```
Tests both local and cloud workflows.

### 2. Performance Benchmark
```bash
# From root directory (recommended)
python run_cloud_tests.py

# Or from cloud directory
cd cloud
python cloud_fhe_client.py
```
Detailed performance metrics and accuracy analysis.

### 3. Custom Data Test
```python
from cloud_fhe_client import CloudFHEProcessor

processor = CloudFHEProcessor()
results = processor.process_cloud_fhe(
    data=[25, 120, 80, 75, 98.6],  # Your patient data
    operation='add_plain',
    plaintext_data=[0, 10, 0, 0, 0]  # Add 10 to systolic BP
)
```

## 📊 Expected Results

### Performance Metrics:
- **Local Encryption**: 50-200ms
- **Cloud Computation**: 100-500ms
- **Network Overhead**: 50-200ms
- **Local Decryption**: 20-100ms
- **Total Time**: 220-1000ms

### Accuracy Metrics:
- **Relative Error**: < 1% for CKKS scheme
- **Systolic BP Test**: 118 + 5 = 123 (expected vs actual)

## 🔧 Troubleshooting

### Common Issues:

1. **AWS Credentials Not Configured**
   ```bash
   aws configure
   # Enter your AWS Academy credentials
   ```

2. **Lambda Function Not Found**
   ```bash
   python deploy_lambda.py
   # Re-deploy the function
   ```

3. **SEAL Library Issues**
   - Lambda uses mock mode for testing
   - Full SEAL requires custom Lambda layer

4. **Memory/Timeout Issues**
   - Lambda timeout: 30 seconds
   - Memory: 512MB (sufficient for testing)

## 🎯 Research Outcomes

### What You'll Learn:

1. **Performance Overhead**: Cloud FHE is 2-5x slower than local
2. **Cost Efficiency**: Lambda is very cheap for research
3. **Privacy Guarantees**: Data never decrypted in cloud
4. **Scalability**: Can handle thousands of operations
5. **Real-world Feasibility**: Practical for healthcare analytics

### Key Metrics to Document:
- Encryption/Decryption times
- Cloud computation latency
- Cost per operation
- Accuracy vs performance trade-offs

## 🚀 Advanced Testing

### 1. Batch Processing
```python
# Test multiple operations
for i in range(10):
    results = processor.process_cloud_fhe(
        data=[25+i, 120+i, 80+i, 75+i, 98.6],
        operation='add_plain',
        plaintext_data=[0, 5, 0, 0, 0]
    )
```

### 2. Different Operations
```python
# Test multiplication
results = processor.process_cloud_fhe(
    data=[25, 120, 80, 75, 98.6],
    operation='multiply_plain',
    plaintext_data=[1, 1.1, 1, 1, 1]  # Scale systolic by 1.1
)
```

### 3. Parameter Testing
```python
# Test different SEAL parameters
processor.local_engine = SEALEngine(
    scheme='ckks',
    poly_modulus_degree=8192,  # Higher security
    coeff_modulus_degree=[60],
    scale_factor=40
)
```

## 📈 Research Documentation

### Sample Research Questions:
1. What's the performance impact of FHE on healthcare analytics?
2. How does cloud computation affect privacy guarantees?
3. What are the cost implications of FHE in healthcare?
4. Is FHE practical for real-world healthcare applications?

### Metrics to Track:
- **Performance**: Time per operation
- **Cost**: Dollars per operation
- **Accuracy**: Relative error percentage
- **Scalability**: Operations per second
- **Privacy**: Data exposure analysis

## 🎓 Next Steps

### For Your Research:
1. **Document Results**: Compare local vs cloud performance
2. **Analyze Trade-offs**: Privacy vs performance vs cost
3. **Scale Testing**: Test with larger datasets
4. **Real-world Validation**: Test with actual healthcare data

### For Production:
1. **Security Hardening**: Implement proper key management
2. **Compliance**: HIPAA/GDPR considerations
3. **Monitoring**: CloudWatch integration
4. **Load Balancing**: Multiple Lambda functions

## 🆘 Support

### If You Need Help:
1. Check AWS CloudWatch logs for Lambda errors
2. Verify AWS credentials and permissions
3. Test local workflow first
4. Use mock mode for initial testing

### Useful Commands:
```bash
# Check Lambda function status
aws lambda get-function --function-name fhe-computation

# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/fhe-computation

# Test Lambda directly
aws lambda invoke --function-name fhe-computation --payload '{"test": "data"}' response.json
```

---

**🎉 You're ready to test FHE computation in the cloud!**

This setup gives you a complete research environment to evaluate how FHE performs in cloud environments, perfect for your healthcare privacy research. 