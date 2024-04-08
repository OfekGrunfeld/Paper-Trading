from typing import Self, Literal, Optional
from dataclasses import dataclass, asdict, fields
from datetime import datetime

import numpy as np

from utils.logger_script import logger

@dataclass
class StockRecord:
    timestamp: datetime 
    symbol: str 
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    shares: float 
    # price: float # at the time of action, same as quantity for market currently
    total_cost: np.double

    notes: Optional[str]
    
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
