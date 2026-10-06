# Business Analytics & ML Report - Smart Public Transport

*All figures below are generated automatically from the synthetic dataset by `src/generate_report.py`.*

## 1. Headline KPIs (90 days)
| KPI | Value |
|---|---|
| Passengers carried | 189,031 |
| Total revenue | PKR 12,852,545 |
| Trip completion rate | 96.9% |
| Average delay | 10.0 min |
| Trips delayed >= 15 min | 18.0% |
| Most profitable route | Green Town - Cantt Station (PKR 2,240,400) |
| Peak travel hour | 9:00 |

## 2. Data quality
9,076 raw rows -> 9,004 clean rows. Removed 72 duplicates, fixed 27
impossible passenger counts and 34 delay outliers, imputed missing weather / traffic / passengers / delay
using group-wise mode/median. All validation checks passed.

## 3. Descriptive insights
* **Revenue concentration:** top 3 routes (Green Town - Cantt Station, Johar Town - Railway Station, Iqbal Town - Anarkali) generate 45% of revenue.
* **Peaks:** passenger load is highest at 9:00; the 8-9 AM and 5-6 PM windows carry 56% of all passengers.
* **Delays:** slowest route is Johar Town - Railway Station (11.8 min avg). Weather ranking by delay: Rain 14.0, Fog 12.5, Heat 8.2, Clear 8.1 min.
* **Fleet age:** average delay by bus age band (min) - 0-4 yrs: 8.4, 5-8 yrs: 10.3, 9+ yrs: 11.3.

## 4. Machine-learning results
| Task | Best model | Result |
|---|---|---|
| Delay-risk classification (>=15 min) | GradientBoosting | F1 0.657, ROC-AUC 0.916, accuracy 0.893 |
| Delay-minutes regression | Ridge | MAE 2.45 min, R2 0.669 |
| Passenger-demand regression | GradientBoosting | MAE 2.82 passengers, R2 0.894 |
| 14-day daily forecast | GradientBoosting (lag features) | MAE 247.7 vs seasonal-naive 249.9 (MAPE 12.15%) |
| Route segmentation | KMeans k=2 | silhouette 0.44 |
| Anomaly detection | IsolationForest | 88 trips flagged (1% contamination) |

**Honest caveats.** The data is synthetic, so models learn the simulator's rules; real-world scores would be lower and need
retraining on real operations data. The daily forecaster only marginally beats the seasonal-naive baseline because daily weather
is not known in advance - a real deployment should add a weather-forecast feature. Only pre-departure features are used
(no leakage).

## 5. Recommendations
1. **Add capacity at peaks** on the top-revenue routes between 8-9 AM and 5-6 PM.
2. **Trim low-occupancy route-hours** (SQL query Q14) and redeploy buses to peak windows.
3. **Proactive rider alerts:** call `/predict/trip` for rainy peak-hour trips and notify passengers when delay risk is High.
4. **Maintenance priority** for buses 9+ years old (longer delays, more cancellations).
5. **Schedule padding** on Johar Town - Railway Station and Bahria Town - Ferozepur Road, the two slowest routes.
6. **Review anomalies** in `reports/anomalous_trips.csv` for sensor / data-entry problems or genuine disruptions.
