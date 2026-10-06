"""Data cleaning + validation pipeline.

Handles: duplicates, missing values, impossible values, outliers (IQR/domain rules),
type fixes, and writes a data-quality report.
"""
import json
import numpy as np
import pandas as pd
from config import RAW_DIR, PROC_DIR, REPORTS_DIR, DELAY_THRESHOLD_MIN


def clean():
    raw = pd.read_csv(RAW_DIR / "trips_raw.csv")
    routes = pd.read_csv(RAW_DIR / "routes.csv")
    buses = pd.read_csv(RAW_DIR / "buses.csv")
    log = {"rows_raw": len(raw)}

    df = raw.drop_duplicates(subset="trip_id").copy()
    log["duplicates_removed"] = len(raw) - len(df)
    log["missing_before"] = {k: int(v) for k, v in df.isna().sum().items() if v}

    df = df.merge(routes, on="route_id").merge(buses[["bus_id", "capacity", "bus_age_years"]], on="bus_id")
    df["date"] = pd.to_datetime(df["date"])

    # weather -> mode within the same date (weather is a daily attribute)
    day_mode = df.groupby("date")["weather"].agg(lambda s: s.mode().iat[0] if not s.mode().empty else np.nan)
    df["weather"] = df["weather"].fillna(df["date"].map(day_mode)).fillna("Clear")

    # impossible passenger counts (> bus capacity) -> treated as missing
    bad_pax = (df["passengers"] > df["capacity"]).sum()
    df.loc[df["passengers"] > df["capacity"], "passengers"] = np.nan
    log["impossible_passengers_fixed"] = int(bad_pax)
    # cancelled trips legitimately carry 0 passengers
    df.loc[df["status"] == "Cancelled", "passengers"] = 0
    med = df[df.status == "Completed"].groupby(["route_id", "departure_hour"])["passengers"].transform("median")
    df["passengers"] = df["passengers"].fillna(med).fillna(df["passengers"].median()).round().astype(int)

    # traffic index -> median by hour
    df["traffic_index"] = df["traffic_index"].fillna(df.groupby("departure_hour")["traffic_index"].transform("median"))

    # delay outliers: domain rule (-10..120 min) then IQR cap on the remainder
    comp = df["status"] == "Completed"
    out = comp & ((df["delay_min"] > 120) | (df["delay_min"] < -10))
    log["delay_outliers_fixed"] = int(out.sum())
    df.loc[out, "delay_min"] = np.nan
    q1, q3 = df.loc[comp, "delay_min"].quantile([.25, .75])
    hi = q3 + 3 * (q3 - q1)
    log["delay_iqr_capped"] = int((df["delay_min"] > hi).sum())
    df["delay_min"] = df["delay_min"].clip(upper=hi)
    df.loc[comp, "delay_min"] = df.loc[comp, "delay_min"].fillna(
        df[comp].groupby("route_id")["delay_min"].transform("median"))

    # derived columns
    df["revenue_pkr"] = df["passengers"] * df["fare_pkr"]
    df["occupancy_pct"] = (df["passengers"] / df["capacity"] * 100).round(1)
    df["is_delayed"] = ((df["delay_min"] >= DELAY_THRESHOLD_MIN)).astype(int)
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_name"] = df["date"].dt.day_name()
    df = df.sort_values(["date", "departure_hour", "route_id"]).reset_index(drop=True)

    # validation
    checks = {
        "no_duplicate_trip_ids": bool(df.trip_id.is_unique),
        "passengers_within_capacity": bool((df.passengers <= df.capacity).all()),
        "no_nulls_in_core_cols": bool(df[["route_id", "passengers", "weather", "traffic_index"]].notna().all().all()),
        "revenue_non_negative": bool((df.revenue_pkr >= 0).all()),
    }
    log.update(rows_clean=len(df), validation=checks)
    assert all(checks.values()), f"Validation failed: {checks}"

    df.to_csv(PROC_DIR / "trips_clean.csv", index=False)
    (REPORTS_DIR / "data_quality_report.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))
    return df


if __name__ == "__main__":
    clean()
