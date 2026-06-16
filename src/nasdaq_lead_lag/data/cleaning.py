import polars as pl

def clean_market_data(
    data: pl.LazyFrame,
    price_col: str,
    sector_col: str,
    market_cap_col: str,
) -> pl.LazyFrame:
    return data.filter(
        pl.col(price_col).is_not_null(),
        pl.col(price_col) > 0,
        pl.col(sector_col).is_not_null(),
        pl.col(market_cap_col).is_not_null(),
    )

def add_trading_date_time(data: pl.LazyFrame, date_col: str) -> pl.LazyFrame:
    return data.with_columns(
        pl.col(date_col).dt.date().alias("trading_date"),
        pl.col(date_col).dt.time().alias("trading_time"),
    )
