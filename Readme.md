# E-commerce Sales & Customer Analytics

A reproducible PostgreSQL analytics project built from synthetic e-commerce transactions. It includes a Python data generator, a Docker Compose environment for PostgreSQL, pgAdmin, Apache Superset and optional Metabase, SQL scripts for schema creation, loading, validation and reusable analytics views, and a sample dashboard screenshot.

## Project Contents

```text
ecommerce-sql-analytics/
|-- .env.example                 # Compose settings template; copy to .env
|-- Dockerfile.superset          # Superset image with the PostgreSQL driver
|-- docker-compose.yml           # PostgreSQL, pgAdmin, Superset and optional Metabase
|-- metabase/
|   `-- synthetic_sales_dashboard.sql # Starter SQL questions for Metabase
|-- generate_dataset.py          # Reproducible CSV generator
|-- extract_meta_ads.py          # Meta Marketing API campaign-insights extractor
|-- data_dictionary.md           # CSV fields, SQL columns and relationships
|-- ecommerce_business_challenge.pdf
|-- data/                        # Generated CSV files mounted into PostgreSQL
|-- sample_dashboards/           # Screenshot of a sample Superset dashboard
`-- sql/
    |-- 01_schema.sql            # Create relational tables
    |-- 02_load.sql              # Load CSV files with PostgreSQL COPY
    |-- 03_validate.sql          # Check row counts and data integrity
    |-- 04_views.sql             # Create analytics views for queries/Superset
    |-- 05_meta_ads_schema.sql  # Add the Meta Ads table to an existing database
    `-- 06_load_meta_ads.sql    # Upsert extracted Meta Ads insights
```

## Data Model

The generator creates 10 categories, 100 products, 300 customers, 2,000 orders and 7,027 order items. The generated dataset is deterministic because the script uses a fixed random seed. Running it again replaces the CSV outputs and refreshes `data_dictionary.md`.

The five e-commerce tables are related by primary and foreign keys. Meta Ads
campaign-day insights are stored separately in `meta_ads_insights`; they are
not joined to orders because the synthetic order data has no ad attribution IDs.

```text
categories 1-to-many products 1-to-many order_items many-to-1 orders many-to-1 customers
```

The complete column definitions and constraints are in [data_dictionary.md](data_dictionary.md). Revenue views use the transaction-time `order_items.unit_price` and include completed orders only.

## Requirements

- Docker Engine or Docker Desktop with the Docker Compose v2 plugin (`docker compose`)
- Python 3 for generating the CSV files (the generator uses only the Python standard library)
- A Meta Marketing API access token with `ads_read` permission and access to the ad account (only for Meta Ads reporting)
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

Edit `.env` and set unique passwords for PostgreSQL, pgAdmin and Superset. For Meta Ads reporting, set `META_AD_ACCOUNT_ID`, `META_ACCESS_TOKEN`, and a currently supported `META_API_VERSION`. Keep the access token private; `.env` is ignored by Git. Generate a strong Superset signing key with:

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
| Metabase (optional profile) | <http://localhost:3000> | `3000` | `3000` |

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

### Optional: Extract and load Meta Ads campaign insights

The Meta Ads extract is an optional, separate step; the synthetic e-commerce
generator does not fabricate advertising results. Configure the three `META_*`
variables in `.env`, then export them in the shell running the extractor:

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/05_meta_ads_schema.sql
set -a
. ./.env
set +a
python3 extract_meta_ads.py --since 2026-01-01 --until 2026-01-31
```

The extractor requests daily campaign-level insights for the inclusive date
range and writes `data/meta_ads_insights.csv` by default. It follows API
pagination, writes the CSV atomically, and does not store the access token in
the output. Choose a Meta API version currently supported for your app. You
can override the output path with `--output`.

Load or refresh those rows in PostgreSQL:

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/06_load_meta_ads.sql
```

This upserts by account, campaign, and reporting dates, so rerunning an
extraction refreshes existing campaign-days without duplicating them. The
CSV must be in the mounted `data/` directory for PostgreSQL's server-side
`COPY` command to read it. The schema step is safe to run after `01_schema.sql`
on a new database and adds the table to an existing database without rerunning
the original non-idempotent schema script.

The extractor includes impressions, reach, clicks, inline link clicks, spend,
purchase count, and purchase conversion value. Purchase metrics are selected
from Meta's `actions` and `action_values` responses, preferring `omni_purchase`
and then the specific purchase action types; attribution and reported results
remain subject to the settings in the Meta Ads account.

### 7. Validate the loaded data

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/03_validate.sql
```

This read-only script reports table counts, compares the generated e-commerce tables with expected dataset sizes, checks missing values, duplicate business keys, orphaned foreign keys and invalid values, and prints the order-status distribution. Meta Ads row counts are account-dependent and are reported without a fixed expected count.

