from datetime import date, time

import pandas as pd
import polars as pl
import pytest

from nasdaq_lead_lag.backtest.engine import run_backtest_day

def test_run_backtest_day_generates_long_trade() -> None:
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
                "2024-01-03 09:31:00",
                "2024-01-03 09:31:00",
            ],
            "trading_date": [
                date(2024, 1, 3),
                date(2024, 1, 3),
                date(2024, 1, 3),
                date(2024, 1, 3),
            ],
            "trading_time": [
                time(9, 30),
                time(9, 30),
                time(9, 31),
                time(9, 31),
            ],
            "symbol": ["A", "B", "A", "B"],
            "close": [101.0, 50.0, 99.0, 51.0],
            "sma_15": [100.0, 50.1, 100.0, 50.1],
        }
    ).with_columns(
        pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
    )
    
    result = run_backtest_day(
        top_pairs=top_pairs,
        intraday_data=intraday_data,
        initial_capital=1_000_000,
        notional_per_trade=100_000,
        transaction_cost_per_share=0.0035,
        market_open=time(9, 30),
        force_exit_time=time(15, 55),
        leader_edge=0.006,
        follower_edge=0.002,
        min_price=10.0,
    )
    
    assert len(result.trades) == 1
    
    trade = result.trades.iloc[0]
    
    assert trade["side"] == "LONG"
    assert trade["entry_price"] == 50.0
    assert trade["exit_price"] == 51.0
    assert trade["quantity"] == 2000
    assert trade["gross_pnl"] == pytest.approx(2000.0)
    assert trade["transaction_costs"] == pytest.approx(14.0)
    assert trade["net_pnl"] == pytest.approx(1986.0)
