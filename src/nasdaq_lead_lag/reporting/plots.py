from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

def plot_equity_curves(
    data: pd.DataFrame,
    date_col: str,
    strategy_col: str,
    benchmark_col: str,
    output_path: str | Path,
) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(data[date_col], data[strategy_col], label="Strategy")
    plt.plot(data[date_col], data[benchmark_col], label="QQQ Buy & Hold")
    plt.yscale("log")
    plt.title("Equity Curve - Log Scale")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
