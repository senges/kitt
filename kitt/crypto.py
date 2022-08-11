"""Handles basic crypto and kitt vault managment"""

import json
import base64
import getpass
from hashlib import sha256
from cryptography.fernet import Fernet


def _forge_key(data: str) -> bytes:
    try:
        _hash = sha256(data.encode('utf8'))
        key = _hash.digest()
        return base64.urlsafe_b64encode(key)
    except Exception:
        return None


def secure_prompt() -> str:
    """Show secure hidden pasword prompt

    Returns:
        str: data
    """
    try:
        return getpass.getpass()
    except Exception:
        return None


def cipher_vault(password: str, vault: list) -> str:
    """Cipher kitt vault

    Args:
        password (str): password as encryption key
        vault (list): list of secrets

    Returns:
        str: encrypted vault as string
    """
    try:
        if not isinstance(vault, list):
            raise ValueError
        vault = json.dumps(vault)
        return cipher_text(password, vault)
    except Exception:
        return None


def uncipher_vault(password: str, vault: str) -> list:
    """Uncipher kitt vault

    Args:
        password (str): password as decryption key
        vault (str): encrypted vault as string

    Returns:
        list: kitt vault as secret list
    """
    vault = uncipher_text(password, vault)
    try:
        vault = json.loads(vault)
        if not isinstance(vault, list):
            raise ValueError
        return vault
    except Exception:
        return None


def cipher_text(password: str, data: str) -> str:
    """Simple text encryption

    Args:
        password (str): password as encryption key
        data (str): data to cipher

    Returns:
        str: encrypted data as string
    """
    key = _forge_key(password)
    try:
        if not key:
            raise ValueError
        cipher = Fernet(key).encrypt(data.encode('utf-8'))
        return base64.b64encode(cipher).decode('utf-8')
    except Exception:
        return None


def uncipher_text(password: str, data: str) -> str:
    """Simple text decryption

    Args:
        password (str): password as decryption key
        data (str): data to decipher

    Returns:
        str: decrypted data as string
    """
    key = _forge_key(password)
    try:
        if not key:
            raise ValueError
        dcode = base64.b64decode(data)
        return Fernet(key).decrypt(dcode).decode('utf-8')
    except Exception:
        return None


def b64(data: bytes) -> str:
    """Base64 encode

    Args:
        data (bytes): data to encode

    Returns:
        str: encoded data
    """
    try:
        return base64.b64encode(data).decode('utf-8')
    except Exception:
        return None


def b64d(data: str) -> bytes:
    """Base64 decode

    Args:
        data (str): encoded data

    Returns:
        bytes: decoded data
    """
    try:
        return base64.b64decode(data.encode('utf-8'))
    except Exception:
        return None
