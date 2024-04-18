from uuid import uuid4
from typing import Self, Literal, Optional, Tuple, override
from dataclasses import dataclass, asdict, fields, field
from datetime import datetime
import numpy as np
from enum import Enum
from utils.logger_script import logger

class Statuses(Enum):
    pending = "pending"  # Indicates a stock record is waiting for action
    tracked = "tracked"  # Indicates a stock record is currently being tracked
    archived = "archived"  # Indicates a stock record is archived and not active

class BetterDataclass:
    """
    A base class that provides enhanced dataclass functionalities such as
    converting to/from dictionaries and tuples.
    """
    def to_dict(self) -> dict:
        """ Converts the dataclass instance to a dictionary. """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """ Creates an instance from a dictionary. """
        field_names = {field.name for field in fields(cls)}
        field_data = {key: data[key] for key in field_names if key in data}
        return cls(**field_data)
        
    def to_tuple(self) -> Tuple:
        """ Converts the dataclass instance to a tuple. """
        return tuple(getattr(self, field.name) for field in fields(self))
    
    @classmethod
    def from_tuple(cls, data_tuple: Tuple) -> 'BetterDataclass':
        """
        Converts a tuple containing ALL the necessary fields to a dataclass instance
        """
        field_dict = {field.name: value for field, value in zip(fields(cls), data_tuple)}
        return cls(**field_dict)
    
    def __str__(self):
        """ Generates a string representation of the instance. """
        return f"{self.__class__.__name__}({', '.join(f'{f.name}={getattr(self, f.name)}' for f in fields(self))})"

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
        self.total_cost = np.double(self.shares * self.cost_per_share)
        self.uid = generate_uuid()

    def create_new_uid(self):
        self.uid = generate_uuid()
    
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


    
    