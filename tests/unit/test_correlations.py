import pandas as pd
import polars as pl

from nasdaq_lead_lag.research.correlations import calculate_sector_pair_correlations

def test_calculate_sector_pair_correlations() -> None:
    universe = pl.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "sic_description": ["TECH", "TECH", "RETAIL"],
            "market_cap": [1000.0, 500.0, 300.0],
        }
    )
    
    returns = pd.DataFrame(
        {
            "A": [0.01, 0.02, 0.03, 0.04],
            "B": [0.01, 0.02, 0.03, 0.04],
            "C": [-0.01, -0.02, -0.01, -0.03],
        }
    )
    
    result = calculate_sector_pair_correlations(
        universe=universe,
        returns=returns,
        symbol_col="symbol",
        sector_col="sic_description",
        market_cap_col="market_cap",
        min_observations=2,
    )
    
    assert len(result) == 1
    assert result.loc[0, "ticker_a"] == "A"
    assert result.loc[0, "ticker_b"] == "B"
    assert result.loc[0, "leader"] == "A"
    assert result.loc[0, "follower"] == "B"
    assert result.loc[0, "correlation"] == 1.0
