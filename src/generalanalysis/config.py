from pathlib import Path
import tomllib
from typing import Any

API_URL = "https://api.generalanalysis.com"
# API_URL = "http://localhost:8000"
CONFIG_DIR = Path.home() / ".config" / "ga"
CONFIG_FILE = CONFIG_DIR / "config.toml"
API_KEY_FILE = CONFIG_DIR / "api_key"
TOKEN_FILE = CONFIG_DIR / "token"

# load config
CONFIG: dict[str, Any] = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "rb") as f:
        CONFIG = tomllib.load(f)
