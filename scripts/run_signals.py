import sys
from datetime import date

from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.data.cleaning import add_trading_date_time, clean_market_data
from nasdaq_lead_lag.data.loader import load_selected_columns
from nasdaq_lead_lag.reporting.exports import export_csv
from nasdaq_lead_lag.research.correlations import select_top_pairs_for_day
from nasdaq_lead_lag.research.indicators import add_intraday_sma, get_intraday_data_for_symbols
from nasdaq_lead_lag.research.signals import generate_intraday_signals, resolve_signal_conflicts

def parse_target_day() -> date:
    if len(sys.argv) < 2:
        raise ValueError("Missing target date. Usage: python scripts/run_signals.py YYYY-MM-DD")
    
    return date.fromisoformat(sys.argv[1])

def main() -> None:
    config = load_config()
    target_day = parse_target_day()
    
    print(f"Generating intraday signals for: {target_day}")
    
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
        print("No valid top pairs found.")
        return
    
    symbols = sorted(
        set(top_pairs["leader"].to_list())
        | set(top_pairs["follower"].to_list())
    )
    
    intraday_data = get_intraday_data_for_symbols(
        data=data,
        trading_day=target_day,
        symbols=symbols,
        date_col=config.data.date_column,
        symbol_col=config.data.symbol_column,
        price_col=config.data.price_column,
        force_exit_time=config.backtest.force_exit_time,
    )
    
    if intraday_data.is_empty():
        print("No intraday data found for selected symbols.")
        return
    
    intraday_data = add_intraday_sma(
        data=intraday_data,
        symbol_col=config.data.symbol_column,
        price_col=config.data.price_column,
        window=config.strategy.sma_window_minutes,
        output_col="sma_15",
    )
    
    raw_signals = generate_intraday_signals(
        top_pairs=top_pairs,
        intraday_data=intraday_data,
        market_open=config.backtest.market_open,
        force_exit_time=config.backtest.force_exit_time,
        leader_edge=config.strategy.leader_edge,
        follower_edge=config.strategy.follower_edge,
        min_price=config.strategy.min_price,
        symbol_col=config.data.symbol_column,
        price_col=config.data.price_column,
        sma_col="sma_15",
    )
    
    signals = resolve_signal_conflicts(raw_signals)
    
    raw_output_path = config.data.output_dir / "performance" / f"raw_signals_{target_day}.csv"
    output_path = config.data.output_dir / "performance" / f"signals_{target_day}.csv"
    
    export_csv(raw_signals, raw_output_path)
    export_csv(signals, output_path)
    
    print(f"Raw signals: {len(raw_signals)}")
    print(f"Resolved signals: {len(signals)}")
    
    if not signals.empty:
        print(signals.head(20))
    
    print(f"Saved raw signals to: {raw_output_path}")
    print(f"Saved resolved signals to: {output_path}")
    print("Signal generation completed successfully.")

if __name__ == "__main__":
    main()
