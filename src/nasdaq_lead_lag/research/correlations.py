from datetime import date, time
from itertools import combinations

import numpy as np
import pandas as pd
import polars as pl

from nasdaq_lead_lag.research.universe import get_daily_universe

def get_previous_trading_days(
    data: pl.LazyFrame,
    trading_day: date,
    lookback_days: int,
) -> list[date]:
    previous_days = (
        data.filter(pl.col("trading_date") < trading_day)
        .select("trading_date")
        .unique()
        .sort("trading_date")
        .tail(lookback_days)
        .collect()
        .get_column("trading_date")
        .to_list()
    )
    
    return previous_days

def build_daily_close_matrix(
    data: pl.LazyFrame,
    trading_days: list[date],
    symbol_col: str,
    price_col: str,
    date_col: str,
    market_open: time,
    market_close: time,
) -> pd.DataFrame:
    daily_close = (
        data.filter(
            pl.col("trading_date").is_in(trading_days),
            pl.col("trading_time").is_between(market_open, market_close, closed="both"),
        )
        .sort([symbol_col, date_col])
        .group_by(["trading_date", symbol_col])
        .agg(pl.col(price_col).last().alias("daily_close"))
        .collect()
    )
    
    if daily_close.is_empty():
        return pd.DataFrame()
    
    return (
        daily_close.to_pandas()
        .pivot(index="trading_date", columns=symbol_col, values="daily_close")
        .sort_index()
    )

def calculate_return_matrix(daily_close_matrix: pd.DataFrame) -> pd.DataFrame:
    return daily_close_matrix.pct_change().dropna(how="all")

def calculate_sector_pair_correlations(
    universe: pl.DataFrame,
    returns: pd.DataFrame,
    symbol_col: str,
    sector_col: str,
    market_cap_col: str,
    min_observations: int = 30,
) -> pd.DataFrame:
    if universe.is_empty() or returns.empty:
        return pd.DataFrame()
    
    universe_pd = universe.to_pandas()
    
    valid_symbols = set(returns.columns)
    universe_pd = universe_pd[universe_pd[symbol_col].isin(valid_symbols)]
    
    rows: list[dict] = []
    
    for sector, sector_group in universe_pd.groupby(sector_col):
        symbols = sorted(sector_group[symbol_col].unique())
        
        if len(symbols) < 2:
            continue
        
        metadata_by_symbol = sector_group.drop_duplicates(symbol_col).set_index(symbol_col)
        
        for ticker_a, ticker_b in combinations(symbols, 2):
            pair_returns = returns[[ticker_a, ticker_b]].dropna()
            
            if len(pair_returns) < min_observations:
                continue
            
            correlation = pair_returns[ticker_a].corr(pair_returns[ticker_b])
            
            if pd.isna(correlation):
                continue
            
            market_cap_a = float(metadata_by_symbol.loc[ticker_a, market_cap_col])
            market_cap_b = float(metadata_by_symbol.loc[ticker_b, market_cap_col])
            
            if market_cap_a >= market_cap_b:
                leader = ticker_a
                follower = ticker_b
                leader_market_cap = market_cap_a
                follower_market_cap = market_cap_b
            else:
                leader = ticker_b
                follower = ticker_a
                leader_market_cap = market_cap_b
                follower_market_cap = market_cap_a
            
            rows.append(
                {
                    "sector": sector,
                    "ticker_a": ticker_a,
                    "ticker_b": ticker_b,
                    "correlation": float(correlation),
                    "leader": leader,
                    "follower": follower,
                    "leader_market_cap": leader_market_cap,
                    "follower_market_cap": follower_market_cap,
                    "observations": int(len(pair_returns)),
                }
            )
    
    if not rows:
        return pd.DataFrame()
    
    return pd.DataFrame(rows)

def select_top_correlated_pairs(
    correlations: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    if correlations.empty:
        return correlations
    
    return (
        correlations.sort_values("correlation", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

def select_top_pairs_for_day(
    data: pl.LazyFrame,
    trading_day: date,
    lookback_days: int,
    top_n: int,
    symbol_col: str,
    sector_col: str,
    market_cap_col: str,
    price_col: str,
    date_col: str,
    market_open: time,
    market_close: time,
    min_observations: int = 30,
) -> pd.DataFrame:
    previous_days = get_previous_trading_days(
        data=data,
        trading_day=trading_day,
        lookback_days=lookback_days,
    )
    
    if len(previous_days) < lookback_days:
        raise ValueError(
            f"Not enough lookback history for {trading_day}. "
            f"Required {lookback_days}, found {len(previous_days)}."
        )
    
    universe = get_daily_universe(
        data=data,
        trading_day=trading_day,
        symbol_col=symbol_col,
        sector_col=sector_col,
        market_cap_col=market_cap_col,
    )
    
    daily_close_matrix = build_daily_close_matrix(
        data=data,
        trading_days=previous_days,
        symbol_col=symbol_col,
        price_col=price_col,
        date_col=date_col,
        market_open=market_open,
        market_close=market_close,
    )
    
    returns = calculate_return_matrix(daily_close_matrix)
    
    correlations = calculate_sector_pair_correlations(
        universe=universe,
        returns=returns,
        symbol_col=symbol_col,
        sector_col=sector_col,
        market_cap_col=market_cap_col,
        min_observations=min_observations,
    )
    
    return select_top_correlated_pairs(
        correlations=correlations,
        top_n=top_n,
    )
