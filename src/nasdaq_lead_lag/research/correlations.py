import polars as pl

def select_top_correlated_pairs(correlations: pl.DataFrame, top_n: int) -> pl.DataFrame:
    return (
        correlations
        .filter(pl.col("correlation").is_not_null())
        .sort("correlation", descending=True)
        .head(top_n)
    )
