from dataclasses import dataclass, asdict, fields
from typing import Self

@dataclass
class Response:
    success: bool = False
    message: str = ""
    error: str = ""
    debug: str = ""
    extra: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        # Ensure all keys in the dictionary match the dataclass fields
        field_names: set[str] = {field.name for field in fields(cls)}
        filtered_data: dict = {key: value for key, value in data.items() if key in field_names}
        return cls(**filtered_data)