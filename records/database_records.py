from enum import Enum

class DatabasesNames(Enum):
    """
    Names of the databases
    """
    userbase = "userbase"
    transactions = "transactions"
    portfolios = "portfolios"

    @classmethod
    def __contains__(cls, item):
        return item in (member.value for member in cls)
    
class UserIdentifiers(Enum):
    """
    Based on the field in the Userbase
    """
    uuid = "uuid"
    email = "email"
    username = "username"
    password = "password"
    balance = "balance"

    @classmethod
    def __contains__(cls, item):
        return item in (member.value for member in cls)