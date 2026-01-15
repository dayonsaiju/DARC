import hashlib
import json
from Crypto.Cipher import AES
from crypto.bb84_qkd import BB84QKD

class QuantumNonce:
    """Generate quantum-based nonces for AES-GCM"""
    
    def __init__(self):
        self.bb84 = BB84QKD(key_size=64)  # Smaller key for nonce generation
    
    def generate_nonce(self, counter):
        """Generate nonce combining constant and quantum randomness"""
        # Generate quantum random bytes
        quantum_bytes = self.bb84._quantum_random_bit().to_bytes(1, 'big')
        
        # Combine with counter and constant
        constant = b"DARC_QKD"
        counter_bytes = counter.to_bytes(4, 'big')
        
        # Create nonce
        nonce_data = constant + counter_bytes + quantum_bytes
        nonce = hashlib.sha256(nonce_data).digest()[:12]  # 96-bit nonce
        
        return nonce

def encrypt_message(key, message, counter):
    """Encrypt message using AES-256 GCM with quantum nonce"""
    try:
        # Generate quantum nonce
        nonce_generator = QuantumNonce()
        nonce = nonce_generator.generate_nonce(counter)
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        
        # Encrypt message
        ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
        
        # Return encrypted data with nonce and tag
        encrypted_data = {
            'nonce': nonce.hex(),
            'tag': tag.hex(),
            'ciphertext': ciphertext.hex(),
            'counter': counter
        }
        
        return json.dumps(encrypted_data)
        
    except Exception as e:
        print(f"Encryption error: {e}")
        return None

def decrypt_message(key, encrypted_data_json, counter):
    """Decrypt message using AES-256 GCM with quantum nonce"""
    try:
        # Parse encrypted data
        encrypted_data = json.loads(encrypted_data_json)
        nonce = bytes.fromhex(encrypted_data['nonce'])
        tag = bytes.fromhex(encrypted_data['tag'])
        ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
        
        # Verify counter matches
        if encrypted_data['counter'] != counter:
            print("Counter mismatch - possible replay attack")
            return None
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        
        # Decrypt and verify
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        
        return plaintext.decode('utf-8')
        
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def generate_session_key_from_qkd(sifted_key):
    """Generate AES-256 key from QKD sifted key"""
    if len(sifted_key) == 0:
        return None
    
    # Convert bits to bytes
    key_bytes = bytearray()
    for i in range(0, len(sifted_key), 8):
        if i + 8 <= len(sifted_key):
            byte_bits = sifted_key[i:i+8]
            byte = 0
            for j, bit in enumerate(byte_bits):
                byte |= bit << (7 - j)
            key_bytes.append(byte)
    
    # Hash to get 32-byte key
    if len(key_bytes) > 0:
        key_hash = hashlib.sha256(bytes(key_bytes)).digest()
        return key_hash
    
    return None
