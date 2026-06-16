import numpy as np
import polars as pl

def total_return(equity: pl.Series) -> float:
    return float(equity[-1] / equity[0] - 1.0)

def annualized_volatility(returns: pl.Series, periods_per_year: int) -> float:
    return float(np.std(returns.to_numpy(), ddof=1) * np.sqrt(periods_per_year))

def sharpe_ratio(returns: pl.Series, periods_per_year: int, risk_free_rate: float = 0.0) -> float:
    returns_np = returns.to_numpy()
    
    if returns_np.std(ddof=1) == 0:
        return 0.0
    
    excess_return = returns_np.mean() - (risk_free_rate / periods_per_year)
    
    return float(excess_return / returns_np.std(ddof=1) * np.sqrt(periods_per_year))
