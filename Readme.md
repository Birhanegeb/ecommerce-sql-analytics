# E-commerce Sales & Customer Analytics

A reproducible PostgreSQL analytics project built from synthetic e-commerce transactions. It includes a Python data generator, a Docker Compose environment for PostgreSQL, pgAdmin and Apache Superset, SQL scripts for schema creation, loading, validation and reusable analytics views, and a sample dashboard screenshot.

## Project Contents

```text
ecommerce-sql-analytics/
|-- .env.example                 # Compose settings template; copy to .env
|-- Dockerfile.superset          # Superset image with the PostgreSQL driver
|-- docker-compose.yml           # PostgreSQL, pgAdmin and Superset services
|-- generate_dataset.py          # Reproducible CSV generator
|-- data_dictionary.md           # CSV fields, SQL columns and relationships
|-- ecommerce_business_challenge.pdf
|-- data/                        # Generated CSV files mounted into PostgreSQL
|-- sample_dashboards/           # Screenshot of a sample Superset dashboard
`-- sql/
    |-- 01_schema.sql            # Create relational tables
    |-- 02_load.sql              # Load CSV files with PostgreSQL COPY
    |-- 03_validate.sql          # Check row counts and data integrity
    `-- 04_views.sql             # Create analytics views for queries/Superset
```

## Data Model

The generator creates 10 categories, 100 products, 300 customers, 2,000 orders and 7,027 order items. The generated dataset is deterministic because the script uses a fixed random seed. Running it again replaces the CSV outputs and refreshes `data_dictionary.md`.

The five tables are related by primary and foreign keys:

```text
categories 1-to-many products 1-to-many order_items many-to-1 orders many-to-1 customers
```

The complete column definitions and constraints are in [data_dictionary.md](data_dictionary.md). Revenue views use the transaction-time `order_items.unit_price` and include completed orders only.

## Requirements

- Docker Engine or Docker Desktop with the Docker Compose v2 plugin (`docker compose`)
- Python 3 for generating the CSV files (the generator uses only the Python standard library)
- OpenSSL for creating a Superset secret key (`openssl`)

## Quick Start

Run commands from the project root.

### 1. Generate the dataset

```bash
python3 generate_dataset.py
```

This writes the five CSV files under `data/` and updates `data_dictionary.md`. The Docker Compose setup mounts `data/` into the PostgreSQL container at `/data`, which is where the SQL `COPY` commands read the files.

### 2. Configure credentials

Create your local environment file:

```bash
cp .env.example .env
```

Edit `.env` and set unique passwords for PostgreSQL, pgAdmin and Superset. Generate a strong Superset signing key with:

```bash
openssl rand -base64 42
```

Put the generated value in `SUPERSET_SECRET_KEY`. Keep `.env` private; it is ignored by Git. Do not use the example passwords in a shared or production environment. If a password contains reserved URL characters, URL-encode it when entering the Superset SQLAlchemy connection URI.

### 3. Validate and start the services

Check that Compose can read the configuration and required variables:

```bash
docker compose config
```

Build the local Superset image, then start PostgreSQL, pgAdmin and Superset in the background:

```bash
docker compose up -d --build
```

Check service state and published ports:

```bash
docker compose ps
```

Follow a service's startup logs when diagnosing startup or connection issues:

```bash
docker compose logs -f postgres
docker compose logs -f pgadmin
docker compose logs -f superset
```

Press `Ctrl+C` to stop following logs; this does not stop the containers.

| Service | URL / host connection | Host port | Container port |
|---|---|---:|---:|
| PostgreSQL | `localhost` from your computer; `postgres` from another Compose service | `5433` | `5432` |
| pgAdmin | <http://localhost:5050> | `5050` | `80` |
| Superset | <http://localhost:8090> | `8090` | `8088` |

The host PostgreSQL port is `5433` to avoid conflicts with a local PostgreSQL server on `5432`. Containers on the Compose network use the service name `postgres` and container port `5432` instead.

## Create and Load the Database

The following commands use the example database name `ecommerce` and user `user` from `.env.example`. If you changed `POSTGRES_DB` or `POSTGRES_USER`, replace those values in the commands. Run them from the project root.

### 4. Check PostgreSQL and mounted files

Confirm PostgreSQL is accepting connections:

```bash
docker compose exec postgres pg_isready -U user -d ecommerce
```

List files visible to PostgreSQL in the mounted `/data` directory:

```bash
docker compose exec postgres ls -lah /data
```

### 5. Create the tables

Send `01_schema.sql` to `psql` inside the PostgreSQL container. `-T` disables the pseudo-terminal so shell redirection supplies the SQL file on standard input, and `ON_ERROR_STOP` stops on the first SQL error.

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/01_schema.sql
```

### 6. Load CSV data

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/02_load.sql
```

The script uses server-side `COPY`, so the CSV paths are `/data/...` inside the container, not local paths. Run schema creation before loading. Loading the same files into already-populated tables will fail on duplicate primary keys; do not rerun it unless you intend to reload the data.

### 7. Validate the loaded data

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/03_validate.sql
```

This read-only script reports table counts, compares them with expected dataset sizes, checks missing values, duplicate business keys, orphaned foreign keys and invalid values, and prints the order-status distribution. Check that the count comparison says `PASS` and integrity checks report zero issues. The expected counts are for the current generated dataset.

### 8. Create reusable analytics views

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/04_views.sql
```

