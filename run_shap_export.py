"""
run_shap_export.py
Runs the computational logic from Notebook 11 and saves shap_results.json.
Equivalent to NB11 without charts — for environments without Jupyter installed.
"""
import sys, os, warnings, json
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from scipy.stats import kruskal, mannwhitneyu

from src.data_loader import load_orders, load_customers, load_drivers
from src.preprocessing import clean_orders, clean_drivers, build_master

# ── Load data
print("Loading data...")
master = pd.read_parquet("data/processed/master.parquet")

# ── Feature engineering — driver_fail_rate without data leakage
# For each order, uses only PRIOR deliveries of the same driver (expanding window).
# Orders with no history receive the global rate as a prior.
master = master.sort_values("date").reset_index(drop=True)
global_rate = master["has_missing"].mean()
master["driver_fail_rate"] = (
    master.groupby("driver_id")["has_missing"]
    .transform(lambda x: x.shift(1).expanding().mean())
    .fillna(global_rate)
)

def hour_to_period(h):
    if h < 6:  return "overnight"
    if h < 12: return "morning"
    if h < 18: return "afternoon"
    return "evening"

master["period"]     = master["delivery_hour"].apply(hour_to_period)
master["is_weekend"] = master["day_of_week"].isin(["Saturday", "Sunday"]).astype(int)
master["is_monday"]  = (master["day_of_week"] == "Monday").astype(int)

le_region = LabelEncoder()
le_period = LabelEncoder()
master["region_enc"] = le_region.fit_transform(master["region"])
master["period_enc"] = le_period.fit_transform(master["period"])

FEATURES = [
    "driver_fail_rate",
    "order_amount", "items_delivered",
    "delivery_hour", "period_enc", "is_weekend", "is_monday",
    "region_enc",
    "customer_age",
]
FEATURE_CATEGORIES = {
    "driver_fail_rate": "Driver",
    "customer_age":     "Customer",
    "order_amount":     "Order",
    "items_delivered":  "Order",
    "delivery_hour":    "Time",
    "period_enc":       "Time",
    "is_weekend":       "Time",
    "is_monday":        "Time",
    "region_enc":       "Location",
}

df_model = master[FEATURES + ["has_missing"]].dropna()
X = df_model[FEATURES]
y = df_model["has_missing"].astype(int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# ── Train Random Forest
print(f"Training Random Forest ({len(X_train):,} training samples)...")
rf = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1])
print(f"AUC = {auc:.4f}")

# ── SHAP values
print("Computing SHAP values (sample of 800)...")
X_sample = X_test.sample(min(800, len(X_test)), random_state=42)
explainer   = shap.TreeExplainer(rf)
shap_values = explainer.shap_values(X_sample)

sv_raw = np.array(shap_values)
if sv_raw.ndim == 3:
    sv = sv_raw[:, :, 1]
elif isinstance(shap_values, list):
    sv = np.array(shap_values[1])
else:
    sv = sv_raw

mean_abs_shap = pd.DataFrame({
    "feature":       FEATURES,
    "mean_abs_shap": np.abs(sv).mean(axis=0).flatten(),
    "category":      [FEATURE_CATEGORIES[f] for f in FEATURES],
})

cat_shap = (
    mean_abs_shap.groupby("category")["mean_abs_shap"]
    .sum().reset_index()
    .sort_values("mean_abs_shap", ascending=False)
)
cat_shap["pct"] = cat_shap["mean_abs_shap"] / cat_shap["mean_abs_shap"].sum() * 100

print("\n=== SHAP by Category ===")
for _, row in cat_shap.iterrows():
    print(f"  {row['category']:<15} {row['pct']:5.1f}%")

# ── Variance
master["age_group"] = pd.cut(
    master["customer_age"], bins=[18, 30, 45, 60, 100],
    labels=["18-29", "30-44", "45-59", "60+"]
)
master["value_segment"] = pd.qcut(
    master.groupby("customer_id")["order_amount"].transform("mean"),
    q=4, labels=["Low Value", "Medium Value", "High Value", "VIP"]
)
driver_rates = (
    master.groupby("driver_id")
    .agg(deliveries=("order_id", "count"), rate=("has_missing", "mean"))
    .query("deliveries >= 10")["rate"]
)
age_rates    = master.groupby("age_group",    observed=True)["has_missing"].mean()
value_rates  = master.groupby("value_segment",observed=True)["has_missing"].mean()
region_rates = master.groupby("region")["has_missing"].mean()

variance_comparison = pd.DataFrame({
    "Dimension": ["Driver (individual)", "Region", "Age Group", "Value Segment"],
    "Maximum":   [driver_rates.max(), region_rates.max(), age_rates.max(), value_rates.max()],
    "Minimum":   [driver_rates.min(), region_rates.min(), age_rates.min(), value_rates.min()],
})
variance_comparison["Range (pp)"] = ((variance_comparison["Maximum"] - variance_comparison["Minimum"]) * 100).round(1)

# ── Statistical tests
age_groups_data = [
    master[master["age_group"] == g]["has_missing"].astype(int).values
    for g in master["age_group"].cat.categories
    if len(master[master["age_group"] == g]) > 0
]
stat_age, pval_age = kruskal(*age_groups_data)

val_groups_data = [
    master[master["value_segment"] == g]["has_missing"].astype(int).values
    for g in ["Low Value", "Medium Value", "High Value", "VIP"]
    if len(master[master["value_segment"] == g]) > 0
]
stat_val, pval_val = kruskal(*val_groups_data)

