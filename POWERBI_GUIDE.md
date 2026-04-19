# Power BI Dashboard Guide — Walmart Delivery Analytics

## Arquivos gerados em `data/powerbi/`

| Arquivo | Tipo | Uso no Power BI |
|---|---|---|
| `fct_orders.csv` | Fato | Tabela central — conecta tudo |
| `dim_date.csv` | Dimensão | Eixo de tempo, filtros de período |
| `dim_drivers.csv` | Dimensão | Segmento, tier, quadrante |
| `dim_customers.csv` | Dimensão | Segmento, churn, valor |
| `dim_regions.csv` | Dimensão | KPIs regionais |
| `dim_products.csv` | Dimensão | Ranking de produtos |
| `agg_monthly_kpis.csv` | Agregado | Gráfico de tendência |
| `agg_hour_day_heatmap.csv` | Agregado | Heatmap hora × dia |
| `agg_region_day.csv` | Agregado | Falha por região × dia |
| `agg_driver_monthly.csv` | Agregado | Consistency index mensal |
| `agg_financial_impact.csv` | Agregado | Custo por quadrante |
| `agg_top_products.csv` | Agregado | Ranking de produtos |
| `agg_retention_summary.csv` | Agregado | Métricas de retenção |

---

## Passo 1 — Importar os dados

1. Abrir Power BI Desktop
2. **Obter Dados → Texto/CSV**
3. Importar TODOS os arquivos da pasta `data/powerbi/`
4. Em cada tabela: verificar se os tipos de coluna estão corretos
   - Colunas de data → tipo **Data**
   - Colunas de taxa (failure_rate, etc.) → tipo **Número Decimal**
   - Colunas de ID → tipo **Texto**

---

## Passo 2 — Montar o Modelo (Star Schema)

Ir em **Exibição de Modelo** e criar os relacionamentos:

```
fct_orders[date_key]       → dim_date[date_key]         (Muitos:1)
fct_orders[driver_id]      → dim_drivers[driver_id]     (Muitos:1)
fct_orders[customer_id]    → dim_customers[customer_id] (Muitos:1)
fct_orders[region]         → dim_regions[region]        (Muitos:1)
fct_orders[order_id]       → agg_driver_monthly         (via driver_id + month — não criar relacionamento direto)
```

> As tabelas `agg_*` são usadas **diretamente** em visuais específicos,
> sem relacionamento com fct_orders — elas já têm os dados calculados.

---

## Passo 3 — Criar Medidas DAX (colar no Power BI)

```dax
-- KPIs Globais
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

-- Comparações
Failure Rate vs Global =
VAR CurrentRate = [Failure Rate]
VAR GlobalRate  = 0.15
RETURN CurrentRate - GlobalRate

-- Motoristas
High Risk Drivers =
CALCULATE(
    DISTINCTCOUNT(dim_drivers[driver_id]),
    dim_drivers[intervention_quadrant] = "Crônico — Ação Disciplinar"
)

Coaching Needed =
CALCULATE(
    DISTINCTCOUNT(dim_drivers[driver_id]),
    dim_drivers[intervention_quadrant] = "Instável — Coaching"
)

-- Clientes
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

-- Savings projetados (para Plano de Ação)
Projected Savings 30pct =
[Total Failure Cost] * 0.30
```

---

## Passo 4 — Estrutura das Páginas

### PÁGINA 1 — Visão Executiva
**Objetivo:** Dar ao executivo o estado geral da operação em 30 segundos.

| Visual | Tipo | Dados | Configuração |
|---|---|---|---|
| Total de Pedidos | Cartão | Medida: `Total Orders` | Negrito, ícone de pacote |
| Receita Total | Cartão | Medida: `Total Revenue` | Formato: $#,##0 |
| Ticket Médio | Cartão | Medida: `Avg Ticket` | Formato: $#,##0.00 |
| Taxa de Falha | Cartão KPI | Medida: `Failure Rate` | Meta: 10% / Alerta: >15% |
| Custo Total de Falhas | Cartão | Medida: `Total Failure Cost` | Cor vermelha |
| Clientes em Risco | Cartão | Medida: `Churned Customers` | |
| Receita em Risco | Cartão | Medida: `Revenue at Risk` | |
| Tendência Mensal | Gráfico de linhas | `agg_monthly_kpis` — month × total_orders + total_revenue | Eixo duplo |
| Taxa de Falha Mensal | Gráfico de linhas | `agg_monthly_kpis` — month × failure_rate | Linha de referência em 15% |
| Receita por Região | Gráfico de barras | `dim_regions` — region × total_revenue | Ordenar decrescente |

