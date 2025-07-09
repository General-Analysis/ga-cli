import typer
from rich import print
from pathlib import Path
from typing import Annotated
import httpx
import shutil, json
from .config import CONFIG, API_URL, API_KEY_FILE

app = typer.Typer()

@app.command()
def test():
    print(f"Hello from {__name__}")
    
@app.command()
def login(api_key: Annotated[str, typer.Option(prompt=True)]):
    # add api-key
    API_KEY_FILE.write_text(api_key)

@app.command()
def guard_text(text: str):
    if not API_KEY_FILE.exists():
        raise FileNotFoundError("API key not set. Run `ga login` to set an API key.")
    api_key = API_KEY_FILE.read_text()
    print(f"Using api key: {api_key[:8]}...")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = httpx.post(API_URL + "/guard", json={"text": text, "policy_name": "@ga/default"}, headers=headers)
    print(response.url)
    response.raise_for_status()
    print(response.json())

@app.command()
def wrap_mcp_config(config_file: Path):
    assert config_file.suffix == ".json", "Not a json config file!"

    data: dict[str, str | dict] = json.loads(config_file.read_text())
    shutil.move(config_file, config_file.with_stem(config_file.stem + "_bak"))

    # do a bunch of stuff
    raise NotImplementedError()

def main():
    app()
