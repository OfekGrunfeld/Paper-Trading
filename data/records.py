from typing import Self, Literal, Optional, Tuple, override
from dataclasses import dataclass, asdict, fields, field
from datetime import datetime
import numpy as np
from enum import Enum
from uuid import uuid4
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
        
    def to_tuple(self) -> Tuple:
        """
        Converts the BetterDataclass instance into a tuple.
        """
        return tuple(getattr(self, f.name) for f in fields(self))
    
    @classmethod
    def from_tuple(cls, data_tuple: Tuple) -> 'StockRecord':
        """
        Creates an instance of BetterDataclass from a tuple by mapping tuple values to the fields.

        Args:
            data_tuple (Tuple): A tuple containing all the necessary fields for BetterDataclass.

        Returns:
            BetterDataclass: An instance of BetterDataclass initialized from the tuple.
        """
        field_names = [f.name for f in fields(cls)]
        field_dict = {field: data_tuple[i] for i, field in enumerate(field_names) if i < len(data_tuple)}
        return cls(**field_dict)
    
    def __str__(self):
        # Build a string representation dynamically using field names and values
        field_strs = [f"{field.name}: {getattr(self, field.name)}" for field in fields(self)]
        return f"{self.__class__.__name__}: {', '.join(field_strs)}"

@dataclass
class StockRecord(BetterDataclass):
    uid: str = field(init=False, default=str(uuid4()))
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

    @override
    @classmethod
    def from_tuple(cls, data_tuple: Tuple) -> 'StockRecord':
        """
        Creates an instance of StockRecord from a tuple by mapping tuple values directly to the fields.
        This method explicitly sets `uid` and `timestamp` from the tuple assuming they are at specific
        indices, so the tuple should exactly match the order of fields in the dataclass.

        Args:
            data_tuple (Tuple): A tuple containing all the necessary fields for StockRecord,
                                including `uid` and `timestamp`.

        Returns:
            StockRecord: An instance of StockRecord initialized from the tuple.
        """
        # Instantiate the object without calling the __init__ or __post_init__
        instance = cls.__new__(cls)

        # Assign all attributes directly from the tuple to the instance
        for field, value in zip(fields(cls), data_tuple):
            setattr(instance, field.name, value)

        # Recalculate any dependent fields if necessary
        instance.total_cost = np.double(instance.shares * instance.cost_per_share)

        return instance


    
    