import polars as pl

def validate_required_columns(data: pl.LazyFrame, required_columns: list[str]) -> None:
    available_columns = set(data.collect_schema().names())
    missing_columns = sorted(set(required_columns) - available_columns)
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

def validate_no_duplicate_symbol_date(data: pl.LazyFrame, date_col: str, symbol_col: str) -> pl.DataFrame:
    return (
        data.group_by([date_col, symbol_col])
        .len()
        .filter(pl.col("len") > 1)
        .collect()
    )

def summarize_nulls(data: pl.LazyFrame, columns: list[str]) -> pl.DataFrame:
    expressions = [pl.col(column).is_null().sum().alias(f"null_{column}") for column in columns]
    return data.select(expressions).collect()
