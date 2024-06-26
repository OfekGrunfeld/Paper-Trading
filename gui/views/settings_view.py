from typing import Union

import flet as ft

import gui.utils.gui_protocol as gp
from gui.router import Router


class SettingsView:
    def __init__(self, router: Router):
        self._router: Router = router
        self.page: Union[ft.Page, None] = None

        self._content: ft.Column = self.init_content()

    def init_content(self) -> ft.Column:
        content: ft.Column = ft.Column(
            [
                ft.Row(
                [
                    ft.Text("My Settings", size=30), 
                    ft.IconButton(icon=ft.icons.SETTINGS_ROUNDED, icon_size=30),

                ], 
                alignment=ft.MainAxisAlignment.CENTER
            ),
                ft.Row(
                    [
                        ft.Switch(
                            label="Toggle Theme", 
                            on_change=gp.app.toggle_theme_switch, 
                        ),
                    ],
                ),
                ft.Row(
                    [
                        ft.TextButton(
                            text="Exit Application", 
                            icon=ft.icons.CLOSE, 
                            on_click=gp.app.exit_app, 
                            icon_color=ft.colors.RED
                        )
                    ]
                ),
            ]
        )
        return content

    def __call__(self, router: Router) -> ft.Column:
        self.page: Union[ft.Page, None] = gp.app.page
        return self._content