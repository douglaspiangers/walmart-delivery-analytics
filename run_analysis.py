"""
run_analysis.py
Executa toda a pipeline de análise e gera os gráficos em reports/figures/.
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from src.data_loader import load_orders, load_customers, load_products, load_drivers, load_order_items
from src.preprocessing import clean_orders, clean_products, clean_drivers, build_master

FIGURES = os.path.join(os.path.dirname(__file__), "reports", "figures")
PROCESSED = os.path.join(os.path.dirname(__file__), "data", "processed")
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(PROCESSED, exist_ok=True)

sns.set_theme(style="whitegrid")
pd.set_option("display.float_format", "{:.2f}".format)


# ─────────────────────────────────────────────
# ETAPA 1 — LIMPEZA E MASTER DATAFRAME
# ─────────────────────────────────────────────
print("=" * 55)
print("  ETAPA 1 — Limpeza e construção do master dataframe")
print("=" * 55)

orders      = clean_orders(load_orders())
products    = clean_products(load_products())
drivers     = clean_drivers(load_drivers())
customers   = load_customers()
order_items = load_order_items()
master      = build_master(orders, customers, drivers)

master.to_parquet(f"{PROCESSED}/master.parquet", index=False)
products.to_parquet(f"{PROCESSED}/products.parquet", index=False)
order_items.to_parquet(f"{PROCESSED}/order_items.parquet", index=False)

print(f"  Pedidos:    {master.shape[0]:,}")
print(f"  Clientes:   {customers.shape[0]:,}")
print(f"  Motoristas: {drivers.shape[0]:,}")
print(f"  Produtos:   {products.shape[0]:,}")
print(f"  Intervalo:  {master['date'].min().date()} a {master['date'].max().date()}")


# ─────────────────────────────────────────────
# ETAPA 2 — KPIs EXECUTIVOS
# ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  ETAPA 2 — KPIs Executivos")
print("=" * 55)

total_revenue  = master["order_amount"].sum()
avg_ticket     = master["order_amount"].mean()
missing_rate   = master["has_missing"].mean()
total_orders   = master.shape[0]

print(f"  Total de Pedidos:        {total_orders:,}")
print(f"  Receita Total:           ${total_revenue:,.2f}")
print(f"  Ticket Médio:            ${avg_ticket:,.2f}")
print(f"  Taxa de Itens Faltando:  {missing_rate*100:.1f}%")
print(f"  Regiões Atendidas:       {master['region'].nunique()}")
print(f"  Motoristas Ativos:       {master['driver_id'].nunique()}")


# ─────────────────────────────────────────────
# FIGURA 1 — Tendência mensal
# ─────────────────────────────────────────────
print("\n[Gerando gráfico 01] Tendência mensal...")

monthly = (
    master.groupby("month")
    .agg(total_orders=("order_id", "count"), total_revenue=("order_amount", "sum"))
    .reset_index()
)

fig, axes = plt.subplots(1, 2, figsize=(16, 5))
axes[0].plot(monthly["month"], monthly["total_orders"], marker="o", color="steelblue", linewidth=2)
axes[0].set_title("Pedidos por Mês", fontsize=13, fontweight="bold")
axes[0].set_xlabel("Mês"); axes[0].set_ylabel("Nº de Pedidos")
axes[0].tick_params(axis="x", rotation=45)

axes[1].plot(monthly["month"], monthly["total_revenue"], marker="o", color="darkorange", linewidth=2)
axes[1].set_title("Receita por Mês (USD)", fontsize=13, fontweight="bold")
axes[1].set_xlabel("Mês"); axes[1].set_ylabel("Receita ($)")
axes[1].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig(f"{FIGURES}/01_monthly_trend.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 2 — Receita por região
# ─────────────────────────────────────────────
print("[Gerando gráfico 02] Receita por região...")

region_revenue = (
    master.groupby("region")["order_amount"]
    .sum().sort_values(ascending=False).reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(region_revenue["region"], region_revenue["order_amount"], color="steelblue")
ax.set_title("Receita Total por Região (USD)", fontsize=13, fontweight="bold")
ax.set_xlabel("Região"); ax.set_ylabel("Receita ($)")
plt.xticks(rotation=45, ha="right"); plt.tight_layout()
plt.savefig(f"{FIGURES}/02_revenue_by_region.png", dpi=150)
plt.close()

print("\n  Receita por região:")
for _, row in region_revenue.iterrows():
    print(f"    {row['region']:<25} ${row['order_amount']:,.0f}")


# ─────────────────────────────────────────────
# FIGURA 3 — Distribuição do valor dos pedidos
# ─────────────────────────────────────────────
print("\n[Gerando gráfico 03] Distribuição do valor dos pedidos...")

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(master["order_amount"], bins=40, color="steelblue", edgecolor="white")
ax.axvline(master["order_amount"].median(), color="red", linestyle="--",
           label=f"Mediana: ${master['order_amount'].median():.2f}")
ax.set_title("Distribuição do Valor dos Pedidos", fontsize=13, fontweight="bold")
ax.set_xlabel("Valor ($)"); ax.set_ylabel("Frequência"); ax.legend()
plt.tight_layout()
plt.savefig(f"{FIGURES}/03_order_amount_distribution.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 4 — Heatmap horário x dia da semana
# ─────────────────────────────────────────────
print("[Gerando gráfico 04] Heatmap horário × dia da semana...")

day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
pivot = (
    master.groupby(["day_of_week", "delivery_hour"])["order_id"]
    .count().unstack(fill_value=0).reindex(day_order)
)

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
ax.set_title("Volume de Entregas: Hora × Dia da Semana", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{FIGURES}/04_delivery_heatmap.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 5 — Distribuição por faixa etária
# ─────────────────────────────────────────────
print("[Gerando gráfico 05] Distribuição por faixa etária...")

age_bins = [18, 30, 45, 60, 100]
age_labels = ["18-29", "30-44", "45-59", "60+"]
master["age_group"] = pd.cut(master["customer_age"], bins=age_bins, labels=age_labels, right=False)
age_dist = master["age_group"].value_counts().sort_index().reset_index()
age_dist.columns = ["age_group", "count"]

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(age_dist["age_group"].astype(str), age_dist["count"], color="#4a90d9")
ax.set_title("Pedidos por Faixa Etária", fontsize=13, fontweight="bold")
ax.set_xlabel("Faixa Etária"); ax.set_ylabel("Nº de Pedidos")
plt.tight_layout()
plt.savefig(f"{FIGURES}/05_age_distribution.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 6 — Categorias de produto
# ─────────────────────────────────────────────
print("[Gerando gráfico 06] Categorias de produto...")

items_cat = order_items.merge(products[["product_id", "category"]], on="product_id", how="left")
cat_counts = items_cat["category"].value_counts().reset_index()
cat_counts.columns = ["category", "count"]

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(cat_counts["category"], cat_counts["count"], color="steelblue")
ax.set_title("Itens Pedidos por Categoria", fontsize=13, fontweight="bold")
ax.set_xlabel("Categoria"); ax.set_ylabel("Quantidade")
plt.xticks(rotation=45, ha="right"); plt.tight_layout()
plt.savefig(f"{FIGURES}/06_product_categories.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 7 — Top 10 produtos
# ─────────────────────────────────────────────
print("[Gerando gráfico 07] Top 10 produtos...")

top_products = (
    order_items
    .merge(products[["product_id", "product_name"]], on="product_id", how="left")
    .groupby("product_name").size()
    .reset_index(name="order_count")
    .sort_values("order_count", ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top_products["product_name"][::-1], top_products["order_count"][::-1], color="steelblue")
ax.set_title("Top 10 Produtos Mais Pedidos", fontsize=13, fontweight="bold")
ax.set_xlabel("Quantidade de Pedidos")
plt.tight_layout()
plt.savefig(f"{FIGURES}/07_top_products.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 8 — Ticket médio por faixa etária
# ─────────────────────────────────────────────
print("[Gerando gráfico 08] Ticket médio por faixa etária...")

ticket_by_age = (
    master.groupby("age_group", observed=True)["order_amount"]
    .mean().reset_index().rename(columns={"order_amount": "avg_ticket"})
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(ticket_by_age["age_group"].astype(str), ticket_by_age["avg_ticket"], color="#4a90d9")
ax.set_title("Ticket Médio por Faixa Etária", fontsize=13, fontweight="bold")
ax.set_xlabel("Faixa Etária"); ax.set_ylabel("Ticket Médio ($)")
plt.tight_layout()
plt.savefig(f"{FIGURES}/08_ticket_by_age.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# FIGURA 9 — Taxa de itens faltando por região
# ─────────────────────────────────────────────
print("[Gerando gráfico 09] Taxa de falha por região...")

region_missing = (
    master.groupby("region")
    .agg(total_orders=("order_id", "count"),
         missing_count=("has_missing", "sum"),
         missing_rate=("has_missing", "mean"))
    .sort_values("missing_rate", ascending=False).reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(region_missing["region"], region_missing["missing_rate"] * 100, color="salmon")
ax.axhline(missing_rate * 100, color="darkred", linestyle="--", label=f"Média geral: {missing_rate*100:.1f}%")
ax.set_title("Taxa de Itens Faltando por Região (%)", fontsize=13, fontweight="bold")
ax.set_xlabel("Região"); ax.set_ylabel("Taxa (%)"); ax.legend()
plt.xticks(rotation=45, ha="right"); plt.tight_layout()
plt.savefig(f"{FIGURES}/09_missing_by_region.png", dpi=150)
plt.close()

print("\n  Taxa de falha por região:")
for _, row in region_missing.iterrows():
    print(f"    {row['region']:<25} {row['missing_rate']*100:.1f}%  ({int(row['missing_count'])}/{int(row['total_orders'])} pedidos)")


# ─────────────────────────────────────────────
# FIGURA 10 — Taxa de falha por dia da semana
# ─────────────────────────────────────────────
print("\n[Gerando gráfico 10] Taxa de falha por dia da semana...")

day_missing = (
    master.groupby("day_of_week")["has_missing"]
    .mean().reindex(day_order).reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(day_missing["day_of_week"], day_missing["has_missing"] * 100, color="#5b8db8")
ax.axhline(missing_rate * 100, color="darkred", linestyle="--", label=f"Média geral: {missing_rate*100:.1f}%")
ax.set_title("Taxa de Itens Faltando por Dia da Semana (%)", fontsize=13, fontweight="bold")
ax.set_xlabel("Dia"); ax.set_ylabel("Taxa (%)"); ax.legend()
plt.xticks(rotation=45, ha="right"); plt.tight_layout()
plt.savefig(f"{FIGURES}/10_missing_by_weekday.png", dpi=150)
plt.close()

print("\n  Taxa por dia da semana:")
for _, row in day_missing.iterrows():
    marker = " <- pior" if row["has_missing"] == day_missing["has_missing"].max() else ""
    print(f"    {row['day_of_week']:<12} {row['has_missing']*100:.1f}%{marker}")


# ─────────────────────────────────────────────
# ANÁLISE DE CORRELAÇÃO
# ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  ETAPA 3 — Correlação: volume de itens × falhas")
print("=" * 55)

corr, pvalue = stats.pointbiserialr(master["items_delivered"], master["items_missing"])
avg_by_missing = master.groupby("has_missing")["items_delivered"].mean()

print(f"  Correlação:  {corr:.4f}")
print(f"  P-value:     {pvalue:.4f}")
print(f"  Média itens — pedidos SEM falha:  {avg_by_missing[False]:.2f}")
print(f"  Média itens — pedidos COM falha:  {avg_by_missing[True]:.2f}")
if pvalue < 0.05:
    print("  -> Correlacao estatisticamente significativa (p < 0.05)")
else:
    print("  -> Sem correlacao significativa")


# ─────────────────────────────────────────────
# FIGURA 11 — Ranking de motoristas
# ─────────────────────────────────────────────
print("\n[Gerando gráfico 11] Ranking de motoristas...")

driver_perf = (
    master.groupby(["driver_id", "driver_name"])
    .agg(deliveries=("order_id", "count"), missing_rate=("has_missing", "mean"))
    .reset_index()
)
qualified   = driver_perf[driver_perf["deliveries"] >= 5].copy()
worst       = qualified.nlargest(10, "missing_rate")
best        = qualified.nsmallest(10, "missing_rate")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
axes[0].barh(worst["driver_name"][::-1], worst["missing_rate"][::-1] * 100, color="salmon")
axes[0].set_title("Top 10 — Maior Taxa de Falha", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Taxa de Itens Faltando (%)")

axes[1].barh(best["driver_name"][::-1], best["missing_rate"][::-1] * 100, color="seagreen")
axes[1].set_title("Top 10 — Menor Taxa de Falha", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Taxa de Itens Faltando (%)")

plt.tight_layout()
plt.savefig(f"{FIGURES}/11_driver_ranking.png", dpi=150)
plt.close()

print(f"\n  Motoristas qualificados (>= 20 entregas): {qualified.shape[0]}")
print(f"  Pior taxa:   {worst['missing_rate'].max()*100:.1f}%  ({worst.iloc[0]['driver_name']})")
print(f"  Melhor taxa: {best['missing_rate'].min()*100:.1f}%  ({best.iloc[0]['driver_name']})")


# ─────────────────────────────────────────────
# FIGURA 12 — Heatmap falha: região × hora
# ─────────────────────────────────────────────
print("\n[Gerando gráfico 12] Heatmap falha por região e hora...")

pivot_missing = (
    master.groupby(["region", "delivery_hour"])["has_missing"]
    .mean().unstack(fill_value=0).round(2)
)

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(pivot_missing, annot=True, fmt=".2f", cmap="RdYlGn_r", ax=ax)
ax.set_title("Taxa de Itens Faltando: Região × Hora do Dia", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{FIGURES}/12_missing_heatmap.png", dpi=150)
plt.close()


# ─────────────────────────────────────────────
# SUMÁRIO FINAL
# ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  ANÁLISE CONCLUÍDA")
print("=" * 55)

worst_region  = region_missing.iloc[0]
best_region   = region_missing.iloc[-1]
worst_day     = day_missing.loc[day_missing["has_missing"].idxmax()]

print(f"\n  Pior região:    {worst_region['region']} ({worst_region['missing_rate']*100:.1f}% de falha)")
print(f"  Melhor região:  {best_region['region']} ({best_region['missing_rate']*100:.1f}% de falha)")
print(f"  Pior dia:       {worst_day['day_of_week']} ({worst_day['has_missing']*100:.1f}% de falha)")
print(f"\n  12 gráficos exportados em: reports/figures/")
print(f"  Dados processados em:      data/processed/")

# retorna os valores reais para atualizar o README
RESULTS = {
    "total_orders":   total_orders,
    "total_revenue":  total_revenue,
    "avg_ticket":     avg_ticket,
    "missing_rate":   missing_rate,
    "worst_region":   worst_region["region"],
    "worst_region_rate": worst_region["missing_rate"],
    "best_region":    best_region["region"],
    "best_region_rate": best_region["missing_rate"],
    "worst_day":      worst_day["day_of_week"],
    "worst_day_rate": worst_day["has_missing"],
    "worst_driver":   worst.iloc[0]["driver_name"],
    "worst_driver_rate": worst.iloc[0]["missing_rate"],
    "best_driver":    best.iloc[0]["driver_name"],
    "best_driver_rate": best.iloc[0]["missing_rate"],
    "corr":           corr,
    "pvalue":         pvalue,
}

import json
with open(f"{PROCESSED}/results_summary.json", "w") as f:
    json.dump(RESULTS, f, indent=2)

print("\n  Resumo de resultados salvo em: data/processed/results_summary.json")
