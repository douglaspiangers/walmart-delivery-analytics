-- =============================================================================
-- Walmart Delivery Analytics — Staging Setup
-- SQL Server T-SQL
--
-- This script documents how the five raw CSV files are loaded into SQL Server.
-- The staging tables receive the data exactly as it comes — no cleaning here.
-- Cleaning and structuring happens in the views (scripts 03 and 04).
-- =============================================================================

USE WalmartDW;
GO

CREATE SCHEMA stg;
GO

-- =============================================================================
-- STAGING TABLES — one per CSV file, columns match the file headers exactly
-- =============================================================================

-- Source: orders.csv (9,999 rows)
-- Known issues documented in 01_raw_data_profile.sql
CREATE TABLE stg.orders (
    date            VARCHAR(10),    -- "2023-01-01"
    order_id        VARCHAR(40),    -- UUID
    order_amount    VARCHAR(20),    -- "$1,095.54" — has $ and comma
    region          VARCHAR(50),    -- "Winter Park"
    items_delivered SMALLINT,
    items_missing   SMALLINT,
    delivery_hour   VARCHAR(10),    -- "8:37:28" — time string, not typed
    driver_id       VARCHAR(15),
    customer_id     VARCHAR(15)
);

-- Source: drivers_data.csv (1,246 rows)
CREATE TABLE stg.drivers (
    driver_id   VARCHAR(15),
    driver_name VARCHAR(100),
    age         TINYINT,
    Trips       INT             -- will be dropped in the view (metric, not attribute)
);

-- Source: customers_data.csv (1,238 rows)
CREATE TABLE stg.customers (
    customer_id   VARCHAR(15),
    customer_name VARCHAR(100),
    customer_age  TINYINT
);

-- Source: products_data.csv (313 rows)
CREATE TABLE stg.products (
    produc_id    VARCHAR(25),    -- typo in source — kept as-is in staging
    product_name VARCHAR(100),
    category     VARCHAR(50),
    price        VARCHAR(15)     -- "$12.53" — has $
);

-- Source: missing_items_data.csv (1,500 rows)
CREATE TABLE stg.missing_items (
    order_id     VARCHAR(40),
    product_id_1 VARCHAR(25),   -- ┐ products stored as columns (pivoted)
    product_id_2 VARCHAR(25),   -- ├ will be unpivoted to rows in the view
    product_id_3 VARCHAR(25)    -- ┘ most rows have only product_id_1 filled
);
GO

-- =============================================================================
-- HOW TO LOAD THE CSVs
-- Use SSMS Import Wizard (right-click database → Tasks → Import Data)
-- or adapt the BULK INSERT templates below.
-- =============================================================================

/*
BULK INSERT stg.orders
FROM 'C:\path\to\orders.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', TABLOCK);

BULK INSERT stg.drivers
FROM 'C:\path\to\drivers_data.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', TABLOCK);

BULK INSERT stg.customers
FROM 'C:\path\to\customers_data.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', TABLOCK);

BULK INSERT stg.products
FROM 'C:\path\to\products_data.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', TABLOCK);

BULK INSERT stg.missing_items
FROM 'C:\path\to\missing_items_data.csv'
WITH (FIRSTROW = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '\n', TABLOCK);
*/

-- Quick check after loading — expected row counts
SELECT 'stg.orders'        AS tbl, COUNT(*) AS rows FROM stg.orders
UNION ALL SELECT 'stg.drivers',      COUNT(*) FROM stg.drivers
UNION ALL SELECT 'stg.customers',    COUNT(*) FROM stg.customers
UNION ALL SELECT 'stg.products',     COUNT(*) FROM stg.products
UNION ALL SELECT 'stg.missing_items',COUNT(*) FROM stg.missing_items;
GO
