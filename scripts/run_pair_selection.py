import sys
from datetime import date

from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.data.cleaning import add_trading_date_time, clean_market_data
from nasdaq_lead_lag.data.loader import load_selected_columns
from nasdaq_lead_lag.reporting.exports import export_csv
from nasdaq_lead_lag.research.correlations import select_top_pairs_for_day

def parse_target_day() -> date:
    if len(sys.argv) < 2:
        raise ValueError(
            "Missing target date. Usage: python scripts/run_pair_selection.py YYYY-MM-DD"
        )
    
    return date.fromisoformat(sys.argv[1])

def main() -> None:
    config = load_config()
    target_day = parse_target_day()
    
    print(f"Selecting top pairs for: {target_day}")
    
    required_columns = [
        config.data.date_column,
        config.data.symbol_column,
        config.data.price_column,
        config.data.sector_column,
        config.data.market_cap_column,
    ]
    
    data = load_selected_columns(
        path=config.data.nasdaq_path,
        columns=required_columns,
    )
    
    data = add_trading_date_time(
        data=data,
        date_col=config.data.date_column,
    )
    
    data = clean_market_data(
        data=data,
        price_col=config.data.price_column,
        sector_col=config.data.sector_column,
        market_cap_col=config.data.market_cap_column,
    )
    
    top_pairs = select_top_pairs_for_day(
        data=data,
        trading_day=target_day,
        lookback_days=config.strategy.correlation_window_days,
        top_n=config.strategy.top_n_pairs,
        symbol_col=config.data.symbol_column,
        sector_col=config.data.sector_column,
        market_cap_col=config.data.market_cap_column,
        price_col=config.data.price_column,
        date_col=config.data.date_column,
        market_open=config.backtest.market_open,
        market_close=config.backtest.market_close,
    )
    
    if top_pairs.empty:
        print("No valid pairs found.")
        return
    
    output_path = config.data.output_dir / "performance" / f"top_pairs_{target_day}.csv"
    
    export_csv(top_pairs, output_path)
    
    print(top_pairs.head(20))
    print(f"Saved top pairs to: {output_path}")
    print("Pair selection completed successfully.")

if __name__ == "__main__":
    main()
