# AgentTool Project - Complete Documentation

**Created:** January 13, 2026
**Location:** `c:\Users\disha\Disha\Projects\AgentTool`

---

## 📁 Project Structure

```
AgentTool/
├── mcp-agent-server/
│   ├── agent_server.py
│   ├── requirements.txt
│   ├── ui.html
│   └── __pycache__/
│
└── mcp-jupyter-server/
    ├── server.py
    ├── requirements.txt
    ├── openai.yaml
    ├── README.md
    ├── .gitignore
    └── .git/
```

---

## 📄 File Contents

---

### 1. mcp-agent-server/agent_server.py

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-agent-server\agent_server.py`

```python
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
```

---

### 2. mcp-agent-server/requirements.txt

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-agent-server\requirements.txt`

```
fastapi
uvicorn
requests
```

---

### 3. mcp-agent-server/ui.html

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-agent-server\ui.html`

```html
(Empty file)
```

---

### 4. mcp-jupyter-server/server.py

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-jupyter-server\server.py`

```python

from flask import Flask, jsonify, request
import nbformat
import os
import tempfile

# Flask web server
app = Flask(__name__)

# --- Helper Functions ---

def get_or_create_notebook(notebook_name):
    """Reads a notebook file. If it doesn't exist, creates a valid, empty one."""
    if not os.path.exists(notebook_name):
        print(f"Notebook '{notebook_name}' not found. Creating a new one.")
        nb = nbformat.v4.new_notebook()
        with open(notebook_name, 'w') as f:
            nbformat.write(nb, f)

    with open(notebook_name, 'r') as f:
        try:
            return nbformat.read(f, as_version=4)
        except nbformat.reader.NotJSONError:
            print(f"Warning: '{notebook_name}' is empty or corrupted. Initializing a new notebook.")
            nb = nbformat.v4.new_notebook()
            return nb

def safe_write_notebook(nb, notebook_name):
    """Atomically writes a notebook to the specified file."""
    temp_path = ""
    try:
        notebook_dir = os.path.dirname(notebook_name) or '.'
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=notebook_dir, suffix='.ipynb') as f:
            nbformat.write(nb, f)
            temp_path = f.name

        if os.path.exists(notebook_name):
            os.remove(notebook_name)

        os.rename(temp_path, notebook_name)
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise e

# --- API Endpoints ---

@app.route('/create_cell', methods=['POST'])
def create_cell():
    try:
        data = request.get_json()
        if not data or 'notebook_name' not in data or 'cell_type' not in data or 'content' not in data:
            return jsonify({'error': 'Missing notebook_name, cell_type, or content'}), 400

        notebook_name = data['notebook_name']
        cell_type = data['cell_type']
        content = data['content']

        nb = get_or_create_notebook(notebook_name)

        if cell_type == 'code':
            new_cell = nbformat.v4.new_code_cell(content)
        elif cell_type == 'markdown':
            new_cell = nbformat.v4.new_markdown_cell(content)
        else:
            return jsonify({'error': 'Invalid cell_type. Must be "code" or "markdown"'}), 400

        nb.cells.append(new_cell)

        safe_write_notebook(nb, notebook_name)
        return jsonify({'message': f'Cell created successfully in {notebook_name}', 'total_cells': len(nb.cells)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit_cell', methods=['POST'])
def edit_cell():
    try:
        data = request.get_json()
        if not data or 'notebook_name' not in data or 'cell_number' not in data or 'content' not in data:
            return jsonify({'error': 'Missing notebook_name, cell_number, or content'}), 400

        notebook_name = data['notebook_name']
        cell_number = data['cell_number']
        content = data['content']

        nb = get_or_create_notebook(notebook_name)

        if not isinstance(cell_number, int) or not (0 <= cell_number < len(nb.cells)):
            return jsonify({'error': f'Cell number {cell_number} is out of range for {notebook_name}'}), 400

        nb.cells[cell_number]['source'] = content

        safe_write_notebook(nb, notebook_name)
        return jsonify({'message': f'Cell {cell_number} in {notebook_name} edited successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_cell', methods=['POST'])
def delete_cell():
    try:
        data = request.get_json()
        if not data or 'notebook_name' not in data or 'cell_number' not in data:
            return jsonify({'error': 'Missing notebook_name or cell_number'}), 400

        notebook_name = data['notebook_name']
        cell_number = data['cell_number']

        nb = get_or_create_notebook(notebook_name)

        if not isinstance(cell_number, int) or not (0 <= cell_number < len(nb.cells)):
            return jsonify({'error': f'Cell number {cell_number} is out of range for {notebook_name}'}), 400

        nb.cells.pop(cell_number)

        safe_write_notebook(nb, notebook_name)
        return jsonify({'message': f'Cell {cell_number} deleted from {notebook_name}', 'total_cells': len(nb.cells)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/move_cell', methods=['POST'])
def move_cell():
    try:
        data = request.get_json()
        if not data or 'notebook_name' not in data or 'cell_number' not in data or 'direction' not in data:
            return jsonify({'error': 'Missing notebook_name, cell_number, or direction'}), 400

        notebook_name = data['notebook_name']
        cell_number = data['cell_number']
        direction = data['direction']
        places = data.get('places', 1)

        nb = get_or_create_notebook(notebook_name)

        if not isinstance(cell_number, int) or not (0 <= cell_number < len(nb.cells)):
            return jsonify({'error': 'Cell number out of range or invalid'}), 400
        if not isinstance(places, int) or places < 1:
            return jsonify({'error': 'Places must be a positive integer'}), 400

        cell_to_move = nb.cells.pop(cell_number)
        new_pos = -1
        if direction == 'up':
            new_pos = max(0, cell_number - places)
        elif direction == 'down':
            new_pos = min(len(nb.cells), cell_number + places)
        else:
            return jsonify({'error': 'Invalid direction. Must be "up" or "down"'}), 400

        nb.cells.insert(new_pos, cell_to_move)
        safe_write_notebook(nb, notebook_name)
        return jsonify({'message': f'Cell {cell_number} moved {direction} to position {new_pos}'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_all', methods=['POST'])
def clear_all():
    try:
        data = request.get_json()
        if not data or 'notebook_name' not in data:
            return jsonify({'error': 'Missing notebook_name'}), 400

        notebook_name = data['notebook_name']
        nb = nbformat.v4.new_notebook()
        safe_write_notebook(nb, notebook_name)
        return jsonify({'message': f'All cells cleared successfully from {notebook_name}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, port=5001, use_reloader = False)

```

