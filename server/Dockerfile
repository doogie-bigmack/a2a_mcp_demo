FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and node/npm first (cacheable)
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing git curl nodejs npm \
    && npm install -g @modelcontextprotocol/server-brave-search \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies separately (cacheable)
COPY ../requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Now copy only your app code (these change most frequently)
COPY shared ./shared
COPY server/agent.py server/main.py server/brave_mcp_client.py server/send_subscribe_sse.py server/jsonrpc_dispatch.py server/task_store.py ./
RUN pwd && ls -l /app && cat /app/agent.py | head -20

EXPOSE 8080
CMD ["python", "main.py"]
