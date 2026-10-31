"""Per-segment transaction statistics computed in parallel via Ray tasks.

Each remote worker reads the parquet file independently and returns one
summary — category stats, country stats, payment-method breakdown or
weekday/hour counts — which the driver then collects.
"""

from pathlib import Path

import pandas as pd
import ray


@ray.remote
def stats_by(parquet_path: str, group_col: str) -> dict:
    df = pd.read_parquet(parquet_path)
    g = df.groupby(group_col)["total_amount"]
    out = pd.DataFrame({
        "count": g.count(),
        "mean": g.mean().round(2),
        "median": g.median().round(2),
        "std": g.std().round(2),
        "p95": g.quantile(0.95).round(2),
        "sum": g.sum().round(2),
    }).reset_index()
    return {"group_col": group_col, "data": out.to_dict(orient="records")}


@ray.remote
def payment_method_breakdown(parquet_path: str) -> dict:
    df = pd.read_parquet(parquet_path)
    g = df.groupby("payment_method").agg(
        transactions=("transaction_id", "count"),
        revenue=("total_amount", "sum"),
        avg_order=("total_amount", "mean"),
    ).round(2).reset_index()
    g = g.sort_values("revenue", ascending=False)
    return {"group_col": "payment_method", "data": g.to_dict(orient="records")}


@ray.remote
def weekday_hour_heatmap(parquet_path: str) -> dict:
    df = pd.read_parquet(parquet_path)
    pivot = (
        df.groupby(["weekday", "hour"]).size().unstack(fill_value=0).sort_index()
    )
    return {"index": pivot.index.tolist(), "columns": pivot.columns.tolist(), "values": pivot.values.tolist()}


def run_parallel(parquet_path: Path) -> dict:
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True, log_to_driver=False, include_dashboard=False)

    p = str(parquet_path)
    futures = [
        stats_by.remote(p, "product_category"),
        stats_by.remote(p, "customer_country"),
        payment_method_breakdown.remote(p),
        weekday_hour_heatmap.remote(p),
    ]
    cat_stats, country_stats, payment_stats, heatmap = ray.get(futures)
    ray.shutdown()

    return {
        "category_stats": cat_stats["data"],
        "country_stats": country_stats["data"],
        "payment_stats": payment_stats["data"],
        "heatmap": heatmap,
        "n_tasks": len(futures),
    }
