"""Train, compare and evaluate all ML models. Saves models + metrics + figures.

Tasks
 1. Delay-risk CLASSIFICATION   : will a trip be delayed >= 15 min?   (scikit-learn)
 2. Delay-minutes REGRESSION    : expected delay in minutes
 3. Passenger-demand REGRESSION : expected passengers for a trip
 4. Daily-demand FORECASTING    : next 14 days of total passengers (lag features)
 5. Route CLUSTERING            : KMeans segments of routes
 6. ANOMALY detection           : IsolationForest on trips
Only features known BEFORE a trip departs are used (no leakage).
"""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from sklearn.ensemble import (GradientBoostingClassifier, GradientBoostingRegressor, IsolationForest,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, r2_score, roc_auc_score,
                             silhouette_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import PROC_DIR, MODELS_DIR, REPORTS_DIR, SEED
from ml.features import CATEGORICAL, NUMERIC, FEATURES, add_peak
from ml.plots import (plot_confusion, plot_importance, plot_pred_vs_actual, plot_forecast,
                      plot_clusters, plot_anomalies, plot_model_comparison)


def preproc():
    return ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
                              ("num", StandardScaler(), NUMERIC)])


def feature_names(pipe):
    return list(pipe.named_steps["prep"].get_feature_names_out())


def compare(models, X_tr, y_tr, X_te, y_te, kind):
    rows, fitted = [], {}
    for name, est in models.items():
        pipe = Pipeline([("prep", preproc()), ("model", est)]).fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        if kind == "clf":
            proba = pipe.predict_proba(X_te)[:, 1]
            cv = cross_val_score(Pipeline([("prep", preproc()), ("model", est)]), X_tr, y_tr, cv=5, scoring="f1").mean()
            rows.append(dict(model=name, accuracy=accuracy_score(y_te, pred), f1=f1_score(y_te, pred),
                             roc_auc=roc_auc_score(y_te, proba), cv_f1=cv))
        else:
            cv = cross_val_score(Pipeline([("prep", preproc()), ("model", est)]), X_tr, y_tr, cv=5, scoring="r2").mean()
            rows.append(dict(model=name, mae=mean_absolute_error(y_te, pred), r2=r2_score(y_te, pred), cv_r2=cv))
        fitted[name] = pipe
    res = pd.DataFrame(rows).round(4)
    best = res.sort_values("f1" if kind == "clf" else "r2", ascending=False).iloc[0].model
    return res, fitted, best