### 8. Create reusable analytics views

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/04_views.sql
```

This creates or replaces six views without changing source rows:

| View | Purpose |
|---|---|
| `vw_completed_order_sales` | Revenue and date/customer details at completed-order grain |
| `vw_monthly_sales` | Monthly completed orders, revenue and average order value |
| `vw_product_performance` | Completed-order units sold and revenue by product/category |
| `vw_customer_summary` | Completed-order count, lifetime revenue and most recent order by customer |
| `vw_meta_ads_campaign_daily` | Daily campaign metrics with CTR, CPC, CPM and purchase ROAS |
| `vw_meta_ads_campaign_monthly` | Monthly campaign totals and weighted CTR, CPC, CPM and purchase ROAS |

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

After the connection is saved, create datasets from the `public` schema. The
Meta Ads datasets are `vw_meta_ads_campaign_daily` and
`vw_meta_ads_campaign_monthly`; create charts for spend, impressions, clicks,
CTR, CPC, CPM, purchases, conversion value, and purchase ROAS from those
views. Reach is only available at daily grain because reach is not additive
across reporting days. E-commerce datasets remain available from
`vw_monthly_sales`, `vw_product_performance`, `vw_customer_summary`, and
`vw_completed_order_sales`.

## Metabase Dashboard, Just alternative to superset added for experinment

Metabase is an alternative dashboard service to Superset, not a replacement.
It runs only when its Compose profile is enabled and uses the existing
PostgreSQL database and completed-order analytics views. Generate and load
the synthetic dataset and create the views first.

Start Metabase without starting the other optional UI services:

```bash
docker compose --profile metabase up -d metabase
```

Open <http://localhost:3000> and complete Metabase's first-run account setup.
That account is separate from the Superset account. Metabase saves its
application setup and dashboard state in the persistent `metabase_data`
volume. The embedded application database is suitable for this local demo;
for production deployments, configure a dedicated supported PostgreSQL
application database for Metabase.

In the Metabase setup wizard (or **Admin settings > Databases > Add a
database**), connect to PostgreSQL using:

| Setting | Value |
|---|---|
| Database type | PostgreSQL |
| Display name | Ecommerce |
| Host | `postgres` |
| Port | `5432` |
| Database name | `POSTGRES_DB` from `.env` (default `ecommerce`) |
| Username | `POSTGRES_USER` from `.env` (default `user`) |
| Password | `POSTGRES_PASSWORD` from `.env` |

Use `postgres:5432`, the Docker network address; `localhost:5433` is only for
clients on the host computer. In the Metabase SQL editor, make a separate
question for each query in [metabase/synthetic_sales_dashboard.sql](metabase/synthetic_sales_dashboard.sql).
Choose a visualization for each question, save them, then add them to a new
dashboard named **E-commerce Sales Overview**:

- Show total revenue, completed orders, and average order value as **Number** cards.
- Show monthly revenue as a **Line** chart.
- Show revenue by category and customer country as **Bar** charts.
- Show the top 10 products as a **Table**.

The queries use completed orders only, consistent with the existing sales
views. Date-based filtering can be added to the monthly revenue question using
`sales_month`. To run Metabase alongside the full stack, use
`docker compose --profile metabase up -d --build`.

## Sample Dashboard

The screenshot below is a visual reference for a Superset dashboard with product revenue, customer revenue, and a total-revenue KPI.

![Sample e-commerce analytics dashboard](sample_dashboards/ecommerce-analysis-2026-10-17T12-15-50.616Z.jpg)

The repository currently contains a Superset dashboard export. 
## Useful Commands

| Command | What it does |
|---|---|
| `python3 generate_dataset.py` | Generate or regenerate the CSV dataset and data dictionary. |
| `python3 extract_meta_ads.py --since YYYY-MM-DD --until YYYY-MM-DD` | Fetch daily Meta campaign insights to `data/meta_ads_insights.csv`; requires the `META_*` environment variables. |
| `docker compose config` | Resolve and validate the Compose configuration and required environment variables; does not start containers. |
| `docker compose up -d --build` | Build the Superset image if needed and start all services in the background. |
| `docker compose --profile metabase up -d metabase` | Start the optional Metabase dashboard service and PostgreSQL dependency. |
| `docker compose logs -f metabase` | Follow Metabase startup and connection logs. |
| `docker compose ps` | Show service status and port mappings. |
| `docker compose logs -f superset` | Follow Superset logs for startup and database connection troubleshooting. |
| `docker compose exec postgres pg_isready -U user -d ecommerce` | Check whether PostgreSQL accepts connections. |
| `docker compose exec -T postgres psql ... < sql/FILE.sql` | Run a project SQL script inside the PostgreSQL container. Use the full commands in the steps above. |
| `docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/06_load_meta_ads.sql` | Upsert the extracted Meta Ads CSV into PostgreSQL. |
| `docker compose down` | Stop and remove containers and the Compose network; named database volumes are retained. |
| `docker compose down -v` | Also delete named volumes, including PostgreSQL data, Superset state and Metabase state. This is destructive and resets persisted databases/accounts. |

To rebuild only Superset after changing `Dockerfile.superset`:

```bash
docker compose up -d --build superset
```

To stop Metabase without affecting the other services:

```bash
docker compose stop metabase
```

## Current Status

- [x] Reproducible synthetic dataset and data dictionary
- [x] PostgreSQL, pgAdmin and Superset Compose services
- [x] Optional Metabase dashboard service and synthetic-sales starter queries
- [x] Relational schema and CSV loading scripts
- [x] Data validation script
- [x] Reusable analytics views
- [x] Meta Marketing API campaign-insights extraction and reporting views
- [x] Sample Superset dashboard screenshot