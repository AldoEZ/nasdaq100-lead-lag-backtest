import sys
from datetime import date

import pandas as pd
import polars as pl
from tqdm import tqdm

from nasdaq_lead_lag.analytics.drawdown import calculate_drawdown
from nasdaq_lead_lag.analytics.metrics import calculate_performance_metrics
from nasdaq_lead_lag.analytics.performance_table import build_performance_table
from nasdaq_lead_lag.backtest.engine import run_backtest_day
from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.data.cleaning import add_trading_date_time, clean_market_data
from nasdaq_lead_lag.data.loader import load_selected_columns
from nasdaq_lead_lag.reporting.exports import export_csv
from nasdaq_lead_lag.reporting.plots import plot_drawdown_curve, plot_single_equity_curve
from nasdaq_lead_lag.research.correlations import select_top_pairs_for_day
from nasdaq_lead_lag.research.indicators import add_intraday_sma, get_intraday_data_for_symbols

def parse_date_range() -> tuple[date, date]:
    if len(sys.argv) < 3:
        raise ValueError(
            "Missing date range. Usage: python scripts/run_backtest.py YYYY-MM-DD YYYY-MM-DD"
        )
    
    start_date = date.fromisoformat(sys.argv[1])
    end_date = date.fromisoformat(sys.argv[2])
    
    if start_date > end_date:
        raise ValueError("start_date cannot be greater than end_date.")
    
    return start_date, end_date

def get_trading_days_in_range(
    data: pl.LazyFrame,
    start_date: date,
    end_date: date,
) -> list[date]:
    return (
        data.filter(
            pl.col("trading_date") >= start_date,
            pl.col("trading_date") <= end_date,
        )
        .select("trading_date")
        .unique()
        .sort("trading_date")
        .collect()
        .get_column("trading_date")
        .to_list()
    )

def build_daily_strategy_equity(
    equity_curve: pd.DataFrame,
    date_col: str = "date",
    equity_col: str = "strategy_equity",
) -> pl.DataFrame:
    if equity_curve.empty:
        raise ValueError("Cannot build daily equity from an empty equity curve.")
    
    data = equity_curve.copy()
    data[date_col] = pd.to_datetime(data[date_col])
    data["trading_date"] = data[date_col].dt.date
    
    daily = (
        data.sort_values(date_col)
        .groupby("trading_date", as_index=False)
        .last()[["trading_date", date_col, equity_col]]
        .sort_values("trading_date")
    )
    
    daily["strategy_return"] = daily[equity_col].pct_change().fillna(0.0)
    
    return pl.from_pandas(daily)