---

### 5. mcp-jupyter-server/requirements.txt

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-jupyter-server\requirements.txt`

```
attrs==25.4.0
blinker==1.9.0
click==8.3.0
fastjsonschema==2.21.2
Flask==3.1.2
gunicorn==23.0.0
itsdangerous==2.2.0
Jinja2==3.1.6
jsonschema==4.25.1
jsonschema-specifications==2025.9.1
jupyter_core==5.9.1
MarkupSafe==3.0.3
nbformat==5.10.4
packaging==25.0
platformdirs==4.5.0
referencing==0.37.0
rpds-py==0.28.0
traitlets==5.14.3
typing_extensions==4.15.0
Werkzeug==3.1.3

```

---

### 6. mcp-jupyter-server/openai.yaml

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-jupyter-server\openai.yaml`

```yaml
openapi: 3.0.0
info:
  title: Local Jupyter Notebook Server
  version: 2.0.0
  description: An API to programmatically control local Jupyter Notebook files.
paths:
  /create_cell:
    post:
      summary: Creates a new cell in a specified notebook.
      description: If the notebook does not exist, it will be created.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                notebook_name:
                  type: string
                  description: "The path to the notebook file (e..g, 'my_notebook.ipynb')."
                content:
                  type: string
                  description: "The content for the new cell."
                cell_type:
                  type: string
                  description: "Type of cell to create ('code' or 'markdown')."
                  default: 'code'
              required:
                - notebook_name
                - content
      responses:
        '200':
          description: Cell created successfully

  /edit_cell:
    post:
      summary: Edits a cell in a specified notebook.
      description: If the notebook does not exist, it will be created.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                notebook_name:
                  type: string
                  description: "The path to the notebook file."
                cell_number:
                  type: integer
                  description: "The index of the cell to edit."
                content:
                  type: string
                  description: "The new content for the cell."
              required:
                - notebook_name
                - cell_number
                - content
      responses:
        '200':
          description: Cell edited successfully

  /delete_cell:
    delete: # <-- This is changed to DELETE to match your server code
      summary: Deletes a cell from a specified notebook.
      description: This will return an error if the notebook does not exist.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                notebook_name:
                  type: string
                  description: "The path to the notebook file."
                cell_number:
                  type: integer
                  description: "The index of the cell to delete."
              required:
                - notebook_name
                - cell_number
      responses:
        '200':
          description: Cell deleted successfully

  /move_cell:
    post:
      summary: Moves a cell up or down in a specified notebook.
      description: This will return an error if the notebook does not exist.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                notebook_name:
                  type: string
                  description: "The path to the notebook file."
                cell_number:
                  type: integer
                  description: "The index of the cell to move."
                direction:
                  type: string
                  description: "Direction to move ('up' or 'down')."
                places:
                  type: integer
                  description: "Number of places to move the cell."
                  default: 1
              required:
                - notebook_name
                - cell_number
                - direction
      responses:
        '200':
          description: Cell moved successfully

  /clear_notebook:
    post:
      summary: Deletes all cells in a specified notebook.
      description: This will overwrite the file with a new, empty notebook.
      requestBody: # <-- This was added
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                notebook_name:
                  type: string
                  description: "The path to the notebook file to clear."
              required:
                - notebook_name
      responses:
        '200':
          description: Notebook cleared successfully
```

