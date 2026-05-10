# Prompt para Lovable — Walmart Delivery Analytics Dashboard

---

## INSTRUCTIONS FOR LOVABLE

Create a complete analytical dashboard in React for the **Walmart Delivery Analytics** project.
The dashboard should tell a data story — starting with the business problem, going through the analysis,
reaching the root cause, and ending with the action plan.

---

## VISUAL IDENTITY

### Color palette (use EXACTLY these)

```
General background:   #F4F6F8   (very light gray — page background)
Card background:      #FFFFFF   (white)
Primary text:         #1C2B3A   (dark blue, almost black)
Secondary text:       #5A6A7A   (blue-gray)
Card border:          #E2E8F0   (light gray)

Primary color:        #2C5F8A   (executive blue — headers, links, icons)
Success color:        #2D7D4F   (dark green — positive indicators)
Alert color:          #B45309   (dark amber — moderate attention)
Critical color:       #991B1B   (dark red — critical alerts)
Neutral color:        #4A5568   (gray — neutral information)

Header gradient:      linear-gradient(135deg, #1C3A5A 0%, #2C5F8A 100%)
```

### Typography
- Font: **Inter** (Google Fonts)
- Page title: 22px, weight 700, color #1C2B3A
- Section subtitle: 15px, weight 600, color #2C5F8A
- KPI value: 32px, weight 700
- KPI label: 13px, weight 500, color #5A6A7A
- Chart legend: 12px, weight 400, color #5A6A7A
- Body text: 14px, weight 400, color #1C2B3A
- **Never use font below 12px**

### Cards and layout
- Border-radius: 10px on cards
- Box-shadow: `0 2px 8px rgba(0,0,0,0.07)`
- Card inner padding: 24px
- Gap between cards: 16px
- Colored top border on KPI cards (4px) indicating the category

---

## DASHBOARD STRUCTURE

The dashboard has **5 pages** accessible via a fixed left sidebar.
The sidebar has a #1C3A5A background, white icons and white text.
The active page is highlighted with a #2C5F8A background.

### Sidebar menu
```
[Logo / Title]
  Walmart Delivery Analytics

[Navigation]
  📊  Executive Overview        → /executive
  🚚  Delivery Quality          → /quality
  👤  Driver Performance        → /drivers
  🧑  Customer Impact           → /customers
  🎯  Action Plan               → /action-plan
```

### Each page header
- Background: gradient #1C3A5A → #2C5F8A
- Page title in white, 22px
- Subtitle: "Delivery Quality Analysis | Jan–Dec 2023 | 7 cities in the Orlando, FL region"
- Padding: 28px 40px

---

## PAGE 1 — EXECUTIVE OVERVIEW

### Narrative (display as introductory text at the top, in a light gray card)
> "In 2023, operations processed **10,000 orders** generating **$2.83M in revenue**.
> However, **15% of deliveries** arrived with at least one item missing —
> creating dissatisfaction, redelivery costs, and revenue at risk.
> This analysis identifies the causes and points to where to intervene first."

### KPI Card Row (6 cards in a 3×2 or 6×1 grid)

| Card | Value | Label | Top border color |
|---|---|---|---|
| Total Orders | 10,000 | Jan–Dec 2023 | #2C5F8A |
| Total Revenue | $2,833,022 | All regions | #2D7D4F |
| Average Ticket | $283.30 | Per order | #B45309 |
| Failure Rate | 15.0% | Missing items per delivery | #991B1B |
| Failure Cost | $106,380 | Redelivery estimate | #991B1B |
| Customers at Risk | 26 | Post-failure churn | #B45309 |

> **Caption below the critical cards** (Failure Rate and Failure Cost):
> "Critical rate: indicates that 1 in every 7 deliveries generated an operational issue.
> The redelivery cost represents 3.75% of total annual revenue."

### Chart 1 — Monthly Trend (dual-line chart, full width)
- Title: "Monthly Orders and Revenue Trend — 2023"
- Legend: "Shows the volume of operations and revenue generated month by month.
  Orders and revenue follow a stable pattern with no extreme seasonality —
  the failure problem is not seasonal, it is structural."
