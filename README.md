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
**Iterations**: 4
**Result**: Claude Shannon was born on April 30, 1916, and died on February 24, 2001. Key contributions: 1) Founding information theory/entropy, 2) "A Mathematical Theory of Communication", 3) Binary data representation.
**Actual Terminal Output**: 
> Claude Shannon was born on April 30, 1916, and died on February 24, 2001. He is known as the father of information theory and made several key contributions including: 1) Developing information entropy as a measure of information content and uncertainty reduction in messages; 2) Publishing the foundational 1948 paper "A Mathematical Theory of Communication" which laid the groundwork of modern information theory; 3) Being the first to describe the use of binary digits (bits) for data representation and communication, forming the basis of digital circuits and computing.

### 2. Multi-Goal Orchestration (Search + Reasoning)
**Query**: *"Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast and tell me which is most appropriate."*
**Iterations**: 4
**Result**: Identified Harajuku, Senso-ji, and Yoyogi Park. Recommended Harajuku for Saturday (27°C) due to its mix of indoor/outdoor options and heat manageability.
**Actual Terminal Output**:
> The user asked for 3 family-friendly things to do in Tokyo this weekend and the Saturday weather forecast to select the most appropriate activity. The three recommended activities are:
> 1. Harajuku: shopping and cultural experience on Takeshita Street with options to be indoors or shaded, suitable for warm weather around 27°C.
> 2. Senso-ji Temple: requires significant outdoor walking, better during cooler parts of the day.
> 3. Yoyogi Park: outdoor play and picnics but higher risk of overheating for children in warm and potentially humid conditions.
> Given the forecast of up to 27°C on Saturday, the Harajuku outing is the most appropriate for a family-friendly activity due to its flexible mix of indoor and outdoor options, making it manageable despite the warm weather.

### 3. Durable Memory (Cross-Session Knowledge)
**Query (Turn 1)**: *"My mom's birthday is 15 May 2026. Remember that and create reminders."*
**Query (Turn 2)**: *"When is mom's birthday?"*
**Iterations**: 4 (Turn 1) + 1 (Turn 2)
**Result**: Successfully stored the birthday and reminders as durable facts. In the second turn, the agent retrieved "15 May 2026" directly from memory state without external tools.
**Actual Terminal Output (Turn 1)**:
> Reminders have been successfully created for your mom's birthday: one on 1 May 2026 (two weeks before) and one on the actual birthday on 15 May 2026.
**Actual Terminal Output (Turn 2)**:
> Mom's birthday is on 15 May 2026.

### 4. Search Synthesis (Best Practices)
**Query**: *"Search for Python asyncio best practices, read top 3 results, and give me a short list of advice they agree on."*
**Iterations**: 6
**Result**: Synthesized 7 core practices: correct async/await use, explicit task scheduling, avoiding blocking calls, using sync primitives, proper exception handling, preferring high-level APIs, and profiling.
**Actual Terminal Output**:
> The search for Python asyncio best practices has been completed successfully with the top 3 results read and analyzed. The common advice they agree on has been summarized into a short numbered list:
> 1. Use async/await properly, understanding that async functions are not inherently concurrent and coroutines generally run in code order.
> 2. Leverage asyncio tasks to schedule and manage concurrent execution explicitly.
> 3. Avoid blocking calls inside async functions to maintain event loop responsiveness.
> 4. Use asyncio's built-in synchronization primitives (locks, events) as needed.
> 5. Properly handle exceptions within async code.
> 6. Prefer higher-level asyncio APIs and libraries over manual event loop management.
> 7. Regularly test and profile async code for performance and concurrency issues.

### 5. Single-File RAG (Transformer Paper)
**Query**: *"Index papers/attention.md and tell me the three key contributions of the Transformer architecture."*
**Iterations**: 3
**Result**: 1) Self-attention mechanism for modeling dependencies, 2) Multi-head attention replacing RNN/CNN for parallelization, 3) Positional encoding for sequence order.
**Actual Terminal Output**:
> The file papers/attention.md is already indexed. The three key contributions of the Transformer architecture according to this paper are: 1) The introduction of the self-attention mechanism that allows modeling of dependencies without regard to their distance in the input or output sequences. 2) The replacement of recurrent and convolutional layers with multi-head self-attention and position-wise fully connected layers, enabling more parallelization and reducing training times. 3) The use of positional encoding to inject information about the order of the sequence, compensating for the lack of recurrence or convolution.