This creates or replaces four views without changing source rows:

| View | Purpose |
|---|---|
| `vw_completed_order_sales` | Revenue and date/customer details at completed-order grain |
| `vw_monthly_sales` | Monthly completed orders, revenue and average order value |
| `vw_product_performance` | Completed-order units sold and revenue by product/category |
| `vw_customer_summary` | Completed-order count, lifetime revenue and most recent order by customer |

List the views to confirm creation:

```bash
docker compose exec postgres psql -U user -d ecommerce -c "\\dv"
```

Try a small query against the monthly view:

```bash
docker compose exec postgres psql -U user -d ecommerce -c "SELECT * FROM vw_monthly_sales ORDER BY sales_month;"
```

Check that the customer summary includes all customers, including customers with no completed orders:

```bash
docker compose exec postgres psql -U user -d ecommerce -c "SELECT COUNT(*) AS customers FROM vw_customer_summary;"
```

## Connect with pgAdmin

1. Open <http://localhost:5050> and sign in with `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` from `.env`.
2. Register a server. Under **General**, choose a name such as `Ecommerce PostgreSQL`.
3. Under **Connection**, enter the following values, using your `.env` settings:

   | Setting | Value |
   |---|---|
   | Host name/address | `postgres` |
   | Port | `5432` |
   | Maintenance database | `ecommerce` (`POSTGRES_DB`) |
   | Username | `user` (`POSTGRES_USER`) |
   | Password | `POSTGRES_PASSWORD` |

Use `postgres:5432` in pgAdmin because pgAdmin runs in Docker on the same Compose network as PostgreSQL. `localhost:5433` is for clients running on your computer, not for the pgAdmin container.

## Connect Superset to PostgreSQL

### 1. Sign in

Open <http://localhost:8090>. Sign in with username `admin` and the `SUPERSET_ADMIN_PASSWORD` value from `.env`. The Compose startup command creates this account on initial setup. If the account already exists in the persistent Superset volume, changing `.env` does not change its existing password.

### 2. Add the PostgreSQL database

In Superset, open **Settings > Database Connections** (the menu may appear as **Data > Databases** in some versions), then choose **+ Database** or **Add Database** and select PostgreSQL. Enter a SQLAlchemy URI using your PostgreSQL credentials:

```text
postgresql+psycopg2://user:YOUR_POSTGRES_PASSWORD@postgres:5432/ecommerce
```

Replace `YOUR_POSTGRES_PASSWORD`, `user` and `ecommerce` with `POSTGRES_PASSWORD`, `POSTGRES_USER` and `POSTGRES_DB` from `.env`. If the password contains characters such as `@`, `/`, `:` or `#`, URL-encode the password before putting it in the URI. Keep the host as `postgres` and port as `5432`; Superset is another Compose service and must use the internal service address, not `localhost:5433`.

Use the UI's **Test Connection** action, then save the database connection. The project image installs `psycopg2-binary`, the PostgreSQL driver needed by Superset.

### 3. Add analytics views as datasets

After the connection is saved, create datasets from the `public` schema. Select `vw_monthly_sales`, `vw_product_performance`, `vw_customer_summary`, or `vw_completed_order_sales`. These views are the intended source for dashboard charts and metrics.

## Sample Dashboard

The screenshot below is a visual reference for a Superset dashboard with product revenue, customer revenue, and a total-revenue KPI.

![Sample e-commerce analytics dashboard](sample_dashboards/ecommerce-analysis-2026-10-17T12-15-50.616Z.jpg)

The repository currently contains the screenshot, not a Superset dashboard export. To build a working dashboard, create datasets from the analytics views above and configure the charts in Superset. The SQL views define sales metrics using completed orders only.

## Useful Commands

| Command | What it does |
|---|---|
| `python3 generate_dataset.py` | Generate or regenerate the CSV dataset and data dictionary. |
| `docker compose config` | Resolve and validate the Compose configuration and required environment variables; does not start containers. |
| `docker compose up -d --build` | Build the Superset image if needed and start all services in the background. |
| `docker compose ps` | Show service status and port mappings. |
| `docker compose logs -f superset` | Follow Superset logs for startup and database connection troubleshooting. |
| `docker compose exec postgres pg_isready -U user -d ecommerce` | Check whether PostgreSQL accepts connections. |
| `docker compose exec -T postgres psql ... < sql/FILE.sql` | Run a project SQL script inside the PostgreSQL container. Use the full commands in the steps above. |
| `docker compose down` | Stop and remove containers and the Compose network; named database volumes are retained. |
| `docker compose down -v` | Also delete named volumes, including PostgreSQL data and Superset state. This is destructive and resets persisted databases/accounts. |

To rebuild only Superset after changing `Dockerfile.superset`:

```bash
docker compose up -d --build superset
```

## Current Status

- [x] Reproducible synthetic dataset and data dictionary
- [x] PostgreSQL, pgAdmin and Superset Compose services
- [x] Relational schema and CSV loading scripts
- [x] Data validation script
- [x] Reusable analytics views
- [x] Sample Superset dashboard screenshot