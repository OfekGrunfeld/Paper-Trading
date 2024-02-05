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
            ]
        )
        return content

    #herlaergluesrlguelurgleuiglergl
    def init_dialog(self):
        pass
    def submit_button_clicked(self, e):
        email, username, password = [field.value for field in self.fields]
        params = {"email": email, "username": username, "password": password}
        try:
            response = requests.post(url=f"{gp.Constants.server_url.value}/sign_up", params=params)
        except Exception as error:
            self._content.controls.append(
                ft.Container(
                    ft.Text(
                        value="Server is currently down. Try to sign up later"
                    ),
                )
            )
            print("what")
            return

        print(f"response: {response.status_code}, {response.json()}")
        if response.status_code == 200 and response.json()["sign_up_success"] == True:
            self._content.controls.append(
                ft.Container(
                    ft.Text(
                        value="Signed Up Successfully!"
                    ),
                )
            )
        else:
            self._content.controls.append(
                ft.Container(
                    ft.Text(
                        value="Error signing up"
                    ),
                )
            )
        self.page.update()
    
    
    def __call__(self, router: Router) -> ft.Column:
        self.page: Union[ft.Page, None] = gp.app.page
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
