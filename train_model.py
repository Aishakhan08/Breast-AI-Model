import numpy as np
import joblib


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

print("Loading dataset...")

import pandas as pd

# Load CSV dataset
df = pd.read_csv("data.csv")

if "Unnamed: 32" in df.columns:
    df = df.drop(columns=["Unnamed: 32"])

# Remove ID column (if present)
if "id" in df.columns:
 df = df.drop(columns=["id"])

# Convert diagnosis to numbers
# M = Malignant (1), B = Benign (0)
df["diagnosis"] = df["diagnosis"].map({
    "M": 1,
    "B": 0
})

# Features and Target
X = df.drop("diagnosis", axis=1)
y = df["diagnosis"]
X = df.drop("diagnosis", axis=1)
y = df["diagnosis"]

print(X.columns.tolist())
print(len(X.columns))

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Scaling...")

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

print("Training model...")

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

print("Predicting...")

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("ROC AUC:", roc_auc_score(y_test, y_prob))
print(classification_report(y_test, y_pred))

joblib.dump(model, "breast_cancer_model.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(list(X.columns), "feature_names.pkl")

print("MODEL SAVED ✔")