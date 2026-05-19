import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

df = pd.read_csv('data/unusual_query_detection_dataset_1200_rows (1).csv')
X = df.drop(columns=['event_id', 'timestamp', 'user_id', 'user_timeline_step', 'unusual_query_flag'])
y = df['unusual_query_flag']

categorical_features = ['table_accessed', 'query_type']
numeric_features = ['rows_returned', 'after_hours_access', 'sensitive_data_access', 'failed_login_attempt', 'total_queries_session', 'data_exfiltration_pattern']

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ],
    remainder='passthrough'
)

model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

model.fit(X, y)
os.makedirs('model', exist_ok=True)
joblib.dump(model, 'model/unusual_query_detector.pkl')
print('Model trained and saved!')
