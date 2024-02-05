from typing import Union
import flet as ft
from Router import Router
import gui_protocol as gp
import requests

class SignUpView:
    def __init__(self, router: Router):
        self._router: Router = router
        self.page: Union[ft.Page, None] = None
        
        
        # Fields for sign up - email, username, password
        self.fields: list[ft.TextField] = self.init_sign_up_fields()
        self.submit_button = ft.ElevatedButton(text="Submit", on_click=self.submit_button_clicked)
        self.response_text = ft.Container()
        # Column for all fields
        self._content: ft.Column = self.init_content()


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
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        self.submit_button,
                    ]
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        self.response_text,
                    ]
                )
            ]
        )
        return content
    def submit_button_clicked(self, e):
        email, username, password = [field.value for field in self.fields]
        params = {"email": email, "username": username, "password": password}
        try:
            response = requests.post(url=f"{gp.Constants.server_url.value}/sign_up", params=params)
        except Exception as error:
            self.response_text.content = ft.Text(value="Server is currently down. Try to sign up later")
            self.page.update()
            return
        print(f"response: {response.status_code}, {response.json()}")
        if response.status_code == 200 and response.json()["sign_up_success"] == True:
            self.response_text.content = ft.Text(value="Signed Up Successfully!")
            self.page.update()
        else:
            self.response_text.content = ft.Text(value=f"Error signing up: {response.json()["error"]}")
        self.page.update()
    
    def __call__(self, router: Router) -> ft.Column:
        self.page: Union[ft.Page, None] = gp.app.page
        return self._content
