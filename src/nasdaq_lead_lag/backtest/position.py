from dataclasses import dataclass
from datetime import datetime

@dataclass
class Position:
    leader: str
    follower: str
    side: str
    entry_time: datetime
    entry_price: float
    quantity: int
    notional: float
    entry_transaction_cost: float
    entry_reason: str
    correlation: float
    sector: str
