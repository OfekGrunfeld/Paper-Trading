import hashlib

def _encode_string(string: str, hash_func) -> str:
    """
    Helper function to encode a string using a specified hash function.

    Args:
        string (str): The string to be encoded.
        hash_func (callable): A hashlib function that will be used for encoding.

    Returns:
        str: The encoded string in hexadecimal format.

    Raises:
        ValueError: If the input string is None.
    """
    if string is None:
        raise ValueError("Input string cannot be None")
    return hash_func(string.encode('utf-8')).hexdigest()

def encode_username(string: str) -> str:
    """
    Encode a given string using the SHA-256 hashing algorithm.
    
    Args:
        string (str): The username string to be encoded.
    
    Returns:
        str: The SHA-256 encoded string in hexadecimal format.
    
    Raises:
        ValueError: If the input string is None.
    """
    return _encode_string(string, hashlib.sha256)

def encode_password(string: str) -> str:
    """
    Encode a given string using the MD5 hashing algorithm.

    Args:
        string (str): The password string to be encoded.
    
    Returns:
        str: The MD5 encoded string in hexadecimal format.
    
    Raises:
        ValueError: If the input string is None.
    """
    return _encode_string(string, hashlib.sha224)
