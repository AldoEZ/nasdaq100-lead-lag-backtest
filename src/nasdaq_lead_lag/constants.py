from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

REGULAR_MARKET_OPEN = "09:30"
REGULAR_MARKET_CLOSE = "16:00"
FORCE_EXIT_TIME = "15:55"