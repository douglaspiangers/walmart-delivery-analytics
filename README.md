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

| Finding | Detail |
|---|---|
| Overall missing item rate | **15.0%** of all orders had at least one missing item |
| Worst performing region | **Altamonte Springs — 16.2%** (vs. 13.9% best region: Sanford) |
| Peak failure window | **Monday deliveries — 16.1%** failure rate |
| Driver variance | Worst driver: **36.4%** failure rate vs. best: **0.0%** |
| Primary causal factor | **Driver historical performance** is the strongest predictor of future failures |
| Estimated financial impact | **~$37,500/year** in redelivery costs attributable to high-risk drivers alone |

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
│   └── processed/              # Cleaned Parquet files + results_summary.json
├── notebooks/
│   ├── 01_data_profiling.ipynb        # Data structure, nulls, duplicates
│   ├── 02_data_cleaning.ipynb         # Type fixes, column normalization, master join
│   ├── 03_exploratory_analysis.ipynb  # Visual EDA — 6 analyses
│   ├── 04_business_insights.ipynb     # Executive KPIs, region table, top products
│   ├── 05_delivery_quality_analysis.ipynb  # Failure patterns by region/day/driver
│   ├── 06_statistical_analysis.ipynb  # Chi-square, Kruskal-Wallis, Mann-Whitney, CIs
│   ├── 07_causal_analysis.ipynb       # Logistic regression, Random Forest, SHAP
│   └── 08_segmentation.ipynb          # K-Means driver & customer segmentation
├── src/
│   ├── data_loader.py          # Raw data loading functions
│   ├── preprocessing.py        # Cleaning, transformation, master join logic
│   └── visualization.py        # Reusable matplotlib chart functions
├── dashboard/
│   └── dashboard.py            # Interactive Plotly Dash app (4 views)
├── reports/
│   └── figures/                # Exported PNG charts (01–24)
├── run_analysis.py             # Full pipeline script — generates all figures
└── requirements.txt
```

---

## Datasets

| File | Rows | Description |
|---|---|---|
| `orders.csv` | 10,000 | Delivery orders — region, amount, hour, driver, customer, items |
| `customers.csv` | 1,239 | Customer profiles with age |
| `drivers.csv` | 1,247 | Driver profiles with trip count |
| `products.csv` | 314 | Product catalog with category and price |
| `order_items.csv` | 1,662 | Order-to-product link table |

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

### 06 — Statistical Analysis
Rigorous statistical validation of EDA patterns:
- **Chi-square** test: failure rate across regions (are differences real or chance?)
- **Chi-square** test: failure rate across weekdays
- **Kruskal-Wallis** test: order value distribution across regions
- **Mann-Whitney U**: high-risk vs. low-risk driver performance
- **Wilson confidence intervals** (95%) for failure rates by region
- **Effect sizes**: Cramér's V and Cohen's d

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

| KPI | What it measures | Business question answered |
|---|---|---|
| **Failure Rate by Experience Tier** | Failure rate by trips bucket (Novice / Intermediate / Expert) | Does experience reduce failures? |
| **H1 vs H2 Improvement Rate** | % of drivers who improved from Jan–Jun to Jul–Dec | Is the operation evolving or stagnating? |
| **Driver Consistency Index** | Coefficient of variation of monthly failure rate per driver | Are problem drivers chronically bad, or just inconsistent? |
| **Financial Cost by Experience Tier** | Estimated redelivery cost per experience segment | Where does training investment generate most ROI? |
| **Recovery Rate** | % of high-risk H1 drivers who improved by H2 | Do problem drivers self-correct without intervention? |

**Key findings:** Intermediate drivers show the highest failure rate (experience is NOT a linear protector). Only ~50% of drivers improved H1→H2 without intervention. Chronic high-risk drivers are the primary target for disciplinary action.

### 10 — Customer Retention Analysis
Quantifies the downstream impact of delivery failures on customer behavior — distinguishing operational cost (redelivery) from strategic cost (churn):

| KPI | What it measures | Business question answered |
|---|---|---|
| **Customer Failure Profile** | Distribution of customers by number of failures experienced | What % of the base was directly impacted? |
| **Return Rate After Failure** | % of customers who placed a new order after their first failure | Does a failure drive customers away? |
| **Order Frequency Comparison** | Orders/month for customers with vs. without failures | Does failure reduce purchase cadence? |
| **Revenue at Risk** | Revenue from customers who churned after a failure | How much money is actually at stake? |
| **Post-Failure Spend Change** | Average ticket before vs. after first failure (returning customers) | Do returning customers spend less? |
| **Churn Rate by Failure Count** | % of customers lost, segmented by number of failures experienced | How much does each additional failure raise churn risk? |

**Key findings:** 71% of customers experienced at least one failure. 92.2% return after a failure — but the 7.8% who don't represent **$47,371 in at-risk revenue**. Churn risk compounds with each additional failure. Intervention must happen at the 1st failure, not the 3rd.

---

## Interactive Dashboard

A 4-tab Plotly Dash application giving operational and executive visibility:

| Tab | Content |
|---|---|
| Executive View | KPI cards, monthly trends, revenue by region, failure rate over time |
| Operational Analysis | Delivery heatmaps (volume + failure rate), failure by day and period |
| Driver Performance | Distribution, top 15 worst/best drivers, volume vs. failure scatter |
| Region Drill-down | Per-region KPIs, weekday pattern, top risky drivers, heatmap |
| **Score de Risco** | Interactive order risk scoring — select region, day, driver, amount, items → real-time failure probability with gauge and feature contribution breakdown |
| **Cohort de Motoristas** | 4 KPI charts: failure rate by experience tier, H1 vs H2 scatter, consistency index quadrants, financial cost by tier |
| **Retenção de Clientes** | 4 KPI charts: customer failure profile, return rate, order frequency comparison, churn rate by failure count |

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

# 4. Option B — Run notebooks in order (01 to 08)
jupyter notebook notebooks/

# 5. Option C — Launch interactive dashboard
python dashboard/dashboard.py
```

