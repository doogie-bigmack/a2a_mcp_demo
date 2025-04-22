FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js and npx (required for Brave MCP subprocess)
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY mcp_client.py .env ./

CMD ["python", "mcp_client.py"]