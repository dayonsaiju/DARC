from Crypto.Cipher import AES
from crypto.qrng import qrng_bytes

def encrypt(key, plaintext):
    nonce = qrng_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return nonce + tag + ciphertext

def decrypt(key, data):
    nonce = data[:12]
    tag = data[12:28]
    ciphertext = data[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()
