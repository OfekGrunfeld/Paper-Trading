from enum import Enum
import flet as ft
import os
from typing import Union
import requests

class Constants(Enum):
    name_of_program = "O.G Papertrading"
    default_theme = ft.ThemeMode.LIGHT
    default_height = 1080
    default_width = 1920
    gui_root_path = os.path.dirname(os.path.realpath(__file__))
    content_width = default_width
    welcome_image_path = gui_root_path + r"\assets\welcome.jpg"
    server_url = "http://127.0.0.1:5555" # Needs to be dynamic!!!!

class ImageSizes(Enum):
    welcome = (1920, 850)


# Code I definitely didn't write
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class App(metaclass=Singleton):
    """
    App class is a singleton that is instantiated at main.py 
    and it's functions can be called from other scripts
    !!!!! BUT NOT WORKING AS INTENDED  !!!!!
    """
    def __init__(self):
        pass
    
    @property
    def page(self) -> ft.app:
        try:
            return self._page
        except AttributeError:
            return None
    
    @page.setter
    def page(self, page: ft.app):
        self._page = page
    
    """
    All features shall be moved to specific pages later
    """
    def toggle_theme_icon_button(self, e) -> None:
        if self._page.theme_mode == ft.ThemeMode.LIGHT:
            self._page.theme_mode = ft.ThemeMode.DARK
        else:
            self._page.theme_mode = ft.ThemeMode.LIGHT
        e.control.selected = not e.control.selected
        e.control.update()
        self._page.update()

    def toggle_theme_text_button(self, e) -> None:
        if self._page.theme_mode == ft.ThemeMode.DARK:
            self._page.theme_mode = ft.ThemeMode.LIGHT
        else: 
            self._page.theme_mode = ft.ThemeMode.DARK
        self._page.update()
    
    def toggle_theme_switch(self, e):
        if self._page.theme_mode == ft.ThemeMode.DARK:
            self._page.theme_mode = ft.ThemeMode.LIGHT
        else: 
            self._page.theme_mode = ft.ThemeMode.DARK
        self._page.update()

    def exit_app(self, e):
        self._page.window_destroy()
        
app: Union[App, None] = App()


# don't use
def get_directory_of_project():
    """
    Useless because in order to use this function you must first import this
    this file and therefore you don't need to see what the directory of file is
    """
    # Start with the current file's directory
    current_path = os.path.abspath(os.path.dirname(__file__))

    # Loop to move up in the directory hierarchy
    while os.path.basename(current_path).lower() != 'papertrading' and current_path != os.path.dirname(current_path):
        current_path = os.path.dirname(current_path)

    # Check if the 'papertrading' directory was found
    if os.path.basename(current_path).lower() == 'papertrading':
        return current_path
    else:
        raise Exception("Failed to find a directory ending with 'papertrading'")