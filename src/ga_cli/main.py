import typer
from rich import print
from pathlib import Path
import tomlkit
from typing import Annotated
import httpx
from .config import get_config, update_config, CONFIG_FILE

app = typer.Typer()

@app.command()
def test():
    print(f"Hello from {__name__}")
    
@app.command()
def login(api_key: Annotated[str, typer.Option(prompt=True)]):
    # add api-key
    update_config("api_key", api_key)

@app.command()
def guard_text():
    config = get_config()
    if "api_key" not in config:
        raise KeyError(f"No API Key configured. Edit {CONFIG_FILE} or run `ga login`")
    print(f"Using api key: {config["api_key"][:5]}...")
    print("This is supposed to look for mcp client (cursor, claude desktop) configs and scan tool descriptions for vulnerabilities. We need to first implement a server endpoint to hide the pipeline config and sys prompt")

def main():
    app()
