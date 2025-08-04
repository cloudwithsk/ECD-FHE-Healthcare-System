"""
SEAL Engine - A Python wrapper for Microsoft SEAL homomorphic encryption library.

This module provides a high-level interface for performing homomorphic encryption
operations using the SEAL library.
"""

import os
import json
from typing import List, Union, Optional, Dict, Any
import numpy as np
import seal


class SEALEngine:
    """
    A high-level wrapper for Microsoft SEAL homomorphic encryption operations.
    
    This class provides an easy-to-use interface for:
    - Key generation and management
    - Data encryption and decryption
    - Homomorphic operations (addition, multiplication, etc.)
    - Serialization of keys and ciphertexts
    """
    
    def __init__(self, 
                 scheme: str = 'bfv',
                 poly_modulus_degree: int = 4096,
                 security_level: int = 128,
                 key_dir: str = 'core/keys',
                 # Configurable parameters
                 coeff_modulus_degree: Optional[List[int]] = None,
                 plain_modulus_bits: int = 20,
                 scale_factor: int = 20):
        """
        Initialize the SEAL engine.
        
        Args:
            scheme: Encryption scheme ('bfv', 'ckks', 'bgv')
            poly_modulus_degree: Polynomial modulus degree (must be power of 2)
            security_level: Security level in bits
            key_dir: Directory to store keys
            coeff_modulus_degree: List of bit sizes for coefficient modulus (default: auto)
            plain_modulus_bits: Bit size for plain modulus (default: 20)
            scale_factor: Bit size for CKKS scale (default: 20, i.e., 2^20)
        """
        self.scheme = scheme.lower()
        self.poly_modulus_degree = poly_modulus_degree
        self.security_level = security_level
        self.key_dir = key_dir
        
        # Store configurable parameters
        self.coeff_modulus_bits = coeff_modulus_degree  # Keep internal name for compatibility
        self.plain_modulus_bits = plain_modulus_bits
        self.scale_bits = scale_factor  # Keep internal name for compatibility
        self.scale = 2**scale_factor
        
        # Ensure key directory exists
        os.makedirs(key_dir, exist_ok=True)
        
        # Initialize SEAL context
        self._setup_context()
        
        # Initialize components
        self.keygen = None
        self.encryptor = None
        self.decryptor = None
        self.evaluator = None
        self.encoder = None
        
        # Load or generate keys
        self._initialize_keys()
    
    def _setup_context(self):
        """Set up the SEAL encryption context."""
        # Create encryption parameters
        self.params = seal.EncryptionParameters(self._get_scheme_type())
        self.params.set_poly_modulus_degree(self.poly_modulus_degree)
        
        # Set coefficient modulus based on scheme
        if self.scheme == 'bfv':
            self.params.set_coeff_modulus(
                seal.CoeffModulus.BFVDefault(self.poly_modulus_degree, seal.sec_level_type.tc128)
            )
            self.params.set_plain_modulus(
                seal.PlainModulus.Batching(self.poly_modulus_degree, self.plain_modulus_bits)
            )
        elif self.scheme == 'ckks':
            # Use only valid parameters for CKKS (see SEAL docs)
            if self.poly_modulus_degree <= 1024:
                raise ValueError("CKKS does not support poly_modulus_degree <= 1024. Use 2048 or higher.")
            
            # Use configurable coefficient modulus or defaults
            if self.coeff_modulus_bits is not None:
                # Use user-provided coefficient modulus
                self.params.set_coeff_modulus(
                    seal.CoeffModulus.Create(self.poly_modulus_degree, self.coeff_modulus_bits)
                )
            else:
                # Use default values based on poly_modulus_degree
                if self.poly_modulus_degree == 2048:
                    self.params.set_coeff_modulus(
                        seal.CoeffModulus.Create(self.poly_modulus_degree, [54, 55])
                    )
                elif self.poly_modulus_degree == 4096:
                    self.params.set_coeff_modulus(
                        seal.CoeffModulus.Create(self.poly_modulus_degree, [60, 40, 40])
                    )
                else:
                    # Default for other sizes
                    self.params.set_coeff_modulus(
                        seal.CoeffModulus.Create(self.poly_modulus_degree, [60, 40, 40, 60])
                    )
        elif self.scheme == 'bgv':
            self.params.set_coeff_modulus(
                seal.CoeffModulus.BFVDefault(self.poly_modulus_degree, seal.sec_level_type.tc128)
            )
            self.params.set_plain_modulus(
                seal.PlainModulus.Batching(self.poly_modulus_degree, self.plain_modulus_bits)
            )
        
        # Create context
        self.context = seal.SEALContext(self.params)
        
        # Verify context is valid
        if not self.context.parameters_set():
            raise ValueError("Invalid encryption parameters")
    
    def _get_scheme_type(self):
        """Get the SEAL scheme type enum."""
        scheme_map = {
            'bfv': seal.scheme_type.bfv,
            'ckks': seal.scheme_type.ckks,
            'bgv': seal.scheme_type.bgv
        }
        return scheme_map.get(self.scheme, seal.scheme_type.bfv)
    
    def _initialize_keys(self):
        """here we Initialize encryption keys"""
        self._generate_keys()
    
    def _generate_keys(self):
        """and here - Generate new encryption keys."""
        self.keygen = seal.KeyGenerator(self.context)
        self.secret_key = self.keygen.secret_key()
        self.public_key = seal.PublicKey()
        self.keygen.create_public_key(self.public_key)
        
        # Try to create relinearization keys for multiplication (optional)
        self.relin_keys = None
        try:
            self.relin_keys = seal.RelinKeys()
            self.keygen.create_relin_keys(self.relin_keys)
            print("✅ Relinearization keys created successfully")
        except Exception as e:
            print(f"⚠️ Relinearization keys not supported: {e}")
            print("⚠️ Multiplication operations will be limited")
        
        # Initialize components
        self.encryptor = seal.Encryptor(self.context, self.public_key)
        self.decryptor = seal.Decryptor(self.context, self.secret_key)
        self.evaluator = seal.Evaluator(self.context)
        
        # Initialize encoder based on scheme
        if self.scheme == 'bfv':
            self.encoder = seal.BatchEncoder(self.context)
        elif self.scheme == 'ckks':
            self.encoder = seal.CKKSEncoder(self.context)
        elif self.scheme == 'bgv':
            self.encoder = seal.BatchEncoder(self.context)
    
    def encrypt(self, data: Union[List, np.ndarray, float]) -> seal.Ciphertext:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt (list, numpy array, or float)
            
        Returns:
            Encrypted ciphertext
        """
        if self.encoder is None:
            raise RuntimeError("Encoder not initialized")
        if self.encryptor is None:
            raise RuntimeError("Encryptor not initialized")
        
        # Validate input type
        if not isinstance(data, (list, np.ndarray, int, float)):
            raise ValueError(f"Unsupported data type: {type(data)}. Expected list, numpy array, int, or float.")
        # Check for empty input
        if (isinstance(data, (list, np.ndarray)) and len(data) == 0):
            raise ValueError("Cannot encrypt empty list or array.")
            
        if self.scheme in ['bfv', 'bgv']:
            # For BFV/BGV, encode as integers
            if isinstance(data, (int, float)):
                data = np.array([int(data)], dtype=np.int64)
            elif isinstance(data, list):
                data = np.array(data, dtype=np.int64)
            elif isinstance(data, np.ndarray):
                data = data.astype(np.int64)
            
            plaintext = self.encoder.encode(data)
        elif self.scheme == 'ckks':
            # For CKKS, encode as floating point
            if isinstance(data, (int, float)):
                data = np.array([float(data)], dtype=np.float64)
            elif isinstance(data, list):
                data = np.array(data, dtype=np.float64)
            elif isinstance(data, np.ndarray):
                data = data.astype(np.float64)
            
            plaintext = self.encoder.encode(data, self.scale)
        else:
            raise ValueError(f"Unsupported scheme: {self.scheme}")
        
        return self.encryptor.encrypt(plaintext)
    
    def decrypt(self, ciphertext: seal.Ciphertext) -> List:
        """
        Decrypt data.
        
        Args:
            ciphertext: Encrypted ciphertext
            
        Returns:
            Decrypted data as a list
        """
        if self.decryptor is None:
            raise RuntimeError("Decryptor not initialized")
        if self.encoder is None:
            raise RuntimeError("Encoder not initialized")
            
        plaintext = self.decryptor.decrypt(ciphertext)
        
        if self.scheme in ['bfv', 'bgv']:
            result = self.encoder.decode(plaintext)
        elif self.scheme == 'ckks':
            result = self.encoder.decode(plaintext)
        else:
            raise ValueError(f"Unsupported scheme: {self.scheme}")
        # Always return a Python list for compatibility
        return result.tolist() if hasattr(result, 'tolist') else list(result)
    
    def add(self, ciphertext1: seal.Ciphertext, 
            ciphertext2: seal.Ciphertext) -> seal.Ciphertext:
        """Add two ciphertexts."""
        if self.evaluator is None:
            raise RuntimeError("Evaluator not initialized")
        return self.evaluator.add(ciphertext1, ciphertext2)
    
    def multiply(self, ciphertext1: seal.Ciphertext, 
                ciphertext2: seal.Ciphertext) -> seal.Ciphertext:
        """Multiply two ciphertexts."""
        if self.evaluator is None:
            raise RuntimeError("Evaluator not initialized")
        result = self.evaluator.multiply(ciphertext1, ciphertext2)
        if self.relin_keys is not None:
            self.evaluator.relinearize_inplace(result, self.relin_keys)
        else:
            print("⚠️ Relinearization skipped (keys not available)")
        return result
    
    def square(self, ciphertext: seal.Ciphertext) -> seal.Ciphertext:
        """Square a ciphertext."""
        if self.evaluator is None:
            raise RuntimeError("Evaluator not initialized")
        result = self.evaluator.square(ciphertext)
        if self.relin_keys is not None:
            self.evaluator.relinearize_inplace(result, self.relin_keys)
        else:
            print("⚠️ Relinearization skipped (keys not available)")
        return result
    
    def add_plain(self, ciphertext: seal.Ciphertext, 
                  plain_data: Union[List, np.ndarray, float]) -> seal.Ciphertext:
        """Add plaintext to ciphertext."""
        if self.evaluator is None:
            raise RuntimeError("Evaluator not initialized")
        if self.encoder is None:
            raise RuntimeError("Encoder not initialized")
            
        # Get the slot count to properly handle scalar operations
        slot_count = self.encoder.slot_count()
            
        if self.scheme in ['bfv', 'bgv']:
            if isinstance(plain_data, (int, float)):
                # Repeat the scalar value across all slots
                plain_data = np.full(slot_count, int(plain_data), dtype=np.int64)
            elif isinstance(plain_data, list):
                plain_data = np.array(plain_data, dtype=np.int64)
            elif isinstance(plain_data, np.ndarray):
                plain_data = plain_data.astype(np.int64)
            plaintext = self.encoder.encode(plain_data)
        elif self.scheme == 'ckks':
            if isinstance(plain_data, (int, float)):
                # Repeat the scalar value across all slots
                plain_data = np.full(slot_count, float(plain_data), dtype=np.float64)
            elif isinstance(plain_data, list):
                plain_data = np.array(plain_data, dtype=np.float64)
            elif isinstance(plain_data, np.ndarray):
                plain_data = plain_data.astype(np.float64)
            plaintext = self.encoder.encode(plain_data, self.scale)
        
        return self.evaluator.add_plain(ciphertext, plaintext)
    
    def multiply_plain(self, ciphertext: seal.Ciphertext, 
                      plain_data: Union[List, np.ndarray, float]) -> seal.Ciphertext:
        """Multiply ciphertext by plaintext."""
        if self.evaluator is None:
            raise RuntimeError("Evaluator not initialized")
        if self.encoder is None:
            raise RuntimeError("Encoder not initialized")
            
        # Get the slot count to properly handle scalar operations
        slot_count = self.encoder.slot_count()
            
        if self.scheme in ['bfv', 'bgv']:
            if isinstance(plain_data, (int, float)):
                # Repeat the scalar value across all slots
                plain_data = np.full(slot_count, int(plain_data), dtype=np.int64)
            elif isinstance(plain_data, list):
                plain_data = np.array(plain_data, dtype=np.int64)
            elif isinstance(plain_data, np.ndarray):
                plain_data = plain_data.astype(np.int64)
            plaintext = self.encoder.encode(plain_data)
        elif self.scheme == 'ckks':
            if isinstance(plain_data, (int, float)):
                # Repeat the scalar value across all slots
                plain_data = np.full(slot_count, float(plain_data), dtype=np.float64)
            elif isinstance(plain_data, list):
                plain_data = np.array(plain_data, dtype=np.float64)
            elif isinstance(plain_data, np.ndarray):
                plain_data = plain_data.astype(np.float64)
            plaintext = self.encoder.encode(plain_data, self.scale)
        
        return self.evaluator.multiply_plain(ciphertext, plaintext)
    
    def get_noise_budget(self, ciphertext: seal.Ciphertext) -> int:
        """Get the noise budget of a ciphertext."""
        if self.decryptor is None:
            raise RuntimeError("Decryptor not initialized")
        return self.decryptor.invariant_noise_budget(ciphertext)
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the current setup."""
        return {
            'scheme': self.scheme,
            'poly_modulus_degree': self.poly_modulus_degree,
            'security_level': self.security_level,
            'slot_count': self.encoder.slot_count() if self.encoder else None,
            'context_parameters_set': self.context.parameters_set(),
            # Include configurable parameters (using new names)
            'coeff_modulus_degree': self.coeff_modulus_bits,  # Use correct attribute name
            'plain_modulus_bits': self.plain_modulus_bits,
            'scale_factor': self.scale_bits,  # Map to new name
            'scale': self.scale
        } 