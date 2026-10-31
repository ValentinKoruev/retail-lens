"""Render the HTML report and print the console summary."""

import base64
from datetime import datetime
from pathlib import Path

from jinja2 import Template

TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RetailLens — Descriptive Analytics Report</title>
<style>
  :root {
    --bg: #f5f7fa;
    --surface: #ffffff;
    --surface-2: #f9fafc;
    --text: #1f2937;
    --muted: #6b7280;
    --border: #e5e7eb;
    --primary: #2563eb;
    --primary-dark: #1e40af;
    --accent: #0891b2;
    --success: #10b981;
    --warn: #f59e0b;
    --shadow: 0 1px 3px rgba(16, 24, 40, .06), 0 1px 2px rgba(16, 24, 40, .04);
    --shadow-lg: 0 10px 25px -5px rgba(16, 24, 40, .08), 0 8px 10px -6px rgba(16, 24, 40, .04);
  }
  * { box-sizing: border-box; }
  html, body { background: var(--bg); color: var(--text); }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    margin: 0; padding: 2rem 1rem 4rem; line-height: 1.55;
  }
  .container { max-width: 1180px; margin: 0 auto; }

  .hero {
    background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #0891b2 100%);
    color: #fff; padding: 2.4rem 2rem; border-radius: 16px; box-shadow: var(--shadow-lg);
    margin-bottom: 2rem;
  }
  .hero h1 { margin: 0 0 .4rem; font-size: 2rem; font-weight: 700; letter-spacing: -.01em; }
  .hero .subtitle { opacity: .9; font-size: 1rem; margin: 0; }
  .hero .pills { margin-top: 1.1rem; display: flex; flex-wrap: wrap; gap: .5rem; }
  .pill {
    background: rgba(255,255,255,.18); color: #fff; padding: .3rem .8rem;
    border-radius: 999px; font-size: .82rem; font-weight: 500;
    backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,.25);
  }

  .card {
    background: var(--surface); border-radius: 12px; padding: 1.6rem 1.8rem;
    box-shadow: var(--shadow); border: 1px solid var(--border);
    margin-bottom: 1.6rem;
  }
  .card h2 {
    margin: 0 0 1rem; font-size: 1.25rem; font-weight: 600; color: var(--text);
    display: flex; align-items: center; gap: .55rem;
  }
  .card h2::before {
    content: ""; width: 4px; height: 1.1em; background: var(--primary); border-radius: 2px;
  }
  .card .section-note { color: var(--muted); font-size: .88rem; margin: -.5rem 0 1rem; }

  /* headline metric cards */
  .stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
  }
  .stat {
    background: var(--surface-2); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.1rem 1.2rem;
  }
  .stat .label { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; font-weight: 600; }
  .stat .value { font-size: 1.55rem; font-weight: 700; color: var(--text); margin-top: .25rem; letter-spacing: -.01em; }
  .stat .unit { font-size: .9rem; color: var(--muted); margin-left: .25rem; font-weight: 500; }

  /* tables */
  table {
    border-collapse: collapse; width: 100%; font-size: .92rem;
    background: var(--surface); border-radius: 8px; overflow: hidden;
  }
  th, td { padding: .65rem .9rem; text-align: left; border-bottom: 1px solid var(--border); }
  th {
    background: var(--surface-2); font-weight: 600; color: var(--text);
    font-size: .82rem; text-transform: uppercase; letter-spacing: .03em;
  }
  tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: var(--surface-2); }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }

  /* timing bar visualization */
  .timing-bar {
    display: inline-block; background: var(--primary); height: 8px;
    border-radius: 4px; vertical-align: middle; margin-right: .5rem;
    opacity: .75;
  }
  tfoot td { background: var(--surface-2); font-weight: 600; }

  /* plots */
  .plots-grid { display: grid; gap: 1.2rem; }
  .plot {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 1rem; text-align: center;
  }
  .plot img { max-width: 100%; height: auto; border-radius: 6px; }
  .plot .caption {
    color: var(--muted); font-size: .85rem; margin-top: .5rem;
    text-transform: capitalize;
  }

  /* conclusions */
  ul.conclusions { list-style: none; padding: 0; margin: 0; }
  ul.conclusions li {
    background: var(--surface-2); border-left: 3px solid var(--primary);
    padding: .7rem 1rem; margin: .5rem 0; border-radius: 6px;
    font-size: .95rem;
  }

  /* footer */
  footer { text-align: center; color: var(--muted); font-size: .82rem; margin-top: 2rem; }

  @media (max-width: 640px) {
    .hero { padding: 1.6rem 1.2rem; }
    .hero h1 { font-size: 1.5rem; }
    .card { padding: 1.2rem 1rem; }
    th, td { padding: .55rem .55rem; font-size: .85rem; }
  }
