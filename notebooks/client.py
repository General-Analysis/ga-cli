import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.metadata_utils import get_display_name

from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

async def main():
    # Connect to a streamable HTTP server
    async with streamablehttp_client("https://mcp.deepwiki.com/mcp") as (
        read_stream,
        write_stream,
        _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            # Call a tool
            # tool_result = await session.call_tool("echo", {"message": "hello"})
            await display_tools(session)

async def display_tools(session: ClientSession):
    """Display available tools with human-readable names"""
    tools_response = await session.list_tools()

    for tool in tools_response.tools:
        # get_display_name() returns the title if available, otherwise the name
        display_name = get_display_name(tool)
        print(f"Tool: {display_name}")
        if tool.description:
            print(f"   {tool.description}")

if __name__ == "__main__":
    asyncio.run(main())
