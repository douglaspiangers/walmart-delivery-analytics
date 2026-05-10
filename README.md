# Walmart Delivery Analytics

> **End-to-end data science project** — Identifying operational failures in a grocery delivery service using statistical analysis, causal modeling, customer/driver segmentation, and an interactive business dashboard.

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-3.0-green?logo=pandas)](https://pandas.pydata.org)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.x-orange?logo=scikit-learn)](https://scikit-learn.org)
[![Plotly Dash](https://img.shields.io/badge/Plotly%20Dash-interactive-purple)](https://dash.plotly.com)

---

## Business Problem

A grocery delivery operation serving **7 cities in the Orlando, FL area** processed **10,000 orders in 2023**, generating **$2.83M in revenue**. However, **15% of all deliveries arrived with at least one missing item** — creating customer dissatisfaction, redelivery costs, and revenue at risk.

**Core question:** *Which operational factors are driving missing items, and where should the business intervene first?*

---

## Key Findings

| Metric | Value |
|---|---|
| Total orders analyzed | 10,000 (Jan–Dec 2023) |
| Total revenue | $2,833,022 |
| Overall failure rate | 15.0% (1 in 7 deliveries) |
| Driver SHAP contribution | 66.8% of predictive power |
| Client SHAP contribution | 3.4% — not a causal factor |
| Driver vs. client explanatory ratio | 19× |
| Highest-risk region | Altamonte Springs (16.2%) |
| Best-performing region | Sanford (13.9%) |
| Peak failure day | Monday (16.1%) |
| Customers with at least one failure | 71% of the base (881 of 1,239) |
| Churn rate after failure | 7.8% (26 customers) |
| Revenue at risk from churn | $47,371 |
| Model AUC (Random Forest) | 0.80 |

---

## Business Recommendations

### 1. Driver Performance Program (Highest ROI)
- The top 25% highest-risk drivers account for a disproportionate share of failures
- **Action:** Mandatory retraining for drivers with >20% failure rate over 20+ deliveries
- **Expected impact:** Reducing high-risk driver failure rate by 30% saves ~$11,000/year

### 2. Monday Operational Reinforcement
- Monday consistently shows the highest failure rate (16.1%) — likely a post-weekend staffing/process issue
- **Action:** Additional QA checks for Monday dispatches; mandatory double-check protocol

### 3. Regional Audit — Altamonte Springs
- Altamonte Springs has the highest failure rate (16.2%) — statistically significant vs. the global average
- **Action:** On-site operational audit; compare process standards with Sanford (best-performing region)

### 4. High-Value Order Protocol
- Larger orders correlate with higher error probability
- **Action:** Digital checklist required for orders above $400 or with more than 12 items

---

## Project Architecture

```
walmart-delivery-analytics/
├── data/
│   ├── raw/                    # Original CSV files (5 tables)
│   ├── processed/              # Cleaned Parquet files + results_summary.json + shap_results.json
│   └── powerbi/                # Star-schema CSVs ready for Power BI import (13 files)
├── notebooks/
│   ├── 01_data_profiling.ipynb        # Data structure, nulls, duplicates
│   ├── 02_data_cleaning.ipynb         # Type fixes, column normalization, master join
│   ├── 03_exploratory_analysis.ipynb  # Visual EDA — 6 analyses
│   ├── 04_business_insights.ipynb     # Executive KPIs, region table, top products
│   ├── 05_delivery_quality_analysis.ipynb  # Failure patterns by region/day/driver
│   ├── 07_causal_analysis.ipynb       # Logistic regression, Random Forest, SHAP
│   ├── 08_segmentation.ipynb          # K-Means driver & customer segmentation
│   ├── 09_driver_cohort_analysis.ipynb     # H1 vs H2 longitudinal driver performance
│   ├── 10_customer_retention_analysis.ipynb # Churn analysis and at-risk revenue
│   └── 11_executive_conclusion.ipynb       # Final answer: drivers vs. clients (SHAP + statistics)
├── src/
│   ├── data_loader.py          # Raw data loading functions
│   ├── preprocessing.py        # Cleaning, transformation, master join logic
│   └── visualization.py        # Reusable matplotlib chart functions
├── dashboard/
│   └── dashboard.py            # Interactive Plotly Dash app (4 tabs)
├── reports/
│   └── figures/                # Exported PNG charts (12 pipeline + 3 executive conclusion)
├── run_analysis.py             # Full pipeline script — generates all figures
├── export_powerbi.py           # Generates star-schema CSVs for Power BI
├── generate_lovable_data.py    # Exports static JSON for the React dashboard
├── LOVABLE_PROMPT.md           # Full prompt to build the React dashboard in Lovable
├── POWERBI_GUIDE.md            # Step-by-step Power BI import and DAX guide
└── requirements.txt
```

---

## Datasets

| File | Rows | Description |
|---|---|---|
| `orders.csv` | 10,000 | Core transaction table — date, amount, region, delivery hour, driver and customer IDs, items delivered/missing |
| `customers.csv` | 1,239 | Customer registry — name and age |
| `drivers.csv` | 1,247 | Driver registry — name, age, total trip count |
| `order_items.csv` | 1,662 | Order-product junction — maps orders to individual products |
| `products.csv` | 314 | Product catalog — name, category, and unit price |

---

## Notebook Overview

### 01 — Data Profiling
Loads all raw tables. Documents schema, data types, null values, and duplicates. Produces an issues table to guide the cleaning phase.

### 02 — Data Cleaning
Fixes all identified issues: monetary values stored as strings (`$1,095.54` → float), delivery hour as time string → integer, column typos, date parsing. Builds a master dataframe joining orders + customers + drivers. Exports cleaned data to Parquet.

### 03 — Exploratory Data Analysis
- Monthly trend of orders and revenue
- Revenue by region
- Order amount distribution
- Delivery heatmap (hour × day of week)
- Customer age distribution
- Product category breakdown

### 04 — Business Insights
- Executive KPI summary (revenue, ticket, failure rate)
- Region-level performance table
- Top 10 most ordered products
- Average ticket by customer age group

### 05 — Delivery Quality Analysis
- Missing item rate by region vs. overall average
- Missing item rate by day of week
- Statistical correlation: order size vs. missing items
- Driver performance ranking (minimum delivery threshold)
- Failure rate heatmap by region and hour

### 07 — Causal Analysis
Identifies *why* orders fail using predictive models:
- **Feature engineering**: driver historical rate, time periods, weekend flags
- **Logistic Regression** + Odds Ratios — most interpretable causal estimates
- **Random Forest** + Feature Importance — non-linear patterns
- **ROC curves** comparing model performance
- **SHAP values** — individual-level prediction explainability

### 08 — Segmentation
Clusters drivers and customers for targeted interventions:
- **Driver segmentation** (K-Means, k=3): High Risk / Medium Risk / Low Risk
- **Customer segmentation** (K-Means, k=4): VIP / Regular High / Regular Low / Occasional
- **Financial impact matrix** by driver segment with estimated cost per segment
- PCA visualization of clusters

### 09 — Driver Cohort Analysis
Longitudinal analysis of driver performance over time — answers whether experience protects against failures and whether high-risk drivers self-correct:

| Question | Finding |
|---|---|
| Does experience reduce failure rates? | No — intermediate drivers (26–50 trips) show the highest failure rate (15.9%), above both novices and veterans |
| Do high-risk drivers self-correct without intervention? | Only 49.7% improved from H1 to H2 spontaneously — autocorrection alone is insufficient |
| Who should be targeted first? | Chronic high-risk drivers (consistent >Q75 failure rate across both semesters) |

**Key findings:** Intermediate drivers show the highest failure rate (experience is NOT a linear protector). Only ~50% of drivers improved H1→H2 without intervention. Chronic high-risk drivers are the primary target for disciplinary action.

### 10 — Customer Retention Analysis
Quantifies the downstream impact of delivery failures on customer behavior — distinguishing operational cost (redelivery) from strategic cost (churn):

| Metric | Value |
|---|---|
| Customers with at least one failure | 881 (71.1% of base) |
| Return rate after first failure | 92.2% |
| Churned customers (90-day window) | 26 |
| Revenue at risk from churned customers | $47,371 |

**Key findings:** 71% of customers experienced at least one failure. 92.2% return after a failure — but the 7.8% who don't represent **$47,371 in at-risk revenue**. Churn risk compounds with each additional failure. Intervention must happen at the 1st failure, not the 3rd.

---

## Interactive Dashboard

A 4-tab Plotly Dash application giving operational and executive visibility:

| Tab | Content |
|---|---|
| Executive Overview | Global KPIs, monthly revenue and order trend, regional revenue breakdown |
| Delivery Quality | Failure rate by region, day of week, and delivery hour heatmap |
| Driver Performance | Top 10 worst/best drivers, failure rate distribution, H1 vs H2 trajectory scatter |
| Customer Impact | Churn analysis by failure count, retention rates, at-risk revenue by customer segment |

**Run the dashboard:**
```bash
python dashboard/dashboard.py
# Open http://localhost:8050
```

---

## How to Run

```bash
# 1. Clone the repository
git clone https://github.com/douglaspiangers/walmart-delivery-analytics.git
cd walmart-delivery-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Option A — Run full pipeline (generates all charts + processed data)
python -X utf8 run_analysis.py

# 4. Option B — Run notebooks in order (01 to 11)
jupyter notebook notebooks/

# 5. Option C — Launch interactive dashboard
python dashboard/dashboard.py
```

> **Note:** Run `run_analysis.py` (or notebooks 01–02) before launching the dashboard, as it generates the processed Parquet files.

---

## Tools & Libraries

| Tool / Library | Purpose |
|---|---|
| Python 3.14 | Core language |
| Pandas 3.0 | Data manipulation and aggregation |
| NumPy | Numerical operations |
| Scikit-Learn 1.x | Logistic Regression and Random Forest classification |
| SHAP | Model explainability — feature contribution per prediction |
| SciPy | Statistical tests — Kruskal-Wallis, Mann-Whitney U, Point-biserial |
| Plotly Dash | Interactive multi-tab web dashboard |
| Matplotlib / Seaborn | Static chart generation for reports |
| Jupyter Notebook | Exploratory analysis and narrative documentation |

---

## Project Evolution (Commits)

| Commit | Description |
|---|---|
| `82291a7` | Project setup — `.gitignore`, `requirements.txt`, README skeleton |
| `74826ed` | Raw data — 5 CSV files with normalized naming convention |
| `4b736dc` | Source modules — `data_loader.py`, `preprocessing.py`, `visualization.py` |
| `70e2f4f` | Analysis notebooks 01–05 — profiling, cleaning, EDA, business insights, delivery quality |
| `d6d5106` | Pipeline script — `run_analysis.py` generating all 12 report figures |
| `3b7cc1a` | Project v2 — causal analysis (SHAP), segmentation, driver cohort, customer retention, Power BI export |
| `(pending)` | Executive conclusion notebook (11), Lovable React dashboard prompt, README completion |

---

## Author

**Douglas Piangers**
Data Scientist
[GitHub](https://github.com/douglaspiangers) · [LinkedIn](https://linkedin.com/in/douglaspiangers)
