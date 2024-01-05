from enum import Enum
from hashlib import sha256
import logging as log
from sys import stdout

log.basicConfig(format='%(asctime)s -> %(message)s', datefmt='%d/%m/%Y %H:%M:%S', stream=stdout, level=log.INFO)

class Constants(Enum):
    HOST_IP = "127.0.0.1"
    HOST_PORT = 5555

def encode_string(string: str) -> str:
    """
    Encode a given string using the SHA-256 hashing algorithm.

    Parameters:
        string (str): The input string to be encoded.

    Returns:
        str: A hexadecimal representation of the SHA-256 hash of the input string.
    """
    if string is None:
        return False
    return sha256(string.encode("utf-8")).hexdigest()