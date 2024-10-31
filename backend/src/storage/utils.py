import hashlib

def hash_file(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()