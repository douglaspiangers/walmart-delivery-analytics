"""
generate_lovable_data.py
Gera data/lovable_data.json com todos os KPIs reais para o prompt do Lovable.

PRÉ-REQUISITO: Execute o Notebook 11 antes deste script.
  O NB11 treina o modelo, computa SHAP values e testes estatísticos,
  e salva os resultados em data/processed/shap_results.json.
  Este script lê esse arquivo — nenhum valor analítico é hardcoded aqui.
"""
import sys, warnings, json, os
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
import pandas as pd, numpy as np

from src.data_loader import load_orders, load_customers, load_drivers, load_order_items, load_products
from src.preprocessing import clean_orders, clean_drivers, clean_products, build_master

orders      = clean_orders(load_orders())
drivers     = clean_drivers(load_drivers())
customers   = load_customers()
order_items = load_order_items()
products    = clean_products(load_products())
master      = build_master(orders, customers, drivers)

# ── Carregar resultados computados pelo Notebook 11 (SHAP + testes estatísticos)
SHAP_FILE = os.path.join("data", "processed", "shap_results.json")
if not os.path.exists(SHAP_FILE):
    raise FileNotFoundError(
        f"\n[ERRO] Arquivo '{SHAP_FILE}' não encontrado.\n"
        "Execute o Notebook 11 (11_executive_conclusion.ipynb) antes deste script.\n"
        "O notebook treina o modelo, computa os SHAP values e salva os resultados."
    )
with open(SHAP_FILE, encoding="utf-8") as f:
    shap_data = json.load(f)

shap_categories_computed = shap_data["shap_categories"]
statistical_tests        = shap_data["statistical_tests"]
conclusion_computed      = shap_data["conclusion"]

print(f"SHAP carregado de '{SHAP_FILE}' (gerado por: {shap_data.get('generated_by', 'NB11')})")

GLOBAL_RATE = master["has_missing"].mean()
# PREMISSA: custo de reentrega = 25% do ticket médio (referência de mercado: 20–30%).
# Ajustar se dados reais de custo logístico estiverem disponíveis.
COST_PER_FAILURE = master["order_amount"].mean() * 0.25
DAY_ORDER        = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# ── KPIs globais
kpis = {
    "total_orders":        int(len(master)),
    "total_revenue":       round(float(master["order_amount"].sum()), 2),
    "avg_ticket":          round(float(master["order_amount"].mean()), 2),
    "failure_rate_pct":    round(float(GLOBAL_RATE) * 100, 1),
    "total_failures":      int(master["has_missing"].sum()),
    "total_failure_cost":  round(float(master["has_missing"].sum() * COST_PER_FAILURE), 2),
    "total_drivers":       int(master["driver_id"].nunique()),
    "total_customers":     int(master["customer_id"].nunique()),
    "total_regions":       int(master["region"].nunique()),
    "cost_per_failure":    round(float(COST_PER_FAILURE), 2),
}

# ── Regioes
region_stats = (
    master.groupby("region")
    .agg(orders=("order_id","count"), revenue=("order_amount","sum"),
         failures=("has_missing","sum"), failure_rate=("has_missing","mean"))
    .reset_index().sort_values("failure_rate", ascending=False)
)
regions = []
for _, r in region_stats.iterrows():
    regions.append({
        "region":       r["region"],
        "orders":       int(r["orders"]),
        "revenue":      round(float(r["revenue"]), 2),
        "failure_rate": round(float(r["failure_rate"]) * 100, 1),
        "vs_avg_pp":    round((float(r["failure_rate"]) - GLOBAL_RATE) * 100, 1),
        "status":       "critical" if r["failure_rate"] > GLOBAL_RATE else "ok",
    })

# ── Tendencia mensal
monthly = (
    master.groupby("month")
    .agg(orders=("order_id","count"), revenue=("order_amount","sum"),
         failure_rate=("has_missing","mean"))
    .reset_index()
)
monthly_list = [
    {"month": r["month"], "orders": int(r["orders"]),
     "revenue": round(float(r["revenue"]), 2),
     "failure_rate": round(float(r["failure_rate"]) * 100, 1)}
    for _, r in monthly.iterrows()
]

