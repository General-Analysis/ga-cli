from pathlib import Path
import tomlkit
from typing import Any

CONFIG_FILE = Path.home() / ".config" / "ga" / "config.toml"

def get_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = tomlkit.load(f)
    else:
        config = tomlkit.document()
    return config

def update_config(key: str, value: Any):
    config = get_config()
    config[key] = value
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(tomlkit.dumps(config))

