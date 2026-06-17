from typing import Any

from nasdaq_lead_lag.backtest.costs import calculate_transaction_cost
from nasdaq_lead_lag.backtest.execution import calculate_gross_pnl, calculate_pnl_pct
from nasdaq_lead_lag.backtest.position import Position
from nasdaq_lead_lag.backtest.trade_log import Trade

class Portfolio:
    def __init__(self, initial_capital: float) -> None:
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive.")
        
        self.cash = initial_capital
        self.open_positions: dict[str, Position] = {}
    
    def has_open_position(self, follower: str) -> bool:
        return follower in self.open_positions
    
    def open_position(self, position: Position) -> None:
        if self.has_open_position(position.follower):
            raise ValueError(f"Position already open for follower: {position.follower}")
        
        self.cash -= position.entry_transaction_cost
        self.open_positions[position.follower] = position
    
    def close_position(
        self,
        follower: str,
        exit_time: Any,
        exit_price: float,
        exit_reason: str,
        cost_per_share: float,
    ) -> Trade:
        if follower not in self.open_positions:
            raise ValueError(f"No open position found for follower: {follower}")
        
        position = self.open_positions[follower]
        
        exit_transaction_cost = calculate_transaction_cost(
            quantity=position.quantity,
            cost_per_share=cost_per_share,
        )
        
        gross_pnl = calculate_gross_pnl(
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
        )
        
        transaction_costs = position.entry_transaction_cost + exit_transaction_cost
        net_pnl = gross_pnl - transaction_costs
        pnl_pct = calculate_pnl_pct(net_pnl, position.notional)
        
        self.cash += gross_pnl - exit_transaction_cost
        
        del self.open_positions[follower]
        
        return Trade(
            entry_time=position.entry_time,
            exit_time=exit_time,
            leader=position.leader,
            follower=position.follower,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            notional=position.notional,
            gross_pnl=gross_pnl,
            transaction_costs=transaction_costs,
            net_pnl=net_pnl,
            pnl_pct=pnl_pct,
            entry_reason=position.entry_reason,
            exit_reason=exit_reason,
            correlation=position.correlation,
            sector=position.sector,
        )
    
    def mark_to_market(self, latest_prices: dict[str, float]) -> float:
        equity = self.cash
        
        for position in self.open_positions.values():
            current_price = latest_prices.get(position.follower)
            
            if current_price is None:
                continue
            
            unrealized_pnl = calculate_gross_pnl(
                side=position.side,
                entry_price=position.entry_price,
                exit_price=current_price,
                quantity=position.quantity,
            )
            
            equity += unrealized_pnl
        
        return equity
