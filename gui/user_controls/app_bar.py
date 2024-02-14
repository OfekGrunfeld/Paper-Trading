import flet as ft

import gui.gui_protocol as gp

def init_navigation_bar(page):
    navigation_bar = ft.AppBar(
            leading=ft.Icon(ft.icons.PALETTE),
            leading_width=40,
            title=ft.Text(gp.Constants.name_of_program.value),
            center_title=False,
            bgcolor=ft.colors.SURFACE_VARIANT,
            actions=[
                ft.IconButton(ft.icons.PERSON_ROUNDED, on_click=lambda _: page.go('/sign_up')),
                ft.IconButton(ft.icons.SETTINGS_ROUNDED, on_click=lambda _: page.go('/settings')),
                ft.IconButton(ft.icons.FILTER_3),
                ft.IconButton(ft.icons.GARAGE_ROUNDED, on_click=lambda _: page.go('/stocks')),
            ],
        )
    return navigation_bar
