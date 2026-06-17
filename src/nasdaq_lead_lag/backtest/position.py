from dataclasses import dataclass
from typing import Any, Literal

Side = Literal["LONG", "SHORT"]

@dataclass
class Position:
    leader: str
    follower: str
    side: Side
    entry_time: Any
    entry_price: float
    quantity: int
    notional: float
    entry_transaction_cost: float
    entry_reason: str
    correlation: float
    sector: str
    leader_entry_price: float
    leader_base_sma_entry: float
    follower_base_sma_entry: float
