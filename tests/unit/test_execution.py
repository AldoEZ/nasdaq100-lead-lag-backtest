import pytest

from nasdaq_lead_lag.backtest.execution import (
    calculate_gross_pnl,
    calculate_pnl_pct,
    calculate_quantity,
)

def test_calculate_quantity() -> None:
    assert calculate_quantity(notional=100_000, price=250) == 400

def test_calculate_long_gross_pnl() -> None:
    result = calculate_gross_pnl(
        side="LONG",
        entry_price=100,
        exit_price=110,
        quantity=10,
    )

    assert result == 100

def test_calculate_short_gross_pnl() -> None:
    result = calculate_gross_pnl(
        side="SHORT",
        entry_price=100,
        exit_price=90,
        quantity=10,
    )

    assert result == 100

def test_calculate_pnl_pct() -> None:
    assert calculate_pnl_pct(net_pnl=1_000, notional=100_000) == pytest.approx(0.01)
