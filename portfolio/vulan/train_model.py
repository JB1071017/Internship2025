import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay
import xgboost as xgb
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import pickle
import os

os.makedirs('data', exist_ok=True)

def generate_remediation_plan(priority, vulnerability_type):
    plans = {
        'Critical': {
            'SQL Injection': 'Patch immediately. Apply parameterized queries. Block vulnerable endpoints if needed.',
            'XSS': 'Deploy WAF rules. Sanitize all user inputs. Emergency release required.',
            'RCE': 'Isolate affected systems. Apply patches within 24 hours.'
        },
        'High': {
            'Hardcoded Secret': 'Rotate all exposed credentials. Implement secrets management.',
            'SSRF': 'Implement network-level restrictions. Validate all URL inputs.'
        },
        'Medium': {
            'CSRF': 'Add CSRF tokens to all forms. Implement SameSite cookies.',
            'Path Traversal': 'Implement input validation. Chroot sensitive directories.'
        },
        'Low': {
            'Info Leakage': 'Review in next sprint. Add security headers.',
            'Deprecated Algorithm': 'Schedule crypto migration for next quarter.'
        }
    }
    default_plans = {
        'Critical': 'Emergency remediation required. Isolate affected components immediately.',
        'High': 'Fix within 1 week. Implement temporary mitigations.',
        'Medium': 'Address within 1 month. Include in next security sprint.',
        'Low': 'Schedule for quarterly review. Document risk acceptance if needed.'
    }
    return plans.get(priority, {}).get(vulnerability_type, default_plans[priority])

def calculate_priority(row):
    if row['cvss_score'] >= 8.5 or (row['exposed_to_internet'] and row['cvss_score'] >= 7.5):
        return 'High'
    elif row['cvss_score'] >= 5.0 or row['requires_auth'] == 0:
        return 'Medium'
    else:
        return 'Low'

def generate_better_dataset(n_samples=1000):
    np.random.seed(42)
    df = pd.DataFrame({
        'tool_name': np.random.choice(['ZAP', 'SonarQube', 'Bandit'], n_samples),
        'vulnerability_type': np.random.choice(
            ['SQL Injection', 'XSS', 'Hardcoded Secret', 'CSRF', 'RCE', 'SSRF', 'Path Traversal'], n_samples),
        'cwe_id': np.random.randint(1, 1000, n_samples),
        'cvss_score': np.round(np.random.uniform(0, 10, n_samples), 1),
        'raw_severity': np.random.choice(['Low', 'Medium', 'High', 'Critical'], n_samples),
        'lines_in_function': np.random.randint(1, 500, n_samples),
        'cyclomatic_complexity': np.random.randint(1, 50, n_samples),
        'is_core_module': np.random.choice([0, 1], n_samples),
        'requires_auth': np.random.choice([0, 1], n_samples),
        'exposed_to_internet': np.random.choice([0, 1], n_samples),
        'description_length': np.random.randint(10, 1000, n_samples),
    })

    df['priority'] = df.apply(calculate_priority, axis=1)
    return df

def preprocess_data(df):
    categorical_cols = ['tool_name', 'vulnerability_type', 'raw_severity']
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le
    priority_encoder = LabelEncoder()
    df['priority'] = priority_encoder.fit_transform(df['priority'])
    label_encoders['priority'] = priority_encoder
    return df, label_encoders

def train():
    # Step 1: Generate better dataset
    df = generate_better_dataset(1000)
    df['remediation_plan'] = df.apply(lambda x: generate_remediation_plan(x['priority'], x['vulnerability_type']), axis=1)
    df.to_csv('data/sample_dataset.csv', index=False)

    # Step 2: Preprocess
    df, label_encoders = preprocess_data(df)
    X = df.drop(['priority', 'remediation_plan'], axis=1)
    y = df['priority']

    # Step 3: Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Step 4: Apply SMOTE
    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)

    # Step 5: Train model
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Step 6: Evaluate
    y_pred = model.predict(X_test)
    y_test_labels = label_encoders['priority'].inverse_transform(y_test)
    y_pred_labels = label_encoders['priority'].inverse_transform(y_pred)

    print(f"\nAccuracy: {accuracy_score(y_test_labels, y_pred_labels):.2f}")
    print(classification_report(y_test_labels, y_pred_labels))
    ConfusionMatrixDisplay.from_predictions(y_test_labels, y_pred_labels).plot()
    plt.tight_layout()
    plt.show()

    # Step 7: Save model
    with open('data/model.pkl', 'wb') as f:
        pickle.dump({
            'model': model,
            'label_encoders': label_encoders
        }, f)

if __name__ == '__main__':
    train()
