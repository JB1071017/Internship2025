from flask import Flask, render_template, request, send_file
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neural_network import MLPClassifier, MLPRegressor
import pickle
import io
import os

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    model_types = {
        'classification': {
            'random_forest': RandomForestClassifier(),
            'svm': SVC(probability=True),
            'neural_net': MLPClassifier(max_iter=1000)
        },
        'regression': {
            'random_forest': RandomForestRegressor(),
            'svm': SVR(),
            'neural_net': MLPRegressor(max_iter=1000)
        }
    }

    if request.method == 'POST':
        # Get form data
        file = request.files['file']
        target_column = request.form.get('target_column')
        problem_type = request.form.get('problem_type', 'classification')
        model_choice = request.form.get('model_type', 'random_forest')

        # Validate inputs
        if not (file and allowed_file(file.filename)):
            return render_template('index.html', error="Invalid file type. Only CSV files are allowed.",
                                 model_types=model_types.keys())

        if not target_column:
            return render_template('index.html', error="Target column not specified",
                                 model_types=model_types.keys())

        try:
            # Save and read the CSV file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            df = pd.read_csv(filepath)

            # Check if target exists
            if target_column not in df.columns:
                return render_template('index.html', error=f"Target column '{target_column}' not found",
                                     model_types=model_types.keys())

            # Preprocessing
            label_encoders = {}
            for column in df.columns:
                if df[column].dtype == 'object' and column != target_column:
                    le = LabelEncoder()
                    df[column] = le.fit_transform(df[column].astype(str))
                    label_encoders[column] = le

            # Handle target column
            if problem_type == 'classification' and df[target_column].dtype == 'object':
                le = LabelEncoder()
                df[target_column] = le.fit_transform(df[target_column])
                label_encoders[target_column] = le

            # Split data
            X = df.drop(target_column, axis=1)
            y = df[target_column]

            # Scale features for SVM and Neural Nets
            if model_choice in ['svm', 'neural_net']:
                scaler = StandardScaler()
                X = scaler.fit_transform(X)
            else:
                scaler = None

            # Train model
            model = model_types[problem_type][model_choice]
            model.fit(X, y)

            # Create model package
            model_package = {
                'model': model,
                'label_encoders': label_encoders,
                'target_column': target_column,
                'feature_columns': list(df.drop(target_column, axis=1).columns),
                'problem_type': problem_type,
                'scaler': scaler
            }

            # Create pickle file
            buffer = io.BytesIO()
            pickle.dump(model_package, buffer)
            buffer.seek(0)

            # Cleanup
            os.remove(filepath)

            return send_file(
                buffer,
                as_attachment=True,
                download_name='trained_model.pkl',
                mimetype='application/octet-stream'
            )

        except Exception as e:
            return render_template('index.html', error=f"Error: {str(e)}",
                                 model_types=model_types.keys())

    return render_template('index.html', model_types=model_types.keys())

