"""Run the whole project end-to-end:  python run_pipeline.py"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [("Generate synthetic data", ["src/generate_data.py"]),
         ("Clean & validate", ["src/clean_data.py"]),
         ("Build SQLite DB + 14 queries", ["src/build_db.py"]),
         ("Train ML models", ["-m", "ml.train"]),
         ("Build Excel BI dashboard", ["src/build_excel.py"]),
         ("Write business report", ["src/generate_report.py"]),
         ("Build TransitIQ web dashboard", ["src/build_web_dashboard.py"])]

for title, args in STEPS:
    print(f"\n=== {title} ===")
    env = {**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run([sys.executable, *args], cwd=ROOT / "src" if args[0] == "-m" else ROOT, env=env)
    if r.returncode:
        sys.exit(f"Step failed: {title}")
print("\nDone. Next: streamlit run dashboard/streamlit_app.py   |   uvicorn api.app:app --reload")
