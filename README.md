# 🚀 MCP Jupyter Server

A RESTful API server for managing Jupyter notebooks programmatically. Create, edit, delete, and move cells in Jupyter notebooks using simple HTTP requests.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [API Endpoints](#api-endpoints)
- [Testing with cURL](#testing-with-curl)
- [Examples](#examples)
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
