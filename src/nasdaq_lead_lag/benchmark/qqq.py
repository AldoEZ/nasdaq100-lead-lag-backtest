import polars as pl

def build_buy_and_hold_equity(
    qqq_data: pl.DataFrame,
    initial_capital: float,
    price_col: str = "close",
) -> pl.DataFrame:
    first_price = qqq_data.select(pl.col(price_col).first()).item()
    
    return qqq_data.with_columns(
        (initial_capital * pl.col(price_col) / first_price).alias("benchmark_equity")
    )
