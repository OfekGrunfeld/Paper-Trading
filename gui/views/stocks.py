from typing import Union, List
import flet as ft
from flet.matplotlib_chart import MatplotlibChart
from gui.router import Router
import gui.gui_protocol as gp
import matplotlib
import stock_script
import datetime
from time import sleep

matplotlib.use("svg")

class Stocks:
    def __init__(self, router: Router):
        self._router: Router = router
        self.page: Union[ft.Page, None] = None
        
        # Fields for sign up - email, username, password
        self.chart: Union[MatplotlibChart, None]= None
        self.create_graph_button = self.init_create_graph_button()
        
        self.date_picker_button = self.init_date_picker_button()
        self.date_picker = self.init_date_picker()
        self.picked_dates: Union[List[datetime.datetime], List[None]] = []

        self.time_picker_button = self.init_time_picker_button()
        self.time_picker = self.init_time_picker()
        self.picked_times: Union[List[datetime.time], List[None]] = []

        self.list_of_overlay_items = [self.date_picker, self.time_picker]

        # Column for all fields
        self._content: ft.Column = self.init_content()

    def init_date_picker_button(self) -> ft.ElevatedButton:
        date_picker_button = ft.ElevatedButton(
            "Pick date",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker.pick_date(),
        )
        return date_picker_button

    def init_date_picker(self) -> ft.DatePicker:
        date_picker = ft.DatePicker(
            on_change=self.change_date,
            on_dismiss=self.date_picker_dismissed,
            first_date=datetime.datetime.now() - datetime.timedelta(days=2 * 365),
            last_date=datetime.datetime.now(),
        )
        return date_picker
    
    def init_time_picker_button(self) -> ft.ElevatedButton:
        time_picker_button = ft.ElevatedButton(
            "Pick time",
            icon=ft.icons.TIME_TO_LEAVE,
            on_click=lambda _: self.time_picker.pick_time(),
        )
        return time_picker_button
    
    def init_time_picker(self) -> ft.TimePicker:
        time_picker = ft.TimePicker(
            confirm_text="Confirm",
            error_invalid_text="Time out of range",
            help_text="Pick your time slot",
            on_change=self.change_time,
            on_dismiss=self.time_picker_dismissed,
        )
        return time_picker

    def change_time(self, e):
        print(f"Time picker changed, value is {self.time_picker.value}")
        if len(self.picked_times) == 2:
            self.picked_times = []
        self.picked_times.append(self.time_picker.value)
        print(self.picked_times)
    
    def change_date(self, e):
        print(f"Date picker changed, value is {self.date_picker.value}")
        if len(self.picked_dates) == 2:
            self.picked_dates = []
        self.picked_dates.append(self.date_picker.value)
        if len(self.picked_dates) == 2:
            self.create_chart(start=self.picked_dates[0], end=self.picked_dates[1])
        print(self.picked_dates)

    def time_picker_dismissed(self, e):
        print(f"Time picker dismissed, value is {self.time_picker.value}")
        if len(self.picked_times) == 2:
            self.picked_times = []
        self.picked_times.append(self.time_picker.value)
        print(self.picked_times)
    
    def date_picker_dismissed(self, e):
        print(f"Date picker dismissed, value is {self.date_picker.value}")
        if len(self.picked_dates) == 2:
            self.picked_dates = []
        self.picked_dates.append(self.date_picker.value)
        if len(self.picked_dates) == 2:
            self.create_chart(start=self.picked_dates[0], end=self.picked_dates[1])
        print(self.picked_dates)

    def init_create_graph_button(self):
        create_graph_button = ft.ElevatedButton(
            text="Submit", 
            on_click=self.create_graph_button_clicked
        )
        return create_graph_button
    
    def create_graph_button_clicked(self, e):
        print("Button clicked, initiating chart")
        self.create_chart()
        
    
    def create_chart(self, ticker: str = None, start: datetime.datetime = None, end: datetime.datetime = None, interval: str = None):
        self.chart = self.init_chart(ticker=ticker, start=start, end=end, interval=interval)
        self._content.controls.append(
            ft.Row(
                width=gp.Constants.default_width.value / 2,
                height=gp.Constants.default_height.value / 2,
                spacing=10,
                run_spacing=10,
                controls = [
                    self.chart,
                ]
            )
        )
        self.page.update()
        
    def init_chart(self, ticker: str = None, start: datetime.datetime = None, end: datetime.datetime = None, interval: str = None) -> MatplotlibChart:
        my_stock = stock_script.StockPuller.get_stock(ticker=ticker, start=start, end=end, interval=interval)
        print(my_stock)
        fig = stock_script.StockPuller.get_stock_plt_figure(df=my_stock)
        flet_chart = MatplotlibChart(fig, expand=True)
        return flet_chart

    def init_content(self) -> ft.Column:
        content = ft.Column(
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        self.create_graph_button,
                        self.date_picker_button,
                        self.time_picker_button,
                    ]
                ),
            ]
        )
        return content

    def __call__(self, router: Router) -> ft.Column:
        self.page: Union[ft.Page, None] = gp.app.page
        # add time and date pickers in the page
        self.page.overlay.extend(self.list_of_overlay_items)

        return self._content
