"""Interactive Streamlit BI + ML dashboard.   Run: streamlit run dashboard/streamlit_app.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

from config import PROC_DIR, REPORTS_DIR
from ml import predictor

st.set_page_config(page_title="Smart Transport Analytics", page_icon="🚌", layout="wide")


@st.cache_data
def load():
    return pd.read_csv(PROC_DIR / "trips_clean.csv", parse_dates=["date"])


df = load()
st.title("🚌 Smart Public Transport Analytics & ML Dashboard")

# ---------- sidebar filters ----------
st.sidebar.header("Filters")
routes = st.sidebar.multiselect("Routes", sorted(df.route_name.unique()), default=sorted(df.route_name.unique()))
weather = st.sidebar.multiselect("Weather", sorted(df.weather.unique()), default=sorted(df.weather.unique()))
dr = st.sidebar.date_input("Date range", (df.date.min(), df.date.max()))
f = df[df.route_name.isin(routes) & df.weather.isin(weather)]
if len(dr) == 2:
    f = f[(f.date >= pd.Timestamp(dr[0])) & (f.date <= pd.Timestamp(dr[1]))]
comp = f[f.status == "Completed"]

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🛣️ Routes & Time", "🤖 ML Predictions", "🧪 Model Insights"])

with tab1:
    c = st.columns(5)
    c[0].metric("Passengers", f"{f.passengers.sum():,}")
    c[1].metric("Revenue (PKR)", f"{f.revenue_pkr.sum():,.0f}")
    c[2].metric("Completion rate", f"{(f.status == 'Completed').mean() * 100:.1f}%")
    c[3].metric("Avg delay (min)", f"{comp.delay_min.mean():.1f}")
    c[4].metric("Delayed 15+ min", f"{comp.is_delayed.mean() * 100:.1f}%")
    daily = f.groupby("date", as_index=False)[["passengers", "revenue_pkr"]].sum()
    st.plotly_chart(px.line(daily, x="date", y="passengers", title="Daily passengers"), width="stretch")

with tab2:
    a, b = st.columns(2)
    r = f.groupby("route_name", as_index=False).revenue_pkr.sum().sort_values("revenue_pkr")
    a.plotly_chart(px.bar(r, x="revenue_pkr", y="route_name", orientation="h", title="Revenue by route"), width="stretch")
    h = f.groupby("departure_hour", as_index=False).passengers.sum()
    b.plotly_chart(px.bar(h, x="departure_hour", y="passengers", title="Passengers by hour (peak = 9 AM)"), width="stretch")
    heat = comp.pivot_table(index="route_name", columns="departure_hour", values="delay_min", aggfunc="mean")
    st.plotly_chart(px.imshow(heat, aspect="auto", color_continuous_scale="YlOrRd", title="Average delay (min): route x hour"),
                    width="stretch")

with tab3:
    st.subheader("Predict a future trip")
    rt = predictor.route_table()
    x1, x2, x3 = st.columns(3)
    rid = x1.selectbox("Route", rt.route_id, format_func=lambda i: f"{i} - {rt.set_index('route_id').route_name[i]}")
    hour = x1.slider("Departure hour", 5, 21, 9)
    dow = x2.selectbox("Day", range(7), format_func=lambda d: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d])
    wx = x2.selectbox("Weather", ["Clear", "Rain", "Fog", "Heat"])
    cap = x3.selectbox("Bus capacity", [40, 50, 60], index=1)
    age = x3.slider("Bus age (years)", 0, 15, 5)
    p = predictor.predict_trip(rid, hour, dow, wx, 0, cap, age)
    m = st.columns(4)
    m[0].metric("Delay risk (15+ min)", f"{p['delay_probability'] * 100:.0f}%", p["risk_level"], delta_color="off")
    m[1].metric("Expected delay", f"{p['expected_delay_min']} min")
    m[2].metric("Expected passengers", p["expected_passengers"], f"{p['expected_occupancy_pct']}% full", delta_color="off")
    m[3].metric("Expected revenue", f"PKR {p['expected_revenue_pkr']:,}")
    st.subheader("14-day passenger forecast")
    fc = pd.DataFrame(predictor.forecast_daily(df.groupby("date", as_index=False).passengers.sum(), 14))
    st.plotly_chart(px.bar(fc, x="date", y="predicted_passengers"), width="stretch")

with tab4:
    import json
    mt = json.loads((REPORTS_DIR / "ml_metrics.json").read_text())
    st.json(mt, expanded=False)
    for name in ["02_delay_confusion", "03_delay_importance", "05_demand_reg", "07_forecast", "08_route_clusters"]:
        img = REPORTS_DIR / "figures" / f"{name}.png"
        if img.exists():
            st.image(str(img), width=520)
    st.subheader("Route segments")
    st.dataframe(pd.read_csv(REPORTS_DIR / "route_clusters.csv"))
    st.subheader("Flagged anomalous trips")
    st.dataframe(pd.read_csv(REPORTS_DIR / "anomalous_trips.csv"))
