"""
export_powerbi.py
=================
Gera os arquivos CSV para o dashboard Power BI no modelo estrela (Star Schema).

Estrutura gerada em data/powerbi/:
├── FATO
│   └── fct_orders.csv          ← tabela central com todas as métricas
├── DIMENSÕES
│   ├── dim_date.csv             ← calendário completo com atributos de tempo
│   ├── dim_customers.csv        ← perfil + segmentação + flag de churn
│   ├── dim_drivers.csv          ← perfil + tier + performance H1/H2 + quadrante
│   ├── dim_regions.csv          ← KPIs por região
│   └── dim_products.csv         ← catálogo de produtos
└── AGREGADOS (visuais complexos)
    ├── agg_monthly_kpis.csv     ← tendência mensal
    ├── agg_region_day.csv       ← heatmap falha por região × dia
    ├── agg_hour_day.csv         ← heatmap volume/falha por hora × dia
    ├── agg_driver_monthly.csv   ← performance mensal por motorista
    ├── agg_financial_impact.csv ← impacto financeiro por segmento
    └── agg_top_products.csv     ← ranking de produtos

Execução: python export_powerbi.py
"""

import os
import sys
import warnings
import json
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np

from src.data_loader import (
    load_orders, load_customers, load_drivers,
    load_products, load_order_items,
)
from src.preprocessing import clean_orders, clean_products, clean_drivers, build_master

OUT = os.path.join(os.path.dirname(__file__), "data", "powerbi")
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# CARREGAR E LIMPAR DADOS
# ─────────────────────────────────────────────────────────────────
print("Carregando dados...")
orders      = clean_orders(load_orders())
drivers     = clean_drivers(load_drivers())
customers   = load_customers()
products    = clean_products(load_products())
order_items = load_order_items()
master      = build_master(orders, customers, drivers)

# Constantes de negócio
REDELIVERY_COST_RATE = 0.25          # 25% do ticket como custo de reentrega
AVG_TICKET           = master["order_amount"].mean()
COST_PER_FAILURE     = AVG_TICKET * REDELIVERY_COST_RATE
GLOBAL_FAILURE_RATE  = master["has_missing"].mean()
DATASET_END          = master["date"].max()


# ═════════════════════════════════════════════════════════════════
# 1. dim_date — Calendário completo
# ═════════════════════════════════════════════════════════════════
print("[1/8] Gerando dim_date...")

date_range = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
dim_date = pd.DataFrame({"date": date_range})
dim_date["date_key"]     = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
dim_date["day_of_week"]  = dim_date["date"].dt.day_name()
dim_date["day_number"]   = dim_date["date"].dt.dayofweek + 1   # 1=Mon … 7=Sun
dim_date["week_number"]  = dim_date["date"].dt.isocalendar().week.astype(int)
dim_date["month_number"] = dim_date["date"].dt.month
dim_date["month_name"]   = dim_date["date"].dt.strftime("%B")
dim_date["month_short"]  = dim_date["date"].dt.strftime("%b")
dim_date["quarter"]      = dim_date["date"].dt.quarter
dim_date["semester"]     = np.where(dim_date["month_number"] <= 6, "H1", "H2")
dim_date["year"]         = dim_date["date"].dt.year
dim_date["is_weekend"]   = dim_date["day_number"].isin([6, 7])
dim_date["month_year"]   = dim_date["date"].dt.strftime("%Y-%m")

dim_date.to_csv(f"{OUT}/dim_date.csv", index=False)
print(f"   dim_date: {len(dim_date)} linhas")


# ═════════════════════════════════════════════════════════════════
# 2. dim_drivers — Perfil + métricas pré-computadas
# ═════════════════════════════════════════════════════════════════
print("[2/8] Gerando dim_drivers...")

# Performance global por motorista
drv_global = (
    master.groupby(["driver_id", "driver_name"])
    .agg(
        total_deliveries=("order_id", "count"),
        total_failures=("has_missing", "sum"),
        hist_failure_rate=("has_missing", "mean"),
        total_revenue=("order_amount", "sum"),
        avg_ticket=("order_amount", "mean"),
        trips=("trips", "first"),
        driver_age=("age", "first"),
    )
    .reset_index()
)

