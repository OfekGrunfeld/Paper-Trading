import uuid

def generate_uuid() -> str:
    """
    Generatea a unique user identifier
    """
    return str(uuid.uuid4())
