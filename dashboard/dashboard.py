"""
dashboard.py
Dashboard interativo para análise de qualidade de entrega Walmart.
Execução: python dashboard/dashboard.py
Acesso:   http://localhost:8050
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score

from src.data_loader import load_orders, load_customers, load_products, load_drivers, load_order_items
from src.preprocessing import clean_orders, clean_products, clean_drivers, build_master

# ─────────────────────────────────────────────
# CARREGAR E PREPARAR DADOS
# ─────────────────────────────────────────────
PROCESSED = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

if os.path.exists(f"{PROCESSED}/master.parquet"):
    master      = pd.read_parquet(f"{PROCESSED}/master.parquet")
    products    = pd.read_parquet(f"{PROCESSED}/products.parquet")
    order_items = pd.read_parquet(f"{PROCESSED}/order_items.parquet")
else:
    orders      = clean_orders(load_orders())
    products    = clean_products(load_products())
    drivers     = clean_drivers(load_drivers())
    customers   = load_customers()
    order_items = load_order_items()
    master      = build_master(orders, customers, drivers)

# Features derivadas
master["period"] = pd.cut(
    master["delivery_hour"],
    bins=[-1, 5, 11, 17, 23],
    labels=["Madrugada", "Manhã", "Tarde", "Noite"]
)

# KPIs
TOTAL_ORDERS   = master.shape[0]
TOTAL_REVENUE  = master["order_amount"].sum()
AVG_TICKET     = master["order_amount"].mean()
MISSING_RATE   = master["has_missing"].mean()
TOTAL_DRIVERS  = master["driver_id"].nunique()
TOTAL_REGIONS  = master["region"].nunique()

# ─────────────────────────────────────────────
# MODELO DE RISCO (treinado na inicialização)
# ─────────────────────────────────────────────
# Feature: taxa histórica de falha por motorista
driver_hist = (
    master.groupby("driver_id")["has_missing"]
    .mean()
    .reset_index()
    .rename(columns={"has_missing": "driver_hist_rate"})
)
master = master.merge(driver_hist, on="driver_id", how="left")

le_region = LabelEncoder()
le_day    = LabelEncoder()
master["region_enc"] = le_region.fit_transform(master["region"])
master["day_enc"]    = le_day.fit_transform(master["day_of_week"])

RISK_FEATURES = ["region_enc", "day_enc", "delivery_hour",
                 "order_amount", "items_delivered", "driver_hist_rate"]
X_train = master[RISK_FEATURES].values
y_train = master["has_missing"].values

risk_model = LogisticRegression(max_iter=1000, random_state=42)
risk_model.fit(X_train, y_train)
MODEL_AUC = roc_auc_score(y_train, risk_model.predict_proba(X_train)[:, 1])

DRIVER_LIST = (
    master[["driver_id", "driver_name", "driver_hist_rate"]]
    .drop_duplicates("driver_id")
    .sort_values("driver_name")
)
REGION_LIST  = sorted(master["region"].unique().tolist())
DAY_LIST     = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Cohort de motoristas (pré-computado)
master["exp_tier"] = pd.cut(
    master["trips"],
    bins=[0, 25, 50, 100],
    labels=["Novato (≤25)", "Intermediário (26–50)", "Experiente (51+)"]
)
REDELIVERY_COST = AVG_TICKET * 0.25

# Perfil de clientes para retenção (pré-computado)
cust_profile = (
    master.groupby("customer_id")
    .agg(
        total_orders=("order_id", "count"),
        total_failures=("has_missing", "sum"),
        total_revenue=("order_amount", "sum"),
        months_active=("month", "nunique"),
        first_order=("date", "min"),
        last_order=("date", "max"),
    )
    .reset_index()
)
cust_profile["had_failure"]     = cust_profile["total_failures"] > 0
cust_profile["orders_per_month"] = cust_profile["total_orders"] / cust_profile["months_active"]
cust_profile["failure_group"] = pd.cut(
    cust_profile["total_failures"],
    bins=[-1, 0, 1, 2, 100],
    labels=["0 falhas", "1 falha", "2 falhas", "3+ falhas"]
)

# ─────────────────────────────────────────────
# Paleta
COLORS = {
    "primary":   "#1f77b4",
    "danger":    "#d62728",
    "success":   "#2ca02c",
    "warning":   "#ff7f0e",
    "neutral":   "#7f7f7f",
    "bg":        "#f8f9fa",
    "card":      "#ffffff",
    "border":    "#dee2e6",
}

# ─────────────────────────────────────────────
# INICIALIZAR APP
# ─────────────────────────────────────────────
app = dash.Dash(
    __name__,
    title="Walmart Delivery Analytics",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def kpi_card(title, value, subtitle="", color="#1f77b4"):
    return html.Div(
        style={
            "backgroundColor": COLORS["card"],
            "borderRadius": "8px",
            "padding": "20px",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
            "borderTop": f"4px solid {color}",
            "flex": "1",
            "minWidth": "150px",
        },
        children=[
            html.P(title, style={"margin": "0", "color": "#666", "fontSize": "13px", "fontWeight": "600"}),
            html.H3(value, style={"margin": "8px 0 4px", "color": "#1a1a2e", "fontSize": "26px"}),
            html.P(subtitle, style={"margin": "0", "color": "#999", "fontSize": "12px"}),
        ]
    )


# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────
app.layout = html.Div(
    style={"fontFamily": "Inter, Segoe UI, sans-serif", "backgroundColor": COLORS["bg"], "minHeight": "100vh"},
    children=[

        # Header
        html.Div(
            style={
                "background": "linear-gradient(135deg, #1f77b4 0%, #0d4f8c 100%)",
                "padding": "24px 40px",
                "color": "white",
            },
            children=[
                html.H1("Walmart Delivery Analytics", style={"margin": "0", "fontSize": "28px"}),
                html.P(
                    "Análise de qualidade de entregas | 2023 | Região de Orlando, FL",
                    style={"margin": "6px 0 0", "opacity": "0.85", "fontSize": "14px"}
                ),
            ]
        ),

        # Tabs
        html.Div(
            style={"padding": "24px 40px"},
            children=[
                dcc.Tabs(
                    id="tabs",
                    value="tab-executive",
                    style={"marginBottom": "24px"},
                    colors={"primary": COLORS["primary"], "background": "#f0f4f8", "border": "#dee2e6"},
                    children=[
                        dcc.Tab(label="Visão Executiva",        value="tab-executive"),
                        dcc.Tab(label="Análise Operacional",    value="tab-operational"),
                        dcc.Tab(label="Performance Motoristas", value="tab-drivers"),
                        dcc.Tab(label="Drill-down por Região",  value="tab-region"),
                        dcc.Tab(label="Score de Risco",         value="tab-risk"),
                        dcc.Tab(label="Cohort de Motoristas",   value="tab-cohort"),
                        dcc.Tab(label="Retenção de Clientes",   value="tab-retention"),
                    ]
                ),
                html.Div(id="tab-content"),
            ]
        ),

        # Footer
        html.Div(
            style={"textAlign": "center", "padding": "20px", "color": "#999", "fontSize": "12px"},
            children=["Walmart Delivery Analytics Dashboard · Projeto Portfolio Data Science"]
        ),
    ]
)


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):

    # ── TAB 1: EXECUTIVA ──────────────────────────────────────────────────
    if tab == "tab-executive":
        # KPIs
        kpis_row = html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "24px"},
            children=[
                kpi_card("Total de Pedidos",   f"{TOTAL_ORDERS:,}",            "Jan–Dez 2023",    COLORS["primary"]),
                kpi_card("Receita Total",      f"${TOTAL_REVENUE:,.0f}",        "Todas as regiões", COLORS["success"]),
                kpi_card("Ticket Médio",       f"${AVG_TICKET:,.2f}",           "Por pedido",       COLORS["warning"]),
                kpi_card("Taxa de Falha",      f"{MISSING_RATE*100:.1f}%",      "Itens faltando",   COLORS["danger"]),
                kpi_card("Motoristas Ativos",  f"{TOTAL_DRIVERS:,}",            "Cadastrados",      COLORS["neutral"]),
                kpi_card("Regiões Atendidas",  f"{TOTAL_REGIONS}",              "Cidades",          "#8e44ad"),
            ]
        )

        # Trend mensal
        monthly = (
            master.groupby("month")
            .agg(total_orders=("order_id", "count"),
                 total_revenue=("order_amount", "sum"),
                 missing_rate=("has_missing", "mean"))
            .reset_index()
        )
        fig_trend = make_subplots(rows=1, cols=2,
                                   subplot_titles=("Pedidos por Mês", "Receita por Mês ($)"))
        fig_trend.add_trace(
            go.Scatter(x=monthly["month"], y=monthly["total_orders"],
                       mode="lines+markers", name="Pedidos",
                       line=dict(color=COLORS["primary"], width=3)),
            row=1, col=1
        )
        fig_trend.add_trace(
            go.Scatter(x=monthly["month"], y=monthly["total_revenue"],
                       mode="lines+markers", name="Receita",
                       line=dict(color=COLORS["success"], width=3)),
            row=1, col=2
        )
        fig_trend.update_layout(
            height=350, showlegend=False,
            paper_bgcolor="white", plot_bgcolor="white",
            title_text="Evolução Mensal 2023", title_font_size=15
        )
        fig_trend.update_xaxes(tickangle=45)

        # Region revenue bar
        region_rev = (
            master.groupby("region")["order_amount"]
            .sum().sort_values(ascending=True).reset_index()
        )
        fig_reg = px.bar(
            region_rev, x="order_amount", y="region",
            orientation="h", color="order_amount",
            color_continuous_scale=["#c8e6ff", COLORS["primary"]],
            title="Receita Total por Região",
            labels={"order_amount": "Receita ($)", "region": "Região"}
        )
        fig_reg.update_layout(height=340, showlegend=False, coloraxis_showscale=False,
                              paper_bgcolor="white", plot_bgcolor="white")

        # Missing rate over time
        fig_miss = px.line(
            monthly, x="month", y="missing_rate",
            title="Taxa de Falha ao Longo do Ano",
            labels={"missing_rate": "Taxa de Falha", "month": "Mês"},
            markers=True,
        )
        fig_miss.add_hline(y=MISSING_RATE, line_dash="dash", line_color="red",
                           annotation_text=f"Média: {MISSING_RATE*100:.1f}%")
        fig_miss.update_traces(line_color=COLORS["danger"], line_width=3)
        fig_miss.update_layout(height=300, paper_bgcolor="white", plot_bgcolor="white",
                               yaxis_tickformat=".1%")

        return html.Div([
            kpis_row,
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                     children=[
                         html.Div(dcc.Graph(figure=fig_trend), style={"gridColumn": "1 / -1",
                                                                        "backgroundColor": "white", "borderRadius": "8px",
                                                                        "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"}),
                         html.Div(dcc.Graph(figure=fig_reg),   style={"backgroundColor": "white", "borderRadius": "8px",
                                                                        "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"}),
                         html.Div(dcc.Graph(figure=fig_miss),  style={"backgroundColor": "white", "borderRadius": "8px",
                                                                        "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"}),
                     ])
        ])

    # ── TAB 2: OPERACIONAL ────────────────────────────────────────────────
    elif tab == "tab-operational":
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Heatmap volume
        pivot_vol = (
            master.groupby(["day_of_week", "delivery_hour"])["order_id"]
            .count().unstack(fill_value=0).reindex(day_order)
        )
        fig_heat_vol = px.imshow(
            pivot_vol, color_continuous_scale="Blues",
            title="Volume de Entregas: Hora × Dia da Semana",
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Pedidos"),
            aspect="auto"
        )
        fig_heat_vol.update_layout(height=380, paper_bgcolor="white")

        # Heatmap falha
        pivot_fail = (
            master.groupby(["day_of_week", "delivery_hour"])["has_missing"]
            .mean().unstack(fill_value=0).reindex(day_order)
        )
        fig_heat_fail = px.imshow(
            pivot_fail, color_continuous_scale="RdYlGn_r",
            title="Taxa de Falha: Hora × Dia da Semana",
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Taxa"),
            aspect="auto"
        )
        fig_heat_fail.update_layout(height=380, paper_bgcolor="white")

        # Falha por dia + IC
        day_stats = (
            master.groupby("day_of_week")
            .agg(total=("order_id", "count"), missing=("has_missing", "sum"))
            .reindex(day_order).reset_index()
        )
        day_stats["rate"] = day_stats["missing"] / day_stats["total"]
        day_stats["colors"] = ["#d62728" if r > MISSING_RATE else "#2ca02c" for r in day_stats["rate"]]

        fig_day = px.bar(
            day_stats, x="day_of_week", y="rate",
            color="colors", color_discrete_map="identity",
            title="Taxa de Falha por Dia da Semana",
            labels={"rate": "Taxa de Falha", "day_of_week": "Dia"}
        )
        fig_day.add_hline(y=MISSING_RATE, line_dash="dash", line_color="black",
                          annotation_text=f"Média {MISSING_RATE*100:.1f}%")
        fig_day.update_layout(height=320, showlegend=False,
                              paper_bgcolor="white", plot_bgcolor="white",
                              yaxis_tickformat=".1%")

        # Falha por período
        period_stats = (
            master.groupby("period", observed=True)["has_missing"]
            .mean().reset_index()
        )
        fig_period = px.bar(
            period_stats, x="period", y="has_missing",
            color="has_missing", color_continuous_scale=["#2ca02c", "#d62728"],
            title="Taxa de Falha por Período do Dia",
            labels={"has_missing": "Taxa de Falha", "period": "Período"}
        )
        fig_period.add_hline(y=MISSING_RATE, line_dash="dash", line_color="black")
        fig_period.update_layout(height=320, showlegend=False, coloraxis_showscale=False,
                                 paper_bgcolor="white", plot_bgcolor="white",
                                 yaxis_tickformat=".1%")

        def card(fig):
            return html.Div(dcc.Graph(figure=fig),
                            style={"backgroundColor": "white", "borderRadius": "8px",
                                   "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"})

        return html.Div([
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                     children=[
                         html.Div(card(fig_heat_vol), style={"gridColumn": "1 / -1"}),
                         html.Div(card(fig_heat_fail), style={"gridColumn": "1 / -1"}),
                         card(fig_day),
                         card(fig_period),
                     ])
        ])

    # ── TAB 3: MOTORISTAS ─────────────────────────────────────────────────
    elif tab == "tab-drivers":
        driver_perf = (
            master.groupby(["driver_id", "driver_name"])
            .agg(
                deliveries=("order_id", "count"),
                missing_rate=("has_missing", "mean"),
                total_revenue=("order_amount", "sum"),
                avg_ticket=("order_amount", "mean"),
            )
            .reset_index()
        )
        driver_perf = driver_perf[driver_perf["deliveries"] >= 5]

        # Distribuição de taxas
        fig_dist = px.histogram(
            driver_perf, x="missing_rate", nbins=40,
            title="Distribuição da Taxa de Falha entre Motoristas",
            labels={"missing_rate": "Taxa de Falha", "count": "Motoristas"},
            color_discrete_sequence=[COLORS["primary"]]
        )
        fig_dist.add_vline(x=MISSING_RATE, line_dash="dash", line_color="red",
                           annotation_text=f"Média {MISSING_RATE*100:.1f}%")
        fig_dist.update_layout(height=320, paper_bgcolor="white", plot_bgcolor="white",
                               xaxis_tickformat=".0%")

        # Top 15 piores
        worst = driver_perf.nlargest(15, "missing_rate")
        fig_worst = px.bar(
            worst.sort_values("missing_rate"),
            x="missing_rate", y="driver_name",
            orientation="h",
            color="missing_rate", color_continuous_scale=["#ffcccc", "#d62728"],
            title="Top 15 — Motoristas com Maior Taxa de Falha",
            labels={"missing_rate": "Taxa de Falha (%)", "driver_name": ""},
            text=worst.sort_values("missing_rate")["missing_rate"].apply(lambda x: f"{x*100:.1f}%")
        )
        fig_worst.update_layout(height=460, coloraxis_showscale=False,
                                paper_bgcolor="white", plot_bgcolor="white",
                                xaxis_tickformat=".0%")

        # Top 15 melhores
        best = driver_perf[driver_perf["missing_rate"] < 1.0].nsmallest(15, "missing_rate")
        fig_best = px.bar(
            best.sort_values("missing_rate", ascending=False),
            x="missing_rate", y="driver_name",
            orientation="h",
            color="missing_rate", color_continuous_scale=["#2ca02c", "#c8ffcc"],
            title="Top 15 — Motoristas com Menor Taxa de Falha",
            labels={"missing_rate": "Taxa de Falha (%)", "driver_name": ""},
            text=best.sort_values("missing_rate", ascending=False)["missing_rate"].apply(lambda x: f"{x*100:.1f}%")
        )
        fig_best.update_layout(height=460, coloraxis_showscale=False,
                               paper_bgcolor="white", plot_bgcolor="white",
                               xaxis_tickformat=".0%")

        # Scatter: volume x taxa
        fig_scatter = px.scatter(
            driver_perf, x="deliveries", y="missing_rate",
            size="total_revenue", color="missing_rate",
            color_continuous_scale=["#2ca02c", "#ff7f0e", "#d62728"],
            hover_name="driver_name",
            title="Volume de Entregas vs. Taxa de Falha (tamanho = receita)",
            labels={"deliveries": "Total de Entregas", "missing_rate": "Taxa de Falha"}
        )
        fig_scatter.add_hline(y=MISSING_RATE, line_dash="dash", line_color="black",
                              annotation_text="Média")
        fig_scatter.update_layout(height=420, paper_bgcolor="white", plot_bgcolor="white",
                                  yaxis_tickformat=".0%")

        def card(fig):
            return html.Div(dcc.Graph(figure=fig),
                            style={"backgroundColor": "white", "borderRadius": "8px",
                                   "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"})

        return html.Div([
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                     children=[
                         html.Div(card(fig_dist), style={"gridColumn": "1 / -1"}),
                         card(fig_worst),
                         card(fig_best),
                         html.Div(card(fig_scatter), style={"gridColumn": "1 / -1"}),
                     ])
        ])

    # ── TAB 4: DRILL-DOWN POR REGIÃO ──────────────────────────────────────
    elif tab == "tab-region":
        regions = sorted(master["region"].unique())

        return html.Div([
            html.Div(
                style={"backgroundColor": "white", "borderRadius": "8px", "padding": "20px",
                       "boxShadow": "0 2px 6px rgba(0,0,0,0.08)", "marginBottom": "20px"},
                children=[
                    html.Label("Selecionar Região:", style={"fontWeight": "bold", "marginBottom": "8px",
                                                             "display": "block"}),
                    dcc.Dropdown(
                        id="region-dropdown",
                        options=[{"label": r, "value": r} for r in regions],
                        value=regions[0],
                        clearable=False,
                        style={"width": "320px"}
                    ),
                ]
            ),
            html.Div(id="region-detail-content"),
        ])

    # ── TAB 5: SCORE DE RISCO ─────────────────────────────────────────────
    elif tab == "tab-risk":
        def section(title, children):
            return html.Div(
                style={"backgroundColor": "white", "borderRadius": "8px", "padding": "20px",
                       "boxShadow": "0 2px 6px rgba(0,0,0,0.08)", "marginBottom": "20px"},
                children=[html.H4(title, style={"margin": "0 0 16px", "color": "#1a1a2e"})] + children
            )

        model_kpis = html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
            children=[
                kpi_card("AUC do Modelo", f"{MODEL_AUC:.3f}", "Logistic Regression", COLORS["primary"]),
                kpi_card("Amostras de Treino", f"{len(X_train):,}", "Pedidos 2023", COLORS["neutral"]),
                kpi_card("Features", "6", "Região, Dia, Hora, Valor, Itens, Histórico Motorista", COLORS["warning"]),
                kpi_card("Taxa Base de Falha", f"{MISSING_RATE*100:.1f}%", "Baseline para comparação", COLORS["danger"]),
            ]
        )

        form = section("Simular Risco de um Pedido", [
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "16px"},
                children=[
                    html.Div([
                        html.Label("Região", style={"fontWeight": "600", "marginBottom": "4px", "display": "block"}),
                        dcc.Dropdown(id="risk-region",
                            options=[{"label": r, "value": r} for r in REGION_LIST],
                            value=REGION_LIST[0], clearable=False),
                    ]),
                    html.Div([
                        html.Label("Dia da Semana", style={"fontWeight": "600", "marginBottom": "4px", "display": "block"}),
                        dcc.Dropdown(id="risk-day",
                            options=[{"label": d, "value": d} for d in DAY_LIST],
                            value="Monday", clearable=False),
                    ]),
                    html.Div([
                        html.Label("Hora da Entrega (0–23)", style={"fontWeight": "600", "marginBottom": "4px", "display": "block"}),
                        dcc.Slider(id="risk-hour", min=0, max=23, step=1, value=10,
                                   marks={h: str(h) for h in [0, 6, 12, 18, 23]},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ]),
                    html.Div([
                        html.Label("Valor do Pedido ($)", style={"fontWeight": "600", "marginBottom": "4px", "display": "block"}),
                        dcc.Slider(id="risk-amount", min=20, max=600, step=10, value=280,
                                   marks={v: f"${v}" for v in [20, 150, 300, 450, 600]},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ]),
                    html.Div([
                        html.Label("Itens no Pedido", style={"fontWeight": "600", "marginBottom": "4px", "display": "block"}),
                        dcc.Slider(id="risk-items", min=1, max=30, step=1, value=8,
                                   marks={v: str(v) for v in [1, 5, 10, 15, 20, 25, 30]},
                                   tooltip={"placement": "bottom", "always_visible": True}),
                    ]),
                    html.Div([
                        html.Label("Motorista", style={"fontWeight": "600", "marginBottom": "4px", "display": "block"}),
                        dcc.Dropdown(id="risk-driver",
                            options=[{"label": f"{row['driver_name']} ({row['driver_hist_rate']*100:.0f}% hist.)",
                                      "value": row["driver_id"]}
                                     for _, row in DRIVER_LIST.iterrows()],
                            value=DRIVER_LIST["driver_id"].iloc[0], clearable=False,
                            style={"fontSize": "13px"}),
                    ]),
                ]
            )
        ])

        output_area = html.Div(id="risk-output", style={"marginTop": "20px"})

        return html.Div([model_kpis, form, output_area])

    # ── TAB 6: COHORT DE MOTORISTAS ───────────────────────────────────────
    elif tab == "tab-cohort":
        def card(fig):
            return html.Div(dcc.Graph(figure=fig),
                            style={"backgroundColor": "white", "borderRadius": "8px",
                                   "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"})

        # KPI 1 — Failure Rate by Experience Tier
        tier_stats = (
            master.groupby("exp_tier", observed=True)
            .agg(motoristas=("driver_id","nunique"),
                 pedidos=("order_id","count"),
                 falhas=("has_missing","sum"),
                 taxa=("has_missing","mean"))
            .reset_index()
        )
        tier_stats["custo"] = tier_stats["falhas"] * REDELIVERY_COST

        tier_colors = [COLORS["danger"] if r > MISSING_RATE else COLORS["success"]
                       for r in tier_stats["taxa"]]
        fig_tier = go.Figure()
        fig_tier.add_trace(go.Bar(
            x=tier_stats["exp_tier"].astype(str),
            y=tier_stats["taxa"] * 100,
            marker_color=tier_colors,
            text=[f"{v*100:.1f}%" for v in tier_stats["taxa"]],
            textposition="outside",
            name="Taxa de Falha",
        ))
        fig_tier.add_hline(y=MISSING_RATE*100, line_dash="dash", line_color="black",
                           annotation_text=f"Média {MISSING_RATE*100:.1f}%")
        fig_tier.update_layout(
            title="KPI 1 — Taxa de Falha por Nível de Experiência<br>"
                  "<sup>Insight: Experiência não é fator protetor linear — intermediários lideram falhas</sup>",
            yaxis_title="Taxa de Falha (%)", xaxis_title="Nível de Experiência",
            height=380, paper_bgcolor="white", plot_bgcolor="white", showlegend=False
        )

        # KPI 2 — H1 vs H2
        h1 = master[master["date"].dt.month <= 6]
        h2 = master[master["date"].dt.month > 6]

        def driver_rate(df, min_del=5):
            return (df.groupby("driver_id")
                    .agg(deliveries=("order_id","count"), rate=("has_missing","mean"))
                    .query(f"deliveries >= {min_del}"))

        r_h1 = driver_rate(h1).rename(columns={"rate":"rate_h1","deliveries":"del_h1"})
        r_h2 = driver_rate(h2).rename(columns={"rate":"rate_h2","deliveries":"del_h2"})
        both = r_h1.join(r_h2, how="inner").reset_index()
        both["improved"] = both["rate_h2"] < both["rate_h1"]
        pct_imp = both["improved"].mean() * 100

        fig_h1h2 = px.scatter(
            both, x="rate_h1", y="rate_h2",
            color="improved",
            color_discrete_map={True: COLORS["success"], False: COLORS["danger"]},
            labels={"rate_h1": "Taxa H1 (%)", "rate_h2": "Taxa H2 (%)", "improved": "Melhorou"},
            title=f"KPI 2 — Trajetória H1 → H2 por Motorista<br>"
                  f"<sup>Insight: {pct_imp:.0f}% melhoraram — mas {100-pct_imp:.0f}% pioraram sem intervenção</sup>",
            opacity=0.7,
        )
        lim = max(both[["rate_h1","rate_h2"]].max()) * 100 + 5
        fig_h1h2.add_shape(type="line", x0=0, y0=0, x1=lim/100, y1=lim/100,
                           line=dict(dash="dash", color="black", width=1))
        fig_h1h2.update_layout(height=400, paper_bgcolor="white", plot_bgcolor="white")

        # KPI 3 — Consistency Index quadrant counts
        monthly_d = (
            master.groupby(["driver_id","month"])
            .agg(del_=("order_id","count"), rate=("has_missing","mean"))
            .reset_index().query("del_ >= 3")
        )
        cons = (
            monthly_d.groupby("driver_id")
            .agg(months=("month","count"), avg_rate=("rate","mean"), std_rate=("rate","std"))
            .query("months >= 3").reset_index()
        )
        cons["cv"] = (cons["std_rate"] / cons["avg_rate"]).fillna(0)
        rate_med = cons["avg_rate"].median()
        cv_med   = cons["cv"].median()

        def quad(row):
            high_risk = row["avg_rate"] > rate_med
            high_cv   = row["cv"] > cv_med
            if high_risk and not high_cv: return "Crônico (Alto Risco)"
            if high_risk and high_cv:     return "Instável (Coaching)"
            if not high_risk and not high_cv: return "Referência (Baixo Risco)"
            return "Monitorar (Baixo Risco)"

        cons["quadrant"] = cons.apply(quad, axis=1)
        qcounts = cons["quadrant"].value_counts().reset_index()
        qcounts.columns = ["quadrant","count"]
        q_colors = {
            "Crônico (Alto Risco)":    "#c0392b",
            "Instável (Coaching)":      "#e67e22",
            "Referência (Baixo Risco)": "#27ae60",
            "Monitorar (Baixo Risco)":  "#2980b9",
        }
        fig_quad = px.bar(
            qcounts.sort_values("count", ascending=True),
            x="count", y="quadrant", orientation="h",
            color="quadrant",
            color_discrete_map=q_colors,
            title="KPI 3 — Driver Consistency Index: Quadrantes de Intervenção<br>"
                  "<sup>Insight: Motoristas crônicos têm perfil previsível — ação disciplinar tem ROI claro</sup>",
            text="count",
            labels={"count": "Motoristas", "quadrant": ""},
        )
        fig_quad.update_layout(height=350, showlegend=False,
                               paper_bgcolor="white", plot_bgcolor="white")

        # KPI 4 — Financial Cost by Tier
        fig_fin = go.Figure()
        fig_fin.add_trace(go.Bar(
            x=tier_stats["exp_tier"].astype(str),
            y=tier_stats["custo"],
            marker_color=["#e74c3c","#e67e22","#f39c12"],
            text=[f"${v:,.0f}" for v in tier_stats["custo"]],
            textposition="outside",
        ))
        fig_fin.update_layout(
            title="KPI 4 — Custo Estimado de Falhas por Nível de Experiência<br>"
                  "<sup>Insight: Onde concentrar orçamento de treinamento para máximo ROI</sup>",
            yaxis_title="Custo Estimado ($)", xaxis_title="Nível de Experiência",
            height=350, paper_bgcolor="white", plot_bgcolor="white", showlegend=False
        )

        # KPIs no topo
        n_chronic  = qcounts.loc[qcounts["quadrant"]=="Crônico (Alto Risco)","count"].sum()
        n_coaching = qcounts.loc[qcounts["quadrant"]=="Instável (Coaching)","count"].sum()
        total_cost = tier_stats["custo"].sum()

        kpis_cohort = html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
            children=[
                kpi_card("Motoristas Crônicos", f"{n_chronic}",
                         "Alto risco + consistentes", COLORS["danger"]),
                kpi_card("Para Coaching", f"{n_coaching}",
                         "Alto risco + instáveis", COLORS["warning"]),
                kpi_card("Melhoraram H1→H2", f"{pct_imp:.0f}%",
                         "Sem intervenção", COLORS["success"]),
                kpi_card("Custo Total Falhas", f"${total_cost:,.0f}",
                         "Estimativa reentrega", COLORS["neutral"]),
            ]
        )

        return html.Div([
            kpis_cohort,
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                     children=[
                         card(fig_tier),
                         card(fig_h1h2),
                         html.Div(card(fig_quad), style={"gridColumn": "1 / -1"}),
                         html.Div(card(fig_fin),  style={"gridColumn": "1 / -1"}),
                     ])
        ])

    # ── TAB 7: RETENÇÃO DE CLIENTES ───────────────────────────────────────
    elif tab == "tab-retention":
        def card(fig):
            return html.Div(dcc.Graph(figure=fig),
                            style={"backgroundColor": "white", "borderRadius": "8px",
                                   "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"})

        # KPI 1 — Failure Profile
        profile_grp = (
            cust_profile.groupby("failure_group", observed=True)
            .agg(clientes=("customer_id","count"), receita=("total_revenue","sum"))
            .reset_index()
        )
        fig_profile = px.pie(
            profile_grp, names="failure_group", values="clientes",
            color_discrete_sequence=[COLORS["success"],"#f39c12","#e67e22",COLORS["danger"]],
            title="KPI 1 — Customer Failure Profile<br>"
                  "<sup>Insight: Proporção da base que foi impactada por falhas</sup>",
            hole=0.4,
        )
        fig_profile.update_layout(height=380, paper_bgcolor="white")

        # KPI 2 — Return Rate
        failed_orders = master[master["has_missing"]].copy()
        first_fail = (
            failed_orders.groupby("customer_id")["date"]
            .min().reset_index().rename(columns={"date":"first_failure_date"})
        )
        cohort_ret = first_fail.merge(
            master[["customer_id","order_id","date"]], on="customer_id", how="left"
        )
        cohort_ret["is_post"] = cohort_ret["date"] > cohort_ret["first_failure_date"]
        returned_n = cohort_ret[cohort_ret["is_post"]]["customer_id"].nunique()
        total_fail_n = first_fail["customer_id"].nunique()
        return_rate = returned_n / total_fail_n * 100

        no_fail_ids = cust_profile[~cust_profile["had_failure"]]["customer_id"].unique()
        no_fail_repeat = (
            master[master["customer_id"].isin(no_fail_ids)]
            .groupby("customer_id").size().reset_index(name="n")
        )
        nf_return_rate = (no_fail_repeat["n"] > 1).mean() * 100

        fig_return = go.Figure(go.Bar(
            x=["Sem falha", "Com falha"],
            y=[nf_return_rate, return_rate],
            marker_color=[COLORS["success"], COLORS["warning"]],
            text=[f"{nf_return_rate:.1f}%", f"{return_rate:.1f}%"],
            textposition="outside",
        ))
        fig_return.update_layout(
            title="KPI 2 — Return Rate: Com Falha vs. Sem Falha<br>"
                  "<sup>Insight: A falha reduz a taxa de recompra?</sup>",
            yaxis_title="Taxa de Recompra (%)", height=380,
            yaxis_range=[0, 110],
            paper_bgcolor="white", plot_bgcolor="white", showlegend=False
        )

        # KPI 3 — Frequency Comparison
        freq_g = (
            cust_profile.groupby("had_failure")["orders_per_month"]
            .agg(["mean","median"]).reset_index()
        )
        freq_g["had_failure"] = freq_g["had_failure"].map({False:"Sem falha", True:"Com falha"})
        fig_freq = go.Figure()
        fig_freq.add_trace(go.Bar(
            name="Média", x=freq_g["had_failure"], y=freq_g["mean"],
            marker_color=[COLORS["success"], COLORS["danger"]],
            text=[f"{v:.2f}" for v in freq_g["mean"]], textposition="outside",
        ))
        fig_freq.update_layout(
            title="KPI 3 — Frequência de Pedidos por Grupo<br>"
                  "<sup>Insight: Clientes com falha pediem com cadência diferente?</sup>",
            yaxis_title="Pedidos por Mês", height=380,
            paper_bgcolor="white", plot_bgcolor="white", showlegend=False
        )

        # KPI 6 — Churn by Failure Count
        churn_map = set()
        last_fail = (
            failed_orders.groupby("customer_id")["date"]
            .max().reset_index().rename(columns={"date":"last_fail_date"})
        )
        last_ord = (
            master.groupby("customer_id")["date"]
            .max().reset_index().rename(columns={"date":"last_order_date"})
        )
        DATASET_END = master["date"].max()
        churn_df = last_fail.merge(last_ord, on="customer_id")
        churn_df["days_since"] = (DATASET_END - churn_df["last_fail_date"]).dt.days
        churn_df["days_after"] = (churn_df["last_order_date"] - churn_df["last_fail_date"]).dt.days
        churn_df["churned"] = (churn_df["days_since"] >= 90) & (churn_df["days_after"] <= 0)

        cust_churn = cust_profile.merge(
            churn_df[["customer_id","churned"]], on="customer_id", how="left"
        )
        cust_churn["churned"] = cust_churn["churned"].fillna(False)
        cust_churn["fail_cap"] = cust_churn["total_failures"].clip(upper=5).astype(str)
        cust_churn.loc[cust_churn["total_failures"] >= 5, "fail_cap"] = "5+"

        churn_by_fail = (
            cust_churn[cust_churn["total_failures"] > 0]
            .groupby("fail_cap")
            .agg(clientes=("customer_id","count"), churned=("churned","sum"))
            .reset_index()
        )
        churn_by_fail["churn_rate"] = churn_by_fail["churned"] / churn_by_fail["clientes"]

        fig_churn = px.bar(
            churn_by_fail, x="fail_cap", y="churn_rate",
            color="churn_rate",
            color_continuous_scale=["#f9ebea","#e74c3c"],
            text=[f"{v*100:.1f}%" for v in churn_by_fail["churn_rate"]],
            labels={"fail_cap": "Nº de Falhas", "churn_rate": "Taxa de Churn"},
            title="KPI 6 — Churn Rate por Nº de Falhas Sofridas<br>"
                  "<sup>Insight: A cada falha adicional o risco de perda permanente aumenta</sup>",
        )
        fig_churn.update_traces(textposition="outside")
        fig_churn.update_layout(height=380, coloraxis_showscale=False,
                                paper_bgcolor="white", plot_bgcolor="white")

        # KPIs de topo
        n_affected = cust_profile["had_failure"].sum()
        pct_affected = n_affected / len(cust_profile) * 100
        n_churned = churn_df["churned"].sum()
        rev_at_risk = cust_churn[cust_churn["churned"]]["total_revenue"].sum()

        kpis_ret = html.Div(
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
            children=[
                kpi_card("Clientes Impactados", f"{n_affected}",
                         f"{pct_affected:.0f}% da base sofreu falha", COLORS["danger"]),
                kpi_card("Taxa de Retorno", f"{return_rate:.1f}%",
                         "Após primeira falha", COLORS["warning"]),
                kpi_card("Clientes Perdidos", f"{n_churned}",
                         "Churn pós-falha (90 dias)", COLORS["danger"]),
                kpi_card("Receita em Risco", f"${rev_at_risk:,.0f}",
                         "Histórico de clientes perdidos", COLORS["neutral"]),
            ]
        )

        return html.Div([
            kpis_ret,
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                     children=[
                         card(fig_profile),
                         card(fig_return),
                         card(fig_freq),
                         card(fig_churn),
                     ])
        ])

    return html.Div("Selecione uma aba.")


@app.callback(
    Output("risk-output", "children"),
    Input("risk-region", "value"),
    Input("risk-day", "value"),
    Input("risk-hour", "value"),
    Input("risk-amount", "value"),
    Input("risk-items", "value"),
    Input("risk-driver", "value"),
    prevent_initial_call=False,
)
def compute_risk_score(region, day, hour, amount, items, driver_id):
    driver_row = DRIVER_LIST[DRIVER_LIST["driver_id"] == driver_id]
    driver_hist_rate = float(driver_row["driver_hist_rate"].values[0]) if len(driver_row) else MISSING_RATE

    region_enc = le_region.transform([region])[0]
    day_enc    = le_day.transform([day])[0]
    X_new = np.array([[region_enc, day_enc, hour, amount, items, driver_hist_rate]])
    prob  = float(risk_model.predict_proba(X_new)[0][1])

    if prob < 0.10:
        risk_label, risk_color = "Baixo Risco", COLORS["success"]
    elif prob < 0.20:
        risk_label, risk_color = "Médio Risco", COLORS["warning"]
    else:
        risk_label, risk_color = "Alto Risco", COLORS["danger"]

    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=prob * 100,
        delta={"reference": MISSING_RATE * 100, "suffix": "% (baseline)"},
        number={"suffix": "%", "font": {"size": 40}},
        title={"text": f"Score de Risco de Falha<br><b>{risk_label}</b>",
               "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 50], "ticksuffix": "%"},
            "bar": {"color": risk_color},
            "steps": [
                {"range": [0, 10],  "color": "#eafaf1"},
                {"range": [10, 20], "color": "#fef9e7"},
                {"range": [20, 50], "color": "#fdedec"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.75,
                "value": MISSING_RATE * 100,
            },
        }
    ))
    fig_gauge.update_layout(height=300, paper_bgcolor="white")

    # Feature contributions
    coefs = risk_model.coef_[0]
    feat_names = ["Região", "Dia da Semana", "Hora", "Valor do Pedido", "Nº de Itens", "Histórico Motorista"]
    contribs = coefs * X_new[0]
    fig_contrib = go.Figure(go.Bar(
        x=contribs,
        y=feat_names,
        orientation="h",
        marker_color=[COLORS["danger"] if c > 0 else COLORS["success"] for c in contribs],
        text=[f"{c:+.3f}" for c in contribs],
        textposition="outside",
    ))
    fig_contrib.add_vline(x=0, line_color="black", line_width=1)
    fig_contrib.update_layout(
        title="Contribuição de cada Feature para o Score",
        xaxis_title="Contribuição (positivo = aumenta risco)",
        height=300, paper_bgcolor="white", plot_bgcolor="white",
    )

    summary = html.Div(
        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"},
        children=[
            kpi_card("Score de Risco",  f"{prob*100:.1f}%", risk_label, risk_color),
            kpi_card("Baseline Geral",  f"{MISSING_RATE*100:.1f}%", "Taxa histórica", COLORS["neutral"]),
            kpi_card("Delta",           f"{(prob-MISSING_RATE)*100:+.1f} pp",
                     "vs. média global", risk_color),
            kpi_card("Hist. Motorista", f"{driver_hist_rate*100:.1f}%",
                     "Taxa histórica do motorista selecionado", COLORS["warning"]),
        ]
    )

    return html.Div([
        summary,
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                html.Div(dcc.Graph(figure=fig_gauge),
                         style={"backgroundColor": "white", "borderRadius": "8px",
                                "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"}),
                html.Div(dcc.Graph(figure=fig_contrib),
                         style={"backgroundColor": "white", "borderRadius": "8px",
                                "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"}),
            ]
        )
    ])


@app.callback(
    Output("region-detail-content", "children"),
    Input("region-dropdown", "value"),
    prevent_initial_call=False,
)
def update_region_detail(region):
    df = master[master["region"] == region]
    total   = len(df)
    revenue = df["order_amount"].sum()
    rate    = df["has_missing"].mean()
    ticket  = df["order_amount"].mean()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    kpis_row = html.Div(
        style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "20px"},
        children=[
            kpi_card("Pedidos",        f"{total:,}",           region,       COLORS["primary"]),
            kpi_card("Receita",        f"${revenue:,.0f}",      "",           COLORS["success"]),
            kpi_card("Taxa de Falha",  f"{rate*100:.1f}%",
                     "vs. média " + ("acima" if rate > MISSING_RATE else "abaixo"),
                     COLORS["danger"] if rate > MISSING_RATE else COLORS["success"]),
            kpi_card("Ticket Médio",   f"${ticket:,.2f}",       "",           COLORS["warning"]),
        ]
    )

    # Falha por dia
    day_miss = (
        df.groupby("day_of_week")["has_missing"].mean()
        .reindex(day_order).reset_index()
    )
    fig_day = px.bar(
        day_miss, x="day_of_week", y="has_missing",
        color="has_missing", color_continuous_scale=["#2ca02c", "#d62728"],
        title=f"Taxa de Falha por Dia — {region}",
        labels={"has_missing": "Taxa", "day_of_week": "Dia"}
    )
    fig_day.add_hline(y=MISSING_RATE, line_dash="dash", line_color="black",
                      annotation_text=f"Média global {MISSING_RATE*100:.1f}%")
    fig_day.update_layout(height=320, showlegend=False, coloraxis_showscale=False,
                          paper_bgcolor="white", plot_bgcolor="white",
                          yaxis_tickformat=".1%")

    # Top motoristas da região
    driver_reg = (
        df.groupby("driver_name")
        .agg(deliveries=("order_id", "count"), missing_rate=("has_missing", "mean"))
        .reset_index()
        .query("deliveries >= 3")
        .nlargest(10, "missing_rate")
        .sort_values("missing_rate")
    )
    fig_drivers = px.bar(
        driver_reg, x="missing_rate", y="driver_name",
        orientation="h",
        color="missing_rate", color_continuous_scale=["#ffcccc", "#d62728"],
        title=f"Top 10 Motoristas de Maior Risco — {region}",
        labels={"missing_rate": "Taxa de Falha", "driver_name": ""}
    )
    fig_drivers.update_layout(height=380, coloraxis_showscale=False,
                              paper_bgcolor="white", plot_bgcolor="white",
                              xaxis_tickformat=".0%")

    # Heatmap hora da região
    pivot_r = (
        df.groupby(["day_of_week", "delivery_hour"])["has_missing"]
        .mean().unstack(fill_value=0).reindex(day_order)
    )
    fig_heat = px.imshow(
        pivot_r, color_continuous_scale="RdYlGn_r",
        title=f"Taxa de Falha: Hora × Dia — {region}",
        labels=dict(x="Hora", y="Dia", color="Taxa"),
        aspect="auto"
    )
    fig_heat.update_layout(height=360, paper_bgcolor="white")

    def card(fig):
        return html.Div(dcc.Graph(figure=fig),
                        style={"backgroundColor": "white", "borderRadius": "8px",
                               "padding": "16px", "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"})

    return html.Div([
        kpis_row,
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
                 children=[
                     card(fig_day),
                     card(fig_drivers),
                     html.Div(card(fig_heat), style={"gridColumn": "1 / -1"}),
                 ])
    ])


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Walmart Delivery Analytics Dashboard")
    print("  Acesse: http://localhost:8050")
    print("=" * 55)
    app.run(debug=False, port=8050)