# Experience tier
drv_global["exp_tier"] = pd.cut(
    drv_global["trips"],
    bins=[0, 25, 50, 100],
    labels=["Novato (≤25 trips)", "Intermediário (26–50 trips)", "Experiente (51+ trips)"],
).astype(str)

# H1 vs H2
def semester_rate(df, semester):
    months = range(1, 7) if semester == "H1" else range(7, 13)
    sub = df[df["date"].dt.month.isin(months)]
    return (
        sub.groupby("driver_id")
        .agg(deliveries=("order_id", "count"), rate=("has_missing", "mean"))
        .query("deliveries >= 5")
        .rename(columns={"rate": f"rate_{semester.lower()}", "deliveries": f"del_{semester.lower()}"})
    )

r_h1 = semester_rate(master, "H1")
r_h2 = semester_rate(master, "H2")
h1h2 = r_h1.join(r_h2, how="inner")
h1h2["delta_h1_h2"] = h1h2["rate_h2"] - h1h2["rate_h1"]
h1h2["improved_h1_h2"] = h1h2["delta_h1_h2"] < 0

drv_global = drv_global.merge(
    h1h2[["rate_h1", "rate_h2", "delta_h1_h2", "improved_h1_h2"]],
    on="driver_id", how="left"
)

# Consistency Index (CV mensal)
monthly_drv = (
    master.groupby(["driver_id", "month"])
    .agg(del_=("order_id", "count"), rate=("has_missing", "mean"))
    .reset_index()
)
cons = (
    monthly_drv.groupby("driver_id")
    .agg(months_active=("month", "count"), avg_rate=("rate", "mean"), std_rate=("rate", "std"))
    .reset_index()
)
cons["consistency_cv"] = (cons["std_rate"] / cons["avg_rate"]).fillna(0).round(3)
drv_global = drv_global.merge(cons[["driver_id", "consistency_cv", "months_active"]], on="driver_id", how="left")

# Quadrante de intervenção — usa mediana global (todos os motoristas com >= 5 entregas)
qualified = drv_global[drv_global["total_deliveries"] >= 5].copy()
rate_med = qualified["hist_failure_rate"].median()
cv_med   = qualified["consistency_cv"].median()

def assign_quadrant(row):
    if row["total_deliveries"] < 5:
        return "Volume Insuficiente (<5)"
    high_risk = row["hist_failure_rate"] > rate_med
    high_cv   = row["consistency_cv"] > cv_med
    if high_risk and not high_cv: return "Crônico — Ação Disciplinar"
    if high_risk and high_cv:     return "Instável — Coaching"
    if not high_risk and not high_cv: return "Referência — Boas Práticas"
    return "Monitorar — Baixo Risco"

drv_global["intervention_quadrant"] = drv_global.apply(assign_quadrant, axis=1)

# Custo estimado por motorista
drv_global["estimated_failure_cost"] = drv_global["total_failures"] * COST_PER_FAILURE
drv_global["risk_flag"] = drv_global["hist_failure_rate"] > 0.20

dim_drivers = drv_global.round(4)
dim_drivers.to_csv(f"{OUT}/dim_drivers.csv", index=False)
print(f"   dim_drivers: {len(dim_drivers)} linhas | {dim_drivers['intervention_quadrant'].value_counts().to_dict()}")


# ═════════════════════════════════════════════════════════════════
# 3. dim_customers — Perfil + segmentação + churn
# ═════════════════════════════════════════════════════════════════
print("[3/8] Gerando dim_customers...")

cust_stats = (
    master.groupby(["customer_id", "customer_name", "customer_age"])
    .agg(
        total_orders=("order_id", "count"),
        total_failures=("has_missing", "sum"),
        total_revenue=("order_amount", "sum"),
        avg_ticket=("order_amount", "mean"),
        months_active=("month", "nunique"),
        first_order=("date", "min"),
        last_order=("date", "max"),
    )
    .reset_index()
)

