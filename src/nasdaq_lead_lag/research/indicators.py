from datetime import date, time

import polars as pl

def get_intraday_data_for_symbols(
    data: pl.LazyFrame,
    trading_day: date,
    symbols: list[str],
    date_col: str,
    symbol_col: str,
    price_col: str,
    force_exit_time: time,
) -> pl.DataFrame:
    """
    Get intraday data for a given trading day and a list of symbols.
    
    We keep data before the market open because the strategy needs the SMA
    to be available as early as 09:30.
    """
    
    return (
        data.filter(
            pl.col("trading_date") == trading_day,
            pl.col(symbol_col).is_in(symbols),
            pl.col("trading_time") <= force_exit_time,
        )
        .select(
            [
                date_col,
                "trading_date",
                "trading_time",
                symbol_col,
                price_col,
            ]
        )
        .sort([symbol_col, date_col])
        .collect()
    )

def add_sma(
    data: pl.LazyFrame,
    symbol_col: str,
    price_col: str,
    window: int,
    output_col: str = "sma_15",
) -> pl.LazyFrame:
    """
    Add a shifted rolling SMA to a LazyFrame.
    
    The shift prevents look-ahead bias by making sure the current bar
    does not use its own close to generate a signal.
    """
    
    return (
        data.sort([symbol_col, "date"])
        .with_columns(
            pl.col(price_col)
            .rolling_mean(window_size=window)
            .shift(1)
            .over(symbol_col)
            .alias(output_col)
        )
    )

def add_intraday_sma(
    data: pl.DataFrame,
    symbol_col: str,
    price_col: str,
    window: int,
    output_col: str = "sma_15",
) -> pl.DataFrame:
    """
    Add a shifted rolling SMA to an eager Polars DataFrame.
    """
    
    return (
        data.sort([symbol_col, "date"])
        .with_columns(
            pl.col(price_col)
            .rolling_mean(window_size=window)
            .shift(1)
            .over(symbol_col)
            .alias(output_col)
        )
        .sort(["date", symbol_col])
    )
