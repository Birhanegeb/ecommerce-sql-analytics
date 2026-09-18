"""
generate_dataset.py
Generates a synthetic e-commerce dataset:
  categories.csv, products.csv, customers.csv, orders.csv, order_items.csv
  data_dictionary.md
Validates all integrity constraints and prints a validation report.
"""

import csv
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict

random.seed(42)  # reproducible

# ---------------------------------------------------------------- config
N_CATEGORIES     = 10
N_PRODUCTS       = 100
N_CUSTOMERS      = 300
N_ORDERS         = 2000
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 6
TARGET_ORDER_ITEMS  = 5000   # aim 4000-6000

CUSTOMERS_WITHOUT_ORDERS = 22   # >= 20
PRODUCTS_WITHOUT_SALES   = 12   # >= 10

ORDER_START = datetime(2025, 1, 1, 8, 0, 0)
ORDER_END   = datetime(2026, 6, 30, 22, 0, 0)

COUNTRIES = ["Germany", "France", "Netherlands", "Belgium", "Spain",
             "Italy", "Austria", "Sweden", "Denmark", "Poland"]

STATUS_WEIGHTS = [("completed", 0.85), ("cancelled", 0.075), ("returned", 0.075)]

# ---------------------------------------------------------------- categories
CATEGORY_NAMES = [
    "Electronics", "Home & Kitchen", "Clothing", "Books", "Sports",
    "Beauty", "Toys", "Office", "Grocery", "Accessories",
]

categories = [(i + 1, name) for i, name in enumerate(CATEGORY_NAMES)]

# ---------------------------------------------------------------- products
# (name, category_id, base_price)
PRODUCT_TEMPLATES = [
    # Electronics (1)
    ("Wireless Keyboard", 1, 49.99), ("Bluetooth Headphones", 1, 89.00),
    ("Smart Watch", 1, 199.00), ("USB-C Charger", 1, 24.99),
    ("Portable Speaker", 1, 59.90), ("Noise-Cancelling Earbuds", 1, 129.00),
    ("4K Webcam", 1, 79.50), ("Mechanical Mouse", 1, 39.99),
    ("Power Bank 20000mAh", 1, 45.00), ("HDMI Cable 2m", 1, 12.99),
    # Home & Kitchen (2)
    ("Coffee Maker", 2, 69.99), ("Air Fryer", 2, 119.00),
    ("Blender 1.5L", 2, 54.90), ("Electric Kettle", 2, 34.99),
    ("Non-Stick Frying Pan", 2, 27.50), ("Dinner Plate Set", 2, 44.00),
    ("Vacuum Cleaner", 2, 189.00), ("Toaster 2-Slice", 2, 39.99),
    ("Knife Block Set", 2, 79.00), ("Food Storage Containers", 2, 22.99),
    # Clothing (3)
    ("Running Shoes", 3, 99.99), ("Cotton T-Shirt", 3, 19.99),
    ("Denim Jeans", 3, 59.90), ("Winter Jacket", 3, 149.00),
    ("Wool Socks 3-Pack", 3, 14.99), ("Baseball Cap", 3, 17.50),
    ("Leather Belt", 3, 29.99), ("Rain Jacket", 3, 89.00),
    ("Hoodie", 3, 45.00), ("Silk Scarf", 3, 35.00),
    # Books (4)
    ("Python Programming Book", 4, 39.99), ("SQL for Data Analysis", 4, 34.50),
    ("The Art of Clean Code", 4, 29.99), ("Data Science Handbook", 4, 49.00),
    ("Cookbook: European Cuisine", 4, 24.99), ("Fantasy Novel: The Lost Realm", 4, 15.99),
    ("History of Europe", 4, 27.50), ("Business Strategy Guide", 4, 31.00),
    ("Children's Picture Book", 4, 12.99), ("Travel Guide: Scandinavia", 4, 21.50),
    # Sports (5)
    ("Yoga Mat", 5, 29.99), ("Dumbbell Set 20kg", 5, 89.00),
    ("Cycling Helmet", 5, 59.90), ("Tennis Racket", 5, 79.99),
    ("Soccer Ball", 5, 24.99), ("Resistance Bands Set", 5, 19.99),
    ("Water Bottle 1L", 5, 14.50), ("Fitness Tracker", 5, 69.00),
    ("Jump Rope", 5, 12.99), ("Camping Tent 2-Person", 5, 129.00),
    # Beauty (6)
    ("Face Moisturizer", 6, 22.99), ("Shampoo 500ml", 6, 11.99),
    ("Perfume 50ml", 6, 69.00), ("Electric Toothbrush", 6, 49.99),
    ("Hair Dryer", 6, 39.90), ("Makeup Brush Set", 6, 24.50),
    ("Sunscreen SPF50", 6, 17.99), ("Beard Trimmer", 6, 44.00),
    ("Body Lotion", 6, 13.50), ("Nail Care Kit", 6, 19.99),
    # Toys (7)
    ("Building Blocks 500pcs", 7, 49.99), ("Remote Control Car", 7, 39.90),
    ("Puzzle 1000 Pieces", 7, 19.99), ("Board Game: Strategy", 7, 34.50),
    ("Plush Teddy Bear", 7, 24.99), ("Art Supplies Kit", 7, 29.00),
    ("Toy Train Set", 7, 59.90), ("Dollhouse", 7, 79.00),
    ("Science Experiment Kit", 7, 35.50), ("Outdoor Play Set", 7, 89.00),
    # Office (8)
    ("Office Chair", 8, 179.00), ("Desk Lamp", 8, 34.99),
    ("Standing Desk", 8, 299.00), ("Notebook A5", 8, 8.99),
    ("Ballpoint Pen Set", 8, 12.50), ("File Organizer", 8, 19.99),
    ("Monitor Stand", 8, 44.00), ("Whiteboard 60x90cm", 8, 54.90),
    ("Desk Organizer", 8, 24.99), ("Ergonomic Footrest", 8, 39.00),
    # Grocery (9)
    ("Organic Coffee Beans 1kg", 9, 19.99), ("Olive Oil 750ml", 9, 12.99),
    ("Pasta 500g", 9, 2.99), ("Dark Chocolate 200g", 9, 4.50),
    ("Green Tea 100 Bags", 9, 8.99), ("Honey 500g", 9, 9.50),
    ("Almonds 500g", 9, 11.99), ("Tomato Sauce 6-Pack", 9, 7.50),
    ("Breakfast Cereal", 9, 5.99), ("Sparkling Water 12-Pack", 9, 6.99),
    # Accessories (10)
    ("Backpack", 10, 59.99), ("Leather Wallet", 10, 34.90),
    ("Sunglasses", 10, 49.00), ("Umbrella", 10, 19.99),
    ("Travel Mug", 10, 22.50), ("Keychain Flashlight", 10, 9.99),
    ("Laptop Sleeve", 10, 29.00), ("Phone Case", 10, 14.99),
    ("Belt Bag", 10, 39.50), ("Watch Band", 10, 24.99),
]

