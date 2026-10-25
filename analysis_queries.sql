-- name: kpi_overview
SELECT COUNT(*) AS orders,
       ROUND(AVG(total_min), 1) AS avg_delivery_min,
       ROUND(100.0 * AVG(delayed), 1) AS delayed_pct,
       ROUND(100.0 * AVG(cancelled), 2) AS cancelled_pct,
       ROUND(AVG(rating), 2) AS avg_rating
FROM orders;

-- name: delay_by_hour
SELECT hour, COUNT(*) AS orders, ROUND(100.0 * AVG(delayed), 1) AS delayed_pct,
       ROUND(AVG(rider_wait_min), 2) AS avg_rider_wait
FROM orders GROUP BY hour ORDER BY hour;

-- name: delay_by_store
SELECT s.city, s.area, s.riders_on_roster, s.avg_distance_km, COUNT(*) AS orders,
       ROUND(100.0 * AVG(o.delayed), 1) AS delayed_pct,
       ROUND(AVG(o.rider_wait_min), 2) AS avg_rider_wait,
       ROUND(AVG(o.travel_min), 1) AS avg_travel
FROM orders o JOIN stores s USING (store_id)
GROUP BY s.store_id ORDER BY delayed_pct DESC;

-- name: delay_by_rain
SELECT CASE WHEN rain THEN 'Rain' ELSE 'Dry' END AS weather, COUNT(*) AS orders,
       ROUND(100.0 * AVG(delayed), 1) AS delayed_pct, ROUND(AVG(travel_min), 1) AS avg_travel
FROM orders GROUP BY rain;

-- name: delay_stage_breakdown
-- Where do minutes go for delayed vs on-time orders?
SELECT CASE WHEN delayed THEN 'Delayed' ELSE 'On time' END AS status,
       ROUND(AVG(pick_pack_min), 1) AS pick_pack, ROUND(AVG(rider_wait_min), 1) AS rider_wait,
       ROUND(AVG(travel_min), 1) AS travel, ROUND(AVG(total_min), 1) AS total
FROM orders GROUP BY delayed;

-- name: rider_capacity_buckets
-- Riders available per order in the store-hour (roster/3 assumed active per hour)
WITH x AS (
  SELECT o.*, (s.riders_on_roster / 3.0) / o.orders_in_store_hour AS riders_per_order
  FROM orders o JOIN stores s USING (store_id))
SELECT CASE WHEN riders_per_order < 0.5 THEN '1: <0.5 riders/order'
            WHEN riders_per_order < 1.0 THEN '2: 0.5-1.0'
            WHEN riders_per_order < 2.0 THEN '3: 1.0-2.0' ELSE '4: 2.0+' END AS capacity_bucket,
       COUNT(*) AS orders, ROUND(100.0 * AVG(delayed), 1) AS delayed_pct,
       ROUND(AVG(rider_wait_min), 2) AS avg_rider_wait
FROM x GROUP BY capacity_bucket ORDER BY capacity_bucket;

-- name: lateness_vs_rating_cancel
SELECT CASE WHEN total_min - promised_min <= 0 THEN '0: On time'
            WHEN total_min - promised_min <= 2 THEN '1: Up to 2 min late'
            WHEN total_min - promised_min <= 5 THEN '2: 2-5 min late' ELSE '3: 5+ min late' END AS lateness,
       COUNT(*) AS orders, ROUND(AVG(rating), 2) AS avg_rating, ROUND(100.0 * AVG(cancelled), 2) AS cancel_pct
FROM orders GROUP BY lateness ORDER BY lateness;

-- name: revenue_at_risk
SELECT ROUND(SUM(order_value_inr)) AS cancelled_value_inr, COUNT(*) AS cancelled_orders
FROM orders WHERE cancelled = 1;
