import pandas as pd
import string
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (accuracy_score, classification_report, 
                            confusion_matrix, precision_recall_curve, 
                            roc_auc_score, roc_curve)
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
import joblib
import numpy as np
import os

# ---------------------------
# 1. Load and Prepare Dataset
# ---------------------------
def load_data(filename="spam_dataset.csv"):
    df = pd.read_csv(filename)
    df['label'] = df['label'].map({'ham': 0, 'spam': 1})
    print("\nClass Distribution:")
    print(df['label'].value_counts())
    return df

# ---------------------------
# 2. Enhanced Preprocessing
# ---------------------------
stopwords = set([
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "from", "of", 
    "is", "are", "was", "were", "be", "been", "has", "have", "had", "do", 
    "does", "did", "will", "would", "can", "could", "should", "this", "that"
])

def preprocess(text):
    text = str(text).lower()
    text = ''.join([ch for ch in text if ch not in string.punctuation])
    words = text.split()
    words = [word for word in words if word not in stopwords and len(word) > 2]
    return ' '.join(words)

# ---------------------------
# 3. Feature Engineering
# ---------------------------
def create_features(df):
    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer(max_features=5000, 
                                ngram_range=(1, 2),
                                min_df=2, 
                                max_df=0.8)
    X_text = vectorizer.fit_transform(df['cleaned'])
    
    # Message length feature
    df['msg_length'] = df['cleaned'].apply(len)
    scaler = MinMaxScaler()
    length_scaled = scaler.fit_transform(df[['msg_length']])
    
    # Combine features
    X_features = np.hstack([X_text.toarray(), length_scaled])
    y = df['label'].values
    
    return X_features, y, vectorizer, scaler

# ---------------------------
# 4. Handle Class Imbalance
# ---------------------------
def balance_data(X, y):
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    return X_resampled, y_resampled

# ---------------------------
# 5. Model Training
# ---------------------------
def train_models(X_train, y_train):
    # Random Forest (better performance)
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42
    )
    rf_model.fit(X_train, y_train)
    
    return rf_model

# ---------------------------
# 6. Save Artifacts
# ---------------------------
def save_artifacts(model, vectorizer, scaler, folder="spammer"):
    # Create directory if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    
    # Save all components
    joblib.dump(model, os.path.join(folder, "model_rf.pkl"))
    joblib.dump(vectorizer, os.path.join(folder, "vectorizer.pkl"))
    joblib.dump(scaler, os.path.join(folder, "length_scaler.pkl"))
    print(f"\nAll artifacts saved to {folder} directory")

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == "__main__":
    # 1. Load data
    df = load_data("your_dataset.csv")  # Change to your filename
    
    # 2. Preprocess
    df['cleaned'] = df['message'].apply(preprocess)
    
    # 3. Create features
    X, y, vectorizer, scaler = create_features(df)
    
    # 4. Balance data
    X_resampled, y_resampled = balance_data(X, y)
    
    # 5. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_resampled, y_resampled, test_size=0.2, random_state=42, stratify=y_resampled)
    
    # 6. Train model
    model = train_models(X_train, y_train)
    
    # 7. Evaluate
    y_pred = model.predict(X_test)
    print("\nModel Evaluation:")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # 8. Save everything
    save_artifacts(model, vectorizer, scaler)
    
    print("\nModel training complete! All files generated:")
    print("- model_rf.pkl (Random Forest model)")
    print("- vectorizer.pkl (TF-IDF vectorizer)")
    print("- length_scaler.pkl (Length feature scaler)")