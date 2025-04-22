from flask import Flask, request, jsonify
import logfire
logfire.configure(service_name="mcp_client")
from dotenv import load_dotenv
import os
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai import Agent

load_dotenv()

app = Flask(__name__)

# Brave Search MCP server
brave_server = MCPServerStdio(
    'npx', ['-y', '@modelcontextprotocol/server-brave-search'],
    env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
)

agent = Agent(
    model="openai:gpt-4o-mini",
    system_prompt="You are an assistant with the ability to search the web with Brave.",
    mcp_servers=[brave_server]
)

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    async def run_agent():
        async with agent.run_mcp_servers():
            result = await agent.run(query)
        return result.data

    import asyncio
    try:
        logfire.info("search_agent_start", query=query)
        response_text = asyncio.run(run_agent())
        logfire.info("search_agent_success", query=query, response=response_text)
        return jsonify({"result": response_text})
    except Exception as e:
        logfire.error("search_agent_error", error=str(e), query=query)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

