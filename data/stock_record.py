from typing import Self, Literal, Optional
from dataclasses import dataclass, asdict, fields
from datetime import datetime

from utils.logger_script import logger

@dataclass
class StockRecord:
    symbol: str 
    timestamp: datetime 
    action: Literal["buy", "sell"]
    order_type: Literal["market_order", "limit_order","stop_loss"]
    shares: float
    price: float # at the time of action
    commission_price: float
    total_cost: float
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
