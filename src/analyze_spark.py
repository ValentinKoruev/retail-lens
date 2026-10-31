"""Spark aggregations over the cleaned transactions dataset.

Returns monthly revenue, top products, revenue by region and headline
totals via the DataFrame API, plus revenue by category computed with an
RDD reduceByKey.
"""

from pathlib import Path

from pyspark.sql import SparkSession, functions as F


def run_analysis(parquet_path: Path) -> dict:
    spark = (
        SparkSession.builder
        .appName("RetailLens")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    df = spark.read.parquet(str(parquet_path))
    df.cache()
    total_rows = df.count()

    monthly = (
        df.groupBy("year_month")
          .agg(
              F.round(F.sum("total_amount"), 2).alias("revenue"),
              F.count("*").alias("transactions"),
          )
          .orderBy("year_month")
          .toPandas()
    )

    top_products = (
        df.groupBy("product_name")
          .agg(
              F.round(F.sum("total_amount"), 2).alias("revenue"),
              F.sum("quantity").alias("units_sold"),
          )
          .orderBy(F.col("revenue").desc())
          .limit(10)
          .toPandas()
    )

    by_region = (
        df.groupBy("region")
          .agg(F.round(F.sum("total_amount"), 2).alias("revenue"))
          .orderBy(F.col("revenue").desc())
          .toPandas()
    )

    # Revenue by category via RDD reduceByKey (map -> shuffle -> reduce).
    rdd = df.select("product_category", "total_amount").rdd
    mapped = rdd.map(lambda r: (r["product_category"], float(r["total_amount"])))
    reduced = mapped.reduceByKey(lambda a, b: a + b)
    category_revenue_pairs = reduced.collect()
    by_category = (
        [{"product_category": k, "revenue": round(v, 2)} for k, v in category_revenue_pairs]
    )
    by_category.sort(key=lambda d: d["revenue"], reverse=True)

    overall = df.agg(
        F.round(F.sum("total_amount"), 2).alias("total_revenue"),
        F.round(F.avg("total_amount"), 2).alias("avg_order_value"),
        F.countDistinct("customer_id").alias("unique_customers"),
        F.countDistinct("product_name").alias("unique_products"),
    ).toPandas().iloc[0].to_dict()

    spark.stop()

    return {
        "total_rows": int(total_rows),
        "overall": overall,
        "monthly": monthly,
        "top_products": top_products,
        "by_region": by_region,
        "by_category": by_category,
    }
