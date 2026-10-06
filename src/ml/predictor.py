"""Thin inference layer used by both the REST API and the Streamlit dashboard."""
import joblib
import pandas as pd
from config import MODELS_DIR, RAW_DIR
from ml.features import FEATURES, add_peak

_cache = {}


def _load(name):
    if name not in _cache:
        _cache[name] = joblib.load(MODELS_DIR / f"{name}.joblib")
    return _cache[name]


def route_table() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "routes.csv")


def _row(route_id, hour, day_of_week, weather, is_holiday=0, capacity=50, bus_age_years=5):
    r = route_table().set_index("route_id")
    if route_id not in r.index:
        raise ValueError(f"Unknown route_id '{route_id}'. Valid: {list(r.index)}")
    df = pd.DataFrame([dict(route_id=route_id, weather=weather, departure_hour=hour, day_of_week=day_of_week,
                            is_weekend=int(day_of_week >= 5), is_holiday=int(is_holiday),
                            distance_km=r.loc[route_id, "distance_km"], fare_pkr=r.loc[route_id, "fare_pkr"],
                            capacity=capacity, bus_age_years=bus_age_years)])
    return add_peak(df)[FEATURES]


def predict_trip(route_id, hour, day_of_week, weather="Clear", is_holiday=0, capacity=50, bus_age_years=5):
    X = _row(route_id, hour, day_of_week, weather, is_holiday, capacity, bus_age_years)
    p = float(_load("delay_classifier").predict_proba(X)[0, 1])
    pax = float(_load("demand_regressor").predict(X)[0])
    delay = float(_load("delay_regressor").predict(X)[0])
    pax = max(0.0, min(pax, capacity))
    fare = float(X["fare_pkr"].iloc[0])
    return {"delay_probability": round(p, 3),
            "risk_level": "High" if p >= .6 else "Medium" if p >= .3 else "Low",
            "expected_delay_min": round(delay, 1),
            "expected_passengers": round(pax),
            "expected_occupancy_pct": round(pax / capacity * 100, 1),
            "expected_revenue_pkr": round(pax * fare)}


def forecast_daily(history: pd.DataFrame, days=14):
    """history: DataFrame with columns date, passengers (daily totals). Recursive multi-step forecast."""
    art = _load("daily_forecaster")
    model, cols = art["model"], art["cols"]
    h = history[["date", "passengers"]].copy()
    h["date"] = pd.to_datetime(h["date"])
    s = h.set_index("date")["passengers"].astype(float)
    out = []
    for _ in range(days):
        d = s.index[-1] + pd.Timedelta(days=1)
        row = dict(lag_1=s.iloc[-1], lag_7=s.iloc[-7], lag_14=s.iloc[-14], roll7=s.iloc[-7:].mean(),
                   dow=d.dayofweek, is_weekend=int(d.dayofweek >= 5), is_holiday=0)
        yhat = float(model.predict(pd.DataFrame([row])[cols])[0])
        s.loc[d] = yhat
        out.append({"date": d.strftime("%Y-%m-%d"), "predicted_passengers": round(yhat)})
    return out
