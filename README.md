# 🛡️ Enterprise Database Activity Monitoring (DAM) System

## 🌟 Overview
The **Enterprise DAM System** is a high-performance, real-time security platform designed to detect **Insider Threats** and monitor database activities using Machine Learning and Behavioral Analytics. It provides security teams with actionable insights into user behavior, identifies anomalies in query patterns, and generates comprehensive risk profiles for every user within the ecosystem.

## 🚀 Key Features
- **Real-Time Data Pipeline**: A backend pipeline that continually parses simulated PostgreSQL database logs and pushes them into an ML inference engine.
- **ML-Powered Detection**: A Custom `RandomForestClassifier` trained specifically to detect unusual query patterns and exfiltration risks on the fly.
- **Live Dashboards**: A suite of Streamlit interfaces completely uncoupled from hardcoded variables, capable of dynamically generating insights, scatter plot timelines, and risk distributions from the incoming data stream.
- **Risk Scoring Engine**: A relative normalization algorithm that creates a 0-100 organizational risk score by weighing different behavioral and ML-flagged actions.
- **FastAPI Backend (Optional)**: A dedicated REST API capable of serving real-time alerts and user threat profiles to external SIEMs or security tools.
- **Compliance Reporting**: One-click generation of PDF security audit reports for management and regulatory compliance.

## 🛠️ Tech Stack
- **Frontend / Visualization**: [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Machine Learning**: [Scikit-Learn](https://scikit-learn.org/) (Random Forest Pipeline)
- **Backend / Pipeline**: [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (SQLite integration)
- **Reporting**: [ReportLab](https://www.reportlab.com/) (PDF Generation)

## 📁 Project Structure
```text
Final project Front end/
├── app.py                     # Main Streamlit dashboard & entry point
├── requirements.txt           # Python dependencies
├── backend/
│   ├── generate_logs.py       # Simulates real-time PostgreSQL database traffic
│   ├── pipeline.py            # Parses logs, runs ML inference, saves to SQLite
│   └── api.py                 # FastAPI service serving alerts & user audits
├── data/
│   ├── raw_logs.csv           # Initial static dataset (legacy/backup)
│   └── unusual_query...csv    # Training / Static reference dataset
├── model/
│   └── unusual_query_detector.pkl  # Trained Random Forest ML pipeline
├── pages/
│   ├── 1_Dashboard.py         # User Activity Sequence Audit (Forensic view)
│   ├── 2_User_Monitoring.py   # Global Risk Posture (Organizational heatmap)
│   └── 3_Alerts.py            # ML Security Alerts Center (Real-time flags)
├── scripts/
│   └── train_new_detector.py  # Script used to train the current ML model
└── utils/
    ├── data_loader.py         # Dynamic bridge reading from SQLite database
    └── pdf_generator.py       # PDF reporting logic
```

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Final project Front end"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Running the Real-Time System

To experience the full power of the real-time ML pipeline, you need to run the backend generators alongside the frontend.

**Step 1: Start the Database Log Generator**
This script simulates a live PostgreSQL server, writing query logs to `backend/logs/postgresql.log`.
```bash
py backend/generate_logs.py
```
*(Leave this running in Terminal Window 1)*

**Step 2: Start the ML Inference Pipeline**
This script continuously reads the new logs, extracts features, pushes them through the Machine Learning model, and saves the results to a local `security_monitoring.db` database.
```bash
py backend/pipeline.py
```
*(Leave this running in Terminal Window 2)*

**Step 3: Launch the Monitoring Dashboard**
Start the main Streamlit interface. It automatically polls the live database every few seconds to give you real-time security insights.
```bash
py -m streamlit run app.py
```
*(Runs in Terminal Window 3 - opens in your web browser)*

---

### (Optional) Running the REST API
If you want to connect external security tools (like a SIEM) to the ML engine, you can start the FastAPI server:
```bash
py backend/api.py
```
*   **Swagger Docs**: Available at `http://localhost:8000/docs`
*   **Get Active Alerts**: `GET /suspicious_queries`
*   **Get User Profile**: `GET /users/{user_id}/audit`

## 📊 Modules
### 1. Main Hub (`app.py`)
The central cockpit showing live system health, total users monitored, and top-level ML anomalies.

### 2. Security Overview (`2_User_Monitoring.py`)
A bird's-eye view of the organization's risk posture. Includes risk distribution charts and a dynamic leaderboard of high-risk users calculated relative to the organization's worst offenders.

### 3. Behavioral Analysis (`1_Dashboard.py`)
Detailed forensic view of individual users. Features interactive scatter plots mapping exact query sequences over time, with red flags explicitly marking where the ML engine detected a threat.

### 4. Alerts & Reporting (`3_Alerts.py`)
Lists all critical and warning-level incidents based on real-time ML predictions and behavioral rules. Allows security officers to download a professional **Security Incident Report** in PDF format.

## 🛡️ Security Disclaimer
This system is a monitoring and detection tool designed for demonstration and internal auditing. Ensure proper legal authorization before monitoring user activities in a production environment.