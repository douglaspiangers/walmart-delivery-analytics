-- =============================================================================
-- Walmart Delivery Analytics — Load Facts
-- SQL Server T-SQL
--
-- Runs after 03_load_dimensions.sql. Loads fact_orders and fact_missing_items.
-- fact_missing_items requires fact_orders to be populated first (FK constraint).
-- =============================================================================

USE WalmartDW;
GO

-- =============================================================================
-- fact_orders — main grain: one row per delivery order
--
-- Transformations applied:
--   order_amount  : REPLACE '$' and ',' → DECIMAL(10,2)
--   delivery_hour : CAST to TIME → DATEPART(HOUR) → TINYINT
--   date          : CAST to DATE → FORMAT as YYYYMMDD INT → FK to dim_date
--   region        : lookup surrogate key from dim_region
--   has_missing   : derived flag from items_missing > 0
-- =============================================================================

INSERT INTO dw.fact_orders (
    order_id,
    date_key,
    region_id,
    driver_id,
    customer_id,
    order_amount,
    items_delivered,
    items_missing,
    delivery_hour,
    has_missing
)
SELECT
    o.order_id,

    CAST(FORMAT(CAST(o.date AS DATE), 'yyyyMMdd') AS INT)           AS date_key,

    r.region_id,

    o.driver_id,
    o.customer_id,

    CAST(
        REPLACE(REPLACE(o.order_amount, '$', ''), ',', '')
    AS DECIMAL(10,2))                                                AS order_amount,

    o.items_delivered,
    o.items_missing,

    DATEPART(HOUR, CAST(o.delivery_hour AS TIME))                    AS delivery_hour,

    CASE WHEN o.items_missing > 0 THEN 1 ELSE 0 END                  AS has_missing

FROM stg.orders o
JOIN dw.dim_region r ON o.region = r.region_name;
GO

-- Verify
SELECT
    COUNT(*)                            AS total_orders,
    SUM(CAST(has_missing AS INT))       AS orders_with_missing,
    ROUND(
        SUM(CAST(has_missing AS INT)) * 100.0 / COUNT(*), 1
    )                                   AS missing_rate_pct,
    ROUND(SUM(order_amount), 2)         AS total_revenue,
    ROUND(AVG(order_amount), 2)         AS avg_order_value
FROM dw.fact_orders;
GO

-- =============================================================================
-- fact_missing_items — grain: one row per missing product per order
--
-- The source table stg.missing_items is PIVOTED (products as columns):
--
--   order_id  | product_id_1 | product_id_2 | product_id_3
--   ──────────┼──────────────┼──────────────┼─────────────
--   order-001 │ PWPX...982   │ PWPX...983   │ NULL
--   order-002 │ PWPX...985   │ PWPX...985   │ PWPX...986
--
-- After UNPIVOT:
--
--   order_id  | product_id  | item_position
--   ──────────┼─────────────┼──────────────
--   order-001 │ PWPX...982  │ 1
--   order-001 │ PWPX...983  │ 2
--   order-002 │ PWPX...985  │ 1
--   order-002 │ PWPX...985  │ 2
--   order-002 │ PWPX...986  │ 3
--
-- NULLs are excluded (not every order has 3 missing products).
-- =============================================================================

INSERT INTO dw.fact_missing_items (order_id, product_id, item_position)
SELECT
    order_id,
    product_id,
    CAST(REPLACE(item_position, 'product_id_', '') AS TINYINT) AS item_position
FROM stg.missing_items
UNPIVOT (
    product_id FOR item_position IN (product_id_1, product_id_2, product_id_3)
) AS unpvt
WHERE product_id IS NOT NULL;
GO

-- Verify — row count after UNPIVOT and distribution by position
SELECT
    COUNT(*)                        AS total_missing_item_rows,
    COUNT(DISTINCT order_id)        AS orders_affected,
    COUNT(DISTINCT product_id)      AS distinct_missing_products
FROM dw.fact_missing_items;
GO

SELECT
    item_position,
    COUNT(*) AS occurrences
FROM dw.fact_missing_items
GROUP BY item_position
ORDER BY item_position;
GO

-- =============================================================================
-- SECTION 3 — VALIDATION QUERIES
-- Cross-check that the star schema is consistent before connecting to Power BI
-- =============================================================================

-- 3.1 — All FK references resolve (zero orphans expected)
SELECT 'fact_orders → dim_date'    AS check_name,
       COUNT(*) AS orphans
FROM dw.fact_orders f
LEFT JOIN dw.dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL
UNION ALL
SELECT 'fact_orders → dim_region',   COUNT(*)
FROM dw.fact_orders f
LEFT JOIN dw.dim_region r ON f.region_id = r.region_id
WHERE r.region_id IS NULL
UNION ALL
SELECT 'fact_orders → dim_drivers',  COUNT(*)
FROM dw.fact_orders f
LEFT JOIN dw.dim_drivers d ON f.driver_id = d.driver_id
WHERE d.driver_id IS NULL
UNION ALL
SELECT 'fact_orders → dim_customers', COUNT(*)
FROM dw.fact_orders f
LEFT JOIN dw.dim_customers c ON f.customer_id = c.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'fact_missing_items → fact_orders', COUNT(*)
FROM dw.fact_missing_items m
LEFT JOIN dw.fact_orders o ON m.order_id = o.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'fact_missing_items → dim_products', COUNT(*)
FROM dw.fact_missing_items m
LEFT JOIN dw.dim_products p ON m.product_id = p.product_id
WHERE p.product_id IS NULL;
GO

-- 3.2 — Revenue by region (quick sanity check)
SELECT
    r.region_name,
    COUNT(*)                            AS orders,
    ROUND(SUM(f.order_amount), 2)       AS total_revenue,
    ROUND(AVG(f.order_amount), 2)       AS avg_order,
    SUM(CAST(f.has_missing AS INT))     AS missing_orders,
    ROUND(SUM(CAST(f.has_missing AS INT)) * 100.0 / COUNT(*), 1) AS missing_rate_pct
FROM dw.fact_orders f
JOIN dw.dim_region r ON f.region_id = r.region_id
GROUP BY r.region_name
ORDER BY total_revenue DESC;
GO

-- 3.3 — Monthly trend
SELECT
    d.month_label,
    COUNT(*)                           AS orders,
    ROUND(SUM(f.order_amount), 2)      AS revenue,
    ROUND(SUM(CAST(f.has_missing AS INT)) * 100.0 / COUNT(*), 1) AS missing_rate_pct
FROM dw.fact_orders f
JOIN dw.dim_date d ON f.date_key = d.date_key
GROUP BY d.month_label, d.month_num
ORDER BY d.month_num;
GO

-- 3.4 — Top 10 drivers by missing item rate (min 20 deliveries)
SELECT TOP 10
    dr.driver_name,
    COUNT(fo.order_id)                  AS deliveries,
    SUM(CAST(fo.has_missing AS INT))    AS missing_orders,
    ROUND(SUM(CAST(fo.has_missing AS INT)) * 100.0 / COUNT(*), 1) AS missing_rate_pct
FROM dw.fact_orders fo
JOIN dw.dim_drivers dr ON fo.driver_id = dr.driver_id
GROUP BY dr.driver_id, dr.driver_name
HAVING COUNT(fo.order_id) >= 20
ORDER BY missing_rate_pct DESC;
GO

-- 3.5 — Most frequently missing products
SELECT TOP 10
    p.product_name,
    p.category,
    COUNT(*) AS times_missing
FROM dw.fact_missing_items m
JOIN dw.dim_products p ON m.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY times_missing DESC;
GO
