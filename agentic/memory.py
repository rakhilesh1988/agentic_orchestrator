"""Memory service for the agentic module.

This module handles session state, durable knowledge (facts/preferences),
and artifact storage. It provides a pure service for reading and recording
information without LLM dependency.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentic.schemas import MemoryArtifact, MemoryItem

# Configuration
AGENTIC_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = AGENTIC_ROOT / "sandbox" / "artifacts"
STATE_DIR = ARTIFACTS_DIR / "state"
FAISS_THRESHOLD_KB = 4  # Default 4KB

# Ensure directories exist
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)
STATE_DIR.mkdir(exist_ok=True, parents=True)


class ArtifactStorage:
    """
    Manages saving and retrieving Pydantic-validated artifacts.

    Args:
        storage_dir (Path): The filesystem directory to store artifacts in.
        threshold_kb (int): Files larger than this will be FAISS-indexed.
    """

    def __init__(self, storage_dir: Path, threshold_kb: int = FAISS_THRESHOLD_KB):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.threshold_kb = threshold_kb

    async def save(
        self, name: str, data: Any, skip_indexing: bool = False
    ) -> tuple[Path, Optional[dict]]:
        """
        Saves raw data wrapped in a metadata envelope as a JSON artifact.
        If the data exceeds the threshold, it triggers FAISS indexing.

        Args:
            name: Logical name for the artifact.
            data: The payload to save.
            skip_indexing: If True, bypass FAISS indexing regardless of size.

        Returns:
            tuple[Path, Optional[dict]]: The path to the created JSON file and indexing result if any.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in name])
        path = self.storage_dir / f"{timestamp}_{safe_name}.json"
        index_name = f"{timestamp}_{safe_name}"

        envelope = {
            "metadata": {"name": name, "timestamp": datetime.now().isoformat()},
            "payload": data,
        }
        content = json.dumps(envelope, indent=2)
        size_kb = len(content.encode("utf-8")) / 1024

        index_res = None
        if size_kb > self.threshold_kb and not skip_indexing:
            # We calculate size_kb in-memory above before any disk write.
            # We still save the JSON file as a persistent artifact record.
            path.write_text(content, encoding="utf-8")

            # Trigger FAISS indexing (delegated to a helper to avoid circular imports)
            try:
                from mcp_server import create_faiss_index

                rel_path = str(path.relative_to(AGENTIC_ROOT / "sandbox"))
                print(
                    f" [Memory] Size {size_kb:.1f}KB > {self.threshold_kb}KB. Starting FAISS indexing for {name}..."
                )
                # Pass both the path (for metadata) and data (to avoid redundant disk read)
                index_res = await create_faiss_index(rel_path, index_name, data=data)
                if index_res.get("ok"):
                    print(
                        f" [Memory] FAISS index created: {index_res.get('index_path')}"
                    )
                else:
                    print(f" [Memory] FAISS indexing failed: {index_res.get('error')}")
            except ImportError:
                print(f" [Warning] mcp_server not found, skipping FAISS indexing.")
            except Exception as e:
                print(f" [Warning] FAISS indexing failed: {e}")
        else:
            path.write_text(content, encoding="utf-8")

        return path, index_res

    async def sync_file(self, filename: str, data: Any) -> Path:
        """
        Overwrites or creates a specific file with JSON data.
        """
        path = self.storage_dir / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path


class Memory:
    """
    Categorized memory system for the agent.
    """

    def __init__(self, threshold_kb: int = FAISS_THRESHOLD_KB):
        self.artifact_store = ArtifactStorage(ARTIFACTS_DIR, threshold_kb=threshold_kb)
        self.state_store = ArtifactStorage(STATE_DIR, threshold_kb=threshold_kb)

        self.state = MemoryArtifact()
        self.index_registry: Dict[str, str] = {}
        self._load_durable_state()
        self._load_index_registry()

    def _load_durable_state(self):
        """Loads facts and preferences from the state storage into memory."""
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

    def _load_index_registry(self):
        """Loads the registry of previously indexed files."""
        registry_path = STATE_DIR / "index_registry.json"
        if registry_path.exists():
            try:
                self.index_registry = json.loads(
                    registry_path.read_text(encoding="utf-8")
                )
            except Exception as e:
                print(f" [Warning] Could not load index registry: {e}")

    async def register_index(self, source_path: str, index_name: str):
        """
        Maps a source file path to its FAISS index name and persists it.
        """
        self.index_registry[source_path] = index_name
        await self.state_store.sync_file("index_registry.json", self.index_registry)
        print(f" [Memory] Registered index for {source_path}: {index_name}")

    def read(self, filter_kinds: Optional[List[str]] = None) -> str:
        """
        Returns a formatted string of categorized memory items.
        """
        output = []

        # Include Indexed Artifacts Registry first so Decision layer sees it immediately
        if self.index_registry:
            output.append(
                "--- PREVIOUSLY INDEXED FILES (Searchable via search_faiss_index) ---"
            )
            for source, idx in self.index_registry.items():
                output.append(f"- {source} -> Index Name: {idx}")
            output.append("")

        if not self.state.items:
            if not output:
                return "No prior history."
            return "\n".join(output)

        kinds = filter_kinds or ["fact", "preference", "tool_outcome", "scratchpad"]

        for kind in kinds:
            items = [it for it in self.state.items if it.kind == kind]
            if items:
                header = kind.replace("_", " ").upper()
                output.append(f"--- {header} ---")
                for it in items:
                    output.append(f"[{it.timestamp}] {it.content}")

        return "\n".join(output)

    async def record_item(self, content: str, kind: str):
        """
        Records a single item in memory and syncs durable items to disk.
        """
        item = MemoryItem(kind=kind, content=content)
        self.state.items.append(item)
        self.state.last_updated = datetime.now().isoformat()

        # 1. Save standard session snapshot to artifacts
        # We pass a high threshold or skip indexing for internal state to avoid noise
        await self.artifact_store.save(
            "memory_state", self.state.model_dump(), skip_indexing=True
        )

        # 2. If it's a DURABLE KIND (fact or preference), sync to the /state/ folder
        if kind in ["fact", "preference"]:
            durable_items = [
                it.model_dump()
                for it in self.state.items
                if it.kind in ["fact", "preference"]
            ]
            await self.state_store.sync_file("durable_state.json", durable_items)
            # Also save a timestamped version for history
            await self.state_store.save(f"durable_{kind}", item.model_dump())

    async def record_outcome(self, outcome_summary: str):
        """
        Convenience method to record a tool execution outcome.
        """
        await self.record_item(outcome_summary, "tool_outcome")
