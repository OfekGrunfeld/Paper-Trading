from dataclasses import dataclass, asdict, fields
from typing import Self

@dataclass
class Response:
    success: bool = False
    error: str = ""
    data: str = ""
    debug: str = ""
    extra: str = ""

    def reset(self) -> None:
        self.success = False
        self.error = ""
        self.data = ""
        self.debug = ""
        self.extra = ""
        
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        # Ensure all keys in the dictionary match the dataclass fields
        field_names: set[str] = {field.name for field in fields(cls)}
        filtered_data: dict = {key: value for key, value in data.items() if key in field_names}
        return cls(**filtered_data)