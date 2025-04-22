Here’s everything you need to spin‑up a Google A2A + MCP multi‑agent demo with a Docker‑security server agent and a coding client agent powered by GPT‑4.1.

⸻

## Overview (TL;DR)
	•	Protocol layer ✦ Google’s new Agent‑to‑Agent (A2A) spec lets the two agents exchange tasks & artefacts securely over HTTP; the Python reference lives in google/A2A  ￼ ￼ ￼.
	•	Context/tools layer ✦ Each agent embeds the Model‑Context Protocol (MCP) client so it can call external tools (e.g., a Brave‑browser MCP server for live web search) or expose its own tools  ￼ ￼.
	•	Agent framework ✦ We use the brand‑new PydanticAI 0.1.3 for type‑safe, state‑machine‑driven agents  ￼ with Logfire 3.14.0 for structured traces  ￼.
	•	LLM layer ✦ Both agents call GPT‑4.1 through the OpenAI Python SDK 1.75.0  ￼ ￼.
	•	Demo goal ✦ The server inspects a user‑supplied Dockerfile/Compose snippet, queries the web for up‑to‑date hardening advice, and returns a patched config. The client accepts the snippet, delegates security to the server, and shows the user the improved file.

⸻

## 1. Product‑Requirements Document (PRD)

### 1.1 Purpose & scope
Create a reproducible PoC that demonstrates cross‑agent delegation (coding → security) over A2A while showcasing MCP tool‑use for live information retrieval.

### 1.2 Success criteria

Metric	Target
Round‑trip “lint + fix” latency	≤ 20 s on a 4‑CPU laptop
OWASP/BenchSec warnings resolved	≥ 80 % of high/critical issues
Demo run with single docker compose up	✅

### 1.3 Key functional requirements
	1.	Client agent
	•	Accept Dockerfile/Compose text via CLI/REST.
	•	Send a tasks/send A2A call to security agent.
	•	Receive fixed file + JSON diff; display to user.
	2.	Server (security) agent
	•	Expose A2A endpoint + /.well‑known/agent.json.
	•	Provide MCP tool analyze_and_fix_docker with schema‑validated input/output.
	•	During execution
a. Static checks (Hadolint, Trivy).
b. Dynamic best‑practice lookup via Brave‑browser MCP server  ￼ ￼.
c. Apply fixes (least privilege, image pinning, user namespaces, network isolation) per OWASP & industry guides  ￼ ￼ ￼.
	3.	Cross‑agent contract
	•	Follow A2A JSON schemas; messages stream via SSE when available.

### 1.4 Tech stack & versions

# requirements.txt
openai==1.75.0          # GPT‑4.1 access  [oai_citation_attribution:14‡PyPI](https://pypi.org/project/openai/?utm_source=chatgpt.com)
pydantic-ai==0.1.3      # Agent framework  [oai_citation_attribution:15‡PyPI](https://pypi.org/project/pydantic-ai/?utm_source=chatgpt.com)
logfire==3.14.0         # Observability  [oai_citation_attribution:16‡PyPI](https://pypi.org/project/logfire/?utm_source=chatgpt.com)
mcp-agent==0.0.16       # High‑level MCP helper  [oai_citation_attribution:17‡GitHub](https://github.com/lastmile-ai/mcp-agent)
mcp==0.4.3              # Low‑level MCP client/server  [oai_citation_attribution:18‡PyPI](https://pypi.org/project/mcp/?utm_source=chatgpt.com)
browser-use-mcp-server==1.0.2  # Brave automation server  [oai_citation_attribution:19‡PyPI](https://pypi.org/project/browser-use-mcp-server/1.0.2/?utm_source=chatgpt.com)
playwright==1.44.0      # Headless browser control  [oai_citation_attribution:20‡Apify Blog](https://blog.apify.com/unlocking-the-potential-of-brave-and-playwright-for-browser-automation/?utm_source=chatgpt.com)
hadolint==2.12.0        # Dockerfile linter (installed via apk/apt)
trivy==0.50.0           # Container image scanner
git+https://github.com/google/A2A.git@main#subdirectory=python  # A2A SDK  [oai_citation_attribution:21‡GitHub](https://github.com/google/A2A)

Note: A2A has no PyPI release yet; we pull straight from GitHub.

### 1.5 Non‑functional
	•	Security: containers run as non‑root, drop all unnecessary Linux capabilities, use USER instruction, and leverage Docker Secrets  ￼.
	•	Extensibility: any MCP server (e.g., fetch, filesystem) can be plugged in later with one line of YAML.
	•	Observability: Logfire events exported in OTLP for Grafana.

### 1.6 Milestones

Date	Deliverable
 T + 3 d	Running security agent fixing simple Dockerfile
 T + 7 d	A2A integration, end‑to‑end demo
 T + 10 d	Hardened containers, docs, recorded screencast



⸻

## 2. Code stubs (essentials)

<details><summary>Project tree</summary>


a2a‑docker‑demo/
├── client/
│   ├── agent.py
│   ├── main.py
│   └── Dockerfile
├── server/
│   ├── agent.py
│   ├── main.py
│   └── Dockerfile
├── shared/
│   └── models.py
├── docker-compose.yml
└── requirements.txt

</details>


### 2.1 shared/models.py

from pydantic import BaseModel, Field

class DockerConfig(BaseModel):
    raw_text: str = Field(..., description="The Dockerfile or docker‑compose YAML.")

class FixRequest(BaseModel):
    config: DockerConfig
    requested_fixes: list[str] = Field(default_factory=list)