cust_stats["failure_rate"]     = cust_stats["total_failures"] / cust_stats["total_orders"]
cust_stats["orders_per_month"] = cust_stats["total_orders"] / cust_stats["months_active"]
cust_stats["had_failure"]      = cust_stats["total_failures"] > 0

# Faixa etária
cust_stats["age_group"] = pd.cut(
    cust_stats["customer_age"],
    bins=[18, 30, 45, 60, 100],
    labels=["18–29", "30–44", "45–59", "60+"],
).astype(str)

# Grupo de falha
def fail_group(n):
    if n == 0:   return "0 — Sem falha"
    if n == 1:   return "1 — Uma falha"
    if n == 2:   return "2 — Duas falhas"
    return "3+ — Múltiplas falhas"

cust_stats["failure_group"] = cust_stats["total_failures"].apply(fail_group)

# Segmento de valor (Revenue quartile)
q75 = cust_stats["total_revenue"].quantile(0.75)
q50 = cust_stats["total_revenue"].quantile(0.50)
q25 = cust_stats["total_revenue"].quantile(0.25)

def value_segment(rev):
    if rev >= q75: return "VIP"
    if rev >= q50: return "Alto Valor"
    if rev >= q25: return "Médio Valor"
    return "Baixo Valor"

cust_stats["value_segment"] = cust_stats["total_revenue"].apply(value_segment)

# Churn pós-falha (não comprou nos 90 dias após a última falha)
failed_orders = master[master["has_missing"]]
last_fail = (
    failed_orders.groupby("customer_id")["date"]
    .max().reset_index().rename(columns={"date": "last_failure_date"})
)
last_ord = (
    master.groupby("customer_id")["date"]
    .max().reset_index().rename(columns={"date": "last_order_date"})
)
churn_df = last_fail.merge(last_ord, on="customer_id")
churn_df["days_since_last_failure"] = (DATASET_END - churn_df["last_failure_date"]).dt.days
churn_df["days_after_failure"]      = (churn_df["last_order_date"] - churn_df["last_failure_date"]).dt.days
churn_df["churned"] = (
    (churn_df["days_since_last_failure"] >= 90) &
    (churn_df["days_after_failure"] <= 0)
)
cust_stats = cust_stats.merge(churn_df[["customer_id", "churned"]], on="customer_id", how="left")
cust_stats["churned"] = cust_stats["churned"].fillna(False)

# Return rate flag: voltou após falha?
first_fail = (
    failed_orders.groupby("customer_id")["date"]
    .min().reset_index().rename(columns={"date": "first_failure_date"})
)
post_fail = master.merge(first_fail, on="customer_id", how="inner")
post_fail["is_post"] = post_fail["date"] > post_fail["first_failure_date"]
returned = post_fail[post_fail["is_post"]]["customer_id"].unique()
cust_stats["returned_after_failure"] = cust_stats["customer_id"].isin(returned)

dim_customers = cust_stats.round(4)
dim_customers.to_csv(f"{OUT}/dim_customers.csv", index=False)
print(f"   dim_customers: {len(dim_customers)} linhas | churned: {dim_customers['churned'].sum()} | VIP: {(dim_customers['value_segment']=='VIP').sum()}")


# ═════════════════════════════════════════════════════════════════
# 4. dim_regions — KPIs por região
# ═════════════════════════════════════════════════════════════════
print("[4/8] Gerando dim_regions...")

dim_regions = (
    master.groupby("region")
    .agg(
        total_orders=("order_id", "count"),
        total_failures=("has_missing", "sum"),
        failure_rate=("has_missing", "mean"),
        total_revenue=("order_amount", "sum"),
        avg_ticket=("order_amount", "mean"),
        unique_drivers=("driver_id", "nunique"),
        unique_customers=("customer_id", "nunique"),
    )
    .reset_index()
)
dim_regions["failure_cost_estimated"] = dim_regions["total_failures"] * COST_PER_FAILURE
dim_regions["vs_global_avg_pp"]       = (dim_regions["failure_rate"] - GLOBAL_FAILURE_RATE) * 100
dim_regions["performance_label"]      = np.where(
    dim_regions["failure_rate"] > GLOBAL_FAILURE_RATE, "Acima da Média", "Abaixo da Média"
)
dim_regions.to_csv(f"{OUT}/dim_regions.csv", index=False)
print(f"   dim_regions: {len(dim_regions)} regiões")


