-- =============================================================================
-- Walmart Delivery Analytics — Raw Data Profile
-- SQL Server T-SQL
--
-- This script documents the structure of the five source files exactly as
-- they arrive, identifies every data quality issue, and justifies each
-- transformation decision made in the scripts that follow.
-- =============================================================================

USE WalmartDW;
GO

-- =============================================================================
-- SECTION 1 — SOURCE TABLE STRUCTURES (as loaded from CSV)
-- =============================================================================
--
-- stg.orders         (9,999 rows)
-- ─────────────────────────────────────────────────────────────────
--  date            VARCHAR   "2023-01-01"          → needs CAST to DATE
--  order_id        VARCHAR   UUID format            → clean, use as-is
--  order_amount    VARCHAR   "$1,095.54"            → has $ and comma, not numeric
--  region          VARCHAR   "Winter Park"          → 7 distinct values, no FK
--  items_delivered SMALLINT  clean
--  items_missing   SMALLINT  clean
--  delivery_hour   VARCHAR   "8:37:28" / "14:02:01" → time string, extract HOUR only
--  driver_id       VARCHAR   "WDID10627"            → clean, FK to drivers
--  customer_id     VARCHAR   "WCID5031"             → clean, FK to customers
--
-- stg.drivers        (1,246 rows)
-- ─────────────────────────────────────────────────────────────────
--  driver_id       VARCHAR   clean
--  driver_name     VARCHAR   clean
--  age             TINYINT   clean
--  Trips           INT       column name inconsistent (PascalCase vs rest);
--                            value is a static count — should be computed
--                            from fact_orders, not stored as an attribute
--
-- stg.customers      (1,238 rows)
-- ─────────────────────────────────────────────────────────────────
--  customer_id     VARCHAR   clean
--  customer_name   VARCHAR   clean
--  customer_age    TINYINT   clean — age_group will be derived in dim_customers
--
-- stg.products       (313 rows)
-- ─────────────────────────────────────────────────────────────────
--  produc_id       VARCHAR   TYPO in column name → rename to product_id
--  product_name    VARCHAR   clean
--  category        VARCHAR   clean
--  price           VARCHAR   "$12.53" format → strip $ before casting
--
-- stg.missing_items  (1,500 rows)
-- ─────────────────────────────────────────────────────────────────
--  order_id        VARCHAR   FK to orders
--  product_id_1    VARCHAR   ┐
--  product_id_2    VARCHAR   ├─ PIVOTED structure — products stored as columns
--  product_id_3    VARCHAR   ┘  Must be UNPIVOTED to rows for star schema
--
-- =============================================================================
-- SECTION 2 — DATA QUALITY CHECKS
-- Run these against the staging tables after loading the CSVs.
-- =============================================================================

-- 2.1 — Row counts
SELECT 'stg.orders'        AS tbl, COUNT(*) AS rows FROM stg.orders
UNION ALL SELECT 'stg.drivers',    COUNT(*) FROM stg.drivers
UNION ALL SELECT 'stg.customers',  COUNT(*) FROM stg.customers
UNION ALL SELECT 'stg.products',   COUNT(*) FROM stg.products
UNION ALL SELECT 'stg.missing_items', COUNT(*) FROM stg.missing_items;
GO

-- 2.2 — NULL audit across key columns
SELECT
    SUM(CASE WHEN order_id       IS NULL THEN 1 ELSE 0 END) AS null_order_id,
    SUM(CASE WHEN order_amount   IS NULL THEN 1 ELSE 0 END) AS null_amount,
    SUM(CASE WHEN region         IS NULL THEN 1 ELSE 0 END) AS null_region,
    SUM(CASE WHEN driver_id      IS NULL THEN 1 ELSE 0 END) AS null_driver,
    SUM(CASE WHEN customer_id    IS NULL THEN 1 ELSE 0 END) AS null_customer,
    SUM(CASE WHEN delivery_hour  IS NULL THEN 1 ELSE 0 END) AS null_hour
