-- =============================================================================
-- Walmart Delivery Analytics — Load Dimensions
-- SQL Server T-SQL
--
-- Reads from stg.* (raw CSV loads) and inserts into dw.dim_*.
-- Run this script before 04_load_facts.sql.
-- Order within this script matters: dim_date and dim_region must be loaded
-- before fact_orders references them.
-- =============================================================================

USE WalmartDW;
GO

-- =============================================================================
-- dim_date — generated from the full 2023 calendar
-- Not loaded from staging; built directly via recursive CTE.
-- =============================================================================

WITH calendar AS (
    SELECT CAST('2023-01-01' AS DATE) AS d
    UNION ALL
    SELECT DATEADD(DAY, 1, d)
    FROM calendar
    WHERE d < '2023-12-31'
)
INSERT INTO dw.dim_date (
    date_key, full_date, year, quarter, quarter_label,
    month_num, month_name, month_label,
    week_of_year, day_of_month, day_of_week, day_name, is_weekend
)
SELECT
    CAST(FORMAT(d, 'yyyyMMdd') AS INT)                          AS date_key,
    d                                                           AS full_date,
    YEAR(d)                                                     AS year,
    DATEPART(QUARTER, d)                                        AS quarter,
    'Q' + CAST(DATEPART(QUARTER, d) AS VARCHAR) + ' '
        + CAST(YEAR(d) AS VARCHAR)                              AS quarter_label,
    MONTH(d)                                                    AS month_num,
    DATENAME(MONTH, d)                                          AS month_name,
    LEFT(DATENAME(MONTH, d), 3) + ' ' + CAST(YEAR(d) AS VARCHAR) AS month_label,
    DATEPART(WEEK, d)                                           AS week_of_year,
    DAY(d)                                                      AS day_of_month,
    DATEPART(WEEKDAY, d)                                        AS day_of_week,
    DATENAME(WEEKDAY, d)                                        AS day_name,
    CASE WHEN DATEPART(WEEKDAY, d) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend
FROM calendar
OPTION (MAXRECURSION 400);
GO

-- Verify
SELECT COUNT(*) AS date_rows, MIN(full_date) AS first, MAX(full_date) AS last
FROM dw.dim_date;
GO

-- =============================================================================
-- dim_region — extracted from distinct values in stg.orders
-- =============================================================================

INSERT INTO dw.dim_region (region_name)
SELECT DISTINCT region
FROM stg.orders
WHERE region IS NOT NULL
ORDER BY region;
GO

-- Verify (expect 7 rows)
SELECT * FROM dw.dim_region ORDER BY region_id;
GO

-- =============================================================================
-- dim_drivers — cleaned from stg.drivers
-- Trips column dropped (metric belongs in fact, not dimension)
-- =============================================================================

INSERT INTO dw.dim_drivers (driver_id, driver_name, age)
SELECT
    driver_id,
    driver_name,
    age
FROM stg.drivers;
GO

-- Verify
SELECT COUNT(*) AS driver_rows FROM dw.dim_drivers;
GO

-- =============================================================================
-- dim_customers — cleaned from stg.customers
-- Adds age_group derived column
-- =============================================================================

INSERT INTO dw.dim_customers (customer_id, customer_name, customer_age, age_group)
SELECT
    customer_id,
    customer_name,
    customer_age,
    CASE
        WHEN customer_age BETWEEN 18 AND 29 THEN '18-29'
        WHEN customer_age BETWEEN 30 AND 44 THEN '30-44'
        WHEN customer_age BETWEEN 45 AND 59 THEN '45-59'
        ELSE '60+'
    END AS age_group
FROM stg.customers;
GO

-- Verify — check age group distribution
SELECT age_group, COUNT(*) AS customers
FROM dw.dim_customers
GROUP BY age_group
ORDER BY age_group;
GO

-- =============================================================================
-- dim_products — cleaned from stg.products
-- Fixes: produc_id typo → product_id, price VARCHAR → DECIMAL
-- =============================================================================

INSERT INTO dw.dim_products (product_id, product_name, category, unit_price)
SELECT
    produc_id                                                       AS product_id,
    product_name,
    category,
    CAST(REPLACE(price, '$', '') AS DECIMAL(8,2))                  AS unit_price
FROM stg.products
WHERE produc_id IS NOT NULL;
GO

-- Verify — check category distribution
SELECT category, COUNT(*) AS products, ROUND(AVG(unit_price), 2) AS avg_price
FROM dw.dim_products
GROUP BY category
ORDER BY products DESC;
GO
