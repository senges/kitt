import json
import base64
import getpass
from cryptography.fernet import Fernet
from hashlib import sha256

def _forge_key(data: str) -> bytes:
    _hash = sha256(data.encode('utf8'))
    key = _hash.digest()
    key = base64.urlsafe_b64encode(key)

    return key

def secure_prompt() -> str:
    try:
        return getpass.getpass()
    except:
        return None

def cipher_vault(password: str, vault: list) -> str:
    vault = json.dumps(vault)
    return cipher_text(password, vault)

def uncipher_vault(password: str, vault: str) -> list:
    vault = uncipher_text(password, vault)
    return json.loads(vault)

def cipher_text(password: str, data: str) -> str:
    key = _forge_key(password)
    try:
        cipher = Fernet(key).encrypt(data.encode('utf-8'))
        return base64.b64encode(cipher).decode('utf-8')
    except:
        return None

def uncipher_text(password: str, data: str) -> str:
    key = _forge_key(password)
    try:
        dcode = base64.b64decode(data)
        return Fernet(key).decrypt(dcode).decode('utf-8')
    except:
        return None

def b64(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')

def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode('utf-8'))