assert len(PRODUCT_TEMPLATES) == N_PRODUCTS, len(PRODUCT_TEMPLATES)

# Build products: unique names, valid category, price > 0, created_at spread
product_created_base = datetime(2023, 1, 1)
products = []
seen_names = set()
for i, (name, cat_id, price) in enumerate(PRODUCT_TEMPLATES, start=1):
    assert name not in seen_names, name
    seen_names.add(name)
    # price variation +/- 15%
    final_price = round(price * random.uniform(0.85, 1.15), 2)
    final_price = max(final_price, 0.99)
    created = product_created_base + timedelta(
        days=random.randint(0, 900),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    products.append({
        "product_id": i,
        "product_name": name,
        "category_id": cat_id,
        "current_price": final_price,
        "created_at": created,
    })

# choose products with zero sales (spread across categories)
zero_sales_ids = set(random.sample([p["product_id"] for p in products],
                                   PRODUCTS_WITHOUT_SALES))

# ---------------------------------------------------------------- customers
FIRST_NAMES = [
    "Lukas", "Anna", "Sophie", "Maximilian", "Marie", "Jonas", "Laura",
    "Felix", "Julia", "Tim", "Lena", "David", "Sarah", "Niklas", "Emma",
    "Paul", "Hannah", "Leon", "Mia", "Ben", "Clara", "Finn", "Lea",
    "Elias", "Amelie", "Noah", "Ida", "Oskar", "Freya", "Matteo",
    "Chiara", "Luca", "Sofia", "Hugo", "Camille", "Louis", "Manon",
    "Jules", "Alice", "Gabriel", "Eva", "Thomas", "Nina", "Peter",
    "Katrin", "Stefan", "Sabine", "Andreas", "Monika", "Wolfgang",
    "Ingrid", "Jan", "Sanne", "Bram", "Femke", "Daan", "Lotte",
    "Pieter", "Anouk", "Ruben", "Elise", "Mathieu", "Céline",
    "Antoine", "Juliette", "Pierre", "Margaux", "Marta", "Pablo",
    "Lucía", "Javier", "Elena", "Giulia", "Marco", "Alessia",
    "Lorenzo", "Francesca", "Katarzyna", "Piotr", "Agnieszka",
    "Marek", "Astrid", "Erik", "Freja", "Magnus", "Signe",
]
LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
    "Wagner", "Becker", "Schulz", "Hoffmann", "Koch", "Richter",
    "Klein", "Wolf", "Schröder", "Neumann", "Braun", "Krüger",
    "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Krause",
    "Meier", "Lehmann", "Köhler", "Herrmann", "Walter", "König",
    "Mayer", "Huber", "Kaiser", "Fuchs", "Peters", "Lang",
    "Jansen", "de Vries", "van den Berg", "Bakker", "Visser",
    "Smit", "Meijer", "de Boer", "Mulder", "Dubois", "Lefebvre",
    "Moreau", "Laurent", "Simon", "Michel", "Garcia", "Martínez",
    "López", "Sánchez", "Rossi", "Russo", "Ferrari", "Esposito",
    "Bianchi", "Romano", "Nowak", "Kowalski", "Wiśniewski",
    "Wójcik", "Kamiński", "Lewandowski", "Andersson", "Johansson",
    "Karlsson", "Nilsson", "Eriksson", "Larsen", "Hansen",
    "Jensen", "Nielsen", "Pedersen",
]

