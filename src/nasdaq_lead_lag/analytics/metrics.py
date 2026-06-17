from datetime import date, datetime
from typing import Any

import numpy as np
import polars as pl

from nasdaq_lead_lag.analytics.drawdown import calculate_drawdown

def total_return(equity: pl.Series) -> float:
    return float(equity[-1] / equity[0] - 1.0)

def annualized_volatility(returns: pl.Series, periods_per_year: int) -> float:
    returns_np = returns.to_numpy()
    
    if len(returns_np) < 2:
        return 0.0
    
    return float(np.std(returns_np, ddof=1) * np.sqrt(periods_per_year))

def sharpe_ratio(
    returns: pl.Series,
    periods_per_year: int,
    risk_free_rate: float = 0.0,
) -> float:
    returns_np = returns.to_numpy()
    
    if len(returns_np) < 2:
        return 0.0
    
    volatility = np.std(returns_np, ddof=1)
    
    if volatility == 0:
        return 0.0
    
    excess_return = returns_np.mean() - (risk_free_rate / periods_per_year)
    
    return float(excess_return / volatility * np.sqrt(periods_per_year))

def sortino_ratio(
    returns: pl.Series,
    periods_per_year: int,
    risk_free_rate: float = 0.0,
) -> float:
    returns_np = returns.to_numpy()
    
    if len(returns_np) < 2:
        return 0.0
    
    downside_returns = returns_np[returns_np < 0]
    
    if len(downside_returns) < 2:
        return 0.0
    
    downside_volatility = np.std(downside_returns, ddof=1)
    
    if downside_volatility == 0:
        return 0.0
    
    excess_return = returns_np.mean() - (risk_free_rate / periods_per_year)
    
    return float(excess_return / downside_volatility * np.sqrt(periods_per_year))

def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    
    raise TypeError(f"Unsupported date type: {type(value)}")

def calculate_cagr(data: pl.DataFrame, date_col: str, equity_col: str) -> float:
    start_equity = float(data[equity_col][0])
    end_equity = float(data[equity_col][-1])
    
    start_date = _to_datetime(data[date_col][0])
    end_date = _to_datetime(data[date_col][-1])
    
    days = (end_date - start_date).days
    
    if days <= 0 or start_equity <= 0:
        return 0.0
    
    years = days / 365.25
    
    return float((end_equity / start_equity) ** (1 / years) - 1.0)

def calculate_best_worst_rolling_return(
    data: pl.DataFrame,
    date_col: str,
    equity_col: str,
    window: int = 252,
) -> tuple[float, Any, float, Any]:
    if data.height <= window:
        return 0.0, None, 0.0, None
    
    equity = data[equity_col].to_numpy()
    dates = data[date_col].to_list()
    
    rolling_returns = equity[window:] / equity[:-window] - 1.0
    
    best_idx = int(np.argmax(rolling_returns))
    worst_idx = int(np.argmin(rolling_returns))
    
    best_return = float(rolling_returns[best_idx])
    worst_return = float(rolling_returns[worst_idx])
    
    best_date = dates[best_idx + window]
    worst_date = dates[worst_idx + window]
    
    return best_return, best_date, worst_return, worst_date

def calculate_max_drawdown_period(
    data: pl.DataFrame,
    date_col: str,
    equity_col: str,
) -> tuple[float, Any, Any]:
    drawdown_data = calculate_drawdown(data, equity_col)
    
    drawdowns = drawdown_data["drawdown"].to_numpy()
    equity = drawdown_data[equity_col].to_numpy()
    dates = drawdown_data[date_col].to_list()
    
    end_idx = int(np.argmin(drawdowns))
    max_drawdown = float(drawdowns[end_idx])
    
    equity_until_dd_end = equity[: end_idx + 1]
    peak_value = np.max(equity_until_dd_end)
    
    peak_indices = np.where(equity_until_dd_end == peak_value)[0]
    start_idx = int(peak_indices[-1])
    
    return max_drawdown, dates[start_idx], dates[end_idx]

def calculate_performance_metrics(
    data: pl.DataFrame,
    date_col: str,
    equity_col: str,
    return_col: str,
    periods_per_year: int = 252,
    bar_freq: str = "D",
) -> dict[str, Any]:
    if data.height < 2:
        raise ValueError("At least two rows are required to calculate performance metrics.")
    
    returns = data[return_col].drop_nulls()
    equity = data[equity_col]
    
    cagr = calculate_cagr(data, date_col, equity_col)
    ann_vol = annualized_volatility(returns, periods_per_year)
    sharpe = sharpe_ratio(returns, periods_per_year)
    sortino = sortino_ratio(returns, periods_per_year)
    
    max_drawdown, max_dd_start, max_dd_end = calculate_max_drawdown_period(
        data,
        date_col=date_col,
        equity_col=equity_col,
    )
    
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0.0
    
    drawdown_data = calculate_drawdown(data, equity_col)
    negative_drawdowns = drawdown_data.filter(pl.col("drawdown") < 0)["drawdown"]
    
    avg_max_dd = float(negative_drawdowns.mean()) if len(negative_drawdowns) > 0 else 0.0
    
    best_1y_return, best_1y_date, worst_1y_return, worst_1y_date = (
        calculate_best_worst_rolling_return(
            data,
            date_col=date_col,
            equity_col=equity_col,
            window=periods_per_year,
        )
    )
    
    return {
        "CAGR": cagr,
        "Ann_Vol": ann_vol,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Calmar": calmar,
        "Total_Return": total_return(equity),
        "Avg_Max_DD": avg_max_dd,
        "Max_Drawdown": max_drawdown,
        "Max_DD_Start": max_dd_start,
        "Max_DD_End": max_dd_end,
        "Best_1Y_Return": best_1y_return,
        "Best_1Y_Date": best_1y_date,
        "Worst_1Y_Return": worst_1y_return,
        "Worst_1Y_Date": worst_1y_date,
        "Bar_Freq": bar_freq,
        "Periods_Per_Year": periods_per_year,
    }
