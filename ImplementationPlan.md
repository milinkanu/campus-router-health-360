# Router Health Dashboard + AI Copilot — Implementation Spec

This document is a complete, self-contained implementation spec. An LLM (or developer)
should be able to build the entire application from this file alone, without asking
clarifying questions. Follow the phases in order. Do not skip validation steps.

---

## 1. Project Overview

A web app that ingests router telemetry + support complaints, computes a **health score**
per router, surfaces the worst-performing routers, lets a user drill into any router's
history, and offers an **AI copilot** that diagnoses a specific router's problem using
only real retrieved data (no hallucinated numbers).

**Three input datasets** (CSV, comma-separated, header row present):

**`routers.csv`**
| column | type | example | notes |
|---|---|---|---|
| router_id | string | R-1000 | primary key |
| model | string | TL-841N | |
| firmware_version | string | v3.0 | |
| building | string | Lab-Complex | categorical, used for filtering |
| room | string | 241 | |
| user_type | string | student / staff | |
| issue_date | date (YYYY-MM-DD) | 2024-08-16 | when router was issued |

**`metrics.csv`** (hourly time series, many rows per router)
| column | type | example | notes |
|---|---|---|---|
| router_id | string | R-1000 | foreign key -> routers.csv |
| hour | datetime (YYYY-MM-DDTHH:MM) | 2026-08-06T00:00 | one row per router per hour |
| avg_speed_mbps | float | 74.4 | |
| latency_ms | float | 12 | |
| packet_loss_pct | float | 0.9 | 0-100 scale |
| disconnects | int | 0 | count in that hour |
| connected_devices | int | 9 | |
| signal_dbm | float | -41 | negative dBm, closer to 0 = stronger |

**`complaints.csv`**
| column | type | example | notes |
|---|---|---|---|
| ticket_id | string | T-901 | primary key |
| router_id | string | R-1002 | foreign key -> routers.csv |
| date | date (YYYY-MM-DD) | 2026-08-02 | |
| complaint_text | string | "Video calls freeze constantly" | free text |

> **Before coding**, run a quick pandas profiling pass on the real CSVs (row counts, null
> checks, value ranges, unique router_id counts across the 3 files) and adjust the health
> score thresholds in Section 4 if the real data's distribution differs materially from
> assumptions below. Do not skip this — the score is meaningless if thresholds are
> miscalibrated to the actual data.

---

## 2. Tech Stack & Dependencies

**Backend** — Python 3.11+, FastAPI
```
fastapi
uvicorn[standard]
pandas
pydantic>=2
python-dotenv
anthropic          # or openai, whichever LLM is used for the copilot
scikit-learn        # only needed if implementing the bonus clustering feature
python-multipart
```

**Frontend** — React 18 + Vite + Tailwind
```
react, react-dom
vite
tailwindcss, postcss, autoprefixer
recharts
axios
```

**Dev/infra**
```
pytest, httpx        (backend tests)
ruff or flake8        (lint, optional)
```

---

## 3. Folder Structure

```
project-root/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app instance, CORS, router includes
│   │   ├── config.py               # env vars, constants, CSV paths, score weights
│   │   ├── data_loader.py          # load & cache CSVs into DataFrames at startup
│   │   ├── schemas.py              # all Pydantic request/response models
│   │   ├── health_score.py         # health score computation logic
│   │   ├── evidence.py             # evidence-bundle builder for the copilot
│   │   ├── copilot.py              # LLM call wrapper + prompt templates
│   │   ├── clustering.py           # (bonus) k-means failure-pattern clustering
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── rankings.py         # GET /rankings
│   │       ├── router_detail.py    # GET /routers/{router_id}
│   │       ├── copilot_routes.py   # POST /copilot/ask
│   │       └── meta.py             # GET /health, GET /filters
│   ├── data/
│   │   ├── routers.csv
│   │   ├── metrics.csv
│   │   └── complaints.csv
│   ├── tests/
│   │   ├── test_health_score.py
│   │   ├── test_rankings.py
│   │   ├── test_router_detail.py
│   │   └── test_copilot.py
│   ├── .env.example
│   ├── requirements.txt
│   └── HEALTH_SCORE.md             # formula + weights documented for reviewers
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── client.js           # axios instance, one function per endpoint
│   │   ├── components/
│   │   │   ├── RankingsTable.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   ├── RouterDetailPanel.jsx
│   │   │   ├── MetricChart.jsx
│   │   │   ├── ComplaintsList.jsx
│   │   │   ├── CopilotBox.jsx
│   │   │   └── HealthDistributionChart.jsx   # bonus
│   │   └── styles/
│   │       └── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── .env.example
│   └── package.json
├── README.md
└── .gitignore
```

