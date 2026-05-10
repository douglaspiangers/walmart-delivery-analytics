# Prompt para Lovable — Walmart Delivery Analytics Dashboard

---

## INSTRUÇÕES PARA O LOVABLE

Crie um dashboard analítico completo em React para o projeto **Walmart Delivery Analytics**.
O dashboard deve contar uma história de dados — começando pelo problema de negócio, passando pela análise,
chegando à causa raiz e terminando com o plano de ação.

---

## IDENTIDADE VISUAL

### Paleta de cores (use EXATAMENTE estas)

```
Background geral:     #F4F6F8   (cinza muito claro — fundo das páginas)
Background cards:     #FFFFFF   (branco)
Texto principal:      #1C2B3A   (azul escuro quase preto)
Texto secundário:     #5A6A7A   (cinza azulado)
Borda dos cards:      #E2E8F0   (cinza claro)

Cor primária:         #2C5F8A   (azul executivo — headers, links, ícones)
Cor de sucesso:       #2D7D4F   (verde escuro — indicadores positivos)
Cor de alerta:        #B45309   (âmbar escuro — atenção moderada)
Cor crítica:          #991B1B   (vermelho escuro — alertas críticos)
Cor neutra:           #4A5568   (cinza — informações neutras)

Gradiente do header:  linear-gradient(135deg, #1C3A5A 0%, #2C5F8A 100%)
```

### Tipografia
- Fonte: **Inter** (Google Fonts)
- Título da página: 22px, weight 700, cor #1C2B3A
- Subtítulo de seção: 15px, weight 600, cor #2C5F8A
- Valor de KPI: 32px, weight 700
- Label de KPI: 13px, weight 500, cor #5A6A7A
- Legenda de gráfico: 12px, weight 400, cor #5A6A7A
- Corpo de texto: 14px, weight 400, cor #1C2B3A
- **Nunca use fonte abaixo de 12px**

### Cards e layout
- Border-radius: 10px nos cards
- Box-shadow: `0 2px 8px rgba(0,0,0,0.07)`
- Padding interno dos cards: 24px
- Gap entre cards: 16px
- Borda top colorida nos KPI cards (4px) indicando a categoria

---

## ESTRUTURA DO DASHBOARD

O dashboard tem **5 páginas** acessíveis por um menu lateral fixo à esquerda.
O menu lateral tem fundo #1C3A5A, ícones brancos e texto branco.
A página ativa é destacada com fundo #2C5F8A.

### Menu lateral (sidebar)
```
[Logo / Título]
  Walmart Delivery Analytics

[Navegação]
  📊  Visão Executiva          → /executive
  🚚  Qualidade de Entregas    → /quality
  👤  Performance de Motoristas → /drivers
  🧑  Impacto no Cliente       → /customers
  🎯  Plano de Ação            → /action-plan
```

### Header de cada página
- Fundo: gradiente #1C3A5A → #2C5F8A
- Título da página em branco, 22px
- Subtítulo: "Análise de Qualidade de Entregas | Jan–Dez 2023 | 7 cidades da região de Orlando, FL"
- Padding: 28px 40px

---

## PÁGINA 1 — VISÃO EXECUTIVA

### Narrativa (exibir como texto introdutório no topo, em card cinza claro)
> "Em 2023, a operação processou **10.000 pedidos** gerando **$2,83M em receita**.
> Porém, **15% das entregas** chegaram com pelo menos um item faltando —
> criando insatisfação, custos de reentrega e receita em risco.
> Esta análise identifica as causas e aponta onde intervir primeiro."

### Linha de KPI Cards (6 cards em grid 3×2 ou 6×1)

| Card | Valor | Legenda | Cor da borda top |
|---|---|---|---|
| Total de Pedidos | 10.000 | Jan–Dez 2023 | #2C5F8A |
| Receita Total | $2.833.022 | Todas as regiões | #2D7D4F |
| Ticket Médio | $283,30 | Por pedido | #B45309 |
| Taxa de Falha | 15,0% | Itens faltando por entrega | #991B1B |
| Custo de Falhas | $106.380 | Estimativa de reentrega | #991B1B |
| Clientes em Risco | 26 | Churn pós-falha | #B45309 |

> **Legenda abaixo dos cards críticos** (Taxa de Falha e Custo de Falhas):
> "Taxa crítica: indica que 1 em cada 7 entregas gerou um problema operacional.
> O custo de reentrega representa 3,75% da receita total anual."

