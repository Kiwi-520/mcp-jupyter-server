
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
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(notebook_name) or '.') as f:
            nbformat.write(nb, f)
            temp_path = f.name
        os.rename(temp_path, notebook_name)
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
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
    app.run(debug=True, port=5001)
