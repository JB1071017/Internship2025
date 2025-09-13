AI-Powered Interactive Circuit Builder (Flask Web App)
Here's a complete Flask web application that integrates AI-powered circuit generation with an interactive interface. This solution combines Gemini API for circuit design, LangChain for structured output, and SchemDraw for rendering.

Directory Structure
text
circuit-builder/
│
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── script.js       # Frontend interactivity
│
├── templates/
│   ├── base.html           # Base template
│   └── index.html          # Main page template
│
├── utils/
│   ├── circuit_generator.py # AI circuit generation logic
│   └── diagram_renderer.py  # Schematic drawing functions
│
└── uploads/                # Generated circuit images
Complete Code Implementation
1. requirements.txt
text
flask>=2.0.0
google-generativeai>=0.3.0
langchain>=0.1.0
schemdraw>=0.14.0
pillow>=9.0.0
python-dotenv>=0.19.0
waitress>=2.1.0
2. config.py
python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
3. app.py
python
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from utils.circuit_generator import generate_circuit_design
from utils.diagram_renderer import render_circuit_diagram
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        description = request.form.get('circuit_description')
        if not description:
            return jsonify({'error': 'No description provided'}), 400
            
        try:
            # Step 1: Generate circuit design with AI
            circuit_data = generate_circuit_design(description)
            
            # Step 2: Render the circuit diagram
            filename = render_circuit_diagram(circuit_data, app.config['UPLOAD_FOLDER'])
            
            return jsonify({
                'success': True,
                'image_url': f'/uploads/{filename}',
                'circuit_data': circuit_data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
4. utils/circuit_generator.py
python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
import json
from config import Config

def generate_circuit_design(description):
    # Define the expected response schema
    component_schema = ResponseSchema(
        name="components",
        description="List of circuit components with their properties"
    )
    connection_schema = ResponseSchema(
        name="connections",
        description="List of connections between components"
    )
    response_schemas = [component_schema, connection_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    
    # Create the prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert electrical engineer. Design circuits based on user requests.
        Return a JSON with components and connections. Components should include:
        - type (resistor, capacitor, IC, etc.)
        - id (unique identifier)
        - value (if applicable)
        - other relevant properties"""),
        ("human", "{input}"),
    ])
    
    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=Config.GEMINI_API_KEY,
        temperature=0.7
    )
    
    # Create and run the chain
    chain = prompt_template | llm | output_parser
    output = chain.invoke({"input": description})
    
    return output
5. utils/diagram_renderer.py
python
import schemdraw
import schemdraw.elements as elm
import os
import uuid
from PIL import Image

# Component mapping
COMPONENT_MAP = {
    'resistor': elm.Resistor,
    'capacitor': elm.Capacitor,
    'inductor': elm.Inductor,
    'diode': elm.Diode,
    'led': elm.LED,
    'transistor': elm.BjtNpn,
    'opamp': elm.Opamp,
    'ic': elm.Ic,
    'motor': elm.Motor,
    'switch': elm.Switch,
    'ground': elm.Ground,
    'battery': elm.BatteryCell,
    'potentiometer': elm.Potentiometer,
    'sensor': elm.Sensor
}

def render_circuit_diagram(circuit_data, output_dir):
    d = schemdraw.Drawing()
    components = {}
    
    # Add components
    for comp in circuit_data['components']:
        comp_type = comp['type'].lower()
        element_class = COMPONENT_MAP.get(comp_type, elm.Element)
        element = element_class()
        
        # Set common properties
        if 'label' in comp:
            element.label(comp['label'])
        elif 'id' in comp:
            element.label(comp['id'])
            
        if 'value' in comp:
            element.label(f"{element.label.text}\n{comp['value']}")
            
        components[comp['id']] = element
    
    # Add connections
    for conn in circuit_data.get('connections', []):
        if len(conn) >= 2 and conn[0] in components and conn[1] in components:
            d += components[conn[0]]
            d += components[conn[1]]
    
    # Save the diagram
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(output_dir, filename)
    d.save(filepath)
    
    # Convert to PNG and optimize
    img = Image.open(filepath)
    img.save(filepath, optimize=True, quality=85)
    
    return filename
6. templates/base.html
html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Circuit Builder</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
7. templates/index.html
html
{% extends "base.html" %}

{% block content %}
<div class="row mt-5">
    <div class="col-md-8 mx-auto">
        <h1 class="text-center mb-4">AI Circuit Builder</h1>
        
        <div class="card shadow">
            <div class="card-body">
                <form id="circuitForm">
                    <div class="mb-3">
                        <label for="circuitDescription" class="form-label">Describe your circuit:</label>
                        <textarea class="form-control" id="circuitDescription" rows="3" 
                            placeholder="e.g., 'Build a 555 timer circuit that blinks an LED every second'"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Generate Circuit</button>
                </form>
            </div>
        </div>
        
        <div id="loadingSpinner" class="text-center mt-4 d-none">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Generating your circuit...</p>
        </div>
        
        <div id="resultContainer" class="mt-4 d-none">
            <div class="card shadow">
                <div class="card-header">
                    <h5>Generated Circuit</h5>
                </div>
                <div class="card-body text-center">
                    <img id="circuitImage" src="" class="img-fluid" alt="Generated Circuit">
                </div>
            </div>
        </div>
        
        <div id="errorContainer" class="alert alert-danger mt-4 d-none"></div>
    </div>
</div>
{% endblock %}
8. static/js/script.js
javascript
document.getElementById('circuitForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const description = document.getElementById('circuitDescription').value.trim();
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    // Reset UI
    resultContainer.classList.add('d-none');
    errorContainer.classList.add('d-none');
    loadingSpinner.classList.remove('d-none');
    
    try {
        const response = await fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'circuit_description': description
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Display the result
        document.getElementById('circuitImage').src = data.image_url;
        resultContainer.classList.remove('d-none');
        
    } catch (error) {
        errorContainer.textContent = error.message;
        errorContainer.classList.remove('d-none');
    } finally {
        loadingSpinner.classList.add('d-none');
    }
});
9. static/css/style.css
css
body {
    background-color: #f8f9fa;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.card {
    border-radius: 10px;
}

#circuitImage {
    max-height: 500px;
    width: auto;
    border: 1px solid #dee2e6;
    border-radius: 5px;
}

textarea {
    resize: vertical;
    min-height: 100px;
}
How to Run the Application
Create a .env file in the root directory with your Gemini API key:

text
GEMINI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
Install dependencies:

bash
pip install -r requirements.txt
Run the application:

bash
python app.py
Access the application at http://localhost:5000

Features
AI-Powered Circuit Design:

Users describe circuits in natural language

Gemini API generates structured circuit data

Interactive Schematic Generation:

Automatic rendering of circuit diagrams

Supports common electronic components

Responsive Web Interface:

Clean, mobile-friendly design

Real-time feedback during generation

Error Handling:

Graceful handling of invalid inputs

User-friendly error messages

Deployment Options
Render (Recommended for simplicity):

Push to GitHub and connect to Render

Add environment variables in Render dashboard

Heroku:

bash
heroku create
git push heroku main
PythonAnywhere:

Upload files via web interface

Configure WSGI file

This complete solution provides a production-ready web application that combines AI-powered circuit design with interactive visualization.

