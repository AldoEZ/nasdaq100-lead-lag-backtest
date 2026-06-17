from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

@dataclass
class Trade:
    entry_time: Any
    exit_time: Any
    leader: str
    follower: str
    side: str
    entry_price: float
    exit_price: float
    quantity: int
    notional: float
    gross_pnl: float
    transaction_costs: float
    net_pnl: float
    pnl_pct: float
    entry_reason: str
    exit_reason: str
    correlation: float
    sector: str

def trades_to_dataframe(trades: list[Trade]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame(
            columns=[
                "entry_time",
                "exit_time",
                "leader",
                "follower",
                "side",
                "entry_price",
                "exit_price",
                "quantity",
                "notional",
                "gross_pnl",
                "transaction_costs",
                "net_pnl",
                "pnl_pct",
                "entry_reason",
                "exit_reason",
                "correlation",
                "sector",
            ]
        )
    
    return pd.DataFrame([asdict(trade) for trade in trades])
