import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.health_score import aggregate_router_metrics, normalize_column
from app.config import WEIGHTS, ISSUE_LABELS

logger = logging.getLogger(__name__)


def cluster_routers(metrics_df: pd.DataFrame, routers_df: pd.DataFrame, n_clusters: int = 4) -> dict:
    """
    1. Reuse aggregate_router_metrics() + normalize_column() from health_score.py.
    2. Build a feature matrix of the 5 normalized component columns per router.
    3. Run sklearn.cluster.KMeans(n_clusters=n_clusters, random_state=42, n_init=10).
    4. For each cluster, compute the mean of raw feature values and assign an auto-label.
    5. Return dict with cluster summaries and router lists.
    """
    aggs = aggregate_router_metrics(metrics_df)
    if aggs.empty:
        return {"clusters": []}

    features = list(WEIGHTS.keys())
    norm_df = pd.DataFrame(index=aggs.index)

    for f in features:
        norm_df[f] = normalize_column(aggs[f])

    X = norm_df.values

    # Determine number of clusters based on sample size
    num_samples = len(X)
    actual_k = min(n_clusters, num_samples)

    if actual_k < 1:
        return {"clusters": []}

    try:
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X)
    except Exception as e:
        logger.warning("KMeans failed (%s). Using fallback quantile binning.", e)
        # Quantile binning fallback
        cluster_labels = (norm_df.sum(axis=1) * actual_k).astype(int).clip(0, actual_k - 1).values

    aggs["cluster_id"] = cluster_labels

    cluster_results = []
    for cid in range(actual_k):
        c_subset = aggs[aggs["cluster_id"] == cid]
        if c_subset.empty:
            continue

        # Find highest mean feature among raw metrics for cluster naming
        means = c_subset[features].mean()
        # Find which metric has highest normalized mean in cluster
        norm_subset = norm_df.loc[c_subset.index]
        norm_means = norm_subset[features].mean()
        highest_feature = norm_means.idxmax()

        base_label = ISSUE_LABELS.get(highest_feature, "Performance Issue")
        if norm_means[highest_feature] < 0.15:
            cluster_name = f"Cluster {cid + 1}: Healthy Fleet"
        else:
            cluster_name = f"Cluster {cid + 1}: {base_label} Pattern"

        router_list = c_subset["router_id"].tolist()

        cluster_results.append({
            "cluster_id": int(cid),
            "cluster_label": cluster_name,
            "count": len(router_list),
            "router_ids": router_list,
        })

    return {"clusters": cluster_results}
