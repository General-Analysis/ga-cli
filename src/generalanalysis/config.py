from pathlib import Path
from typing import Any

API_URL = "https://api.generalanalysis.com"
# API_URL = "http://localhost:8000"
CONFIG_DIR = Path.home() / ".config" / "ga"
API_KEY_FILE = CONFIG_DIR / "api_key"
TOKEN_FILE = CONFIG_DIR / "token"

