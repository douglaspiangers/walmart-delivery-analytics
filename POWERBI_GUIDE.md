# Power BI Dashboard Guide — Walmart Delivery Analytics

## Files generated in `data/powerbi/`

| File | Type | Usage in Power BI |
|---|---|---|
| `fct_orders.csv` | Fact | Central table — connects everything |
| `dim_date.csv` | Dimension | Time axis, period filters |
| `dim_drivers.csv` | Dimension | Segment, tier, quadrant |
| `dim_customers.csv` | Dimension | Segment, churn, value |
| `dim_regions.csv` | Dimension | Regional KPIs |
| `dim_products.csv` | Dimension | Product ranking |
| `agg_monthly_kpis.csv` | Aggregate | Trend chart |
| `agg_hour_day_heatmap.csv` | Aggregate | Hour × day heatmap |
| `agg_region_day.csv` | Aggregate | Failure by region × day |
| `agg_driver_monthly.csv` | Aggregate | Monthly consistency index |
| `agg_financial_impact.csv` | Aggregate | Cost by quadrant |
| `agg_top_products.csv` | Aggregate | Product ranking |
| `agg_retention_summary.csv` | Aggregate | Retention metrics |

---

## Step 1 — Import the data

1. Open Power BI Desktop
2. **Get Data → Text/CSV**
3. Import ALL files from the `data/powerbi/` folder
4. For each table: verify that column types are correct
   - Date columns → **Date** type
   - Rate columns (failure_rate, etc.) → **Decimal Number** type
   - ID columns → **Text** type

---

## Step 2 — Build the Model (Star Schema)

Go to **Model View** and create the relationships:

```
fct_orders[date_key]       → dim_date[date_key]         (Many:1)
fct_orders[driver_id]      → dim_drivers[driver_id]     (Many:1)
fct_orders[customer_id]    → dim_customers[customer_id] (Many:1)
fct_orders[region]         → dim_regions[region]        (Many:1)
fct_orders[order_id]       → agg_driver_monthly         (via driver_id + month — do not create a direct relationship)
```

> The `agg_*` tables are used **directly** in specific visuals,
> without a relationship to fct_orders — they already contain pre-calculated data.

---

## Step 3 — Create DAX Measures (paste into Power BI)

```dax
-- Global KPIs
Total Orders = COUNTROWS(fct_orders)

Total Revenue = SUM(fct_orders[order_amount])

Avg Ticket = AVERAGE(fct_orders[order_amount])

Failure Rate =
DIVIDE(
    COUNTROWS(FILTER(fct_orders, fct_orders[has_missing] = TRUE())),
    COUNTROWS(fct_orders),
    0
)

Total Failure Cost = SUM(fct_orders[failure_cost])

-- Comparisons
Failure Rate vs Global =
VAR CurrentRate = [Failure Rate]
VAR GlobalRate  = 0.15
RETURN CurrentRate - GlobalRate

-- Drivers
High Risk Drivers =
CALCULATE(
    DISTINCTCOUNT(dim_drivers[driver_id]),
    dim_drivers[intervention_quadrant] = "Chronic — Disciplinary Action"
)

Coaching Needed =
CALCULATE(
    DISTINCTCOUNT(dim_drivers[driver_id]),
    dim_drivers[intervention_quadrant] = "Unstable — Coaching"
)

-- Customers
Customers with Failure =
CALCULATE(
    COUNTROWS(dim_customers),
    dim_customers[had_failure] = TRUE()
)

Churned Customers =
CALCULATE(
    COUNTROWS(dim_customers),
    dim_customers[churned] = TRUE()
)

Revenue at Risk =
CALCULATE(
    SUM(dim_customers[total_revenue]),
    dim_customers[churned] = TRUE()
)

-- Projected savings (for Action Plan)
Projected Savings 30pct =
[Total Failure Cost] * 0.30
```

---

## Step 4 — Page Structure

### PAGE 1 — Executive Overview
**Objective:** Give the executive the overall state of the operation in 30 seconds.

| Visual | Type | Data | Configuration |
|---|---|---|---|
| Total Orders | Card | Measure: `Total Orders` | Bold, package icon |
| Total Revenue | Card | Measure: `Total Revenue` | Format: $#,##0 |
| Average Ticket | Card | Measure: `Avg Ticket` | Format: $#,##0.00 |
| Failure Rate | KPI Card | Measure: `Failure Rate` | Target: 10% / Alert: >15% |
| Total Failure Cost | Card | Measure: `Total Failure Cost` | Red color |
| Customers at Risk | Card | Measure: `Churned Customers` | |
| Revenue at Risk | Card | Measure: `Revenue at Risk` | |
| Monthly Trend | Line chart | `agg_monthly_kpis` — month × total_orders + total_revenue | Dual axis |
| Monthly Failure Rate | Line chart | `agg_monthly_kpis` — month × failure_rate | Reference line at 15% |
| Revenue by Region | Bar chart | `dim_regions` — region × total_revenue | Sort descending |

**Page filters:** Slicer by Month / Semester / Day of Week

---

### PAGE 2 — Delivery Quality
**Objective:** Show WHERE and WHEN failures occur — operational dashboard.

| Visual | Type | Data | Configuration |
|---|---|---|---|
| Failure Rate by Region | Bar chart | `dim_regions` — region × failure_rate | Global reference line at 15% / Green=OK, Red=Bad |
| Comparison vs Average | Clustered column chart | `dim_regions` — region × vs_global_avg_pp | Positive = red, negative = green |
| Hour × Day Heatmap | Matrix | `agg_hour_day_heatmap` — day_of_week × delivery_hour, value: failure_rate | Conditional color formatting (white→red) |
| Volume by Hour and Day | Matrix | `agg_hour_day_heatmap` — value: volume | Blue scale |
| Failure by Day of Week | Column chart | `agg_region_day` grouped — day_of_week × avg failure_rate | Monday highlighted |
| Failure by Period | Donut chart | `fct_orders` — period × has_missing_int | Overnight/Morning/Afternoon/Evening |

