"""Decision service for the agentic module.

This module picks the single next action (tool call or final answer) for a
bounded goal, ensuring logical progression and avoiding redundant operations.
"""

import json
from typing import Dict, List, Optional

from agentic.schemas import DecisionResult, Goal
from llm_gatewayV3.client import LLM


class Decision:
    """
    Action selector for specific agent goals.

    Evaluates the current goal against memory and perception summaries to
    determine if a tool call is needed or if the goal can be satisfied.
    """

    def __init__(self, llm: LLM, provider: str = "openai"):
        self.llm = llm
        self.provider = provider

    def plan(
        self,
        goal: Goal,
        memory_context: str,
        tools: List[Dict],
        original_query: str = "",
        relevant_artifacts: List[str] = None,
        perception_summary: str = "",
    ) -> DecisionResult:
        """
        Picks the next action for a specific bounded goal.

        Args:
            goal (Goal): The specific goal being addressed in this turn.
            memory_context (str): Formatted memory content.
            tools (List[Dict]): List of available MCP tools.
            original_query (str): The full original request from the user.
            relevant_artifacts (Optional[List[str]]): List of raw data addresses.
            perception_summary (str): Reasoning and state summary from Perception.

        Returns:
            DecisionResult: The chosen tool call or final answer string.
        """
        artifacts_info = ""
        if relevant_artifacts:
            artifacts_info = (
                "INDEXED & SEARCHABLE ARTIFACTS (Use 'search_faiss_index' for these):\n- "
                + "\n- ".join(relevant_artifacts)
            )

        prompt = (
            f"Original User Request: {original_query}\n"
            f"Current Focused Goal: {goal.description}\n\n"
            f"PERCEPTION SUMMARY (The Orchestrator's View):\n{perception_summary}\n\n"
            f"{artifacts_info}\n\n"
            f"CURRENT CATEGORIZED MEMORY:\n{memory_context}\n\n"
            f"Available Tools:\n{json.dumps(tools, indent=2)}"
        )

        try:
            # Using temperature=1.0 for better compatibility with structured output on some providers.
            result = self.llm.chat(
                prompt=prompt,
                system=(
                    "You are the Decision layer. Pick the NEXT ACTION for the current goal.\n\n"
                    "RULES:\n"
                    "1. VECTOR SEARCH: If you need information from indexed files:\n"
                    "   - For a SPECIFIC file, use 'search_faiss_index' with its unique Index Name.\n"
                    "   - For research ACROSS multiple papers or general questions, you MUST use 'search_all_indices' to save iterations. This is much faster than searching one by one.\n"
                    "2. LOCAL KNOWLEDGE: If the info is personal or about the session, use 'read_durable_state'.\n"
                    "3. ESCALATION: Use 'web_search' ONLY if the information is not in any indexed artifact or durable state.\n"
                    "4. ACT, DON'T CHAT: If you need a tool, you MUST return a 'tool_call'. Do NOT provide a 'final_answer' saying you will use a tool.\n"
                    "5. FORMAT: You must return valid JSON with either 'tool_call' OR 'final_answer'.\n\n"
                    "EXAMPLES:\n"
                    '- Tool Call: {"tool_call": {"name": "search_faiss_index", "arguments": {"query": "transformer birth", "index_name": "20260527_102030_raw_output_read_file"}}, "thought": "Searching local index for transformer info."}\n'
                    '- Final Answer: {"final_answer": "The answer is X.", "thought": "Found the answer in memory."}'
                ),
                response_format={
                    "type": "json_schema",
                    "schema": DecisionResult.model_json_schema(),
                },
                provider=self.provider,
                temperature=1.0,
            )

            if not result or ("text" not in result and "parsed" not in result):
                raise ValueError("LLM Gateway returned an empty or invalid response")

            if result.get("parsed"):
                decision = DecisionResult.model_validate(result["parsed"])
            else:
                # Robustly extract JSON from markdown blocks if present (client-side fallback)
                text = result["text"].strip()
                if text.startswith("```"):
                    import re

                    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                    if match:
                        text = match.group(1).strip()
                decision = DecisionResult.model_validate_json(text)

            # Prevent empty decisions
            if not decision.tool_call and not decision.final_answer:
                raise ValueError(
                    "LLM returned an empty decision (no tool_call or final_answer)"
                )

            return decision

        except Exception as e:
            print(f" [Decision DEBUG] Error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(
                    f" [Error] Decision Gateway returned {e.response.status_code}: {e.response.text}"
                )
            return DecisionResult(
                final_answer=f"Decision Error: {e}",
                thought="Fallback due to error.",
            )
