"""Plot rendering for the report.

Monetary axes use a short-form USD formatter ("$10.0M", "$500K") so the
numbers stay readable without scientific notation.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CURRENCY = "USD"


def _usd(value: float) -> str:
    v = abs(value)
    if v >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def _usd_formatter() -> FuncFormatter:
    return FuncFormatter(lambda x, _: _usd(x))


def _save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_monthly_trend(monthly: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(monthly["year_month"], monthly["revenue"], marker="o", color="#2a7ab0")
    ax.set_title(f"Monthly Revenue Trend ({CURRENCY})")
    ax.set_xlabel("Month")
    ax.set_ylabel(f"Revenue ({CURRENCY})")
    ax.yaxis.set_major_formatter(_usd_formatter())
    ax.tick_params(axis="x", rotation=45)
    _save(fig, out)


def plot_top_products(top: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top, y="product_name", x="revenue", ax=ax, color="#4caf50")
    ax.set_title(f"Top 10 Products by Revenue ({CURRENCY})")
    ax.set_xlabel(f"Revenue ({CURRENCY})")
    ax.set_ylabel("Product")
    ax.xaxis.set_major_formatter(_usd_formatter())
    for i, rev in enumerate(top["revenue"]):
        ax.text(rev, i, "  " + _usd(rev), va="center", fontsize=9, color="#333")
    _save(fig, out)


def plot_by_category(by_category: list[dict], out: Path):
    df = pd.DataFrame(by_category).sort_values("revenue", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df["product_category"], df["revenue"], color="#5e81ac")
    total = df["revenue"].sum()
    for bar, value in zip(bars, df["revenue"]):
        pct = value / total * 100 if total else 0
        ax.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f"  {_usd(value)}  ({pct:.1f}%)",
            va="center",
            fontsize=9,
            color="#222",
        )
    ax.set_title(f"Revenue by Product Category ({CURRENCY})\n"
                 "computed via RDD map / shuffle / reduce")
    ax.set_xlabel(f"Revenue ({CURRENCY})")
    ax.set_ylabel("Category")
    ax.xaxis.set_major_formatter(_usd_formatter())
    ax.margins(x=0.18)
    _save(fig, out)


def plot_by_region(by_region: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=by_region, x="region", y="revenue", ax=ax, color="#ff7043")
    ax.set_title(f"Revenue by Region ({CURRENCY})")
    ax.set_xlabel("Region")
    ax.set_ylabel(f"Revenue ({CURRENCY})")
    ax.yaxis.set_major_formatter(_usd_formatter())
    for i, v in enumerate(by_region["revenue"]):
        ax.text(i, v, _usd(v), ha="center", va="bottom", fontsize=9, color="#333")
    ax.margins(y=0.12)
    _save(fig, out)


def plot_weekday_hour_heatmap(heatmap: dict, out: Path):
    values = np.array(heatmap["values"])
    index_labels = [WEEKDAY_NAMES[i] if 0 <= i < 7 else str(i) for i in heatmap["index"]]
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(
        values,
        annot=False,
        cmap="viridis",
        xticklabels=heatmap["columns"],
        yticklabels=index_labels,
        ax=ax,
        cbar_kws={"label": "Transaction count"},
    )
    ax.set_title("Transactions by Weekday × Hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Weekday")
    _save(fig, out)


def generate_all(spark_results: dict, ray_results: dict, plots_dir: Path) -> list[str]:
    paths = {
        "monthly_trend": plots_dir / "01_monthly_trend.png",
        "top_products":  plots_dir / "02_top_products.png",
        "by_category":   plots_dir / "03_revenue_by_category.png",
        "by_region":     plots_dir / "04_revenue_by_region.png",
        "heatmap":       plots_dir / "05_weekday_hour_heatmap.png",
    }
    plot_monthly_trend(spark_results["monthly"], paths["monthly_trend"])
    plot_top_products(spark_results["top_products"], paths["top_products"])
    plot_by_category(spark_results["by_category"], paths["by_category"])
    plot_by_region(spark_results["by_region"], paths["by_region"])
    plot_weekday_hour_heatmap(ray_results["heatmap"], paths["heatmap"])
    return [str(p) for p in paths.values()]
