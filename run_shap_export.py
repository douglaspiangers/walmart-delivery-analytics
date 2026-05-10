"""
run_shap_export.py
Executa a lógica computacional do Notebook 11 e salva shap_results.json.
Equivalente ao NB11 sem os gráficos — para ambientes sem Jupyter instalado.
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

# ── Carregar dados
print("Carregando dados...")
master = pd.read_parquet("data/processed/master.parquet")

# ── Feature engineering — driver_fail_rate sem data leakage
# Para cada pedido, usa apenas entregas ANTERIORES do mesmo motorista (expanding window).
# Pedidos sem histórico recebem a taxa global como prior.
master = master.sort_values("date").reset_index(drop=True)
global_rate = master["has_missing"].mean()
master["driver_fail_rate"] = (
    master.groupby("driver_id")["has_missing"]
    .transform(lambda x: x.shift(1).expanding().mean())
    .fillna(global_rate)
)

def hour_to_period(h):
    if h < 6:  return "madrugada"
    if h < 12: return "manha"
    if h < 18: return "tarde"
    return "noite"

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
    "driver_fail_rate": "Motorista",
    "customer_age":     "Cliente",
    "order_amount":     "Pedido",
    "items_delivered":  "Pedido",
    "delivery_hour":    "Tempo",
    "period_enc":       "Tempo",
    "is_weekend":       "Tempo",
    "is_monday":        "Tempo",
    "region_enc":       "Localização",
}

df_model = master[FEATURES + ["has_missing"]].dropna()
X = df_model[FEATURES]
y = df_model["has_missing"].astype(int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# ── Treinar Random Forest
print(f"Treinando Random Forest ({len(X_train):,} amostras de treino)...")
rf = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1])
print(f"AUC = {auc:.4f}")

# ── SHAP values
print("Computando SHAP values (amostra de 800)...")
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

print("\n=== SHAP por Categoria ===")
for _, row in cat_shap.iterrows():
    print(f"  {row['category']:<15} {row['pct']:5.1f}%")

# ── Variância
master["age_group"] = pd.cut(
    master["customer_age"], bins=[18, 30, 45, 60, 100],
    labels=["18-29", "30-44", "45-59", "60+"]
)
master["value_segment"] = pd.qcut(
    master.groupby("customer_id")["order_amount"].transform("mean"),
    q=4, labels=["Baixo Valor", "Médio Valor", "Alto Valor", "VIP"]
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
    "Dimensão": ["Motorista (individual)", "Região", "Faixa Etária", "Segmento de Valor"],
    "Máximo":   [driver_rates.max(), region_rates.max(), age_rates.max(), value_rates.max()],
    "Mínimo":   [driver_rates.min(), region_rates.min(), age_rates.min(), value_rates.min()],
})
variance_comparison["Range (pp)"] = ((variance_comparison["Máximo"] - variance_comparison["Mínimo"]) * 100).round(1)

# ── Testes estatísticos
age_groups_data = [
    master[master["age_group"] == g]["has_missing"].astype(int).values
    for g in master["age_group"].cat.categories
    if len(master[master["age_group"] == g]) > 0
]
stat_age, pval_age = kruskal(*age_groups_data)

val_groups_data = [
    master[master["value_segment"] == g]["has_missing"].astype(int).values
    for g in ["Baixo Valor", "Médio Valor", "Alto Valor", "VIP"]
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

print("\n=== Testes Estatísticos ===")
print(f"  Mann-Whitney (motoristas alto vs baixo risco):  p = {pval_drv:.6f}  {'SIGNIFICATIVO' if pval_drv < 0.05 else 'não significativo'}")
print(f"  Kruskal-Wallis (faixas etárias do cliente):     p = {pval_age:.4f}   {'SIGNIFICATIVO' if pval_age < 0.05 else 'não significativo'}")
print(f"  Kruskal-Wallis (segmentos de valor do cliente): p = {pval_val:.4f}   {'SIGNIFICATIVO' if pval_val < 0.05 else 'não significativo'}")
print(f"  Kruskal-Wallis (regiões):                       p = {pval_reg:.6f}  {'SIGNIFICATIVO' if pval_reg < 0.05 else 'não significativo'}")

# ── Montar e salvar export
driver_pct_val = float(cat_shap.loc[cat_shap["category"] == "Motorista", "pct"].values[0])
client_pct_val = float(cat_shap.loc[cat_shap["category"] == "Cliente",   "pct"].values[0])
driver_range_val = float(variance_comparison.loc[variance_comparison["Dimensão"] == "Motorista (individual)", "Range (pp)"].values[0])
age_range_val    = float(variance_comparison.loc[variance_comparison["Dimensão"] == "Faixa Etária",           "Range (pp)"].values[0])

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
        "description": "Alta risco (>=Q75) vs. Baixo risco (<=Q25) entre motoristas",
        "statistic":   round(float(stat_drv), 2),
        "p_value":     float(pval_drv),
        "significant": bool(pval_drv < 0.05),
        "label":       "p < 0.001" if pval_drv < 0.001 else f"p = {pval_drv:.4f}",
    },
    "kruskal_age_groups": {
        "test":        "Kruskal-Wallis",
        "description": "Taxa de falha por faixa etária do cliente",
        "statistic":   round(float(stat_age), 4),
        "p_value":     float(pval_age),
        "significant": bool(pval_age < 0.05),
        "label":       f"p = {pval_age:.3f}",
    },
    "kruskal_value_segments": {
        "test":        "Kruskal-Wallis",
        "description": "Taxa de falha por segmento de valor do cliente",
        "statistic":   round(float(stat_val), 4),
        "p_value":     float(pval_val),
        "significant": bool(pval_val < 0.05),
        "label":       f"p = {pval_val:.3f}",
    },
    "kruskal_regions": {
        "test":        "Kruskal-Wallis",
        "description": "Taxa de falha entre regiões",
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
    "verdict":                "O problema está nos motoristas — não nos clientes.",
}

os.makedirs("data/processed", exist_ok=True)
output_path = "data/processed/shap_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "shap_categories":   shap_export,
        "statistical_tests": statistical_export,
        "conclusion":        conclusion_export,
        "generated_by":      "run_shap_export.py (equivalente ao NB11 sem gráficos)",
    }, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Salvo em '{output_path}'")
print(f"  Motorista: {driver_pct_val:.1f}% | Cliente: {client_pct_val:.1f}% | Razão: {driver_pct_val/client_pct_val:.0f}x")
print(f"  AUC: {auc:.4f} | Pior motorista: {conclusion_export['worst_driver_rate']}%")
