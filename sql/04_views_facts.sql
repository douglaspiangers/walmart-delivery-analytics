-- =============================================================================
-- Walmart Delivery Analytics — Fact Views
-- SQL Server T-SQL
--
-- Two views that capture the measurable events:
--   vw_fact_orders        → every delivery (9,999 rows)
--   vw_fact_missing_items → every missing product per order (unpivoted)
--
-- Run after 03_views_dimensions.sql — vw_fact_orders references vw_dim_region.
-- =============================================================================

USE WalmartDW;
GO

-- =============================================================================
-- vw_fact_orders — the main fact: one row per delivery
--
-- Transformations applied to the raw data:
--
--   order_amount   "$1,095.54"  →  1095.54     (removes $ and comma, casts to DECIMAL)
--   delivery_hour  "8:37:28"    →  8           (extracts the hour as an integer 0–23)
--   date           "2023-01-01" →  20230101    (integer key for joining to vw_dim_date)
--   region         "Winter Park" → region_id   (numeric key from vw_dim_region)
--   has_missing    derived       →  1 or 0     (flag: did this order have missing items?)
-- =============================================================================

CREATE OR ALTER VIEW vw_fact_orders AS
SELECT
    o.order_id,

    CAST(FORMAT(CAST(o.date AS DATE), 'yyyyMMdd') AS INT)           AS date_key,
    CAST(o.date AS DATE)                                            AS order_date,

    r.region_id,
    o.region                                                        AS region_name,

    o.driver_id,
    o.customer_id,

    CAST(
        REPLACE(REPLACE(o.order_amount, '$', ''), ',', '')
    AS DECIMAL(10,2))                                               AS order_amount,

    o.items_delivered,
    o.items_missing,

    DATEPART(HOUR, CAST(o.delivery_hour AS TIME))                   AS delivery_hour,

    CASE WHEN o.items_missing > 0 THEN 1 ELSE 0 END                 AS has_missing

FROM stg.orders o
JOIN vw_dim_region r ON o.region = r.region_name;
GO

-- =============================================================================
-- vw_fact_missing_items — one row per missing product per order
--
-- The raw table stg.missing_items stores products as three separate columns:
--
--   order_id  | product_id_1     | product_id_2     | product_id_3
--   ──────────┼──────────────────┼──────────────────┼─────────────
--   order-001 │ PWPX...982       │ NULL             │ NULL         → 1 product missing
--   order-002 │ PWPX...985       │ PWPX...986       │ NULL         → 2 products missing
--   order-003 │ PWPX...990       │ PWPX...991       │ PWPX...992  → 3 products missing
--
-- This structure cannot be related to dim_product in Power BI.
-- The UNPIVOT below converts it to one row per missing product:
--
--   order_id  | product_id   | position
--   ──────────┼──────────────┼──────────
--   order-001 │ PWPX...982   │ 1
--   order-002 │ PWPX...985   │ 1
--   order-002 │ PWPX...986   │ 2
--   order-003 │ PWPX...990   │ 1
--   order-003 │ PWPX...991   │ 2
--   order-003 │ PWPX...992   │ 3
--
-- NULLs are excluded automatically by UNPIVOT.
-- =============================================================================

CREATE OR ALTER VIEW vw_fact_missing_items AS
SELECT
    order_id,
    product_id,
    CAST(REPLACE(col_name, 'product_id_', '') AS TINYINT)   AS position
FROM stg.missing_items
UNPIVOT (
    product_id FOR col_name IN (product_id_1, product_id_2, product_id_3)
) AS unpvt;
GO


-- =============================================================================
-- VALIDATION — run after creating the views
-- =============================================================================

-- Row counts
SELECT COUNT(*)                         AS total_orders       FROM vw_fact_orders;
SELECT COUNT(*)                         AS missing_item_rows  FROM vw_fact_missing_items;
SELECT COUNT(DISTINCT order_id)         AS orders_with_missing FROM vw_fact_missing_items;
GO

-- Overall missing item rate
SELECT
    COUNT(*)                                                    AS total_orders,
    SUM(has_missing)                                            AS orders_with_missing,
    CAST(SUM(has_missing) * 100.0 / COUNT(*) AS DECIMAL(5,1))  AS missing_rate_pct,
    ROUND(SUM(order_amount), 2)                                 AS total_revenue,
    ROUND(AVG(order_amount), 2)                                 AS avg_order_value
FROM vw_fact_orders;
GO

-- Missing rate by region
SELECT
    region_name,
    COUNT(*)                                                    AS orders,
    SUM(has_missing)                                            AS missing_orders,
    CAST(SUM(has_missing) * 100.0 / COUNT(*) AS DECIMAL(5,1))  AS missing_rate_pct,
    ROUND(AVG(order_amount), 2)                                 AS avg_order_value
FROM vw_fact_orders
GROUP BY region_id, region_name
ORDER BY missing_rate_pct DESC;
GO

-- Missing rate by month
SELECT
    d.month_label,
    COUNT(*)                                                    AS orders,
    SUM(f.has_missing)                                          AS missing_orders,
    CAST(SUM(f.has_missing) * 100.0 / COUNT(*) AS DECIMAL(5,1)) AS missing_rate_pct
FROM vw_fact_orders f
JOIN vw_dim_date d ON f.date_key = d.date_key
GROUP BY d.month_num, d.month_label
ORDER BY d.month_num;
GO

-- Top 10 drivers with highest missing rate (min 20 deliveries)
SELECT TOP 10
    d.driver_name,
    d.age_group,
    COUNT(*)                                                    AS deliveries,
    SUM(f.has_missing)                                          AS missing_orders,
    CAST(SUM(f.has_missing) * 100.0 / COUNT(*) AS DECIMAL(5,1)) AS missing_rate_pct
FROM vw_fact_orders f
JOIN vw_dim_driver d ON f.driver_id = d.driver_id
GROUP BY d.driver_id, d.driver_name, d.age_group
HAVING COUNT(*) >= 20
ORDER BY missing_rate_pct DESC;
GO

-- Most frequently missing products
SELECT TOP 10
    p.product_name,
    p.category,
    p.unit_price,
    COUNT(*)                                                    AS times_missing
FROM vw_fact_missing_items m
JOIN vw_dim_product p ON m.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.unit_price
ORDER BY times_missing DESC;
GO

-- Missing rate by customer age group
SELECT
    c.age_group,
    COUNT(*)                                                    AS orders,
    SUM(f.has_missing)                                          AS missing_orders,
    CAST(SUM(f.has_missing) * 100.0 / COUNT(*) AS DECIMAL(5,1)) AS missing_rate_pct
FROM vw_fact_orders f
JOIN vw_dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.age_group
ORDER BY c.age_group;
GO
