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

### 3. Start the LLM Gateway
The gateway must be running for the agent to function.
```bash
cd llm_gatewayV3
./run.sh
```
*Gateway runs on `http://localhost:8101`*

### 4. Run the Agent
Execute the iterative loop from the root directory:
```bash
python3 agentic/agent.py
```

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
