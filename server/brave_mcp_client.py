import os
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai import Agent
import logfire

logfire.configure(service_name="brave_mcp_client")

load_dotenv()

brave_server = MCPServerStdio(
    'npx', ['-y', '@modelcontextprotocol/server-brave-search'],
    env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
)
agent = Agent(
    model="openai:gpt-4o-mini",
    system_prompt="You are an assistant with the ability to search the web with Brave and an expert in Cybersecurity Docker best practices",
    mcp_servers=[brave_server]
)


import asyncio
from concurrent.futures import ThreadPoolExecutor

async def web_search(query: str) -> str:
    """
    Perform a web search using the Brave MCP agent and return the result.
    Args:
        query (str): The search query to run via the Brave MCP agent.
    Returns:
        str: The result data from the agent's search.
    Raises:
        RuntimeError: If the agent search fails or an exception occurs.
    """
    logfire.info("web_search_agent_start", query=query)
    try:
        async with agent.run_mcp_servers():
            result = await agent.run(query)
            logfire.info("web_search_agent_success", query=query, response=getattr(result, 'data', result))
            return getattr(result, 'data', result)
    except Exception as e:
        logfire.error("web_search_agent_error", error=str(e), query=query)
        raise RuntimeError(f"web_search failed: {str(e)}")
