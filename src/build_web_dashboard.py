"""Build the standalone 'TransitIQ' web dashboard (single HTML file, no server needed).

Embeds the cleaned data aggregates and REAL predictions from the trained models
(10 routes x 17 hours x 7 days x 4 weather) so the AI Predictor page works offline.
Output: docs/index.html (GitHub Pages ready) and web/transitiq_dashboard.html
"""
import json
import pandas as pd
from config import ROOT, PROC_DIR, RAW_DIR, REPORTS_DIR
from ml import predictor


def main():
    d = pd.read_csv(PROC_DIR / "trips_clean.csv")
    m = json.loads((REPORTS_DIR / "ml_metrics.json").read_text())
    cl = pd.read_csv(REPORTS_DIR / "route_clusters.csv").set_index("route_name")
    routes, weather, dates = sorted(d.route_name.unique()), sorted(d.weather.unique()), sorted(d.date.unique())
    ri, wi, di = ({n: i for i, n in enumerate(x)} for x in (routes, weather, dates))
    t = [[ri[r.route_name], di[r.date], int(r.departure_hour), wi[r.weather], int(r.passengers), int(r.revenue_pkr),
          round(float(r.delay_min), 1) if r.status == "Completed" else 0, int(r.status == "Completed")] for r in d.itertuples()]
    rid = pd.read_csv(RAW_DIR / "routes.csv").set_index("route_name").route_id

    def one(rn, h, dw, wx):
        p = predictor.predict_trip(rid[rn], h, dw, wx)
        return [round(p["delay_probability"] * 100), p["expected_delay_min"], p["expected_passengers"], p["expected_revenue_pkr"]]

    P = [[[[one(rn, h, dw, wx) for wx in weather] for dw in range(7)] for h in range(5, 22)] for rn in routes]
    comp = d[d.status == "Completed"]; g = comp.groupby("route_name")
    hi = cl.avg_pax.groupby(cl.cluster).mean().idxmax()
    rt = sorted([dict(name=n, pax=int(d[d.route_name == n].passengers.sum()), rev=int(d[d.route_name == n].revenue_pkr.sum()),
                      delay=round(g.delay_min.mean()[n], 1), occ=round(g.occupancy_pct.mean()[n]),
                      seg="High-demand" if cl.cluster[n] == hi else "Standard") for n in routes], key=lambda x: -x["rev"])
    best = lambda k: next(x for x in m[k]["comparison"] if x["model"] == m[k]["best"])
    c, rg, dr, fc = best("delay_classifier"), best("delay_regressor"), best("demand_regressor"), m["forecast"]
    ml = [["Delay-risk classifier", m["delay_classifier"]["best"], f"F1 {c['f1']:.2f} · AUC {c['roc_auc']:.2f}"],
          ["Delay-minutes regressor", m["delay_regressor"]["best"], f"MAE {rg['mae']:.1f} min · R² {rg['r2']:.2f}"],
          ["Demand regressor", m["demand_regressor"]["best"], f"MAE {dr['mae']:.1f} · R² {dr['r2']:.2f}"],
          ["Daily forecaster", "GradientBoosting", f"MAE {fc['mae']:.0f} (naive {fc['seasonal_naive_mae']:.0f})"],
          ["Route segmentation", "KMeans", f"k = {m['clustering']['best_k']}"],
          ["Anomaly detector", "IsolationForest", f"{m['anomaly']['flagged_trips']} trips flagged"]]
    daily = d.groupby("date", as_index=False).passengers.sum()
    f = predictor.forecast_daily(daily, 14)
    fcd = dict(h=[list(daily.date[-30:]), [int(x) for x in daily.passengers[-30:]]],
               p=[[x["date"] for x in f], [x["predicted_passengers"] for x in f]])
    data = json.dumps(dict(routes=routes, weather=weather, dates=dates, t=t, P=P, rt=rt, ml=ml, fc=fcd),
                      separators=(",", ":"), ensure_ascii=False)
    html = (ROOT / "web" / "template.html").read_text().replace("__DATA__", data)
    for out in (ROOT / "docs" / "index.html", ROOT / "web" / "transitiq_dashboard.html"):
        out.write_text(html)
    print("Web dashboard written to docs/index.html")


if __name__ == "__main__":
    main()
