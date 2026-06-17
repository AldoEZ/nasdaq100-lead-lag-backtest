from typing import Any

import pandas as pd

METRIC_ORDER = [
    "CAGR",
    "Ann_Vol",
    "Sharpe",
    "Sortino",
    "Calmar",
    "Total_Return",
    "Avg_Max_DD",
    "Max_Drawdown",
    "Max_DD_Start",
    "Max_DD_End",
    "Best_1Y_Return",
    "Best_1Y_Date",
    "Worst_1Y_Return",
    "Worst_1Y_Date",
    "Bar_Freq",
    "Periods_Per_Year",
]

def build_performance_table(metrics_by_name: dict[str, dict[str, Any]]) -> pd.DataFrame:
    table = pd.DataFrame(metrics_by_name)
    
    existing_metrics = [metric for metric in METRIC_ORDER if metric in table.index]
    
    return table.reindex(existing_metrics)
