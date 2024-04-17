from typing import Self, Literal, Optional
from dataclasses import dataclass, asdict, fields
from datetime import datetime
import numpy as np

from utils.logger_script import logger


class BetterDataclass:
    """
    Added functionality to export dataclasses as dictionaries
    and also make them from dictionaries
    """
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
            logger.error(f"Couldn't create new {cls.__name__} record from input dict {data}. Error: {error}")
            return None

@dataclass
class StockRecord(BetterDataclass):
    timestamp: datetime 
    symbol: str 
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    shares: float 
    cost_per_share: np.double
    total_cost: np.double
    status: str
    notes: Optional[str]
    
    