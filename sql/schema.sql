-- Normalized schema (3NF): routes, buses, weather_days, trips
DROP TABLE IF EXISTS trips; DROP TABLE IF EXISTS buses; DROP TABLE IF EXISTS routes; DROP TABLE IF EXISTS weather_days;

CREATE TABLE routes (
    route_id TEXT PRIMARY KEY, route_name TEXT NOT NULL,
    distance_km REAL NOT NULL, fare_pkr INTEGER NOT NULL);
CREATE TABLE buses (
    bus_id TEXT PRIMARY KEY, route_id TEXT NOT NULL REFERENCES routes(route_id),
    capacity INTEGER NOT NULL, bus_age_years INTEGER NOT NULL);
CREATE TABLE weather_days (
    date TEXT PRIMARY KEY, weather TEXT NOT NULL, is_weekend INTEGER, is_holiday INTEGER);
CREATE TABLE trips (
    trip_id TEXT PRIMARY KEY, date TEXT NOT NULL REFERENCES weather_days(date),
    route_id TEXT NOT NULL REFERENCES routes(route_id), bus_id TEXT NOT NULL REFERENCES buses(bus_id),
    departure_hour INTEGER, traffic_index REAL, passengers INTEGER, delay_min REAL,
    status TEXT, revenue_pkr INTEGER, is_delayed INTEGER);
CREATE INDEX idx_trips_route ON trips(route_id);
CREATE INDEX idx_trips_date ON trips(date);
