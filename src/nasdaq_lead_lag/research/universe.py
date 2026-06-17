from datetime import date

import polars as pl

from nasdaq_lead_lag.data.avoid_tickers import AVOID_TICKERS_BY_PERIOD

def parse_period(period: str) -> tuple[date, date]:
    start, end = period.split("/")
    
    return date.fromisoformat(start), date.fromisoformat(end)

def get_avoid_tickers_for_day(trading_day: date) -> set[str]:
    tickers: set[str] = set()
    
    for period, period_tickers in AVOID_TICKERS_BY_PERIOD.items():
        start, end = parse_period(period)
        
        if start <= trading_day <= end:
            tickers.update(period_tickers)
    
    return tickers

def get_daily_universe(
    data: pl.LazyFrame,
    trading_day: date,
    symbol_col: str,
    sector_col: str,
    market_cap_col: str,
) -> pl.DataFrame:
    avoid_tickers = get_avoid_tickers_for_day(trading_day)
    
    universe = (
        data.filter(pl.col("trading_date") == trading_day)
        .select([symbol_col, sector_col, market_cap_col])
        .drop_nulls([symbol_col, sector_col, market_cap_col])
        .unique(subset=[symbol_col])
        .collect()
    )
    
    if avoid_tickers:
        universe = universe.filter(~pl.col(symbol_col).is_in(list(avoid_tickers)))
    
    return universe
