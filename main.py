"""RetailLens pipeline entry point."""

import argparse
from pathlib import Path

from src.timing import TIMINGS, timed
from src.generate import generate
from src.etl_dask import run_etl
from src.analyze_spark import run_analysis
from src.compute_ray import run_parallel
from src.visualize import generate_all
from src.report import build_report, print_console_summary

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"


def main():
    parser = argparse.ArgumentParser(description="RetailLens — distributed descriptive analytics pipeline")
    parser.add_argument("--rows", type=int, default=500_000, help="rows to generate")
    parser.add_argument("--skip-generate", action="store_true", help="reuse existing sales.csv")
    args = parser.parse_args()

    csv_path = DATA_DIR / "sales.csv"
    parquet_path = DATA_DIR / "sales.parquet"
    report_path = OUTPUT_DIR / "report.html"

    counts: dict = {}

    if args.skip_generate and csv_path.exists():
        print(f"[generate] skipping; using existing {csv_path}")
        counts["generated"] = sum(1 for _ in csv_path.open()) - 1
        TIMINGS["generate"] = 0.0
    else:
        with timed("generate"):
            counts["generated"] = generate(args.rows, csv_path)

    with timed("clean"):
        etl_info = run_etl(csv_path, parquet_path)
    counts["clean"] = etl_info["clean_rows"]
    counts["dropped"] = etl_info["dropped_rows"]
    counts["partitions"] = etl_info["partitions"]

    with timed("aggregate"):
        spark_results = run_analysis(parquet_path)
    counts["spark_rows"] = spark_results["total_rows"]

    with timed("per_segment_stats"):
        ray_results = run_parallel(parquet_path)
    counts["ray_tasks"] = ray_results["n_tasks"]

    with timed("plots"):
        plot_paths = generate_all(spark_results, ray_results, PLOTS_DIR)

    with timed("report"):
        conclusions = build_report(
            spark_results=spark_results,
            ray_results=ray_results,
            counts=counts,
            timings=TIMINGS,
            plot_paths=plot_paths,
            out_html=report_path,
        )

    print_console_summary(spark_results, counts, TIMINGS, conclusions)
    print(f"HTML report: {report_path}")
    print(f"Plots:       {PLOTS_DIR}")


if __name__ == "__main__":
    main()
