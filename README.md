# 🧠 AgentTool — Natural Language → Jupyter Notebook Automation

A production-minded, MCP-inspired system that converts natural language instructions into safe, deterministic Jupyter notebook operations using a local LLM.

## 🚀 Why This Project Exists

Jupyter notebooks are powerful, but programmatic control is brittle and unsafe:

- Manual edits are error-prone
- LLMs hallucinate APIs
- Notebook corruption is common
- Automation lacks guardrails

AgentTool solves this by introducing a strict, JSON-only agent layer that converts natural language into validated, executable notebook actions.

This project demonstrates:

- Agent design
- LLM safety constraints
- Deterministic execution
- Real-world system integration

## 🧩 What This Project Does

✅ Accepts natural language commands
✅ Converts them into strict JSON action plans
✅ Validates actions against allowed MCP endpoints
✅ Executes notebook operations atomically and safely
✅ Works entirely locally (no cloud dependency)

**Example:**

```
"Create a notebook and add a markdown title called Analysis"
```

➡️ Automatically creates:

```markdown
# Analysis
```

inside a `.ipynb` file — safely.

## 🏗️ High-Level Architecture

```
┌───────────────┐
│   User / CLI  │
└───────┬───────┘
        │ Natural Language
        ▼
┌────────────────────────┐
│  MCP Agent Server      │
│  (FastAPI)             │
│  - LLM prompt control  │
│  - JSON enforcement    │
│  - Action validation   │
└────────┬───────────────┘
         │ JSON Action Plan
         ▼
┌────────────────────────┐
│  MCP Jupyter Server    │
│  (Flask)               │
│  - Notebook CRUD       │
│  - Atomic writes       │
│  - File safety         │
└────────────────────────┘
```

## 📁 Project Structure

```
AgentTool/
├── mcp-agent-server/        # LLM-powered agent
│   ├── agent_server.py
│   ├── requirements.txt
│   └── ui.html
│
└── mcp-jupyter-server/      # Deterministic execution layer
    ├── server.py
    ├── requirements.txt
    ├── openai.yaml
    ├── README.md
```

## 🧠 Key Engineering Decisions (Hiring Signal)

### 1️⃣ Strict JSON Enforcement

- Agent rejects markdown, prose, or invalid JSON
- Prevents hallucinated APIs
- Guarantees machine-readable plans

### 2️⃣ Action Whitelisting

Only allowed endpoint:

```
"/create_cell"
```

No invented endpoints. No surprises.

### 3️⃣ Atomic Notebook Writes

Notebook corruption is avoided by:

- Writing to a temp file
- Replacing the original atomically

This mirrors production-grade filesystem safety.

### 4️⃣ Local-First LLM (Ollama)

- Uses Ollama with locally hosted models (e.g. `phi3:mini`, `qwen2.5:7b`)
- No external APIs
- Reproducible and privacy-safe

### 5️⃣ Framework Separation

| Layer    | Tech     | Reason                      |
|----------|----------|-----------------------------|
| Agent    | FastAPI  | Type safety, async-ready    |
| Executor | Flask    | Simple, stable file ops     |

## 🔌 MCP Agent Server (FastAPI)

### Responsibilities

- Accept user input
- Call local LLM
- Enforce JSON-only output
- Validate MCP actions
- Execute against connected MCP servers

### Run

```bash
cd mcp-agent-server
pip install -r requirements.txt
uvicorn agent_server:app --reload
```

## 📓 MCP Jupyter Server (Flask)

### Responsibilities

- Create/edit/delete/move notebook cells
- Auto-create notebooks
- Prevent file corruption
- Provide REST API for agents

### Run

```bash
cd mcp-jupyter-server
pip install -r requirements.txt
python server.py
```

Runs on: `http://localhost:5001`

## 🧪 Example End-to-End Flow

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{ "message": "Create a notebook and add a markdown title called Analysis" }'
```

**Result:**

- Notebook auto-created
- Markdown title added
- No hallucinations
- No corruption

## 🛡️ Failure Handling

| Failure          | Handling         |
|------------------|------------------|
| Invalid JSON     | Rejected         |
| Unknown endpoint | Dropped          |
| LLM timeout      | Safe error       |
| Notebook missing | Auto-created     |
| Corrupt file     | Reinitialized    |

## 📌 What This Project Demonstrates

✔ Agent design principles
✔ Safe LLM orchestration
✔ MCP-style tooling
✔ Real file system guarantees
✔ Production-thinking, not demos

## 📈 Future Extensions

- Multi-step plans
- Edit / delete / move via agent
- Notebook diff preview
- UI for live agent execution
- Streaming LLM responses

## 👩‍💻 Author

**Disha Holmukhe**
AI Systems | Agentic AI | Backend Engineering

📖 Blog:
[How I Built a Local MCP Server to Control Jupyter Notebooks](https://dishaholmukhe-jupyter-server.hashnode.dev/how-i-built-a-local-mcp-server-to-control-your-jupyter-notebooks)
