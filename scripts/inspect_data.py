from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.data.loader import scan_parquet
from nasdaq_lead_lag.data.validation import summarize_nulls, validate_required_columns

def main() -> None:
    config = load_config()
    
    required_columns = [
        config.data.date_column,
        config.data.symbol_column,
        config.data.price_column,
        config.data.sector_column,
        config.data.market_cap_column,
    ]
    
    data = scan_parquet(config.data.nasdaq_path)
    
    validate_required_columns(data, required_columns)
    
    null_summary = summarize_nulls(data, required_columns)
    
    print("Data inspection completed.")
    print(null_summary)

if __name__ == "__main__":
    main()