---

### 7. mcp-jupyter-server/.gitignore

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-jupyter-server\.gitignore`

```
# Virtual Environment
venv/

# Python cache
__pycache__/
*.pyc

# IDE / Editor specific
.vscode/
.idea/
```

---

### 8. mcp-jupyter-server/README.md

**Location:** `c:\Users\disha\Disha\Projects\AgentTool\mcp-jupyter-server\README.md`

````markdown
# 🚀 MCP Jupyter Server

A MCP server for managing Jupyter notebooks programmatically. Create, edit, delete, and move cells in Jupyter notebooks using simple HTTP requests.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Testing with cURL](#testing-with-curl)
- [Examples](#examples)
- [Checkout my article for detailed tutorial](#checkout-my-article-for-detailed-tutorial)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **Create Cells**: Add code or markdown cells to notebooks
- **Edit Cells**: Modify existing cell content
- **Delete Cells**: Remove cells from notebooks
- **Move Cells**: Reorder cells within notebooks
- **Clear All**: Remove all cells from a notebook
- **Auto-create**: Automatically creates notebooks if they don't exist
- **Safe Writing**: Uses atomic file operations to prevent corruption

## 📦 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- curl (for testing)

## 🔧 Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/Kiwi-520/mcp-jupyter-server.git
cd mcp-jupyter-server
```

### 2. (Optional) Create a Virtual Environment

It's recommended to use a virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- nbformat (Jupyter notebook format handler)
- gunicorn (production WSGI server)
- And other dependencies

## 🚀 Running the Server

### Development Mode

```bash
python server.py
```

The server will start on `http://localhost:5001` with debug mode enabled.

### Production Mode (with Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5001 server:app
```

You should see output like:
```
 * Running on http://127.0.0.1:5001
 * Debug mode: on
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create_cell` | POST | Create a new cell in a notebook |
| `/edit_cell` | POST | Edit an existing cell |
| `/delete_cell` | POST | Delete a cell from a notebook |
| `/move_cell` | POST | Move a cell up or down |
| `/clear_all` | POST | Remove all cells from a notebook |

## 🧪 Testing with cURL

Below are comprehensive examples for testing each endpoint using curl commands.

### 1. Create a Code Cell

```bash
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_type": "code",
    "content": "print(\"Hello, World!\")"
  }'
```

**Expected Response:**
```json
{
  "message": "Cell created successfully in test.ipynb",
  "total_cells": 1
}
```

### 2. Create a Markdown Cell

```bash
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_type": "markdown",
    "content": "# My Notebook\nThis is a markdown cell."
  }'
