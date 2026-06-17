import math

def calculate_quantity(notional: float, price: float) -> int:
    if notional <= 0:
        raise ValueError("Notional must be positive.")
    
    if price <= 0:
        raise ValueError("Price must be positive.")
    
    return math.floor(notional / price)

def calculate_gross_pnl(
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: int,
) -> float:
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    
    if entry_price <= 0 or exit_price <= 0:
        raise ValueError("Prices must be positive.")
    
    if side == "LONG":
        return (exit_price - entry_price) * quantity
    
    if side == "SHORT":
        return (entry_price - exit_price) * quantity
    
    raise ValueError(f"Unsupported side: {side}")

def calculate_pnl_pct(net_pnl: float, notional: float) -> float:
    if notional <= 0:
        raise ValueError("Notional must be positive.")
    
    return net_pnl / notional