**Filtros de página:** Segmentação por Mês / Semestre / Dia da Semana

---

### PÁGINA 2 — Qualidade de Entrega
**Objetivo:** Mostrar ONDE e QUANDO as falhas acontecem — painel operacional.

| Visual | Tipo | Dados | Configuração |
|---|---|---|---|
| Taxa de Falha por Região | Gráfico de barras | `dim_regions` — region × failure_rate | Linha de referência global 15% / Verde=OK, Vermelho=Ruim |
| Comparação vs Média | Gráfico de colunas clusterizado | `dim_regions` — region × vs_global_avg_pp | Positivo = vermelho, negativo = verde |
| Heatmap Hora × Dia | Matriz | `agg_hour_day_heatmap` — day_of_week × delivery_hour, valor: failure_rate | Formatação condicional por cor (branco→vermelho) |
| Volume por Hora e Dia | Matriz | `agg_hour_day_heatmap` — valor: volume | Escala de azul |
| Falha por Dia da Semana | Gráfico de colunas | `agg_region_day` agrupado — day_of_week × avg failure_rate | Segunda em destaque |
| Falha por Período | Gráfico de rosca | `fct_orders` — period × has_missing_int | Madrugada/Manhã/Tarde/Noite |

**Filtros de página:** Região / Mês / Semestre

---

### PÁGINA 3 — Performance de Motoristas
**Objetivo:** Identificar quem precisa de ação — ranqueamento e segmentação.

| Visual | Tipo | Dados | Configuração |
|---|---|---|---|
| Motoristas Alto Risco | Cartão | Medida: `High Risk Drivers` | Alerta vermelho |
| Motoristas para Coaching | Cartão | Medida: `Coaching Needed` | Alerta laranja |
| Custo por Quadrante | Gráfico de barras | `agg_financial_impact` — quadrant × total_failure_cost | Incluir savings_if_30pct_reduction como linha |
| Distribuição por Quadrante | Gráfico de rosca | `dim_drivers` — intervention_quadrant × count | 4 cores: vermelho / laranja / verde / azul |
| Top 15 Motoristas Críticos | Tabela | `dim_drivers` — filtrar crônico+instável — colunas: driver_name, exp_tier, hist_failure_rate, estimated_failure_cost, intervention_quadrant | Formatação condicional na taxa |
| Distribuição de Taxa de Falha | Histograma | `dim_drivers` — hist_failure_rate | Linha vertical em 15% (média global) |
| Performance H1 vs H2 | Gráfico de dispersão | `dim_drivers` — rate_h1 × rate_h2, legenda: improved_h1_h2 | Linha diagonal (x=y) como referência |
| Motoristas que Melhoraram | Cartão | Contar dim_drivers onde improved_h1_h2 = TRUE | % do total |

**Filtros de página:** Tier de Experiência / Quadrante / Região

---

### PÁGINA 4 — Impacto no Cliente
**Objetivo:** Traduzir falhas operacionais em perda de receita e relacionamento.

