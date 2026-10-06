"""Load cleaned data into a normalized SQLite DB and run the 14 analytical queries."""
import re
import sqlite3
import pandas as pd
from config import ROOT, DB_PATH, PROC_DIR, RAW_DIR, REPORTS_DIR


def build():
    df = pd.read_csv(PROC_DIR / "trips_clean.csv")
    routes = pd.read_csv(RAW_DIR / "routes.csv")[["route_id", "route_name", "distance_km", "fare_pkr"]]
    buses = pd.read_csv(RAW_DIR / "buses.csv")
    days = df.groupby("date").agg(weather=("weather", "first"), is_weekend=("is_weekend", "first"),
                                  is_holiday=("is_holiday", "first")).reset_index()
    con = sqlite3.connect(DB_PATH)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    routes.to_sql("routes", con, if_exists="append", index=False)
    buses[["bus_id", "route_id", "capacity", "bus_age_years"]].to_sql("buses", con, if_exists="append", index=False)
    days.to_sql("weather_days", con, if_exists="append", index=False)
    cols = ["trip_id", "date", "route_id", "bus_id", "departure_hour", "traffic_index", "passengers",
            "delay_min", "status", "revenue_pkr", "is_delayed"]
    df[cols].to_sql("trips", con, if_exists="append", index=False)
    con.commit()

    text = (ROOT / "sql" / "queries.sql").read_text()
    blocks = re.split(r"-- name: ", text)[1:]
    out = ["# SQL Query Results\n"]
    for b in blocks:
        title, sql = b.split("\n", 1)
        res = pd.read_sql_query(sql, con)
        out.append(f"## {title}\n\n```sql\n{sql.strip()}\n```\n\n{res.to_markdown(index=False, disable_numparse=True)}\n")
    (REPORTS_DIR / "sql_results.md").write_text("\n".join(out))
    con.close()
    print(f"DB built at {DB_PATH} with {len(blocks)} queries executed")


if __name__ == "__main__":
    build()
