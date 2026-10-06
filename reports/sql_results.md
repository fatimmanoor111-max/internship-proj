# SQL Query Results

## Q01 Total KPIs

```sql
SELECT COUNT(*) AS trips, SUM(passengers) AS total_passengers, SUM(revenue_pkr) AS total_revenue_pkr,
       ROUND(100.0*SUM(status='Completed')/COUNT(*),1) AS completion_rate_pct,
       ROUND(AVG(CASE WHEN status='Completed' THEN delay_min END),1) AS avg_delay_min FROM trips;
```

| trips   | total_passengers   | total_revenue_pkr   | completion_rate_pct   | avg_delay_min   |
|:--------|:-------------------|:--------------------|:----------------------|:----------------|
| 9004.0  | 189031.0           | 12852545.0          | 96.9                  | 10.0            |

## Q02 Revenue and passengers by route

```sql
SELECT r.route_name, SUM(t.passengers) AS passengers, SUM(t.revenue_pkr) AS revenue_pkr
FROM trips t JOIN routes r USING(route_id) GROUP BY r.route_name ORDER BY revenue_pkr DESC;
```

| route_name                    | passengers   | revenue_pkr   |
|:------------------------------|:-------------|:--------------|
| Green Town - Cantt Station    | 28005        | 2240400       |
| Johar Town - Railway Station  | 23070        | 2076300       |
| Iqbal Town - Anarkali         | 22388        | 1455220       |
| Model Town - Liberty Market   | 22499        | 1349940       |
| DHA - Cantt Station           | 17750        | 1242500       |
| Bahria Town - Ferozepur Road  | 11966        | 1196600       |
| Gulberg - Mall Road           | 19082        | 954100        |
| Township - Kalma Chowk        | 14312        | 858720        |
| Samanabad - Data Darbar       | 16898        | 760410        |
| Wapda Town - Thokar Niaz Baig | 13061        | 718355        |

## Q03 Most profitable route (revenue per km)

```sql
SELECT r.route_name, ROUND(SUM(t.revenue_pkr)*1.0/(COUNT(*)*r.distance_km),1) AS revenue_per_km
FROM trips t JOIN routes r USING(route_id) GROUP BY r.route_id ORDER BY revenue_per_km DESC LIMIT 5;
```

| route_name                   | revenue_per_km   |
|:-----------------------------|:-----------------|
| Green Town - Cantt Station   | 174.5            |
| Model Town - Liberty Market  | 155.8            |
| Gulberg - Mall Road          | 155.4            |
| Iqbal Town - Anarkali        | 147.8            |
| Johar Town - Railway Station | 143.8            |

## Q04 Passengers by departure hour (peak hours)

```sql
SELECT departure_hour, SUM(passengers) AS passengers FROM trips GROUP BY departure_hour ORDER BY passengers DESC;
```

| departure_hour   | passengers   |
|:-----------------|:-------------|
| 9                | 28859        |
| 18               | 26772        |
| 8                | 25516        |
| 17               | 25440        |
| 19               | 8633         |
| 10               | 8235         |
| 16               | 8157         |
| 7                | 7690         |
| 13               | 7444         |
| 12               | 6730         |
| 11               | 6456         |
| 14               | 6407         |
| 15               | 6395         |
| 20               | 5854         |
| 6                | 4453         |
| 21               | 3372         |
| 5                | 2618         |

## Q05 Average delay by route (completed trips)

```sql
SELECT r.route_name, ROUND(AVG(t.delay_min),1) AS avg_delay_min, ROUND(100.0*AVG(t.is_delayed),1) AS pct_delayed_15plus
FROM trips t JOIN routes r USING(route_id) WHERE t.status='Completed' GROUP BY r.route_name ORDER BY avg_delay_min DESC;
```

| route_name                    | avg_delay_min   | pct_delayed_15plus   |
|:------------------------------|:----------------|:---------------------|
| Johar Town - Railway Station  | 11.8            | 26.9                 |
| Bahria Town - Ferozepur Road  | 11.1            | 21.8                 |
| Wapda Town - Thokar Niaz Baig | 10.8            | 21.7                 |
| Green Town - Cantt Station    | 10.5            | 19.3                 |
| Iqbal Town - Anarkali         | 9.9             | 17.5                 |
| Gulberg - Mall Road           | 9.8             | 16.7                 |
| Samanabad - Data Darbar       | 9.6             | 14.8                 |
| DHA - Cantt Station           | 9.6             | 16.0                 |
| Model Town - Liberty Market   | 9.4             | 15.4                 |
| Township - Kalma Chowk        | 8.2             | 10.1                 |