---

## 4. Health Score Design (`backend/app/health_score.py`)

Compute **once per router**, aggregating across all its hourly rows. Use **sustained**
behavior (percentage of bad hours), not single-hour averages, so one bad hour does not
tank a router's score.

### 4.1 Per-router aggregates to compute first

```python
def aggregate_router_metrics(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group metrics_df by router_id and compute, per router:
      - avg_latency_ms          : mean(latency_ms)
      - avg_packet_loss_pct     : mean(packet_loss_pct)
      - disconnects_per_hour    : mean(disconnects)
      - low_speed_hours_pct     : % of hours where avg_speed_mbps < LOW_SPEED_THRESHOLD
      - weak_signal_hours_pct   : % of hours where signal_dbm < WEAK_SIGNAL_THRESHOLD
      - high_latency_hours_pct  : % of hours where latency_ms > HIGH_LATENCY_THRESHOLD
      - total_hours_observed    : row count (for confidence / data-sufficiency flag)
    Returns one row per router_id.
    """
```

Constants (put in `config.py`, tune after profiling real data):
```python
LOW_SPEED_THRESHOLD = 20        # mbps
WEAK_SIGNAL_THRESHOLD = -75     # dBm
HIGH_LATENCY_THRESHOLD = 100    # ms
```

### 4.2 Normalization

Min-max normalize each aggregate column across the whole fleet to a 0-1 scale, where
1 = worst:
```python
def normalize_column(series: pd.Series) -> pd.Series:
    # (x - min) / (max - min), guard against div-by-zero when max == min
```

### 4.3 Weighted score

```python
WEIGHTS = {
    "disconnects_per_hour":   0.30,
    "avg_packet_loss_pct":    0.25,
    "low_speed_hours_pct":    0.20,
    "avg_latency_ms":         0.15,
    "weak_signal_hours_pct":  0.10,
}

def compute_health_scores(metrics_df, routers_df) -> pd.DataFrame:
    """
    1. aggregate_router_metrics(metrics_df)
    2. normalize each of the 5 component columns (0=best/1=worst)
    3. penalty = sum(weight * normalized_value for each component)
    4. health_score = round(100 * (1 - penalty), 1)   # 0-100, 100 = perfect
    5. merge with routers_df to attach building/model/firmware/user_type
    6. return DataFrame sorted ascending by health_score, with columns:
       router_id, health_score, building, model, firmware_version, user_type,
       avg_latency_ms, avg_packet_loss_pct, disconnects_per_hour,
       low_speed_hours_pct, weak_signal_hours_pct, total_hours_observed,
       top_issue (see 4.4)
    """
```

### 4.4 `top_issue` label

For each router, identify the single component with the highest weighted contribution
to the penalty and map it to a human label:
```python
ISSUE_LABELS = {
    "disconnects_per_hour":  "Frequent disconnects",
    "avg_packet_loss_pct":   "High packet loss",
    "low_speed_hours_pct":   "Consistently low speed",
    "avg_latency_ms":        "High latency",
    "weak_signal_hours_pct": "Weak signal coverage",
}
```
If a router's overall `health_score >= 80`, set `top_issue = "Healthy"` regardless of
the largest component (avoids labeling a fine router with a nitpick).

### 4.5 Validation cases to hand-test after implementing

Write these as actual pytest cases in `tests/test_health_score.py` using small synthetic
DataFrames (do not rely only on eyeballing real data):
1. Router with sustained bad metrics across most hours → low score, appears in worst-10.
2. Router with one bad hour, otherwise clean → score stays high, NOT in worst-10.
3. Router with complaints logged but clean metrics → high health_score (complaints are
   surfaced separately in the detail view / copilot, not folded into the numeric score).
4. Router with clean metrics and no complaints → score near 100, top_issue = "Healthy".

---

## 5. Pydantic Schemas (`backend/app/schemas.py`)

