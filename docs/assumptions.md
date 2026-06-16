# Backtest Assumptions

## Timestamp Handling

Although timestamps are displayed with a "Z" suffix, volume analysis around the market open shows that 09:30 corresponds to the U.S. regular market open. Therefore, timestamps are treated as New York exchange time and are not converted from UTC.

## Sector Classification

The dataset does not contain a column explicitly named `sector`. The `sic_description` column is used as the sector or industry grouping variable.

## Missing Sector Data

Tickers with missing `sic_description` are excluded from pair formation because the strategy requires pairs to be formed within the same sector group.

## Market Cap

The dataset provides a fixed `market_cap` per ticker. This value is used to define the leader and follower in each pair.

## Execution Price

The first implementation uses `close` as the signal and execution reference price.

## Transaction Costs

Transaction costs are modeled as 0.0035 USD per share per side.

## Position Sizing

Each position uses a fixed notional amount of 100,000 USD. Share quantity is rounded down to the nearest whole share.

## Overnight Risk

No overnight positions are allowed. All open positions are force-closed at 15:55.
