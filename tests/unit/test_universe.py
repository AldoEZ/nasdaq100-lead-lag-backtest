from datetime import date

from nasdaq_lead_lag.research.universe import parse_period

def test_parse_period() -> None:
    start, end = parse_period("2021-01-01/2021-12-31")
    
    assert start == date(2021, 1, 1)
    assert end == date(2021, 12, 31)
