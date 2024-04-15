
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from utils.constants import SECRET_KEY, CRYPTO_BACKEND

from utils.logger_script import logger
def decrypt(stored_encrypted_data: str) -> bytes:
    """
    Decrypt the encrypted data using AES-CBC.

    Args:
        stored_encrypted_data (str): The encrypted data, serialized as a string.

    Returns:
        bytes: The decrypted binary data.
    """
    algorithm, iv, binary_data_length, encrypted_data = stored_encrypted_data.split("$")
    assert algorithm == "AES.MODE_CBC"

    iv = b64decode(iv.encode())
    encrypted_data = b64decode(encrypted_data.encode())
    binary_data_length = int(binary_data_length)
    cipher = Cipher(
        algorithms.AES(b64decode(SECRET_KEY)), 
        modes.CBC(iv), 
        backend=CRYPTO_BACKEND
    )
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    return decrypted_data[:binary_data_length]


