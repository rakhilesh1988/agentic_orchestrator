import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentic.schemas import MemoryArtifact, MemoryItem

# Configuration
AGENTIC_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = AGENTIC_ROOT / "sandbox" / "artifacts"
STATE_DIR = ARTIFACTS_DIR / "state"

# Ensure directories exist
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)
STATE_DIR.mkdir(exist_ok=True, parents=True)


class ArtifactStorage:
    """Manages saving and retrieving Pydantic-validated artifacts."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True, parents=True)

    def save(self, name: str, data: Any) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in name])
        path = self.storage_dir / f"{timestamp}_{safe_name}.json"

        envelope = {
            "metadata": {"name": name, "timestamp": datetime.now().isoformat()},
            "payload": data,
        }
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        return path

    def sync_file(self, filename: str, data: Any) -> Path:
        """Overwrites a specific file (used for durable state like facts.json)."""
        path = self.storage_dir / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path


class Memory:
    """Axiom Memory: Stores categorized facts, preferences, outcomes, and scratchpad entries."""

    def __init__(self):
        # Two storage locations
        self.artifact_store = ArtifactStorage(ARTIFACTS_DIR)
        self.state_store = ArtifactStorage(STATE_DIR)

        self.state = MemoryArtifact()
        self._load_durable_state()

    def _load_durable_state(self):
        """Load facts and preferences from the /state/ folder into current session memory."""
        durable_path = STATE_DIR / "durable_state.json"
        if durable_path.exists():
            try:
                data = json.loads(durable_path.read_text(encoding="utf-8"))
                for item_data in data:
                    item = MemoryItem.model_validate(item_data)
                    # Add to session state if not already there
                    if item.content not in [it.content for it in self.state.items]:
                        self.state.items.append(item)
            except Exception as e:
                print(f" [Warning] Could not load durable state: {e}")

    def read(self, filter_kinds: Optional[List[str]] = None) -> str:
        """Fetch categorized context for Perception/Decision."""
        if not self.state.items:
            return "No prior history."

        output = []
        kinds = filter_kinds or ["fact", "preference", "tool_outcome", "scratchpad"]

        for kind in kinds:
            items = [it for it in self.state.items if it.kind == kind]
            if items:
                header = kind.replace("_", " ").upper()
                output.append(f"--- {header} ---")
                for it in items:
                    output.append(f"[{it.timestamp}] {it.content}")

        return "\n".join(output)

    def record_item(self, content: str, kind: str):
        """Write a categorized memory item and sync durable state to /state/."""
        item = MemoryItem(kind=kind, content=content)
        self.state.items.append(item)
        self.state.last_updated = datetime.now().isoformat()

        # 1. Save standard session snapshot to artifacts
        self.artifact_store.save("memory_state", self.state.model_dump())

        # 2. If it's a DURABLE KIND (fact or preference), sync to the /state/ folder
        if kind in ["fact", "preference"]:
            durable_items = [
                it.model_dump()
                for it in self.state.items
                if it.kind in ["fact", "preference"]
            ]
            self.state_store.sync_file("durable_state.json", durable_items)
            # Also save a timestamped version for history
            self.state_store.save(f"durable_{kind}", item.model_dump())

    def record_outcome(self, outcome_summary: str):
        """Helper for tool outcomes."""
        self.record_item(outcome_summary, "tool_outcome")
