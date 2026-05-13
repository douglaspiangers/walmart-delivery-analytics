-- Walmart Delivery Analytics — Dimension Views
-- SQL Server T-SQL
-- Run before views_facts.sql

-- vw_dim_date
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

-- vw_dim_region
CREATE OR ALTER VIEW vw_dim_region AS
SELECT
    DENSE_RANK() OVER (ORDER BY region)  AS region_id,
    region                               AS region_name
FROM (
    SELECT DISTINCT region
    FROM orders
    WHERE region IS NOT NULL
) r;
GO

-- vw_dim_driver
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
    END AS age_group,
    Trips AS total_trips
FROM drivers;
GO

-- vw_dim_customer
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
FROM customers;
GO

-- vw_dim_product
CREATE OR ALTER VIEW vw_dim_product AS
SELECT
    produc_id                                           AS product_id,
    product_name,
    category,
    CAST(REPLACE(price, '$', '') AS DECIMAL(8,2))       AS unit_price
FROM products;
GO
