import pandas as pd
import numpy as np
from app.config import (
    LOW_SPEED_THRESHOLD,
    WEAK_SIGNAL_THRESHOLD,
    HIGH_LATENCY_THRESHOLD,
    WEIGHTS,
    ISSUE_LABELS,
)


def aggregate_router_metrics(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group metrics_df by router_id and compute per-router aggregated metrics.
    """
    if metrics_df.empty:
        return pd.DataFrame(columns=[
            "router_id", "avg_latency_ms", "avg_packet_loss_pct",
            "disconnects_per_hour", "low_speed_hours_pct",
            "weak_signal_hours_pct", "high_latency_hours_pct",
            "total_hours_observed"
        ])

    def calc_router_aggs(g):
        total_hours = len(g)
        if total_hours == 0:
            return pd.Series({
                "avg_latency_ms": 0.0,
                "avg_packet_loss_pct": 0.0,
                "disconnects_per_hour": 0.0,
                "low_speed_hours_pct": 0.0,
                "weak_signal_hours_pct": 0.0,
                "high_latency_hours_pct": 0.0,
                "total_hours_observed": 0,
            })

        low_speed_cnt = (g["avg_speed_mbps"] < LOW_SPEED_THRESHOLD).sum()
        weak_signal_cnt = (g["signal_dbm"] < WEAK_SIGNAL_THRESHOLD).sum()
        high_latency_cnt = (g["latency_ms"] > HIGH_LATENCY_THRESHOLD).sum()

        return pd.Series({
            "avg_latency_ms": float(g["latency_ms"].mean()),
            "avg_packet_loss_pct": float(g["packet_loss_pct"].mean()),
            "disconnects_per_hour": float(g["disconnects"].mean()),
            "low_speed_hours_pct": float(low_speed_cnt / total_hours),
            "weak_signal_hours_pct": float(weak_signal_cnt / total_hours),
            "high_latency_hours_pct": float(high_latency_cnt / total_hours),
            "total_hours_observed": int(total_hours),
        })

    aggs = metrics_df.groupby("router_id", as_index=False).apply(
        calc_router_aggs, include_groups=False
    )
    return aggs


def normalize_column(series: pd.Series) -> pd.Series:
    """
    Min-max normalize a Series to a 0-1 scale, where 1 = worst.
    Guards against division by zero when max == min.
    """
    s_min = series.min()
    s_max = series.max()
    if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
        return pd.Series(0.0, index=series.index)
    return (series - s_min) / (s_max - s_min)


def compute_health_scores(metrics_df: pd.DataFrame, routers_df: pd.DataFrame) -> pd.DataFrame:
    """
    1. aggregate_router_metrics(metrics_df)
    2. normalize each of the 5 component columns (0=best/1=worst)
    3. penalty = sum(weight * normalized_value for each component)
    4. health_score = round(100 * (1 - penalty), 1)   # 0-100, 100 = perfect
    5. merge with routers_df to attach building/model/firmware/user_type
    6. determine top_issue label
    7. return DataFrame sorted ascending by health_score
    """
    aggs = aggregate_router_metrics(metrics_df)

    if aggs.empty:
        # Merge empty aggs with routers_df
        result = routers_df.copy()
        result["health_score"] = 100.0
        result["top_issue"] = "Healthy"
        for col in ["avg_latency_ms", "avg_packet_loss_pct", "disconnects_per_hour", "low_speed_hours_pct", "weak_signal_hours_pct", "total_hours_observed"]:
            result[col] = 0.0
        return result

    # Compute normalized component metrics (0=best, 1=worst)
    norm_df = pd.DataFrame(index=aggs.index)
    weighted_contribs = pd.DataFrame(index=aggs.index)

    for comp, weight in WEIGHTS.items():
        norm_val = normalize_column(aggs[comp])
        norm_df[comp] = norm_val
        weighted_contribs[comp] = norm_val * weight

    penalty = weighted_contribs.sum(axis=1)

    # Health score between 0 and 100
    aggs["health_score"] = (100.0 * (1.0 - penalty)).clip(0.0, 100.0).round(1)

    # Determine top issue
    top_issues = []
    for idx, row in aggs.iterrows():
        score = row["health_score"]
        if score >= 80.0:
            top_issues.append("Healthy")
        else:
            contribs = weighted_contribs.loc[idx]
            max_comp = contribs.idxmax()
            top_issues.append(ISSUE_LABELS.get(max_comp, "Performance degradation"))

    aggs["top_issue"] = top_issues

    # Merge with routers_df
    merged = pd.merge(routers_df, aggs, on="router_id", how="left")

    # Fill NaNs if any router had no metrics
    merged["health_score"] = merged["health_score"].fillna(100.0)
    merged["top_issue"] = merged["top_issue"].fillna("Healthy")
    merged["total_hours_observed"] = merged["total_hours_observed"].fillna(0).astype(int)

    for col in ["avg_latency_ms", "avg_packet_loss_pct", "disconnects_per_hour", "low_speed_hours_pct", "weak_signal_hours_pct"]:
        merged[col] = merged[col].fillna(0.0)

    # Sort ascending by health_score
    merged = merged.sort_values("health_score", ascending=True).reset_index(drop=True)
    return merged
