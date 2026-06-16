import polars as pl

from nasdaq_lead_lag.research.pairs import build_sector_pairs

def test_build_sector_pairs() -> None:
    universe = pl.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "sic_description": ["TECH", "TECH", "RETAIL"],
        }
    )
    
    pairs = build_sector_pairs(universe, "symbol", "sic_description")
    
    assert pairs.height == 1
    assert pairs.row(0, named=True)["ticker_a"] == "A"
    assert pairs.row(0, named=True)["ticker_b"] == "B"
