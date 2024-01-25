from enum import Enum
import flet as ft
import os
import sys

path1 = sys.path
print("\n".join(path1), end="\n\n\n")
def get_directory_of_project():
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
papertrading_dir = get_directory_of_project()
sys.path.append(papertrading_dir)
path2 = sys.path
print("\n".join(path2))

"""
class Constants(Enum):
    name_of_program = "O.G Papertrading"
    default_theme = ft.ThemeMode.LIGHT
    default_height = 1080
    default_width = 1920
    dir_path = os.path.dirname(os.path.realpath(__file__))

    content_width = default_width
    welcome_image_path = str(dir_path).replace("\gui", "") + r"\images\welcome_page\cool.jpg"


class ImageSizes(Enum):
    welcome = (1920, 850)
"""