- Left Y-axis: No. of Orders (blue line #2C5F8A)
- Right Y-axis: Revenue $ (green line #2D7D4F)
- Monthly data:

```
Jan: 841 orders / $238,230
Feb: 759 orders / $214,902
Mar: 840 orders / $238,193
Apr: 814 orders / $230,494
May: 837 orders / $237,210
Jun: 789 orders / $223,501
Jul: 849 orders / $240,443
Aug: 838 orders / $237,406
Sep: 823 orders / $233,076
Oct: 841 orders / $238,243
Nov: 833 orders / $235,952
Dec: 836 orders / $236,907
```

### Chart 2 — Monthly Failure Rate (area chart, full width)
- Title: "Failure Rate Throughout the Year"
- Legend: "The failure rate remains consistently close to 15% throughout the year —
  confirming that the problem is operational and chronic, not isolated or seasonal.
  Red dashed line indicates the global average of 15.0%."
- Dashed reference line at 15.0% with label "Global average: 15.0%"
- Area filled in very transparent red (#991B1B with opacity 0.08)
- Line in #991B1B

### Chart 3 — Revenue by Region (horizontal bars)
- Title: "Total Revenue by Region"
- Legend: "Revenue distribution across the 7 cities served.
  Revenue volume by region indicates where to focus operational efforts."
- Bars in #2C5F8A, sorted largest to smallest
- Data:
```
Orlando:           $463,523
Winter Park:       $430,695
Altamonte Springs: $430,441
Kissimmee:         $407,289
Apopka:            $373,067
Sanford:           $368,026
Clermont:          $359,981
```

---

## PAGE 2 — DELIVERY QUALITY

### Narrative (introductory card)
> "With a 15% global failure rate, the analysis seeks to identify
> **where** and **when** errors occur most frequently.
> Geographic and temporal patterns reveal critical operational hotspots
> that can be corrected with targeted interventions."

### Chart 1 — Failure Rate by Region (vertical bars with reference line)
- Title: "Missing Items Rate by Region"
- Legend: "Altamonte Springs leads with 16.2% — 2.3pp above the global average.
  Sanford is the positive benchmark with only 13.9%.
  Regions in red are above average and require an audit."
- Black dashed line at 15.0% with label "Global average: 15.0%"
- Bars: red #991B1B if above average, green #2D7D4F if below
- Data:
```
Altamonte Springs: 16.2%  ← CRITICAL
Clermont:          15.8%  ← CRITICAL
Apopka:            15.3%  ← CRITICAL
Orlando:           15.1%  ← CRITICAL
Winter Park:       14.5%  ← OK
Kissimmee:         14.4%  ← OK
Sanford:           13.9%  ← BEST
```
- Green "REFERENCE" badge on Sanford
- Red "AUDIT REQUIRED" badge on Altamonte Springs

### Chart 2 — Failure Rate by Day of Week (bars)
- Title: "Failures by Day of Week"
- Legend: "Monday concentrates the highest failure rate (16.1%) —
  a consistent pattern suggesting operational difficulty at the start of the week,
  possibly related to team scheduling after the weekend."
- Monday: red bar with "WORST DAY" badge
- Other days: blue-gray #4A5568 if below average, light salmon if above
- Reference line at 15.0%
- Data:
```
Monday:    16.1%  ← CRITICAL
Tuesday:   15.0%
Wednesday: 14.9%
Thursday:  14.8%
Friday:    14.8%
Saturday:  14.8%
Sunday:    15.0%
```

### Chart 3 — Failure by Time of Day (bars or donut)
- Title: "Failure Distribution by Time Period"
- Legend: "Overnight deliveries have the highest error rate,
  but represent a small volume. The afternoon period concentrates
  the highest volume with an above-average rate — greatest absolute impact."
- Data:
```
Overnight (0-5h):   high rate, low volume
Morning (6-11h):    rate close to average
Afternoon (12-17h): highest volume, rate above average
Evening (18-23h):   rate close to average
```

### Insight Section (highlighted card with left red border)
```
KEY INSIGHT — OPERATIONAL PATTERN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The failure rate does not vary randomly.
There is a clear pattern: the start of the week and the afternoon period
are the highest-risk windows. Altamonte Springs consistently shows above-average
failures on every day of the week — indicating a structural process problem,
not just a volume issue.

Recommended action: on-site audit in Altamonte Springs
and staffing reinforcement on Mondays.
```

---

## PAGE 3 — DRIVER PERFORMANCE

### Narrative (introductory card)
> "The single factor with the greatest impact on failures is the driver.
> SHAP analysis (a machine learning explainability technique)
> shows that **66.8% of the failure predictive power** lies in the driver's history —
> **19 times more** than the customer profile (3.4%).
> The problem is not who orders — it is who delivers."

### Visual highlight — Root Cause Breakdown (horizontal bar chart with colors)
- Title: "What Explains the Failures? — SHAP Analysis"
- Legend: "Machine learning model (Random Forest, AUC 0.80) identifies
  each factor's contribution to the probability of failure.
  SHAP measures the average impact of each variable on each individual order."
- Bars colored by category:
```
Driver      66.8%  → color #991B1B (critical — long bar)
Order       13.4%  → color #B45309 (alert)
Time         5.0%  → color #2C5F8A (neutral)
Customer     3.4%  → color #2D7D4F (ok — short bar)
Location     2.3%  → color #2D7D4F (ok)
```
- Annotation next to it: "Driver = 19x more impact than the customer"

### KPI Card Row (4 cards)
| Card | Value | Label | Color |
|---|---|---|---|
| Active Drivers | 1,247 | Registered in the operation | #2C5F8A |
| Worst Individual Rate | 36.4% | Highest-risk driver | #991B1B |
| Best Individual Rate | 0.0% | Reference driver | #2D7D4F |
| Total Failure Cost | $106,380 | Annual redelivery estimate | #991B1B |

### Chart 1 — Failure by Experience Level (bars with reference line)
- Title: "Failure Rate by Driver Experience Level"
- Legend: "Accumulated experience (number of trips) does not reduce failures linearly.
  Intermediate drivers show the highest rate — suggesting that
  initial training is insufficient and there is no ongoing reinforcement.
  Experience alone is not protective."
- Data:
```
Rookie (<=25 trips):        14.3%  → green (below average)
Intermediate (26-50):       15.9%  → red (above — WORST)
Experienced (51+ trips):    14.6%  → gray (close to average)
```
- Reference line at 15.0%

### Table — Top 10 Highest-Risk Drivers
- Title: "Drivers Requiring Immediate Intervention"
- Legend: "Drivers with a failure rate above 20% and a minimum volume of
  5 deliveries. These are the priority candidates for the retraining program.
  Each red row represents an avoidable cost for the operation."
- Columns: Name | Experience Level | Failure Rate | No. of Deliveries
- Formatting: rate > 25% in bold red, 20-25% in amber

### Chart 2 — H1 vs H2 Trajectory (scatter plot)
- Title: "Performance Evolution: 1st Semester vs. 2nd Semester"
- Legend: "Each point is a driver. Points below the diagonal improved
  in the 2nd semester; above, they worsened. Without formal intervention, only
  49.7% of drivers improved — and 50.3% worsened or stagnated.
  Self-correction is not sufficient."
- Green points: improved
- Red points: worsened
- Dashed diagonal line: "no change"
- Annotation: "50% improved spontaneously | 50% need intervention"

---

## PAGE 4 — CUSTOMER IMPACT

### Narrative (introductory card)
> "The customer does not cause the failures — they suffer them.
> 71% of the customer base experienced at least one missing item in 2023.
> The good news: 92.2% return after the failure.
> The bad news: the 7.8% who do not come back represent **$47,371 in lost revenue**.
> The cost of churn far exceeds the cost of redelivery."

### KPI Card Row (4 cards)
| Card | Value | Label | Color |
|---|---|---|---|
| Impacted Customers | 881 | 71.1% of the base suffered a failure | #B45309 |
| Return Rate | 92.2% | After the first failure | #2D7D4F |
| Lost Customers | 26 | Post-failure churn (90 days) | #991B1B |
| Revenue at Risk | $47,371 | Revenue history of churned customers | #991B1B |

### Chart 1 — Customer Failure Profile (donut chart)
- Title: "Customer Base Distribution by Failure Experience"
- Legend: "Only 28.9% of customers never had a problem.
  The majority of the base was impacted — the problem is systemic,
  not an isolated exception. This makes delivery quality
  a strategic priority, not just an operational one."
- Data:
```
0 failures:   358 customers (28.9%)  → green #2D7D4F
1 failure:    approx. 400 customers  → amber #B45309
2 failures:   approx. 280 customers  → orange
3+ failures:  approx. 200 customers  → red #991B1B
```

### Chart 2 — Churn Rate by Number of Failures (ascending bars)
- Title: "Loss Risk by Number of Failures Experienced"
- Legend: "With each additional failure, the probability of losing the customer
  increases. Intervention must happen at the FIRST failure —
  not the third, when the customer has already decided to leave."
- Bars with white → red gradient as the number of failures increases
- Annotation: "Intervening at the 1st failure costs less than recovering at the 3rd"

### Chart 3 — Return Rate: With Failure vs Without Failure (comparative bars)
- Title: "Repurchase Rate: Customers With and Without Failure"
- Legend: "Customers who never had a failure have a naturally high repurchase rate.
  Failure reduces this rate — but 92.2% of impacted customers
  still return, showing the resilience of the base.
  The focus should be the minority group that does not come back."
- Two side-by-side bars: "Without failure" (green) and "With failure" (amber)

### Insight Card (left amber border)
```
TRUE COST OF THE PROBLEM
━━━━━━━━━━━━━━━━━━━━━━━━
Direct cost (redelivery):       $106,380/year
Lost revenue (churn):            $47,371/year
─────────────────────────────────────────────
Total estimated cost:           $153,751/year

Proactive compensation cost:    ~$5,000/year
(20% discount after 1st failure for the 26 churned customers)

Intervention ROI: 9x
```

---

## PAGE 5 — ACTION PLAN

### Narrative (introductory card)
> "Two independent analyses confirm the same conclusion:
> **the problem lies with the drivers, not the customers**.
> SHAP: 66.8% vs 3.4% of explanatory power.
> Variance: drivers range from 0% to 36.4%; customers show a nearly uniform failure rate.
> The actions below are prioritized by expected financial impact."

### Section — Verdict (large card, red border, visual highlight)
```
╔══════════════════════════════════════════════════════════╗
║  ROOT CAUSE IDENTIFIED                                   ║
║                                                          ║
║  The missing items problem is primarily                  ║
║  a DRIVER OPERATIONAL PROBLEM.                           ║
║                                                          ║
║  Driver:      66.8% of explanatory power                 ║
║  Order:       13.4%                                      ║
║  Time:         5.0%                                      ║
║  Customer:     3.4%  ← NOT the cause                     ║
║  Location:     2.3%                                      ║
╚══════════════════════════════════════════════════════════╝
```

### Action Plan Table (5 rows, sorted by priority)

Style: clean table with zebra striping (alternating rows #F8FAFC and #FFFFFF).
Columns: Priority | Action | Target | Expected Impact | Estimated Savings

| Pri | Action | Target | Impact | Savings |
|---|---|---|---|---|
| 🔴 1 | Mandatory retraining — drivers with rate > 20% | Chronic and unstable drivers | -30% in failure cost | $31,914/year |
| 🟠 2 | Digital checklist for orders > 12 items or > $400 | High-risk orders | -2pp in failure rate | $13,829/year |
| 🟡 3 | Operational reinforcement on Mondays | Weekly operational team | Reduction of the worst window | $5,319/year |
| 🔵 4 | Audit in Altamonte Springs | Regional management | Alignment to Sanford | $4,255/year |
| 🟢 5 | Immediate compensation after customer's 1st failure | 26 churned customers | Recover $47,371 in revenue | $47,371 |

> **Note:** Estimated savings based on a redelivery cost of $70.83 per failure
> and a projected 30% reduction from priority action 1.

### Chart — ROI by Action (horizontal bars)
- Title: "Projected Savings by Initiative ($/year)"
- Legend: "The bars represent the financial value of each action if executed successfully.
  Action 1 (retraining) has the highest absolute return.
  Combined, the 5 actions can generate total savings of $102,688/year —
  equivalent to 96% of the current failure cost."
- Bar 1 (largest): color #991B1B
- Bars 2-4: color #B45309 with gradual transparency
- Bar 5: color #2D7D4F

### Final Card — Executive Summary
```
PROJECT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10,000 orders analyzed | $2.83M in revenue | 7 cities

Problem identified:   15.0% failure rate
Root cause:           Drivers (66.8% of the explanatory factor)
Current cost:         $106,380/year in redeliveries
Revenue at risk:      $47,371 (post-failure churn)

Potential savings:    $102,688/year with 5 actions
Program ROI:          96% reduction in failure cost
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analysis performed with: Python, Pandas, Scikit-learn, SHAP
Methodology: EDA + Inferential Statistics + Machine Learning + Segmentation
```

---

## TECHNICAL NOTES FOR LOVABLE

1. **All data is static** — use the exact values provided above. Do not generate random data.

2. **Recharts** for charts (default library in Lovable).

3. **Responsiveness**: the dashboard must work on screens >= 1280px. The sidebar collapses on smaller screens.

4. **Tooltips**: all charts must have a tooltip on hover showing the exact value.

5. **Insight cards**: use a colored left border (4px) to differentiate narrative cards from KPI cards.
   - Red border: critical insight
   - Amber border: attention
   - Blue border: informational

6. **Legends**: each chart must have a text legend below the title, in 13px font, color #5A6A7A,
   explaining what the chart shows and what the user should conclude from looking at it.

7. **Animations**: smooth when loading each page (fade-in 300ms). No excessive animations.

8. **Footer**: on all pages, a subtle footer:
   "Walmart Delivery Analytics · 2023 Analysis · Douglas Piangers · Data Science Portfolio"

9. **Favicon / tab title**: "Walmart Delivery Analytics — Dashboard"
