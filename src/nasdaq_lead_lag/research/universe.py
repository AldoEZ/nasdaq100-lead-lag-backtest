import polars as pl

def get_daily_universe(
    data: pl.LazyFrame,
    trading_day,
    symbol_col: str,
    sector_col: str,
    market_cap_col: str,
) -> pl.DataFrame:
    return (
        data.filter(pl.col("trading_date") == trading_day)
        .select([symbol_col, sector_col, market_cap_col])
        .unique()
        .collect()
    )
