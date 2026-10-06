import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from fastapi.testclient import TestClient
from config import PROC_DIR
from api.app import app

client = TestClient(app)


def test_clean_data_quality():
    df = pd.read_csv(PROC_DIR / "trips_clean.csv")
    assert df.trip_id.is_unique
    assert (df.passengers <= df.capacity).all()
    assert df[["weather", "traffic_index", "passengers"]].notna().all().all()


def test_health_and_routes():
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/routes").json()) == 10


def test_predict_trip_ok_and_peak_riskier():
    peak = client.post("/predict/trip", json={"route_id": "R01", "departure_hour": 9, "day_of_week": 0, "weather": "Rain"}).json()
    calm = client.post("/predict/trip", json={"route_id": "R01", "departure_hour": 14, "day_of_week": 6, "weather": "Clear"}).json()
    assert 0 <= peak["delay_probability"] <= 1
    assert peak["delay_probability"] > calm["delay_probability"]


def test_predict_validation_errors():
    assert client.post("/predict/trip", json={"route_id": "R99", "departure_hour": 9, "day_of_week": 0}).status_code == 422
    assert client.post("/predict/trip", json={"route_id": "R01", "departure_hour": 3, "day_of_week": 0}).status_code == 422


def test_forecast():
    r = client.get("/forecast?days=5").json()
    assert len(r) == 5 and all(x["predicted_passengers"] > 0 for x in r)
