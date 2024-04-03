from typing import Dict, Self, Literal
from dataclasses import dataclass, asdict, fields
from datetime import datetime

from utils.logger_script import logger

@dataclass
class StockRecord:
    timeframe: datetime = False
    action: Literal["buy", "sell"] = "invalid"
    amount: float = 0.0
    price: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        try:
            # Ensure all keys in the dictionary match the dataclass fields
            field_names: set[str] = {field.name for field in fields(cls)}
            filtered_data: dict = {key: value for key, value in data.items() if key in field_names}
            return cls(**filtered_data)
        except Exception as error:
            logger.error(f"Couldn't create new stock record from input dict {dict}. Error: {error}")
            return None
