from flask import Flask, jsonify, request
import nbformat
import os
import tempfile
# Flask web server
'''Creating flask web server'''
app = Flask(__name__)
NOTEBOOK_FILE = 'test.ipynb'
# -------------------------------------------------------------------
# Helper function for safe writing 
'''Helps solve the Race condition issue whihc is solved by the Atomic Write'''
def safe_write_notebook(nb):
    '''Atomically writes a notebook to the NOTEBOOK_FILE.'''
    temp_path = ''
    try:
        # Write to a temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete = False, dir = os.path.dirname(NOTEBOOK_FILE) or '.')as f:
            nbformat.write(nb,f)
            temp_path = f.name 
            #Atomically rename the temporary file to the final destinaition
        os.rename(temp_path, NOTEBOOK_FILE)
    except Exception as e:
        # If anything fails, cleanup the temporary file and re-raise the exception
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

# -------------------------------------------------------------------
# Edit cell
'''Defining the /edit_cell endpoint'''
@app.route('/edit_cell', methods=['POST'])
def edit_cell():
    # 1. Get the data sent by AI
    data = request.get_json()
    cell_number=data.get('cell_number')
    content = data.get('content')

    # Notebook logic
    '''Core logic for edit cell in jupyter notebook'''

    # 2. Load the notebook
    try:
        with open(NOTEBOOK_FILE, 'r') as f:
            nb = nbformat.read(f, as_version = 4)

    # 3. Find the cell number and edit the content
        if 0 <= cell_number <len(nb.cells):
            nb.cells[cell_number]['source'] = content
        else:
            return jsonify({'error':'Cell number out of range'}),400

    # 4. Save the modified notebook
        '''Safely save it overwriting the old one'''
        safe_write_notebook(nb)
        return jsonify({'message':f'Received request to edit cell {cell_number} with new content'}), 200

    except Exception as e:
        return jsonify({'error':str(e)}),500
# -------------------------------------------------------------------
# Delete a cell
'''Delete a cell in jupyter notebook'''
@app.route('/delete_cell',methods=['DELETE'])
def delete_cell():
    data = request.get_json()
    cell_number = data.get('cell_number')

    try:
        # 2. load the file
        with open(NOTEBOOK_FILE, 'r') as f:
            nb = nbformat.read(f, as_version = 4)
        # 3.Delete cell
            if 0 <= cell_number < len(nb.cells):
                del nb.cells[cell_number]
            else:
                return jsonify({'error':'Cell number out of range'}),400

        #4 .Save the file with changes
        '''Safely save it overwriting the old one'''
        safe_write_notebook(nb)
        return jsonify({'message':f'Received request to delete cell {cell_number}'}), 200
    except Exception as e:
        return jsonify({'error':str(e)}), 500
# -------------------------------------------------------------
# Create a cell
'''Creating a new cell in jupyter notebook'''
@app.route('/create_cell',methods=['POST'])
def create_cell():
    data = request.get_json()
    content = data.get('content')
    cell_type = data.get('cell_type')

    try:
        # 2. load the file
        with open(NOTEBOOK_FILE, 'r') as f:
            nb = nbformat.read(f, as_version = 4)
        # 3.Create a cell
        if cell_type == 'code':
            new_cell = nbformat.v4.new_code_cell(content)
        else:
            new_cell = nbformat.v4.new_markdown_cell(content)
        nb.cells.append(new_cell)
        #4 .Save the file with changes
        '''Safely save it overwriting the old one'''
        safe_write_notebook(nb)
        return jsonify({'message':f'Received request to create cell with {content}'}), 200
    except Exception as e:
        return jsonify({'error':str(e)}), 500
# -------------------------------------------------------------------
# Move cell
'''Moves a cell in jupyter notebook'''
@app.route('/move_cell',methods=['POST'])
def move_cell():
    data = request.get_json()
    cell_number = data.get('cell_number')
    places = data.get('places')
    direction = data.get('direction')

    try:
        # 2. load the file
        with open(NOTEBOOK_FILE, 'r') as f:
            nb = nbformat.read(f, as_version = 4)
        # 3.Move cell
            original_cell = cell_number
            cell = nb.cells.pop(original_cell)
            if direction in ['up', 'upward', 'above']:
                target_cell_number = cell_number - places
            elif direction in ['down', 'downward', 'below']:
                target_cell_number = cell_number + places
            nb.cells.insert(target_cell_number, cell)

        #4 .Save the file with changes
        '''Safely save it overwriting the old one'''
        safe_write_notebook(nb)
        return jsonify({'message':f'Received request to move cell {direction} by {places} places'}), 200
    except Exception as e:
        return jsonify({'error':str(e)}), 500
# -------------------------------------------------------------
# Clear the notebook
'''Clear whole jupyter notebook'''
@app.route('/clear_cell', methods=['POST'])
def clear_cell():
    try:
    # 3.Clear notebook
        '''Create a new empty object'''
        nb = nbformat.v4.new_notebook()
        '''Safely save it overwriting the old one'''
        safe_write_notebook(nb)
        return jsonify({'message':f'Received request to clear notebook!'}), 200
    except Exception as e:
        return jsonify({'error':str(e)}), 500
# ------------------------------------------------------------
if __name__ == '__main__':
    '''Create a dummy notebook of it doesnt exist'''
    if not os.path.exists(NOTEBOOK_FILE):
        nb = nbformat.v4.new_notebook()
        nb['cells'] = [
            nbformat.v4.new_code_cell("print('Hello from cell 0')"),
            nbformat.v4.new_code_cell("print('Heloo from cell 1')")
        ]
        with open(NOTEBOOK_FILE,'w')as f:
            nbformat.write(nb, f)
        print(f"Created dummy notebook at {NOTEBOOK_FILE}")
    app.run(debug=True, port = 5001)