# ═════════════════════════════════════════════════════════════════
# 5. dim_products — Catálogo enriquecido
# ═════════════════════════════════════════════════════════════════
print("[5/8] Gerando dim_products...")

# Contar pedidos por produto
product_orders = (
    order_items.groupby("product_id").size().reset_index(name="order_count")
)
dim_products = products.merge(product_orders, on="product_id", how="left")
dim_products["order_count"] = dim_products["order_count"].fillna(0).astype(int)
dim_products["revenue_potential"] = dim_products["order_count"] * dim_products["price"]
dim_products.to_csv(f"{OUT}/dim_products.csv", index=False)
print(f"   dim_products: {len(dim_products)} produtos | {dim_products['category'].nunique()} categorias")


# ═════════════════════════════════════════════════════════════════
# 6. fct_orders — Tabela fato central
# ═════════════════════════════════════════════════════════════════
print("[6/8] Gerando fct_orders...")

fct = orders.copy()
fct["date_key"]   = fct["date"].dt.strftime("%Y%m%d").astype(int)
fct["has_missing_int"] = fct["has_missing"].astype(int)
fct["failure_cost"]    = fct["has_missing"].astype(int) * COST_PER_FAILURE

fct["period"] = pd.cut(
    fct["delivery_hour"],
    bins=[-1, 5, 11, 17, 23],
    labels=["Madrugada (0–5h)", "Manhã (6–11h)", "Tarde (12–17h)", "Noite (18–23h)"]
).astype(str)

fct["order_size_tier"] = pd.cut(
    fct["items_delivered"],
    bins=[0, 5, 10, 20, 100],
    labels=["Pequeno (1–5)", "Médio (6–10)", "Grande (11–20)", "Extra (21+)"]
).astype(str)

fct["amount_tier"] = pd.cut(
    fct["order_amount"],
    bins=[0, 100, 250, 400, 10000],
    labels=["< $100", "$100–$250", "$250–$400", "> $400"]
).astype(str)

fct["week_number"] = fct["date"].dt.isocalendar().week.astype(int)
fct["quarter"]     = fct["date"].dt.quarter
fct["semester"]    = np.where(fct["date"].dt.month <= 6, "H1", "H2")

# Manter só colunas necessárias (chaves + métricas)
fct_orders = fct[[
    "order_id", "date_key", "date", "driver_id", "customer_id", "region",
    "order_amount", "items_delivered", "items_missing", "delivery_hour",
    "has_missing", "has_missing_int", "failure_cost",
    "day_of_week", "month", "week_number", "quarter", "semester",
    "period", "order_size_tier", "amount_tier",
]]

fct_orders.to_csv(f"{OUT}/fct_orders.csv", index=False)
print(f"   fct_orders: {len(fct_orders)} linhas | {fct_orders.columns.tolist()}")


# ═════════════════════════════════════════════════════════════════
# 7. TABELAS AGREGADAS (visuais complexos prontos)
# ═════════════════════════════════════════════════════════════════

# ── 7a. Tendência mensal
print("[7/8] Gerando tabelas agregadas...")

agg_monthly = (
    master.groupby("month")
    .agg(
        total_orders=("order_id", "count"),
        total_revenue=("order_amount", "sum"),
        avg_ticket=("order_amount", "mean"),
        total_failures=("has_missing", "sum"),
        failure_rate=("has_missing", "mean"),
    )
    .reset_index()
)
agg_monthly["failure_cost"]       = agg_monthly["total_failures"] * COST_PER_FAILURE
agg_monthly["mom_revenue_change"] = agg_monthly["total_revenue"].pct_change() * 100
agg_monthly["mom_failure_change"] = agg_monthly["failure_rate"].diff() * 100
agg_monthly.to_csv(f"{OUT}/agg_monthly_kpis.csv", index=False)

