# What changed: Analytics project → Analytics + AI/ML project

## Kept from the original project (all still included)
| Original feature | Where it lives now |
|---|---|
| Fully original synthetic dataset (city bus network) | `src/generate_data.py` |
| Cleaning & validation (missing values, duplicates, outliers) | `src/clean_data.py` + `reports/data_quality_report.json` |
| Excel BI dashboard: 8 charts, KPIs, dynamic filters, executive summary | `src/build_excel.py` → `excel/Transport_BI_Dashboard.xlsx` |
| Business analytics report with recommendations | `src/generate_report.py` → `reports/business_report.md` |
| Normalized SQLite DB + 14 analytical queries | `sql/schema.sql`, `sql/queries.sql`, `src/build_db.py` |
| Streamlit web dashboard | `dashboard/streamlit_app.py` |

## NEW: AI / Machine Learning
1. **Delay-risk classifier** - predicts if a trip will be delayed ≥ 15 min (3 models compared, CV, ROC-AUC, confusion matrix, permutation importance).
2. **Delay-minutes regressor** - expected delay in minutes.
3. **Passenger-demand regressor** - expected passengers & revenue for a planned trip.
4. **Daily passenger forecaster** - lag/rolling features, time-ordered hold-out, compared to a seasonal-naive baseline.
5. **Route clustering** (KMeans + PCA view) - segments routes by demand, occupancy, delay.
6. **Anomaly detection** (IsolationForest) - flags unusual trips.
7. **Visualisation upgrade** - Matplotlib + Seaborn PNGs and interactive Plotly HTML in `reports/figures/`.
8. **REST API (FastAPI)** - `/predict/trip`, `/forecast`, `/routes`, `/health` with input validation + Swagger docs.
9. **ML in the web app** - new Streamlit tabs: "ML Predictions" (what-if trip simulator + 14-day forecast) and "Model Insights".
10. **Node.js client** for the API (the original stack listed Node.js).
11. **Engineering** - `run_pipeline.py` (one command), `tests/` (pytest, 5 tests), `requirements.txt`, `.gitignore`, fixed random seed.

12. **TransitIQ web dashboard** (`web/`, `docs/index.html`, `src/build_web_dashboard.py`) - minimal professional UI with an AI Predictor powered by real model outputs; GitHub-Pages ready.

## Small adjustments to the original pieces
* Dataset now also holds `traffic_index`, `bus_age_years`, `is_holiday`, `capacity` so ML has meaningful features.
* Streamlit got sidebar filters (route / weather / date) and a route × hour delay heat-map.
* Excel: route filter drives both KPI formulas and two live charts; added Analysis sheet as chart source.

## Honest notes
* **Numbers differ from the original LinkedIn post** (14,824 passengers, PKR 1,125,612 ...) because this rebuild
  generates its own dataset. If you want the post and repo to match, either update the post with the new README numbers
  or replace `data/raw/trips_raw.csv` with your original data (keep the same column names) and run `python run_pipeline.py`.
* Data is synthetic: ML scores show the pipeline works, not real-world accuracy.
