# Enterprise Database Activity Monitoring (DAM) System - Comprehensive Documentation

This document provides an extremely detailed, in-depth breakdown of the entire Enterprise DAM System, including the project architecture, machine learning pipeline, mathematical risk scoring models, and dataset definitions.

---

## 1. Project Architecture & File Structure

The project is built as a modular Streamlit web application. Below is the exact location of every file and its specific purpose in the ecosystem.

### 📂 Root Directory (`Final project Front end/`)
*   **`app.py`**: The main entry point and landing dashboard. It loads real-time KPIs (Total Users, Anomalous Queries, Security Events) by processing the dataset through the ML model. It serves as the navigational hub to the other modules.
*   **`requirements.txt`**: Contains all Python dependencies required to run the application (e.g., `streamlit`, `pandas`, `scikit-learn`, `plotly`, `joblib`, `reportlab`).

### 📂 `pages/` (The Frontend Dashboards)
*   **`1_User_Monitoring.py` (Organizational Risk Posture)**: Aggregates the raw event-level data into user-level risk profiles. It applies the **Dynamic Risk Scoring Algorithm** (detailed below) to categorize users into High, Medium, and Low risk. It includes distribution pie charts and a Top 5 Critical Users leaderboard.
*   **`2_Dashboard.py` (User Activity Sequence Audit)**: A deep forensic view of a specific user. It plots every query on a chronological scatter plot based on the user's timeline. It visualizes data volume (`rows_returned`) via bubble size and ML anomalies via color.
*   **`3_Alerts.py` (Security Alerts Center)**: A live feed of flagged events. It parses individual queries into `CRITICAL` or `WARNING` tiers based on specific feature combinations. It also provides the functionality to export these incidents as a PDF.

### 📂 `utils/` (Helper Functions)
*   **`data_loader.py`**: The crucial bridge between the frontend and the ML model. It exposes the `@st.cache_data` function `get_processed_data()`. This script loads the CSV file, loads the Random Forest model, drops the existing `unusual_query_flag`, and forces the data through the ML model to generate *fresh, dynamic predictions* for the flag, which are then fed to the rest of the application.
*   **`pdf_generator.py`**: Uses the `reportlab` library to programmatically generate formatting PDF compliance reports out of pandas DataFrames (used in the Alerts page).

### 📂 `model/` (Machine Learning Artifacts)
*   **`unusual_query_detector.pkl`**: The serialized (saved) Scikit-Learn `Pipeline` object containing the `ColumnTransformer` (for One-Hot Encoding) and the trained `RandomForestClassifier`.

### 📂 `scripts/` (Backend Training & Simulation)
*   **`train_new_detector.py`**: The script written to specifically ingest the `1200_rows` dataset, define the categorical/numeric features, train the Random Forest model, and export it to the `model/` directory.

### 📂 `data/` (Datasets)
*   **`unusual_query_detection_dataset_1200_rows (1).csv`**: The primary database log simulation file driving the entire application.

---

## 2. Dataset Definition

The system relies on an event-level dataset where every row represents a single database query executed by a user. 

### Data Fields Used:
1.  `event_id`: Unique identifier for the query event.
2.  `timestamp`: Datetime of the query.
3.  `user_id`: The identifier of the person executing the query (e.g., `user_01`).
4.  `user_timeline_step`: A chronological integer showing the exact sequence of the user's actions. Used in the `2_Dashboard.py` scatter plot to track behavioral flow.
5.  `table_accessed`: Categorical data (e.g., `salary`, `customers`, `finance`).
6.  `query_type`: Categorical data (e.g., `SELECT`, `UPDATE`, `DELETE`).
7.  `rows_returned`: Numeric magnitude of the query. Large numbers indicate potential bulk data access.
8.  `after_hours_access`: Binary (1/0). Identifies if the query was run outside normal business hours.
9.  `sensitive_data_access`: Binary (1/0). Identifies if the table accessed contains PII or financial data.
10. `failed_login_attempt`: Binary (1/0). Indicates if a failed login preceded the query.
11. `total_queries_session`: Numeric. The velocity/volume of queries in the current session.
12. `data_exfiltration_pattern`: Binary (1/0). A heuristic flag indicating mass data downloading (Used as an input feature for the ML model).
13. `unusual_query_flag`: The target variable. **Note:** In the live app, this column is ignored from the CSV and re-calculated dynamically by the ML model.

---

## 3. Machine Learning Architecture

