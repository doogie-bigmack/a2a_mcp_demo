# A2A + MCP Docker Security Demo: Task Checklist

This checklist breaks down the implementation into actionable steps. Check off each item as you progress.

---

## 1. Project Setup
- ✅ Create project directory structure (`client/`, `server/`, `shared/`, etc.)
- ✅ Initialize `requirements.txt` with all dependencies
- ✅ Create `docker-compose.yml` for orchestration

## 2. Shared Models
- ✅ Define Pydantic models for input (Dockerfile/Compose), output (patched file), and JSON diff in `shared/models.py`

## 3. Server (Security Agent)
- ✅ Scaffold server with A2A endpoint and Agent Card (`/.well-known/agent.json`)
- ✅ Implement MCP tool: `analyze_and_fix_docker`
  - ✅ Integrate Hadolint for static Dockerfile checks
  - ✅ Integrate Trivy for container image scanning
  - ✅ Integrate Brave/Playwright for live best-practice lookup
  - ✅ Apply best-practice fixes (least privilege, image pinning, etc.)
- ✅ Ensure schema-validated input/output
- ✅ Add observability/logging (Logfire, JSON logs)
- ✅ Write server `Dockerfile`

## 4. Client (Coding Agent)
- ✅ Scaffold client CLI/REST app
- ✅ Accept Dockerfile/Compose input
- ✅ Send A2A `tasks/send` call to server
- ✅ Receive and display fixed file + JSON diff
- ✅ Add observability/logging
- ✅ Write client `Dockerfile`

## 5. A2A Integration
- ✅ Implement A2A protocol on both client and server
- ✅ Support JSON schemas and SSE streaming
- ✅ Serve and consume Agent Card

## 6. Testing & Validation
- ✅ End-to-end test: client submits Dockerfile, server returns hardened version + diff
- ✅ Validate round-trip latency (≤ 20s)
- ✅ Ensure ≥80% critical issues resolved (simulate if needed)

## 7. Documentation
- ✅ Write a clear `README.md` with setup and usage instructions
- ✅ Document environment variables and configuration

## 8. Extras (Optional)
- ✅ Add sample Dockerfiles/Compose files for testing
- ✅ Add CI/CD pipeline for automated testing

---

**Note:** The Brave MCP server is now run via `npx -y @modelcontextprotocol/server-brave-search` in a separate terminal. Your `.env` must include `BRAVE_MCP_SERVER_URL=http://host.docker.internal:3000` for Docker containers to reach the server.

**Progress Tracking:**
- Mark each item as `[x]` when complete.
- Add notes or links to PRs/issues as needed.

---

_Last updated: 2025-04-21_
