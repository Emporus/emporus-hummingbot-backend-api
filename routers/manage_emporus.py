import math
import os
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter
from sqlalchemy import create_engine

router = APIRouter(tags=["Emporus Management"])


@router.get("/emporus-trades", response_model=Dict[str, Any])
async def emporus_trades(start_time: int = None, end_time: int = None):
    try:
        username = os.getenv("POSTGRES_USERNAME", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", 5432))
        database = os.getenv("POSTGRES_DATABASE", "hummingbot")
        db_connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"

        engine = create_engine(
            db_connection_string,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            connect_args={"connect_timeout": 10}
        )
        request_query = "SELECT * FROM \"EmporusTrades\" WHERE 1=1"
        query_params = []

        if start_time:
            request_query += " AND \"update_timestamp\" > %s"
            query_params.append(start_time)

        if end_time:
            request_query += " AND \"update_timestamp\" < %s"
            query_params.append(end_time)

        with engine.connect() as connection:
            trades_list = pd.read_sql_query(request_query, connection.connection, params=query_params).to_dict('records')

            def clean_trade(trade):
                for key, value in trade.items():
                    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                        trade[key] = None
                    elif value is None:
                        trade[key] = None  # Replace None with a safe default (can be None if needed)
                return trade

            safe_trades_list = [clean_trade(trade) for trade in trades_list]

            print(f"Retrieved {len(safe_trades_list)} trades, last trade is {safe_trades_list[-1] if safe_trades_list else None}")
            return {"data": safe_trades_list}
    except Exception as e:
        print(f"Error retrieving trades: {str(e)}")
        return {"error": str(e)}
