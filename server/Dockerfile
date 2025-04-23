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
COPY server ./server
RUN pwd && ls -l /app && ls -l /app/server && head -20 /app/server/agent.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
EXPOSE 8080
CMD ["uvicorn", "server.agent:app", "--host", "0.0.0.0", "--port", "8080"]
