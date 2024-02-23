from typing import Union

import flet as ft

from gui.routes import router
from gui.user_controls.app_bar import init_navigation_bar
import gui.utils.gui_protocol as gp


class App:
    def __init__(self):
        self.page: Union[ft.Page, None] = None
        self.title: str = "O.G Papertrading"
        self.theme_mode = ft.ThemeMode.LIGHT

    def set_window_size(self) -> None:
        self.page.window_height = gp.Constants.default_height.value
        self.page.window_width = gp.Constants.default_width.value
        self.page.window_resizable = True

    def main(self, page = ft.Page):
        self.page = page
        gp.app.page = page
        
        self.page.title = self.title
        self.page.theme_mode = self.theme_mode
        self.page.scroll = ft.ScrollMode.ALWAYS
        self.set_window_size()

        # Adding page elements
        self.page.appbar = init_navigation_bar(self.page)

        # Routing Settings
        self.page.on_route_change = router.route_change

        page.add(
            router.body
        )
        page.go('/')

    

def main():
    flet_app = App()
    ft.app(
        target=flet_app.main, 
        assets_dir="assets"
    )

if __name__ == "__main__":
    main()