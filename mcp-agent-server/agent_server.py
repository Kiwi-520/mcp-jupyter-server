from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import re

app = FastAPI()

# ---------------- CONFIG ----------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3:mini"   # IMPORTANT: stable on Windows

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are an MCP client agent.

Return ONLY valid JSON.
NO markdown, NO explanations, NO code fences.

Allowed endpoints:
- /create_cell

JSON format:
{
  "actions": [
    {
      "endpoint": "/create_cell",
      "method": "POST",
      "payload": {
        "notebook_name": "example.ipynb",
        "cell_type": "markdown",
        "content": "# Title"
      }
    }
  ]
}

Rules:
- Always include notebook
- Use markdown for titles
- Do NOT invent endpoints
"""



# ---------------- SCHEMAS ----------------
class ChatRequest(BaseModel):
    message: str

class ConnectRequest(BaseModel):
    server_url: str

# ---------------- STATE ----------------
CONNECTED_MCP_SERVER: list[str] = []

# ---------------- UTILS ----------------
def clean_llm_json(text: str) -> dict:
    """
    Remove markdown fences but keep JSON content
    """

    # Remove ```json or ``` fences only
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()

    # Extract first JSON object
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("No JSON object found")

    return json.loads(match.group())

def normalize_plan(plan: dict) -> dict:
    """Force MCP-compatible actions"""
    actions = []
    for act in plan.get("actions", []):
        if act.get("endpoint") != "/create_cell":
            continue

        payload = act.get("payload", {})
        payload.setdefault("notebook_name", "example.ipynb")
        payload.setdefault("cell_type", "markdown")
        payload.setdefault("content", "# Untitled")

        actions.append({
            "endpoint": "/create_cell",
            "method": "POST",
            "payload": payload
        })

    if not actions:
        raise ValueError("No valid MCP actions found")

    return {"actions": actions}

# ---------------- ROUTES ----------------
@app.get("/")
def health():
    return {"status": "agent running"}

@app.post("/connect")
def connect(req: ConnectRequest):
    if req.server_url not in CONNECTED_MCP_SERVER:
        CONNECTED_MCP_SERVER.append(req.server_url)
    return {"connected": req.server_url, "servers": CONNECTED_MCP_SERVER}

@app.post("/chat")
def chat(req: ChatRequest):
    if not CONNECTED_MCP_SERVER:
        return {"error": "No MCP servers connected"}

    try:
        llm = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": SYSTEM_PROMPT + "\nUser request:\n" + req.message,
                "stream": False
            },
            timeout=120
        )
        llm.raise_for_status()
    except Exception as e:
        return {"error": "Ollama call failed", "details": str(e)}

    raw_text = llm.json().get("response", "")

    try:
        plan = clean_llm_json(raw_text)
        plan = normalize_plan(plan)
    except Exception as e:
        return {
            "error": "Invalid JSON from model",
            "reason": str(e),
            "raw_response": raw_text
        }

    server = CONNECTED_MCP_SERVER[0]
    results = []

    for action in plan["actions"]:
        try:
            r = requests.post(
                f"{server}{action['endpoint']}",
                json=action["payload"],
                timeout=10
            )
            results.append({
                "endpoint": action["endpoint"],
                "status": r.status_code,
                "response": r.json()
            })
        except Exception as e:
            results.append({"endpoint": action["endpoint"], "error": str(e)})

    return {"plan": plan, "results": results}