> **Note:** Run `run_analysis.py` (or notebooks 01–02) before launching the dashboard, as it generates the processed Parquet files.

---

## Tools & Libraries

| Purpose | Library |
|---|---|
| Data manipulation | pandas, numpy |
| Visualization (static) | matplotlib, seaborn |
| Visualization (interactive) | plotly, dash |
| Statistical testing | scipy |
| Machine learning | scikit-learn |
| Model explainability | shap |
| Data storage | parquet (via pandas) |
| Notebook environment | Jupyter |

---

## Statistical Results Summary

| Test | Target | Result | p-value | Effect Size |
|---|---|---|---|---|
| Chi-square | Region → Failure rate | See notebook 06 | See nb06 | Cramér's V |
| Chi-square | Weekday → Failure rate | See notebook 06 | See nb06 | Cramér's V |
| Kruskal-Wallis | Order value across regions | See notebook 06 | See nb06 | — |
| Mann-Whitney U | High vs. low risk drivers | Significant | See nb06 | Cohen's d |
| Random Forest AUC | Failure prediction | See notebook 07 | — | — |

> Run the notebooks to compute exact values. The `data/processed/results_summary.json` file contains the key business metrics from the pipeline run.

---

## Project Evolution (Commits)

| Commit | Description |
|---|---|
| `chore: project setup` | gitignore, requirements, README scaffold |
| `data: add raw CSV files` | 5 raw datasets with consistent naming |
| `feat: add src modules` | data_loader, preprocessing, visualization |
| `feat: add analysis notebooks 01-05` | EDA, cleaning, quality analysis |
| `feat: add run_analysis.py` | Full pipeline script, 12 figures, results JSON |
| `feat: statistical analysis notebook 06` | Hypothesis tests, confidence intervals, effect sizes |
| `feat: causal analysis notebook 07` | Logistic regression, Random Forest, SHAP |
| `feat: segmentation notebook 08` | Driver/customer K-Means clustering |
| `feat: interactive dashboard` | Plotly Dash, 4 views, region drill-down |
| `feat: driver cohort analysis (nb09)` | Experience tiers, H1/H2 trajectory, consistency index, financial cost, recovery rate |
| `feat: customer retention analysis (nb10)` | Failure profile, return rate, frequency, revenue at risk, churn by failure count |
| `feat: dashboard v2 — 7 tabs` | Risk scoring simulator, driver cohort view, customer retention view |
| `docs: final README` | Complete storytelling and business recommendations |

---

## Author

**Douglas Piangers**
Data Scientist
[GitHub](https://github.com/douglaspiangers) · [LinkedIn](https://linkedin.com/in/douglaspiangers)