### 6. Recursive Batch Indexing
**Query**: *"Index every .md file under papers/. Confirm how many chunks were indexed in total."*
**Iterations**: 7
**Result**: Successfully traversed the directory and indexed 5 papers (Attention, CoT, DPO, LoRA, ReAct). Confirmed a total of 25 chunks (5 per file).
**Actual Terminal Output**:
> All .md files under papers/ directory (attention.md, cot.md, dpo.md, lora.md, react.md) were successfully indexed. Each file was split into 5 chunks before indexing. Therefore, the total number of chunks indexed is 25 (5 files x 5 chunks each).

### 7. Global Multi-Index Search
**Query**: *"Across these papers, how do they handle the credit assignment problem?"*
**Iterations**: 4
**Result**: Utilized `search_all_indices` to synthesize approaches across the entire library: structured reasoning steps, reward propagation, CoT decomposition, and attention-based contribution weighing.
**Actual Terminal Output**:
> The synthesis of how the credit assignment problem is handled across the indexed papers is complete. Approaches vary from structured reasoning steps explicitly tracking contributions, reinforcement learning style reward propagation, use of chain-of-thought prompting to decompose tasks, and architectural mechanisms like attention to weigh input contributions. The common theme is breaking outputs into interpretable components and assigning credit based on their causal influence.

### 8. Comparative Research (ReAct vs CoT)
**Query**: *"Compare how the ReAct paper and the Chain-of-Thought paper differ in their treatment of intermediate reasoning."*
**Iterations**: 4
**Result**: CoT emphasizes linear sequential reasoning steps to improve accuracy; ReAct interleaves reasoning traces with actions to enable dynamic plan updates and environmental interaction.
**Actual Terminal Output**:
> Completed extraction of relevant details on intermediate reasoning from both the ReAct paper and the Chain-of-Thought (CoT) paper. The ReAct paper integrates intermediate reasoning traces interleaved with actions, enabling the model to update action plans and handle exceptions dynamically. In contrast, the Chain-of-Thought paper focuses on generating a linear series of intermediate reasoning steps to improve complex reasoning performance. The comparison highlights ReAct's interleaved reasoning and acting approach versus CoT's sequential intermediate reasoning steps.

### 9. Rocketlane Knowledge Retrieval: Inviting Teams
**Query**: *"Across the indexed indices/.markdown_files.faiss, search the CONTENT and give the steps to invite teams to Rocketlane."*
**Iterations**: 3
**Actual Terminal Output**:
> Found detailed steps to invite team members to a project in Rocketlane from the search across all indices. Steps include selecting the project, clicking 'Invite' from the top-right corner, adding team members by searching their names within the organization or adding external members via email ids, and recognizing project owner by a Crown icon next to their name.

### 10. Rocketlane Knowledge Retrieval: Creating Projects
**Query**: *"Across the indexed indices/.markdown_files.faiss, search the CONTENT and give the steps to create a rocketlane project."*
**Iterations**: 3
**Actual Terminal Output**:
> The search across all indices returned a detailed list of steps to create a Rocketlane project including pressing 'N', typing task name, choosing project, adding assignees, due date, task description, and options for creating tasks (public/private).

### 11. Rocketlane Knowledge Retrieval: Adding Documents
**Query**: *"Across the indexed indices/.markdown_files.faiss, search the CONTENT and give the steps to add a document to a rocketlane project."*
**Iterations**: 4
**Actual Terminal Output**:
> The query to find steps to add a document to a Rocketlane project was performed by searching across all indices. The steps identified are:
> 1. Use a Template: Select an existing document template to standardize your document format.
> 2. Rocketlane Documents: Create collaborative shared private and shared documents accessible to project team members.

### 12. Rocketlane Knowledge Retrieval: Task Creation
**Query**: *"Across the indexed indices/.markdown_files.faiss, search the CONTENT and give the steps to create a task in a rocketlane project."*
**Iterations**: 3
**Actual Terminal Output**:
> The search across all indexed indices found relevant content describing the steps to create a task in a Rocketlane project. The steps include pressing key 'N' while logged in, typing a task name and choosing a project, adding assignees, due date, and description, selecting create options for public or private tasks, and then the task is created and opened.

### 13. Rocketlane Knowledge Retrieval: Workflow Automations
**Query**: *"Across the indexed indices/.markdown_files.faiss, search the CONTENT and give the steps to create workflow automations in a rocketlane project."*
**Iterations**: 4
**Actual Terminal Output**:
> The detailed steps to create workflow automations in a Rocketlane project include accessing the workflow automation feature, planning based on project needs and plan type, setting parent task status updates, defining trigger conditions, specifying actions, testing automations, and ongoing monitoring and refinement.

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
