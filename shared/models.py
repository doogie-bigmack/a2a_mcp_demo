from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Part(BaseModel):
    """
    Represents a part of an artifact (e.g., a text chunk, file, or data block) in the A2A protocol.

    Attributes:
        part_id (str): Unique part identifier.
        type (str): Type of part (text, file, or data).
        content (Any): Content of the part (string, bytes, or dict).
        encoding (Optional[str]): Encoding if applicable (e.g., base64 for files).
    """
    part_id: str = Field(..., description="Unique part identifier.")
    type: str = Field(..., description="Type of part: text, file, or data.")
    content: Any = Field(..., description="Content of the part (string, bytes, or dict).")
    encoding: Optional[str] = Field(None, description="Encoding if applicable (e.g., base64 for files).")

class Artifact(BaseModel):
    """
    Represents an artifact, which is a collection of parts (e.g., files, text blocks) in the A2A protocol.

    Attributes:
        artifact_id (str): Unique artifact identifier.
        type (str): Type of artifact (text, file, or data).
        parts (List[Part]): Parts that make up the artifact.
        metadata (Optional[Dict[str, Any]]): Additional metadata about the artifact.
    """
    artifact_id: str = Field(..., description="Unique artifact identifier.")
    type: str = Field(..., description="Type of artifact: text, file, or data.")
    parts: List[Part] = Field(default_factory=list, description="Parts that make up the artifact.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the artifact.")

class TaskHistory(BaseModel):
    """
    Represents the history of a task, including state transitions and produced artifacts.

    Attributes:
        transitions (List[Dict[str, Any]]): State transitions with timestamps.
        artifacts (List[Artifact]): Artifacts produced by the task.
    """
    transitions: List[Dict[str, Any]] = Field(default_factory=list, description="State transitions with timestamps.")
    artifacts: List[Artifact] = Field(default_factory=list, description="Artifacts produced by the task.")

class PushNotificationEndpoint(BaseModel):
    """
    Represents a push notification endpoint for task updates in the A2A protocol.

    Attributes:
        endpoint (str): The push notification endpoint URL.
        token (Optional[str]): Optional authentication token for the endpoint.
    """
    endpoint: str
    token: str | None = None

class TaskStore:
    """
    In-memory store for managing tasks, their histories, and notification endpoints.
    Used by the FastAPI server to track A2A task state and delivery.
    """
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.history: Dict[str, TaskHistory] = {}
        self.push_endpoints: Dict[str, PushNotificationEndpoint] = {}

class DockerConfig(BaseModel):
    """
    Represents a Docker configuration (Dockerfile or docker-compose YAML) for analysis.

    Attributes:
        raw_text (str): The Dockerfile or docker-compose YAML content.
    """
    raw_text: str = Field(..., description="The Dockerfile or docker-compose YAML.")

class SendTaskRequest(BaseModel):
    """
    Request model for sending a Docker configuration as a task via the A2A protocol.

    Attributes:
        raw_text (str): The Dockerfile or docker-compose YAML content.
    """
    raw_text: str = Field(..., description="The Dockerfile or docker-compose YAML.")

class Task(BaseModel):
    """
    Represents an A2A task, including its state and associated Docker configuration.

    Attributes:
        id (str): Task identifier.
        state (str): Task state (e.g., 'submitted').
        docker_config (DockerConfig): The Docker configuration associated with the task.
    """
    id: str = Field(..., description="Task identifier.")
    state: str = Field(..., description="Task state, e.g., 'submitted'.")
    docker_config: DockerConfig

class SendTaskResponse(BaseModel):
    """
    Response model for a successful task submission in the A2A protocol.

    Attributes:
        task (Task): The submitted task.
    """
    task: Task

class DockerFixResult(BaseModel):
    """
    Represents the result of a Dockerfile security fix operation.

    Attributes:
        patched_text (str): The hardened Dockerfile or docker-compose YAML.
        diff_json (dict): Structured diff between input and output.
        issues_fixed (Optional[List[str]]): List of security issues fixed.
        issues_remaining (Optional[List[str]]): List of issues not fixed.
    """
    patched_text: str = Field(..., description="The hardened Dockerfile or docker-compose YAML.")
    diff_json: dict = Field(..., description="A structured diff between input and output.")
    issues_fixed: Optional[List[str]] = Field(default=None, description="List of security issues fixed.")
    issues_remaining: Optional[List[str]] = Field(default=None, description="List of issues not fixed.")
