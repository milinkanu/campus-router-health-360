# Campus Router Health 360 — Health Score Formula & Methodology

This document explains the mathematical formula, thresholds, component weights, and architectural rationale behind the **Router Health Score**.

---

## 1. Core Rationale: Why Sustained Metrics Over Single-Hour Averages?

A single high-latency spike or temporary burst in traffic (e.g., during a single peak hour) should not classify a router as broken. Traditional simple averaging masks persistent failures and penalizes temporary blips equally.

Our scoring system evaluates **sustained behavior** by measuring the **percentage of hours** in which performance metrics cross critical thresholds. This ensures that routers with persistent, ongoing degradation rank at the bottom of the fleet (worst health scores), while routers with isolated single-hour spikes maintain high scores.

---

## 2. Threshold Constants

The following critical performance thresholds are applied across all hourly telemetry rows:

| Metric Name | Threshold | Condition | Rationale |
|---|---|---|---|
| **Low Speed** | `< 20 Mbps` | `avg_speed_mbps < 20.0` | Speeds below 20 Mbps degrade video conferencing and file downloads |
| **Weak Signal** | `< -75 dBm` | `signal_dbm < -75.0` | Signals weaker than -75 dBm cause high packet loss and instability |
| **High Latency** | `> 100 ms` | `latency_ms > 100.0` | Latency above 100 ms causes noticeable audio/video lag and timeouts |

---

## 3. Aggregation & Normalization

For each router $i$, telemetry is aggregated across all observed hours into 5 core component metrics:

1. **`disconnects_per_hour`**: $\text{mean}(\text{disconnects})$
2. **`avg_packet_loss_pct`**: $\text{mean}(\text{packet\_loss\_pct})$
3. **`low_speed_hours_pct`**: $\frac{\text{Count}(\text{speed} < 20)}{\text{Total Hours}}$
4. **`avg_latency_ms`**: $\text{mean}(\text{latency\_ms})$
5. **`weak_signal_hours_pct`**: $\frac{\text{Count}(\text{signal} < -75)}{\text{Total Hours}}$

Each of these 5 metrics is min-max normalized across the entire active fleet to a 0–1 scale, where **0 = best performance** and **1 = worst performance**:

$$\text{Normalized Component}_c = \frac{X_c - \min(X_c)}{\max(X_c) - \min(X_c)}$$

---

## 4. Component Weights & Penalty Calculation

Each normalized metric is multiplied by its domain-weighted importance:

| Component Metric | Weight ($w_c$) | Rationale |
|---|---|---|
| `disconnects_per_hour` | **0.30 (30%)** | Frequent disconnects completely sever connectivity (highest impact) |
| `avg_packet_loss_pct` | **0.25 (25%)** | High packet loss destroys real-time streaming, calls, and web browsing |
| `low_speed_hours_pct` | **0.20 (20%)** | Sustained low speed degrades overall throughput across users |
| `avg_latency_ms` | **0.15 (15%)** | High latency affects interactive sessions and web responsiveness |
| `weak_signal_hours_pct` | **0.10 (10%)** | Weak coverage indicates dead zones or physical obstruction |

The total weighted penalty for router $i$ is calculated as:

$$\text{Penalty}_i = \sum_{c=1}^{5} w_c \times \text{Normalized Component}_{c, i}$$

---

## 5. Final Health Score & Top Issue Assignment

The final **Health Score** is expressed on a 0–100 scale:

$$\text{Health Score}_i = \text{round}\Big(100 \times (1 - \text{Penalty}_i), 1\Big)$$

- **`100.0`**: Perfect router performance across all metrics.
- **`< 50.0`**: Critical health state requiring immediate intervention.

### Primary Top Issue Labeling:
For each router:
- If $\text{Health Score}_i \ge 80.0$, `top_issue` is assigned **`"Healthy"`**.
- If $\text{Health Score}_i < 80.0$, `top_issue` is mapped to the single component with the largest weighted penalty contribution ($\text{argmax}(w_c \times \text{Normalized Component}_{c, i})$):
  - `disconnects_per_hour` $\rightarrow$ `"Frequent disconnects"`
  - `avg_packet_loss_pct` $\rightarrow$ `"High packet loss"`
  - `low_speed_hours_pct` $\rightarrow$ `"Consistently low speed"`
  - `avg_latency_ms` $\rightarrow$ `"High latency"`
  - `weak_signal_hours_pct` $\rightarrow$ `"Weak signal coverage"`
