from dataclasses import dataclass
from datetime import time

import pandas as pd
import polars as pl

from nasdaq_lead_lag.backtest.costs import calculate_transaction_cost
from nasdaq_lead_lag.backtest.execution import calculate_quantity
from nasdaq_lead_lag.backtest.portfolio import Portfolio
from nasdaq_lead_lag.backtest.position import Position
from nasdaq_lead_lag.backtest.trade_log import Trade, trades_to_dataframe

@dataclass
class BacktestDayResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame

def build_pair_market_data(
    top_pairs: pd.DataFrame,
    intraday_data: pl.DataFrame,
    market_open: time,
    force_exit_time: time,
    leader_edge: float,
    follower_edge: float,
    symbol_col: str = "symbol",
    price_col: str = "close",
    sma_col: str = "sma_15",
) -> pd.DataFrame:
    if top_pairs.empty or intraday_data.is_empty():
        return pd.DataFrame()
    
    prices = intraday_data.to_pandas()
    rows: list[pd.DataFrame] = []
    
    for pair in top_pairs.itertuples(index=False):
        leader = pair.leader
        follower = pair.follower
        
        leader_prices = prices.loc[
            prices[symbol_col] == leader,
            ["date", "trading_date", "trading_time", price_col, sma_col],
        ].rename(
            columns={
                price_col: "leader_price",
                sma_col: "leader_base_sma",
            }
        )
        
        follower_prices = prices.loc[
            prices[symbol_col] == follower,
            ["date", "trading_date", "trading_time", price_col, sma_col],
        ].rename(
            columns={
                price_col: "follower_price",
                sma_col: "follower_base_sma",
            }
        )
        
        merged = leader_prices.merge(
            follower_prices,
            on=["date", "trading_date", "trading_time"],
            how="inner",
        )
        
        if merged.empty:
            continue
        
        merged = merged[
            (merged["trading_time"] >= market_open)
            & (merged["trading_time"] <= force_exit_time)
        ].copy()
        
        merged = merged.dropna(
            subset=[
                "leader_price",
                "follower_price",
                "leader_base_sma",
                "follower_base_sma",
            ]
        )
        
        if merged.empty:
            continue
        
        merged["sector"] = pair.sector
        merged["leader"] = leader
        merged["follower"] = follower
        merged["correlation"] = pair.correlation
        
        merged["leader_long_sma"] = merged["leader_base_sma"] * (1.0 + leader_edge)
        merged["follower_long_sma"] = merged["follower_base_sma"] * (1.0 + follower_edge)
        merged["leader_short_sma"] = merged["leader_base_sma"] * (1.0 - leader_edge)
        merged["follower_short_sma"] = merged["follower_base_sma"] * (1.0 - follower_edge)
        
        rows.append(merged)
    
    if not rows:
        return pd.DataFrame()
    
    return pd.concat(rows, ignore_index=True).sort_values(
        ["date", "follower", "correlation"],
        ascending=[True, True, False],
    )

def build_entry_candidates(
    minute_rows: pd.DataFrame,
    min_price: float,
) -> pd.DataFrame:
    if minute_rows.empty:
        return pd.DataFrame()
    
    rows: list[dict] = []
    
    for _, row in minute_rows.iterrows():
        long_condition = (
            row["leader_price"] > row["leader_long_sma"]
            and row["follower_price"] < row["follower_long_sma"]
            and row["follower_price"] > min_price
        )
        
        short_condition = (
            row["leader_price"] < row["leader_short_sma"]
            and row["follower_price"] < row["follower_short_sma"]
            and row["follower_price"] > min_price
        )
        
        if long_condition:
            signal = row.to_dict()
            signal["side"] = "LONG"
            signal["entry_reason"] = "leader_above_long_sma_and_follower_below_long_sma"
            rows.append(signal)
        
        if short_condition:
            signal = row.to_dict()
            signal["side"] = "SHORT"
            signal["entry_reason"] = "leader_below_short_sma_and_follower_below_short_sma"
            rows.append(signal)
    
    if not rows:
        return pd.DataFrame()
    
    candidates = pd.DataFrame(rows)
    
    side_count = candidates.groupby(["date", "follower"])["side"].transform("nunique")
    candidates = candidates[side_count == 1]
    
    candidates = candidates.sort_values(
        ["date", "follower", "correlation"],
        ascending=[True, True, False],
    )
    
    candidates = candidates.drop_duplicates(
        subset=["date", "follower"],
        keep="first",
    )
    
    return candidates.reset_index(drop=True)

def should_exit_position(position: Position, row: pd.Series, force_exit_time: time) -> str | None:
    current_time = row["trading_time"]
    
    if current_time >= force_exit_time:
        return "end_of_day_exit"
    
    if position.side == "LONG" and row["leader_price"] < row["leader_base_sma"]:
        return "leader_below_base_sma"
    
    if position.side == "SHORT" and row["leader_price"] > row["leader_base_sma"]:
        return "leader_above_base_sma"
    
    return None