</style>
</head>
<body>
<div class="container">

  <div class="hero">
    <h1>RetailLens</h1>
    <p class="subtitle">Sales performance overview — {{ period_label }}</p>
    <p class="subtitle" style="opacity:.8;font-size:.9rem;margin-top:.3rem;">Generated {{ generated_at }}</p>
  </div>

  <div class="card">
    <h2>Headline metrics</h2>
    <div class="section-note">All monetary values are in USD.</div>
    <div class="stats-grid">
      <div class="stat">
        <div class="label">Total revenue</div>
        <div class="value">${{ "{:,.0f}".format(overall.total_revenue) }}<span class="unit">USD</span></div>
      </div>
      <div class="stat">
        <div class="label">Average order value</div>
        <div class="value">${{ "{:,.2f}".format(overall.avg_order_value) }}<span class="unit">USD</span></div>
      </div>
      <div class="stat">
        <div class="label">Unique customers</div>
        <div class="value">{{ "{:,}".format(overall.unique_customers) }}</div>
      </div>
      <div class="stat">
        <div class="label">Unique products</div>
        <div class="value">{{ "{:,}".format(overall.unique_products) }}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Record counts</h2>
    <div class="stats-grid">
      <div class="stat">
        <div class="label">Total transactions</div>
        <div class="value">{{ "{:,}".format(counts.generated) }}</div>
      </div>
      <div class="stat">
        <div class="label">After cleaning</div>
        <div class="value">{{ "{:,}".format(counts.clean) }}</div>
      </div>
      <div class="stat">
        <div class="label">Dropped</div>
        <div class="value">{{ "{:,}".format(counts.dropped) }}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Processing time</h2>
    {% set tmax = timings.values()|max %}
    <table>
      <thead>
        <tr><th>Step</th><th class="num">Seconds</th><th>Share</th></tr>
      </thead>
      <tbody>
      {% for stage, secs in timings.items() %}
        <tr>
          <td>{{ stage }}</td>
          <td class="num">{{ "%.2f"|format(secs) }}</td>
          <td><span class="timing-bar" style="width: {{ (secs / tmax * 240)|round(0) }}px"></span></td>
        </tr>
      {% endfor %}
      </tbody>
      <tfoot>
        <tr>
          <td>Total</td>
          <td class="num">{{ "%.2f"|format(timings.values()|sum) }}</td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>

  <div class="card">
    <h2>Visualizations</h2>
    <div class="plots-grid">
      {% for p in plots %}
        <div class="plot">
          <img src="data:image/png;base64,{{ p.data }}" alt="{{ p.title }}">
          <div class="caption">{{ p.title }}</div>
        </div>
      {% endfor %}
    </div>
  </div>

  <div class="card">
    <h2>Revenue by category</h2>
    <table>
      <thead><tr><th>Category</th><th class="num">Revenue (USD)</th></tr></thead>
      <tbody>
      {% for row in by_category %}
        <tr><td>{{ row.product_category }}</td><td class="num">${{ "{:,.2f}".format(row.revenue) }}</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Top 10 products</h2>
    <table>
      <thead><tr><th>Product</th><th class="num">Revenue (USD)</th><th class="num">Units sold</th></tr></thead>
      <tbody>
      {% for _, row in top_products.iterrows() %}
        <tr>
          <td>{{ row.product_name }}</td>
          <td class="num">${{ "{:,.2f}".format(row.revenue) }}</td>
          <td class="num">{{ "{:,}".format(row.units_sold) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Per-category statistics</h2>
    <div class="section-note">Amounts in USD. "Count" is the number of transactions.</div>
    <table>
      <thead>
        <tr>
          <th>Category</th><th class="num">Count</th><th class="num">Mean</th>
          <th class="num">Median</th><th class="num">Std</th><th class="num">P95</th><th class="num">Sum</th>
        </tr>
      </thead>
      <tbody>
      {% for row in category_stats %}
        <tr>
          <td>{{ row.product_category }}</td>
          <td class="num">{{ "{:,}".format(row["count"]) }}</td>
          <td class="num">${{ "{:,.2f}".format(row["mean"]) }}</td>
          <td class="num">${{ "{:,.2f}".format(row["median"]) }}</td>
          <td class="num">${{ "{:,.2f}".format(row["std"]) }}</td>
          <td class="num">${{ "{:,.2f}".format(row["p95"]) }}</td>
          <td class="num">${{ "{:,.2f}".format(row["sum"]) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Payment-method breakdown</h2>
    <table>
      <thead>
        <tr><th>Method</th><th class="num">Transactions</th><th class="num">Revenue (USD)</th><th class="num">Avg order (USD)</th></tr>
      </thead>
      <tbody>
      {% for row in payment_stats %}
        <tr>
          <td>{{ row.payment_method }}</td>
          <td class="num">{{ "{:,}".format(row.transactions) }}</td>
          <td class="num">${{ "{:,.2f}".format(row.revenue) }}</td>
          <td class="num">${{ "{:,.2f}".format(row.avg_order) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Conclusions</h2>
    <ul class="conclusions">
      {% for c in conclusions %}
        <li>{{ c }}</li>
      {% endfor %}
    </ul>
  </div>

</div>
</body>
</html>
""")


def _embed_png(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _derive_conclusions(spark_results: dict, ray_results: dict, counts: dict) -> list[str]:
    out = []
    overall = spark_results["overall"]

    top = spark_results["top_products"].iloc[0]
    out.append(
        f"Top-selling product by revenue is '{top.product_name}' with "
        f"${top.revenue:,.2f} USD across {int(top.units_sold):,} units sold."
    )

    by_cat = spark_results["by_category"]
    if by_cat:
        best = by_cat[0]
        total_rev = overall["total_revenue"]
        share = best["revenue"] / total_rev * 100 if total_rev else 0
        out.append(
            f"'{best['product_category']}' is the strongest category, contributing "
            f"${best['revenue']:,.2f} USD ({share:.1f}% of total revenue)."
        )

    by_region = spark_results["by_region"]
    if not by_region.empty:
        r = by_region.iloc[0]
        out.append(
            f"Region '{r.region}' leads in revenue (${r.revenue:,.2f} USD)."
        )

    monthly = spark_results["monthly"]
    if len(monthly) >= 2:
        first, last = monthly.iloc[0], monthly.iloc[-1]
        delta = last.revenue - first.revenue
        trend = "upward" if delta > 0 else "downward"
        out.append(
            f"Revenue trend from {first.year_month} to {last.year_month} is {trend} "
            f"(Δ = ${delta:,.2f} USD)."
        )

    payment = ray_results["payment_stats"]
    if payment:
        best_pm = payment[0]
        out.append(
            f"Preferred payment method by revenue is '{best_pm['payment_method']}' "
            f"(${best_pm['revenue']:,.2f} USD across {best_pm['transactions']:,} transactions)."
        )

    out.append(
        f"{counts['clean']:,} clean transactions were analysed."
    )
    return out


PLOT_TITLES = {
    "01_monthly_trend":        "Monthly revenue trend",
    "02_top_products":         "Top 10 products by revenue",
    "03_revenue_by_category":  "Revenue share by category",
    "04_revenue_by_region":    "Revenue by region",
    "05_weekday_hour_heatmap": "Transactions by weekday and hour",
}


def _period_label(monthly) -> str:
    if monthly is None or len(monthly) == 0:
        return ""
    first = str(monthly.iloc[0]["year_month"])
    last = str(monthly.iloc[-1]["year_month"])
    return f"{first} to {last}"


def build_report(
    spark_results: dict,
    ray_results: dict,
    counts: dict,
    timings: dict,
    plot_paths: list[str],
    out_html: Path,
) -> list[str]:
    plots = []
    for p in plot_paths:
        path = Path(p)
        plots.append({
            "title": PLOT_TITLES.get(path.stem, path.stem.replace("_", " ")),
            "data": _embed_png(path),
        })

    conclusions = _derive_conclusions(spark_results, ray_results, counts)

    html = TEMPLATE.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        period_label=_period_label(spark_results.get("monthly")),
        timings=timings,
        counts=counts,
        overall=spark_results["overall"],
        by_category=spark_results["by_category"],
        top_products=spark_results["top_products"],
        category_stats=ray_results["category_stats"],
        payment_stats=ray_results["payment_stats"],
        plots=plots,
        conclusions=conclusions,
    )
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    return conclusions


def print_console_summary(
    spark_results: dict,
    counts: dict,
    timings: dict,
    conclusions: list[str],
):
    overall = spark_results["overall"]
    print("\n" + "=" * 70)
    print("RETAILLENS — DESCRIPTIVE ANALYTICS CONSOLE SUMMARY")
    print("=" * 70)
    print(f"Generated rows (Faker):    {counts['generated']:,}")
    print(f"Clean rows (Dask ETL):     {counts['clean']:,}")
    print(f"Rows dropped:              {counts['dropped']:,}")
    print(f"Dask partitions:           {counts['partitions']}")
    print(f"Spark rows processed:      {counts['spark_rows']:,}")
    print(f"Ray parallel tasks:        {counts['ray_tasks']}")
    print("-" * 70)
    print(f"Total revenue:             ${overall['total_revenue']:,.2f} USD")
    print(f"Average order value:       ${overall['avg_order_value']:,.2f} USD")
    print(f"Unique customers:          {overall['unique_customers']:,}")
    print(f"Unique products:           {overall['unique_products']:,}")
    print("-" * 70)
    print("Stage timings:")
    for stage, secs in timings.items():
        print(f"  {stage:<30s} {secs:>8.2f}s")
    print(f"  {'TOTAL':<30s} {sum(timings.values()):>8.2f}s")
    print("-" * 70)
    print("Conclusions:")
    for c in conclusions:
        print(f"  • {c}")
    print("=" * 70 + "\n")
