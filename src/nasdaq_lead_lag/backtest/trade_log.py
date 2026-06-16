from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trade:
    entry_time: datetime
    exit_time: datetime
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