### Gráfico 1 — Tendência Mensal (gráfico de linhas duplo, largura total)
- Título: "Evolução Mensal de Pedidos e Receita — 2023"
- Legenda: "Mostra o volume de operações e a receita gerada mês a mês.
  Pedidos e receita seguem padrão estável, sem sazonalidade extrema —
  o problema de falhas não é sazonal, é estrutural."
- Eixo Y esquerdo: Nº de Pedidos (linha azul #2C5F8A)
- Eixo Y direito: Receita $ (linha verde #2D7D4F)
- Dados mensais:

```
Jan: 841 pedidos / $238.230
Fev: 759 pedidos / $214.902
Mar: 840 pedidos / $238.193
Abr: 814 pedidos / $230.494
Mai: 837 pedidos / $237.210
Jun: 789 pedidos / $223.501
Jul: 849 pedidos / $240.443
Ago: 838 pedidos / $237.406
Set: 823 pedidos / $233.076
Out: 841 pedidos / $238.243
Nov: 833 pedidos / $235.952
Dez: 836 pedidos / $236.907
```

### Gráfico 2 — Taxa de Falha Mensal (gráfico de área, largura total)
- Título: "Taxa de Falha ao Longo do Ano"
- Legenda: "A taxa de falha permanece consistente próxima aos 15% durante todo o ano —
  confirmando que o problema é operacional e crônico, não pontual ou sazonal.
  Linha tracejada vermelha indica a média global de 15,0%."
- Linha de referência tracejada em 15,0% com label "Média global: 15,0%"
- Área preenchida em vermelho muito transparente (#991B1B com opacity 0.08)
- Linha em #991B1B

### Gráfico 3 — Receita por Região (barras horizontais)
- Título: "Receita Total por Região"
- Legenda: "Distribuição de receita entre as 7 cidades atendidas.
  O volume de receita por região indica onde concentrar esforços operacionais."
- Barras em #2C5F8A, ordenadas maior para menor
- Dados:
```
Orlando:           $463.523
Winter Park:       $430.695
Altamonte Springs: $430.441
Kissimmee:         $407.289
Apopka:            $373.067
Sanford:           $368.026
Clermont:          $359.981
```

---

## PÁGINA 2 — QUALIDADE DE ENTREGAS

### Narrativa (card introdutório)
> "Com 15% de taxa global de falha, a análise busca identificar
> **onde** e **quando** os erros acontecem com mais frequência.
> Padrões geográficos e temporais revelam pontos críticos operacionais
> que podem ser corrigidos com intervenções específicas."

### Gráfico 1 — Taxa de Falha por Região (barras verticais com linha de referência)
- Título: "Taxa de Itens Faltando por Região"
- Legenda: "Altamonte Springs lidera com 16,2% — 2,3pp acima da média global.
  Sanford é a referência positiva com apenas 13,9%.
  Regiões em vermelho estão acima da média e requerem auditoria."
- Linha tracejada preta em 15,0% com label "Média global: 15,0%"
- Barras: vermelho #991B1B se acima da média, verde #2D7D4F se abaixo
- Dados:
```
Altamonte Springs: 16,2%  ← CRÍTICO
Clermont:          15,8%  ← CRÍTICO
Apopka:            15,3%  ← CRÍTICO
Orlando:           15,1%  ← CRÍTICO
Winter Park:       14,5%  ← OK
Kissimmee:         14,4%  ← OK
Sanford:           13,9%  ← MELHOR
```
- Badge "REFERÊNCIA" verde em Sanford
- Badge "AUDITORIA NECESSÁRIA" vermelho em Altamonte Springs

### Gráfico 2 — Taxa de Falha por Dia da Semana (barras)
- Título: "Falhas por Dia da Semana"
- Legenda: "Segunda-feira concentra a maior taxa de falha (16,1%) —
  padrão consistente que sugere dificuldade operacional no início da semana,
  possivelmente relacionada a escala de equipe pós-final de semana."
- Segunda-feira: barra vermelha com badge "PIOR DIA"
- Demais dias: cinza azulado #4A5568 se abaixo da média, salmão claro se acima
- Linha de referência em 15,0%
- Dados:
```
Monday:    16,1%  ← CRÍTICO
Tuesday:   15,0%
Wednesday: 14,9%
Thursday:  14,8%
Friday:    14,8%
Saturday:  14,8%
Sunday:    15,0%
```

### Gráfico 3 — Falha por Período do Dia (barras ou donut)
- Título: "Distribuição de Falhas por Período"
- Legenda: "Entregas da madrugada têm a maior taxa de erro,
  porém representam volume pequeno. O período da tarde concentra
  o maior volume com taxa acima da média — maior impacto absoluto."
- Dados:
```
Madrugada (0-5h):  alta taxa, baixo volume
Manhã (6-11h):     taxa próxima da média
Tarde (12-17h):    maior volume, taxa acima da média
Noite (18-23h):    taxa próxima da média
```

### Seção de Insight (card destacado com borda esquerda vermelha)
```
INSIGHT PRINCIPAL — PADRÃO OPERACIONAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A taxa de falha não varia aleatoriamente.
Existe um padrão claro: início da semana e período da tarde são
as janelas de maior risco. Altamonte Springs repete falhas acima
da média em todos os dias da semana — indicando problema estrutural
de processo, não apenas de volume.

Ação recomendada: auditoria presencial em Altamonte Springs
e reforço de equipe às segundas-feiras.
```

---

## PÁGINA 3 — PERFORMANCE DE MOTORISTAS

### Narrativa (card introdutório)
> "O fator individual de maior impacto nas falhas é o motorista.
> Análise de SHAP (técnica de explicabilidade de modelos de machine learning)
> mostra que **75,8% do poder preditivo de falha** está no histórico do entregador —
> **22 vezes mais** do que o perfil do cliente (3,5%).
> O problema não está em quem pede — está em quem entrega."

### Destaque visual — Decomposição de Causas (gráfico de barras horizontais com cores)
- Título: "O que Explica as Falhas? — Análise SHAP"
- Legenda: "Modelo de machine learning (Random Forest, AUC 0,83) identifica
  a contribuição de cada fator para a probabilidade de falha.
  SHAP mede o impacto médio de cada variável em cada pedido individual."
- Barras coloridas por categoria:
```
Motorista   75,8%  → cor #991B1B (crítico — barra longa)
Pedido      13,4%  → cor #B45309 (alerta)
Tempo        5,0%  → cor #2C5F8A (neutro)
Cliente      3,5%  → cor #2D7D4F (ok — barra curta)
Localização  2,3%  → cor #2D7D4F (ok)
```
- Annotation ao lado: "Motorista = 22x mais impacto que o cliente"

### Linha de KPI Cards (4 cards)
| Card | Valor | Legenda | Cor |
|---|---|---|---|
| Motoristas Ativos | 1.247 | Cadastrados na operação | #2C5F8A |
| Pior Taxa Individual | 36,4% | Motorista de maior risco | #991B1B |
| Melhor Taxa Individual | 0,0% | Motorista de referência | #2D7D4F |
| Custo Total de Falhas | $106.380 | Estimativa anual de reentrega | #991B1B |

### Gráfico 1 — Falha por Nível de Experiência (barras com linha de referência)
- Título: "Taxa de Falha por Nível de Experiência do Motorista"
- Legenda: "Experiência acumulada (número de viagens) não reduz falhas de forma linear.
  Motoristas intermediários apresentam a maior taxa — sugerindo que
  o treinamento inicial é insuficiente e não há reforço contínuo.
  A experiência sozinha não protege."
- Dados:
```
Novato (<=25 trips):       14,3%  → verde (abaixo da média)
Intermediário (26-50):     15,9%  → vermelho (acima — PIOR)
Experiente (51+ trips):    14,6%  → cinza (próximo da média)
```
- Linha de referência em 15,0%

### Tabela — Top 10 Motoristas de Maior Risco
- Título: "Motoristas que Requerem Intervenção Imediata"
- Legenda: "Motoristas com taxa de falha acima de 20% e volume mínimo de
  5 entregas. São os candidatos prioritários para o programa de retreinamento.
  Cada linha vermelha representa um custo evitável para a operação."
- Colunas: Nome | Nível de Experiência | Taxa de Falha | Nº de Entregas
- Formatação: taxa > 25% em vermelho bold, 20-25% em âmbar

### Gráfico 2 — Trajetória H1 vs H2 (scatter plot)
- Título: "Evolução de Performance: 1º Semestre vs. 2º Semestre"
- Legenda: "Cada ponto é um motorista. Pontos abaixo da diagonal melhoraram
  no 2º semestre; acima, pioraram. Sem intervenção formal, apenas
  49,7% dos motoristas melhoraram — e 50,3% pioraram ou estagnaram.
  A autocorreção não é suficiente."
- Pontos verdes: melhoraram
- Pontos vermelhos: pioraram
- Linha diagonal tracejada: "sem mudança"
- Annotation: "50% melhoraram espontaneamente | 50% precisam de intervenção"

---

## PÁGINA 4 — IMPACTO NO CLIENTE

### Narrativa (card introdutório)
> "O cliente não causa as falhas — ele as sofre.
> 71% da base de clientes experimentou ao menos um item faltando em 2023.
> A boa notícia: 92,2% retornam após a falha.
> A má notícia: os 7,8% que não voltam representam **$47.371 em receita perdida**.
> O custo do churn supera em várias vezes o custo de reentrega."

### Linha de KPI Cards (4 cards)
| Card | Valor | Legenda | Cor |
|---|---|---|---|
| Clientes Impactados | 881 | 71,1% da base sofreu falha | #B45309 |
| Taxa de Retorno | 92,2% | Após a primeira falha | #2D7D4F |
| Clientes Perdidos | 26 | Churn pós-falha (90 dias) | #991B1B |
| Receita em Risco | $47.371 | Histórico dos clientes perdidos | #991B1B |

### Gráfico 1 — Perfil de Falha da Base (donut chart)
- Título: "Distribuição da Base por Experiência de Falha"
- Legenda: "Apenas 28,9% dos clientes nunca tiveram um problema.
  A maioria da base foi impactada — o problema é sistêmico,
  não uma exceção isolada. Isso torna a qualidade de entrega
  uma prioridade estratégica, não apenas operacional."
- Dados:
```
0 falhas:     358 clientes (28,9%)  → verde #2D7D4F
1 falha:      aprox. 400 clientes   → âmbar #B45309
2 falhas:     aprox. 280 clientes   → laranja
3+ falhas:    aprox. 200 clientes   → vermelho #991B1B
```

### Gráfico 2 — Taxa de Churn por Número de Falhas (barras crescentes)
- Título: "Risco de Perda por Número de Falhas Sofridas"
- Legenda: "A cada falha adicional, a probabilidade de perder o cliente
  aumenta. A intervenção deve acontecer na PRIMEIRA falha —
  não na terceira, quando o cliente já decidiu ir embora."
- Barras com gradiente branco → vermelho conforme aumenta o número de falhas
- Annotation: "Intervir na 1ª falha custa menos do que recuperar na 3ª"

### Gráfico 3 — Return Rate: Com Falha vs Sem Falha (barras comparativas)
- Título: "Taxa de Recompra: Clientes com e sem Falha"
- Legenda: "Clientes que nunca tiveram falha têm taxa de recompra
  naturalmente alta. A falha reduz essa taxa — mas 92,2% dos
  impactados ainda retornam, mostrando resiliência da base.
  O foco deve ser o grupo minoritário que não volta."
- Duas barras lado a lado: "Sem falha" (verde) e "Com falha" (âmbar)

### Card de Insight (borda esquerda âmbar)
```
CUSTO REAL DO PROBLEMA
━━━━━━━━━━━━━━━━━━━━━━
Custo direto (reentrega):        $106.380/ano
Receita perdida (churn):          $47.371/ano
─────────────────────────────────────────────
Custo total estimado:            $153.751/ano

Custo de compensação proativa:   ~$5.000/ano
(desconto de 20% após 1ª falha para os 26 clientes perdidos)

ROI da intervenção: 9x
```

---

## PÁGINA 5 — PLANO DE AÇÃO

### Narrativa (card introdutório)
> "Duas análises independentes confirmam a mesma conclusão:
> **o problema está nos motoristas, não nos clientes**.
> SHAP: 75,8% vs 3,5% de poder explicativo.
> Variância: motoristas variam de 0% a 36,4%; clientes apresentam taxa de falha praticamente uniforme.
> As ações abaixo são priorizadas por impacto financeiro esperado."

### Seção — Veredicto (card grande, borda vermelha, destaque visual)
```
╔══════════════════════════════════════════════════════════╗
║  CAUSA RAIZ IDENTIFICADA                                 ║
║                                                          ║
║  O problema de itens faltantes é primariamente           ║
║  um problema OPERACIONAL DE MOTORISTAS.                  ║
║                                                          ║
║  Motorista:    75,8% do poder explicativo                ║
║  Pedido:       13,4%                                     ║
║  Tempo:         5,0%                                     ║
║  Cliente:       3,5%  ← NÃO é a causa                   ║
║  Localização:   2,3%                                     ║
╚══════════════════════════════════════════════════════════╝
```

### Tabela de Plano de Ação (5 linhas, ordenadas por prioridade)

Estilo: tabela limpa com zebra striping (linhas alternadas #F8FAFC e #FFFFFF).
Colunas: Prioridade | Ação | Alvo | Impacto Esperado | Economia Estimada

| Pri | Ação | Alvo | Impacto | Economia |
|---|---|---|---|---|
| 🔴 1 | Retreinamento obrigatório — motoristas com taxa > 20% | Motoristas crônicos e instáveis | -30% no custo de falha | $31.914/ano |
| 🟠 2 | Checklist digital para pedidos > 12 itens ou > $400 | Pedidos de alto risco | -2pp na taxa de falha | $13.829/ano |
| 🟡 3 | Reforço operacional às Segundas-feiras | Equipe operacional semanal | Redução da pior janela | $5.319/ano |
| 🔵 4 | Auditoria em Altamonte Springs | Gestão regional | Alinhamento à Sanford | $4.255/ano |
| 🟢 5 | Compensação imediata após 1ª falha do cliente | 26 clientes em churn | Recuperar $47.371 em receita | $47.371 |

> **Legenda:** Economia estimada com base em custo de reentrega de $70,83 por falha
> e redução projetada de 30% pela ação prioritária 1.

### Gráfico — ROI por Ação (barras horizontais)
- Título: "Economia Projetada por Iniciativa ($/ano)"
- Legenda: "As barras representam o valor financeiro de cada ação se executada com sucesso.
  A ação 1 (retreinamento) tem o maior retorno absoluto.
  Combinadas, as 5 ações podem gerar economia total de $102.688/ano —
  o equivalente a 96% do custo atual de falhas."
- Barra 1 (maior): cor #991B1B
- Barras 2-4: cor #B45309 com transparência gradual
- Barra 5: cor #2D7D4F

### Card Final — Resumo Executivo
```
RESUMO DO PROJETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10.000 pedidos analisados | $2,83M em receita | 7 cidades

Problema identificado:    15,0% de taxa de falha
Causa principal:          Motoristas (75,8% do fator explicativo)
Custo atual:              $106.380/ano em reentregas
Receita em risco:         $47.371 (churn pós-falha)

Economia potencial:       $102.688/ano com 5 ações
ROI do programa:          96% de redução no custo de falhas
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Análise realizada com: Python, Pandas, Scikit-learn, SHAP
Metodologia: EDA + Estatística inferencial + Machine Learning + Segmentação
```

---

## NOTAS TÉCNICAS PARA O LOVABLE

1. **Todos os dados são estáticos** — use os valores exatos informados acima. Não gere dados aleatórios.

2. **Recharts** para os gráficos (biblioteca padrão no Lovable).

3. **Responsividade**: o dashboard deve funcionar em telas >= 1280px. Menu lateral colapsa em telas menores.

4. **Tooltips**: todos os gráficos devem ter tooltip ao passar o mouse mostrando o valor exato.

5. **Cards de insight**: use uma borda esquerda colorida (4px) para diferenciar cards de narrativa dos cards de KPI.
   - Borda vermelha: insight crítico
   - Borda âmbar: atenção
   - Borda azul: informativo

6. **Legendas**: cada gráfico deve ter uma legenda em texto abaixo do título, em fonte 13px, cor #5A6A7A,
   explicando o que o gráfico mostra e o que o usuário deve concluir ao olhar para ele.

7. **Animações**: suaves ao carregar cada página (fade-in 300ms). Sem animações excessivas.

8. **Footer**: em todas as páginas, rodapé discreto:
   "Walmart Delivery Analytics · Análise 2023 · Douglas Piangers · Data Science Portfolio"

9. **Favicon / título da aba**: "Walmart Delivery Analytics — Dashboard"
