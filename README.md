# Walmart Delivery Analytics

End-to-end data analysis project simulating a real business scenario: identifying operational failures in a grocery delivery service using Python, pandas, and data visualization.

---

## Business Context

A delivery operation running across multiple regions needs to understand why orders are arriving with missing items. This project analyzes ~10,000 orders to uncover patterns in delivery failures and translate them into actionable business recommendations.

---

## Project Structure

```
walmart-delivery-analytics/
├── data/
│   ├── raw/               # Original CSV files
│   └── processed/         # Cleaned data (generated locally, not versioned)
├── notebooks/
│   ├── 01_data_profiling.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_business_insights.ipynb
│   └── 05_delivery_quality_analysis.ipynb
├── src/
│   ├── data_loader.py     # Data loading functions
│   ├── preprocessing.py   # Cleaning and transformation logic
│   └── visualization.py   # Reusable chart functions
├── reports/
│   └── figures/           # Exported charts
├── requirements.txt
└── .gitignore
```

---

## Datasets

| File | Rows | Description |
|---|---|---|
| `orders.csv` | 9,999 | Delivery orders with region, amount, hour, driver and customer |
| `customers.csv` | 1,238 | Customer profiles with age |
| `drivers.csv` | 1,246 | Driver profiles with trip count |
| `products.csv` | 313 | Product catalog with category and price |
| `order_items.csv` | 1,662 | Link table between orders and products |

---

## Notebooks Overview

### 01 — Data Profiling
Loads all raw tables and documents structure, data types, null values, and duplicates. Produces a table of issues to be fixed.

### 02 — Data Cleaning
Fixes all identified issues: monetary values stored as strings (`$1,095.54` → float), delivery hour as time string → integer, column typos, and date parsing. Builds a master dataframe by joining orders with customers and drivers. Exports cleaned data to Parquet.

### 03 — Exploratory Analysis
- Monthly trend of orders and revenue
- Revenue by region
- Order amount distribution
- Delivery heatmap (hour × day of week)
- Customer age distribution
- Product category breakdown

### 04 — Business Insights
- Executive KPI summary
- Region-level performance table (revenue, volume, missing rate)
- Top 10 most ordered products
- Average ticket by customer age group

### 05 — Delivery Quality Analysis
- Missing item rate by region vs. overall average
- Missing item rate by day of week
- Statistical correlation between order size and missing items
- Driver performance ranking (minimum 20 deliveries threshold)
- Heatmap of failure rate by region and hour

---

## Key Findings

| Finding | Detail |
|---|---|
| Overall missing item rate | ~X% of all orders had at least one missing item |
| Worst performing region | Region X — X% above average |
| Peak failure window | Hour X on [day] shows the highest failure concentration |
| Driver variance | Top 10 worst drivers show 2x the missing rate of top 10 best |
| Order size effect | Larger orders correlate with higher probability of missing items |

> Run the notebooks in order to generate the actual numbers and figures.

---

## How to Run

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/walmart-delivery-analytics.git
cd walmart-delivery-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run notebooks in order
jupyter notebook notebooks/
```

> **Note:** Run notebooks 01 through 05 in sequence. Notebook 02 generates the processed data files that the subsequent notebooks depend on.

---

## Tools & Libraries

| Purpose | Library |
|---|---|
| Data manipulation | pandas, numpy |
| Visualization | matplotlib, seaborn |
| Statistical tests | scipy |
| Data storage | parquet (via pandas) |
| Notebook environment | Jupyter |

---

## Author

**[Your Name]**  
Data Scientist  
[LinkedIn](https://linkedin.com/in/your-profile) · [GitHub](https://github.com/your-username)
