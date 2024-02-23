from copy import deepcopy
from enum import Enum
from typing import Union, override, List, Literal
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import use as matplotlib_use

from utils.server_protocol import logger


matplotlib_use("svg")

class Constants(Enum):
    default_start_time = datetime.now() - timedelta(days=10, hours=1)
    default_end_time = datetime.now()

class StockPuller:
    @staticmethod
    def get_stock(ticker: str = None, start: datetime = None, end: datetime = None, interval: str = None) -> Union[pd.DataFrame, None]:
        """
        Get a dataframe of a stock - pull data from yfinance

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
            logger.warning(f"No ticker specified defaulting to {ticker}")
        if start is None:
            start = Constants.default_start_time.value
            logger.warning(f"No start date specified defaulting to {start}")
        if end is None:
            end = Constants.default_end_time.value
            logger.warning(f"No end date specified defaulting to {end}")
        if interval is None:
            interval = "30m"
            logger.warning(f"No interval specified defaulting to {interval}")

        try:
            data = yf.download(tickers=[ticker],start=start,end=end,interval=interval)
            logger.info(f"Downloaded {ticker} data successfully")
        except Exception as error:
            logger.exception(f"Error getting stocks, error: \n{error}")
        finally:
            return data
    
    @staticmethod
    def get_stock_plt_figure(df: pd.DataFrame, plot_type: str = "Adj Close") -> plt.Figure:
        """
        Generate a plt figure from a pandas dataframe, based on a plot type which is one of OHLCVT

        CURRENTLY SUPPORTING ONLY Adj Close

        :param df: Pandas dataframe of a stock
        :param plot_type: Plot type - one of OHLCVT
        :returns: Plt figure (sv)
        """
        try:
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
            
        except Exception as error:
            logger.exception(f"Exception in getting plt stock figure: {error}")
            fig = plt.figure()
            return None
        return fig