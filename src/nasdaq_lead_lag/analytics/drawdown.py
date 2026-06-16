import polars as pl

def calculate_drawdown(data: pl.DataFrame, equity_col: str) -> pl.DataFrame:
    return data.with_columns(
        pl.col(equity_col).cum_max().alias("equity_peak")
    ).with_columns(
        ((pl.col(equity_col) / pl.col("equity_peak")) - 1.0).alias("drawdown")
    )