| Visual | Tipo | Dados | Configuração |
|---|---|---|---|
| Clientes Impactados | Cartão | Medida: `Customers with Failure` | Com % do total |
| Taxa de Retorno | Cartão | `agg_retention_summary` — Return Rate (%) | Benchmark: >90% = OK |
| Clientes em Churn | Cartão | Medida: `Churned Customers` | Alerta vermelho |
| Revenue at Risk | Cartão | Medida: `Revenue at Risk` | Formato $#,##0 |
| Perfil de Falha | Gráfico de rosca | `dim_customers` — failure_group × count | 4 cores por grupo |
| Segmento de Valor × Falha | Matriz | `dim_customers` — value_segment × failure_group, valor: count | Formatação condicional |
| Churn por Grupo de Falha | Gráfico de colunas | `dim_customers` agrupado — failure_group × avg(churned) | Cor gradiente branco→vermelho |
| Frequência de Compra | Gráfico de colunas clusterizadas | `dim_customers` — had_failure × avg(orders_per_month) | Lado a lado: com falha vs sem falha |
| Clientes Perdidos (Tabela) | Tabela | `dim_customers` filtrado: churned = TRUE — customer_name, failure_group, total_revenue, value_segment | Ordenar por total_revenue desc |

**Filtros de página:** Segmento de Valor / Grupo de Falha / Idade

---

### PÁGINA 5 — Plano de Ação
**Objetivo:** Traduzir toda a análise em recomendações com ROI estimado.

| Visual | Tipo | Dados | Configuração |
|---|---|---|---|
| Custo Total Atual | Cartão grande | Medida: `Total Failure Cost` | Contexto: "por ano" |
| Economia Estimada (30%) | Cartão grande | Medida: `Projected Savings 30pct` | Verde — "se atingir meta" |
| Prioridade por Impacto | Gráfico de barras horizontal | `agg_financial_impact` — quadrant × total_failure_cost + savings | Mostrar delta |
| Tabela de Recomendações | Tabela manual (Enter Data) | 4 ações priorizadas com impacto estimado | Ver abaixo |
| Revenue at Risk vs Custo de Retenção | Gráfico de dispersão ou cartões comparativos | Mostrar que $47,371 em risco vs. custo de compensação | Narrativa visual |

**Tabela de Recomendações (inserir manualmente via Enter Data):**

| Prioridade | Ação | Alvo | Impacto Estimado |
|---|---|---|---|
| 1 | Programa de retreinamento obrigatório | Motoristas Crônico + Instável | -30% no custo de falha |
| 2 | Protocolo reforçado às Segundas-feiras | Todos os motoristas | -2pp na taxa de falha |
| 3 | Auditoria operacional — Altamonte Springs | Gestão regional | -1.5pp na região |
| 4 | Compensação imediata após 1ª falha | Clientes com 1 falha | Recuperar $47k em risco |

---

## Dicas de Design Profissional

### Paleta de cores recomendada
```
Primário (azul):   #1F77B4
Sucesso (verde):   #2CA02C
Alerta (laranja):  #FF7F0E
Perigo (vermelho): #D62728
Neutro (cinza):    #7F7F7F
Fundo das páginas: #F8F9FA
Fundo dos cartões: #FFFFFF
```

### Configurações gerais
- **Tema:** Usar o tema padrão do Power BI ou importar um tema JSON com as cores acima
- **Fonte:** Segoe UI em todo o relatório
- **Cartões KPI:** Usar visual "Cartão" com bordas arredondadas e sombra sutil
- **Linhas de referência:** Sempre adicionar linha pontilhada vermelha na média global (15%) nos gráficos de taxa
- **Formatação condicional:** Usar escala Branco→Vermelho em toda coluna de `failure_rate` ou `failure_cost` nas tabelas
- **Tooltips:** Customizar para mostrar contexto adicional (ex: no gráfico de região, tooltip com nº de pedidos e motoristas)

### Hierarquia de informação por página
```
TÍTULO DA PÁGINA (grande, negrito)
  └── Subtítulo com contexto ("Jan–Dez 2023 | 7 cidades | 10.000 pedidos")
      └── KPI Cards (linha de cartões no topo)
          └── Gráficos principais (2/3 da página)
              └── Tabela de detalhe (1/3 inferior, opcional)
```

---

## Ordem de criação recomendada

1. Criar modelo e relacionamentos
2. Criar todas as medidas DAX
3. Montar Página 1 (Executiva) — referência visual para as demais
4. Montar Página 5 (Plano de Ação) — âncora narrativa
5. Montar Páginas 2, 3, 4

> Comece pelo final (Plano de Ação) para ter clareza de qual história
> cada página anterior precisa contar.
