from nasdaq_lead_lag.backtest.position import Position

class Portfolio:
    def __init__(self, initial_capital: float) -> None:
        self.cash = initial_capital
        self.open_positions: list[Position] = []
    
    def has_open_position(self, follower: str) -> bool:
        return any(position.follower == follower for position in self.open_positions)
    
    def add_position(self, position: Position) -> None:
        self.open_positions.append(position)
    
    def remove_position(self, position: Position) -> None:
        self.open_positions.remove(position)
