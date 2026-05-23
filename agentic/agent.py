import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ValidationError

# Ensure project root is in sys.path so llm_gatewayV3 can be imported
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import separated schemas
from agentic.schemas import (
    ActionResponse,
    DecisionResult,
    MemoryArtifact,
    PerceptionResult,
    PlanStep,
)
from llm_gatewayV3.client import LLM

# Configuration
AGENTIC_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = AGENTIC_ROOT / "sandbox" / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)

# ────────────────────────────────────────────────────────────────────────────
# Artifact Storage
# ────────────────────────────────────────────────────────────────────────────


class ArtifactStorage:
    """Manages saving and retrieving Pydantic-validated artifacts."""

    def __init__(self, storage_dir: Path = ARTIFACTS_DIR):
        self.storage_dir = storage_dir

    def save(self, name: str, model: BaseModel) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in name])
        path = self.storage_dir / f"{timestamp}_{safe_name}.json"

        data = {
            "metadata": {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "model_type": model.__class__.__name__,
            },
            "payload": model.model_dump(),
        }

        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def load_latest(
        self, name_pattern: str, model_class: type[BaseModel]
    ) -> Optional[BaseModel]:
        """Load the most recent artifact matching a name pattern."""
        files = sorted(self.storage_dir.glob(f"*_{name_pattern}.json"), reverse=True)
        if not files:
            return None
        try:
            data = json.loads(files[0].read_text(encoding="utf-8"))
            return model_class.model_validate(data["payload"])
        except Exception:
            return None


# ────────────────────────────────────────────────────────────────────────────
# Cognitive Layers
# ────────────────────────────────────────────────────────────────────────────


class Perception:
    def __init__(self, llm: LLM):
        self.llm = llm

    def process(self, input_text: str) -> PerceptionResult:
        result = self.llm.chat(
            prompt=f"Analyze: {input_text}",
            system="You are the Perception layer. Extract intent, entities, sentiment, and urgency.",
            response_format={
                "type": "json_schema",
                "schema": PerceptionResult.model_json_schema(),
            },
            auto_route="perception",
        )
        try:
            return PerceptionResult.model_validate_json(result["text"])
        except (ValidationError, json.JSONDecodeError):
            return PerceptionResult(intent=input_text, entities=[])


class Memory:
    def __init__(self, llm: LLM, storage: ArtifactStorage):
        self.llm = llm
        self.storage = storage

    def update(self, thread_id: str, new_info: str) -> MemoryArtifact:
        existing = self.storage.load_latest(f"memory_{thread_id}", MemoryArtifact)
        context_str = existing.summary if existing else "No prior history."

        prompt = f"Existing Memory: {context_str}\nNew Info: {new_info}"

        result = self.llm.chat(
            prompt=prompt,
            system="You are the Memory layer. Consolidate info into a summary and extract key facts.",
            response_format={
                "type": "json_schema",
                "schema": MemoryArtifact.model_json_schema(),
            },
            auto_route="memory",
        )
        try:
            mem = MemoryArtifact.model_validate_json(result["text"])
            self.storage.save(f"memory_{thread_id}", mem)
            return mem
        except Exception:
            mem = MemoryArtifact(summary=new_info)
            self.storage.save(f"memory_{thread_id}", mem)
            return mem


class Decision:
    def __init__(self, llm: LLM):
        self.llm = llm

    def plan(
        self, objective: PerceptionResult, memory: MemoryArtifact
    ) -> DecisionResult:
        prompt = (
            f"Objective: {objective.model_dump_json()}\n"
            f"Context: {memory.summary}\n"
            f"Facts: {memory.key_facts}"
        )

        result = self.llm.chat(
            prompt=prompt,
            system="You are the Decision layer. Create a plan with steps (thought, tool, args).",
            response_format={
                "type": "json_schema",
                "schema": DecisionResult.model_json_schema(),
            },
            auto_route="decision",
        )
        try:
            return DecisionResult.model_validate_json(result["text"])
        except Exception:
            return DecisionResult(
                steps=[PlanStep(thought="Direct answer", tool="final_answer", args={})],
                rationale="Fallback",
            )


class Action:
    def __init__(self, storage: ArtifactStorage):
        self.storage = storage

    def execute(self, step: PlanStep) -> ActionResponse:
        print(f"  >> Executing [{step.tool}] with args: {step.args}")
        response = ActionResponse(
            status="success", output=f"Simulated output for {step.tool}"
        )
        path = self.storage.save(f"action_{step.tool}", response)
        response.artifact_path = str(path)
        return response


# ────────────────────────────────────────────────────────────────────────────
# Agent Orchestrator
# ────────────────────────────────────────────────────────────────────────────


class Agent:
    def __init__(self):
        self.llm = LLM()
        self.storage = ArtifactStorage()
        self.perception = Perception(self.llm)
        self.memory = Memory(self.llm, self.storage)
        self.decision = Decision(self.llm)
        self.action = Action(self.storage)

    def run(self, user_input: str, thread_id: str = "prod_session"):
        print(f"\n--- Agent Loop Start: '{user_input}' ---")

        perceived = self.perception.process(user_input)
        print(
            f" [Perception] Intent: {perceived.intent} | Urgency: {perceived.urgency}"
        )

        mem = self.memory.update(thread_id, user_input)
        print(f" [Memory] Summary length: {len(mem.summary)} chars")

        decision = self.decision.plan(perceived, mem)
        print(f" [Decision] Strategy: {decision.rationale}")
        print(f" [Decision] Plan: {len(decision.steps)} steps")

        results = []
        for i, step in enumerate(decision.steps):
            print(f" [Action] Step {i + 1}/{len(decision.steps)}: {step.thought}")
            res = self.action.execute(step)
            results.append(res)

        print("--- Agent Loop Complete ---\n")
        return {
            "perceived": perceived,
            "memory": mem,
            "decision": decision,
            "actions": results,
        }


if __name__ == "__main__":
    agent = Agent()
    agent.run("Find the weather in Tokyo and tell me if I need an umbrella.")
