import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from server_protocol import logger
from enum import Enum
import server_protocol as sp
from typing import Union, override, List, Literal
from datetime import datetime, timedelta
import matplotlib
from copy import deepcopy

matplotlib.use("svg")

class Constants(Enum):
    tickers = [line.strip() for line in open(sp.Constants.stock_tickers_location.value, "r")]
    default_start_time = datetime.now() - timedelta(days=10, hours=1)
    default_end_time = datetime.now()

class Stock:
    def __init__(self, stock_ticker: str, start: datetime, end: datetime, interval: str) -> None:
        self.stock_ticker: str = stock_ticker
        self.stock_name: str = Stock.translate_stock_ticker_to_name(stock_ticker)
        self.start = start
        self.end = end
        self.interval = interval

    def generate_stock(self) -> pd.DataFrame:
        """
        Add stock dataframe (data) to the class based on the start, end and interval
        """
        self.stock = StockPuller.get_stock(self.stock_ticker, start=self.start, end=self.end, interval=self.interval)
        return self.stock

    @staticmethod
    def translate_stock_ticker_to_name(stock_ticker: str) -> str:
        pass
   
class StockPuller:
    @staticmethod
    def get_stock(ticker: str = None, start: datetime = None, end: datetime = None, interval: str = None) -> Union[pd.DataFrame, None]:
        """
        Get a dataframe of multiple stocks
        :patam tickers: Stock ticker. E.g: AMZN, AAPL
        :param start: Datetime of start
        :param end: Datetime of end
        :param interval: Interval (yFinance Interval) for dataframe. E.g: 1d, 1m, 1s
        :return: Dataframe of multiple stocks
        """
        data = None
        # if there was no param specified, set default
        if ticker is None:
            ticker = "AAPL"
            print(f"No ticker specified defaulting to {ticker}")
        if start is None:
            start = Constants.default_start_time.value
            print(f"No start date specified defaulting to {start}")
        if end is None:
            end = Constants.default_end_time.value
            print(f"No end date specified defaulting to {end}")
        if interval is None:
            interval = "30m"
            print(f"No end date specified defaulting to {interval}")

        try:
            data = yf.download(tickers=[ticker],start=start,end=end,interval=interval)
        except Exception as error:
            logger.exception(f"Error getting stocks, error: \n{error}")
        finally:
            return data
    
    @staticmethod
    def get_stock_plt_figure(df: pd.DataFrame, plot_type: str = "Adj Close") -> plt.Figure:
        # Create a new figure and axis object
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Plot the data on the axis
        ((df[plot_type].pct_change()+1).cumprod()).plot(ax=ax)
        ax.legend()
        ax.set_title(plot_type, fontsize=16)

        # Define the labels
        ax.set_ylabel(f"{plot_type} value", fontsize=14)
        ax.set_xlabel('Time', fontsize=14)

        # Plot the grid lines
        ax.grid(which="major", color='k', linestyle='-.', linewidth=0.5)
        
        return fig

def main():
    stocks = StockPuller.get_stock(ticker="AMZN", interval="30m")
    print(stocks)
    fig = StockPuller.get_stock_plt_figure(df=stocks)


if __name__ == "__main__":
    main()