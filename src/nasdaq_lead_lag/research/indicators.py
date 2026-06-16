import polars as pl

def add_sma(
    data: pl.LazyFrame,
    symbol_col: str,
    price_col: str,
    window: int,
    output_col: str = "sma_15",
) -> pl.LazyFrame:
    return data.with_columns(
        pl.col(price_col)
        .rolling_mean(window_size=window)
        .over(symbol_col)
        .shift(1)
        .alias(output_col)
    )
