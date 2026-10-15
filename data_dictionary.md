# Data Dictionary-Synthetic E-Commerce Dataset

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
```

## SQL Tables

The SQL schema defines the following tables. Primary keys uniquely identify
rows, and foreign keys enforce the relationships shown above.

### `categories`

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `category_id` | INTEGER | Unique identifier for a product category. | Primary key |
| `category_name` | VARCHAR(100) | Name of the category. | Required; unique |

### `products`

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `product_id` | INTEGER | Unique identifier for a product. | Primary key |
| `product_name` | VARCHAR(200) | Product name. | Required; unique |
| `category_id` | INTEGER | Category to which the product belongs. | Required; foreign key to `categories.category_id` |
| `current_price` | NUMERIC(10,2) | Current product price. | Required; greater than 0 |
| `created_at` | TIMESTAMP | Date and time the product was created. | Required |

### `customers`

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `customer_id` | INTEGER | Unique identifier for a customer. | Primary key |
| `first_name` | VARCHAR(100) | Customer's first name. | Required |
| `last_name` | VARCHAR(100) | Customer's last name. | Required |
| `email` | VARCHAR(255) | Customer's email address. | Required; unique |
| `country` | VARCHAR(100) | Customer's country. | Required |
| `signup_date` | DATE | Date the customer signed up. | Required |

### `orders`

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `order_id` | INTEGER | Unique identifier for an order. | Primary key |
| `customer_id` | INTEGER | Customer who placed the order. | Required; foreign key to `customers.customer_id` |
| `order_date` | TIMESTAMP | Date and time the order was placed. | Required |
| `status` | VARCHAR(20) | Current order outcome. | Required; one of `completed`, `cancelled`, or `returned` |

### `order_items`

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `order_item_id` | INTEGER | Unique identifier for an order line item. | Primary key |
| `order_id` | INTEGER | Order containing this line item. | Required; foreign key to `orders.order_id` |
| `product_id` | INTEGER | Product included in this line item. | Required; foreign key to `products.product_id` |
| `quantity` | INTEGER | Number of units purchased. | Required; greater than 0 |
| `unit_price` | NUMERIC(10,2) | Price per unit recorded for this order item. | Required; greater than 0 |