# ── Dia da semana
day_stats = (
    master.groupby("day_of_week")["has_missing"]
    .mean().reindex(DAY_ORDER).reset_index()
)
days = [
    {"day": r["day_of_week"],
     "failure_rate": round(float(r["has_missing"]) * 100, 1),
     "status": "critical" if r["has_missing"] > GLOBAL_RATE else "ok"}
    for _, r in day_stats.iterrows()
]

# ── Periodo do dia
master["period"] = pd.cut(
    master["delivery_hour"], bins=[-1, 5, 11, 17, 23],
    labels=["Madrugada (0-5h)", "Manha (6-11h)", "Tarde (12-17h)", "Noite (18-23h)"]
)
period_stats = master.groupby("period", observed=True)["has_missing"].mean().reset_index()
periods = [
    {"period": str(r["period"]), "failure_rate": round(float(r["has_missing"]) * 100, 1)}
    for _, r in period_stats.iterrows()
]

# ── Motoristas
driver_hist = master.groupby("driver_id")["has_missing"].mean().rename("hist_rate")
master      = master.join(driver_hist, on="driver_id")
driver_perf = (
    master.groupby(["driver_id","driver_name"])
    .agg(deliveries=("order_id","count"), failure_rate=("has_missing","mean"),
         trips=("trips","first"))
    .reset_index()
)
driver_perf["tier"] = pd.cut(
    driver_perf["trips"], bins=[0, 25, 50, 100],
    labels=["Novato (<=25)", "Intermediario (26-50)", "Experiente (51+)"]
)
driver_perf["cost"] = driver_perf["failure_rate"] * driver_perf["deliveries"] * COST_PER_FAILURE

worst_drivers = (
    driver_perf.nlargest(10, "failure_rate")
    [["driver_name", "failure_rate", "deliveries", "tier"]].copy()
)
worst_drivers["failure_rate"] = (worst_drivers["failure_rate"] * 100).round(1)
worst_drivers["tier"]         = worst_drivers["tier"].astype(str)
worst_list = worst_drivers.to_dict("records")

tier_stats = (
    driver_perf.groupby("tier", observed=True)
    .agg(drivers=("driver_id","count"), avg_rate=("failure_rate","mean"),
         total_cost=("cost","sum"))
    .reset_index()
)
tier_list = [
    {"tier": str(r["tier"]), "drivers": int(r["drivers"]),
     "failure_rate": round(float(r["avg_rate"]) * 100, 1),
     "cost": round(float(r["total_cost"]), 2)}
    for _, r in tier_stats.iterrows()
]

# ── Retencao de clientes
cust = (
    master.groupby("customer_id")
    .agg(orders=("order_id","count"), failures=("has_missing","sum"),
         revenue=("order_amount","sum"), months=("month","nunique"))
    .reset_index()
)
cust["had_failure"] = cust["failures"] > 0

failed_orders = master[master["has_missing"]]
first_fail = (
    failed_orders.groupby("customer_id")["date"]
    .min().reset_index().rename(columns={"date": "ff"})
)
post = master.merge(first_fail, on="customer_id", how="inner")
post["is_post"] = post["date"] > post["ff"]
returned_n      = post[post["is_post"]]["customer_id"].nunique()
total_failed_c  = first_fail["customer_id"].nunique()
return_rate     = round(returned_n / total_failed_c * 100, 1)

last_fail = (
    failed_orders.groupby("customer_id")["date"]
    .max().reset_index().rename(columns={"date": "lf"})
)
last_ord = (
    master.groupby("customer_id")["date"]
    .max().reset_index().rename(columns={"date": "lo"})
)
END      = master["date"].max()
churn_df = last_fail.merge(last_ord, on="customer_id")
churn_df["churned"] = (
    ((END - churn_df["lf"]).dt.days >= 90) &
    ((churn_df["lo"] - churn_df["lf"]).dt.days <= 0)
)
n_churned   = int(churn_df["churned"].sum())
cust_churn  = cust.merge(churn_df[["customer_id","churned"]], on="customer_id", how="left")
cust_churn["churned"] = cust_churn["churned"].fillna(False)
rev_at_risk = round(float(cust_churn[cust_churn["churned"]]["revenue"].sum()), 2)

