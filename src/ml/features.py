"""Feature definitions shared by training, the REST API and the dashboard."""
import pandas as pd

CATEGORICAL = ["route_id", "weather"]
NUMERIC = ["departure_hour", "day_of_week", "is_weekend", "is_holiday", "distance_km",
           "fare_pkr", "capacity", "bus_age_years", "is_peak"]
FEATURES = CATEGORICAL + NUMERIC
PEAK_HOURS = (8, 9, 17, 18)


def add_peak(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_peak"] = df["departure_hour"].isin(PEAK_HOURS).astype(int)
    return df