## Q06 Daily revenue trend (first 10 days)

```sql
SELECT date, SUM(passengers) AS passengers, SUM(revenue_pkr) AS revenue_pkr FROM trips GROUP BY date ORDER BY date LIMIT 10;
```

| date       | passengers   | revenue_pkr   |
|:-----------|:-------------|:--------------|
| 2026-06-01 | 1948         | 133330        |
| 2026-06-02 | 2217         | 148730        |
| 2026-06-03 | 1994         | 137415        |
| 2026-06-04 | 2330         | 158790        |
| 2026-06-05 | 2099         | 143930        |
| 2026-06-06 | 1693         | 114155        |
| 2026-06-07 | 1694         | 112940        |
| 2026-06-08 | 2241         | 153310        |
| 2026-06-09 | 1977         | 135035        |
| 2026-06-10 | 2588         | 177840        |

## Q07 Weekday vs weekend performance

```sql
SELECT CASE w.is_weekend WHEN 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
       ROUND(AVG(t.passengers),1) AS avg_pax_per_trip, ROUND(AVG(t.delay_min),1) AS avg_delay
FROM trips t JOIN weather_days w USING(date) GROUP BY w.is_weekend;
```

| day_type   | avg_pax_per_trip   | avg_delay   |
|:-----------|:-------------------|:------------|
| Weekday    | 22.8               | 10.4        |
| Weekend    | 16.2               | 9.1         |

## Q08 Weather impact on delays and cancellations

```sql
SELECT w.weather, COUNT(*) AS trips, ROUND(AVG(t.delay_min),1) AS avg_delay_min,
       ROUND(100.0*SUM(t.status='Cancelled')/COUNT(*),2) AS cancel_rate_pct
FROM trips t JOIN weather_days w USING(date) GROUP BY w.weather ORDER BY avg_delay_min DESC;
```

| weather   | trips   | avg_delay_min   | cancel_rate_pct   |
|:----------|:--------|:----------------|:------------------|
| Rain      | 2593    | 14.0            | 5.05              |
| Fog       | 504     | 12.5            | 4.37              |
| Heat      | 1911    | 8.2             | 1.94              |
| Clear     | 3996    | 8.1             | 2.28              |

## Q09 Bus utilisation (occupancy) by capacity class

```sql
SELECT b.capacity, COUNT(*) AS trips, ROUND(100.0*AVG(t.passengers*1.0/b.capacity),1) AS avg_occupancy_pct
FROM trips t JOIN buses b USING(bus_id) WHERE t.status='Completed' GROUP BY b.capacity ORDER BY b.capacity;
```

| capacity   | trips   | avg_occupancy_pct   |
|:-----------|:--------|:--------------------|
| 40.0       | 2168.0  | 39.4                |
| 50.0       | 4807.0  | 43.8                |
| 60.0       | 1748.0  | 47.3                |

## Q10 Older buses vs delays

```sql
SELECT CASE WHEN b.bus_age_years<=4 THEN '0-4 yrs' WHEN b.bus_age_years<=8 THEN '5-8 yrs' ELSE '9+ yrs' END AS age_band,
       ROUND(AVG(t.delay_min),1) AS avg_delay_min, ROUND(100.0*SUM(t.status='Cancelled')/COUNT(*),2) AS cancel_rate_pct
FROM trips t JOIN buses b USING(bus_id) GROUP BY age_band ORDER BY age_band;
```

| age_band   | avg_delay_min   | cancel_rate_pct   |
|:-----------|:----------------|:------------------|
| 0-4 yrs    | 8.4             | 2.49              |
| 5-8 yrs    | 10.2            | 2.99              |
| 9+ yrs     | 11.3            | 3.73              |

## Q11 Top 5 buses by revenue

```sql
SELECT bus_id, SUM(revenue_pkr) AS revenue_pkr, SUM(passengers) AS passengers FROM trips GROUP BY bus_id ORDER BY revenue_pkr DESC LIMIT 5;
```