```python
class RouterRankingItem(BaseModel):
    router_id: str
    health_score: float
    building: str
    model: str
    firmware_version: str
    user_type: str
    top_issue: str
    disconnects_per_hour: float
    avg_packet_loss_pct: float
    avg_latency_ms: float

class RankingsResponse(BaseModel):
    total_routers: int
    routers: list[RouterRankingItem]

class HourlyMetric(BaseModel):
    hour: str
    avg_speed_mbps: float
    latency_ms: float
    packet_loss_pct: float
    disconnects: int
    connected_devices: int
    signal_dbm: float

class Complaint(BaseModel):
    ticket_id: str
    date: str
    complaint_text: str

class RouterDetailResponse(BaseModel):
    router_id: str
    model: str
    firmware_version: str
    building: str
    room: str
    user_type: str
    issue_date: str
    health_score: float
    top_issue: str
    metrics: list[HourlyMetric]
    complaints: list[Complaint]

class CopilotRequest(BaseModel):
    router_id: str
    question: str

class CopilotResponse(BaseModel):
    router_id: str
    diagnosis: str
    evidence: list[str]
    recommended_fix: str          # one of: firmware_update, relocate, replace, user_education, none
    confidence: str                # "low" | "medium" | "high"

class FiltersResponse(BaseModel):
    buildings: list[str]
    firmware_versions: list[str]
    models: list[str]
```

---

## 6. Backend Endpoints

All routes are prefixed with `/api`. CORS: allow all origins for the hackathon (`allow_origins=["*"]`).

### 6.1 `GET /api/health`
Returns `{"status": "ok"}`. No dependencies. Used for uptime checks and deploy verification.

### 6.2 `GET /api/filters`
Returns `FiltersResponse` — distinct buildings, firmware_versions, models from `routers.csv`.
Powers the frontend filter dropdowns.

### 6.3 `GET /api/rankings`
Query params:
- `limit: int = 10` — number of worst routers to return (use `-1` or omit for "all", needed for the bonus histogram).
- `building: str | None = None`
- `firmware: str | None = None`
- `model: str | None = None`

