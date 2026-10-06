# 🚌 Smart Public Transport Analytics & ML Platform

An end-to-end **data analytics + machine-learning** project simulating a 10-route city bus network:
from raw (dirty) data → cleaning → SQL → Excel BI → **ML models** → **REST API** → interactive **Streamlit** app.

> Part 1 (analytics) was the original project. Part 2 (**AI/ML**) extends it with scikit-learn models,
> a REST API and ML-powered dashboard pages. See [`CHANGES.md`](CHANGES.md) for exactly what was added.

**Tech stack:** Python (pandas, NumPy, scikit-learn, openpyxl) · Matplotlib / Seaborn / Plotly · FastAPI · Streamlit · SQLite · Excel · Node.js (API client)

## 🌐 TransitIQ web dashboard (modern UI)
A clean, minimal presentation dashboard (light/dark theme, KPIs, route filters, **AI Predictor** with delay-risk gauge,
model insights + forecast). It is a single static file: open `docs/index.html` in a browser, or enable
**GitHub Pages** (Settings → Pages → Branch `main`, folder `/docs`) to get a public link like
`https://<username>.github.io/<repo>/`. Rebuild with `python src/build_web_dashboard.py`.

## Pipeline

```
generate_data ─► clean_data ─► build_db (SQLite, 14 queries) ─► ML training ─► Excel BI
 (synthetic,      (dupes,        sql/schema.sql                  6 tasks          8 charts
  dirty)           NaN, outliers) sql/queries.sql                 models/          KPIs, filters
                                                                      │
                                              FastAPI (api/) ◄────────┤────► Streamlit (dashboard/)
```

## Key results (this synthetic dataset, 90 days)

| Metric | Value |
|---|---|
| Passengers / Revenue | 189,031 / PKR 12,852,545 |
| Trip completion rate | 96.9% |
| Average delay | 10.0 min |
| Most profitable route | Green Town - Cantt Station |
| Peak travel hour | 9:00 AM |

> Exact numbers are regenerated on every run (fixed seed 42) — see `reports/business_report.md`.

## 🤖 Machine-learning part

| # | Task | Models compared | Best (hold-out) |
|---|---|---|---|
| 1 | **Delay-risk classification** (delay ≥ 15 min) | LogReg, RandomForest, GradientBoosting | GradientBoosting - F1 0.66, ROC-AUC 0.92 |
| 2 | **Delay-minutes regression** | Ridge, RandomForest, GradientBoosting | Ridge - MAE 2.5 min, R² 0.67 |
| 3 | **Passenger-demand regression** | Ridge, RandomForest, GradientBoosting | GradientBoosting - MAE 2.8, R² 0.89 |
| 4 | **14-day passenger forecasting** (lag features, time-ordered split) | GradientBoosting vs seasonal-naive | MAE 248 vs 250 baseline (marginal) |
| 5 | **Route segmentation** | KMeans (k chosen by silhouette) | k = 2 |
| 6 | **Anomaly detection** | IsolationForest | 88 trips flagged |

Good-practice details: sklearn `Pipeline` + `ColumnTransformer`, 5-fold CV, stratified split, no target leakage
(only pre-departure features), permutation importance, baseline comparison.
**Caveat:** data is synthetic, so scores reflect the simulator, not real-world performance.

## Quick start

```bash
git clone <your-repo-url> && cd smart-transport-analytics
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_pipeline.py                      # data -> clean -> SQL -> ML -> Excel -> report
streamlit run dashboard/streamlit_app.py    # interactive dashboard (4 tabs incl. ML predictions)
PYTHONPATH=src uvicorn api.app:app --reload # REST API, docs at http://127.0.0.1:8000/docs
PYTHONPATH=src pytest -q tests              # tests
node node_client/client.js                  # optional: Node.js client calling the API
```
(Windows PowerShell: `$env:PYTHONPATH="src"` before the uvicorn / pytest commands.)

### API example
```bash
curl -X POST http://127.0.0.1:8000/predict/trip -H "Content-Type: application/json" \
  -d '{"route_id":"R01","departure_hour":9,"day_of_week":0,"weather":"Rain"}'
# {"delay_probability":0.779,"risk_level":"High","expected_delay_min":17.8,"expected_passengers":44, ...}
```
Endpoints: `GET /health` · `GET /routes` · `POST /predict/trip` · `GET /forecast?days=7`

## Project structure
```
├── run_pipeline.py          one command to run everything
├── src/                     generate_data, clean_data, build_db, build_excel, generate_report
│   └── ml/                  features, train, plots, predictor (shared by API + dashboard)
├── api/app.py               FastAPI REST service
├── dashboard/streamlit_app.py
├── web/ + docs/             TransitIQ static web dashboard (template, build output for GitHub Pages)
├── sql/                     schema.sql (normalized) + queries.sql (14 analytical queries)
├── excel/                   Transport_BI_Dashboard.xlsx (8 charts, KPIs, live route filter, exec summary)
├── data/{raw,processed}/    datasets      ·  db/transport.db  SQLite
├── models/                  trained .joblib models
├── reports/                 business_report.md, sql_results.md, ml_metrics.json, figures/ (PNG + interactive HTML)
├── node_client/client.js    tests/test_pipeline.py
```

## Excel dashboard
Pick a route in the yellow cell (`Dashboard!C4`) and the KPI tiles plus the *Daily passengers* and *Passengers by hour*
charts update through `SUMIFS` formulas. The `Data` sheet has filters; `Executive Summary` lists findings and recommendations.

## Business recommendations
Add capacity at 8-9 AM / 5-6 PM peaks · trim low-occupancy route-hours · send delay alerts for rainy peak trips ·
prioritise maintenance on buses 9+ years old · pad schedules on the slowest routes. Details in `reports/business_report.md`.
