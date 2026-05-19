from pathlib import Path

APP_TITLE = "Enterprise Database Activity Monitoring"
APP_SHORT_TITLE = "Enterprise DAM"
PAGE_ICON = "shield"

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
LOG_DIR = BACKEND_DIR / "logs"
LOG_FILE = LOG_DIR / "postgresql.log"

DB_NAME = "security_monitoring"
# Using the single table populated by the MySQL pipeline
LIVE_TABLE = "query_monitoring"

MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "root_password"
DB_URI = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{DB_NAME}"
)

QUERY_TYPES = {"SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"}
RISK_COLORS = {
    "High Risk": "#dc2626",
    "Medium Risk": "#d97706",
    "Low Risk": "#16a34a",
}
