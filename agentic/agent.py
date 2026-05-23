import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

# Ensure project root is in sys.path so llm_gatewayV3 can be imported
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from agentic.action import Action
from agentic.decision import Decision

# Import specialized cognitive services
from agentic.memory import ArtifactStorage, Memory
from agentic.perception import Perception
from llm_gatewayV3.client import LLM


class Agent:
    """Orchestrates the iterative agent loop using specialized cognitive services."""

    def __init__(self):
        self.llm = LLM()
        self.memory = Memory()
        self.perception = Perception(self.llm)
        self.decision = Decision(self.llm)
        self.action = Action(self.memory.artifact_store)

    def _get_tools(self) -> List[Dict]:
        """Discover tools from the MCP server."""
        try:
            from mcp_server import mcp

            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in mcp._tool_manager.list_tools()
            ]
        except:
            return []

    async def run(self, query: str, max_iters: int = 10):
        print(f"\n[AGENT START] {query}\n" + "=" * 50)
        run_history = []

        for i in range(max_iters):
            print(f"\n--- Iteration {i + 1} ---")

            # 1. Read Memory
            context = self.memory.read()

            # 2. Perceive (Orchestrator: Updates Goal List & Extracts Knowledge)
            perception = self.perception.process(
                query, context, run_history=run_history
            )

            # RECORD NEW KNOWLEDGE (Facts/Preferences)
            for item in perception.new_knowledge:
                print(f" [Perception] Discovered {item.kind}: {item.content}")
                self.memory.record_item(item.content, item.kind)

            # Check if all goals are done
            unfinished = [g for g in perception.goals if not g.is_done]
            if not unfinished:
                print(" [Perception] All goals satisfied.")
                return perception.context_summary

            current_goal = unfinished[0]
            print(f" [Perception] Current Goal: {current_goal.description}")

            # 3. Decide (Pick action for the current bounded goal)
            tools = self._get_tools()
            decision = self.decision.plan(
                current_goal,
                context,
                tools,
                original_query=query,
                relevant_artifacts=perception.relevant_artifacts,
                perception_summary=perception.context_summary,
            )
            print(f" [Decision] Thought: {decision.thought}")
            run_history.append(f"Turn {i + 1} Thought: {decision.thought}")

            if decision.final_answer:
                print(f" [Decision] Goal satisfying answer generated.")
                # Record the answer as a tool outcome so Perception can mark the goal as done in the next turn
                self.memory.record_item(
                    f"Goal '{current_goal.description}' resolved: {decision.final_answer}",
                    "tool_outcome",
                )
                run_history.append(f"Turn {i + 1} Result: {decision.final_answer}")
                continue

            if decision.tool_call:
                # 4. Action (Pure Dispatch)
                tool_call = decision.tool_call
                action_res = await self.action.execute(tool_call)

                # 5. Record outcome back to Memory
                print(f" [Action] Result: {action_res.status}")
                self.memory.record_item(action_res.output_summary, "tool_outcome")
                run_history.append(
                    f"Turn {i + 1} Action: {tool_call.name} -> {action_res.status}"
                )
            else:
                # Fallback
                print(" [Decision] No action provided. Recording status to memory.")
                self.memory.record_item(
                    f"Decision for goal '{current_goal.description}' provided no action or answer.",
                    "scratchpad",
                )
                run_history.append(f"Turn {i + 1} Result: No action.")

        return "Reached maximum iterations without final answer."


# if __name__ == "__main__":
#     agent = Agent()
#     # Test query
#     query = "Search for news about Gemini 2.0 and save a fact about its release date."
#     res = asyncio.run(agent.run(query))
#     print(f"\n[FINAL RESPONSE]\n{res}")
