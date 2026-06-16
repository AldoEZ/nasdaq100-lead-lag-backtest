from pathlib import Path

import polars as pl

def scan_parquet(path: str | Path) -> pl.LazyFrame:
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    
    return pl.scan_parquet(path)

def load_selected_columns(path: str | Path, columns: list[str]) -> pl.LazyFrame:
    return scan_parquet(path).select(columns)