```

**Expected Response:**
```json
{
  "message": "Cell created successfully in test.ipynb",
  "total_cells": 2
}
```

### 3. Edit a Cell

Edit the cell at index 0 (first cell):

```bash
curl -X POST http://localhost:5001/edit_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_number": 0,
    "content": "print(\"Updated Hello, World!\")"
  }'
```

**Expected Response:**
```json
{
  "message": "Cell 0 in test.ipynb edited successfully"
}
```

### 4. Delete a Cell

Delete the cell at index 1 (second cell):

```bash
curl -X POST http://localhost:5001/delete_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_number": 1
  }'
```

**Expected Response:**
```json
{
  "message": "Cell 1 deleted from test.ipynb",
  "total_cells": 1
}
```

### 5. Move a Cell

Move cell at index 2 down by 1 position:

```bash
curl -X POST http://localhost:5001/move_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_number": 2,
    "direction": "down",
    "places": 1
  }'
```

Move cell at index 1 up by 1 position:

```bash
curl -X POST http://localhost:5001/move_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_number": 1,
    "direction": "up",
    "places": 1
  }'
```

**Expected Response:**
```json
{
  "message": "Cell 1 moved up to position 0"
}
```

### 6. Clear All Cells

Remove all cells from a notebook:

```bash
curl -X POST http://localhost:5001/clear_all \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb"
  }'
```

**Expected Response:**
```json
{
  "message": "All cells cleared successfully from test.ipynb"
}
```

## 📚 Examples

### Complete Workflow Example

Here's a complete example that creates a notebook with multiple cells:

```bash
# 1. Create a markdown title cell
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "demo.ipynb",
    "cell_type": "markdown",
    "content": "# Data Analysis Demo"
  }'

# 2. Create a code cell to import libraries
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "demo.ipynb",
    "cell_type": "code",
    "content": "import pandas as pd\nimport numpy as np"
  }'

# 3. Create another code cell
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "demo.ipynb",
    "cell_type": "code",
    "content": "data = pd.DataFrame({\"A\": [1, 2, 3], \"B\": [4, 5, 6]})\nprint(data)"
  }'

# 4. Create a markdown cell for notes
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "demo.ipynb",
    "cell_type": "markdown",
    "content": "## Analysis Results\nThe data shows..."
  }'
```

### Error Handling Examples

**Invalid cell type:**
```bash
curl -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_type": "invalid",
    "content": "test"
  }'
```

**Response:**
```json
{
  "error": "Invalid cell_type. Must be \"code\" or \"markdown\""
}
```

**Out of range cell number:**
```bash
curl -X POST http://localhost:5001/edit_cell \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_name": "test.ipynb",
    "cell_number": 999,
    "content": "test"
  }'
```

**Response:**
```json
{
  "error": "Cell number 999 is out of range for test.ipynb"
}
```

## Checkout my article for detailed tutorial 😊

[How I Built a Local MCP Server to Control Your Jupyter Notebooks](https://dishaholmukhe-jupyter-server.hashnode.dev/how-i-built-a-local-mcp-server-to-control-your-jupyter-notebooks)


## 🔍 Troubleshooting

### Server Won't Start

**Issue:** `Address already in use`

**Solution:** Another process is using port 5001. Either kill that process or change the port:
```bash
# Change port in server.py (last line)
app.run(debug=True, port=5002)  # Use different port

# Or find and kill the process
lsof -ti:5001 | xargs kill -9
```

### Module Not Found Error

**Issue:** `ModuleNotFoundError: No module named 'flask'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Permission Errors

**Issue:** Cannot write to notebook file

**Solution:** Ensure you have write permissions in the directory:
```bash
chmod 755 .
chmod 644 *.ipynb
```

### JSON Parsing Errors

**Issue:** `400 Bad Request` with JSON error

**Solution:** Ensure your JSON is properly formatted. Use `-v` flag with curl to see the full error:
```bash
curl -v -X POST http://localhost:5001/create_cell \
  -H "Content-Type: application/json" \
  -d '{"notebook_name": "test.ipynb", "cell_type": "code", "content": "print(123)"}'
```

## 🛠️ Development