# ── 7b. Heatmap hora × dia
day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

agg_hour_day = (
    master.groupby(["day_of_week", "delivery_hour"])
    .agg(
        volume=("order_id", "count"),
        failure_rate=("has_missing", "mean"),
        revenue=("order_amount", "sum"),
    )
    .reset_index()
)
agg_hour_day["day_order"] = agg_hour_day["day_of_week"].map({d: i for i, d in enumerate(day_order)})
agg_hour_day = agg_hour_day.sort_values(["day_order", "delivery_hour"]).drop(columns="day_order")
agg_hour_day.to_csv(f"{OUT}/agg_hour_day_heatmap.csv", index=False)

# ── 7c. Falha por região × dia
agg_region_day = (
    master.groupby(["region", "day_of_week"])
    .agg(
        total_orders=("order_id", "count"),
        failure_rate=("has_missing", "mean"),
        total_failures=("has_missing", "sum"),
    )
    .reset_index()
)
agg_region_day["day_order"] = agg_region_day["day_of_week"].map({d: i for i, d in enumerate(day_order)})
agg_region_day = agg_region_day.sort_values(["region", "day_order"]).drop(columns="day_order")
agg_region_day.to_csv(f"{OUT}/agg_region_day.csv", index=False)

# ── 7d. Performance mensal de motoristas (Consistency Index)
agg_driver_monthly = (
    master.groupby(["driver_id", "driver_name", "month"])
    .agg(
        deliveries=("order_id", "count"),
        failures=("has_missing", "sum"),
        failure_rate=("has_missing", "mean"),
        revenue=("order_amount", "sum"),
    )
    .reset_index()
)
agg_driver_monthly.to_csv(f"{OUT}/agg_driver_monthly.csv", index=False)

# ── 7e. Impacto financeiro por quadrante
fin_impact = (
    dim_drivers.groupby("intervention_quadrant")
    .agg(
        motoristas=("driver_id", "count"),
        total_deliveries=("total_deliveries", "sum"),
        total_failures=("total_failures", "sum"),
        total_failure_cost=("estimated_failure_cost", "sum"),
        avg_failure_rate=("hist_failure_rate", "mean"),
    )
    .reset_index()
)
fin_impact["pct_total_cost"] = fin_impact["total_failure_cost"] / fin_impact["total_failure_cost"].sum() * 100
fin_impact["savings_if_30pct_reduction"] = fin_impact["total_failure_cost"] * 0.30
fin_impact.to_csv(f"{OUT}/agg_financial_impact.csv", index=False)

# ── 7f. Top produtos
agg_products = (
    order_items
    .merge(products[["product_id","product_name","category","price"]], on="product_id", how="left")
    .groupby(["product_id","product_name","category","price"])
    .size().reset_index(name="order_count")
    .sort_values("order_count", ascending=False)
)
agg_products["revenue_generated"] = agg_products["order_count"] * agg_products["price"]
agg_products.to_csv(f"{OUT}/agg_top_products.csv", index=False)

# ── 7g. Retenção de clientes (agregado para visuals de retenção)
retention_summary = pd.DataFrame({
    "metric": [
        "Total de Clientes",
        "Clientes com Falha",
        "% Base Impactada",
        "Retornaram Após Falha",
        "Return Rate (%)",
        "Clientes em Churn",
        "Revenue at Risk ($)",
        "Custo Médio por Churn ($)",
    ],
    "value": [
        len(dim_customers),
        int(dim_customers["had_failure"].sum()),
        round(dim_customers["had_failure"].mean() * 100, 1),
        int(dim_customers["returned_after_failure"].sum()),
        round(dim_customers["returned_after_failure"].mean() * 100, 1),
        int(dim_customers["churned"].sum()),
        round(dim_customers[dim_customers["churned"]]["total_revenue"].sum(), 2),
        round(dim_customers[dim_customers["churned"]]["total_revenue"].mean(), 2),
    ],
})
retention_summary.to_csv(f"{OUT}/agg_retention_summary.csv", index=False)


