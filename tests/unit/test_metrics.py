import polars as pl

from nasdaq_lead_lag.analytics.metrics import total_return

def test_total_return() -> None:
    equity = pl.Series([100.0, 150.0])
    assert total_return(equity) == 0.5
