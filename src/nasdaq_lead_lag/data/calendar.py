import polars as pl

def get_trading_days(data: pl.LazyFrame) -> list:
    days = (
        data.select("trading_date")
        .unique()
        .sort("trading_date")
        .collect()
        .get_column("trading_date")
        .to_list()
    )
    return days
