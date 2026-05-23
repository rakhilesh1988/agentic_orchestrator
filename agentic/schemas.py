from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PerceptionResult(BaseModel):
    """Output of the Perception layer."""

    intent: str = Field(description="The primary objective identified from the input")
    entities: List[str] = Field(
        default_factory=list, description="Key subjects, names, or objects mentioned"
    )
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    urgency: Literal["low", "medium", "high"] = "low"


class PlanStep(BaseModel):
    """A single discrete step in a plan."""

    thought: str = Field(description="Internal reasoning for this step")
    tool: str = Field(
        description="The tool to use (e.g., 'web_search', 'read_file', 'final_answer')"
    )
    args: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the tool"
    )


class DecisionResult(BaseModel):
    """Output of the Decision layer."""

    steps: List[PlanStep] = Field(
        description="Ordered list of steps to achieve the goal"
    )
    rationale: str = Field(description="Overall strategy explanation")


class MemoryArtifact(BaseModel):
    """Structure for stored memories."""

    summary: str
    key_facts: List[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class ActionResponse(BaseModel):
    """Result of an action execution."""

    status: Literal["success", "failure", "pending"]
    output: Any
    artifact_path: Optional[str] = None
