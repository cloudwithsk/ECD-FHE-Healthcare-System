# FHE Healthcare System - Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [ECD Workflow Architecture](#ecd-workflow-architecture)
4. [Key Management Architecture](#key-management-architecture)
5. [Local vs Cloud Processing](#local-vs-cloud-processing)
6. [Performance Monitoring Architecture](#performance-monitoring-architecture)
7. [Data Processing Pipeline](#data-processing-pipeline)
8. [Security Architecture](#security-architecture)
9. [Implementation Details](#implementation-details)

---

## System Overview

The FHE Healthcare System implements two distinct workflows for Encrypt-Compute-Decrypt (ECD) operations:

1. **Local ECD Workflow**: Complete processing on local machine
2. **Cloud ECD Workflow**: Local encryption → Cloud computation → Local decryption

Both workflows use Microsoft SEAL library with CKKS scheme for approximate floating-point arithmetic suitable for healthcare data.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FHE Healthcare System                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                    ┌─────────────────┐                │
│  │   Local ECD     │                    │   Cloud ECD     │                │
│  │   Workflow      │                    │   Workflow       │                │
│  │                 │                    │                 │                │
│  │ • Local Encrypt │                    │ • Local Encrypt │                │
│  │ • Local Compute │                    │ • Cloud Compute │                │
│  │ • Local Decrypt │                    │ • Local Decrypt │                │
│  └─────────────────┘                    └─────────────────┘                │
│           │                                       │                        │
│           ▼                                       ▼                        │
│  ┌─────────────────┐                    ┌─────────────────┐                │
│  │   SEAL Engine   │                    │   AWS Lambda    │                │
│  │   (CKKS/BFV)    │                    │   FHE Handler   │                │
│  └─────────────────┘                    └─────────────────┘                │
│           │                                       │                        │
│           ▼                                       ▼                        │
│  ┌─────────────────┐                    ┌─────────────────┐                │
│  │ Performance     │                    │ Cloud Storage   │                │
│  │ Monitor         │                    │ & Networking    │                │
│  └─────────────────┘                    └─────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ECD Workflow Architecture

### 1. Local ECD Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Local ECD Workflow                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Input     │───▶│  Encrypt    │───▶│  Compute    │───▶│  Decrypt    │ │
│  │   Data      │    │  (SEAL)     │    │ (Homomorphic)│   │  (SEAL)     │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  [Patient Data]      [Ciphertext]        [Result CT]        [Decrypted]   │
│  [26,118,76,80,97.6] [Encrypted]        [Encrypted]        [26,123,76,80,97.6] │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Performance Monitoring                              │ │
│  │  • Execution Time: ~1.17ms total                                      │ │
│  │  • Memory Usage: RSS/VMS tracking                                     │ │
│  │  • Accuracy: 0.01% relative error                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Cloud ECD Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Cloud ECD Workflow                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Local     │───▶│   Serialize │───▶│   AWS       │───▶│   Deserialize│ │
│  │  Encrypt    │    │   & Send    │    │  Lambda     │    │   & Decrypt  │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  [Patient Data]      [Base64 CT]        [Computed CT]      [Final Result] │
│  [45,120,80,72,98.6] [Serialized]      [Cloud Processed]  [45,125,80,72,98.6] │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Cloud Performance Metrics                           │ │
│  │  • Local Encryption: ~Xms                                             │ │
│  │  • Network Transfer: ~Yms                                             │ │
│  │  • Cloud Computation: ~Zms                                            │ │
│  │  • Local Decryption: ~Wms                                             │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Management Architecture

### SEAL Key Generation and Usage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Key Management Architecture                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Context       │───▶│   KeyGenerator  │───▶│   Key Storage   │        │
│  │   Setup         │    │   (SEAL)        │    │   (Memory)      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  [SEAL Context]           [Key Objects]           [Key Components]        │
│  • Poly Modulus: 4096     • Secret Key            • Public Key            │
│  • Coeff Modulus: [50]    • Public Key            • Secret Key            │
│  • Scale Factor: 30       • Relin Keys            • Relin Keys            │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Encryption    │    │   Computation   │    │   Decryption    │        │
│  │   Components    │    │   Components    │    │   Components    │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  • Encryptor              • Evaluator              • Decryptor            │
│  • Public Key             • Relin Keys             • Secret Key            │
│  • CKKS Encoder           • Context                • CKKS Encoder         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Usage in Operations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Key Usage in ECD Operations                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENCRYPTION PHASE:                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   Plaintext │───▶│   Encoder   │───▶│  Encryptor  │                    │
│  │   Data      │    │ (CKKS)      │    │ (Public Key)│                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│                                                                             │
│  COMPUTATION PHASE:                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │  Ciphertext │───▶│  Evaluator  │───▶│  Result CT  │                    │
│  │             │    │ (Relin Keys)│    │             │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│                                                                             │
│  DECRYPTION PHASE:                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │  Ciphertext │───▶│  Decryptor  │───▶│   Decoder   │                    │
│  │             │    │(Secret Key) │    │  (CKKS)     │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Local vs Cloud Processing

### Comparison Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Local vs Cloud Processing Comparison                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOCAL PROCESSING:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │ │
│  │  │ Encrypt │─▶│ Compute │─▶│ Decrypt │─▶│ Monitor │─▶│ Result  │     │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │ │
│  │     │             │             │             │             │           │ │
│  │   ~0.85ms      ~0.15ms      ~0.17ms      Memory      Final Data      │ │
│  │                                                                         │ │
│  │  Total Time: ~1.17ms                                                    │ │
│  │  Memory: Local RAM                                                      │ │
│  │  Security: Full local control                                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CLOUD PROCESSING:                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │ │
│  │  │ Encrypt │─▶│ Serialize│─▶│ AWS     │─▶│ Deserialize│─▶│ Decrypt │     │ │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │ │
│  │     │             │             │             │             │           │ │
│  │   Local        Base64        Lambda       Base64        Local         │ │
│  │                                                                         │ │
│  │  Total Time: Network + Cloud computation                                │ │
│  │  Memory: Distributed (Local + Cloud)                                   │ │
│  │  Security: Encrypted transmission                                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Performance Monitoring Architecture

### Performance Monitor Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Performance Monitoring Architecture                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Simple        │    │   Comprehensive │    ┌─────────────────┐        │
│  │   Monitor       │    │   Monitor       │    │   Statistical   │        │
│  │   (ECD_fhe_new)│    │   (ECD_fhe)     │    │   Analysis      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  • Basic timing              • Advanced timing         • Mean/Median       │
│  • Memory RSS/VMS            • Multiple runs           • Std Deviation     │
│  • Single measurement        • Statistical analysis    • Range calculation │
│  • Minimal output            • Detailed reporting      • Performance trends│
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Memory        │    │   Timing        │    │   Accuracy      │        │
│  │   Tracking      │    │   Measurement   │    │   Verification  │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  • psutil.Process()         • time.perf_counter()     • Relative error    │
│  • RSS/VMS monitoring       • Microsecond precision   • Expected vs Actual│
│  • GC before measurement    • High-resolution timing   • Error percentage  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Performance Metrics Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Performance Metrics Flow                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Operation │───▶│   Measure   │───▶│   Calculate │───▶│   Report    │ │
│  │   Start     │    │   Time &    │    │   Metrics   │    │   Results   │ │
│  └─────────────┘    │   Memory    │    └─────────────┘    └─────────────┘ │
│         │            └─────────────┘            │                   │       │
│         ▼                   │                   ▼                   ▼       │
│  [Function Call]      [GC + Timing]      [Statistics]        [Output]     │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  [Encrypt/Compute/    [Execution Time]   [Mean/Std Dev]     [Formatted]   │
│   Decrypt]            [Memory Delta]     [Range]            [Display]     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Measured Performance (5 runs average)               │ │
│  │  • Encryption: 0.85ms (0.7-1.2ms, σ=0.20ms)                          │ │
│  │  • Computation: 0.15ms (0.1-0.2ms, σ=0.02ms)                         │ │
│  │  • Decryption: 0.17ms (0.1-0.3ms, σ=0.07ms)                          │ │
│  │  • Total Workflow: 1.17ms                                             │ │
│  │  • Memory RSS Δ: +0.0MB                                               │ │
│  │  • Accuracy: 0.01% relative error                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Processing Pipeline

### Complete Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Data Processing Pipeline                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT PHASE:                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   Raw       │───▶│   Validate  │───▶│   Normalize │                    │
│  │   Data      │    │   Input     │    │   Data      │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  [Patient Data]      [Type Check]        [Float Array]                    │
│  [26,118,76,80,97.6] [List/Array]       [numpy.float64]                  │
│                                                                             │
│  ENCRYPTION PHASE:                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   Encode    │───▶│   Encrypt   │───▶│   Ciphertext│                    │
│  │   (CKKS)    │    │   (SEAL)    │    │   (SEAL)    │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  [Plaintext]          [Public Key]        [Encrypted]                     │
│  [Scale: 2^30]        [Encryptor]        [Ciphertext]                    │
│                                                                             │
│  COMPUTATION PHASE:                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   Plaintext │───▶│   Add       │───▶│   Result    │                    │
│  │   Operand   │    │   Operation │    │   Ciphertext│                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  [0,5,0,0,0]         [Evaluator]        [Encrypted]                      │
│  [Plaintext]          [Add_Plain]        [Result]                         │
│                                                                             │
│  DECRYPTION PHASE:                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   Decrypt   │───▶│   Decode    │───▶│   Final     │                    │
│  │   (SEAL)    │    │   (CKKS)    │    │   Result    │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  [Secret Key]         [Plaintext]        [26,123,76,80,97.6]              │
│  [Decryptor]          [Decode]           [List]                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Multi-Layer Security Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Security Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   FHE           │    │   Cloud         │    │   Data          │        │
│  │   Security      │    │   Security      │    │   Security      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  • CKKS Encryption         • AWS Lambda              • Sample Data         │
│  • Public Key Only         • VPC Isolation           • No Real PII         │
│  • Homomorphic Ops         • IAM Roles               • Data Protection     │
│  • Secret Key Local        • CloudWatch              • Encryption          │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   Key           │    │   Network       │    │   Application   │        │
│  │   Management    │    │   Security      │    │   Security      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  • Auto Generation         • HTTPS/TLS               • Input Validation    │
│  • Memory Storage          • Base64 Encoding         • Error Handling      │
│  • No Persistence          • Encrypted Transfer      • Access Control      │
│  • Session Scoped          • Network Isolation       • Audit Logging       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### SEAL Engine Configuration

```python
# Actual Implementation Parameters:
SEALEngine(
    scheme='ckks',                    # Approximate floating-point arithmetic
    poly_modulus_degree=4096,        # Polynomial modulus degree
    coeff_modulus_degree=[50],       # Coefficient modulus bits
    scale_factor=30                  # CKKS scale factor (2^30)
)
```

### Performance Monitor Implementation

```python
# Simple Performance Monitor (ECD_fhe_new.py):
class SimplePerformanceMonitor:
    def measure_operation(self, operation_name, operation_func, *args, **kwargs):
        # Force garbage collection
        gc.collect()
        
        # Get initial memory
        initial_memory = self.get_memory_usage()
        
        # Measure time with high precision
        start_time = time.perf_counter()
        result = operation_func(*args, **kwargs)
        end_time = time.perf_counter()
        
        # Calculate metrics
        execution_time_ms = (end_time - start_time) * 1000
        memory_delta = final_memory - initial_memory
        
        return {
            "operation": operation_name,
            "execution_time_ms": execution_time_ms,
            "memory_delta_rss_mb": memory_delta_rss,
            "memory_delta_vms_mb": memory_delta_vms,
            "result": result
        }
```

### Cloud Integration Implementation

```python
# Cloud FHE Client (cloud_fhe_client.py):
class CloudFHEProcessor:
    def process_cloud_fhe(self, data, operation, plaintext_data):
        # Step 1: Local encryption
        encrypted_b64 = self.encrypt_for_cloud(data)
        
        # Step 2: Cloud computation
        cloud_result = self.send_to_cloud(encrypted_b64, operation, plaintext_data)
        
        # Step 3: Local decryption
        decrypted_result = self.decrypt_from_cloud(cloud_result['result'])
        
        return {
            'original_data': data,
            'operation': operation,
            'decrypted_result': decrypted_result,
            'performance': {
                'encryption_time_ms': encryption_time,
                'cloud_computation_time_ms': cloud_result.get('computation_time_ms', 0),
                'decryption_time_ms': decryption_time,
                'total_time_ms': total_time
            }
        }
```

### Key Usage in Operations

```python
# Key Generation (core/engine.py):
def _generate_keys(self):
    self.keygen = seal.KeyGenerator(self.context)
    self.secret_key = self.keygen.secret_key()
    self.public_key = seal.PublicKey()
    self.keygen.create_public_key(self.public_key)
    
    # Optional relinearization keys for multiplication
    self.relin_keys = seal.RelinKeys()
    self.keygen.create_relin_keys(self.relin_keys)
    
    # Initialize components with keys
    self.encryptor = seal.Encryptor(self.context, self.public_key)
    self.decryptor = seal.Decryptor(self.context, self.secret_key)
    self.evaluator = seal.Evaluator(self.context)
```

### Serialization for Cloud Transmission

```python
# Serialization (cloud_fhe_client.py):
def serialize_ciphertext(ciphertext):
    # Create temporary file with .seal extension
    with tempfile.NamedTemporaryFile(delete=False, suffix='.seal') as temp_file:
        temp_filename = temp_file.name
    
    try:
        # Save ciphertext to file (SEAL requires string filename)
        ciphertext.save(temp_filename)
        
        # Read file content as bytes for transmission
        with open(temp_filename, 'rb') as f:
            encrypted_bytes = f.read()
        
        return encrypted_bytes
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
```

---

## Summary

This technical documentation provides a comprehensive overview of the FHE Healthcare System's architecture, focusing on:

1. **Two ECD Workflows**: Local and Cloud processing with different performance characteristics
2. **Key Management**: SEAL library key generation and usage in encryption/decryption
3. **Performance Monitoring**: Comprehensive timing and memory tracking
4. **Data Processing**: Complete pipeline from input to output
5. **Security**: Multi-layer security model for FHE operations
6. **Implementation Details**: Actual code patterns and configurations used

The system demonstrates practical implementation of homomorphic encryption for healthcare data processing with measurable performance metrics and security considerations. 