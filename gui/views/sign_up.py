from typing import Union
import flet as ft
from Router import Router
import gui_protocol as gp

class SignUpView:
    def __init__(self, router: Router):
        self.page: Union[ft.Page, None] = None
        self._router: Router = router


        # Fields for sign up - email, username, password
        self.fields: list[ft.TextField] = self.init_sign_up_fields()

        # Column for all fields
        self._content: ft.Column = self.init_content()

        submit_button = ft.ElevatedButton(text="Submit", on_click=self.submit_button_clicked)
    
    def init_sign_up_fields(self) -> list[ft.TextField]:
        email_field = ft.TextField(label="Email", max_lines=1, width=280, hint_text="Enter email here")
        username_field = ft.TextField(label="Username", max_lines=1, width=280, hint_text="Enter username here")
        password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, max_lines=1, width=280, hint_text="Enter password here")
        return [email_field, username_field, password_field]

    def init_content(self) -> ft.Column:
        content = ft.Column(
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        ft.Column(
                            spacing=20, 
                            controls=self.fields
                        ),
                    ]
                )
            ]
        )
        return content
    def submit_button_clicked(self, e):
        email, username, password = self.items
        """
        if response == "Username invalid!":
            self.username_tb.border_color = ft.colors.RED_400
            self.username_tb.value = ''
            self.username_tb.label = response
            self.username_tb.hint_text = "Enter new username here"
            self.email_tb.border_color = ft.colors.SURFACE_VARIANT
            self.email_tb.label = "Email"
        if response == "Invalid email address!" or response == "Account with the same email exists!":
            self.email_tb.border_color = ft.colors.RED_400
            self.email_tb.value = ''
            self.email_tb.label = response
            self.email_tb.hint_text = "Enter new email here"
            self.username_tb.border_color = ft.colors.SURFACE_VARIANT
            self.username_tb.label = "Username"
        self.page.update()
        if response == "Signed up successfully!":
            pass
            # redirect to another page
        """
    
    
    def __call__(self, router: Router) -> ft.Column:
        return self._content
"""
def send_data(e: ft.ControlEvent):
    if text_field.value == "":
        return
    if router_data and router_data.data_strategy == DataStrategy.QUERY:
        e.page.go("/data", data=text_field.value)
    elif router_data and router_data.data_strategy == DataStrategy.ROUTER_DATA: 
        router_data.set_data("data", text_field.value)
        e.page.go("/data", data=text_field.value)
    elif router_data and router_data.data_strategy == DataStrategy.CLIENT_STORAGE:
        e.page.client_storage.set("data", text_field.value)
        e.page.go("/data")
    elif router_data and router_data.data_strategy == DataStrategy.STATE:
        state = State("data", text_field.value)
        e.page.go("/data")
    else:
        e.page.go("/data")
    """

