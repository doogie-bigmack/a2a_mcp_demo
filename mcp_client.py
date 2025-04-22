import asyncio
import os
from dotenv import load_dotenv
from fastmcp.client import MCPClient

async def main():
    # Load environment variables
    load_dotenv()

    # Create MCPClient from config file
    client = MCPClient.from_config_file("mcp.json")

    # Make a search query
    response = await client.request(
        {"method": "brave_web_search"},
        {"query": "best coffee shops in Seattle", "count": 10}
    )
    print(f"Search Results: {response}")

if __name__ == "__main__":
    asyncio.run(main())
