# A2A Compliance Task List

## TODO
- [ ] When updating Markdown checklists for A2A compliance, always use green check marks (✅) to indicate completed items, not just [x]. This applies to task lists in a2a-task.md and similar files.

> This task board tracks everything we need to implement (or refactor) so that the **client** and **server** in this repo fully conform to the A2A‑PRD specification (`A2A-prd.md`). Tick items off as they are completed. Feel free to break down further or re‑prioritise.

---

## 🏁 Legend
- [ ]  = not started
- [~]  = in progress / PR open
- ✅  = done / merged (✅)

---

## 1. Agent Card & Discovery
| Status | Task |
|:---:|---|
| ✅ | **Server** → expose `/.well-known/agent.json` with all required fields (`name`, `url`, `version`, `skills`, `capabilities`, optional `authentication`) |
| ✅ | **Client** → serve its own `agent.json` (optional but useful for mutual auth) |
| ✅ | **Client** → fetch & validate server agent card on startup (check required fields, capabilities, auth schemes) |
| ✅ | Unit tests for agent card schema compliance |

## 2. Authentication
| Status | Task |
|:---:|---|
| ✅ | Support `Bearer` token scheme (env‑driven shared secret for PoC) |
| ✅ | Embed auth header in **client → server** calls |
| ✅ | Validate token inside server middleware; return JSON‑RPC auth error on failure |
| [ ] | Add optional **server → client** auth verification if we publish client agent card |

## 3. Core JSON‑RPC Methods
### 3.a `tasks/send` (synchronous)  
_Current code_: implemented **as REST POST** `/a2a/tasks/send` — must migrate to JSON‑RPC at root (“/”)._
| Status | Task |
|:---:|---|
| ✅ | Replace REST handler with JSON‑RPC router (FastAPI or `jsonrpcserver`) |
| ✅ | Marshal request → `SendTaskRequest` schema (`params.raw_text`, metadata…) |
| ✅ | Return `SendTaskResponse` with Task object (state=`submitted`) |

### 3.b `tasks/sendSubscribe` (streaming)
| Status | Task |
|:---:|---|
| ✅ | Implement SSE endpoint at `/stream/{task_id}` returning **channel URL** (live) |
| ✅ | Stream TaskStatusUpdate + optional TaskArtifactUpdate events |
| ✅ | Support graceful close & final state

### 3.c `tasks/get`
| Status | Task |
|:---:|---|
| ✅ | Add task store (in‑mem dict for PoC) tracking `state`, `history`, `artifacts` |
| ✅ | Implement JSON‑RPC handler with `historyLength` param slice |
| ✅ | Return −32001 if id unknown

### 3.d `tasks/cancel`
| Status | Task |
|:---:|---|
| ✅ | Cancellation logic + −32002 error if not cancelable |

### 3.e Push Notifications (`tasks/pushNotification/set|get`)
| Status | Task |
|:---:|---|
| ✅ | Persist push endpoint (url + token) per task |

---


| [ ] | Async task executor POSTs events to callback |
| [ ] | Opt‑in check during `send`

### 3.f `tasks/resubscribe`
| Status | Task |
|:---:|---|
| ✅ | Accept id, return fresh stream URL, resume events from `historyLength` offset |

## 4. Task Lifecycle & State Machine
| Status | Task |
|:---:|---|
| ✅ | Central `Task` dataclass with allowed state transitions |
| ✅ | Store `transitionHistory` when capability enabled |
| ✅ | Enforce lifecycle (submitted → working → completed/failed/canceled) |

## 5. Artifacts & Parts Model
| Status | Task |
|:---:|---|
| ✅ | Define `Artifact` & `Part` pydantic models (text/file/data) |
| ✅ | Chunked uploads (`append`, `lastChunk` flags) not needed for PoC but provide api stubs |

## 6. Client Library Updates
| Status | Task |
|:---:|---|
| ✅ | Replace direct `requests.post` with JSON‑RPC helper (sync + streaming) (stub or implemented) |
| ✅ | Handle SSE/WebSocket stream, update CLI in real time (stub or implemented) |
| ✅ | Implement polling (`tasks/get`) fallback (stub or implemented) |
| ✅ | Support `--cancel` CLI flag that calls `tasks/cancel` (stub or implemented) |
| ✅ | Option to register push‑notification endpoint (local webhook or ngrok) (stub or implemented) |

## 7. Error Handling & Mapping
| Status | Task |
|:---:|---|
| ✅ | Map server exceptions to JSON‑RPC standard codes & domain codes (−32001…−32004) |
| [ ] | Extend client pretty‑print for errors |

## 8. Logging & Observability
| Status | Task |
|:---:|---|
| ✅ | Add trace ids + task ids to all logfire events |
| ✅ | Structured logs for each state transition & artifact creation |

## 9. Tests & CI
| Status | Task |
|:---:|---|
| [ ] | Unit tests for each method (success & error paths) |
| [ ] | Integration test – full happy path (`sendSubscribe` with stream) |
| [ ] | Integration test – cancel mid‑way |
| [ ] | GitHub Actions matrix: Python 3.9/3.10 on Ubuntu & Mac |

---

### 🌱 Stretch Goals / Nice‑to‑have
- [ ] gRPC transport option instead of JSON‑RPC over HTTP
- [ ] JWT‑based auth with rotating keys
- [ ] Persist tasks to Redis for horizontal scaling
- [ ] OpenTelemetry traces across client ↔ server
- [ ] GET to invalid endpoint (e.g., /.well-known/agent.jsonBAD) returns 404
- [ ] POST/PUT/DELETE to /.well-known/agent.json returns 405
- [ ] Malformed Accept header (e.g., application/xml) returns 406 or JSON error
- [ ] No Accept header (should default to JSON)
- [ ] Extra query parameters on /.well-known/agent.json handled gracefully
- [ ] Validate agent card JSON schema and required fields
- [ ] JSON-RPC: send malformed request (invalid JSON, missing fields)
- [ ] JSON-RPC: request non-existent task ID returns −32001
- [ ] SSE: connect with invalid/expired task ID returns error/close

---

**Next step:** pick a high‑value slice (e.g. JSON‑RPC `tasks/send` + agent card) and open a PR.
