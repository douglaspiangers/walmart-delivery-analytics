# SQL — Star Schema for Power BI

This folder contains the SQL Server scripts that transform the five raw source
files into a star schema ready for Power BI.

---

## Why a star schema

The raw files had two structural problems that make Power BI inefficient:
the missing items table stored products as columns instead of rows (pivoted),
and there was no date dimension, which blocks all time intelligence functions
(month-over-month, year-to-date, period comparisons).

The star schema fixes both and adds clean FK relationships between every
dimension and the two fact tables.

---

## Final model

```
              dim_date
                 │
 dim_region ─ fact_orders ─ dim_drivers
                 │               dim_customers
         fact_missing_items
                 │
            dim_products
```

| Table | Type | Rows (approx.) | Key change from raw |
|---|---|---|---|
| `dim_date` | Dimension | 365 | Generated — did not exist in source |
| `dim_region` | Dimension | 7 | Extracted from orders; adds surrogate key |
| `dim_drivers` | Dimension | 1,246 | `Trips` column dropped — computed from facts |
| `dim_customers` | Dimension | 1,238 | `age_group` derived column added |
| `dim_products` | Dimension | 313 | `produc_id` typo fixed; `price` cleaned to DECIMAL |
| `fact_orders` | Fact | 9,999 | `order_amount` and `delivery_hour` cleaned; `has_missing` flag added |
| `fact_missing_items` | Fact (bridge) | ~2,400 | UNPIVOTed from 3 columns into rows |

---

## Scripts

| Script | What it does |
|---|---|
| `01_raw_data_profile.sql` | Documents raw table structures, data quality checks, and transformation decisions |
| `02_star_schema_ddl.sql` | Creates `stg.*` staging tables and `dw.*` star schema tables with FKs and indexes |
| `03_load_dimensions.sql` | Loads all five dimension tables from staging with cleaning applied |
| `04_load_facts.sql` | Loads `fact_orders` and `fact_missing_items` (UNPIVOT), then runs validation queries |

---

## How to use

1. Create the `WalmartDW` database in SQL Server
2. Run `02_star_schema_ddl.sql` to create all tables
3. Load the five CSV files into the `stg.*` tables (SSMS Import Wizard or BULK INSERT)
4. Run `03_load_dimensions.sql`
5. Run `04_load_facts.sql`
6. Connect Power BI to the `dw.*` tables — do not connect to `stg.*`