### Project Structure

```
mcp-jupyter-server/
├── server.py           # Main Flask application
├── server2.py          # Additional server (if needed)
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── main.ipynb         # Sample notebook
├── test.ipynb         # Test notebook
└── openai.yaml        # Configuration file
```

### Adding New Features

The server is built with Flask and follows a simple structure. To add new endpoints:

1. Define a new route in `server.py`
2. Add appropriate error handling
3. Use `get_or_create_notebook()` and `safe_write_notebook()` helpers
4. Test with curl commands

## 📝 API Request/Response Reference

### Create Cell

**Request:**
```json
{
  "notebook_name": "string (required)",
  "cell_type": "code|markdown (required)",
  "content": "string (required)"
}
```

**Response (Success - 200):**
```json
{
  "message": "string",
  "total_cells": number
}
```

### Edit Cell

**Request:**
```json
{
  "notebook_name": "string (required)",
  "cell_number": number (required, 0-indexed),
  "content": "string (required)"
}
```

**Response (Success - 200):**
```json
{
  "message": "string"
}
```

### Delete Cell

**Request:**
```json
{
  "notebook_name": "string (required)",
  "cell_number": number (required, 0-indexed)
}
```

**Response (Success - 200):**
```json
{
  "message": "string",
  "total_cells": number
}
```

### Move Cell

**Request:**
```json
{
  "notebook_name": "string (required)",
  "cell_number": number (required, 0-indexed),
  "direction": "up|down (required)",
  "places": number (optional, default: 1)
}
```

**Response (Success - 200):**
```json
{
  "message": "string"
}
```

### Clear All

**Request:**
```json
{
  "notebook_name": "string (required)"
}
```

**Response (Success - 200):**
```json
{
  "message": "string"
}
```

### Error Response (4xx/5xx)

```json
{
  "error": "string"
}
```
**Happy Coding! 🎉**

````

---

## 🔍 Project Overview

### MCP Agent Server

The **MCP Agent Server** is a FastAPI-based application that acts as a client agent for the Model Context Protocol (MCP). Key features:

- **LLM Integration**: Uses Ollama with the `phi3:mini` model
- **JSON Plan Generation**: Converts natural language to structured actions
- **MCP Server Connection**: Manages connections to MCP servers
- **Action Execution**: Executes notebook cell creation actions

**Dependencies:**
- fastapi
- uvicorn
- requests

**Configuration:**
- Ollama URL: `http://localhost:11434/api/generate`
- Model: `phi3:mini`
- Port: Not specified in code (default FastAPI)

### MCP Jupyter Server

The **MCP Jupyter Server** is a Flask-based REST API for programmatic Jupyter notebook management. Key features:

- **Cell Management**: Create, edit, delete, and move cells
- **Notebook Operations**: Auto-create notebooks, clear all cells
- **Safe Operations**: Atomic file writes to prevent corruption
- **API Endpoints**: RESTful interface for all operations

**Dependencies:**
- Flask==3.1.2
- nbformat==5.10.4
- gunicorn==23.0.0
- And 17 other dependencies

**Configuration:**
- Port: `5001`
- Debug: `False`
- Reloader: `False`

---

## 🚀 How to Run

### Running MCP Agent Server

```bash
cd mcp-agent-server
pip install -r requirements.txt
uvicorn agent_server:app --reload
```

### Running MCP Jupyter Server

```bash
cd mcp-jupyter-server
pip install -r requirements.txt
python server.py
```

Or with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5001 server:app
```

---

## 📊 Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Agent Server   │  ← Processes natural language
│  (FastAPI)      │  ← Calls Ollama LLM
└────────┬────────┘
         │ JSON Plan
         v
┌─────────────────┐
│ Jupyter Server  │  ← Executes notebook operations
│  (Flask)        │  ← Manages .ipynb files
└─────────────────┘
```

---

## 📝 Notes

- The `ui.html` file appears to contain only text (dependencies) rather than actual HTML markup
- The project uses two different web frameworks: FastAPI for the agent server and Flask for the Jupyter server
- Both servers are designed to run on localhost
- The agent server requires Ollama to be running on port 11434

---

**End of Documentation**
