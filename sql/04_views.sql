-- E-commerce Sales & Customer Analytics
-- Step 4: Reusable analytics views
--
-- Run from the repository root:
-- docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/04_views.sql
--
-- These views do not modify source rows. They provide reusable query logic
-- for analysis and later use as datasets in Apache Superset.
--
-- Metric rule: primary sales metrics include completed orders only.
-- Revenue uses order_items.unit_price, the price recorded on the transaction.

\echo '=== Creating vw_completed_order_sales ==='

CREATE OR REPLACE VIEW vw_completed_order_sales AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    SUM(oi.quantity * oi.unit_price) AS order_revenue
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY
    o.order_id,
    o.customer_id,
    o.order_date;

\echo '=== Creating vw_monthly_sales ==='

CREATE OR REPLACE VIEW vw_monthly_sales AS
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    COUNT(*) AS completed_orders,
    SUM(order_revenue) AS revenue,
    ROUND(AVG(order_revenue), 2) AS average_order_value
FROM vw_completed_order_sales
GROUP BY DATE_TRUNC('month', order_date)::date;

\echo '=== Creating vw_product_performance ==='

CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    SUM(oi.quantity) AS units_sold,
    SUM(oi.quantity * oi.unit_price) AS revenue,
    COUNT(DISTINCT o.order_id) AS completed_orders
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.order_id
JOIN products AS p
    ON p.product_id = oi.product_id
JOIN categories AS c
    ON c.category_id = p.category_id
WHERE o.status = 'completed'
GROUP BY
    p.product_id,
    p.product_name,
    c.category_name;

\echo '=== Creating vw_customer_summary ==='

CREATE OR REPLACE VIEW vw_customer_summary AS
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country,
    c.signup_date,
    COUNT(s.order_id) AS completed_orders,
    COALESCE(SUM(s.order_revenue), 0) AS total_revenue,
    MAX(s.order_date) AS most_recent_completed_order
FROM customers AS c
LEFT JOIN vw_completed_order_sales AS s
    ON s.customer_id = c.customer_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country,
    c.signup_date;

\echo '=== Analytics views created successfully ==='
