# class StockHandler:
#     CHECK_TIME = 15 # seconds
#     pending = []

# def change_pending(scheduler: sched.scheduler):
#     pass

# def run_query_loop():
#     my_scheduler = sched.scheduler(time.monotonic, time.sleep)
#     my_scheduler.enter(StockHandler.CHECK_TIME, 1, query_pending_stock_records, (my_scheduler,))
#     # my_scheduler.enter(StockHandler.CHECK_TIME, 2, printer, (my_scheduler,))
#     my_scheduler.run()


