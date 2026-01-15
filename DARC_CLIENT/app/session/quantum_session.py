import asyncio
import json
import hashlib
from enum import Enum
from typing import Optional, Dict, Any
from crypto.bb84_qkd import BB84QKD, QUBIT_STATES, REVERSE_QUBIT_STATES

class SessionState(Enum):
    IDLE = "idle"
    SESSION_REQUESTED = "session_requested"
    SESSION_ACCEPTED = "session_accepted"
    QKD_EXCHANGING = "qkd_exchanging"
    KEY_ESTABLISHED = "key_established"
    SESSION_ACTIVE = "session_active"
    SESSION_TERMINATED = "session_terminated"

class QuantumSession:
    """Manages quantum session between two users"""
    
    def __init__(self, user_id: str, peer_id: str, signaling_client):
        self.user_id = user_id
        self.peer_id = peer_id
        self.signaling_client = signaling_client
        self.state = SessionState.IDLE
        self.bb84 = BB84QKD(key_size=256)
        
        # QKD data
        self.alice_bits = []
        self.alice_bases = []
        self.bob_bases = []
        self.qubits = []
        self.shared_key = None
        self.qber = 0.0
        
        # Message encryption
        self.message_counter = 0
        
    async def start_session(self):
        """Start a quantum session with peer"""
        if self.state != SessionState.IDLE:
            return False
            
        self.state = SessionState.SESSION_REQUESTED
        
        # Send session request
        await self.signaling_client.send_session_request(self.peer_id, {
            "type": "session_request",
            "from": self.user_id,
            "to": self.peer_id
        })
        
        return True
    
    async def handle_session_request(self, request_data):
        """Handle incoming session request"""
        if self.state != SessionState.IDLE:
            return False
            
        self.state = SessionState.SESSION_ACCEPTED
        
        # Accept session request
        await self.signaling_client.send_session_response(self.peer_id, {
            "type": "session_accept",
            "from": self.user_id,
            "to": self.peer_id
        })
        
        # Start QKD process
        asyncio.create_task(self.start_qkd_as_receiver())
        
        return True
    
    async def handle_session_accept(self, accept_data):
        """Handle session acceptance"""
        if self.state != SessionState.SESSION_REQUESTED:
            return False
            
        self.state = SessionState.QKD_EXCHANGING
        
        # Start QKD process as sender
        asyncio.create_task(self.start_qkd_as_sender())
        
        return True
    
    async def start_qkd_as_sender(self):
        """Start BB84 QKD as sender (Alice)"""
        try:
            # Generate quantum random bits and bases
            self.alice_bits, self.alice_bases = self.bb84.generate_qrng_bits_and_bases(256)
            
            # Prepare qubits
            self.qubits = self.bb84.prepare_qubits(self.alice_bits, self.alice_bases)
            
            # Convert qubits to transmittable format
            qubit_states = []
            for qubit in self.qubits:
                qubit_states.append(qubit.state)
            
            # Send qubits to receiver
            await self.signaling_client.send_qkd_data(self.peer_id, {
                "type": "qkd_qubits",
                "from": self.user_id,
                "to": self.peer_id,
                "qubits": qubit_states
            })
            
        except Exception as e:
            print(f"Error in QKD sender: {e}")
            await self.restart_session()
    
    async def start_qkd_as_receiver(self):
        """Start BB84 QKD as receiver (Bob)"""
        try:
            # Generate random bases for measurement
            self.bob_bases = []
            for _ in range(256):
                basis = self.bb84._quantum_random_basis()
                self.bob_bases.append(basis)
            
            # Send bases to sender
            await self.signaling_client.send_qkd_data(self.peer_id, {
                "type": "qkd_bases",
                "from": self.user_id,
                "to": self.peer_id,
                "bases": self.bob_bases
            })
            
        except Exception as e:
            print(f"Error in QKD receiver: {e}")
            await self.restart_session()
    
    async def handle_qkd_qubits(self, data):
        """Handle received qubits (as receiver)"""
        if self.state != SessionState.QKD_EXCHANGING:
            return
            
        try:
            qubit_states = data["qubits"]
            
            # Measure qubits with our bases
            measurements = []
            for i, qubit_state in enumerate(qubit_states):
                # Convert state back to bit and basis
                bit, basis = REVERSE_QUBIT_STATES[qubit_state]
                qubit = self.bb84.prepare_qubits([bit], [basis])[0]
                
                # Measure with our basis
                measurement = qubit.measure(self.bob_bases[i])
                measurements.append(measurement)
            
            # Send measurements back
            await self.signaling_client.send_qkd_data(self.peer_id, {
                "type": "qkd_measurements",
                "from": self.user_id,
                "to": self.peer_id,
                "measurements": measurements
            })
            
        except Exception as e:
            print(f"Error handling qubits: {e}")
            await self.restart_session()
    
    async def handle_qkd_bases(self, data):
        """Handle received bases (as sender)"""
        if self.state != SessionState.QKD_EXCHANGING:
            return
            
        try:
            self.bob_bases = data["bases"]
            
            # Measure our qubits with Bob's bases
            measurements = []
            for i, qubit in enumerate(self.qubits):
                measurement = qubit.measure(self.bob_bases[i])
                measurements.append(measurement)
            
            # Send measurements to Bob
            await self.signaling_client.send_qkd_data(self.peer_id, {
                "type": "qkd_measurements",
                "from": self.user_id,
                "to": self.peer_id,
                "measurements": measurements
            })
            
        except Exception as e:
            print(f"Error handling bases: {e}")
            await self.restart_session()
    
    async def handle_qkd_measurements(self, data):
        """Handle received measurements and complete QKD"""
        if self.state != SessionState.QKD_EXCHANGING:
            return
            
        try:
            measurements = data["measurements"]
            
            # Sift keys
            sifted_key, alice_sifted, bob_sifted = self.bb84.sift_keys(
                self.alice_bits, self.alice_bases, measurements, self.bob_bases
            )
            
            # Calculate QBER
            self.qber = self.bb84.calculate_qber(alice_sifted, bob_sifted)
            
            if self.qber > 11.0:
                # QBER too high, restart session
                print(f"QBER too high: {self.qber}%, restarting session")
                await self.restart_session()
                return
            
            # Error correction
            corrected_alice, corrected_bob = self.bb84.error_correction(alice_sifted, bob_sifted)
            
            # Privacy amplification and final key generation
            self.shared_key = self.bb84.generate_final_key(corrected_alice)
            
            # Verify key consistency
            await self.verify_key_consistency()
            
        except Exception as e:
            print(f"Error in QKD completion: {e}")
            await self.restart_session()
    
    async def verify_key_consistency(self):
        """Verify that both parties have the same key"""
        if not self.shared_key:
            await self.restart_session()
            return
            
        # Share a small part of the key for verification
        verification_hash = hashlib.sha256(self.shared_key[:16]).hexdigest()
        
        await self.signaling_client.send_qkd_data(self.peer_id, {
            "type": "key_verification",
            "from": self.user_id,
            "to": self.peer_id,
            "verification_hash": verification_hash
        })
    
    async def handle_key_verification(self, data):
        """Handle key verification"""
        try:
            verification_hash = data["verification_hash"]
            my_hash = hashlib.sha256(self.shared_key[:16]).hexdigest()
            
            if verification_hash == my_hash:
                # Keys match, session established
                self.state = SessionState.KEY_ESTABLISHED
                print(f"✅ Quantum key established with {self.peer_id}")
                
                # Notify peer
                await self.signaling_client.send_qkd_data(self.peer_id, {
                    "type": "key_confirmed",
                    "from": self.user_id,
                    "to": self.peer_id
                })
                
                # Start active session
                self.state = SessionState.SESSION_ACTIVE
                
            else:
                # Keys don't match, restart
                print("❌ Key verification failed, restarting session")
                await self.restart_session()
                
        except Exception as e:
            print(f"Error in key verification: {e}")
            await self.restart_session()
    
    async def handle_key_confirmed(self, data):
        """Handle key confirmation from peer"""
        self.state = SessionState.SESSION_ACTIVE
        print(f"✅ Quantum session active with {self.peer_id}")
    
    async def restart_session(self):
        """Restart the quantum session"""
        print(f"🔄 Restarting quantum session with {self.peer_id}")
        
        # Reset all QKD data
        self.alice_bits = []
        self.alice_bases = []
        self.bob_bases = []
        self.qubits = []
        self.shared_key = None
        self.qber = 0.0
        self.message_counter = 0
        
        # Reset state and restart
        self.state = SessionState.SESSION_REQUESTED
        
        # Send new session request
        await self.signaling_client.send_session_request(self.peer_id, {
            "type": "session_restart",
            "from": self.user_id,
            "to": self.peer_id
        })
    
    async def terminate_session(self):
        """Terminate the quantum session"""
        self.state = SessionState.SESSION_TERMINATED
        
        # Clear all sensitive data
        self.alice_bits = []
        self.alice_bases = []
        self.bob_bases = []
        self.qubits = []
        self.shared_key = None
        self.qber = 0.0
        self.message_counter = 0
        
        # Notify peer
        await self.signaling_client.send_session_request(self.peer_id, {
            "type": "session_terminated",
            "from": self.user_id,
            "to": self.peer_id
        })
        
        print(f"🔒 Quantum session terminated with {self.peer_id}")
    
    def encrypt_message(self, message):
        """Encrypt message using quantum key"""
        if not self.shared_key or self.state != SessionState.SESSION_ACTIVE:
            return None
            
        from crypto.aes_quantum import encrypt_message
        return encrypt_message(self.shared_key, message, self.message_counter)
    
    def decrypt_message(self, encrypted_data):
        """Decrypt message using quantum key"""
        if not self.shared_key or self.state != SessionState.SESSION_ACTIVE:
            return None
            
        from crypto.aes_quantum import decrypt_message
        return decrypt_message(self.shared_key, encrypted_data, self.message_counter)
    
    def increment_message_counter(self):
        """Increment message counter for unique nonces"""
        self.message_counter += 1
