import pytest

from nasdaq_lead_lag.backtest.costs import calculate_transaction_cost

def test_calculate_transaction_cost() -> None:
    assert calculate_transaction_cost(quantity=100, cost_per_share=0.0035) == pytest.approx(0.35)