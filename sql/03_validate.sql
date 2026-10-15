-- E-commerce Sales & Customer Analytics
-- Step 3: Data validation
-- Run from the repository root:
-- docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/03_validate.sql
--
-- This script is read-only: it checks the loaded data and does not modify rows.
-- Expected row counts are based on the current synthetic dataset. Update these
-- expectations only if you intentionally regenerate the dataset.

\echo '=== 1. Table row counts ==='

SELECT 'categories' AS table_name, COUNT(*) AS row_count FROM categories
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
ORDER BY table_name;

\echo '=== 2. Compare row counts with expected dataset sizes ==='

WITH actual AS (
    SELECT 'categories' AS table_name, COUNT(*) AS actual_rows FROM categories
    UNION ALL SELECT 'products', COUNT(*) FROM products
    UNION ALL SELECT 'customers', COUNT(*) FROM customers
    UNION ALL SELECT 'orders', COUNT(*) FROM orders
    UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
),
expected(table_name, expected_rows) AS (
    VALUES
        ('categories', 10::bigint),
        ('products', 100::bigint),
        ('customers', 300::bigint),
        ('orders', 2000::bigint),
        ('order_items', 7027::bigint)
)
SELECT
    e.table_name,
    e.expected_rows,
    a.actual_rows,
    CASE WHEN e.expected_rows = a.actual_rows THEN 'PASS' ELSE 'CHECK' END AS result
FROM expected e
JOIN actual a USING (table_name)
ORDER BY e.table_name;

\echo '=== 3. Missing required values ==='

SELECT
    'customers.email' AS field,
    COUNT(*) FILTER (WHERE email IS NULL) AS missing_count
FROM customers
UNION ALL
SELECT 'orders.customer_id', COUNT(*) FILTER (WHERE customer_id IS NULL)
FROM orders
UNION ALL
SELECT 'orders.order_date', COUNT(*) FILTER (WHERE order_date IS NULL)
FROM orders
UNION ALL
SELECT 'orders.status', COUNT(*) FILTER (WHERE status IS NULL)
FROM orders
UNION ALL
SELECT 'order_items.order_id', COUNT(*) FILTER (WHERE order_id IS NULL)
FROM order_items
UNION ALL
SELECT 'order_items.product_id', COUNT(*) FILTER (WHERE product_id IS NULL)
FROM order_items
UNION ALL
SELECT 'order_items.quantity', COUNT(*) FILTER (WHERE quantity IS NULL)
FROM order_items
UNION ALL
SELECT 'order_items.unit_price', COUNT(*) FILTER (WHERE unit_price IS NULL)
FROM order_items
ORDER BY field;

\echo '=== 4. Duplicate business keys ==='

SELECT 'customers.email' AS key_name, email AS duplicate_value, COUNT(*) AS occurrences
FROM customers
GROUP BY email
HAVING COUNT(*) > 1
UNION ALL
SELECT 'products.product_name', product_name, COUNT(*)
FROM products
GROUP BY product_name
HAVING COUNT(*) > 1
ORDER BY key_name, duplicate_value;

\echo '=== 5. Orphaned relationships ==='

SELECT
    'orders_without_customer' AS check_name,
    COUNT(*) AS issue_count
FROM orders o
LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'order_items_without_order', COUNT(*)
FROM order_items oi
LEFT JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'order_items_without_product', COUNT(*)
FROM order_items oi
LEFT JOIN products p ON p.product_id = oi.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT 'products_without_category', COUNT(*)
FROM products p
LEFT JOIN categories c ON c.category_id = p.category_id
WHERE c.category_id IS NULL
ORDER BY check_name;

\echo '=== 6. Invalid business values ==='

SELECT 'invalid_order_status' AS check_name, COUNT(*) AS issue_count
FROM orders
WHERE status IS NULL OR status NOT IN ('completed', 'cancelled', 'returned')
UNION ALL
SELECT 'non_positive_quantity', COUNT(*)
FROM order_items
WHERE quantity IS NULL OR quantity <= 0
UNION ALL
SELECT 'non_positive_unit_price', COUNT(*)
FROM order_items
WHERE unit_price IS NULL OR unit_price <= 0
UNION ALL
SELECT 'products_with_non_positive_current_price', COUNT(*)
FROM products
WHERE current_price IS NULL OR current_price <= 0
ORDER BY check_name;

\echo '=== 7. Order status distribution ==='

SELECT status, COUNT(*) AS order_count
FROM orders
GROUP BY status
ORDER BY status;

\echo '=== Validation script finished ==='
