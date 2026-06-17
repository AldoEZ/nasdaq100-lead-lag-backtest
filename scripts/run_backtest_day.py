import sys
from datetime import date

from nasdaq_lead_lag.backtest.engine import run_backtest_day
from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.data.cleaning import add_trading_date_time, clean_market_data
from nasdaq_lead_lag.data.loader import load_selected_columns
from nasdaq_lead_lag.reporting.exports import export_csv
from nasdaq_lead_lag.research.correlations import select_top_pairs_for_day
from nasdaq_lead_lag.research.indicators import add_intraday_sma, get_intraday_data_for_symbols

def parse_target_day() -> date:
    if len(sys.argv) < 2:
        raise ValueError("Missing target date. Usage: python scripts/run_backtest_day.py YYYY-MM-DD")
    
    return date.fromisoformat(sys.argv[1])

def main() -> None:
    config = load_config()
    target_day = parse_target_day()
    
    print(f"Running one-day backtest for: {target_day}")
    
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
    
    symbols = sorted(set(top_pairs["leader"].to_list()) | set(top_pairs["follower"].to_list()))
    
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
    
    result = run_backtest_day(
        top_pairs=top_pairs,
        intraday_data=intraday_data,
        initial_capital=config.backtest.initial_capital,
        notional_per_trade=config.backtest.notional_per_trade,
        transaction_cost_per_share=config.backtest.transaction_cost_per_share,
        market_open=config.backtest.market_open,
        force_exit_time=config.backtest.force_exit_time,
        leader_edge=config.strategy.leader_edge,
        follower_edge=config.strategy.follower_edge,
        min_price=config.strategy.min_price,
        symbol_col=config.data.symbol_column,
        price_col=config.data.price_column,
        sma_col="sma_15",
    )
    
    trade_log_path = config.data.output_dir / "trade_logs" / f"trade_log_{target_day}.csv"
    equity_curve_path = (
        config.data.output_dir / "equity_curves" / f"strategy_equity_{target_day}.csv"
    )
    
    export_csv(result.trades, trade_log_path)
    export_csv(result.equity_curve, equity_curve_path)
    
    print(f"Trades generated: {len(result.trades)}")
    
    if not result.trades.empty:
        print(result.trades.head(20))
    
    print(f"Saved trade log to: {trade_log_path}")
    print(f"Saved equity curve to: {equity_curve_path}")
    print("One-day backtest completed successfully.")

if __name__ == "__main__":
    main()
