"""Generate a fully ORIGINAL synthetic dataset simulating a city bus network.

Outputs (data/raw): routes.csv, buses.csv, trips_raw.csv
trips_raw.csv intentionally contains missing values, duplicates and outliers
so that the cleaning pipeline has real work to do.
"""
import numpy as np
import pandas as pd
from config import RAW_DIR, SEED, START_DATE, N_DAYS

ROUTES = [
    # id, name, distance_km, fare_pkr, popularity
    ("R01", "Green Town - Cantt Station", 14.0, 80, 1.45),
    ("R02", "Model Town - Liberty Market", 9.5, 60, 1.20),
    ("R03", "Johar Town - Railway Station", 16.5, 90, 1.30),
    ("R04", "Gulberg - Mall Road", 7.0, 50, 1.05),
    ("R05", "DHA - Cantt Station", 12.0, 70, 0.95),
    ("R06", "Iqbal Town - Anarkali", 11.0, 65, 1.10),
    ("R07", "Wapda Town - Thokar Niaz Baig", 8.5, 55, 0.80),
    ("R08", "Samanabad - Data Darbar", 6.5, 45, 0.90),
    ("R09", "Bahria Town - Ferozepur Road", 18.0, 100, 0.70),
    ("R10", "Township - Kalma Chowk", 10.0, 60, 0.85),
]
HOLIDAYS = {"2026-06-26", "2026-08-14"}  # illustrative public holidays
HOUR_PROFILE = {5: .35, 6: .6, 7: 1.0, 8: 1.5, 9: 1.7, 10: 1.1, 11: .8, 12: .85,
                13: .9, 14: .8, 15: .9, 16: 1.1, 17: 1.5, 18: 1.6, 19: 1.1, 20: .7, 21: .45}


def main():
    rng = np.random.default_rng(SEED)
    routes = pd.DataFrame(ROUTES, columns=["route_id", "route_name", "distance_km", "fare_pkr", "popularity"])

    buses = pd.DataFrame({
        "bus_id": [f"B{str(i).zfill(3)}" for i in range(1, 41)],
        "capacity": rng.choice([40, 50, 60], 40, p=[.3, .5, .2]),
        "bus_age_years": rng.integers(1, 13, 40),
    })
    buses["route_id"] = np.repeat(routes.route_id.values, 4)

    dates = pd.date_range(START_DATE, periods=N_DAYS)
    rows = []
    for date in dates:
        dow, ds = date.dayofweek, date.strftime("%Y-%m-%d")
        is_weekend = int(dow >= 5)  # Sat/Sun
        is_hol = int(ds in HOLIDAYS)
        weather = rng.choice(["Clear", "Rain", "Fog", "Heat"], p=[.55, .2, .05, .2])
        for _, r in routes.iterrows():
            route_buses = buses[buses.route_id == r.route_id]
            for hour, prof in HOUR_PROFILE.items():
                if rng.random() < 0.55 and hour not in (8, 9, 17, 18):
                    continue  # not every hour is served
                b = route_buses.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
                peak = hour in (8, 9, 17, 18)
                traffic = np.clip(0.25 + 0.5 * peak + 0.1 * rng.random()
                                  - 0.15 * (is_weekend or is_hol) + 0.15 * (weather == "Rain"), 0, 1)
                w_demand = {"Clear": 1.0, "Rain": 0.85, "Fog": 0.8, "Heat": 0.92}[weather]
                lam = b.capacity * 0.55 * r.popularity * prof / 1.2 * w_demand
                lam *= 0.7 if (is_weekend or is_hol) else 1.0
                pax = int(np.clip(rng.normal(lam, lam * 0.15), 3, b.capacity))
                sched = r.distance_km * 3.2 + 6
                delay = (-1 + 12 * traffic + 4 * (weather == "Rain") + 5 * (weather == "Fog")
                         + 0.12 * r.distance_km + 0.35 * b.bus_age_years + rng.normal(0, 3))
                p_cancel = 0.009 + 0.028 * (weather in ("Rain", "Fog")) + 0.002 * b.bus_age_years
                status = "Cancelled" if rng.random() < p_cancel else "Completed"
                rows.append(dict(
                    date=ds, route_id=r.route_id, bus_id=b.bus_id, departure_hour=hour,
                    day_of_week=dow, is_weekend=is_weekend, is_holiday=is_hol, weather=weather,
                    traffic_index=round(float(traffic), 3), passengers=pax if status == "Completed" else 0,
                    scheduled_duration_min=round(sched, 1),
                    delay_min=round(float(max(delay, -3)), 1) if status == "Completed" else np.nan,
                    status=status))
    df = pd.DataFrame(rows)
    df.insert(0, "trip_id", [f"T{str(i).zfill(6)}" for i in range(1, len(df) + 1)])

    # ---- inject realistic dirt for the cleaning pipeline ----
    n = len(df)
    for col, frac in [("weather", .01), ("passengers", .015), ("traffic_index", .01)]:
        df.loc[rng.choice(n, int(n * frac), replace=False), col] = np.nan
    df.loc[rng.choice(n, int(n * .004), replace=False), "delay_min"] = rng.choice([180, 240, -45], int(n * .004))
    df.loc[rng.choice(n, int(n * .003), replace=False), "passengers"] = 400  # impossible values
    df = pd.concat([df, df.sample(int(n * .008), random_state=SEED)], ignore_index=True)  # duplicates

    routes.to_csv(RAW_DIR / "routes.csv", index=False)
    buses.to_csv(RAW_DIR / "buses.csv", index=False)
    df.to_csv(RAW_DIR / "trips_raw.csv", index=False)
    print(f"Generated {len(df):,} raw trip rows, {len(routes)} routes, {len(buses)} buses")


if __name__ == "__main__":
    main()
