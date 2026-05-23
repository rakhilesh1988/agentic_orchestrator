from llm_gatewayV3.client import LLM, ask

llm = LLM()  # defaults to http://localhost:8101

# 1) Plain V2-style call — no routing, no surprises
text = ask("Hello in 3 words")
text = llm.chat("Explain transformers in 2 sentences", provider="oa")["text"]
print(text)
# 2) Auto-routed call (cognitive layer = perception)
# result = llm.chat(
#     "What is the capital of France?",
#     auto_route="perception",
# )
# print(result["text"])
# print(result["router_decision"])
# {
#   "role": "perception",
#   "tier": "TINY",
#   "estimated_tokens": 15,
#   "router_provider": "cerebras",
#   "router_model": "llama3.1-8b",
#   "router_latency_ms": 84,
#   "chosen_worker_provider": "github",
#   "chosen_worker_model": "openai/gpt-4.1-mini",
#   "fallback_used": false
# }

# # 3) Memory layer routing — summarizing retrieved facts
# result = llm.chat(
#     f"Summarize for relevance to '{query}':\n\n{retrieved_chunk}",
#     auto_route="memory",
# )

# # 4) Decision layer routing — planning the next step
# result = llm.chat(
#     plan_state_serialized,
#     auto_route="decision",
# )

# # 5) Explicit provider beats auto_route (debugging escape hatch)
# result = llm.chat(
#     "Hello",
#     auto_route="perception",  # logged but ignored
#     provider="g",  # gemini wins
# )
# assert result["router_decision"] is None

# # 6) All V2 features still work — tools, caching, reasoning, structured output
# result = llm.chat(
#     messages=[{"role": "user", "content": "What is 7+5? Use the add tool."}],
#     tools=[
#         {
#             "name": "add",
#             "description": "a+b",
#             "input_schema": {
#                 "type": "object",
#                 "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
#                 "required": ["a", "b"],
#             },
#         }
#     ],
#     tool_choice="auto",
#     auto_route="decision",  # routes via cognitive-layer hint
# )
