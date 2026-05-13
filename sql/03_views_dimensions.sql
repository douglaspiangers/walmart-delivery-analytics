-- =============================================================================
-- Walmart Delivery Analytics — Dimension Views
-- SQL Server T-SQL
--
-- Five views that describe the context of each delivery:
--   WHEN  → vw_dim_date
--   WHERE → vw_dim_region
--   WHO delivered → vw_dim_driver
--   WHO received  → vw_dim_customer
--   WHAT was missing → vw_dim_product
--
-- These views sit on top of the staging tables. No data is duplicated.
-- Power BI connects directly to these views.
-- =============================================================================

USE WalmartDW;
GO

-- =============================================================================
-- vw_dim_date — full 2023 calendar
--
-- Generated from the date range present in stg.orders.
-- Provides the time breakdowns Power BI needs for trend analysis:
-- month, quarter, day of week, weekend flag.
--
-- Uses master..spt_values as a number sequence (avoids recursive CTE,
-- which cannot be used inside a view in SQL Server).
-- =============================================================================

CREATE OR ALTER VIEW vw_dim_date AS
SELECT
    CAST(FORMAT(d.full_date, 'yyyyMMdd') AS INT)                    AS date_key,
    d.full_date,
    YEAR(d.full_date)                                               AS year,
    DATEPART(QUARTER, d.full_date)                                  AS quarter,
    'Q' + CAST(DATEPART(QUARTER, d.full_date) AS VARCHAR)
        + ' ' + CAST(YEAR(d.full_date) AS VARCHAR)                  AS quarter_label,
    MONTH(d.full_date)                                              AS month_num,
    DATENAME(MONTH, d.full_date)                                    AS month_name,
    LEFT(DATENAME(MONTH, d.full_date), 3)
        + ' ' + CAST(YEAR(d.full_date) AS VARCHAR)                  AS month_label,
    DATEPART(WEEK,    d.full_date)                                  AS week_of_year,
    DAY(d.full_date)                                                AS day_of_month,
    DATEPART(WEEKDAY, d.full_date)                                  AS day_of_week,
    DATENAME(WEEKDAY, d.full_date)                                  AS day_name,
    CASE WHEN DATEPART(WEEKDAY, d.full_date) IN (1,7) THEN 1
         ELSE 0 END                                                 AS is_weekend
FROM (
    SELECT DATEADD(DAY, number, '2023-01-01') AS full_date
    FROM master..spt_values
    WHERE type = 'P'
      AND number BETWEEN 0 AND 364
) d;
GO

-- =============================================================================
-- vw_dim_region — the 7 delivery zones
--
-- Extracted from the distinct region values in stg.orders.
-- DENSE_RANK generates a stable numeric ID for each zone — used as the
-- join key between vw_fact_orders and this view in Power BI.
-- =============================================================================

CREATE OR ALTER VIEW vw_dim_region AS
SELECT
    DENSE_RANK() OVER (ORDER BY region)  AS region_id,
    region                               AS region_name
FROM (
    SELECT DISTINCT region
    FROM stg.orders
    WHERE region IS NOT NULL
) r;
GO

-- =============================================================================
-- vw_dim_driver — the delivery drivers
--
-- age_group added to enable customer demographic analysis without needing
-- to create calculated columns in Power BI.
-- Trips column removed — that count is computed from fact_orders at query time.
-- =============================================================================

CREATE OR ALTER VIEW vw_dim_driver AS
SELECT
    driver_id,
    driver_name,
    age,
    CASE
        WHEN age BETWEEN 18 AND 29 THEN '18-29'
        WHEN age BETWEEN 30 AND 44 THEN '30-44'
        WHEN age BETWEEN 45 AND 59 THEN '45-59'
        ELSE '60+'
    END AS age_group
FROM stg.drivers;
GO

-- =============================================================================
-- vw_dim_customer — the customers who received the deliveries
--
-- age_group added for the same reason as vw_dim_driver.
-- =============================================================================

CREATE OR ALTER VIEW vw_dim_customer AS
SELECT
    customer_id,
    customer_name,
    customer_age                                AS age,
    CASE
        WHEN customer_age BETWEEN 18 AND 29 THEN '18-29'
        WHEN customer_age BETWEEN 30 AND 44 THEN '30-44'
        WHEN customer_age BETWEEN 45 AND 59 THEN '45-59'
        ELSE '60+'
    END                                         AS age_group
FROM stg.customers;
GO

-- =============================================================================
-- vw_dim_product — products that were reported as missing
--
-- Fixes the column name typo (produc_id → product_id).
-- Cleans the price field: removes the $ sign and casts to DECIMAL.
-- =============================================================================

CREATE OR ALTER VIEW vw_dim_product AS
SELECT
    produc_id                                           AS product_id,
    product_name,
    category,
    CAST(REPLACE(price, '$', '') AS DECIMAL(8,2))       AS unit_price
FROM stg.products;
GO


-- =============================================================================
-- QUICK CHECKS — run after creating the views to confirm they return data
-- =============================================================================

SELECT COUNT(*) AS date_rows  FROM vw_dim_date;      -- expect 365
SELECT COUNT(*) AS regions    FROM vw_dim_region;     -- expect 7
SELECT COUNT(*) AS drivers    FROM vw_dim_driver;     -- expect 1,246
SELECT COUNT(*) AS customers  FROM vw_dim_customer;   -- expect 1,238
SELECT COUNT(*) AS products   FROM vw_dim_product;    -- expect 313
GO

-- Age group distribution — customers
SELECT age_group, COUNT(*) AS customers
FROM vw_dim_customer
GROUP BY age_group
ORDER BY age_group;
GO

-- Product categories
SELECT category, COUNT(*) AS products, ROUND(AVG(unit_price), 2) AS avg_price
FROM vw_dim_product
GROUP BY category
ORDER BY products DESC;
GO
