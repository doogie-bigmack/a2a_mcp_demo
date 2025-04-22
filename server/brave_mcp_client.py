import os
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai import Agent
import asyncio
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

async def web_search(query: str) -> str:
    logfire.info("web_search_agent_start", extra={"query": query})
    async def run_agent():
        async with agent.run_mcp_servers():
            result = await agent.run(query)
        return result.data
    try:
        response_text = await run_agent()
        logfire.info("web_search_agent_success", extra={"query": query, "response": response_text})
        return response_text
    except Exception as e:
        logfire.error("web_search_agent_error", extra={"error": str(e), "query": query})
        raise RuntimeError(f"web_search failed: {str(e)}")
