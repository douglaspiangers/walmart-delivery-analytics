# SQL — Star Schema for Power BI

This folder organizes the five raw source files into a star schema using SQL
Server views. The raw data stays untouched in staging tables — all cleaning
and structuring is expressed as views that Power BI connects to directly.

---

## Model

```
              vw_dim_date
                   │
vw_dim_region ─ vw_fact_orders ─ vw_dim_driver
                   │                  vw_dim_customer
         vw_fact_missing_items
                   │
             vw_dim_product
```

| View | Type | Source | Key change |
|---|---|---|---|
| `vw_dim_date` | Dimension | Generated | Did not exist — full 2023 calendar |
| `vw_dim_region` | Dimension | `stg.orders` | Extracted from loose text; adds numeric ID |
| `vw_dim_driver` | Dimension | `stg.drivers` | `Trips` removed; `age_group` added |
| `vw_dim_customer` | Dimension | `stg.customers` | `age_group` added |
| `vw_dim_product` | Dimension | `stg.products` | `produc_id` typo fixed; price cleaned |
| `vw_fact_orders` | Fact | `stg.orders` | `order_amount` cleaned; `delivery_hour` as integer; `has_missing` flag |
| `vw_fact_missing_items` | Fact | `stg.missing_items` | UNPIVOTed from 3 columns to rows |

---

## Scripts

| Script | What it does |
|---|---|
| `01_raw_data_profile.sql` | Audits raw data: structure, quality issues, transformation decisions |
| `02_staging_setup.sql` | Creates staging tables and documents how to load the CSVs |
| `03_views_dimensions.sql` | Creates the 5 dimension views |
| `04_views_facts.sql` | Creates the 2 fact views + validation and analytical queries |

---

## How to use

1. Run `02_staging_setup.sql` to create the staging tables
2. Load the five CSVs into `stg.*` via SSMS Import Wizard or BULK INSERT
3. Run `03_views_dimensions.sql`
4. Run `04_views_facts.sql`
5. In Power BI Desktop: **Get Data → SQL Server** → connect to the `vw_*` views
6. Set relationships in Power BI model view:
   - `vw_fact_orders[date_key]` → `vw_dim_date[date_key]`
   - `vw_fact_orders[region_id]` → `vw_dim_region[region_id]`
   - `vw_fact_orders[driver_id]` → `vw_dim_driver[driver_id]`
   - `vw_fact_orders[customer_id]` → `vw_dim_customer[customer_id]`
   - `vw_fact_missing_items[order_id]` → `vw_fact_orders[order_id]`
   - `vw_fact_missing_items[product_id]` → `vw_dim_product[product_id]`
