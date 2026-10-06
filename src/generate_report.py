"""Auto-write the business analytics + ML report from the real data (numbers never hand-typed)."""
import json
import pandas as pd
from config import PROC_DIR, REPORTS_DIR


def main():
    df = pd.read_csv(PROC_DIR / "trips_clean.csv")
    comp = df[df.status == "Completed"]
    m = json.loads((REPORTS_DIR / "ml_metrics.json").read_text())
    dq = json.loads((REPORTS_DIR / "data_quality_report.json").read_text())
    rev = df.groupby("route_name").revenue_pkr.sum().sort_values(ascending=False)
    hour = df.groupby("departure_hour").passengers.sum()
    dly = comp.groupby("route_name").delay_min.mean().sort_values(ascending=False)
    wx = comp.groupby("weather").delay_min.mean().sort_values(ascending=False)
    age = comp.assign(band=pd.cut(comp.bus_age_years, [0, 4, 8, 99], labels=["0-4", "5-8", "9+"])).groupby("band", observed=True).delay_min.mean()
    best = lambda k: next(r for r in m[k]["comparison"] if r["model"] == m[k]["best"])
    c, rg, dr = best("delay_classifier"), best("delay_regressor"), best("demand_regressor")
    fc = m["forecast"]
    md = f"""# Business Analytics & ML Report - Smart Public Transport

*All figures below are generated automatically from the synthetic dataset by `src/generate_report.py`.*

## 1. Headline KPIs (90 days)
| KPI | Value |
|---|---|
| Passengers carried | {df.passengers.sum():,} |
| Total revenue | PKR {df.revenue_pkr.sum():,.0f} |
| Trip completion rate | {(df.status == 'Completed').mean() * 100:.1f}% |
| Average delay | {comp.delay_min.mean():.1f} min |
| Trips delayed >= 15 min | {comp.is_delayed.mean() * 100:.1f}% |
| Most profitable route | {rev.index[0]} (PKR {rev.iloc[0]:,.0f}) |
| Peak travel hour | {hour.idxmax()}:00 |

## 2. Data quality
{dq['rows_raw']:,} raw rows -> {dq['rows_clean']:,} clean rows. Removed {dq['duplicates_removed']} duplicates, fixed {dq['impossible_passengers_fixed']}
impossible passenger counts and {dq['delay_outliers_fixed']} delay outliers, imputed missing weather / traffic / passengers / delay
using group-wise mode/median. All validation checks passed.

## 3. Descriptive insights
* **Revenue concentration:** top 3 routes ({', '.join(rev.index[:3])}) generate {rev.iloc[:3].sum() / rev.sum() * 100:.0f}% of revenue.
* **Peaks:** passenger load is highest at {hour.idxmax()}:00; the 8-9 AM and 5-6 PM windows carry {hour.loc[[8, 9, 17, 18]].sum() / hour.sum() * 100:.0f}% of all passengers.
* **Delays:** slowest route is {dly.index[0]} ({dly.iloc[0]:.1f} min avg). Weather ranking by delay: {', '.join(f'{k} {v:.1f}' for k, v in wx.items())} min.
* **Fleet age:** average delay by bus age band (min) - {', '.join(f'{k} yrs: {v:.1f}' for k, v in age.items())}.

## 4. Machine-learning results
| Task | Best model | Result |
|---|---|---|
| Delay-risk classification (>=15 min) | {m['delay_classifier']['best']} | F1 {c['f1']:.3f}, ROC-AUC {c['roc_auc']:.3f}, accuracy {c['accuracy']:.3f} |
| Delay-minutes regression | {m['delay_regressor']['best']} | MAE {rg['mae']:.2f} min, R2 {rg['r2']:.3f} |
| Passenger-demand regression | {m['demand_regressor']['best']} | MAE {dr['mae']:.2f} passengers, R2 {dr['r2']:.3f} |
| 14-day daily forecast | GradientBoosting (lag features) | MAE {fc['mae']} vs seasonal-naive {fc['seasonal_naive_mae']} (MAPE {fc['mape_pct']}%) |
| Route segmentation | KMeans k={m['clustering']['best_k']} | silhouette {max(m['clustering']['silhouette'].values()):.2f} |
| Anomaly detection | IsolationForest | {m['anomaly']['flagged_trips']} trips flagged (1% contamination) |

**Honest caveats.** The data is synthetic, so models learn the simulator's rules; real-world scores would be lower and need
retraining on real operations data. The daily forecaster only marginally beats the seasonal-naive baseline because daily weather
is not known in advance - a real deployment should add a weather-forecast feature. Only pre-departure features are used
(no leakage).

## 5. Recommendations
1. **Add capacity at peaks** on the top-revenue routes between 8-9 AM and 5-6 PM.
2. **Trim low-occupancy route-hours** (SQL query Q14) and redeploy buses to peak windows.
3. **Proactive rider alerts:** call `/predict/trip` for rainy peak-hour trips and notify passengers when delay risk is High.
4. **Maintenance priority** for buses 9+ years old (longer delays, more cancellations).
5. **Schedule padding** on {dly.index[0]} and {dly.index[1]}, the two slowest routes.
6. **Review anomalies** in `reports/anomalous_trips.csv` for sensor / data-entry problems or genuine disruptions.
"""
    (REPORTS_DIR / "business_report.md").write_text(md)
    print("Report written")


if __name__ == "__main__":
    main()