Logic:
1. Call `compute_health_scores()` (cache the full result at startup or per-request behind an in-memory cache — do not recompute on every call if it's expensive; for this dataset size a per-request recompute is fine).
2. Apply filters if provided (case-insensitive exact match).
3. Sort ascending by `health_score`, take `limit` rows (or all if `limit == -1`).
4. Return `RankingsResponse` with `total_routers` = count after filtering, before limiting.

Error handling: if `building`/`firmware`/`model` value doesn't exist in the data, return
an empty `routers` list with `total_routers: 0` (not a 404 — filters can legitimately
match nothing).

### 6.4 `GET /api/routers/{router_id}`
Logic:
1. Look up router in `routers.csv`. If not found → `404 {"detail": "router_id not found"}`.
2. Pull that router's rows from `metrics.csv`, sorted by `hour` ascending.
3. Pull that router's rows from `complaints.csv`, sorted by `date` descending.
4. Compute (or look up cached) health_score + top_issue for this router.
5. Return `RouterDetailResponse`.

### 6.5 `POST /api/copilot/ask`
Body: `CopilotRequest`.

Logic:
1. If `router_id` not found → `404`.
2. Call `build_evidence(router_id)` (see Section 7.1) — pure pandas, no LLM.
3. Call `ask_copilot(evidence, question)` (see Section 7.2) — this hits the LLM.
4. Parse/validate the LLM's JSON output against `CopilotResponse`. If parsing fails,
   retry once with a stricter "return ONLY valid JSON" reminder appended; if it fails
   again, return a `502` with a clear error message — never pass malformed JSON to the
   frontend silently.
5. Return `CopilotResponse`.

### 6.6 (Bonus) `GET /api/clusters`
Returns router failure-pattern clusters. Only build after core endpoints 6.1-6.5 work
end-to-end. See Section 9.

---

## 7. AI Copilot Module (`backend/app/evidence.py`, `backend/app/copilot.py`)

### 7.1 Evidence builder — `evidence.py`

```python
def build_evidence(router_id: str) -> dict:
    """
    Pure pandas/pydantic, NO LLM call here. Returns a dict:
    {
        "router_id": ...,
        "health_score": ...,
        "top_issue": ...,
        "metadata": {model, firmware_version, building, room, user_type},
        "metric_summary": {
            "avg_latency_ms": ..., "max_latency_ms": ...,
            "avg_packet_loss_pct": ..., "avg_disconnects_per_hour": ...,
            "low_speed_hours_pct": ..., "weak_signal_hours_pct": ...,
            "total_hours_observed": ...,
        },
        "recent_complaints": [ "2026-08-02: Video calls freeze constantly", ... ],
        # at most the 10 most recent complaint texts, prefixed with date
    }
    This is the ONLY source of truth the LLM will see for this router. If a value would
    be based on fewer than 5 hours of data, add a "data_sufficiency": "low" flag.
    """
```

### 7.2 LLM call wrapper — `copilot.py`

System prompt (use verbatim, do not let the model deviate from the JSON contract):

```
You are a network diagnostics assistant for a campus IT team. You will be given a JSON
evidence bundle for exactly one router: its health score, aggregated metric summary, and
recent complaint texts. This evidence is the ONLY information you have about this router.

Rules:
- Base your diagnosis strictly on the numbers and complaint text provided. Never invent
  metrics, dates, or complaints not present in the evidence.
- If the metrics are healthy (health_score >= 80) and there are no complaints, say so
  plainly — do not manufacture a problem.
- If there are complaints but metrics are healthy, treat it as a likely user-education or
  environmental issue, not a hardware fault.
- Cite the specific numbers you used to reach your conclusion inside the "evidence" list.
- Choose exactly one recommended_fix from this fixed set:
  ["firmware_update", "relocate", "replace", "user_education", "none"]
- Respond with ONLY a single valid JSON object, no markdown fences, no prose outside
  the JSON, matching exactly this schema:
{
  "diagnosis": "<2-4 sentence plain-English diagnosis>",
  "evidence": ["<short bullet citing a specific number>", "..."],
  "recommended_fix": "<one of the fixed set above>",
  "confidence": "<low|medium|high>"
}
```

User message: the evidence dict (as JSON) + the user's free-text question, e.g.:
```
Evidence: {evidence_json}
Question: {question}
```

```python
def ask_copilot(evidence: dict, question: str) -> dict:
    """
    Calls the Anthropic API (model: claude-sonnet-4-6 or later available model string —
    check config for which one; do not hardcode an outdated model id) with the system
    prompt above and the user message. Parses response text as JSON (strip any
    accidental ```json fences before parsing). Raises a clear exception on parse failure
    so the route handler can retry/return 502 per Section 6.5.
    """
```

Config: API key read from `ANTHROPIC_API_KEY` env var via `python-dotenv`. Never commit
the key; `.env.example` should list the variable name only.

---

## 8. Frontend Implementation

### 8.1 `api/client.js`
One axios instance with `baseURL = import.meta.env.VITE_API_URL`. Export one function
per endpoint: `getRankings(params)`, `getFilters()`, `getRouterDetail(id)`, `askCopilot(payload)`.

### 8.2 `App.jsx`
Top-level state: `selectedRouterId`, `filters`. Layout: `FilterBar` + `RankingsTable` on
the left/top, `RouterDetailPanel` (which contains `MetricChart` x2, `ComplaintsList`,
`CopilotBox`) shown when a router is selected.

### 8.3 `RankingsTable.jsx`
- Fetches `/api/rankings` on mount and whenever filters change.
- Columns: router_id, building, health_score (color-coded: red <50, amber 50-79, green ≥80), top_issue.
- Row click sets `selectedRouterId` in parent.
- Sortable by clicking column headers (client-side sort of the fetched page is fine).

### 8.4 `FilterBar.jsx`
- Fetches `/api/filters` on mount, renders building/firmware/model dropdowns + a "clear filters" button.

### 8.5 `RouterDetailPanel.jsx`
- Fetches `/api/routers/{id}` when `selectedRouterId` changes.
- Shows metadata header (model, firmware, building/room, user_type, health_score badge).
- Renders two `MetricChart` instances (latency_ms over hour, packet_loss_pct over hour) and one `ComplaintsList`.
- Renders `CopilotBox` below, passing `router_id`.

### 8.6 `MetricChart.jsx`
- Props: `data` (array of `{hour, value}`), `label`, `unit`, `color`.
- Recharts `LineChart` with `XAxis` on `hour`, `YAxis` on `value`, tooltip showing exact value.

### 8.7 `ComplaintsList.jsx`
- Props: `complaints`. Renders a simple scrollable list, date + text, empty state "No complaints logged."

### 8.8 `CopilotBox.jsx`
- Text input + "Ask" button, disabled while loading.
- On submit, POST `/api/copilot/ask`, render the structured response as a card:
  diagnosis paragraph, "Evidence" bullet list, "Recommended fix" badge, confidence tag.
- Handle and display errors (502/404) with a friendly inline message, not a blank screen.

### 8.9 (Bonus) `HealthDistributionChart.jsx`
- Fetch `/api/rankings?limit=-1`, render a Recharts `BarChart` histogram of `health_score`
  buckets (0-20, 20-40, ... 80-100).

---

## 9. Bonus: Clustering (`backend/app/clustering.py`, `GET /api/clusters`)

Only implement after everything above works end-to-end.

```python
def cluster_routers(metrics_df, routers_df, n_clusters=4) -> pd.DataFrame:
    """
    1. Reuse aggregate_router_metrics() + normalize_column() from health_score.py.
    2. Build a feature matrix of the 5 normalized component columns per router.
    3. Run sklearn.cluster.KMeans(n_clusters=n_clusters, random_state=42, n_init=10).
    4. For each resulting cluster, compute the mean of each raw (non-normalized) feature
       and pick the single highest-mean feature to auto-label the cluster using
       ISSUE_LABELS from health_score.py (e.g. "Weak-signal cluster").
    5. Return DataFrame: router_id, cluster_id, cluster_label.
    """
```
Endpoint `GET /api/clusters` returns `{clusters: [{cluster_id, cluster_label, router_ids: [...]}]}`.

---

## 10. Non-Functional / Production-Grade Requirements

- **Pydantic everywhere**: no raw dicts returned from route handlers.
- **Startup-time CSV load**: `data_loader.py` loads all 3 CSVs once into module-level
  DataFrames (or a small in-memory cache class) on app startup, not per-request.
- **Error handling**: every route wraps risky operations (unknown IDs, LLM parse
  failures, empty filter results) in explicit checks with correct HTTP status codes
  (404 for missing router, 400 for bad params, 502 for LLM failure) — never a bare 500.
- **Logging**: use Python's `logging` module (INFO for requests, ERROR for LLM/parsing
  failures), not `print()`.
- **CORS**: configured explicitly in `main.py`, not left to defaults.
- **Env vars**: `ANTHROPIC_API_KEY` (or equivalent), `CSV_DATA_DIR`, all documented in
  `.env.example` on both backend and frontend (`VITE_API_URL`).
- **Tests**: at minimum, the 4 health-score validation cases (Section 4.5) and one test
  per endpoint happy-path + one error-path (404 router, empty filter result).
- **README.md** at repo root: setup steps (backend venv + `pip install -r requirements.txt`
  + `uvicorn app.main:app --reload`; frontend `npm install` + `npm run dev`), env var
  list, and a link to `HEALTH_SCORE.md` explaining the formula.
- **HEALTH_SCORE.md**: plain-English explanation of the weighted formula, thresholds, and
  why sustained-hours metrics are used instead of raw averages (so reviewers don't have
  to read code to understand the scoring logic).

---

## 11. Build Order (for the LLM to follow literally)

1. `data_loader.py` + `config.py` — load and sanity-check the 3 CSVs.
2. `health_score.py` — implement + pytest the 4 validation cases in Section 4.5 before moving on.
3. `schemas.py`.
4. Routes 6.1-6.4 (health, filters, rankings, router detail) — get these fully working
   and manually tested via `/docs` (FastAPI's auto Swagger UI) before touching the copilot.
5. `evidence.py` — test `build_evidence()` standalone against a couple of real router_ids,
   print the output, sanity check it by eye.
6. `copilot.py` + route 6.5 — wire up the LLM call, test against the 4 copilot scenarios
   from the original brief (sustained bad metrics / one bad hour / complaints-but-healthy /
   genuinely healthy).
7. Frontend scaffold → `RankingsTable` + `FilterBar` → `RouterDetailPanel` + charts →
   `CopilotBox` — build and visually check each piece before adding the next.
8. Bonus features (Section 9, histogram) only after 1-7 are solid.
9. `README.md`, `.env.example` files, deploy.