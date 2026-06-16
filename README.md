# Nasdaq-100 Lead-Lag Backtest

Intraday lead-lag backtest on Nasdaq-100 equities using sector-based rolling correlations, SMA signals, transaction costs, trade logs, and QQQ benchmark comparison.

## Objective

The objective of this project is to implement and evaluate an intraday systematic trading strategy on Nasdaq-100 stocks and compare its performance against a buy-and-hold QQQ benchmark.

## Strategy Summary

The strategy selects highly correlated stock pairs within the same sector or industry group. For each selected pair, the stock with the larger market capitalization is defined as the leader and the other stock as the follower.

The follower is traded intraday based on the relationship between leader/follower prices and their 15-minute simple moving averages adjusted by predefined edge factors.

## Main Features

- Nasdaq-100 intraday data handling
- Sector-based pair formation
- Rolling 60-day correlation ranking
- Leader/follower assignment by market capitalization
- 15-minute SMA signal generation
- Long and short trade simulation
- Transaction cost modeling
- Trade log generation
- Equity curve construction
- QQQ benchmark comparison
- Performance table and drawdown analysis

## Data

Raw data files are expected locally in:

```text
data/raw/
