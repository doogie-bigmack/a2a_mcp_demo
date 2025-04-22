FROM python:3.12-slim
WORKDIR /app
COPY shared ./shared
COPY client/agent.py client/main.py ./
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing git curl \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*
EXPOSE 8080
CMD ["python", "main.py"]
