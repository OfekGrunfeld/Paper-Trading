from typing import Self, Literal, Optional
from dataclasses import dataclass, asdict, fields, field
from datetime import datetime
import numpy as np
from enum import Enum

from utils.logger_script import logger

class Statuses(Enum):
    # for stock record creation - stocks that should be tracked
    pending = "pending"
    # for stocks that need to be tracked
    tracked = "tracked"
    # for stocks in the transaction history or 
    archived = "archived"

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
    timestamp: datetime = field(init=False, default=datetime.now())
    symbol: str 
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    shares: np.double 
    cost_per_share: np.double
    total_cost: np.double = field(init=False)
    status: str = field(default=Statuses.pending.value)
    notes: Optional[str] = None

    def __post_init__(self):
        self.total_cost = np.double(self.shares * self.cost_per_share)
    
    