import hashlib

def derive_key(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()
