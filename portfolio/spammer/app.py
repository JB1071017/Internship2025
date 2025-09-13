from flask import Flask, render_template, request, jsonify
import joblib
import string
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from nltk.corpus import stopwords
try:
    stopwords = set(stopwords.words('english')) | set(string.punctuation)
except LookupError:
    nltk.download('stopwords')
    stopwords = set(stopwords.words('english')) | set(string.punctuation)

app = Flask(__name__, template_folder='templates')

# Load the model, vectorizer, and scaler
model = joblib.load("spammer/model_rf.pkl")  # Changed to RF model
vectorizer = joblib.load("spammer/vectorizer.pkl")
scaler = joblib.load("spammer/length_scaler.pkl")  # Added length scaler

# Setup NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Enhanced preprocessing (keep your existing stopwords list)
stemmer = PorterStemmer()


def enhanced_preprocess(text):
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)


    
    try:
        tokens = word_tokenize(text)
    except:
        tokens = text.split()
    
    tokens = [stemmer.stem(word) for word in tokens if word not in stopwords and len(word) > 2]
    return ' '.join(tokens)

def prepare_features(text):
    cleaned_message = enhanced_preprocess(text)
    print(f"Cleaned message: {cleaned_message}")  # Debug print
    
    text_features = vectorizer.transform([cleaned_message])
    print(f"Text features shape: {text_features.shape}")  # Debug print
    
    msg_length = len(cleaned_message)
    print(f"Message length: {msg_length}")  # Debug print
    
    scaled_length = scaler.transform([[msg_length]])
    print(f"Scaled length: {scaled_length}")  # Debug print
    
    features = np.hstack([text_features.toarray(), scaled_length])
    return features

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        # Handle both form submission and AJAX request
        if request.is_json:
            data = request.get_json()
            message = data['message']
        else:
            message = request.form['message']
        
        # Prepare features with message length
        features = prepare_features(message)
        
        # Make prediction
        prediction = model.predict(features)
        probability = model.predict_proba(features)[0][1] if hasattr(model, "predict_proba") else None
        
        result = "Spam" if prediction[0] == 1 else "Not Spam"
        
        response = {
            'message': message,
            'result': result,
            'prediction': int(prediction[0]),
            'probability': float(probability) if probability is not None else None
        }
        
        if request.is_json:
            return jsonify(response)
        else:
            return render_template('index.html', 
                                show_result=True,
                                input_message=message,
                                result=result,
                                prediction=int(prediction[0]),
                                probability=probability)

@app.route('/check', methods=['POST'])
def check():
    # API endpoint for AJAX calls
    data = request.get_json()
    message = data['message']
    
    features = prepare_features(message)
    prediction = model.predict(features)
    probability = model.predict_proba(features)[0][1] if hasattr(model, "predict_proba") else None
    
    return jsonify({
        'prediction': int(prediction[0]),
        'probability': float(probability) if probability is not None else None,
        'message': message,
        'result': "Spam" if prediction[0] == 1 else "Not Spam"
    })