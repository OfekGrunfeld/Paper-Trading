from typing import Tuple
from dataclasses import asdict, fields

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
        # Instantiate the object without calling the __init__ or __post_init__
        instance = cls.__new__(cls)

        # Assign all attributes directly from the tuple to the instance
        for field, value in zip(fields(cls), data_tuple):
            setattr(instance, field.name, value)

        # Recalculate any dependent fields if necessary
        instance.__post_init__()

        return instance
    
    def __str__(self):
        """ Generates a string representation of the instance. """
        return f"{self.__class__.__name__}({', '.join(f'{f.name}={getattr(self, f.name)}' for f in fields(self))})"