class FixResponse(BaseModel):
    fixed_config: str
    summary: str   # human‑readable explanation

### 2.2 Server agent (server/agent.py)

import asyncio, os, subprocess, json, pathlib
from typing import Any
from openai import AsyncOpenAI
from pydantic_ai import Agent, tool, message
from logfire import configure
from mcp_agent import MCPApp           # high‑level wrapper
from mcp_agent.mcp.gen_client import gen_client
from shared.models import FixRequest, FixResponse

configure()  # Logfire

client = AsyncOpenAI()

class DockerSecurityAgent(Agent):
    """Secure‑by‑design agent that lints and patches Docker configs."""

    @tool
    async def analyze_and_fix(self, request: FixRequest) -> FixResponse:
        # 1. Static lint
        tmp = pathlib.Path("/tmp/config")
        tmp.write_text(request.config.raw_text)
        hadolint_out = subprocess.run(
            ["hadolint", "-f", "json", tmp], capture_output=True, text=True
        ).stdout

        # 2. Fetch best‑practice snippets via Brave MCP server
        async with gen_client("brave-browser") as brave:
            best_practices = await brave.call_tool("search", {"query": "docker security best practices 2025 site:docs.docker.com"})
        
        # 3. Ask GPT‑4.1 to combine lint results + best practices into a patch
        prompt = f"""
        You are a container‑security specialist. 
        Original Dockerfile:\n{request.config.raw_text}
        Lint findings:\n{hadolint_out}
        External guidelines:\n{best_practices}
        Produce a *fully fixed* Dockerfile and a short summary.
        """
        resp = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        fixed, summary = resp.choices[0].message.content.split("---SUMMARY---")
        return FixResponse(fixed_config=fixed.strip(), summary=summary.strip())

app = MCPApp(agent=DockerSecurityAgent())
# When run inside Docker the app starts an A2A‑aware HTTP server (see main.py)

### 2.3 Server launcher (server/main.py)

from a2a import A2AServer
from server.agent import app

server = A2AServer(agent_app=app, host="0.0.0.0", port=8080)
server.run()

### 2.4 Client agent (client/agent.py)

from typing import Any
from pydantic_ai import Agent, tool
from openai import AsyncOpenAI
from a2a import A2AClient              # python sdk from google/A2A
from shared.models import DockerConfig, FixRequest, FixResponse

class DockerCodingAgent(Agent):
    def __init__(self, security_url: str):
        super().__init__()
        self.security = A2AClient(security_url)

    @tool
    async def delegate_security(self, cfg: DockerConfig) -> FixResponse:
        task = await self.security.tasks.send(
            FixRequest(config=cfg).model_dump())
        # Wait for completion (stream or polling)
        final = await task.wait()
        return FixResponse(**final["result"])

agent = DockerCodingAgent(security_url="http://security-agent:8080")

### 2.5 Client CLI (client/main.py)

import sys, asyncio, yaml, pathlib, rich
from shared.models import DockerConfig
from client.agent import agent

async def run(path: str):
    text = pathlib.Path(path).read_text()
    resp = await agent.delegate_security(DockerConfig(raw_text=text))
    rich.print("[bold green]Fixed config:[/bold green]\n", resp.fixed_config)
    rich.print("[bold yellow]Why:[/bold yellow]\n", resp.summary)

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))



⸻

## 3. Containerisation & orchestration

### 3.1 server/Dockerfile

FROM python:3.12-slim

# Install Brave + Hadolint + Trivy (abbrev)
RUN apt-get update && \
    apt-get install -y curl gnupg ca-certificates && \
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
         https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] \
         https://brave-browser-apt-release.s3.brave.com/ stable main" \
         > /etc/apt/sources.list.d/brave-browser-release.list && \
    apt-get update && apt-get install -y brave-browser hadolint trivy && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

WORKDIR /app
COPY server/ server/
COPY shared/ shared/

CMD ["python", "-m", "server.main"]
USER 1000:1000   # non‑root per best practice  [oai_citation_attribution:23‡OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html?utm_source=chatgpt.com) [oai_citation_attribution:24‡KDnuggets](https://www.kdnuggets.com/how-to-secure-docker-containers-with-best-practices?utm_source=chatgpt.com)

### 3.2 client/Dockerfile

FROM python:3.12-slim

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

WORKDIR /app
COPY client/ client/
COPY shared/ shared/

CMD ["python", "-m", "client.main", "/input/Dockerfile"]

### 3.3 docker-compose.yml

version: "3.9"
services:
  security-agent:
    build: ./server
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports: ["8080:8080"]
  coding-agent:
    build: ./client
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./sample:/input    # put your Dockerfile here
    depends_on:
      - security-agent



⸻

## Next steps for you
	1.	export OPENAI_API_KEY=sk-…
	2.	docker compose build && docker compose up
	3.	Place a test Dockerfile in ./sample/ and watch the client log the patched version.

Feel free to iterate on the PRD, extend the agents with additional tools (SBOM checks, dependency pinning, etc.), or swap Brave for any other MCP server—the wiring remains the same.

⸻

### Key references
	•	GPT‑4.1 launch & capabilities  ￼
	•	Google A2A announcement & repo  ￼ ￼
	•	MCP core spec & Python helper  ￼ ￼
	•	PydanticAI framework  ￼
	•	Logfire observability  ￼
	•	Brave browser MCP server & Playwright setup  ￼ ￼
	•	Docker security best‑practice sources  ￼ ￼ ￼

Happy hacking!