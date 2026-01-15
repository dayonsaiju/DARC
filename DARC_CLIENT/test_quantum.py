#!/usr/bin/env python3
"""
Test script for DARC Quantum Chat System
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from crypto.bb84_qkd import BB84QKD, QUBIT_STATES, REVERSE_QUBIT_STATES
from crypto.aes_quantum import encrypt_message, decrypt_message
from session.quantum_session import QuantumSession
import asyncio

def test_bb84_qkd():
    """Test BB84 QKD implementation"""
    print("🔬 Testing BB84 Quantum Key Distribution...")
    
    bb84 = BB84QKD(key_size=256)
    
    # Test quantum random generation
    print("  📊 Generating quantum random bits and bases...")
    alice_bits, alice_bases = bb84.generate_qrng_bits_and_bases(256)
    bob_bases = []
    for _ in range(256):
        bob_bases.append(bb84._quantum_random_basis())
    
    print(f"  ✅ Generated {len(alice_bits)} bits and bases")
    
    # Test qubit preparation
    print("  🔄 Preparing qubits...")
    qubits = bb84.prepare_qubits(alice_bits, alice_bases)
    print(f"  ✅ Prepared {len(qubits)} qubits")
    
    # Test measurement
    print("  📏 Measuring qubits...")
    measurements = bb84.measure_qubits(qubits, bob_bases)
    print(f"  ✅ Measured {len(measurements)} qubits")
    
    # Test sifting
    print("  🔍 Sifting keys...")
    sifted_key, alice_sifted, bob_sifted = bb84.sift_keys(
        alice_bits, alice_bases, measurements, bob_bases
    )
    print(f"  ✅ Sifted key length: {len(sifted_key)} bits")
    
    # Test QBER calculation
    print("  📈 Calculating QBER...")
    qber = bb84.calculate_qber(alice_sifted, bob_sifted)
    print(f"  ✅ QBER: {qber:.2f}%")
    
    # Test final key generation
    print("  🔑 Generating final key...")
    final_key = bb84.generate_final_key(sifted_key)
    print(f"  ✅ Final key: {len(final_key)} bytes")
    
    return qber < 11.0, final_key

def test_aes_encryption():
    """Test AES-256 GCM encryption with quantum nonce"""
    print("\n🔐 Testing AES-256 GCM Encryption...")
    
    # Test key (exactly 32 bytes for AES-256)
    key = b'test_key_32_bytes_long__1234567!'
    
    # Test message
    message = "Hello, quantum world!"
    
    # Test encryption
    print("  🔒 Encrypting message...")
    encrypted = encrypt_message(key, message, 1)
    print(f"  ✅ Encrypted: {len(encrypted)} characters")
    
    # Test decryption
    print("  🔓 Decrypting message...")
    decrypted = decrypt_message(key, encrypted, 1)
    print(f"  ✅ Decrypted: {decrypted}")
    
    return message == decrypted

def test_qubit_states():
    """Test qubit state mappings"""
    print("\n⚛️ Testing Qubit State Mappings...")
    
    # Test all qubit states
    test_cases = [
        (0, 0, "|0⟩"),
        (1, 0, "|1⟩"),
        (0, 1, "|+⟩"),
        (1, 1, "|-⟩"),
    ]
    
    for bit, basis, expected_state in test_cases:
        actual_state = QUBIT_STATES[(bit, basis)]
        reverse_bit, reverse_basis = REVERSE_QUBIT_STATES[expected_state]
        
        print(f"  🔄 Bit {bit} + Basis {basis} → {actual_state}")
        
        assert actual_state == expected_state, f"Expected {expected_state}, got {actual_state}"
        assert reverse_bit == bit and reverse_basis == basis, f"Reverse mapping failed for {expected_state}"
    
    print("  ✅ All qubit state mappings correct!")
    return True

def main():
    """Run all tests"""
    print("🚀 DARC Quantum Chat System Test Suite")
    print("=" * 50)
    
    try:
        # Test qubit states
        qubit_ok = test_qubit_states()
        
        # Test BB84 QKD
        qkd_success, final_key = test_bb84_qkd()
        
        # Test AES encryption
        aes_ok = test_aes_encryption()
        
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"  ⚛️ Qubit States: {'✅ PASS' if qubit_ok else '❌ FAIL'}")
        print(f"  🔬 BB84 QKD: {'✅ PASS' if qkd_success else '❌ FAIL'}")
        print(f"  🔐 AES Encryption: {'✅ PASS' if aes_ok else '❌ FAIL'}")
        
        if all([qubit_ok, qkd_success, aes_ok]):
            print("\n🎉 All tests passed! Quantum chat system is ready!")
            return True
        else:
            print("\n❌ Some tests failed. Check the implementation.")
            return False
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
