import math

def calculate_quantity(notional: float, price: float) -> int:
    if notional <= 0:
        raise ValueError("Notional must be positive.")
    
    if price <= 0:
        raise ValueError("Price must be positive.")
    
    return math.floor(notional / price)
