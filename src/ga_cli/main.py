import typer
# from rich import print
from pathlib import Path
from typing import Annotated
import httpx
import shutil, json
from typing import Any
import time
from .config import CONFIG, API_URL, CONFIG_DIR, API_KEY_FILE, TOKEN_FILE

app = typer.Typer()

@app.command()
def login():
    """
        Login to ga-cli.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # check for existing API Key
    if API_KEY_FILE.exists():
        cached_api_key = API_KEY_FILE.read_text()
        typer.confirm(f"Found cached GA API Key {cached_api_key[:10]}..., are you sure you want to re-login? The cached key will be overwritten.", abort=True)

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

    # make project
    project_name = "ga-cli"
    headers = {"Authorization": f"Bearer {token}"}
    # check if project exists
    resp = httpx.get(API_URL + f"/projects", params={"project_name": project_name}, headers=headers)
    resp.raise_for_status()
    if len(resp.json()) == 0:
        print("Creating new project `ga-cli`...")
        resp = httpx.post(API_URL + "/projects", json={"name": project_name}, headers=headers)
        resp.raise_for_status()
    else:
        print("Project `ga-cli` already exists. Proceeding...")
    
    # make apikey and cache
    print("Creating new api key...")
    resp = httpx.post(API_URL + "/api-keys", json={"project_name": project_name}, headers=headers)
    resp.raise_for_status()

    api_key = resp.json()

    # cache all creds
    TOKEN_FILE.write_text(token)
    API_KEY_FILE.write_text(api_key)
    
@app.command()
def set_api_key(api_key: Annotated[str, typer.Option(prompt=True)]):
    """
        Manually override the GA API key used by the cli.
    """
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
def wrap_mcp_config(mcp_config_file: Path):
    """
        Wraps the MCP json config with GA proxy server.
    """
    assert mcp_config_file.suffix == ".json", "Not a json config file!"
    data: dict[str, Any] = json.loads(mcp_config_file.read_text())
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
