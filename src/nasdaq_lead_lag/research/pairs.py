from itertools import combinations

import polars as pl

def build_sector_pairs(
    universe: pl.DataFrame,
    symbol_col: str,
    sector_col: str,
) -> pl.DataFrame:
    rows: list[dict] = []
    
    for sector, group in universe.group_by(sector_col):
        sector_name = sector[0] if isinstance(sector, tuple) else sector
        symbols = sorted(group.get_column(symbol_col).to_list())
        
        if len(symbols) < 2:
            continue
        
        for ticker_a, ticker_b in combinations(symbols, 2):
            rows.append(
                {
                    "sector": sector_name,
                    "ticker_a": ticker_a,
                    "ticker_b": ticker_b,
                }
            )
    
    return pl.DataFrame(rows)
