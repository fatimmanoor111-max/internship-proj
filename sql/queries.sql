-- name: Q01 Total KPIs
SELECT COUNT(*) AS trips, SUM(passengers) AS total_passengers, SUM(revenue_pkr) AS total_revenue_pkr,
       ROUND(100.0*SUM(status='Completed')/COUNT(*),1) AS completion_rate_pct,
       ROUND(AVG(CASE WHEN status='Completed' THEN delay_min END),1) AS avg_delay_min FROM trips;
-- name: Q02 Revenue and passengers by route
SELECT r.route_name, SUM(t.passengers) AS passengers, SUM(t.revenue_pkr) AS revenue_pkr
FROM trips t JOIN routes r USING(route_id) GROUP BY r.route_name ORDER BY revenue_pkr DESC;
-- name: Q03 Most profitable route (revenue per km)
SELECT r.route_name, ROUND(SUM(t.revenue_pkr)*1.0/(COUNT(*)*r.distance_km),1) AS revenue_per_km
FROM trips t JOIN routes r USING(route_id) GROUP BY r.route_id ORDER BY revenue_per_km DESC LIMIT 5;
-- name: Q04 Passengers by departure hour (peak hours)
SELECT departure_hour, SUM(passengers) AS passengers FROM trips GROUP BY departure_hour ORDER BY passengers DESC;
-- name: Q05 Average delay by route (completed trips)
SELECT r.route_name, ROUND(AVG(t.delay_min),1) AS avg_delay_min, ROUND(100.0*AVG(t.is_delayed),1) AS pct_delayed_15plus
FROM trips t JOIN routes r USING(route_id) WHERE t.status='Completed' GROUP BY r.route_name ORDER BY avg_delay_min DESC;
-- name: Q06 Daily revenue trend (first 10 days)
SELECT date, SUM(passengers) AS passengers, SUM(revenue_pkr) AS revenue_pkr FROM trips GROUP BY date ORDER BY date LIMIT 10;
-- name: Q07 Weekday vs weekend performance
SELECT CASE w.is_weekend WHEN 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
       ROUND(AVG(t.passengers),1) AS avg_pax_per_trip, ROUND(AVG(t.delay_min),1) AS avg_delay
FROM trips t JOIN weather_days w USING(date) GROUP BY w.is_weekend;
-- name: Q08 Weather impact on delays and cancellations
SELECT w.weather, COUNT(*) AS trips, ROUND(AVG(t.delay_min),1) AS avg_delay_min,
       ROUND(100.0*SUM(t.status='Cancelled')/COUNT(*),2) AS cancel_rate_pct
FROM trips t JOIN weather_days w USING(date) GROUP BY w.weather ORDER BY avg_delay_min DESC;
-- name: Q09 Bus utilisation (occupancy) by capacity class
SELECT b.capacity, COUNT(*) AS trips, ROUND(100.0*AVG(t.passengers*1.0/b.capacity),1) AS avg_occupancy_pct
FROM trips t JOIN buses b USING(bus_id) WHERE t.status='Completed' GROUP BY b.capacity ORDER BY b.capacity;
-- name: Q10 Older buses vs delays
SELECT CASE WHEN b.bus_age_years<=4 THEN '0-4 yrs' WHEN b.bus_age_years<=8 THEN '5-8 yrs' ELSE '9+ yrs' END AS age_band,
       ROUND(AVG(t.delay_min),1) AS avg_delay_min, ROUND(100.0*SUM(t.status='Cancelled')/COUNT(*),2) AS cancel_rate_pct
FROM trips t JOIN buses b USING(bus_id) GROUP BY age_band ORDER BY age_band;
-- name: Q11 Top 5 buses by revenue
SELECT bus_id, SUM(revenue_pkr) AS revenue_pkr, SUM(passengers) AS passengers FROM trips GROUP BY bus_id ORDER BY revenue_pkr DESC LIMIT 5;
-- name: Q12 Weekly revenue with week-over-week growth (window function)
WITH wk AS (SELECT strftime('%W',date) AS week, SUM(revenue_pkr) AS revenue FROM trips GROUP BY week)
SELECT week, revenue, ROUND(100.0*(revenue-LAG(revenue) OVER (ORDER BY week))/LAG(revenue) OVER (ORDER BY week),1) AS wow_growth_pct FROM wk;
-- name: Q13 Route rank by revenue within peak vs off-peak (window function)
SELECT * FROM (
  SELECT r.route_name, CASE WHEN t.departure_hour IN (8,9,17,18) THEN 'Peak' ELSE 'Off-peak' END AS period,
         SUM(t.revenue_pkr) AS revenue_pkr,
         RANK() OVER (PARTITION BY CASE WHEN t.departure_hour IN (8,9,17,18) THEN 'Peak' ELSE 'Off-peak' END ORDER BY SUM(t.revenue_pkr) DESC) AS rnk
  FROM trips t JOIN routes r USING(route_id) GROUP BY r.route_name, period) WHERE rnk<=3 ORDER BY period, rnk;
-- name: Q14 Underperforming route-hours (low occupancy, candidates to reduce service)
SELECT r.route_name, t.departure_hour, COUNT(*) AS trips, ROUND(100.0*AVG(t.passengers*1.0/b.capacity),1) AS avg_occupancy_pct
FROM trips t JOIN routes r USING(route_id) JOIN buses b USING(bus_id) WHERE t.status='Completed'
GROUP BY r.route_name, t.departure_hour HAVING trips>=20 AND avg_occupancy_pct<25 ORDER BY avg_occupancy_pct LIMIT 10;
