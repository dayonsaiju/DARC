import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import hashlib

class QuantumQubit:
    """Simulated quantum qubit for BB84 protocol"""
    
    def __init__(self, bit, basis):
        self.bit = bit
        self.basis = basis
        self.state = self._encode_qubit(bit, basis)
    
    def _encode_qubit(self, bit, basis):
        """Encode bit into quantum state based on basis"""
        if basis == 0:  # Z basis
            return f"|{bit}⟩"  # |0⟩ or |1⟩
        else:  # X basis
            return "|+⟩" if bit == 0 else "|-⟩"  # |+⟩ or |-⟩
    
    def measure(self, measurement_basis):
        """Measure qubit in specified basis"""
        if self.basis == measurement_basis:
            # Same basis - correct measurement
            return self.bit
        else:
            # Different basis - random measurement (50/50)
            return np.random.randint(0, 2)

class BB84QKD:
    """Complete BB84 Quantum Key Distribution implementation"""
    
    def __init__(self, key_size=256):
        self.key_size = key_size
        self.simulator = AerSimulator()
    
    def generate_qrng_bits_and_bases(self, size):
        """Generate quantum random bits and bases using Qiskit"""
        bits = []
        bases = []
        
        for _ in range(size):
            # Generate quantum random bit
            bit = self._quantum_random_bit()
            # Generate quantum random basis
            basis = self._quantum_random_basis()
            
            bits.append(bit)
            bases.append(basis)
        
        return bits, bases
    
    def _quantum_random_bit(self):
        """Generate single quantum random bit"""
        qc = QuantumCircuit(1, 1)
        qc.h(0)  # Create superposition
        qc.measure(0, 0)
        
        job = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        return int(list(counts.keys())[0], 2)
    
    def _quantum_random_basis(self):
        """Generate quantum random basis (0: Z, 1: X)"""
        qc = QuantumCircuit(1, 1)
        qc.h(0)  # Create superposition
        qc.measure(0, 0)
        
        job = self.simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        return int(list(counts.keys())[0], 2)
    
    def prepare_qubits(self, bits, bases):
        """Prepare qubits from bits and bases"""
        qubits = []
        for bit, basis in zip(bits, bases):
            qubit = QuantumQubit(bit, basis)
            qubits.append(qubit)
        return qubits
    
    def measure_qubits(self, qubits, bases):
        """Measure qubits in specified bases"""
        measurements = []
        for qubit, basis in zip(qubits, bases):
            measurement = qubit.measure(basis)
            measurements.append(measurement)
        return measurements
    
    def sift_keys(self, alice_bits, alice_bases, bob_bits, bob_bases):
        """Sift keys by keeping only measurements with same basis"""
        sifted_key = []
        alice_sifted = []
        bob_sifted = []
        
        for i in range(len(alice_bases)):
            if alice_bases[i] == bob_bases[i]:
                sifted_key.append(bob_bits[i])
                alice_sifted.append(alice_bits[i])
                bob_sifted.append(bob_bits[i])
        
        return sifted_key, alice_sifted, bob_sifted
    
    def calculate_qber(self, alice_sifted, bob_sifted):
        """Calculate Quantum Bit Error Rate"""
        if len(alice_sifted) == 0:
            return 100.0  # No matching bases
        
        errors = 0
        for alice_bit, bob_bit in zip(alice_sifted, bob_sifted):
            if alice_bit != bob_bit:
                errors += 1
        
        qber = (errors / len(alice_sifted)) * 100
        return qber
    
    def error_correction(self, alice_sifted, bob_sifted):
        """Simple error correction using parity checks"""
        if len(alice_sifted) == 0:
            return alice_sifted, bob_sifted
        
        # For simplicity, use majority voting on blocks of 3
        corrected_alice = []
        corrected_bob = []
        
        block_size = 3
        for i in range(0, len(alice_sifted), block_size):
            alice_block = alice_sifted[i:i+block_size]
            bob_block = bob_sifted[i:i+block_size]
            
            if len(alice_block) >= 3:
                # Majority vote
                alice_majority = max(set(alice_block), key=alice_block.count)
                bob_majority = max(set(bob_block), key=bob_block.count)
                
                corrected_alice.extend([alice_majority] * len(alice_block))
                corrected_bob.extend([bob_majority] * len(bob_block))
            else:
                corrected_alice.extend(alice_block)
                corrected_bob.extend(bob_block)
        
        return corrected_alice, corrected_bob
    
    def privacy_amplification(self, sifted_key):
        """Privacy amplification using hash function"""
        if len(sifted_key) == 0:
            return []
        
        # Convert bits to bytes
        key_bytes = bytearray()
        for i in range(0, len(sifted_key), 8):
            if i + 8 <= len(sifted_key):
                byte_bits = sifted_key[i:i+8]
                byte = 0
                for j, bit in enumerate(byte_bits):
                    byte |= bit << (7 - j)
                key_bytes.append(byte)
        
        # Hash for privacy amplification
        if len(key_bytes) > 0:
            hash_result = hashlib.sha256(bytes(key_bytes)).digest()
            # Convert hash back to bits
            final_key = []
            for byte in hash_result:
                for i in range(8):
                    final_key.append((byte >> (7 - i)) & 1)
            return final_key[:256]  # Return 256-bit key
        
        return []
    
    def generate_final_key(self, sifted_key):
        """Generate final shared key from sifted key"""
        final_key_bits = self.privacy_amplification(sifted_key)
        
        # Convert to 32-byte key for AES-256
        key_bytes = bytearray()
        for i in range(0, len(final_key_bits), 8):
            if i + 8 <= len(final_key_bits):
                byte_bits = final_key_bits[i:i+8]
                byte = 0
                for j, bit in enumerate(byte_bits):
                    byte |= bit << (7 - j)
                key_bytes.append(byte)
        
        # Ensure 32 bytes (256 bits)
        while len(key_bytes) < 32:
            key_bytes.append(0)
        
        return bytes(key_bytes[:32])

# Qubit state mappings for communication
QUBIT_STATES = {
    (0, 0): "|0⟩",  # 0 with Z basis
    (1, 0): "|1⟩",  # 1 with Z basis  
    (0, 1): "|+⟩",  # 0 with X basis
    (1, 1): "|-⟩",  # 1 with X basis
}

REVERSE_QUBIT_STATES = {
    "|0⟩": (0, 0),
    "|1⟩": (1, 0),
    "|+⟩": (0, 1),
    "|-⟩": (1, 1),
}
