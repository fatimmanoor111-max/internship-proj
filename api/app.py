"""REST API for the Smart Public Transport ML models.

Run:  uvicorn api.app:app --reload --app-dir .   (from project root, with PYTHONPATH=src)
Docs: http://127.0.0.1:8000/docs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from config import PROC_DIR
from ml import predictor

app = FastAPI(title="Smart Transport ML API", version="1.0.0",
              description="Delay risk, demand and daily-passenger forecasts for a city bus network.")


class TripRequest(BaseModel):
    route_id: str = Field(..., examples=["R01"])
    departure_hour: int = Field(..., ge=5, le=21, examples=[9])
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    weather: Literal["Clear", "Rain", "Fog", "Heat"] = "Clear"
    is_holiday: int = Field(0, ge=0, le=1)
    capacity: int = Field(50, ge=20, le=100)
    bus_age_years: int = Field(5, ge=0, le=30)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/routes")
def routes():
    return predictor.route_table()[["route_id", "route_name", "distance_km", "fare_pkr"]].to_dict("records")


@app.post("/predict/trip")
def predict_trip(req: TripRequest):
    try:
        return predictor.predict_trip(req.route_id, req.departure_hour, req.day_of_week, req.weather,
                                      req.is_holiday, req.capacity, req.bus_age_years)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/forecast")
def forecast(days: int = 7):
    if not 1 <= days <= 30:
        raise HTTPException(status_code=422, detail="days must be between 1 and 30")
    df = pd.read_csv(PROC_DIR / "trips_clean.csv")
    daily = df.groupby("date", as_index=False)["passengers"].sum()
    return predictor.forecast_daily(daily, days)
