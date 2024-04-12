@papertrading_app.get("/stock_data")
def get_stock_data(ticker: str = None, start: datetime.datetime = None, end: datetime.datetime = None, interval: str = None) -> List[dict]:
    try:
        # get stock data
        logger.info(f"Got stock data request for {ticker}, Start: {start}, End: {end}, interval: {interval}")
        stock_data: DataFrame | None = StockPuller.get_stock(ticker=ticker, start=start, end=end, interval=interval)
        logger.debug(f"Stock data request for {ticker} complete:\n{stock_data}")

        # output to json
        stock_data_json = stock_data.to_dict(orient="records")
        return stock_data_json
    except Exception as error:
        logger.error(f"Error getting for {ticker}, Start: {start}, End: {end}, interval: {interval}")
        return {"error": True}

@papertrading_app.post("/check")
def send_stock_update(data: dict):
    try:
        logger.debug(f"got data dict {data}")
        dataframe = pd.read_json(data)
        logger.debug(f"outputted to dataframe\n{dataframe}")
        return "good"
    except Exception as error:
        print(error)
        return "bad"