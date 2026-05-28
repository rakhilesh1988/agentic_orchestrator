"""Action service for the agentic module.

This module handles the execution of MCP tools and the management of
tool-specific artifacts. It provides a bridge between the cognitive
Decision layer and the physical tool environment.
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from agentic.memory import Memory

from agentic.schemas import ActionResponse, ToolCall


class Action:
    """
    Dispatcher and executor for MCP tools.

    Handles tool discovery, asynchronous execution, and raw data persistence
    using ArtifactStorage.
    """

    def __init__(self, memory: "Memory"):
        self.memory = memory
        self.storage = memory.artifact_store

    async def execute(self, tool_call: ToolCall) -> ActionResponse:
        """
        Executes a specific tool call and records the outcome.

        Args:
            tool_call (ToolCall): The tool name and arguments.

        Returns:
            ActionResponse: Status, raw output, and a short summary.
        """
        print(f"  >> Executing [{tool_call.name}]...")

        # Real MCP tool discovery and execution
        try:
            from mcp_server import mcp

            # Find the tool in the manager
            tool = next(
                (t for t in mcp._tool_manager.list_tools() if t.name == tool_call.name),
                None,
            )
            if not tool:
                return ActionResponse(
                    status="failure",
                    output_summary=f"Tool '{tool_call.name}' not found.",
                )

            # Execute (handles both sync and async tools)
            raw_res = tool.fn(**tool_call.arguments)
            if asyncio.iscoroutine(raw_res):
                raw_res = await raw_res

            # Save raw output to artifact store
            # Skip indexing for tools that don't produce primary knowledge or are recursive (like search)
            skip_indexing = tool_call.name in [
                "search_faiss_index",
                "list_dir",
                "get_time",
                "read_durable_state",
                "currency_convert",
            ]
            path, index_res = await self.storage.save(
                f"raw_output_{tool_call.name}", raw_res, skip_indexing=skip_indexing
            )

            # Create short descriptor for memory
            # Use sandbox-relative path for tool outcomes so read_file works correctly
            rel_path = f"artifacts/{path.name}"
            content_snippet = ""
            if isinstance(raw_res, (str, list, dict)):
                raw_str = str(raw_res)
                content_snippet = (
                    f"\nContent Snippet (first 1000 chars): {raw_str[:1000]}..."
                )

            indexing_info = ""
            if index_res:
                if index_res.get("ok"):
                    index_name = Path(index_res.get("index_path")).stem
                    indexing_info = (
                        f" FAISS index created at {index_res.get('index_path')}."
                    )
                    # Register the index in the persistent registry
                    # Try to find the original source path
                    source = tool_call.arguments.get("path")
                    if not source and isinstance(raw_res, dict):
                        source = raw_res.get("source")

                    if source:
                        await self.memory.register_index(str(source), index_name)
                else:
                    indexing_info = f" FAISS indexing failed: {index_res.get('error')}."

            summary = (
                f"Executed {tool_call.name}. Result length: {len(str(raw_res))} chars. "
                f"Full result stored in {rel_path}.{indexing_info}{content_snippet}"
            )

            return ActionResponse(
                status="success",
                output_summary=summary,
                artifact_path=str(path),
                raw_output=raw_res,
            )
        except Exception as e:
            return ActionResponse(
                status="failure", output_summary=f"Execution error: {e}"
            )
