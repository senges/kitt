import json
import base64
import getpass
from cryptography.fernet import Fernet
from hashlib import sha256


def _forge_key(data: str) -> bytes:
    try:
        _hash = sha256(data.encode('utf8'))
        key = _hash.digest()
        return base64.urlsafe_b64encode(key)
    except Exception:
        return None


def secure_prompt() -> str:
    try:
        return getpass.getpass()
    except Exception:
        return None


def cipher_vault(password: str, vault: list) -> str:
    try:
        if not isinstance(vault, list):
            raise
        vault = json.dumps(vault)
        return cipher_text(password, vault)
    except Exception:
        return None


def uncipher_vault(password: str, vault: str) -> list:
    vault = uncipher_text(password, vault)
    try:
        vault = json.loads(vault)
        if not isinstance(vault, list):
            raise
        return vault
    except Exception:
        return None


def cipher_text(password: str, data: str) -> str:
    key = _forge_key(password)
    try:
        if not key:
            raise
        cipher = Fernet(key).encrypt(data.encode('utf-8'))
        return base64.b64encode(cipher).decode('utf-8')
    except Exception:
        return None


def uncipher_text(password: str, data: str) -> str:
    key = _forge_key(password)
    try:
        if not key:
            raise
        dcode = base64.b64decode(data)
        return Fernet(key).decrypt(dcode).decode('utf-8')
    except Exception:
        return None


def b64(data: bytes) -> str:
    try:
        return base64.b64encode(data).decode('utf-8')
    except Exception:
        return None


def b64d(data: str) -> bytes:
    try:
        return base64.b64decode(data.encode('utf-8'))
    except Exception:
        return None