def main():
    df = add_peak(pd.read_csv(PROC_DIR / "trips_clean.csv", parse_dates=["date"]))
    comp = df[df.status == "Completed"].copy()
    metrics = {}

    # ---- 1. delay classification ----
    X, y = comp[FEATURES], comp["is_delayed"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=.2, random_state=SEED, stratify=y)
    clf_models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(n_estimators=200, min_samples_leaf=3, class_weight="balanced",
                                               random_state=SEED, n_jobs=-1),
        "GradientBoosting": GradientBoostingClassifier(random_state=SEED),
    }
    res, fitted, best = compare(clf_models, X_tr, y_tr, X_te, y_te, "clf")
    print("\n[1] Delay classification\n", res.to_string(index=False), "\nbest:", best)
    joblib.dump(fitted[best], MODELS_DIR / "delay_classifier.joblib")
    metrics["delay_classifier"] = {"best": best, "comparison": res.to_dict("records")}
    plot_model_comparison(res, "f1", "Delay classifier - model comparison (F1)", "01_delay_model_comparison.png")
    plot_confusion(y_te, fitted[best].predict(X_te), "Delay classifier - confusion matrix", "02_delay_confusion.png")
    plot_importance(fitted[best], X_te, y_te, "Delay classifier - permutation importance", "03_delay_importance.png")

    # ---- 2. delay minutes regression ----
    y2 = comp["delay_min"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y2, test_size=.2, random_state=SEED)
    reg_models = {"Ridge": Ridge(alpha=1.0),
                  "RandomForest": RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=SEED, n_jobs=-1),
                  "GradientBoosting": GradientBoostingRegressor(random_state=SEED)}
    res, fitted, best = compare(reg_models, X_tr, y_tr, X_te, y_te, "reg")
    print("\n[2] Delay minutes regression\n", res.to_string(index=False), "\nbest:", best)
    joblib.dump(fitted[best], MODELS_DIR / "delay_regressor.joblib")
    metrics["delay_regressor"] = {"best": best, "comparison": res.to_dict("records")}
    plot_pred_vs_actual(y_te, fitted[best].predict(X_te), "Delay minutes - predicted vs actual", "04_delay_reg.png")

    # ---- 3. demand regression ----
    y3 = comp["passengers"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y3, test_size=.2, random_state=SEED)
    res, fitted, best = compare(reg_models, X_tr, y_tr, X_te, y_te, "reg")
    print("\n[3] Passenger demand regression\n", res.to_string(index=False), "\nbest:", best)
    joblib.dump(fitted[best], MODELS_DIR / "demand_regressor.joblib")
    metrics["demand_regressor"] = {"best": best, "comparison": res.to_dict("records")}
    plot_pred_vs_actual(y_te, fitted[best].predict(X_te), "Passenger demand - predicted vs actual", "05_demand_reg.png")
    plot_importance(fitted[best], X_te, y_te, "Demand model - permutation importance", "06_demand_importance.png", scoring="r2")

    # ---- 4. daily forecasting (time-ordered split, no shuffling) ----
    daily = df.groupby("date").agg(passengers=("passengers", "sum"), is_weekend=("is_weekend", "first"),
                                   is_holiday=("is_holiday", "first")).reset_index()
    def make_lags(d):
        d = d.copy()
        for k in (1, 7, 14):
            d[f"lag_{k}"] = d["passengers"].shift(k)
        d["roll7"] = d["passengers"].shift(1).rolling(7).mean()
        d["dow"] = d["date"].dt.dayofweek
        return d
    lagged = make_lags(daily).dropna().reset_index(drop=True)
    fcols = ["lag_1", "lag_7", "lag_14", "roll7", "dow", "is_weekend", "is_holiday"]
    split = len(lagged) - 14
    tr, te = lagged.iloc[:split], lagged.iloc[split:]
    fm = GradientBoostingRegressor(random_state=SEED).fit(tr[fcols], tr["passengers"])
    naive = te["lag_7"]  # seasonal-naive baseline
    pred = fm.predict(te[fcols])
    metrics["forecast"] = {"holdout_days": 14, "mae": round(mean_absolute_error(te.passengers, pred), 1),
                           "seasonal_naive_mae": round(mean_absolute_error(te.passengers, naive), 1),
                           "mape_pct": round(float(np.mean(np.abs((te.passengers - pred) / te.passengers)) * 100), 2)}
    print("\n[4] Forecast", metrics["forecast"])
    fm = GradientBoostingRegressor(random_state=SEED).fit(lagged[fcols], lagged["passengers"])  # refit on all
    joblib.dump({"model": fm, "cols": fcols}, MODELS_DIR / "daily_forecaster.joblib")
    plot_forecast(te["date"], te["passengers"], pred, naive)

    # ---- 5. route clustering ----
    rf = comp.groupby("route_name").agg(avg_pax=("passengers", "mean"), avg_occ=("occupancy_pct", "mean"),
                                        avg_delay=("delay_min", "mean"), rev_per_trip=("revenue_pkr", "mean"),
                                        distance=("distance_km", "first")).reset_index()
    Z = StandardScaler().fit_transform(rf.drop(columns="route_name"))
    scores = {k: silhouette_score(Z, KMeans(k, n_init=10, random_state=SEED).fit_predict(Z)) for k in (2, 3, 4)}
    k = max(scores, key=scores.get)
    km = KMeans(k, n_init=10, random_state=SEED).fit(Z)
    rf["cluster"] = km.labels_
    rf.round(2).to_csv(REPORTS_DIR / "route_clusters.csv", index=False)
    metrics["clustering"] = {"best_k": k, "silhouette": {str(a): round(b, 3) for a, b in scores.items()}}
    print("\n[5] Clustering", metrics["clustering"])
    plot_clusters(rf, Z)

    # ---- 6. anomaly detection ----
    a_cols = ["passengers", "occupancy_pct", "delay_min", "traffic_index"]
    iso = IsolationForest(contamination=0.01, random_state=SEED).fit(comp[a_cols])
    comp["anomaly"] = (iso.predict(comp[a_cols]) == -1)
    comp[comp.anomaly][["trip_id", "date", "route_name", "departure_hour", *a_cols]].to_csv(
        REPORTS_DIR / "anomalous_trips.csv", index=False)
    joblib.dump({"model": iso, "cols": a_cols}, MODELS_DIR / "anomaly_detector.joblib")
    metrics["anomaly"] = {"flagged_trips": int(comp.anomaly.sum()), "contamination": 0.01}
    print("\n[6] Anomalies flagged:", metrics["anomaly"]["flagged_trips"])
    plot_anomalies(comp)

    (REPORTS_DIR / "ml_metrics.json").write_text(json.dumps(metrics, indent=2, default=float))
    print("\nSaved models to /models and metrics to reports/ml_metrics.json")


if __name__ == "__main__":
    main()
