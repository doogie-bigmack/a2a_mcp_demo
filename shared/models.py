from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Part(BaseModel):
    part_id: str = Field(..., description="Unique part identifier.")
    type: str = Field(..., description="Type of part: text, file, or data.")
    content: Any = Field(..., description="Content of the part (string, bytes, or dict).")
    encoding: Optional[str] = Field(None, description="Encoding if applicable (e.g., base64 for files).")

class Artifact(BaseModel):
    artifact_id: str = Field(..., description="Unique artifact identifier.")
    type: str = Field(..., description="Type of artifact: text, file, or data.")
    parts: List[Part] = Field(default_factory=list, description="Parts that make up the artifact.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the artifact.")

class TaskHistory(BaseModel):
    transitions: List[Dict[str, Any]] = Field(default_factory=list, description="State transitions with timestamps.")
    artifacts: List[Artifact] = Field(default_factory=list, description="Artifacts produced by the task.")

class PushNotificationEndpoint(BaseModel):
    endpoint: str
    token: str | None = None

class TaskStore:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.history: Dict[str, TaskHistory] = {}
        self.push_endpoints: Dict[str, PushNotificationEndpoint] = {}

class DockerConfig(BaseModel):
    raw_text: str = Field(..., description="The Dockerfile or docker-compose YAML.")

class SendTaskRequest(BaseModel):
    raw_text: str = Field(..., description="The Dockerfile or docker-compose YAML.")

class Task(BaseModel):
    id: str = Field(..., description="Task identifier.")
    state: str = Field(..., description="Task state, e.g., 'submitted'.")
    docker_config: DockerConfig

class SendTaskResponse(BaseModel):
    task: Task

class DockerFixResult(BaseModel):
    patched_text: str = Field(..., description="The hardened Dockerfile or docker-compose YAML.")
    diff_json: dict = Field(..., description="A structured diff between input and output.")
    issues_fixed: Optional[List[str]] = Field(default=None, description="List of security issues fixed.")
    issues_remaining: Optional[List[str]] = Field(default=None, description="List of issues not fixed.")