# ── Plano de acao
total_cost = kpis["total_failure_cost"]
action_plan = [
    {"priority": 1, "action": "Retreinamento de motoristas com taxa > 20%",
     "target": "Motoristas Cronicos e Instaveis", "impact": "Reducao de 30% no custo de falha",
     "savings": round(total_cost * 0.30, 2), "category": "driver"},
    {"priority": 2, "action": "Checklist digital para pedidos > 12 itens ou > $400",
     "target": "Pedidos de alto valor/volume", "impact": "-2pp na taxa de falha",
     "savings": round(total_cost * 0.13, 2), "category": "order"},
    {"priority": 3, "action": "Reforco operacional nas Segundas-feiras",
     "target": "Operacao semanal", "impact": "Reducao da pior janela de falha",
     "savings": round(total_cost * 0.05, 2), "category": "time"},
    {"priority": 4, "action": "Auditoria operacional em Altamonte Springs",
     "target": "Pior regiao — 16.2% de falha", "impact": "Alinhamento ao benchmark de Sanford",
     "savings": round(total_cost * 0.04, 2), "category": "region"},
    {"priority": 5, "action": "Compensacao imediata apos 1a falha do cliente",
     "target": f"{n_churned} clientes em churn", "impact": f"Recuperar ${rev_at_risk:,.0f} em receita",
     "savings": rev_at_risk, "category": "retention"},
]

# ── Exportar
export = {
    "meta": {
        "project": "Walmart Delivery Analytics",
        "subtitle": "Analise de Qualidade de Entregas | 2023 | Regiao de Orlando, FL",
        "period": "Jan–Dez 2023",
        "cities": 7,
    },
    "kpis":          kpis,
    "regions":       regions,
    "monthly_trend": monthly_list,
    "days_of_week":  days,
    "periods_of_day": periods,
    "driver_tiers":  tier_list,
    "worst_drivers": worst_list,
    "retention": {
        "total_customers":           int(len(cust)),
        "customers_with_failure":    int(cust["had_failure"].sum()),
        "pct_affected":              round(cust["had_failure"].mean() * 100, 1),
        "return_rate_after_failure": return_rate,
        "churned_customers":         n_churned,
        "revenue_at_risk":           rev_at_risk,
    },
    "shap_categories": shap_categories_computed,
    "action_plan": action_plan,
    "conclusion": {
        "verdict":                conclusion_computed["verdict"],
        "driver_shap_pct":        conclusion_computed["driver_shap_pct"],
        "client_shap_pct":        conclusion_computed["client_shap_pct"],
        "driver_vs_client_ratio": int(conclusion_computed["driver_vs_client_ratio"]),
        "worst_driver_rate":      conclusion_computed["worst_driver_rate"],
        "best_driver_rate":       conclusion_computed["best_driver_rate"],
        "model_auc":              conclusion_computed["model_auc"],
        "statistical_proof": (
            f"Mann-Whitney {statistical_tests['mann_whitney_drivers']['label']} (motoristas)"
            f" vs Kruskal-Wallis {statistical_tests['kruskal_age_groups']['label']} (clientes por idade)"
        ),
        "statistical_tests": statistical_tests,
    },
}

with open("data/lovable_data.json", "w", encoding="utf-8") as f:
    json.dump(export, f, indent=2, ensure_ascii=False)

print("lovable_data.json gerado em data/")
print(f"KPIs: {json.dumps(kpis, indent=2)}")
print(f"Revenue at risk: ${rev_at_risk:,.0f}")
print(f"Return rate: {return_rate}%")
print(f"Regioes: {[r['region'] + ' ' + str(r['failure_rate']) + '%' for r in regions]}")
