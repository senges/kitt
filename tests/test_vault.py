from kitt.crypto import *
from kitt.crypto import _forge_key

password = 'kitt_secret_password'
text = 'kitt_secret_text'
key = b'9d3qoWCH4zUmAF-qmwGIj4fuGn6TnJ6LqHswq1oYYWw='
secret = 'Z0FBQUFBQmk4VXB6cGhLdG9xLURrTEhOMDY0U0RTb2JZMVh4RVNQY0JEWF9seFpZQTk0R1Q2U09zU3YwNEZOVnhWWmVsWEloaVVqOHVCaXBwZFVxLUtHcVN6Y1ptaU9BMWUxZFRXcFkxanh2SmVNdm95OUVQQjg9'
base64 = 'a2l0dF9zZWNyZXRfdGV4dA=='
vault = [{
    'text': text,
    'base64': base64,
}]
secret_vault = 'Z0FBQUFBQmk4aXpVMThQRGhwbnFvWVAtZ1hQYmZHXzlGMkZ6c1AxRHpIbmtNOFVLZVdxRjRObVh6Zlk2azFEM1FEaWs5MWlZLWpUOVMzTkhjdzUzcXRXMGdxT3B3SzFzaktfN2JWaDRMRU5vSXl6MXBLQnVmdDh0TEo1SV9FTWllS25ETEpNWXd5N19vNjhsZ3ZzSlN5bUMxWm1SMVVaZk5hbEFvaXBjTk96TWM4eFdEVFlkTFRVPQ=='

def test_forge_key():
    computed = _forge_key(password)
    assert(computed == key)
    none = _forge_key(123)
    assert(none is None)


def test_cipher_text():
    ciphered = cipher_text(password, text)
    assert(ciphered is not None)
    none = cipher_text(password, 123)
    assert(none is None)


def test_unciper_text():
    unciphered = uncipher_text(password, secret)
    assert(unciphered == text)
    none = uncipher_text(password, text)
    assert(none is None)


def test_cipher_vault():
    ciphered = cipher_vault(password, vault)
    assert(isinstance(ciphered, str))
    none = cipher_vault(password, 123)
    assert(none is None)


def test_unciper_vault():
    unciphered = uncipher_vault(password, secret_vault)
    assert(unciphered == vault)
    none = uncipher_vault(password, vault)
    assert(none is None)


def test_b64():
    encoded = b64(text.encode('utf-8'))
    assert(encoded == base64)
    none = b64(base64)
    assert(none is None)


def test_b64d():
    decoded = b64d(base64).decode('utf-8')
    assert(decoded == text)
    none = b64d(text)
    assert(none is None)
