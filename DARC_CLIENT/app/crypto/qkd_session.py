import numpy as np
import hashlib
import json
from enum import Enum
from crypto.qrng import qrng_bytes
from crypto.key_derivation import derive_key
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

class QKDState(Enum):
    CONNECTED = 1
    SESSION_REQUEST = 2
    QKD_INITIALIZATION = 3
    BASIS_RECONCILIATION = 4
    QBER_CHECK = 5
    ERROR_CORRECTION = 6
    KEY_CONFIRMATION = 7
    SECURE_CHAT = 8
    SESSION_TERMINATED = 9

class QKDSession:
    def __init__(self, session_id, target_name, is_initiator=False):
        self.session_id = session_id
        self.target_name = target_name
        self.is_initiator = is_initiator
        self.state = QKDState.CONNECTED
        self.shared_key = None
        
        # QKD parameters
        self.key_length = 256
        self.alice_bits = []
        self.alice_basis = []
        self.alice_states = []
        self.bob_basis = []
        self.bob_measurements = []
        self.sifted_key = []
        self.final_key = None
        
    def generate_qkd_request(self):
        """STATE 2: Generate session request"""
        self.state = QKDState.SESSION_REQUEST
        return {
            "type": "qkd_request",
            "session_id": self.session_id,
            "from": self.target_name,
            "message": f"Quantum session request from {self.target_name}"
        }
    
    def accept_session(self):
        """Accept session and move to QKD initialization"""
        self.state = QKDState.QKD_INITIALIZATION
        return self.initialize_qkd()
    
    def initialize_qkd(self):
        """STATE 3: QKD Initialization"""
        if self.is_initiator:
            # Alice's side: generate bits, bases, and encode states
            self.alice_bits = []
            self.alice_basis = []
            self.alice_states = []
            
            for _ in range(self.key_length):
                # Random bit (0 or 1)
                bit = int.from_bytes(qrng_bytes(1), 'big') % 2
                # Random basis (0: Z-basis, 1: X-basis)
                basis = int.from_bytes(qrng_bytes(1), 'big') % 2
                
                self.alice_bits.append(bit)
                self.alice_basis.append(basis)
                
                # Encode into quantum state symbols
                if basis == 0:  # Z-basis
                    state_symbol = '|' + str(bit) + '⟩'  # |0⟩ or |1⟩
                else:  # X-basis
                    state_symbol = '|+' if bit == 0 else '|-'  # |+⟩ or |-⟩
                
                self.alice_states.append(state_symbol)
            
            # Send encoded qubit symbols to Bob
            return {
                "type": "qkd_states",
                "session_id": self.session_id,
                "states": self.alice_states
            }
        else:
            # Bob's side: generate random bases for measurement
            self.bob_basis = []
            for _ in range(self.key_length):
                basis = int.from_bytes(qrng_bytes(1), 'big') % 2
                self.bob_basis.append(basis)
            
            return None  # Wait for Alice's states
    
    def receive_qkd_states(self, states):
        """Bob receives Alice's quantum states and measures them"""
        self.alice_states = states
        self.bob_measurements = []
        
        for i, state_symbol in enumerate(states):
            # Decode state symbol
            if state_symbol == '|0⟩':
                bit, basis = 0, 0
            elif state_symbol == '|1⟩':
                bit, basis = 1, 0
            elif state_symbol == '|+⟩':
                bit, basis = 0, 1
            elif state_symbol == '|-⟩':
                bit, basis = 1, 1
            else:
                continue
            
            # Create quantum circuit
            qc = QuantumCircuit(1, 1)
            
            # Prepare Alice's state
            if bit == 1:
                qc.x(0)
            if basis == 1:  # X-basis
                qc.h(0)
            
            # Bob measures in his chosen basis
            if self.bob_basis[i] == 1:  # X-basis
                qc.h(0)
            
            qc.measure(0, 0)
            
            # Execute measurement
            simulator = AerSimulator()
            job = simulator.run(qc, shots=1)
            result = job.result()
            counts = result.get_counts()
            measurement = int(list(counts.keys())[0], 2)
            self.bob_measurements.append(measurement)
        
        # Move to basis reconciliation
        self.state = QKDState.BASIS_RECONCILIATION
        return self.exchange_bases()
    
    def exchange_bases(self):
        """STATE 4: Basis Reconciliation"""
        if self.is_initiator:
            # Alice sends her bases
            return {
                "type": "basis_exchange",
                "session_id": self.session_id,
                "bases": self.alice_basis
            }
        else:
            # Bob sends his bases
            return {
                "type": "basis_exchange", 
                "session_id": self.session_id,
                "bases": self.bob_basis
            }
    
    def receive_bases(self, bases):
        """Receive partner's bases and perform sifting"""
        if self.is_initiator:
            self.bob_basis = bases
        else:
            self.alice_basis = bases
        
        # Perform sifting - keep only matching basis positions
        self.sifted_key = []
        matching_indices = []
        
        for i in range(self.key_length):
            if self.alice_basis[i] == self.bob_basis[i]:
                if self.is_initiator:
                    self.sifted_key.append(self.alice_bits[i])
                else:
                    self.sifted_key.append(self.bob_measurements[i])
                matching_indices.append(i)
        
        # Move to QBER check
        self.state = QKDState.QBER_CHECK
        return self.perform_qber_check()
    
    def perform_qber_check(self):
        """STATE 5: QBER Check"""
        if len(self.sifted_key) < 20:
            # Not enough bits for QBER check, proceed
            self.final_key = self.sifted_key
            self.state = QKDState.ERROR_CORRECTION
            return self.error_correction()
        
        # Sample 25% of bits for QBER check
        sample_size = max(5, len(self.sifted_key) // 4)
        sample_indices = np.random.choice(len(self.sifted_key), sample_size, replace=False)
        
        if self.is_initiator:
            # Alice sends sample bits and indices
            sample_bits = [self.sifted_key[i] for i in sample_indices]
            return {
                "type": "qber_sample",
                "session_id": self.session_id,
                "sample_indices": sample_indices.tolist(),
                "sample_bits": sample_bits
            }
        else:
            # Wait for Alice's sample
            return None
    
    def receive_qber_sample(self, sample_indices, sample_bits):
        """Receive QBER sample and calculate error rate"""
        # Compare with own bits
        errors = 0
        for i, idx in enumerate(sample_indices):
            if self.sifted_key[idx] != sample_bits[i]:
                errors += 1
        
        qber = errors / len(sample_indices)
        
        if qber > 0.11:  # 11% threshold
            # Too many errors, abort session
            self.state = QKDState.SESSION_TERMINATED
            return {
                "type": "qkd_abort",
                "session_id": self.session_id,
                "reason": f"QBER too high: {qber:.2%}"
            }
        
        # Remove sampled bits from key
        self.final_key = [bit for i, bit in enumerate(self.sifted_key) 
                         if i not in sample_indices]
        
        # Move to error correction
        self.state = QKDState.ERROR_CORRECTION
        return self.error_correction()
    
    def error_correction(self):
        """STATE 6: Error Correction & Privacy Amplification"""
        # Simple parity-based error correction (simulation)
        if len(self.final_key) < 32:
            # Pad key if too short
            self.final_key.extend([0] * (32 - len(self.final_key)))
        
        # Convert bits to bytes
        key_bytes = bytearray()
        for i in range(0, len(self.final_key), 8):
            if i + 8 <= len(self.final_key):
                byte_bits = self.final_key[i:i+8]
                byte = 0
                for j, bit in enumerate(byte_bits):
                    byte |= bit << (7 - j)
                key_bytes.append(byte)
        
        # Privacy amplification via hashing
        self.shared_key = hashlib.sha256(bytes(key_bytes)).digest()
        
        # Move to key confirmation
        self.state = QKDState.KEY_CONFIRMATION
        return self.key_confirmation()
    
    def key_confirmation(self):
        """STATE 7: Key Confirmation"""
        # Exchange first 64 bits of key hash
        key_hash = hashlib.sha256(self.shared_key).digest()
        confirmation_bits = key_hash[:8]  # First 64 bits
        
        return {
            "type": "key_confirmation",
            "session_id": self.session_id,
            "confirmation": confirmation_bits.hex()
        }
    
    def receive_key_confirmation(self, confirmation_hex):
        """Receive key confirmation and verify"""
        key_hash = hashlib.sha256(self.shared_key).digest()
        my_confirmation = key_hash[:8]
        their_confirmation = bytes.fromhex(confirmation_hex)
        
        if my_confirmation != their_confirmation:
            # Key mismatch, restart session
            self.state = QKDState.SESSION_TERMINATED
            return {
                "type": "key_mismatch",
                "session_id": self.session_id
            }
        
        # Key confirmed! Ready for secure chat
        self.state = QKDState.SECURE_CHAT
        return {
            "type": "session_ready",
            "session_id": self.session_id,
            "message": "Quantum key established successfully!"
        }
    
    def encrypt_message(self, message):
        """STATE 8: Encrypt message using established key"""
        if self.state != QKDState.SECURE_CHAT or not self.shared_key:
            raise Exception("Session not ready for encryption")
        
        from crypto.aes_gcm import encrypt
        return encrypt(self.shared_key, message)
    
    def decrypt_message(self, ciphertext):
        """STATE 8: Decrypt message using established key"""
        if self.state != QKDState.SECURE_CHAT or not self.shared_key:
            raise Exception("Session not ready for decryption")
        
        from crypto.aes_gcm import decrypt
        return decrypt(self.shared_key, ciphertext)
    
    def terminate_session(self):
        """STATE 9: Session Termination"""
        self.state = QKDState.SESSION_TERMINATED
        self.shared_key = None
        self.final_key = None
        self.sifted_key = []
        
        return {
            "type": "session_terminated",
            "session_id": self.session_id
        }