def main() -> None:
    config = load_config()
    start_date, end_date = parse_date_range()
    
    print(f"Running multi-day backtest from {start_date} to {end_date}")
    
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
    
    trading_days = get_trading_days_in_range(
        data=data,
        start_date=start_date,
        end_date=end_date,
    )
    
    if not trading_days:
        print("No trading days found in the selected range.")
        return
    
    print(f"Trading days found: {len(trading_days)}")
    
    current_capital = config.backtest.initial_capital
    
    all_trades: list[pd.DataFrame] = []
    all_equity_curves: list[pd.DataFrame] = []
    skipped_days: list[dict] = []
    
    for trading_day in tqdm(trading_days, desc="Backtesting days"):
        try:
            top_pairs = select_top_pairs_for_day(
                data=data,
                trading_day=trading_day,
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
        except ValueError as error:
            skipped_days.append(
                {
                    "trading_date": trading_day,
                    "reason": str(error),
                }
            )
            continue
        
        if top_pairs.empty:
            skipped_days.append(
                {
                    "trading_date": trading_day,
                    "reason": "No valid top pairs found.",
                }
            )
            continue
        
        symbols = sorted(
            set(top_pairs["leader"].to_list())
            | set(top_pairs["follower"].to_list())
        )
        
        intraday_data = get_intraday_data_for_symbols(
            data=data,
            trading_day=trading_day,
            symbols=symbols,
            date_col=config.data.date_column,
            symbol_col=config.data.symbol_column,
            price_col=config.data.price_column,
            force_exit_time=config.backtest.force_exit_time,
        )
        
        if intraday_data.is_empty():
            skipped_days.append(
                {
                    "trading_date": trading_day,
                    "reason": "No intraday data found.",
                }
            )
            continue
        
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
            initial_capital=current_capital,
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
        
        if not result.trades.empty:
            result.trades["trading_date"] = trading_day
            all_trades.append(result.trades)
        
        if not result.equity_curve.empty:
            day_equity = result.equity_curve.copy()
            day_equity["trading_date"] = trading_day
            all_equity_curves.append(day_equity)
            
            current_capital = float(day_equity["equity"].iloc[-1])
    
    if not all_equity_curves:
        print("No equity curve was generated.")
        return
    
    full_equity = pd.concat(all_equity_curves, ignore_index=True)
    full_equity = full_equity.rename(
        columns={
            "equity": "strategy_equity",
            "return": "strategy_return",
        }
    )
    
    full_trades = (
        pd.concat(all_trades, ignore_index=True)
        if all_trades
        else pd.DataFrame()
    )
    
    equity_curve_path = config.data.output_dir / "equity_curves" / "strategy_equity_full.csv"
    trade_log_path = config.data.output_dir / "trade_logs" / "trade_log_full.csv"
    skipped_days_path = config.data.output_dir / "performance" / "skipped_days.csv"
    
    export_csv(full_equity, equity_curve_path)
    export_csv(full_trades, trade_log_path)
    
    if skipped_days:
        export_csv(pd.DataFrame(skipped_days), skipped_days_path)
    
    daily_equity = build_daily_strategy_equity(
        equity_curve=full_equity,
        date_col="date",
        equity_col="strategy_equity",
    )
    
    daily_equity_path = config.data.output_dir / "equity_curves" / "strategy_daily_equity.csv"
    
    export_csv(daily_equity.to_pandas(), daily_equity_path)
    
    strategy_metrics = calculate_performance_metrics(
        daily_equity,
        date_col="date",
        equity_col="strategy_equity",
        return_col="strategy_return",
        periods_per_year=252,
        bar_freq="D",
    )
    
    performance_table = build_performance_table(
        {
            "Strategy": strategy_metrics,
        }
    )
    
    performance_table_path = config.data.output_dir / "performance" / "strategy_performance_table.csv"
    
    export_csv(
        performance_table.rename_axis("metric").reset_index(),
        performance_table_path,
    )
    
    daily_drawdown = calculate_drawdown(
        daily_equity,
        equity_col="strategy_equity",
    )
    
    equity_plot_path = config.data.output_dir / "plots" / "strategy_equity_curve_log.png"
    
    plot_single_equity_curve(
        data=daily_equity.to_pandas(),
        date_col="date",
        equity_col="strategy_equity",
        label="Strategy",
        output_path=equity_plot_path,
        title="Strategy Equity Curve - Log Scale",
        log_scale=True,
    )
    
    drawdown_plot_path = config.data.output_dir / "plots" / "strategy_drawdown.png"
    
    plot_drawdown_curve(
        data=daily_drawdown.to_pandas(),
        date_col="date",
        drawdown_col="drawdown",
        label="Strategy",
        output_path=drawdown_plot_path,
        title="Strategy Drawdown",
    )
    
    print("Multi-day backtest completed successfully.")
    print(f"Initial capital: {config.backtest.initial_capital:,.2f}")
    print(f"Final capital: {current_capital:,.2f}")
    print(f"Trades generated: {len(full_trades)}")
    print(f"Trading days processed: {len(all_equity_curves)}")
    print(f"Trading days skipped: {len(skipped_days)}")
    print(f"Saved equity curve to: {equity_curve_path}")
    print(f"Saved daily equity to: {daily_equity_path}")
    print(f"Saved trade log to: {trade_log_path}")
    print(f"Saved performance table to: {performance_table_path}")
    print(f"Saved equity plot to: {equity_plot_path}")
    print(f"Saved drawdown plot to: {drawdown_plot_path}")

if __name__ == "__main__":
    main()
