from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Goal(BaseModel):
    """A specific objective within the larger user query."""

    description: str = Field(alias="goal", description="What needs to be accomplished")
    is_done: bool = Field(
        default=False, description="Whether this goal has been satisfied"
    )
    artifact_path: Optional[str] = Field(
        default=None,
        description="Path to the raw data file if this goal involved a tool",
    )

    model_config = ConfigDict(populate_by_name=True)


class MemoryKind(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    TOOL_OUTCOME = "tool_outcome"
    SCRATCHPAD = "scratchpad"


class MemoryItem(BaseModel):
    kind: Literal["fact", "preference", "tool_outcome", "scratchpad"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PerceptionResult(BaseModel):
    """Output of the Perception layer: the current state of goals."""

    goals: List[Goal] = Field(
        alias="goal_list", description="The current list of goals and their status"
    )
    context_summary: str = Field(
        default="", description="Brief summary of the current session state"
    )
    relevant_artifacts: List[str] = Field(
        default_factory=list,
        description="List of all artifact paths relevant to the current session",
    )
    new_knowledge: List[MemoryItem] = Field(
        alias="knowledge",
        default_factory=list,
        description="New facts or preferences discovered during this perception step",
    )

    model_config = ConfigDict(populate_by_name=True)


class ToolCall(BaseModel):
    """A request to execute a specific tool."""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class FinalAnswer(BaseModel):
    """The final response to the user's query."""

    text: str


class DecisionResult(BaseModel):
    """Output of the Decision layer: picking the next action."""

    tool_call: Optional[ToolCall] = Field(
        default=None, description="Request to run a tool"
    )
    final_answer: Optional[str] = Field(
        default=None, description="Final answer to the user as a plain string"
    )
    thought: str = Field(
        default="", description="The reasoning behind picking this action"
    )


class MemoryArtifact(BaseModel):
    """Structure for stored memories/facts grouped by kind."""

    items: List[MemoryItem] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class ActionResponse(BaseModel):
    """Result of an action execution."""

    status: Literal["success", "failure"]
    output_summary: str = Field(
        description="Short descriptor of what happened for Memory"
    )
    artifact_path: Optional[str] = None
    raw_output: Optional[Any] = None
