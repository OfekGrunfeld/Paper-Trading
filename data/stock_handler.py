from typing import Union

from sqlalchemy import create_engine, MetaData, Engine, and_
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker

from data.database import db_metadata_transactions, db_engine_transactions, db_metadata_portfolios, db_engine_portfolios

from utils.logger_script import logger

from sqlalchemy import create_engine, MetaData, select, and_
from sqlalchemy.orm import sessionmaker

def query_same_column_across_tables(columns: list[str], filters: list[tuple], metadata: MetaData, engine: Engine):
    session = sessionmaker(bind=engine)()
    try:
        results = []
        metadata.reflect(bind=engine)
        for table_name in metadata.tables:
            table = metadata.tables[table_name]
            if all(col in table.columns for col in columns):
                select_columns = [table.c[col] for col in columns]
                query = select(*select_columns)
                
                if filters and all(col in table.columns for col, _, _ in filters):
                    conditions = [op(table.c[col], val) for col, op, val in filters]
                    query = query.where(and_(*conditions))
                
                result = session.execute(query).fetchall()
                results.append((table_name, result))
        return results
    finally:
        session.close()

def run():
    from sqlalchemy.sql import operators
    # Example of using different operators with new filters parameter
    results = query_same_column_across_tables(
        columns=['symbol', 'total_cost'],
        filters=[
            ('symbol', operators.eq, 'AAPL'),
            ('total_cost', operators.gt, 1900)
        ],
        metadata=db_metadata_transactions,
        engine=db_engine_transactions
    )

    print("Database Results:")
    for table_name, data in results:
        print(f"Data from {table_name}:")
        for row in data:
            print(row)
