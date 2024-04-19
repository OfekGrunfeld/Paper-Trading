from typing import Union
import numpy as np
import copy 
from sqlalchemy import update
from sqlalchemy.orm.session import Session

from data.database import DatabasesNames, get_db
from data.database_models import UserIdentifiers, Userbase
from data.records import StockRecord, Statuses
from data.database_helper import (add_stock_data_to_selected_database_table, get_table_object_from_selected_database_by_name, 
                                  remove_row_by_uid)
from data.query_helper import get_user_from_userbase, get_user_shares_by_symbol
from utils.logger_script import logger
from utils.yfinance_helper import get_symbol_info

class StockHandler:
    CHECK_TIME = 15 # seconds
    pending = []

    @staticmethod
    def deal_with_transaction(stock_record: StockRecord, uuid: str):
        """
        Check whether the given stock record is valid and then add to transactions list
        """
        saved_user: Union[Userbase, None] = get_user_from_userbase(identifier=UserIdentifiers.uuid.value, value=uuid)

        if saved_user is None:
            logger.error(f"Could not retrieve user from userbase")

        
        user_balance = saved_user.balance

        if stock_record.side == "buy":
            if user_balance >= stock_record.total_cost:
                # Remove cost of shares from user's balance
                user_balance -= stock_record.total_cost
                # Update transaction to be tracked
                stock_record.status = Statuses.tracked.value
                # Output stock record to dict
                try:
                    stock_record_dict = stock_record.to_dict()
                except Exception as error:
                    logger.error(f"Could not output stock record into a dictionary. Error: {error}")
                    return 
                success_transactions = add_stock_data_to_selected_database_table(
                    database_name=DatabasesNames.transactions.value,
                    table_name=uuid,
                    stock_data=stock_record_dict
                )
                success_portfolio = add_stock_data_to_selected_database_table(
                    database_name=DatabasesNames.portfolios.value,
                    table_name=uuid,
                    stock_data=stock_record_dict
                )

                if success_transactions and success_portfolio:
                    logger.debug(f"Successfully added transaction to transaction history and active portfolio of user {uuid}")
                else:
                    logger.error(f"Transaction from user {uuid} was not succcessful")
            else:
                logger.warning(f"User {uuid} doesn't have enough money to buy {stock_record.shares} shares of {stock_record.symbol}.")
                return
        elif stock_record.side == "sell":      
            # Get the portfolio's table object for querying
            table_object = get_table_object_from_selected_database_by_name(table_name=uuid, database_name=DatabasesNames.transactions.value)

            if table_object is None:
                logger.error(f"Could not retrieve portfolio table object")
                return

            if stock_record.shares <= 0:
                logger.warning(f"Transaction from user {uuid} attempted to sell 0 or fewer shares")
                return
            
            # Sell the shares of the symbol form the portfolio
            revenue, unsold_shares = StockHandler.sell_shares(uuid=uuid, symbol=stock_record.symbol, shares=stock_record.shares)

            # Add to user balance
            user_balance += revenue
 
            stock_record.shares -= unsold_shares
            stock_record.status = Statuses.archived.value

            try:
                stock_record_dict = stock_record.to_dict()
            except Exception as error:
                logger.error(f"Could not output stock record into a dictionary. Error: {error}")
            
            flag = add_stock_data_to_selected_database_table(
                database_name=DatabasesNames.transactions.value,
                table_name=uuid,
                stock_data=stock_record_dict
            )
            if flag:
                logger.info(f"Successully sold {stock_record.shares} shares for a revenue of {revenue}")
            else:
                logger.info(f"Failed to update transactions database with the sell transaction data")

        # Update user balance 
        saved_user.balance = user_balance
            
    
    @staticmethod
    def sell_shares(uuid: str, symbol: str, shares: float) -> float:
        """
        Sells shares from the user's portfolio by finding the shares with prices closest to the current market price.
        It reduces those shares from the transaction in the portfolio and calculates revenue based on the current market price.

        Args:
            uuid (str): The UUID of the user selling the shares.
            symbol (str): The symbol of the stock to sell.
            shares_to_sell (float): The amount of shares to sell.

        Returns:
            np.double: The revenue generated from selling the shares.
        """
        shares_to_sell = copy.copy(shares)
        if shares_to_sell <= 0:
            logger.warning("Attempted to sell zero or fewer shares.")
            return (0, shares)

        # Fetch the current market price for the symbol
        symbol_info = get_symbol_info(symbol)
        if not symbol_info or 'currentPrice' not in symbol_info:
            logger.error("Failed to fetch current market price.")
            return (0, shares)

        current_price = symbol_info['currentPrice']

        portfolio_session: Session = next(get_db(DatabasesNames.portfolios.value))
        transaction_session: Session = next(get_db(DatabasesNames.transactions.value))

        try:
            shares_list = get_user_shares_by_symbol(DatabasesNames.portfolios.value, uuid, symbol)
            total_shares = sum(shares for _, shares, _ in shares_list)

            if total_shares < shares_to_sell:
                logger.error("Not enough shares to sell.")
                return (0, shares)

            revenue = 0

            # Sort transactions by lowest price when bought
            shares_list.sort(key=lambda x: abs(x[2]))

            table_object_portfolios = get_table_object_from_selected_database_by_name(table_name=uuid, database_name=DatabasesNames.portfolios.value)
            table_object_transactions = get_table_object_from_selected_database_by_name(table_name=uuid, database_name=DatabasesNames.transactions.value)

            rows_uids_to_remove = []
            for uid, shares, _ in shares_list:
                if shares_to_sell <= 0:
                    logger.debug(f"Done selling all shares")
                    break

                shares_to_reduce = min(shares, shares_to_sell)
                revenue += shares_to_reduce * current_price
                shares_to_sell -= shares_to_reduce

                # Update the shares count in the database
                new_share_count = shares - shares_to_reduce
                if new_share_count > 0:
                    update_stmt = update(table_object_portfolios).where(table_object_portfolios.c.uid == uid).values(shares=new_share_count)
                    portfolio_session.execute(update_stmt)
                    logger.info(f"Reduced {shares_to_reduce} shares from UID {uid} in transaction.")
                else:
                    # Archive the transaction if no shares remain
                    archive_stmt = update(table_object_transactions).where(table_object_transactions.c.uid == uid).values(status=Statuses.archived.value)
                    transaction_session.execute(archive_stmt)
                    logger.info(f"Transaction UID {uid} archived as all shares are sold. {shares}")

                    rows_uids_to_remove.append(uid)

            portfolio_session.commit()
            transaction_session.commit()
            
            for row_uid in rows_uids_to_remove:
                remove_row_by_uid(DatabasesNames.portfolios.value, uuid, row_uid)

            if shares_to_sell > 0:
                logger.warning(f"Not all shares could be sold; {shares_to_sell} shares remain unsold.")

            return revenue, shares_to_sell
        except Exception as error:
            import traceback
            portfolio_session.rollback()
            transaction_session.rollback()
            logger.error(f"Error while trying to sell shares for user {uuid}: {error}")
            logger.error(traceback.format_exc())
            return (0,shares)
        finally:
            portfolio_session.close()
            transaction_session.close()



            

            

                




# def change_pending(scheduler: sched.scheduler):
#     pass

# def run_query_loop():
#     my_scheduler = sched.scheduler(time.monotonic, time.sleep)
#     my_scheduler.enter(StockHandler.CHECK_TIME, 1, query_pending_stock_records, (my_scheduler,))
#     # my_scheduler.enter(StockHandler.CHECK_TIME, 2, printer, (my_scheduler,))
#     my_scheduler.run()


