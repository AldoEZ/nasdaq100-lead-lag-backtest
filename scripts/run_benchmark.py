from nasdaq_lead_lag.analytics.drawdown import calculate_drawdown
from nasdaq_lead_lag.analytics.metrics import calculate_performance_metrics
from nasdaq_lead_lag.analytics.performance_table import build_performance_table
from nasdaq_lead_lag.benchmark.qqq import build_qqq_benchmark, to_daily_equity
from nasdaq_lead_lag.config import load_config
from nasdaq_lead_lag.reporting.exports import export_csv
from nasdaq_lead_lag.reporting.plots import plot_drawdown_curve, plot_single_equity_curve

def main() -> None:
    config = load_config()
    
    output_dir = config.data.output_dir
    
    print("Building QQQ buy-and-hold benchmark...")
    
    benchmark_equity = build_qqq_benchmark(
        path=config.data.qqq_path,
        initial_capital=config.backtest.initial_capital,
        market_open=config.backtest.market_open,
        market_close=config.backtest.market_close,
    )
    
    benchmark_equity_export = benchmark_equity.select(
        [
            "date",
            "symbol",
            "close",
            "benchmark_equity",
            "benchmark_return",
        ]
    )
    
    equity_curve_path = output_dir / "equity_curves" / "qqq_benchmark_equity.csv"
    
    export_csv(
        benchmark_equity_export.to_pandas(),
        equity_curve_path,
    )
    
    print(f"Saved benchmark equity curve to: {equity_curve_path}")
    
    daily_benchmark_equity = to_daily_equity(
        benchmark_equity,
        date_col="date",
        equity_col="benchmark_equity",
        return_col="benchmark_return",
    )
    
    daily_drawdown = calculate_drawdown(
        daily_benchmark_equity,
        equity_col="benchmark_equity",
    )
    
    metrics = calculate_performance_metrics(
        daily_benchmark_equity,
        date_col="date",
        equity_col="benchmark_equity",
        return_col="benchmark_return",
        periods_per_year=252,
        bar_freq="D",
    )
    
    performance_table = build_performance_table(
        {
            "QQQ Buy & Hold": metrics,
        }
    )
    
    performance_table_path = output_dir / "performance" / "qqq_performance_table.csv"
    
    export_csv(
        performance_table.rename_axis("metric").reset_index(),
        performance_table_path,
    )
    
    print(f"Saved benchmark performance table to: {performance_table_path}")
    
    equity_plot_path = output_dir / "plots" / "qqq_equity_curve_log.png"
    
    plot_single_equity_curve(
        data=benchmark_equity.to_pandas(),
        date_col="date",
        equity_col="benchmark_equity",
        label="QQQ Buy & Hold",
        output_path=equity_plot_path,
        log_scale=True,
    )
    
    print(f"Saved benchmark equity plot to: {equity_plot_path}")
    
    drawdown_plot_path = output_dir / "plots" / "qqq_drawdown.png"
    
    plot_drawdown_curve(
        data=daily_drawdown.to_pandas(),
        date_col="date",
        drawdown_col="drawdown",
        label="QQQ Buy & Hold",
        output_path=drawdown_plot_path,
    )
    
    print(f"Saved benchmark drawdown plot to: {drawdown_plot_path}")
    
    print("QQQ benchmark completed successfully.")

if __name__ == "__main__":
    main()
