# EAGv3: Iterative Cognitive Agent Ecosystem

A robust, self-improving AI ecosystem built on the **Axiom Architecture**. This project coordinates an intelligent agentic loop, a capability-aware routing gateway, and a versatile tool server.

## 🏗 System Architecture

The ecosystem consists of three primary layers:

1.  **Agentic Module (`/agentic`)**: The cognitive core. Implements an iterative **Perception-Memory-Decision-Action** loop. It manages goals, extracts durable knowledge, and plans tool usage.
2.  **LLM Gateway V3 (`/llm_gatewayV3`)**: The routing backbone. A FastAPI service that routes requests across multiple providers (OpenAI, Gemini, Groq, etc.) with automatic failover and cognitive-layer routing.
3.  **MCP Server (`mcp_server.py`)**: The tool repository. Provides the agent with "hands" to interact with the world (web search, browser fetching, file operations, etc.) via the Model Context Protocol.

---

## 📂 Project Structure

```text
.
├── agentic/            # Iterative Agentic Loop (Perception, Memory, Decision, Action)
├── llm_gatewayV3/      # Smart Routing Gateway (Multi-provider, RPM/TPM management)
├── sandbox/            # Secure environment for agent file operations
│   └── artifacts/      # JSON state, durable facts, and tool outputs
├── mcp_server.py       # Model Context Protocol tool definitions
├── main.py             # Simple entry point for gateway testing
└── .env                # Environment secrets (API Keys)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`

### 2. Configuration
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key (for web search)
# See .env.example for more provider keys
```

### 3. Configuration
1. **Secrets**: Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key (for web search)
# See .env.example for more provider keys
```

2. **Parameters**: Modify `parameter.yaml` to set your query and choose providers for each cognitive layer:
```yaml
query: "Search for today's top tech news."
perception:
  provider: "openai"
decision:
  provider: "openai"
```

### 4. Run the Application
You can run the entire ecosystem with a single command from the root directory. This will start the LLM Gateway, wait for it to be ready, and then trigger the agent:

```bash
python3 main.py
```

---

## 📖 Validated Test Results

Below are the results of 8 core test scenarios used to validate the iterative cognitive loop and tool integration.

### 1. Complex Fact Extraction (Web Research)
**Query**: *"Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory."*
**Result**: Claude Shannon was born on April 30, 1916, and died on February 24, 2001. Key contributions: 1) Founding information theory/entropy, 2) "A Mathematical Theory of Communication", 3) Binary data representation.

### 2. Multi-Goal Orchestration (Search + Reasoning)
**Query**: *"Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast and tell me which is most appropriate."*
**Result**: Identified Harajuku, Senso-ji, and Yoyogi Park. Recommended Harajuku for Saturday (27°C) due to its mix of indoor/outdoor options and heat manageability.

### 3. Durable Memory (Cross-Session Knowledge)
**Query (Turn 1)**: *"My mom's birthday is 15 May 2026. Remember that and create reminders."*
**Query (Turn 2)**: *"When is mom's birthday?"*
**Result**: Successfully stored the birthday and reminders as durable facts. In the second turn, the agent retrieved "15 May 2026" directly from memory state without external tools.

### 4. Search Synthesis (Best Practices)
**Query**: *"Search for Python asyncio best practices, read top 3 results, and give me a short list of advice they agree on."*
**Result**: Synthesized 7 core practices: correct async/await use, explicit task scheduling, avoiding blocking calls, using sync primitives, proper exception handling, preferring high-level APIs, and profiling.

### 5. Single-File RAG (Transformer Paper)
**Query**: *"Index papers/attention.md and tell me the three key contributions of the Transformer architecture."*
**Result**: 1) Self-attention mechanism for modeling dependencies, 2) Multi-head attention replacing RNN/CNN for parallelization, 3) Positional encoding for sequence order.

### 6. Recursive Batch Indexing
**Query**: *"Index every .md file under papers/. Confirm how many chunks were indexed in total."*
**Result**: Successfully traversed the directory and indexed 5 papers (Attention, CoT, DPO, LoRA, ReAct). Confirmed a total of 25 chunks (5 per file).

### 7. Global Multi-Index Search
**Query**: *"Across these papers, how do they handle the credit assignment problem?"*
**Result**: Utilized `search_all_indices` to synthesize approaches across the entire library: structured reasoning steps, reward propagation, CoT decomposition, and attention-based contribution weighing.

### 8. Comparative Research (ReAct vs CoT)
**Query**: *"Compare how the ReAct paper and the Chain-of-Thought paper differ in their treatment of intermediate reasoning."*
**Result**: CoT emphasizes linear sequential reasoning steps to improve accuracy; ReAct interleaves reasoning traces with actions to enable dynamic plan updates and environmental interaction.

---

## 🧠 Component Deep Dives

### [Agentic Module](./agentic/README.md)
The agent follows the **Axiom pattern**:
- **Perception**: Evaluates state and manages the goal list (Orchestrator).
- **Memory**: Stores durable facts/preferences in `/sandbox/artifacts/state/`.
- **Decision**: Selects the next tool call or provides the final answer.
- **Action**: Dispatches tools to the MCP server.

### [LLM Gateway V3](./llm_gatewayV3/README.md)
A high-performance router designed for agentic workloads:
- **Cognitive Routing**: Automatically routes based on `perception`, `memory`, or `decision` requirements.
- **Failover**: If OpenAI is down or rate-limited, it automatically falls back to Gemini, Groq, or others.
- **Schema Validation**: Ensures all LLM outputs strictly match the Pydantic models defined in the agent.

### MCP Server
Exposes a suite of tools to the agent:
- `web_search`: Multi-engine search for information gathering.
- `fetch_url`: Full-page markdown extraction via headless browser (`crawl4ai`).
- `read_file` / `create_file`: Sandbox-safe filesystem operations.
- `read_durable_state`: Direct access to the agent's long-term memory.

---

## 🛠 Features
- **Cross-Session Memory**: Facts learned today are available tomorrow.
- **Production-Ready**: Built with Pydantic v2 and FastAPI.
- **Type Safe**: Strict data contracts between all cognitive layers.
- **Observability**: Every action is saved as a JSON artifact for debugging.