| bus_id   | revenue_pkr   | passengers   |
|:---------|:--------------|:-------------|
| B003     | 673440        | 8418         |
| B010     | 565290        | 6281         |
| B004     | 548400        | 6855         |
| B012     | 547830        | 6087         |
| B002     | 518880        | 6486         |

## Q12 Weekly revenue with week-over-week growth (window function)

```sql
WITH wk AS (SELECT strftime('%W',date) AS week, SUM(revenue_pkr) AS revenue FROM trips GROUP BY week)
SELECT week, revenue, ROUND(100.0*(revenue-LAG(revenue) OVER (ORDER BY week))/LAG(revenue) OVER (ORDER BY week),1) AS wow_growth_pct FROM wk;
```

| week   | revenue   | wow_growth_pct   |
|:-------|:----------|:-----------------|
| 22     | 949290    | nan              |
| 23     | 1006435   | 6.0              |
| 24     | 978085    | -2.8             |
| 25     | 1080995   | 10.5             |
| 26     | 1020730   | -5.6             |
| 27     | 995040    | -2.5             |
| 28     | 1028865   | 3.4              |
| 29     | 1029790   | 0.1              |
| 30     | 902045    | -12.4            |
| 31     | 1034425   | 14.7             |
| 32     | 927665    | -10.3            |
| 33     | 983825    | 6.1              |
| 34     | 915355    | -7.0             |

## Q13 Route rank by revenue within peak vs off-peak (window function)

```sql
SELECT * FROM (
  SELECT r.route_name, CASE WHEN t.departure_hour IN (8,9,17,18) THEN 'Peak' ELSE 'Off-peak' END AS period,
         SUM(t.revenue_pkr) AS revenue_pkr,
         RANK() OVER (PARTITION BY CASE WHEN t.departure_hour IN (8,9,17,18) THEN 'Peak' ELSE 'Off-peak' END ORDER BY SUM(t.revenue_pkr) DESC) AS rnk
  FROM trips t JOIN routes r USING(route_id) GROUP BY r.route_name, period) WHERE rnk<=3 ORDER BY period, rnk;
```

| route_name                   | period   | revenue_pkr   | rnk   |
|:-----------------------------|:---------|:--------------|:------|
| Green Town - Cantt Station   | Off-peak | 1000400       | 1     |
| Johar Town - Railway Station | Off-peak | 898830        | 2     |
| Iqbal Town - Anarkali        | Off-peak | 626665        | 3     |
| Green Town - Cantt Station   | Peak     | 1240000       | 1     |
| Johar Town - Railway Station | Peak     | 1177470       | 2     |
| Iqbal Town - Anarkali        | Peak     | 828555        | 3     |

## Q14 Underperforming route-hours (low occupancy, candidates to reduce service)

```sql
SELECT r.route_name, t.departure_hour, COUNT(*) AS trips, ROUND(100.0*AVG(t.passengers*1.0/b.capacity),1) AS avg_occupancy_pct
FROM trips t JOIN routes r USING(route_id) JOIN buses b USING(bus_id) WHERE t.status='Completed'
GROUP BY r.route_name, t.departure_hour HAVING trips>=20 AND avg_occupancy_pct<25 ORDER BY avg_occupancy_pct LIMIT 10;
```

| route_name                    | departure_hour   | trips   | avg_occupancy_pct   |
|:------------------------------|:-----------------|:--------|:--------------------|
| Bahria Town - Ferozepur Road  | 5                | 41      | 8.3                 |
| Wapda Town - Thokar Niaz Baig | 5                | 41      | 9.4                 |
| Township - Kalma Chowk        | 5                | 48      | 9.9                 |
| Bahria Town - Ferozepur Road  | 21               | 47      | 10.9                |
| Samanabad - Data Darbar       | 5                | 41      | 10.9                |
| DHA - Cantt Station           | 5                | 36      | 12.0                |
| Wapda Town - Thokar Niaz Baig | 21               | 39      | 12.4                |
| Gulberg - Mall Road           | 5                | 40      | 13.0                |
| Township - Kalma Chowk        | 21               | 48      | 13.4                |
| Iqbal Town - Anarkali         | 5                | 41      | 14.1                |
