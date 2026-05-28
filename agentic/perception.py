"""Perception service for the agentic module.

This module acts as the orchestrator for the cognitive loop. It breaks down
user queries into discrete goals and evaluates when those goals have been
satisfied based on memory and action history.
"""

import json
from typing import Dict, List, Optional

from pydantic import ValidationError

from agentic.schemas import Goal, MemoryItem, PerceptionResult
from llm_gatewayV3.client import LLM


class Perception:
    """
    The orchestrator of the cognitive cycle.

    Responsible for goal management, knowledge extraction, and high-level
    state summarization using the LLM.
    """

    def __init__(self, llm: LLM, provider: str = "openai"):
        self.llm = llm
        self.provider = provider

    def process(
        self, query: str, memory_context: str, run_history: List[str] = None
    ) -> PerceptionResult:
        """
        Processes the current state to update goals and extract knowledge.

        Args:
            query (str): The original user query.
            memory_context (str): Categorized memory content from the Memory service.
            run_history (Optional[List[str]]): Chronological thoughts and action
                summaries from the current loop execution.

        Returns:
            PerceptionResult: Updated goal list and discovered facts/preferences.
        """
        history_str = ""
        if run_history:
            history_str = "\nCHRONOLOGICAL RUN HISTORY:\n- " + "\n- ".join(run_history)

        prompt = (
            f"USER QUERY: {query}\n\n"
            f"{history_str}\n\n"
            f"CURRENT CATEGORIZED MEMORY:\n{memory_context}"
        )

        try:
            # Using gpt-4.1-mini tier for better orchestration and goal evaluation.
            result = self.llm.chat(
                prompt=prompt,
                system=(
                    "You are the Perception layer (The Orchestrator). Your job is to manage the GOAL LIST, extract KNOWLEDGE, and summarize STATE.\n\n"
                    "GOAL RULES:\n"
                    "1. BREAKDOWN: Break the query into logical steps. If it has multiple parts (e.g., 'Do X then Y'), emit separate goals.\n"
                    "2. NO SKIPPING: Do NOT mark a goal as 'is_done' unless you see the SPECIFIC tool output in the Memory. Do NOT assume a future action will be done.\n"
                    "3. PERSISTENCE: Maintain the same goal list across turns. Update 'is_done' status based on tool outcomes in Memory.\n"
                    "VERIFICATION: \n"
                    "   - INDEX goals: Must see 'FAISS index created' in Memory OR the file must be listed in 'PREVIOUSLY INDEXED FILES'.\n"
                    "   - READ/FETCH goals: Must see the content snippet in Memory.\n"
                    "   - RESEARCH goals: Use 'search_all_indices' for broad or 'across papers' questions to save turns.\n"
                    "5. TRACK ARTIFACTS: \n"
                    "   - In the 'goals' list, include the 'artifact_path' for completed goals.\n"
                    "   - In the 'relevant_artifacts' list, include ONLY the paths of artifacts that have been successfully INDEXED (i.e., you see 'FAISS index created' in Memory OR it is in 'PREVIOUSLY INDEXED FILES'). Use the 'Index Name' from the registry for previously indexed files.\n\n"
                    "KNOWLEDGE & STATE RULES:\n"
                    "6. TERMINATION: ONLY mark all goals 'is_done': true when the USER QUERY is fully satisfied by the Memory.\n"
                    "7. FINAL ANSWER: Provide the comprehensive answer in 'context_summary' ONLY when all goals are done.\n"
                    "8. STATE SUMMARY: If goals are pending, use 'context_summary' to summarize progress.\n"
                    "9. EXTRACTION: Identify new durable FACTS or PREFERENCES and add to 'new_knowledge'.\n\n"
                    "EXAMPLES:\n"
                    '- First turn: {"goals": [{"description": "Index A", "is_done": false}, {"description": "Summarize", "is_done": false}], "context_summary": "Starting task."}\n'
                    '- Progress: {"goals": [{"description": "Index A", "is_done": true, "artifact_path": "artifacts/A.json"}, {"description": "Summarize", "is_done": false}], "context_summary": "A is indexed."}\n'
                    '- Final: {"goals": [{"description": "Index A", "is_done": true}, {"description": "Summarize", "is_done": true}], "context_summary": "The final answer is..."}'
                ),
                response_format={
                    "type": "json_schema",
                    "schema": PerceptionResult.model_json_schema(),
                },
                provider=self.provider,
                temperature=1.0,
            )

            if result.get("parsed"):
                return PerceptionResult.model_validate(result["parsed"])

            # Robustly extract JSON from markdown blocks if present
            text = result["text"].strip()
            if text.startswith("```"):
                import re

                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                if match:
                    text = match.group(1).strip()

            return PerceptionResult.model_validate_json(text)
        except Exception as e:
            if hasattr(e, "response") and e.response is not None:
                print(
                    f" [Error] Perception Gateway returned {e.response.status_code}: {e.response.text}"
                )
            return PerceptionResult(
                goals=[Goal(description=query)], context_summary=f"Error: {e}"
            )
