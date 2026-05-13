-- =============================================================================
-- Walmart Delivery Analytics — Star Schema DDL
-- SQL Server T-SQL
--
-- Creates the staging schema (stg) for raw CSV loads and the data warehouse
-- schema (dw) with the full star schema. Load order: dimensions first, then
-- facts. fact_missing_items depends on both fact_orders and dim_products.
--
--  ┌─────────────┐
--  │  dim_date   │
--  └──────┬──────┘
--         │
--  ┌──────▼──────────────────────────────────────┐
--  │              fact_orders                     │
--  │  date_key ──► dim_date                       │
--  │  region_id ──► dim_region                    │
--  │  driver_id ──► dim_drivers                   │
--  │  customer_id ──► dim_customers               │
--  └──────────────────────┬───────────────────────┘
--                         │
--              ┌──────────▼──────────┐
--              │  fact_missing_items  │
--              │  order_id ──► fact_orders   │
--              │  product_id ──► dim_products│
--              └─────────────────────┘
-- =============================================================================

USE WalmartDW;
GO

-- =============================================================================
-- STAGING SCHEMA — raw CSV data, no transformations, VARCHAR for everything
-- =============================================================================

CREATE SCHEMA stg;
GO

CREATE TABLE stg.orders (
    date            VARCHAR(10),
    order_id        VARCHAR(40),
    order_amount    VARCHAR(20),
    region          VARCHAR(50),
    items_delivered SMALLINT,
    items_missing   SMALLINT,
    delivery_hour   VARCHAR(10),
    driver_id       VARCHAR(15),
    customer_id     VARCHAR(15)
);

CREATE TABLE stg.drivers (
    driver_id   VARCHAR(15),
    driver_name VARCHAR(100),
    age         TINYINT,
    Trips       INT
);

CREATE TABLE stg.customers (
    customer_id   VARCHAR(15),
    customer_name VARCHAR(100),
    customer_age  TINYINT
);

CREATE TABLE stg.products (
    produc_id    VARCHAR(25),   -- original typo preserved in staging
    product_name VARCHAR(100),
    category     VARCHAR(50),
    price        VARCHAR(15)
);

CREATE TABLE stg.missing_items (
    order_id     VARCHAR(40),
    product_id_1 VARCHAR(25),
    product_id_2 VARCHAR(25),
    product_id_3 VARCHAR(25)
);
GO

-- =============================================================================
-- DATA WAREHOUSE SCHEMA — cleaned, typed, star schema
-- =============================================================================

CREATE SCHEMA dw;
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSIONS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE dw.dim_date (
    date_key        INT           NOT NULL PRIMARY KEY,  -- YYYYMMDD integer key
    full_date       DATE          NOT NULL,
    year            SMALLINT      NOT NULL,
    quarter         TINYINT       NOT NULL,
    quarter_label   VARCHAR(7)    NOT NULL,              -- "Q1 2023"
    month_num       TINYINT       NOT NULL,
    month_name      VARCHAR(10)   NOT NULL,
    month_label     VARCHAR(8)    NOT NULL,              -- "Jan 2023"
    week_of_year    TINYINT       NOT NULL,
    day_of_month    TINYINT       NOT NULL,
    day_of_week     TINYINT       NOT NULL,              -- 1=Sunday … 7=Saturday
    day_name        VARCHAR(10)   NOT NULL,
    is_weekend      BIT           NOT NULL DEFAULT 0
);

CREATE TABLE dw.dim_region (
    region_id   INT           NOT NULL PRIMARY KEY IDENTITY(1,1),
    region_name VARCHAR(50)   NOT NULL UNIQUE
);

CREATE TABLE dw.dim_drivers (
    driver_id   VARCHAR(15)   NOT NULL PRIMARY KEY,
    driver_name VARCHAR(100)  NOT NULL,
    age         TINYINT       NOT NULL
    -- Trips removed: computed from fact_orders as COUNT(order_id) per driver
);

CREATE TABLE dw.dim_customers (
    customer_id   VARCHAR(15)  NOT NULL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_age  TINYINT      NOT NULL,
    age_group     VARCHAR(10)  NOT NULL   -- "18-29", "30-44", "45-59", "60+"
);

CREATE TABLE dw.dim_products (
    product_id   VARCHAR(25)   NOT NULL PRIMARY KEY,   -- renamed from produc_id
    product_name VARCHAR(100)  NOT NULL,
    category     VARCHAR(50)   NOT NULL,
    unit_price   DECIMAL(8,2)  NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- FACTS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE dw.fact_orders (
    order_id        VARCHAR(40)   NOT NULL PRIMARY KEY,
    date_key        INT           NOT NULL,
    region_id       INT           NOT NULL,
    driver_id       VARCHAR(15)   NOT NULL,
    customer_id     VARCHAR(15)   NOT NULL,
    order_amount    DECIMAL(10,2) NOT NULL,
    items_delivered SMALLINT      NOT NULL,
    items_missing   SMALLINT      NOT NULL,
    delivery_hour   TINYINT       NOT NULL,   -- integer 0–23
    has_missing     BIT           NOT NULL,
    CONSTRAINT fk_fact_orders_date     FOREIGN KEY (date_key)    REFERENCES dw.dim_date(date_key),
    CONSTRAINT fk_fact_orders_region   FOREIGN KEY (region_id)   REFERENCES dw.dim_region(region_id),
    CONSTRAINT fk_fact_orders_driver   FOREIGN KEY (driver_id)   REFERENCES dw.dim_drivers(driver_id),
    CONSTRAINT fk_fact_orders_customer FOREIGN KEY (customer_id) REFERENCES dw.dim_customers(customer_id)
);

CREATE TABLE dw.fact_missing_items (
    id            INT           NOT NULL PRIMARY KEY IDENTITY(1,1),
    order_id      VARCHAR(40)   NOT NULL,
    product_id    VARCHAR(25)   NOT NULL,
    item_position TINYINT       NOT NULL,   -- 1, 2, or 3 (original column position)
    CONSTRAINT fk_missing_order   FOREIGN KEY (order_id)   REFERENCES dw.fact_orders(order_id),
    CONSTRAINT fk_missing_product FOREIGN KEY (product_id) REFERENCES dw.dim_products(product_id)
);
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES — covering the most common Power BI query patterns
-- ─────────────────────────────────────────────────────────────────────────────

-- fact_orders: filter/group by date, region, driver
CREATE NONCLUSTERED INDEX ix_fact_orders_date     ON dw.fact_orders (date_key);
CREATE NONCLUSTERED INDEX ix_fact_orders_region   ON dw.fact_orders (region_id);
CREATE NONCLUSTERED INDEX ix_fact_orders_driver   ON dw.fact_orders (driver_id);
CREATE NONCLUSTERED INDEX ix_fact_orders_customer ON dw.fact_orders (customer_id);

-- fact_missing_items: join to orders and products
CREATE NONCLUSTERED INDEX ix_missing_order   ON dw.fact_missing_items (order_id);
CREATE NONCLUSTERED INDEX ix_missing_product ON dw.fact_missing_items (product_id);

-- dim_date: range scans by month/year
CREATE NONCLUSTERED INDEX ix_dim_date_month ON dw.dim_date (year, month_num);
GO
