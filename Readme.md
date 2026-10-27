# 🛒 E-commerce Sales & Customer Analytics

End-to-end SQL analytics project: **synthetic data → PostgreSQL → analytics views → Superset / Metabase dashboards**, fully reproducible with Docker.

![Sample dashboard](sample_dashboards/ecommerce-analysis-2026-10-17T12-15-50.616Z.png)

##  What This Project Demonstrates

- **Data generation**: deterministic Python generator (standard library only, fixed seed)
- **Data modeling**: 5 relational tables with PK/FK constraints
- **SQL engineering**: schema, loading (`COPY`), validation checks, reusable views
- **BI dashboards**: Apache Superset, plus Metabase as an alternative
- **API integration**: optional Meta Marketing API extractor for ad campaign insights
- **DevOps**: one-command Docker Compose stack (PostgreSQL, pgAdmin, Superset, Metabase)

##  Data Model

`categories → products → order_items ← orders ← customers`

| Entity | Rows |
|---|---|
| Categories | 10 |
| Products | 100 |
| Customers | 300 |
| Orders | 2,000 |
| Order items | 7,027 |

Revenue uses transaction-time `unit_price` and **completed orders only**. Full column definitions are in [`data_dictionary.md`](data_dictionary.md).

##  Quick Start

**Requirements:** Docker Compose v2, Python 3, OpenSSL

```bash
# 1. Generate data
python3 generate_dataset.py

# 2. Configure credentials (set passwords; SUPERSET_SECRET_KEY = openssl rand -base64 42)
cp .env.example .env

# 3. Start services
docker compose up -d --build

# 4. Create tables and load data
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/01_schema.sql
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/02_load.sql

# 5. Validate and create views
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/03_validate.sql
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/04_views.sql
```


| Service | URL |
|---|---|
| Superset | http://localhost:8090 |
| pgAdmin | http://localhost:5050 |
| Metabase (optional) | http://localhost:3000 |
| PostgreSQL | `localhost:5433` |

##  Analytics Views

| View | Purpose |
|---|---|
| `vw_completed_order_sales` | Revenue by order, date and customer |
| `vw_monthly_sales` | Monthly orders, revenue, average order value |
| `vw_product_performance` | Units sold and revenue by product/category |
| `vw_customer_summary` | Order count, lifetime revenue, last order |
| `vw_meta_ads_campaign_daily` | Daily CTR, CPC, CPM, purchase ROAS |
| `vw_meta_ads_campaign_monthly` | Monthly weighted ad metrics |

## Connect the Dashboards

**Superset:** Database Connections - PostgreSQL, then add the views as datasets:
```
postgresql+psycopg2://user:PASSWORD@postgres:5432/ecommerce (replace password from env)
```
**Metabase (optional):** `docker compose -profile metabase up -d metabase`. Connect to host `postgres`, port `5432`, then build the *E-commerce Sales Overview* dashboard from `metabase/synthetic_sales_dashboard.sql` (KPI cards, monthly revenue line, revenue by category and country, top 10 products).


##  Meta Ads Insights(just future work- ad integration)

Pulls daily campaign metrics (spend, impressions, clicks, purchases, ROAS) from the Meta Marketing API.

```bash
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/05_meta_ads_schema.sql
set -a; . ./.env; set +a      # needs META_AD_ACCOUNT_ID, META_ACCESS_TOKEN, META_API_VERSION
python3 extract_meta_ads.py --since 2026-01-01 --until 2026-01-31
docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/06_load_meta_ads.sql
```
Loads are **idempotent upserts**, so reruns never create duplicates.

## 📁 Project Structure

```
├── generate_dataset.py      # Data generator
├── extract_meta_ads.py      # Meta Ads API extractor
├── docker-compose.yml       # PostgreSQL, pgAdmin, Superset, Metabase
├── sql/                     # 01 schema · 02 load · 03 validate · 04 views · 05-06 Meta Ads
├── metabase/                # Starter dashboard queries
├── sample_dashboards/       # Dashboard screenshot / export
├── data/                    # Generated CSVs
└── data_dictionary.md
```

## 🧹 Useful Commands

```bash
docker compose ps            # service status
docker compose logs -f superset
docker compose down          # stop (data kept)
docker compose down -v       # stop and DELETE all volumes ⚠️
```

## ✅ Status

Synthetic dataset · SQL schema, validation and views · Superset and Metabase dashboards · Meta Ads extraction · Dockerized stack