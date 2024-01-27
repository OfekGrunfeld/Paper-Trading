from typing import Callable, Any
import flet as ft
from enum import Enum

class DataStrategy(Enum):
    QUERY = 0
    ROUTER_DATA = 1
    CLIENT_STORAGE = 2
    STATE = 3

class Router:
    def __init__(self, data_strategy=DataStrategy.QUERY):
        self.data_strategy: DataStrategy = data_strategy
        self.data: dict = {}
        self.routes = {}
        self.body = ft.Container()

    """
    def set_route(self, stub: str, view: Callable):
        self.routes[stub] = view
    
    def set_routes(self, route_dictionary: dict):
        
        #Sets multiple routes at once. Ex: {"/": IndexView }
        
        self.routes.update(route_dictionary)
    """

    def route_change(self, route):
        """
        Don't touch - flet stuff 
        """
        _page = route.route.split("?")[0]
        queries = route.route.split("?")[1:]

        for item in queries:
            key = item.split("=")[0]
            value = item.split("=")[1]
            self.data[key] = value.replace('+', ' ')

        self.body.content = self.routes[_page](self)
        self.body.update()

    """
    No clue what this was for
    
    #def set_data(self, key, value):
    #    self.data[key] = value

    #def get_data(self, key):
    #    return self.data.get(key)

    #def get_query(self, key):
    #    return self.data.get(key)
    """

