# Backtest Methodology

This project implements an intraday lead-lag strategy on Nasdaq-100 equities.

The strategy forms same-sector pairs using rolling 60-day correlations, selects the top 50 pairs, assigns the leader as the stock with the larger market capitalization, and trades the follower based on intraday SMA thresholds.

The strategy is compared against a buy-and-hold QQQ benchmark.
