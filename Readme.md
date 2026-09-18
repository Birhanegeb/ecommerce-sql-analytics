# E-commerce Sales & Customer Analytics

A PostgreSQL-based SQL analytics project using synthetic e-commerce transaction data. The project focuses on analyzing sales performance, customer purchasing behavior, product performance, and revenue trends using SQL.

## Problem Statement

An e-commerce company records its transactional data across several related tables, including **customers, orders, products, categories, and order items**. While the data captures individual purchases and customer activity, the raw transactional structure is not directly suitable for answering recurring business questions.

The goal of this project is to build a structured PostgreSQL dataset from the generated transactional data and develop a SQL analytics layer that can be used to investigate key areas of e-commerce performance:

* **Sales performance** — How much revenue is generated, and how does sales activity change over time?
* **Customer purchasing behavior** — Which customers purchase most frequently or generate the most revenue?
* **Product performance** — Which products and categories contribute most to sales?
* **Revenue trends** — How do revenue and order activity vary across different periods?

The analysis will use SQL techniques including:

* `JOIN`s to combine related transactional data
* `GROUP BY` and aggregate functions for business metrics
* `CTE`s for structuring multi-step analysis
* Subqueries for filtering and comparison
* Window functions for rankings, running totals, and period-based analysis

The project demonstrates how PostgreSQL can transform raw e-commerce transactions into structured analytical results that support recurring business questions and decision-making.

## Technology & Environment

The project uses a combination of local development tools and containerized database services.

| Component               | Technology     |
| ----------------------- | -------------- |
| Data generation         | Python 3       |
| Database                | PostgreSQL 16  |
| Database administration | pgAdmin 4      |
| Containerization        | Docker Compose |
| Data format             | CSV            |
| Query language          | SQL            |

The project runs **Python locally** to generate the synthetic dataset, while **PostgreSQL and pgAdmin run as Docker containers**.

```text
Local Machine
│
├── Python
│   └── generate_dataset.py
│       └── generates CSV files
│
└── Docker Compose
    │
    ├── PostgreSQL
    │   └── stores and queries the data
    │
    └── pgAdmin
        └── database administration and SQL execution
```

The generated `data/` directory is mounted into the PostgreSQL container so that PostgreSQL can load the CSV files using the `COPY` command.

PostgreSQL is exposed on host port `5433`, while pgAdmin is available on host port `5050`.

## Dataset

The project uses reproducible synthetic data generated with `generate_dataset.py`.

The dataset currently contains:

| Table         | Description                          |  Rows |
| ------------- | ------------------------------------ | ----: |
| `categories`  | Product categories                   |    10 |
| `products`    | Products and their categories        |   100 |
| `customers`   | Customer information                 |   300 |
| `orders`      | Customer orders and order status     | 2,000 |
| `order_items` | Products purchased within each order | 7,027 |

The tables are connected through primary and foreign-key relationships:

```text
categories
    │
    └── products
            │
            └── order_items
                    │
                    └── orders
                            │
                            └── customers
```

## Project Structure

```text
ecommerce-sql-analytics/
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
├── generate_dataset.py
├── data_dictionary.md
│
├── data/
│   ├── categories.csv
│   ├── products.csv
│   ├── customers.csv
│   ├── orders.csv
│   └── order_items.csv
│
└── sql/
    ├── 01_schema.sql
    └── 02_load.sql
```

## project Setup

The stages of the project covers:

1. Synthetic dataset generation
2. PostgreSQL database setup
3. Docker-based PostgreSQL and pgAdmin environment
4. Database schema creation
5. CSV data loading
6. Row-count verification
7. analytical SQL queries- Future works

## 1. Generate the Dataset

Generate the synthetic e-commerce data:

```bash
python3 generate_dataset.py
```

The script creates:

```text
data/
├── categories.csv
├── products.csv
├── customers.csv
├── orders.csv
└── order_items.csv
```

It also generates:

```text
data_dictionary.md
```

The dataset generation uses a fixed random seed to make the data reproducible.

```python
random.seed(42)
```

## 2. Configure Environment Variables

a local `.env` file:

```env
POSTGRES_DB=db_name
POSTGRES_USER=user_name
POSTGRES_PASSWORD=password

PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=password
```

## 3. Start PostgreSQL and pgAdmin

Start the services:

```bash
docker compose up -d
```

Check the containers:

```bash
docker compose ps
```

The project uses:

| Service    | Host Port | Container Port |
| ---------- | --------: | -------------: |
| PostgreSQL |    `5433` |         `5432` |
| pgAdmin    |    `5050` |           `80` |

PostgreSQL uses host port `5433` because another PostgreSQL instance is already using host port `5432`.

Open pgAdmin:

```text
http://localhost:5050
```

## 4. Verify PostgreSQL

Check that PostgreSQL is accepting connections:

```bash
docker exec ecommerce-postgres pg_isready -U user -d ecommerce
```

Expected:

```text
/var/run/postgresql:5432 - accepting connections
```

Verify that the CSV files are available inside the PostgreSQL container:

```bash
docker exec ecommerce-postgres ls -lah /data
```

Expected files:

```text
categories.csv
products.csv
customers.csv
orders.csv
order_items.csv
```

## 5. Connect PostgreSQL with pgAdmin

Open:

```text
http://localhost:5050
```

Log in using the credentials from `.env`.

Register a new server.

### General

```text
Name: Ecommerce PostgreSQL
```

### Connection

```text
Host name/address: postgres
Port: 5432
Maintenance database: ecommerce
Username: user
Password: password
```

> **Important:** When connecting from pgAdmin, use `postgres:5432`, not `localhost:5433`. pgAdmin runs inside Docker and connects to the PostgreSQL service through the Docker network.

## 6. Create the Database Schema

In pgAdmin:

1. Open the `ecommerce` database.
2. Open **Query Tool**.
3. Open `sql/01_schema.sql`.
4. Execute the script.

The script creates:

```text
categories
products
customers
orders
order_items
```

The schema uses primary keys and foreign keys to maintain relationships between the tables.

## 7. Load the CSV Data

After creating the tables, open:

```text
sql/02_load.sql
```

Execute the script in pgAdmin.

The data is loaded in dependency order:

```text
categories
    ↓
products
    ↓
customers
    ↓
orders
    ↓
order_items
```

The loading script uses PostgreSQL `COPY` to load the CSV files mounted into the PostgreSQL container at:

```text
/data/
```

## 8. Verify the Loaded Data

Run:

```sql
SELECT 'categories' AS table_name, COUNT(*) AS row_count
FROM categories

UNION ALL

SELECT 'products', COUNT(*)
FROM products

UNION ALL

SELECT 'customers', COUNT(*)
FROM customers

UNION ALL

SELECT 'orders', COUNT(*)
FROM orders

UNION ALL

SELECT 'order_items', COUNT(*)
FROM order_items;
```

Expected current row counts:

```text
categories     10
products       100
customers      300
orders         2000
order_items    7027
```

## Current Project Status

* [x] Synthetic e-commerce dataset generation
* [x] Reproducible data generation
* [x] PostgreSQL Docker setup
* [x] pgAdmin setup
* [x] Database connection
* [x] Relational schema creation
* [x] CSV data loading
* [x] Row-count verification
* [ ] Sales analysis queries
* [ ] Customer analysis queries
* [ ] Product and category analysis
* [ ] Revenue trend analysis
* [ ] Advanced SQL using CTEs, subqueries, and window functions