EMAIL_DOMAINS = ["example.com", "example.org", "example.net"]

def make_unique_email(first, last, used):
    base = f"{first}.{last}".lower()
    base = (base.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
                .replace("ß", "ss").replace("é", "e").replace("è", "e")
                .replace("í", "i").replace("ó", "o").replace("á", "a")
                .replace("ś", "s").replace("ł", "l").replace("ż", "z")
                .replace("ź", "z").replace("ć", "c").replace("ń", "n")
                .replace(" ", ""))
    base = "".join(ch for ch in base if ch.isalnum() or ch in ".-_")
    domain = random.choice(EMAIL_DOMAINS)
    candidate = f"{base}@{domain}"
    n = 1
    while candidate in used:
        candidate = f"{base}{n}@{domain}"
        n += 1
    used.add(candidate)
    return candidate

signup_start = datetime(2023, 1, 1)
signup_end   = datetime(2026, 5, 31)

customers = []
used_emails = set()
for cid in range(1, N_CUSTOMERS + 1):
    first = random.choice(FIRST_NAMES)
    last  = random.choice(LAST_NAMES)
    email = make_unique_email(first, last, used_emails)
    country = random.choice(COUNTRIES)
    delta = signup_end - signup_start
    sd = signup_start + timedelta(
        days=random.randint(0, delta.days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    customers.append({
        "customer_id": cid,
        "first_name": first,
        "last_name": last,
        "email": email,
        "country": country,
        "signup_date": sd,
    })

# customers with no orders
no_order_customers = set(random.sample([c["customer_id"] for c in customers],
                                       CUSTOMERS_WITHOUT_ORDERS))
active_customers = [c for c in customers if c["customer_id"] not in no_order_customers]

# ---------------------------------------------------------------- orders
# Build a customer -> order count distribution with clear variation:
#   ~30% of active customers: 1 order
#   ~45%: 2-4 orders
#   ~20%: 5-10 orders
#   ~5%: 11-25 orders
def build_order_counts(active):
    n = len(active)
    counts = {}
    idx = 0
    random.shuffle(active)
    n_single = int(n * 0.30)
    n_low    = int(n * 0.45)
    n_mid    = int(n * 0.20)
    # remainder -> heavy
    for c in active[idx:idx + n_single]:
        counts[c["customer_id"]] = 1
    idx += n_single
    for c in active[idx:idx + n_low]:
        counts[c["customer_id"]] = random.randint(2, 4)
    idx += n_low
    for c in active[idx:idx + n_mid]:
        counts[c["customer_id"]] = random.randint(5, 10)
    idx += n_mid
    for c in active[idx:]:
        counts[c["customer_id"]] = random.randint(11, 25)
    return counts

order_counts = build_order_counts(active_customers)

# We need exactly N_ORDERS. Adjust counts to match.
def adjust_counts(counts, target):
    total = sum(counts.values())
    keys = list(counts.keys())
    while total > target:
        k = random.choice(keys)
        if counts[k] > 1:
            counts[k] -= 1
            total -= 1
    while total < target:
        k = random.choice(keys)
        counts[k] += 1
        total += 1
    return counts

order_counts = adjust_counts(order_counts, N_ORDERS)

# Expand to a list of customer_ids, then assign random dates per customer
customer_order_dates = {}
for cid, cnt in order_counts.items():
    # ensure each customer's orders are on different dates
    dates = set()
    while len(dates) < cnt:
        d = ORDER_START + timedelta(
            seconds=random.randint(0, int((ORDER_END - ORDER_START).total_seconds()))
        )
        # only keep unique calendar days per customer to guarantee LAG works
        dates.add(d.date())
    # convert to datetimes with random times of day
    dt_list = []
    for d in dates:
        dt = datetime(d.year, d.month, d.day,
                      random.randint(6, 23),
                      random.randint(0, 59),
                      random.randint(0, 59))
        dt_list.append(dt)
    dt_list.sort()
    customer_order_dates[cid] = dt_list

# Flatten and sort globally
all_orders_flat = []
for cid, dts in customer_order_dates.items():
    for dt in dts:
        all_orders_flat.append((cid, dt))
all_orders_flat.sort(key=lambda x: x[1])

# status assignment
def pick_status():
    r = random.random()
    acc = 0.0
    for s, w in STATUS_WEIGHTS:
        acc += w
        if r <= acc:
            return s
    return "completed"

orders = []
for oid, (cid, dt) in enumerate(all_orders_flat, start=1):
    orders.append({
        "order_id": oid,
        "customer_id": cid,
        "order_date": dt,
        "status": pick_status(),
    })

# ---------------------------------------------------------------- order_items
# Weighted product popularity: some sell a lot, some rarely.
available_products = [p for p in products if p["product_id"] not in zero_sales_ids]
# popularity weights (Zipf-ish)
weights = [1.0 / (i ** 0.7) for i in range(1, len(available_products) + 1)]
random.shuffle(weights)

product_by_id = {p["product_id"]: p for p in products}

order_items = []
item_id = 1
for order in orders:
    n_items = random.randint(MIN_ITEMS_PER_ORDER, MAX_ITEMS_PER_ORDER)
    chosen = set()
    attempts = 0
    while len(chosen) < n_items and attempts < 50:
        pid = random.choices([p["product_id"] for p in available_products],
                             weights=weights, k=1)[0]
        chosen.add(pid)
        attempts += 1
    for pid in chosen:
        prod = product_by_id[pid]
        base = prod["current_price"]
        # historical price: +/- 20% discount / change
        unit_price = round(base * random.uniform(0.80, 1.10), 2)
        unit_price = max(unit_price, 0.50)
        quantity = random.randint(1, 10)
        order_items.append({
            "order_item_id": item_id,
            "order_id": order["order_id"],
            "product_id": pid,
            "quantity": quantity,
            "unit_price": unit_price,
        })
        item_id += 1

# ---------------------------------------------------------------- write CSVs
def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

write_csv(
    "categories.csv",
    ["category_id", "category_name"],
    categories
)
write_csv("products.csv",
          ["product_id", "product_name", "category_id", "current_price", "created_at"],
          [(p["product_id"], p["product_name"], p["category_id"],
            f"{p['current_price']:.2f}",
            p["created_at"].strftime("%Y-%m-%d %H:%M:%S"))
           for p in products])

write_csv("customers.csv",
          ["customer_id", "first_name", "last_name", "email", "country", "signup_date"],
          [(c["customer_id"], c["first_name"], c["last_name"], c["email"],
            c["country"], c["signup_date"].strftime("%Y-%m-%d"))
           for c in customers])

write_csv("orders.csv",
          ["order_id", "customer_id", "order_date", "status"],
          [(o["order_id"], o["customer_id"],
            o["order_date"].strftime("%Y-%m-%d %H:%M:%S"), o["status"])
           for o in orders])

write_csv("order_items.csv",
          ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
          [(i["order_item_id"], i["order_id"], i["product_id"],
            i["quantity"], f"{i['unit_price']:.2f}")
           for i in order_items])

# ---------------------------------------------------------------- data dictionary
data_dict = """# Data Dictionary — Synthetic E-Commerce Dataset

This dataset models a small e-commerce business and is designed for SQL
analytics practice (aggregations, JOINs, GROUP BY/HAVING, window functions).

## Files

| File | Description |
|------|-------------|
| `categories.csv`  | Product categories (10 rows) |
| `products.csv`    | Products (100 rows) |
| `customers.csv`   | Customers (300 rows) |
| `orders.csv`      | Orders (~2000 rows) |
| `order_items.csv` | Line items per order (~5000 rows) |

## Relationships
```text
categories.category_id
        │
        │ 1:N
        ▼
products.category_id

products.product_id
        │
        │ 1:N
        ▼
order_items.product_id

orders.order_id
        │
        │ 1:N
        ▼
order_items.order_id

customers.customer_id
        │
        │ 1:N
        ▼
orders.customer_id
"""
with open("data_dictionary.md", "w", encoding="utf-8") as f:
    f.write(data_dict)
print("Generated data_dictionary.md")