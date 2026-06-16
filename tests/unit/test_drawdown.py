import polars as pl

from nasdaq_lead_lag.analytics.drawdown import calculate_drawdown

def test_calculate_drawdown() -> None:
    data = pl.DataFrame({"equity": [100.0, 120.0, 90.0, 150.0]})
    result = calculate_drawdown(data, "equity")
    
    assert result["drawdown"].to_list() == [0.0, 0.0, -0.25, 0.0]
