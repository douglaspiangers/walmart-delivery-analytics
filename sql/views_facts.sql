-- Walmart Delivery Analytics — Fact Views
-- SQL Server T-SQL
-- Run after views_dimensions.sql

-- vw_fact_orders
CREATE OR ALTER VIEW vw_fact_orders AS
SELECT
    o.order_id,

    CAST(FORMAT(CAST(o.date AS DATE), 'yyyyMMdd') AS INT)           AS date_key,

    r.region_id,

    o.driver_id,
    o.customer_id,

    CAST(
        REPLACE(REPLACE(o.order_amount, '$', ''), ',', '')
    AS DECIMAL(10,2))                                               AS order_amount,

    o.items_delivered,
    o.items_missing,

    DATEPART(HOUR, CAST(o.delivery_hour AS TIME))                   AS delivery_hour,

    CASE WHEN o.items_missing > 0 THEN 1 ELSE 0 END                 AS has_missing

FROM orders o
JOIN vw_dim_region r ON o.region = r.region_name;
GO

-- vw_fact_missing_items
CREATE OR ALTER VIEW vw_fact_missing_items AS
SELECT
    order_id,
    product_id,
    CAST(REPLACE(col_name, 'product_id_', '') AS TINYINT)   AS position
FROM missing_items
UNPIVOT (
    product_id FOR col_name IN (product_id_1, product_id_2, product_id_3)
) AS unpvt;
GO