The system utilizes a **Supervised Machine Learning** approach to detect anomalous database queries.

### Algorithm Used: `RandomForestClassifier`
A Random Forest was chosen because it handles a mix of categorical and numerical data exceptionally well, is robust against overfitting, and can easily capture non-linear relationships (e.g., the combination of `after_hours_access` = 1 AND `rows_returned` = 1000).

### The Training Pipeline (`scripts/train_new_detector.py`)
1.  **Feature Engineering & Preprocessing**:
    *   *Categorical Features* (`table_accessed`, `query_type`) are passed through a `OneHotEncoder`. This converts text labels into binary vectors so the math model can understand them.
    *   *Numeric Features* (`rows_returned`, `after_hours_access`, `sensitive_data_access`, `failed_login_attempt`, `total_queries_session`, `data_exfiltration_pattern`) are passed through as-is.
2.  **Model Configuration**:
    *   `n_estimators=100`: The "forest" consists of 100 individual decision trees. The final prediction (0 or 1) is determined by a majority vote from these 100 trees.
3.  **Live Prediction Workflow (`utils/data_loader.py`)**:
    *   When the Streamlit app boots, it loads the raw CSV.
    *   It extracts the feature columns and feeds them into `unusual_query_detector.pkl`.
    *   The model outputs an array of `0`s (Normal) and `1`s (Anomalous).
    *   These predictions overwrite the `unusual_query_flag` column and are propagated to every dashboard.

---

## 4. The Dynamic Risk Scoring Engine (Detailed Math)

Located in `pages/1_User_Monitoring.py`, this is the core algorithm that turns thousands of individual events into a single, understandable Risk Score (0–100) for every user.

### Step 4A: Event Aggregation
The system groups all raw events by `user_id` and sums up the bad behaviors:
*   Total ML Anomalies (`unusual_query_flag` == 1)
*   Total Failed Logins
*   Total Sensitive Table Accesses
*   Total After-Hours Accesses

### Step 4B: Relative Normalization
If we simply added these numbers, highly active users would be penalized just for working hard. To fix this, the system normalizes every user's count against the **maximum count found in the entire organization**.

*Formula:* 
`Normalized_Score = User_Count / Maximum_Organizational_Count`

### Step 4C: Weighted Final Calculation
The normalized scores (ranging from 0.0 to 1.0) are multiplied by strict organizational weights to create a score out of 100:

*   **ML Predicted Anomalies:** 50% Weight (Multiplier: 50)
*   **Failed Logins:** 20% Weight (Multiplier: 20)
*   **Sensitive Data Access:** 20% Weight (Multiplier: 20)
*   **After-Hours Access:** 10% Weight (Multiplier: 10)

*Exact Python Logic:*
```python
risk_score = (
    (norm_exfil * 35) +
    (norm_anomalies * 35) +
    (norm_logins * 15) +
    (norm_sensitive * 10) +
    (norm_after * 5)
)
```

### Step 4D: Categorization
*   **🔴 High Risk (Score > 70)**: Severe policy violators and likely insider threats.
*   **🟡 Medium Risk (Score 41 - 70)**: Users exhibiting elevated suspicious behavior requiring audit.
*   **🟢 Low Risk (Score <= 40)**: Standard operating behavior.

---

## 5. Security Alerts & Incident Logic

Located in `pages/3_Alerts.py`, this module evaluates queries on an *individual event* basis (rather than aggregated user profiles) to provide real-time alerts.

### Alert Tiering Rules:
1.  **CRITICAL Tier**:
    *   Triggered IF: The Machine Learning model predicts the query is anomalous (`unusual_query_flag == 1`).
2.  **WARNING Tier**:
    *   Triggered IF: `failed_login_attempt == 1`.
    *   Triggered IF: The user accesses sensitive data outside of business hours (`after_hours_access == 1` AND `sensitive_data_access == 1`).
    *   *(Note: The system explicitly excludes events from the Warning tier if they already qualified for the Critical tier to prevent duplicate alerts).*

---

## 6. How to Run the System

To launch the Enterprise DAM platform and view the ML model and algorithms in action:

1. Open your terminal (PowerShell, Command Prompt, or bash).
2. Navigate to the root directory of the project:
   ```bash
   cd "C:\Users\kes05\OneDrive\Desktop\Final project Front end"
   ```
3. Ensure all requirements are installed:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Streamlit server:
   ```bash
   py -m streamlit run app.py
   ```
5. The application will automatically open in your default web browser at `http://localhost:8501`.