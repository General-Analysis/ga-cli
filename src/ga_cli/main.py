import typer
from rich import print
from pathlib import Path
from typing import Annotated
import httpx
import shutil, json
from typing import Any
import time
from .config import CONFIG, API_URL, CONFIG_DIR, API_KEY_FILE, TOKEN_FILE

app = typer.Typer()

@app.command()
def test():
    print(f"Hello from {__name__}")
    
@app.command()
def signup():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    resp = httpx.get(API_URL + "/auth/device")
    resp.raise_for_status()
    data = resp.json()
    print("Open in browser:", data["verification_url"])
    device_code = data["device_code"]

    code = 202
    while code == 202:
        time.sleep(1)
        resp = httpx.get(API_URL + f"/auth/device/{device_code}")
        resp.raise_for_status()
        code = resp.status_code
    if code == 200:
        token = resp.json()
        # cache token
        TOKEN_FILE.write_text(token)

    # make project
    project_name = "ga-cli"
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.post(API_URL + "/projects", json={"name": project_name}, headers=headers)
    resp.raise_for_status()
    
    # make apikey and cache
    resp = httpx.post(API_URL + "/api-keys/new", json={"project_name": project_name}, headers=headers)
    resp.raise_for_status()

    api_key = resp.json()
    API_KEY_FILE.write_text(api_key)
    
@app.command()
def login(api_key: Annotated[str, typer.Option(prompt=True)]):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
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
    data: dict[str, Any] = json.loads(config_file.read_text())
    encoded_args: list[str] = []
    for name, server_config in data["mcpServers"].items():
        server_config["name"] = name
        encoded = json.dumps(server_config, separators=(',', ':'))
        encoded_args.append(encoded)

    new_config = {
        "command": "npx",
        "args": [
            "-y",
            "@"
        ]
    }
    
    # shutil.move(config_file, config_file.with_stem(config_file.stem + "_bak"))

    

    # do a bunch of stuff
    # raise NotImplementedError()

def main():
    app()
