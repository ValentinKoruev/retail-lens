"""Read the raw sales CSV, clean it, add calendar columns, write parquet."""

from pathlib import Path

import dask.dataframe as dd


def run_etl(csv_path: Path, parquet_path: Path) -> dict:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    ddf = dd.read_csv(
        csv_path,
        dtype={
            "transaction_id": "string",
            "customer_id": "string",
            "customer_name": "string",
            "customer_email": "string",
            "customer_city": "string",
            "customer_country": "string",
            "ip_address": "string",
            "product_category": "string",
            "product_name": "string",
            "payment_method": "string",
            "region": "string",
            "quantity": "int32",
            "unit_price": "float64",
            "total_amount": "float64",
        },
        parse_dates=["timestamp"],
        blocksize="8MB",
    )

    raw_count = int(ddf.shape[0].compute())

    ddf = ddf.dropna()
    ddf = ddf[(ddf["quantity"] > 0) & (ddf["unit_price"] > 0)]

    ddf["year"] = ddf["timestamp"].dt.year.astype("int16")
    ddf["month"] = ddf["timestamp"].dt.month.astype("int8")
    ddf["weekday"] = ddf["timestamp"].dt.weekday.astype("int8")
    ddf["hour"] = ddf["timestamp"].dt.hour.astype("int8")
    ddf["year_month"] = (
        ddf["year"].astype("string") + "-" + ddf["month"].astype("string").str.zfill(2)
    )

    if parquet_path.exists():
        import shutil
        shutil.rmtree(parquet_path)

    ddf.to_parquet(
        parquet_path,
        write_index=False,
        engine="pyarrow",
        coerce_timestamps="us",
        allow_truncated_timestamps=True,
    )

    clean_ddf = dd.read_parquet(parquet_path)
    clean_count = int(clean_ddf.shape[0].compute())
    n_partitions = clean_ddf.npartitions

    return {
        "raw_rows": raw_count,
        "clean_rows": clean_count,
        "dropped_rows": raw_count - clean_count,
        "partitions": n_partitions,
    }
