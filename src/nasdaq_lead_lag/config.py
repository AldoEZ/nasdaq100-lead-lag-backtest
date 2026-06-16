from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

import yaml

@dataclass(frozen=True)
class DataConfig:
    nasdaq_path: Path
    qqq_path: Path
    output_dir: Path
    date_column: str
    symbol_column: str
    price_column: str
    sector_column: str
    market_cap_column: str

@dataclass(frozen=True)
class StrategyConfig:
    correlation_window_days: int
    sma_window_minutes: int
    leader_edge: float
    follower_edge: float
    top_n_pairs: int
    min_price: float
    use_sector_column: str
    use_price_column: str
    allow_multiple_positions_same_follower: bool
    allow_long_and_short_same_follower_same_minute: bool

@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float
    notional_per_trade: float
    transaction_cost_per_share: float
    market_open: time
    market_close: time
    force_exit_time: time
    timestamp_assumption: str

@dataclass(frozen=True)
class AppConfig:
    data: DataConfig
    strategy: StrategyConfig
    backtest: BacktestConfig

def parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))

def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    
    if data is None:
        raise ValueError(f"Config file is empty: {path}")
    
    return data

def load_config(config_dir: str | Path = "configs") -> AppConfig:
    config_dir = Path(config_dir)
    
    data_raw = load_yaml(config_dir / "data.yaml")
    strategy_raw = load_yaml(config_dir / "strategy.yaml")
    backtest_raw = load_yaml(config_dir / "backtest.yaml")
    
    data_config = DataConfig(
        nasdaq_path=Path(data_raw["nasdaq_path"]),
        qqq_path=Path(data_raw["qqq_path"]),
        output_dir=Path(data_raw["output_dir"]),
        date_column=str(data_raw["date_column"]),
        symbol_column=str(data_raw["symbol_column"]),
        price_column=str(data_raw["price_column"]),
        sector_column=str(data_raw["sector_column"]),
        market_cap_column=str(data_raw["market_cap_column"]),
    )
    
    strategy_config = StrategyConfig(
        correlation_window_days=int(strategy_raw["correlation_window_days"]),
        sma_window_minutes=int(strategy_raw["sma_window_minutes"]),
        leader_edge=float(strategy_raw["leader_edge"]),
        follower_edge=float(strategy_raw["follower_edge"]),
        top_n_pairs=int(strategy_raw["top_n_pairs"]),
        min_price=float(strategy_raw["min_price"]),
        use_sector_column=str(strategy_raw["use_sector_column"]),
        use_price_column=str(strategy_raw["use_price_column"]),
        allow_multiple_positions_same_follower=bool(
            strategy_raw["allow_multiple_positions_same_follower"]
        ),
        allow_long_and_short_same_follower_same_minute=bool(
            strategy_raw["allow_long_and_short_same_follower_same_minute"]
        ),
    )
    
    backtest_config = BacktestConfig(
        initial_capital=float(backtest_raw["initial_capital"]),
        notional_per_trade=float(backtest_raw["notional_per_trade"]),
        transaction_cost_per_share=float(backtest_raw["transaction_cost_per_share"]),
        market_open=parse_time(backtest_raw["market_open"]),
        market_close=parse_time(backtest_raw["market_close"]),
        force_exit_time=parse_time(backtest_raw["force_exit_time"]),
        timestamp_assumption=str(backtest_raw["timestamp_assumption"]),
    )
    
    return AppConfig(
        data=data_config,
        strategy=strategy_config,
        backtest=backtest_config,
    )
