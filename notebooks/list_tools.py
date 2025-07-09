#!/usr/bin/env python3
import json
import asyncio
import traceback
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

async def get_server_tools(name: str, config: dict):
    """Connect to an MCP server and retrieve its tools."""
    try:
        if "command" in config:
            # Command-based server (stdio transport)
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env", {})
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    return [(tool.name, tool.description) for tool in tools_response.tools]
        
        elif "url" in config:
            # URL-based server using Streamable HTTP transport
            url = config["url"]
            if not url.endswith('/mcp'):
                if url.endswith('/'):
                    url = url + 'mcp'
                else:
                    url = url + '/mcp'
            
            async with streamablehttp_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    return [(tool.name, tool.description) for tool in tools_response.tools]
            
    except Exception as e:
        # Print full stack trace
        error_details = traceback.format_exc()
        return [("Error", f"{str(e)}\n{error_details}")]

async def list_all_tools(config_path: str = "data/demo_config.json"):
    """List tools from all MCP servers in config file."""
    config = json.loads(Path(config_path).read_text())
    
    print("MCP Server Tools:")
    print("=" * 80)
    
    for name, server_config in config.get("mcpServers", {}).items():
        print(f"\n📡 {name}:")
        print("-" * 40)
        tools = await get_server_tools(name, server_config)
        
        if not tools:
            print("  No tools available")
            continue
            
        for tool_name, tool_desc in tools:
            print(f"  🔧 {tool_name}")
            if tool_desc:
                # Wrap long descriptions
                desc_lines = tool_desc.split('\n')
                for line in desc_lines:
                    if len(line) > 70:
                        # Simple word wrap
                        words = line.split(' ')
                        current_line = "     "
                        for word in words:
                            if len(current_line + word) > 70:
                                print(current_line)
                                current_line = "     " + word + " "
                            else:
                                current_line += word + " "
                        if current_line.strip():
                            print(current_line)
                    else:
                        print(f"     {line}")
            else:
                print("     (No description available)")
            print()

if __name__ == "__main__":
    asyncio.run(list_all_tools())
