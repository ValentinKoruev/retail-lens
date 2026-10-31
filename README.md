# RetailLens

Descriptive analytics pipeline for a synthetic e-commerce transactions
dataset. Generates the data, cleans it, aggregates it, parallelises
per-segment statistics, plots the results and renders a self-contained
HTML report.

## Requirements

- Python 3.11+ (developed on 3.14)
- Java 11+ (needed by PySpark)
- ~2 GB free RAM for a 500k-row run

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

With the virtualenv active:

```bash
python main.py                   # default: 500,000 rows
python main.py --rows 1000000    # bigger dataset
python main.py --skip-generate   # reuse existing data/sales.csv
```

When you're done, `deactivate` leaves the virtualenv.

The run takes ~40–50 s for 500k rows on a modern laptop.

## Output

After a successful run:

- `output/report.html` — self-contained report with headline metrics,
  tables, visualisations and conclusions
- `output/plots/*.png` — the five charts, also embedded in the HTML
- Console summary with timings, counts and conclusions

Open the HTML in any browser:

```bash
xdg-open output/report.html     # Linux
open output/report.html         # macOS
```

## Project layout

```
.
├── main.py                 # orchestrator / CLI
├── requirements.txt
├── src/
│   ├── generate.py         # synthetic data generator
│   ├── etl_dask.py         # read CSV, clean, derive calendar columns, write parquet
│   ├── analyze_spark.py    # revenue aggregations, headline metrics
│   ├── compute_ray.py      # per-segment statistics, parallel
│   ├── visualize.py        # matplotlib / seaborn plots
│   ├── report.py           # HTML renderer + console summary
│   └── timing.py           # @timed context manager
├── data/                   # generated CSV / parquet (git-ignored)
└── output/
    ├── plots/              # PNG charts
    └── report.html
```

## Dataset schema

Fifteen columns per transaction: identifiers (`transaction_id`,
`customer_id`), customer profile (`customer_name`, `customer_email`,
`customer_city`, `customer_country`, `ip_address`), product
(`product_category`, `product_name`), order (`quantity`, `unit_price`,
`total_amount`, `payment_method`), geography (`region`) and `timestamp`.

Monetary values are in USD. Categories, products, regions, hours and
weekdays are drawn from weighted distributions so the data is non-uniform
(Electronics dominates; evenings and weekends are busier; etc.).

## CLI reference

```
main.py [--rows N] [--skip-generate]

  --rows N          number of transactions to generate (default 500000)
  --skip-generate   reuse an existing data/sales.csv
```
