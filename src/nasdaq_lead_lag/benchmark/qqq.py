from datetime import date, time
from pathlib import Path

import polars as pl

REQUIRED_QQQ_COLUMNS = [
    "date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "vwap",
    "transactions",
]

def load_qqq_data(path: str | Path) -> pl.DataFrame:
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"QQQ parquet file not found: {path}")
    
    data = pl.scan_parquet(path)
    
    available_columns = set(data.collect_schema().names())
    missing_columns = sorted(set(REQUIRED_QQQ_COLUMNS) - available_columns)
    
    if missing_columns:
        raise ValueError(f"Missing required QQQ columns: {missing_columns}")
    
    return data.select(REQUIRED_QQQ_COLUMNS).sort("date").collect()

def add_trading_date_time(data: pl.DataFrame, date_col: str = "date") -> pl.DataFrame:
    return data.with_columns(
        pl.col(date_col).dt.date().alias("trading_date"),
        pl.col(date_col).dt.time().alias("trading_time"),
    )

def filter_regular_session(
    data: pl.DataFrame,
    market_open: time,
    market_close: time,
    date_col: str = "date",
) -> pl.DataFrame:
    data = add_trading_date_time(data, date_col=date_col)
    
    return data.filter(
        pl.col("trading_time").is_between(
            market_open,
            market_close,
            closed="both",
        )
    ).sort(date_col)

def filter_date_range(
    data: pl.DataFrame,
    start_date: date,
    end_date: date,
) -> pl.DataFrame:
    return data.filter(
        pl.col("trading_date") >= start_date,
        pl.col("trading_date") <= end_date,
    ).sort("date")

def build_buy_and_hold_equity(
    data: pl.DataFrame,
    initial_capital: float,
    price_col: str = "close",
    equity_col: str = "benchmark_equity",
    return_col: str = "benchmark_return",
) -> pl.DataFrame:
    if data.is_empty():
        raise ValueError("Cannot build benchmark equity curve from an empty DataFrame.")
    
    first_price = data.select(pl.col(price_col).drop_nulls().first()).item()
    
    if first_price is None or first_price <= 0:
        raise ValueError(f"Invalid first benchmark price: {first_price}")
    
    return data.with_columns(
        (initial_capital * pl.col(price_col) / first_price).alias(equity_col)
    ).with_columns(
        pl.col(equity_col).pct_change().fill_null(0.0).alias(return_col)
    )

def to_daily_equity(
    data: pl.DataFrame,
    date_col: str = "date",
    equity_col: str = "benchmark_equity",
    return_col: str = "benchmark_return",
) -> pl.DataFrame:
    if "trading_date" not in data.columns:
        data = add_trading_date_time(data, date_col=date_col)
    
    return (
        data.sort(date_col)
        .group_by("trading_date")
        .agg(
            pl.col(date_col).last().alias(date_col),
            pl.col(equity_col).last().alias(equity_col),
        )
        .sort("trading_date")
        .with_columns(pl.col(equity_col).pct_change().fill_null(0.0).alias(return_col))
    )

def build_qqq_benchmark(
    path: str | Path,
    initial_capital: float,
    market_open: time,
    market_close: time,
) -> pl.DataFrame:
    qqq_data = load_qqq_data(path)
    
    qqq_regular_session = filter_regular_session(
        qqq_data,
        market_open=market_open,
        market_close=market_close,
    )
    
    return build_buy_and_hold_equity(
        qqq_regular_session,
        initial_capital=initial_capital,
    )

def build_qqq_benchmark_for_period(
    path: str | Path,
    start_date: date,
    end_date: date,
    initial_capital: float,
    market_open: time,
    market_close: time,
) -> pl.DataFrame:
    qqq_data = load_qqq_data(path)
    
    qqq_regular_session = filter_regular_session(
        qqq_data,
        market_open=market_open,
        market_close=market_close,
    )
    
    qqq_period = filter_date_range(
        qqq_regular_session,
        start_date=start_date,
        end_date=end_date,
    )
    
    return build_buy_and_hold_equity(
        qqq_period,
        initial_capital=initial_capital,
    )
