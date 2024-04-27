from typing import Union
import os
from base64 import b64decode
import json

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from utils.env_variables import SECRET_KEY


from utils.logger_script import logger

backend = default_backend()

def pad_binary_data(binary_data: bytes) -> bytes:
    """
    Pad the binary data with null bytes to ensure the length is a multiple of the block size.

    This is necessary because the AES cipher requires the input data to be a multiple of the block size (16 bytes).

    Args:
        binary_data (bytes): The binary data to be padded.

    Returns:
        bytes: The padded binary data.
    """
    try:
        block_size = 16
        padding_length = block_size - (len(binary_data) % block_size)
        return binary_data + b"\0" * padding_length
    except Exception as error:
        logger.error(f"Error padding data. Error: {error}")

def decrypt(stored_encrypted_data: str) -> Union[dict, str]:
    """
    Decrypt the encrypted data using AES-CBC.

    Args:
        stored_encrypted_data (str): The encrypted data, serialized as a string.

    Returns:
        bytes: The decrypted binary data.
    """
    iv, binary_data_length, encrypted_data = stored_encrypted_data.split("$")

    iv = b64decode(iv.encode())
    encrypted_data = b64decode(encrypted_data.encode())
    binary_data_length = int(binary_data_length)
    cipher = Cipher(
        algorithms.AES(b64decode(SECRET_KEY)), 
        modes.CBC(iv), 
        backend=backend
    )
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    decrypted_data2: bytes = decrypted_data[:binary_data_length]
    decrypted_data_decoded = decrypted_data2.decode("utf-8")
    if decrypted_data_decoded.startswith("{"):
        decrypted_data_decoded = json.loads(decrypted_data_decoded)
    return decrypted_data_decoded