**Page filters:** Region / Month / Semester

---

### PAGE 3 — Driver Performance
**Objective:** Identify who needs action — ranking and segmentation.

| Visual | Type | Data | Configuration |
|---|---|---|---|
| High Risk Drivers | Card | Measure: `High Risk Drivers` | Red alert |
| Drivers for Coaching | Card | Measure: `Coaching Needed` | Orange alert |
| Cost by Quadrant | Bar chart | `agg_financial_impact` — quadrant × total_failure_cost | Include savings_if_30pct_reduction as a line |
| Distribution by Quadrant | Donut chart | `dim_drivers` — intervention_quadrant × count | 4 colors: red / orange / green / blue |
| Top 15 Critical Drivers | Table | `dim_drivers` — filter chronic+unstable — columns: driver_name, exp_tier, hist_failure_rate, estimated_failure_cost, intervention_quadrant | Conditional formatting on rate |
| Failure Rate Distribution | Histogram | `dim_drivers` — hist_failure_rate | Vertical line at 15% (global average) |
| H1 vs H2 Performance | Scatter plot | `dim_drivers` — rate_h1 × rate_h2, legend: improved_h1_h2 | Diagonal line (x=y) as reference |
| Drivers Who Improved | Card | Count dim_drivers where improved_h1_h2 = TRUE | % of total |

**Page filters:** Experience Tier / Quadrant / Region

---

### PAGE 4 — Customer Impact
**Objective:** Translate operational failures into revenue loss and relationship damage.

| Visual | Type | Data | Configuration |
|---|---|---|---|
| Impacted Customers | Card | Measure: `Customers with Failure` | With % of total |
| Return Rate | Card | `agg_retention_summary` — Return Rate (%) | Benchmark: >90% = OK |
| Churned Customers | Card | Measure: `Churned Customers` | Red alert |
| Revenue at Risk | Card | Measure: `Revenue at Risk` | Format $#,##0 |
| Failure Profile | Donut chart | `dim_customers` — failure_group × count | 4 colors per group |
| Value Segment × Failure | Matrix | `dim_customers` — value_segment × failure_group, value: count | Conditional formatting |
| Churn by Failure Group | Column chart | `dim_customers` grouped — failure_group × avg(churned) | White→red gradient color |
| Purchase Frequency | Clustered column chart | `dim_customers` — had_failure × avg(orders_per_month) | Side by side: with failure vs without failure |
| Lost Customers (Table) | Table | `dim_customers` filtered: churned = TRUE — customer_name, failure_group, total_revenue, value_segment | Sort by total_revenue desc |

**Page filters:** Value Segment / Failure Group / Age

---

### PAGE 5 — Action Plan
**Objective:** Translate the entire analysis into recommendations with estimated ROI.

| Visual | Type | Data | Configuration |
|---|---|---|---|
| Current Total Cost | Large card | Measure: `Total Failure Cost` | Context: "per year" |
| Estimated Savings (30%) | Large card | Measure: `Projected Savings 30pct` | Green — "if target is met" |
| Priority by Impact | Horizontal bar chart | `agg_financial_impact` — quadrant × total_failure_cost + savings | Show delta |
| Recommendations Table | Manual table (Enter Data) | 4 prioritized actions with estimated impact | See below |
| Revenue at Risk vs Retention Cost | Scatter plot or comparative cards | Show that $47,371 is at risk vs. compensation cost | Visual narrative |

**Recommendations Table (enter manually via Enter Data):**

| Priority | Action | Target | Estimated Impact |
|---|---|---|---|
| 1 | Mandatory retraining program | Chronic + Unstable Drivers | -30% in failure cost |
| 2 | Reinforced protocol on Mondays | All drivers | -2pp in failure rate |
| 3 | Operational audit — Altamonte Springs | Regional management | -1.5pp in the region |
| 4 | Immediate compensation after 1st failure | Customers with 1 failure | Recover $47k at risk |

---

## Professional Design Tips

### Recommended color palette
```
Primary (blue):    #1F77B4
Success (green):   #2CA02C
Alert (orange):    #FF7F0E
Danger (red):      #D62728
Neutral (gray):    #7F7F7F
Page background:   #F8F9FA
Card background:   #FFFFFF
```

### General settings
- **Theme:** Use the default Power BI theme or import a JSON theme with the colors above
- **Font:** Segoe UI throughout the report
- **KPI Cards:** Use the "Card" visual with rounded corners and a subtle shadow
- **Reference lines:** Always add a red dashed line at the global average (15%) on rate charts
- **Conditional formatting:** Use a White→Red scale on every `failure_rate` or `failure_cost` column in tables
- **Tooltips:** Customize to show additional context (e.g., in the region chart, tooltip with number of orders and drivers)

### Information hierarchy per page
```
PAGE TITLE (large, bold)
  └── Subtitle with context ("Jan–Dec 2023 | 7 cities | 10,000 orders")
      └── KPI Cards (card row at the top)
          └── Main charts (2/3 of the page)
              └── Detail table (bottom 1/3, optional)
```

---

## Recommended creation order

1. Create the model and relationships
2. Create all DAX measures
3. Build Page 1 (Executive) — visual reference for all other pages
4. Build Page 5 (Action Plan) — narrative anchor
5. Build Pages 2, 3, 4

> Start from the end (Action Plan) to have clarity about what story
> each preceding page needs to tell.
