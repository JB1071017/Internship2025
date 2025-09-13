from flask import Flask, render_template, request, jsonify
import pandas as pd
import pickle
import numpy as np
import os

app = Flask(__name__, template_folder='templates')

# Load model
def load_model():
    with open('vulan/model.pkl', 'rb') as f:
        data = pickle.load(f)
    return data['model'], data['label_encoders']

model, label_encoders = load_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    try:
        df = pd.read_csv(file)
        original_df = df.copy()

        required_cols = ['tool_name', 'vulnerability_type', 'cwe_id', 'cvss_score', 
                         'raw_severity', 'lines_in_function', 'cyclomatic_complexity',
                         'is_core_module', 'requires_auth', 'exposed_to_internet',
                         'description_length']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({'error': f'Missing columns: {", ".join(missing_cols)}'})

        for col in ['tool_name', 'vulnerability_type', 'raw_severity']:
            if col in label_encoders:
                unseen_mask = ~df[col].isin(label_encoders[col].classes_)
                if unseen_mask.any():
                    df.loc[unseen_mask, col] = 'unknown'
                    if 'unknown' not in label_encoders[col].classes_:
                        label_encoders[col].classes_ = np.append(label_encoders[col].classes_, 'unknown')
                df[col] = label_encoders[col].transform(df[col])

        predictions = model.predict(df[required_cols])
        predicted_labels = label_encoders['priority'].inverse_transform(predictions)

        original_df['predicted_priority'] = predicted_labels

        # Generate remediation plans and timelines
        results = []
        for idx, row in original_df.iterrows():
            priority = row['predicted_priority']
            vuln_type = row['vulnerability_type']
            if isinstance(vuln_type, int):
                # Reverse-transform if necessary
                vuln_type = label_encoders['vulnerability_type'].inverse_transform([vuln_type])[0]
            
            plan = generate_remediation_plan(priority, vuln_type)
            timeline = get_remediation_timeline(priority)
            
            row_data = row.to_dict()
            row_data.update({
                'remediation_plan': plan,
                'timeline': timeline
            })
            results.append(row_data)

        return jsonify({'results': results, 'status': 'success'})

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'})

def generate_remediation_plan(priority, vulnerability_type):
    plans = {
        'SQL Injection': 'Sanitize inputs, use parameterized queries, and update WAF rules.',
        'XSS': 'Escape user inputs, use CSP headers, and validate input formats.',
        'Broken Authentication': 'Enforce strong password policies, enable MFA, and rotate secrets.',
        'Insecure Deserialization': 'Avoid deserializing untrusted data and apply strict input controls.',
        'CSRF': 'Use anti-CSRF tokens, same-site cookies, and validate referrers.'
    }
    generic_plan = 'Conduct code review, apply patches, and monitor affected modules.'
    
    # Simplified rule
    if priority == 'Critical':
        return f"[IMMEDIATE] {plans.get(vulnerability_type, generic_plan)}"
    elif priority == 'High':
        return f"[URGENT] {plans.get(vulnerability_type, generic_plan)}"
    elif priority == 'Medium':
        return f"[SOON] {plans.get(vulnerability_type, generic_plan)}"
    else:
        return f"[LOW] {plans.get(vulnerability_type, generic_plan)}"

def get_remediation_timeline(priority):
    timelines = {
        'Critical': '24 hours',
        'High': '1 week',
        'Medium': '1 month',
        'Low': 'Next quarter'
    }
    return timelines.get(priority, '1 month')