FROM stg.orders;
GO

-- 2.3 — order_amount format check: how many rows have non-numeric characters?
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN order_amount LIKE '$%' THEN 1 ELSE 0 END) AS has_dollar_sign,
    SUM(CASE WHEN order_amount LIKE '%,%' THEN 1 ELSE 0 END) AS has_comma,
    MIN(LEN(order_amount)) AS min_len,
    MAX(LEN(order_amount)) AS max_len
FROM stg.orders;
GO

-- 2.4 — delivery_hour: verify it always parses as a valid time
SELECT TOP 5
    delivery_hour,
    TRY_CAST(delivery_hour AS TIME) AS parsed_time,
    DATEPART(HOUR, TRY_CAST(delivery_hour AS TIME)) AS hour_extracted
FROM stg.orders;
GO

-- 2.5 — Region distribution (confirms 7 distinct values)
SELECT region, COUNT(*) AS order_count
FROM stg.orders
GROUP BY region
ORDER BY order_count DESC;
GO

-- 2.6 — Missing items: how many orders have 1, 2, or 3 missing products?
SELECT
    CASE
        WHEN product_id_2 IS NULL THEN '1 item missing'
        WHEN product_id_3 IS NULL THEN '2 items missing'
        ELSE '3 items missing'
    END AS missing_count,
    COUNT(*) AS orders
FROM stg.missing_items
GROUP BY
    CASE
        WHEN product_id_2 IS NULL THEN '1 item missing'
        WHEN product_id_3 IS NULL THEN '2 items missing'
        ELSE '3 items missing'
    END;
GO

-- 2.7 — Referential integrity: orders with no matching driver
SELECT COUNT(*) AS orphan_orders
FROM stg.orders o
LEFT JOIN stg.drivers d ON o.driver_id = d.driver_id
WHERE d.driver_id IS NULL;
GO

-- 2.8 — Referential integrity: orders with no matching customer
SELECT COUNT(*) AS orphan_orders
FROM stg.orders o
LEFT JOIN stg.customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
GO

-- 2.9 — products in missing_items that don't exist in stg.products
SELECT COUNT(DISTINCT m.product_id_1) AS unmatched_products
FROM stg.missing_items m
LEFT JOIN stg.products p ON m.product_id_1 = p.produc_id
WHERE p.produc_id IS NULL;
GO

-- 2.10 — Date range and order volume per month
SELECT
    FORMAT(CAST(date AS DATE), 'yyyy-MM') AS month,
    COUNT(*) AS orders,
    ROUND(SUM(CAST(REPLACE(REPLACE(order_amount,'$',''),',','') AS DECIMAL(10,2))), 2) AS total_revenue
FROM stg.orders
GROUP BY FORMAT(CAST(date AS DATE), 'yyyy-MM')
ORDER BY month;
GO

-- =============================================================================
-- SECTION 3 — PROBLEMS SUMMARY AND TRANSFORMATION DECISIONS
-- =============================================================================
--
-- PROBLEM                      TRANSFORMATION
-- ─────────────────────────────────────────────────────────────────────────────
-- order_amount is VARCHAR       REPLACE('$','') + REPLACE(',','') → DECIMAL(10,2)
-- delivery_hour is VARCHAR      DATEPART(HOUR, CAST(... AS TIME)) → TINYINT (0-23)
-- region is loose text          Extracted to dim_region with surrogate INT key
-- Trips column in drivers       Dropped — metric computed from fact_orders at query time
-- produc_id typo                Aliased to product_id in all downstream references
-- price is VARCHAR              Same cleaning as order_amount → DECIMAL(8,2)
-- missing_items is PIVOTED      UNPIVOT to one row per missing product per order
-- No date dimension             dim_date generated for full year 2023
-- No has_missing flag           Derived: CASE WHEN items_missing > 0 THEN 1 ELSE 0 END
-- ─────────────────────────────────────────────────────────────────────────────