# ═════════════════════════════════════════════════════════════════
# 8. KPIs GLOBAIS — cartão de referência
# ═════════════════════════════════════════════════════════════════
print("[8/8] Gerando global_kpis.json...")

global_kpis = {
    "total_orders":          int(len(fct_orders)),
    "total_revenue":         round(float(fct_orders["order_amount"].sum()), 2),
    "avg_ticket":            round(float(fct_orders["order_amount"].mean()), 2),
    "global_failure_rate":   round(float(GLOBAL_FAILURE_RATE), 4),
    "total_failures":        int(fct_orders["has_missing_int"].sum()),
    "total_failure_cost":    round(float(fct_orders["failure_cost"].sum()), 2),
    "total_drivers":         int(dim_drivers["driver_id"].nunique()),
    "total_customers":       int(dim_customers["customer_id"].nunique()),
    "total_regions":         int(dim_regions["region"].nunique()),
    "worst_region":          dim_regions.loc[dim_regions["failure_rate"].idxmax(), "region"],
    "worst_region_rate":     round(float(dim_regions["failure_rate"].max()), 4),
    "best_region":           dim_regions.loc[dim_regions["failure_rate"].idxmin(), "region"],
    "best_region_rate":      round(float(dim_regions["failure_rate"].min()), 4),
    "chronic_drivers":       int((dim_drivers["intervention_quadrant"] == "Crônico — Ação Disciplinar").sum()),
    "coaching_drivers":      int((dim_drivers["intervention_quadrant"] == "Instável — Coaching").sum()),
    "customers_with_failure": int(dim_customers["had_failure"].sum()),
    "customer_churn_count":  int(dim_customers["churned"].sum()),
    "revenue_at_risk":       round(float(dim_customers[dim_customers["churned"]]["total_revenue"].sum()), 2),
    "cost_per_failure":      round(float(COST_PER_FAILURE), 2),
}

with open(f"{OUT}/global_kpis.json", "w") as f:
    json.dump(global_kpis, f, indent=2)


# ═════════════════════════════════════════════════════════════════
# SUMÁRIO
# ═════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("  EXPORTAÇÃO CONCLUÍDA")
print("=" * 60)
print(f"  Destino: data/powerbi/")
print()

files = {
    "fct_orders.csv":            f"{len(fct_orders):,} linhas — tabela fato",
    "dim_date.csv":              "365 linhas — calendário completo",
    "dim_drivers.csv":           f"{len(dim_drivers):,} motoristas — com tier e quadrante",
    "dim_customers.csv":         f"{len(dim_customers):,} clientes — com churn e segmento",
    "dim_regions.csv":           f"{len(dim_regions)} regiões — com KPIs",
    "dim_products.csv":          f"{len(dim_products):,} produtos — com rank",
    "agg_monthly_kpis.csv":      "12 meses — tendência MoM",
    "agg_hour_day_heatmap.csv":  "Heatmap hora × dia",
    "agg_region_day.csv":        "Falha por região × dia",
    "agg_driver_monthly.csv":    f"{len(agg_driver_monthly):,} linhas — performance mensal",
    "agg_financial_impact.csv":  "Custo por quadrante de intervenção",
    "agg_top_products.csv":      f"{len(agg_products):,} produtos ranqueados",
    "agg_retention_summary.csv": "8 métricas de retenção",
    "global_kpis.json":          "KPIs globais para referência",
}

for fname, desc in files.items():
    size = os.path.getsize(f"{OUT}/{fname}")
    print(f"  {'OK':2}  {fname:<35} {desc}  ({size/1024:.1f} KB)")

print()
print(f"  Custo por falha estimado: ${COST_PER_FAILURE:.2f}")
print(f"  Taxa de falha global:     {GLOBAL_FAILURE_RATE*100:.1f}%")
print(f"  Revenue at risk:          ${global_kpis['revenue_at_risk']:,.0f}")
