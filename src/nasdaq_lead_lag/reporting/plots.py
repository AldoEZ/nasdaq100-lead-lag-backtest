from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

def plot_single_equity_curve(
    data: pd.DataFrame,
    date_col: str,
    equity_col: str,
    label: str,
    output_path: str | Path,
    title: str = "Equity Curve",
    log_scale: bool = True,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    plt.plot(data[date_col], data[equity_col], label=label)
    
    if log_scale:
        plt.yscale("log")
    
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_drawdown_curve(
    data: pd.DataFrame,
    date_col: str,
    drawdown_col: str,
    label: str,
    output_path: str | Path,
    title: str = "Drawdown",
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    plt.plot(data[date_col], data[drawdown_col], label=label)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_equity_curves(
    data: pd.DataFrame,
    date_col: str,
    strategy_col: str,
    benchmark_col: str,
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    plt.plot(data[date_col], data[strategy_col], label="Strategy")
    plt.plot(data[date_col], data[benchmark_col], label="QQQ Buy & Hold")
    plt.yscale("log")
    plt.title("Strategy vs QQQ Equity Curve - Log Scale")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_drawdown_curves(
    data: pd.DataFrame,
    date_col: str,
    strategy_drawdown_col: str,
    benchmark_drawdown_col: str,
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    plt.plot(data[date_col], data[strategy_drawdown_col], label="Strategy")
    plt.plot(data[date_col], data[benchmark_drawdown_col], label="QQQ Buy & Hold")
    plt.title("Strategy vs QQQ Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
