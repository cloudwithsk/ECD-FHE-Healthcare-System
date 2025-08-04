# FHE Performance Testing Guide

## Overview

This guide explains the comprehensive performance testing capabilities that have been added to the FHE (Fully Homomorphic Encryption) healthcare system. The enhanced testing includes detailed timing measurements and memory usage tracking for all FHE operations.

## 🎯 Key Features

### 1. **Comprehensive Performance Monitoring**
- **Timing Measurements**: Precise execution time tracking for all FHE operations
- **Memory Usage Tracking**: Real-time memory consumption monitoring using `psutil`
- **Statistical Analysis**: Mean, median, standard deviation, and range calculations
- **Multiple Test Runs**: Configurable number of test runs for statistical reliability

### 2. **Enhanced Testing Suite**
- **PerformanceMonitor Class**: Dedicated class for performance measurement
- **Memory-Intensive Testing**: Tests with varying data sizes (10, 50, 100, 500 elements)
- **Comprehensive Reporting**: Detailed performance summaries with visual indicators

## 📊 Performance Metrics Measured

### Timing Metrics
- **Encryption Time**: Time taken to encrypt data
- **Decryption Time**: Time taken to decrypt results
- **Computation Time**: Time for homomorphic operations (addition, multiplication)
- **Total Workflow Time**: End-to-end processing time

### Memory Metrics
- **RSS (Resident Set Size)**: Actual physical memory used
- **VMS (Virtual Memory Size)**: Total virtual memory allocated
- **Memory Delta**: Change in memory usage during operations
- **Peak Memory Usage**: Maximum memory consumption

### Statistical Metrics
- **Mean**: Average performance across multiple runs
- **Median**: Middle value of performance measurements
- **Standard Deviation**: Variability in performance
- **Range**: Minimum to maximum performance values

## 🚀 How to Use

### 1. Basic Performance Test
```bash
# Run the enhanced performance test
python ECD_api/ECD_fhe.py
```

### 2. Test Performance Monitor Only
```bash
# Test the performance monitoring functionality
python test_enhanced_performance.py
```

### 3. Run Existing Benchmarks
```bash
# Run comprehensive benchmark suite
python benchmark_performance.py

# Run quick benchmark test
python test_benchmark.py
```

## 📈 Sample Performance Results

Based on recent testing with Python 3.11.9:

### Typical Performance (5 data points, CKKS scheme)
```
🔹 ENCRYPTION:
   ⏱️  Average Time: 1.08ms
   ⏱️  Time Range: 0.7ms - 1.3ms
   ⏱️  Standard Deviation: 0.22ms
   💾 Avg Memory RSS Δ: +0.0MB
   💾 Max Memory RSS Δ: +0.1MB

🔹 COMPUTATION:
   ⏱️  Average Time: 0.25ms
   ⏱️  Time Range: 0.1ms - 0.5ms
   ⏱️  Standard Deviation: 0.16ms
   💾 Avg Memory RSS Δ: +0.0MB

🔹 DECRYPTION:
   ⏱️  Average Time: 0.18ms
   ⏱️  Time Range: 0.1ms - 0.3ms
   ⏱️  Standard Deviation: 0.05ms
   💾 Avg Memory RSS Δ: +0.0MB

🎯 TOTAL WORKFLOW PERFORMANCE:
   ⏱️  Total Average Time: 1.50ms
   💾 Total Memory RSS Δ: +0.1MB
```

### Memory-Intensive Testing Results
```
📊 Testing with 10 data points:
   Encryption: 0.73ms ± 0.02ms
   Decryption: 0.17ms ± 0.04ms

📊 Testing with 50 data points:
   Encryption: 0.85ms ± 0.15ms
   Decryption: 0.15ms ± 0.01ms

📊 Testing with 100 data points:
   Encryption: 0.86ms ± 0.25ms
   Decryption: 0.17ms ± 0.04ms

📊 Testing with 500 data points:
   Encryption: 0.73ms ± 0.01ms
   Decryption: 0.14ms ± 0.01ms
```

## 🔧 Technical Implementation

