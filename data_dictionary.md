# Data Dictionary — Synthetic E-Commerce Dataset

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