def run_backtest_day(
    top_pairs: pd.DataFrame,
    intraday_data: pl.DataFrame,
    initial_capital: float,
    notional_per_trade: float,
    transaction_cost_per_share: float,
    market_open: time,
    force_exit_time: time,
    leader_edge: float,
    follower_edge: float,
    min_price: float,
    symbol_col: str = "symbol",
    price_col: str = "close",
    sma_col: str = "sma_15",
) -> BacktestDayResult:
    pair_market_data = build_pair_market_data(
        top_pairs=top_pairs,
        intraday_data=intraday_data,
        market_open=market_open,
        force_exit_time=force_exit_time,
        leader_edge=leader_edge,
        follower_edge=follower_edge,
        symbol_col=symbol_col,
        price_col=price_col,
        sma_col=sma_col,
    )
    
    portfolio = Portfolio(initial_capital=initial_capital)
    trades: list[Trade] = []
    equity_rows: list[dict] = []
    
    if pair_market_data.empty:
        return BacktestDayResult(
            trades=trades_to_dataframe(trades),
            equity_curve=pd.DataFrame(columns=["date", "equity", "return"]),
        )
    
    latest_prices: dict[str, float] = {}
    last_snapshot_by_pair: dict[tuple[str, str], pd.Series] = {}
    
    unique_times = (
        pair_market_data[["date", "trading_time"]]
        .drop_duplicates()
        .sort_values("date")
    )
    
    previous_equity = initial_capital
    
    for time_row in unique_times.itertuples(index=False):
        current_timestamp = time_row.date
        current_time = time_row.trading_time
        
        minute_rows = pair_market_data[pair_market_data["date"] == current_timestamp]
        
        for _, row in minute_rows.iterrows():
            latest_prices[row["follower"]] = float(row["follower_price"])
            last_snapshot_by_pair[(row["leader"], row["follower"])] = row
        
        closed_followers_this_minute: set[str] = set()
        
        for follower, position in list(portfolio.open_positions.items()):
            position_rows = minute_rows[
                (minute_rows["leader"] == position.leader)
                & (minute_rows["follower"] == position.follower)
            ]
            
            if position_rows.empty:
                row = last_snapshot_by_pair.get((position.leader, position.follower))
            else:
                row = position_rows.iloc[0]
            
            if row is None:
                continue
            
            exit_reason = should_exit_position(
                position=position,
                row=row,
                force_exit_time=force_exit_time,
            )
            
            if exit_reason is None:
                continue
            
            trade = portfolio.close_position(
                follower=follower,
                exit_time=current_timestamp,
                exit_price=float(row["follower_price"]),
                exit_reason=exit_reason,
                cost_per_share=transaction_cost_per_share,
            )
            
            trades.append(trade)
            closed_followers_this_minute.add(follower)
        
        if current_time < force_exit_time:
            entry_candidates = build_entry_candidates(
                minute_rows=minute_rows,
                min_price=min_price,
            )
            
            for _, signal in entry_candidates.iterrows():
                follower = signal["follower"]
                
                if portfolio.has_open_position(follower):
                    continue
                
                if follower in closed_followers_this_minute:
                    continue
                
                entry_price = float(signal["follower_price"])
                quantity = calculate_quantity(notional_per_trade, entry_price)
                
                if quantity <= 0:
                    continue
                
                entry_transaction_cost = calculate_transaction_cost(
                    quantity=quantity,
                    cost_per_share=transaction_cost_per_share,
                )
                
                position = Position(
                    leader=signal["leader"],
                    follower=follower,
                    side=signal["side"],
                    entry_time=current_timestamp,
                    entry_price=entry_price,
                    quantity=quantity,
                    notional=notional_per_trade,
                    entry_transaction_cost=entry_transaction_cost,
                    entry_reason=signal["entry_reason"],
                    correlation=float(signal["correlation"]),
                    sector=signal["sector"],
                    leader_entry_price=float(signal["leader_price"]),
                    leader_base_sma_entry=float(signal["leader_base_sma"]),
                    follower_base_sma_entry=float(signal["follower_base_sma"]),
                )
                
                portfolio.open_position(position)
        
        equity = portfolio.mark_to_market(latest_prices)
        period_return = equity / previous_equity - 1.0 if previous_equity > 0 else 0.0
        
        equity_rows.append(
            {
                "date": current_timestamp,
                "equity": equity,
                "return": period_return,
                "open_positions": len(portfolio.open_positions),
            }
        )
        
        previous_equity = equity
    
    for follower, position in list(portfolio.open_positions.items()):
        row = last_snapshot_by_pair.get((position.leader, position.follower))
        
        if row is None:
            continue
        
        trade = portfolio.close_position(
            follower=follower,
            exit_time=row["date"],
            exit_price=float(row["follower_price"]),
            exit_reason="forced_close_last_available_price",
            cost_per_share=transaction_cost_per_share,
        )
        
        trades.append(trade)
    
    return BacktestDayResult(
        trades=trades_to_dataframe(trades),
        equity_curve=pd.DataFrame(equity_rows),
    )
