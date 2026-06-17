from datetime import time

import pandas as pd
import polars as pl

SIGNAL_COLUMNS = [
    "entry_time",
    "trading_date",
    "trading_time",
    "sector",
    "leader",
    "follower",
    "side",
    "leader_price",
    "follower_price",
    "leader_base_sma",
    "follower_base_sma",
    "leader_long_sma",
    "follower_long_sma",
    "leader_short_sma",
    "follower_short_sma",
    "correlation",
    "entry_reason",
]

def _empty_signals() -> pd.DataFrame:
    return pd.DataFrame(columns=SIGNAL_COLUMNS)

def generate_intraday_signals(
    top_pairs: pd.DataFrame,
    intraday_data: pl.DataFrame,
    market_open: time,
    force_exit_time: time,
    leader_edge: float,
    follower_edge: float,
    min_price: float,
    symbol_col: str = "symbol",
    price_col: str = "close",
    sma_col: str = "sma_15",
) -> pd.DataFrame:
    """
    Generate raw long and short signals for the selected pairs.
    
    Long rule:
        leader_price > leader_sma * (1 + leader_edge)
        follower_price < follower_sma * (1 + follower_edge)
    
    Short rule:
        leader_price < leader_sma * (1 - leader_edge)
        follower_price < follower_sma * (1 - follower_edge)
    """
    
    if top_pairs.empty or intraday_data.is_empty():
        return _empty_signals()
    
    prices = intraday_data.to_pandas()
    
    rows: list[dict] = []
    
    for pair in top_pairs.itertuples(index=False):
        leader = pair.leader
        follower = pair.follower
        
        leader_prices = (
            prices.loc[prices[symbol_col] == leader, ["date", "trading_date", "trading_time", price_col, sma_col]]
            .rename(
                columns={
                    price_col: "leader_price",
                    sma_col: "leader_base_sma",
                }
            )
        )
        
        follower_prices = (
            prices.loc[prices[symbol_col] == follower, ["date", "trading_date", "trading_time", price_col, sma_col]]
            .rename(
                columns={
                    price_col: "follower_price",
                    sma_col: "follower_base_sma",
                }
            )
        )
        
        merged = leader_prices.merge(
            follower_prices,
            on=["date", "trading_date", "trading_time"],
            how="inner",
        )
        
        if merged.empty:
            continue
        
        merged = merged[
            (merged["trading_time"] >= market_open)
            & (merged["trading_time"] <= force_exit_time)
        ].copy()
        
        if merged.empty:
            continue
        
        merged = merged.dropna(
            subset=[
                "leader_price",
                "follower_price",
                "leader_base_sma",
                "follower_base_sma",
            ]
        )
        
        if merged.empty:
            continue
        
        merged["leader_long_sma"] = merged["leader_base_sma"] * (1.0 + leader_edge)
        merged["follower_long_sma"] = merged["follower_base_sma"] * (1.0 + follower_edge)
        
        merged["leader_short_sma"] = merged["leader_base_sma"] * (1.0 - leader_edge)
        merged["follower_short_sma"] = merged["follower_base_sma"] * (1.0 - follower_edge)
        
        long_condition = (
            (merged["leader_price"] > merged["leader_long_sma"])
            & (merged["follower_price"] < merged["follower_long_sma"])
            & (merged["follower_price"] > min_price)
        )
        
        short_condition = (
            (merged["leader_price"] < merged["leader_short_sma"])
            & (merged["follower_price"] < merged["follower_short_sma"])
            & (merged["follower_price"] > min_price)
        )
        
        for row in merged.loc[long_condition].itertuples(index=False):
            rows.append(
                {
                    "entry_time": row.date,
                    "trading_date": row.trading_date,
                    "trading_time": row.trading_time,
                    "sector": pair.sector,
                    "leader": leader,
                    "follower": follower,
                    "side": "LONG",
                    "leader_price": row.leader_price,
                    "follower_price": row.follower_price,
                    "leader_base_sma": row.leader_base_sma,
                    "follower_base_sma": row.follower_base_sma,
                    "leader_long_sma": row.leader_long_sma,
                    "follower_long_sma": row.follower_long_sma,
                    "leader_short_sma": row.leader_short_sma,
                    "follower_short_sma": row.follower_short_sma,
                    "correlation": pair.correlation,
                    "entry_reason": "leader_above_long_sma_and_follower_below_long_sma",
                }
            )
        
        for row in merged.loc[short_condition].itertuples(index=False):
            rows.append(
                {
                    "entry_time": row.date,
                    "trading_date": row.trading_date,
                    "trading_time": row.trading_time,
                    "sector": pair.sector,
                    "leader": leader,
                    "follower": follower,
                    "side": "SHORT",
                    "leader_price": row.leader_price,
                    "follower_price": row.follower_price,
                    "leader_base_sma": row.leader_base_sma,
                    "follower_base_sma": row.follower_base_sma,
                    "leader_long_sma": row.leader_long_sma,
                    "follower_long_sma": row.follower_long_sma,
                    "leader_short_sma": row.leader_short_sma,
                    "follower_short_sma": row.follower_short_sma,
                    "correlation": pair.correlation,
                    "entry_reason": "leader_below_short_sma_and_follower_below_short_sma",
                }
            )
    
    if not rows:
        return _empty_signals()
    
    return pd.DataFrame(rows).sort_values(
        ["entry_time", "follower", "correlation"],
        ascending=[True, True, False],
    )

def resolve_signal_conflicts(signals: pd.DataFrame) -> pd.DataFrame:
    """
    Resolve duplicated or conflicting signals.

    Rules:
        1. If the same follower has both LONG and SHORT signals at the same minute, drop them.
        2. If multiple pairs generate the same side signal for the same follower and minute, keep the one with the highest correlation.
    """
    
    if signals.empty:
        return signals
    
    signals = signals.copy()
    
    side_count = signals.groupby(["entry_time", "follower"])["side"].transform("nunique")
    signals = signals[side_count == 1]
    
    signals = signals.sort_values(
        ["entry_time", "follower", "correlation"],
        ascending=[True, True, False],
    )
    
    signals = signals.drop_duplicates(
        subset=["entry_time", "follower"],
        keep="first",
    )
    
    return signals.reset_index(drop=True)
