import typer
from rich import print as rprint
from pathlib import Path
from typing import Annotated, Optional, Dict, Any
import httpx
import shutil, json
import time
from datetime import datetime
from .config import API_URL, CONFIG_DIR, API_KEY_FILE, TOKEN_FILE


readme = """
    This is GA cli. I'll manage your credentials to connect to the GA Guardrail server and configures your MCP config files to be protected by injection guardrails.\n
    - Run `ga login` to set up GA credentials.\n
    - They run `ga configure` to detect your MCP clients (Cursor, Claude Code, ...).\n
"""

app = typer.Typer(help=readme)

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
    rprint("Open in browser:")
    print(data["verification_url"])
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
        rprint("Creating new project `ga-cli`...")
        resp = httpx.post(API_URL + "/projects", json={"name": project_name}, headers=headers)
        resp.raise_for_status()
    else:
        rprint("Project `ga-cli` already exists. Proceeding...")
    
    # make apikey and cache
    rprint("Creating new api key...")
    resp = httpx.post(API_URL + "/api-keys", json={"project_name": project_name}, headers=headers)
    resp.raise_for_status()

    api_key = resp.json()

    # cache all creds
    rprint("Caching the credentials to", CONFIG_DIR)
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
    rprint(f"Using api key: {api_key[:8]}...")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = httpx.post(API_URL + "/guard", json={"text": text, "policy_name": "@ga/default"}, headers=headers)
    rprint(response.url)
    response.raise_for_status()
    rprint(response.json())

def _wrap_mcp_config(mcp_config_file: Path, npx_command: str="npx"):
    assert mcp_config_file.suffix == ".json", "Not a json config file!"
    data: Dict[str, Any] = json.loads(mcp_config_file.read_text())
    new_config = {}
    is_changed = False
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    for name, server_config in data["mcpServers"].items():
        if "args" in server_config and len(server_config["args"]) >= 2 and server_config["args"][1].startswith("@general-analysis"):
            new_config[name] = server_config
            continue
        rprint("Configuring", name)
        server_config["name"] = name
        encoded = json.dumps([server_config], separators=(',', ':'))
        new_config[f"protected-{name}"] = {
            "command": npx_command,
            "args": [
                "-y",
                "@general-analysis/mcp-guard@latest",
                encoded,
            ],
            "env": {
                "API_KEY": API_KEY_FILE.read_text(),
                "ENABLE_GUARD_API": "true",
            }
        }
        is_changed = True
    if is_changed:
        backup_file = mcp_config_file.with_stem(mcp_config_file.stem + "_" + datetime.now().replace(microsecond=0).isoformat() + "_bak")
        shutil.move(mcp_config_file, backup_file)
        rprint("Backup saved to", backup_file)
        data["mcpServers"] = new_config
        mcp_config_file.write_text(json.dumps(data, indent=2))
        rprint(mcp_config_file, "is now properly configured!")
    else:
        rprint(f"{mcp_config_file} is already configured!")

@app.command()
def configure(mcp_config_file: Annotated[Optional[Path], typer.Argument(help="The MCP config file (e.g. mcp.json) to configure. Leave empty to look for common MCP clients.")]=None, npx_command: Annotated[str, typer.Option(help="Replacement npx command, e.g. `bunx`")]="npx"):
    """
        Wraps the MCP json config with GA proxy server.
    """
    if mcp_config_file is None:
        app_configs = {
            "Cursor": Path.home() / ".cursor/mcp.json",
            "Claude Desktop": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
            "Claude Code Global": Path.home() / ".claude.json",
            "Claude Code Project": Path(".mcp.json"),
        }
        # look for cursor
        for app, path in app_configs.items():
            rprint(f"Looking for {path}")
            if path.exists():
                rprint(f"Found {app} config at {path}, configuring...")
                _wrap_mcp_config(path, npx_command)
    else:
        _wrap_mcp_config(mcp_config_file, npx_command)

def main():
    app()
