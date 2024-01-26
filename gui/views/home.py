from typing import Union
import flet as ft
from Router import Router
import gui_protocol as gp

Lorem_ipsum = \
"""
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eu hendrerit neque. Donec pellentesque ante sit amet nulla rhoncus, lacinia aliquet nulla congue. Praesent maximus gravida arcu sit amet cursus. Quisque pretium magna nibh, at ultricies lacus placerat vulputate. Ut varius lacus sed lacinia tincidunt. Maecenas hendrerit metus quis tincidunt placerat. Proin imperdiet lorem at libero pretium, in congue erat venenatis. Praesent eget lacus eget felis laoreet imperdiet at et ex. Nam tristique justo at dolor faucibus, eu consectetur mi malesuada. Nunc consequat feugiat erat, ac bibendum erat euismod vitae. Pellentesque rhoncus ligula quis congue ultrices. Proin semper nulla felis, vitae commodo nulla feugiat nec. Donec eu pharetra purus. Interdum et malesuada fames ac ante ipsum primis in faucibus. Integer quis sapien massa. Nunc vel dolor justo.

Nullam eget sagittis urna, nec rutrum massa. Phasellus rutrum est eu tellus vehicula elementum. Morbi id tellus vestibulum, facilisis sem eget, tempus neque. In nunc enim, tempor et lacinia ut, blandit quis velit. Fusce ultrices dui id risus accumsan, nec fermentum nibh dapibus. Morbi dignissim id dolor sed consequat. Vivamus rutrum odio eleifend, pulvinar nisl ac, varius metus. Donec malesuada enim orci, lobortis pellentesque quam volutpat nec.

In commodo massa purus, a imperdiet massa vestibulum quis. Donec hendrerit vehicula nunc eget rhoncus. Aliquam eleifend orci sed elit auctor, nec tincidunt mauris vestibulum. Integer viverra mauris ac lacus faucibus aliquet. Curabitur non nulla rhoncus, aliquet ante id, convallis turpis. Ut molestie dictum tellus, a tincidunt ex imperdiet auctor. Maecenas semper magna sed nibh molestie venenatis. Praesent consectetur, ligula convallis commodo volutpat, leo magna bibendum nibh, quis tristique arcu risus eu urna. Pellentesque a ornare ipsum, non faucibus massa. Phasellus vestibulum viverra dolor, eu porttitor dolor lobortis at.

Fusce aliquam finibus eros, vitae consectetur quam luctus sed. Phasellus eget eros a est facilisis pharetra non id enim. Nulla aliquam eget velit a finibus. Duis ac nisl in neque pharetra tincidunt. Quisque semper velit urna, id egestas ipsum ornare sed. Duis sodales venenatis magna, id scelerisque leo hendrerit in. Aenean lectus mauris, convallis ut nisl id, aliquet elementum erat. Vestibulum ut molestie urna, sit amet tempor elit. Maecenas non facilisis libero. Aenean vestibulum et dui quis tincidunt. Aliquam vitae massa augue. Pellentesque gravida, nulla ut porta vehicula, massa mi varius diam, finibus vestibulum dolor felis eget risus.

"""
class HomeView:
    def __init__(self, router: Router):
        self.page: Union[ft.Page, None] = None
        self._router = router

        # Welcome image of homepage
        self.welcome_container = self.init_welcome_container()
        self.arrow_down = self.init_arrow_down()
        self.main_column = None

        # Content (Combines everything)
        self._content = self.init_content()
        submit_button = ft.ElevatedButton(text="Submit", on_click=self.submit_button_clicked)
    
    def init_welcome_container(self):
        welcome_container = ft.Container(
            content=ft.Text("Welcome", scale=10, color=ft.colors.GREY),
            padding = ft.padding.symmetric(horizontal=10), 
            margin = ft.margin.only(top=10, bottom=10), 
            alignment=ft.alignment.center,
            width=gp.ImageSizes.welcome.value[0],
            height=gp.ImageSizes.welcome.value[1],
            ink=True,
            on_click=lambda e: print("Welcome clicked"),
            #on_hover=self.on_hover_welcome_container,
            image_src=gp.Constants.welcome_image_path.value,
            image_fit=ft.ImageFit.FIT_WIDTH,
        )
        return welcome_container

    def init_arrow_down(self):
        arrow_down = ft.Container(
            alignment=ft.alignment.center,
            content= ft.IconButton(
                icon=ft.icons.KEYBOARD_DOUBLE_ARROW_DOWN_ROUNDED,
                icon_color=ft.colors.BLUE_400,
                icon_size=50,
                on_click = lambda _: self.main_column.scroll_to(key="A", duration=1000)
            ),
        )
        return arrow_down
    
    def init_sign_up_boxes(self):
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
                        self.welcome_container,
                        self.arrow_down,
                        ft.Container(
                            content=ft.Text(
                                value=Lorem_ipsum, 
                                overflow=ft.TextOverflow.NONE,
                                key="A"
                            )
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

