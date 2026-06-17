def calculate_transaction_cost(quantity: int, cost_per_share: float) -> float:
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    
    if cost_per_share < 0:
        raise ValueError("Cost per share cannot be negative.")
    
    return quantity * cost_per_share
