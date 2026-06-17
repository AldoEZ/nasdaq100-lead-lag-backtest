from datetime import date, time

import pandas as pd
import polars as pl

from nasdaq_lead_lag.research.signals import generate_intraday_signals, resolve_signal_conflicts

def test_generate_intraday_long_signal() -> None:
    top_pairs = pd.DataFrame(
        {
            "sector": ["TECH"],
            "leader": ["A"],
            "follower": ["B"],
            "correlation": [0.95],
        }
    )
    
    intraday_data = pl.DataFrame(
        {
            "date": [
                "2024-01-03 09:30:00",
                "2024-01-03 09:30:00",
            ],
            "trading_date": [
                date(2024, 1, 3),
                date(2024, 1, 3),
            ],
            "trading_time": [
                time(9, 30),
                time(9, 30),
            ],
            "symbol": ["A", "B"],
            "close": [101.0, 50.0],
            "sma_15": [100.0, 50.1],
        }
    ).with_columns(
        pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
    )
    
    signals = generate_intraday_signals(
        top_pairs=top_pairs,
        intraday_data=intraday_data,
        market_open=time(9, 30),
        force_exit_time=time(15, 55),
        leader_edge=0.006,
        follower_edge=0.002,
        min_price=10.0,
    )
    
    assert len(signals) == 1
    assert signals.loc[0, "side"] == "LONG"
    assert signals.loc[0, "leader"] == "A"
    assert signals.loc[0, "follower"] == "B"

def test_generate_intraday_short_signal() -> None:
    top_pairs = pd.DataFrame(
        {
            "sector": ["TECH"],
            "leader": ["A"],
            "follower": ["B"],
            "correlation": [0.95],
        }
    )
    
    intraday_data = pl.DataFrame(
        {
            "date": [
                "2024-01-03 09:30:00",
                "2024-01-03 09:30:00",
            ],
            "trading_date": [
                date(2024, 1, 3),
                date(2024, 1, 3),
            ],
            "trading_time": [
                time(9, 30),
                time(9, 30),
            ],
            "symbol": ["A", "B"],
            "close": [99.0, 49.0],
            "sma_15": [100.0, 50.0],
        }
    ).with_columns(
        pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
    )
    
    signals = generate_intraday_signals(
        top_pairs=top_pairs,
        intraday_data=intraday_data,
        market_open=time(9, 30),
        force_exit_time=time(15, 55),
        leader_edge=0.006,
        follower_edge=0.002,
        min_price=10.0,
    )
    
    assert len(signals) == 1
    assert signals.loc[0, "side"] == "SHORT"
    assert signals.loc[0, "leader"] == "A"
    assert signals.loc[0, "follower"] == "B"

def test_resolve_signal_conflicts_keeps_highest_correlation() -> None:
    signals = pd.DataFrame(
        {
            "entry_time": ["2024-01-03 09:30:00", "2024-01-03 09:30:00"],
            "follower": ["B", "B"],
            "side": ["LONG", "LONG"],
            "correlation": [0.80, 0.95],
        }
    )
    
    result = resolve_signal_conflicts(signals)
    
    assert len(result) == 1
    assert result.loc[0, "correlation"] == 0.95

def test_resolve_signal_conflicts_drops_long_short_conflict() -> None:
    signals = pd.DataFrame(
        {
            "entry_time": ["2024-01-03 09:30:00", "2024-01-03 09:30:00"],
            "follower": ["B", "B"],
            "side": ["LONG", "SHORT"],
            "correlation": [0.90, 0.95],
        }
    )
    
    result = resolve_signal_conflicts(signals)
    
    assert result.empty