### PerformanceMonitor Class
```python
class PerformanceMonitor:
    """Comprehensive performance monitoring for FHE operations."""
    
    def __init__(self):
        self.measurements = {}
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None
    
    def measure_operation(self, operation_name, operation_func, *args, **kwargs):
        """Measure performance of an operation including time and memory."""
        
    def run_multiple_measurements(self, operation_name, operation_func, 
                                num_runs=5, *args, **kwargs):
        """Run multiple measurements and calculate statistics."""
```

### Key Features
- **Garbage Collection**: Forces GC before measurements for accurate memory tracking
- **High-Precision Timing**: Uses `time.perf_counter()` for microsecond precision
- **Memory Monitoring**: Tracks both RSS and VMS memory usage
- **Statistical Analysis**: Calculates comprehensive statistics across multiple runs
- **Error Handling**: Graceful handling of measurement failures

## 📋 Dependencies

### Required Packages
```txt
# Performance monitoring
psutil==5.9.5

# Core FHE dependencies
numpy==1.24.3
seal-python (installed via setup.py)
```

### Python Version
- **Tested with**: Python 3.11.9
- **Minimum**: Python 3.8+

## 🎛️ Configuration Options

### PerformanceMonitor Parameters
```python
# Number of test runs for statistical reliability
num_runs = 5  # Default: 5 runs

# Memory measurement options
PSUTIL_AVAILABLE = True  # Auto-detected

# Garbage collection
gc.collect()  # Forced before each measurement
```

### SEAL Engine Parameters
```python
# Working parameters for SEAL 4.0.0
engine = SEALEngine(
    scheme='ckks',
    poly_modulus_degree=2048,
    coeff_modulus_degree=[40],
    scale_factor=16,
    plain_modulus_bits=20
)
```

## 🔍 Troubleshooting

### Common Issues

1. **psutil Not Available**
   ```
   ⚠️ psutil not available - memory monitoring will be limited
   ```
   **Solution**: Install psutil: `pip install psutil==5.9.5`

2. **SEAL Engine Import Error**
   ```
   ❌ SEAL engine not available: [error message]
   ```
   **Solution**: Ensure SEAL-Python is properly installed via `setup.py`

3. **Invalid Encryption Parameters**
   ```
   ❌ Key generation failed: Invalid encryption parameters
   ```
   **Solution**: Use the working parameters provided in the enhanced code

### Performance Optimization Tips

1. **Warmup Runs**: The system includes warmup runs to stabilize performance
2. **Garbage Collection**: Automatic GC before measurements ensures accurate memory tracking
3. **Multiple Runs**: Statistical analysis across multiple runs provides reliable metrics
4. **Memory Monitoring**: Real-time memory tracking helps identify memory leaks

## 📊 Performance Analysis

### What the Metrics Tell Us

1. **Timing Consistency**: Low standard deviation indicates stable performance
2. **Memory Efficiency**: Small memory deltas indicate efficient memory usage
3. **Scalability**: Performance across different data sizes shows system scalability
4. **Accuracy**: Relative error calculations verify FHE computation accuracy

### Benchmarking Best Practices

1. **Multiple Runs**: Always run multiple measurements for statistical reliability
2. **Consistent Environment**: Run tests in the same environment for comparable results
3. **Memory Monitoring**: Track memory usage to identify potential memory leaks
4. **Error Analysis**: Monitor relative errors to ensure FHE accuracy

## 🔮 Future Enhancements

### Planned Features
- **GPU Performance Monitoring**: Track GPU memory and computation usage
- **Network Performance**: Measure network latency for distributed FHE
- **Power Consumption**: Monitor CPU and system power usage
- **Real-time Monitoring**: Live performance dashboard for production systems

### Integration Opportunities
- **CI/CD Integration**: Automated performance regression testing
- **Performance Alerts**: Automated alerts for performance degradation
- **Historical Tracking**: Long-term performance trend analysis
- **Comparative Analysis**: Performance comparison across different hardware

## 📚 Additional Resources

- **SEAL Documentation**: [Microsoft SEAL](https://github.com/microsoft/SEAL)
- **FHE Performance Papers**: Academic research on FHE performance optimization
- **Healthcare FHE Applications**: Real-world FHE use cases in healthcare
- **Performance Benchmarking**: Industry standards for FHE performance testing

---

*This enhanced performance testing system provides comprehensive metrics for evaluating FHE system performance, ensuring reliable and efficient homomorphic encryption operations for healthcare applications.* 