"""Synthetic e-commerce transaction generator.

Writes a CSV where categories, products, timestamps and payment methods
are drawn from non-uniform weighted distributions. Customer identities
come from a reusable Faker-generated pool so the same customer_id
always resolves to the same name/email/city/ip. Monetary values in USD.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

CATEGORIES = {
    "Electronics": ["Smartphone", "Laptop", "Headphones", "Tablet", "Smartwatch", "Camera"],
    "Clothing":    ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Hat"],
    "Home":        ["Lamp", "Chair", "Pillow", "Blanket", "Curtain", "Mug"],
    "Books":       ["Novel", "Textbook", "Comic", "Biography", "Cookbook"],
    "Sports":      ["Yoga Mat", "Dumbbell", "Running Shoes", "Bicycle", "Tennis Racket"],
    "Beauty":      ["Lipstick", "Perfume", "Shampoo", "Face Cream", "Nail Polish"],
}

# How often a category is picked (relative weights).
CATEGORY_WEIGHTS = {
    "Electronics": 32,
    "Clothing":    26,
    "Home":        14,
    "Beauty":      13,
    "Sports":       9,
    "Books":        6,
}

# Weights per product within each category — first product is the "hot seller".
PRODUCT_WEIGHTS = {
    "Electronics": [40, 25, 20, 15, 12, 8],
    "Clothing":    [35, 25, 18, 20, 10, 8],
    "Home":        [30, 10, 25, 22, 8, 20],
    "Books":       [40, 10, 25, 12, 18],
    "Sports":      [45, 20, 25, 6, 14],
    "Beauty":      [28, 20, 30, 14, 18],
}

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "crypto"]
PAYMENT_WEIGHTS = [45, 25, 18, 10, 2]

REGIONS = ["North", "South", "East", "West", "Central"]
REGION_WEIGHTS = [28, 20, 18, 22, 12]

COUNTRIES = ["BG", "DE", "FR", "IT", "ES", "GB", "US", "NL", "PL", "RO"]
COUNTRY_WEIGHTS = [8, 18, 14, 12, 10, 11, 14, 6, 4, 3]

# USD price ranges per category.
PRICE_RANGES = {
    "Electronics": (50, 2000),
    "Clothing":    (10, 300),
    "Home":        (5, 500),
    "Books":       (5, 80),
    "Sports":      (15, 1500),
    "Beauty":      (3, 150),
}

# Hour-of-day popularity (0..23). Night is quiet; late afternoon / evening peak.
HOUR_WEIGHTS = [
    1, 1, 1, 1, 1, 2,     # 00-05 night
    3, 5, 7, 9, 11, 12,   # 06-11 morning ramp
    12, 11, 10, 10, 11, 13,  # 12-17 afternoon
    15, 16, 14, 11, 7, 4,  # 18-23 evening peak then decline
]
HOURS = list(range(24))

# Day-of-week popularity (Mon..Sun). Weekends slightly busier.
WEEKDAY_WEIGHTS = [10, 10, 10, 11, 13, 16, 15]


def _pick_timestamp(start: datetime, days_span: int) -> datetime:
    """Pick a timestamp with weighted weekday and hour, uniform date within span."""
    while True:
        day_offset = random.randint(0, days_span - 1)
        candidate = start + timedelta(days=day_offset)
        wd_weight = WEEKDAY_WEIGHTS[candidate.weekday()]
        # rejection sample to bias toward higher-weight weekdays
        if random.random() * max(WEEKDAY_WEIGHTS) <= wd_weight:
            break
    hour = random.choices(HOURS, weights=HOUR_WEIGHTS, k=1)[0]
    return candidate.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )


def generate(n_rows: int, out_path: Path, chunk_size: int = 50_000, seed: int = 42) -> int:
    Faker.seed(seed)
    random.seed(seed)
    fake = Faker()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Pre-build the customer pool so repeat customer_ids keep the same identity,
    # and Faker is called once per customer rather than once per row.
    n_customers = max(1, n_rows // 10)
    customers: list[tuple[str, str, str, str]] = []
    for _ in range(n_customers):
        name = fake.name()
        email = fake.ascii_free_email()
        city = fake.city()
        ip = fake.ipv4()
        customers.append((name, email, city, ip))

    cat_list = list(CATEGORIES.keys())
    cat_weights = [CATEGORY_WEIGHTS[c] for c in cat_list]

    # Cover exactly 24 full calendar months ending at the last full month.
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_month_last_day = today.replace(day=1) - timedelta(days=1)
    end_date = end_month_last_day.replace(hour=23, minute=59, second=59)
    # Start on the 1st of a month 23 months before end_month -> 24 full months inclusive.
    year = end_month_last_day.year
    month = end_month_last_day.month - 23
    while month <= 0:
        month += 12
        year -= 1
    start_date = datetime(year, month, 1)
    days_span = (end_date.date() - start_date.date()).days + 1

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "transaction_id", "timestamp",
            "customer_id", "customer_name", "customer_email", "customer_city",
            "customer_country", "ip_address",
            "product_category", "product_name", "quantity", "unit_price",
            "total_amount", "payment_method", "region",
        ])

        rows_written = 0
        buffer: list[list] = []
        for i in range(1, n_rows + 1):
            category = random.choices(cat_list, weights=cat_weights, k=1)[0]
            products = CATEGORIES[category]
            product = random.choices(products, weights=PRODUCT_WEIGHTS[category], k=1)[0]

            low, high = PRICE_RANGES[category]
            unit_price = round(random.uniform(low, high), 2)
            quantity = random.choices([1, 2, 3, 4, 5], weights=[55, 25, 10, 6, 4])[0]
            total = round(unit_price * quantity, 2)

            ts = _pick_timestamp(start_date, days_span)

            cust_idx = random.randint(0, n_customers - 1)
            cust_name, cust_email, cust_city, cust_ip = customers[cust_idx]

            buffer.append([
                f"T{i:09d}",
                ts.isoformat(timespec="seconds"),
                f"C{cust_idx + 1:07d}",
                cust_name,
                cust_email,
                cust_city,
                random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS, k=1)[0],
                cust_ip,
                category,
                product,
                quantity,
                unit_price,
                total,
                random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0],
                random.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0],
            ])
            if len(buffer) >= chunk_size:
                writer.writerows(buffer)
                rows_written += len(buffer)
                buffer.clear()
        if buffer:
            writer.writerows(buffer)
            rows_written += len(buffer)

    return rows_written
