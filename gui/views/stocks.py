from typing import Union, List
import datetime

import matplotlib
import flet as ft
from flet.matplotlib_chart import MatplotlibChart

from gui.router import Router
import gui.utils.gui_protocol as gp
import stocks.stock_script as stock_script


matplotlib.use("svg")

class Stocks:
    def __init__(self, router: Router):
        self._router: Router = router
        self.page: Union[ft.Page, None] = None
        
        # Fields for sign up - email, username, password
        self.chart: Union[MatplotlibChart, None]= None
        self.create_graph_button: ft.ElevatedButton = self.init_create_graph_button()
        
        self.date_picker_button: ft.ElevatedButton = self.init_date_picker_button()
        self.date_picker: ft.DatePicker = self.init_date_picker()
        self.picked_dates: Union[List[datetime.datetime], List[None]] = []

        self.time_picker_button: ft.ElevatedButton = self.init_time_picker_button()
        self.time_picker: ft.TimePicker = self.init_time_picker()
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

    def init_create_graph_button(self) -> ft.ElevatedButton:
        create_graph_button = ft.ElevatedButton(
            text="Submit", 
            on_click=self.create_graph_button_clicked
        )
        return create_graph_button
    
    def init_chart(self, ticker: str = None, start: datetime.datetime = None, end: datetime.datetime = None, interval: str = None):
        self.chart = self.get_chart_from_stockpuller(ticker=ticker, start=start, end=end, interval=interval)
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

    def change_time(self, e) -> None:
        print(f"Time picker changed, value is {self.time_picker.value}")
        self.apply_picked_time()
    
    def time_picker_dismissed(self, e) -> None:
        print(f"Time picker dismissed, value is {self.time_picker.value}")
        self.apply_picked_time()
        
    def apply_picked_time(self) -> None:
        match(len(self.picked_times)):
            case 2:
                print("Already picked two times, applying new start time")
                self.picked_times = []
            case 1:
                print("Applying end time")
            case 0:
                print("Applying start time")
        self.picked_times.append(self.time_picker.value)

    def change_date(self, e) -> None:
        print(f"Date picker changed, value is {self.date_picker.value}")
        self.apply_picked_date()

    def date_picker_dismissed(self, e) -> None:
        print(f"Date picker dismissed, value is {self.date_picker.value}")
        self.apply_picked_date()

    def apply_picked_date(self) -> None:
        match(len(self.picked_dates)):
            case 2:
                print("Already picked two dates, applying new start date")
                self.picked_dates = []
            case 1:
                print("Applying end date")
            case 0:
                print("Applying start date")
        self.picked_dates.append(self.date_picker.value)

    def create_graph_button_clicked(self, e) -> None:
        print("Button clicked, initiating chart")
        if len(self.picked_dates) == 2:
            self.init_chart(start=self.picked_dates[0], end=self.picked_dates[1])
        else:
            self.init_chart()
        
    def get_chart_from_stockpuller(self, ticker: str = None, start: datetime.datetime = None, end: datetime.datetime = None, interval: str = None) -> MatplotlibChart:
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