driver_perf   = (
    master.groupby("driver_id")
    .agg(deliveries=("order_id", "count"), fail_rate=("has_missing", "mean"))
    .query("deliveries >= 10")
)
high_risk_ids = driver_perf[driver_perf["fail_rate"] >= driver_perf["fail_rate"].quantile(0.75)].index
low_risk_ids  = driver_perf[driver_perf["fail_rate"] <= driver_perf["fail_rate"].quantile(0.25)].index
orders_high   = master[master["driver_id"].isin(high_risk_ids)]["has_missing"].astype(int)
orders_low    = master[master["driver_id"].isin(low_risk_ids)]["has_missing"].astype(int)
stat_drv, pval_drv = mannwhitneyu(orders_high, orders_low, alternative="greater")

reg_groups_data = [
    master[master["region"] == r]["has_missing"].astype(int).values
    for r in master["region"].unique()
]
stat_reg, pval_reg = kruskal(*reg_groups_data)

print("\n=== Statistical Tests ===")
print(f"  Mann-Whitney (high vs low risk drivers):        p = {pval_drv:.6f}  {'SIGNIFICANT' if pval_drv < 0.05 else 'not significant'}")
print(f"  Kruskal-Wallis (customer age groups):           p = {pval_age:.4f}   {'SIGNIFICANT' if pval_age < 0.05 else 'not significant'}")
print(f"  Kruskal-Wallis (customer value segments):       p = {pval_val:.4f}   {'SIGNIFICANT' if pval_val < 0.05 else 'not significant'}")
print(f"  Kruskal-Wallis (regions):                       p = {pval_reg:.6f}  {'SIGNIFICANT' if pval_reg < 0.05 else 'not significant'}")

# ── Build and save export
driver_pct_val = float(cat_shap.loc[cat_shap["category"] == "Driver",   "pct"].values[0])
client_pct_val = float(cat_shap.loc[cat_shap["category"] == "Customer", "pct"].values[0])
driver_range_val = float(variance_comparison.loc[variance_comparison["Dimension"] == "Driver (individual)", "Range (pp)"].values[0])
age_range_val    = float(variance_comparison.loc[variance_comparison["Dimension"] == "Age Group",            "Range (pp)"].values[0])

shap_export = []
for _, row in cat_shap.iterrows():
    level = "critical" if row["pct"] > 50 else ("warning" if row["pct"] > 10 else "neutral" if row["pct"] > 3 else "ok")
    shap_export.append({
        "category": row["category"],
        "pct":      round(float(row["pct"]), 1),
        "level":    level,
    })

statistical_export = {
    "mann_whitney_drivers": {
        "test":        "Mann-Whitney U",
        "description": "High risk (>=Q75) vs. Low risk (<=Q25) among drivers",
        "statistic":   round(float(stat_drv), 2),
        "p_value":     float(pval_drv),
        "significant": bool(pval_drv < 0.05),
        "label":       "p < 0.001" if pval_drv < 0.001 else f"p = {pval_drv:.4f}",
    },
    "kruskal_age_groups": {
        "test":        "Kruskal-Wallis",
        "description": "Failure rate by customer age group",
        "statistic":   round(float(stat_age), 4),
        "p_value":     float(pval_age),
        "significant": bool(pval_age < 0.05),
        "label":       f"p = {pval_age:.3f}",
    },
    "kruskal_value_segments": {
        "test":        "Kruskal-Wallis",
        "description": "Failure rate by customer value segment",
        "statistic":   round(float(stat_val), 4),
        "p_value":     float(pval_val),
        "significant": bool(pval_val < 0.05),
        "label":       f"p = {pval_val:.3f}",
    },
    "kruskal_regions": {
        "test":        "Kruskal-Wallis",
        "description": "Failure rate across regions",
        "statistic":   round(float(stat_reg), 2),
        "p_value":     float(pval_reg),
        "significant": bool(pval_reg < 0.05),
        "label":       "p < 0.001" if pval_reg < 0.001 else f"p = {pval_reg:.4f}",
    },
}

conclusion_export = {
    "model_auc":              round(auc, 4),
    "driver_shap_pct":        round(driver_pct_val, 1),
    "client_shap_pct":        round(client_pct_val, 1),
    "driver_vs_client_ratio": round(driver_pct_val / client_pct_val, 0),
    "driver_range_pp":        round(driver_range_val, 1),
    "age_range_pp":           round(age_range_val, 1),
    "worst_driver_rate":      round(float(driver_rates.max()) * 100, 1),
    "best_driver_rate":       round(float(driver_rates.min()) * 100, 1),
    "verdict":                "The problem lies with the drivers — not the customers.",
}

os.makedirs("data/processed", exist_ok=True)
output_path = "data/processed/shap_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "shap_categories":   shap_export,
        "statistical_tests": statistical_export,
        "conclusion":        conclusion_export,
        "generated_by":      "run_shap_export.py (equivalent to NB11 without charts)",
    }, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Saved to '{output_path}'")
print(f"  Driver: {driver_pct_val:.1f}% | Customer: {client_pct_val:.1f}% | Ratio: {driver_pct_val/client_pct_val:.0f}x")
print(f"  AUC: {auc:.4f} | Worst driver: {conclusion_export['worst_driver_rate']}%")
