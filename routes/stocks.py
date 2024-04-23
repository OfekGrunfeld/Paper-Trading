import traceback

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
import yfinance as yf
import numpy as np

from records.server_response import ServerResponse
from utils.logger_script import logger
from data.database_models import Userbase
from data.database import get_db_userbase
from records.stock_record import StockRecord
from stocks.stock_handler import StockHandler
from encryption.decrypt import decrypt


stocks_router = APIRouter()

@stocks_router.post("/submit_order")
def submit_order(uuid: str, order: str, db: Session = Depends(get_db_userbase)):
    try:
        uuid, order = decrypt(uuid), decrypt(order)
        return_dict = ServerResponse()

        try:
            info = yf.Ticker(order["symbol"]).info
        except Exception as error:
            logger.error(f"Failed to get info of stock from yfinance: {error}")


        match(order["order_type"]):
            case "market":
                return_dict.success = True
                if order["side"] == "sell":
                    cost_per_share =  np.double(info["bid"])
                else:
                    cost_per_share = np.double(info["ask"])
                try:
                    sr = StockRecord(
                        symbol=order["symbol"],
                        side=order["side"],
                        order_type=order["order_type"],
                        shares=order["shares"],
                        cost_per_share=cost_per_share,
                        notes=None
                    )
                except Exception as error:
                    logger.error(f"Error creating stock record: {error}")
                # for debugging currently
                StockHandler.deal_with_transaction(sr, uuid)
            
            case _:
                return_dict.error = f"Invalid or unsupported order type"
            
        return return_dict
    except Exception as error:
        logger.error(f"Error submitting order. Error: {traceback.format_exc()}")
        return None

