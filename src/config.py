"""Central paths and constants used across the project."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "db" / "transport.db"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"
EXCEL_PATH = ROOT / "excel" / "Transport_BI_Dashboard.xlsx"

SEED = 42
START_DATE = "2026-06-01"
N_DAYS = 90
DELAY_THRESHOLD_MIN = 15  # a trip is "significantly delayed" at/above this

for d in (RAW_DIR, PROC_DIR, DB_PATH.parent, MODELS_DIR, FIG_DIR, EXCEL_PATH.parent):
    d.mkdir(parents=True, exist_ok=True)
