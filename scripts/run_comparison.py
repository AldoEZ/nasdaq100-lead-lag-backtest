import sys
from datetime import date

import pandas as pd
import polars as pl

from nasdaq_lead_lag.analytics.drawdown import calculate_drawdown
from nasdaq_lead_lag.analytics.metrics import calculate_performance_metrics
from nasdaq_lead_lag.analytics.performance_table import build_performance_table
from nasdaq_lead_lag.benchmark.qqq import build_qqq_benchmark_for_period, to_daily_equity
from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.reporting.exports import export_csv
from nasdaq_lead_lag.reporting.plots import plot_drawdown_curves, plot_equity_curves

def parse_date_range() -> tuple[date, date]:
    if len(sys.argv) < 3:
        raise ValueError(
            "Missing date range. Usage: python scripts/run_comparison.py YYYY-MM-DD YYYY-MM-DD"
        )
    
    start_date = date.fromisoformat(sys.argv[1])
    end_date = date.fromisoformat(sys.argv[2])
    
    if start_date > end_date:
        raise ValueError("start_date cannot be greater than end_date.")
    
    return start_date, end_date

def load_strategy_daily_equity(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    
    required_columns = {
        "trading_date",
        "date",
        "strategy_equity",
    }
    
    missing_columns = required_columns - set(data.columns)
    
    if missing_columns:
        raise ValueError(f"Missing strategy daily equity columns: {sorted(missing_columns)}")
    
    data["trading_date"] = pd.to_datetime(data["trading_date"]).dt.date
    data["date"] = pd.to_datetime(data["date"])
    
    return data.sort_values("trading_date").reset_index(drop=True)

def filter_strategy_period(
    strategy_daily: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    filtered = strategy_daily[
        (strategy_daily["trading_date"] >= start_date)
        & (strategy_daily["trading_date"] <= end_date)
    ].copy()
    
    if filtered.empty:
        raise ValueError("No strategy daily equity found for selected period.")
    
    return filtered.sort_values("trading_date").reset_index(drop=True)

def recompute_returns_from_initial_capital(
    data: pd.DataFrame,
    equity_col: str,
    return_col: str,
    initial_capital: float,
) -> pd.DataFrame:
    data = data.copy()
    
    data[return_col] = data[equity_col].pct_change()
    
    data.loc[data.index[0], return_col] = (
        data.loc[data.index[0], equity_col] / initial_capital - 1.0
    )
    
    return data

def build_combined_equity(
    strategy_daily: pd.DataFrame,
    benchmark_daily: pd.DataFrame,
    initial_capital: float,
) -> pd.DataFrame:
    benchmark_pd = benchmark_daily.to_pandas()
    benchmark_pd["trading_date"] = pd.to_datetime(benchmark_pd["trading_date"]).dt.date
    benchmark_pd["date"] = pd.to_datetime(benchmark_pd["date"])
    
    strategy = strategy_daily[
        [
            "trading_date",
            "date",
            "strategy_equity",
        ]
    ].copy()
    
    benchmark = benchmark_pd[
        [
            "trading_date",
            "benchmark_equity",
        ]
    ].copy()
    
    combined = strategy.merge(
        benchmark,
        on="trading_date",
        how="inner",
    ).sort_values("trading_date")
    
    if combined.empty:
        raise ValueError("No overlapping trading dates between strategy and benchmark.")
    
    combined = recompute_returns_from_initial_capital(
        combined,
        equity_col="strategy_equity",
        return_col="strategy_return",
        initial_capital=initial_capital,
    )
    
    combined = recompute_returns_from_initial_capital(
        combined,
        equity_col="benchmark_equity",
        return_col="benchmark_return",
        initial_capital=initial_capital,
    )
    
    return combined.reset_index(drop=True)

def build_drawdown_comparison(combined_equity: pd.DataFrame) -> pd.DataFrame:
    strategy_data = pl.from_pandas(
        combined_equity[
            [
                "date",
                "strategy_equity",
            ]
        ]
    )
    
    benchmark_data = pl.from_pandas(
        combined_equity[
            [
                "date",
                "benchmark_equity",
            ]
        ]
    )
    
    strategy_drawdown = calculate_drawdown(
        strategy_data,
        equity_col="strategy_equity",
    ).to_pandas()[["date", "drawdown"]]
    
    benchmark_drawdown = calculate_drawdown(
        benchmark_data,
        equity_col="benchmark_equity",
    ).to_pandas()[["date", "drawdown"]]
    
    strategy_drawdown = strategy_drawdown.rename(
        columns={
            "drawdown": "strategy_drawdown",
        }
    )
    
    benchmark_drawdown = benchmark_drawdown.rename(
        columns={
            "drawdown": "benchmark_drawdown",
        }
    )
    
    return strategy_drawdown.merge(
        benchmark_drawdown,
        on="date",
        how="inner",
    )

def main() -> None:
    config = load_config()
    start_date, end_date = parse_date_range()
    
    print(f"Running Strategy vs QQQ comparison from {start_date} to {end_date}")
    
    strategy_daily_path = config.data.output_dir / "equity_curves" / "strategy_daily_equity.csv"
    
    strategy_daily = load_strategy_daily_equity(str(strategy_daily_path))
    
    strategy_period = filter_strategy_period(
        strategy_daily=strategy_daily,
        start_date=start_date,
        end_date=end_date,
    )
    
    qqq_intraday = build_qqq_benchmark_for_period(
        path=config.data.qqq_path,
        start_date=start_date,
        end_date=end_date,
        initial_capital=config.backtest.initial_capital,
        market_open=config.backtest.market_open,
        market_close=config.backtest.market_close,
    )
    
    qqq_daily = to_daily_equity(
        qqq_intraday,
        date_col="date",
        equity_col="benchmark_equity",
        return_col="benchmark_return",
    )
    
    combined_equity = build_combined_equity(
        strategy_daily=strategy_period,
        benchmark_daily=qqq_daily,
        initial_capital=config.backtest.initial_capital,
    )
    
    combined_equity_path = (
        config.data.output_dir / "equity_curves" / "strategy_vs_qqq_equity.csv"
    )
    
    export_csv(combined_equity, combined_equity_path)
    
    strategy_metrics = calculate_performance_metrics(
        pl.from_pandas(
            combined_equity[
                [
                    "date",
                    "strategy_equity",
                    "strategy_return",
                ]
            ]
        ),
        date_col="date",
        equity_col="strategy_equity",
        return_col="strategy_return",
        periods_per_year=252,
        bar_freq="D",
    )
    
    benchmark_metrics = calculate_performance_metrics(
        pl.from_pandas(
            combined_equity[
                [
                    "date",
                    "benchmark_equity",
                    "benchmark_return",
                ]
            ]
        ),
        date_col="date",
        equity_col="benchmark_equity",
        return_col="benchmark_return",
        periods_per_year=252,
        bar_freq="D",
    )
    
    performance_table = build_performance_table(
        {
            "Strategy": strategy_metrics,
            "QQQ Buy & Hold": benchmark_metrics,
        }
    )
    
    performance_table_path = (
        config.data.output_dir / "performance" / "strategy_vs_qqq_performance_table.csv"
    )
    
    export_csv(
        performance_table.rename_axis("metric").reset_index(),
        performance_table_path,
    )
    
    drawdown_comparison = build_drawdown_comparison(combined_equity)
    
    drawdown_path = (
        config.data.output_dir / "equity_curves" / "strategy_vs_qqq_drawdown.csv"
    )
    
    export_csv(drawdown_comparison, drawdown_path)
    
    equity_plot_path = (
        config.data.output_dir / "plots" / "strategy_vs_qqq_equity_log.png"
    )
    
    plot_equity_curves(
        data=combined_equity,
        date_col="date",
        strategy_col="strategy_equity",
        benchmark_col="benchmark_equity",
        output_path=equity_plot_path,
    )
    
    drawdown_plot_path = (
        config.data.output_dir / "plots" / "strategy_vs_qqq_drawdown.png"
    )
    
    plot_drawdown_curves(
        data=drawdown_comparison,
        date_col="date",
        strategy_drawdown_col="strategy_drawdown",
        benchmark_drawdown_col="benchmark_drawdown",
        output_path=drawdown_plot_path,
    )
    
    strategy_final = float(combined_equity["strategy_equity"].iloc[-1])
    benchmark_final = float(combined_equity["benchmark_equity"].iloc[-1])
    
    print("Comparison completed successfully.")
    print(f"Strategy final equity: {strategy_final:,.2f}")
    print(f"QQQ final equity: {benchmark_final:,.2f}")
    print(f"Strategy total return: {strategy_final / config.backtest.initial_capital - 1.0:.4%}")
    print(f"QQQ total return: {benchmark_final / config.backtest.initial_capital - 1.0:.4%}")
    print(f"Saved combined equity to: {combined_equity_path}")
    print(f"Saved drawdown comparison to: {drawdown_path}")
    print(f"Saved performance table to: {performance_table_path}")
    print(f"Saved equity plot to: {equity_plot_path}")
    print(f"Saved drawdown plot to: {drawdown_plot_path}")

if __name__ == "__main__":
    main()
