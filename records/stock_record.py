from enum import Enum
from uuid import uuid4
from typing import Literal, Optional, Tuple
from dataclasses import dataclass, field, fields
from datetime import datetime

import numpy as np

from records.records_helper import BetterDataclass

class Statuses(Enum):
    pending = "pending"  # Indicates a stock record is waiting for action
    tracked = "tracked"  # Indicates a stock record is currently being tracked
    archived = "archived"  # Indicates a stock record is archived and not active

def generate_uuid() -> str:
    """ Generates a unique identifier using UUID4. """
    return str(uuid4())

@dataclass
class StockRecord(BetterDataclass):
    uid: str = field(init=False)
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
        """ Calculates the total cost after the stock record is initialized. """
        self.update_total_cost()
        self.uid = generate_uuid()

    def create_new_uid(self):
        self.uid = generate_uuid()
    
    def update_total_cost(self):
        self.total_cost = np.double(self.shares * self.cost_per_share)
    
    @classmethod
    def from_uidless_tuple(cls, data_tuple: Tuple) -> 'StockRecord':
        """
        Converts a tuple containing ALL the necessary fields to a dataclass instance
        """
        # Instantiate the object without calling the __init__ or __post_init__
        instance = cls.__new__(cls)

        # Assign all attributes directly from the tuple to the instance
        setattr(instance, "uid", None)
        for field, value in zip(fields(cls)[1:], data_tuple):
            setattr(instance, field.name, value)
        
        return instance

    