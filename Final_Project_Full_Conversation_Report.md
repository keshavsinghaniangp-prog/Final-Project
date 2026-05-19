
# Final Project Development & Conversation Report

This document serves as a complete record of the development journey, technical decisions, and conversational milestones for the **Enterprise Database Activity Monitoring (DAM) System**.

---

## 📅 Project Timeline & Milestones

### Phase 1: Foundation & Skeletal Setup
*   **Initialization**: Established the root structure of the Streamlit application. Created the entry point (`app.py`) and the initial organizational pages (`Dashboard`, `User Monitoring`, `Alerts`).
*   **Static Mocking**: Initially built the UI using simulated/random data to establish the look and feel of the "Enterprise Security" theme.

### Phase 2: Data Integration & ML Evolution
*   **Dataset Migration**: Successfully transitioned from dummy data to a provided 1,200-row event-level dataset (`unusual_query_detection_dataset_1200_rows (1).csv`).
*   **ML Implementation**:
    *   Initially explored `IsolationForest` and `LocalOutlierFactor`.
    *   Ultimately trained and deployed a robust **Random Forest Classifier** (`unusual_query_detector.pkl`) to handle the complex mix of categorical and numerical security features.
*   **Feature Engineering**: Developed logic to extract security indicators such as `after_hours_access`, `sensitive_data_access`, and `data_exfiltration_pattern`.

### Phase 3: Transition to Real-Time Architecture
*   **Log Simulation**: Created `backend/generate_logs.py` to simulate a live PostgreSQL server writing raw text logs.
*   **The Pipeline**: Developed `backend/pipeline.py` using the `watchdog` library to "tail" logs in real-time, perform ML inference on every new line, and store results in a SQLite database (`security_monitoring.db`).
*   **The REST API**: Built a FastAPI service (`backend/api.py`) to provide a standardized JSON interface for security alerts and user audits.

### Phase 4: Dynamic UI & High-Resolution Auditing
*   **Removing Hardcoding**: Modified all front-end scripts to dynamically detect columns. The app now auto-discovers User IDs, Anomaly Flags, and Resource columns directly from the data headers.
*   **Forensic Audit**: Built the interactive scatter plot timeline in `pages/1_Dashboard.py` to map specific user sequences and data volumes.
*   **Interactive Input**: Created `pages/4_Query_Console.py`, allowing users to manually type SQL and see the ML pipeline react instantly.

---

## 🛠 Technical Logic Breakdown

### 1. Machine Learning
*   **Model**: Random Forest Classifier (100 Trees).
*   **Input Features**: 8 dimensions (Table, Query Type, Rows, Time, Sensitivity, Failed Logins, Session Vol, Exfil Patterns).
*   **Normalization**: Used `StandardScaler` for density-based features and `OneHotEncoder` for strings.

### 2. Risk Scoring Algorithm
*   **Formula**: `(Norm_Anomaly * 50) + (Norm_Logins * 20) + (Norm_Sensitive * 20) + (Norm_AfterHours * 10)`.
*   **Relative Normalization**: Scores are calculated relative to the "worst offender" currently in the database to prevent activity-volume bias.

---

## 📝 Critical Files Reference

| File | Description |
| :--- | :--- |
| `app.py` | Main hub & KPI landing page. |
| `backend/pipeline.py` | Real-time ML processing engine. |
| `backend/generate_logs.py` | Database log simulator. |
| `pages/1_Dashboard.py` | Forensic user activity audit. |
| `pages/2_User_Monitoring.py` | Organizational risk leaderboard. |
| `pages/3_Alerts.py` | Security incident feed & PDF export. |
| `pages/4_Query_Console.py` | Manual SQL log injection console. |
| `utils/data_loader.py` | Live SQLite -> Streamlit bridge. |
| `file4.md` | Extremely detailed technical documentation. |
| `file5.md` | Project explanation written for a 10-year-old. |

---

## ✅ System Status
The project is currently in a **Fully Operational, Real-Time** state. It successfully bridges raw database logs, machine learning intelligence, and a professional-grade forensic UI.
