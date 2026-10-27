-- Copy each query into a separate Metabase SQL question.

-- KPI: completed-order revenue
SELECT SUM(revenue) AS total_revenue
FROM vw_monthly_sales;

-- KPI: completed orders
SELECT SUM(completed_orders) AS completed_orders
FROM vw_monthly_sales;

-- KPI: average order value across the selected period
SELECT
    ROUND(
        SUM(revenue) / NULLIF(SUM(completed_orders), 0),
        2
    ) AS average_order_value
FROM vw_monthly_sales;

-- Trend: monthly revenue and completed orders
SELECT
    sales_month,
    revenue,
    completed_orders,
    average_order_value
FROM vw_monthly_sales
ORDER BY sales_month;

-- Breakdown: revenue by product category
SELECT
    category_name,
    SUM(revenue) AS revenue
FROM vw_product_performance
GROUP BY category_name
ORDER BY revenue DESC;

-- Ranking: top 10 products by completed-order revenue
SELECT
    product_name,
    category_name,
    units_sold,
    revenue
FROM vw_product_performance
ORDER BY revenue DESC
LIMIT 10;

-- Breakdown: revenue by customer country
SELECT
    country,
    SUM(total_revenue) AS revenue,
    SUM(completed_orders) AS completed_orders
FROM vw_customer_summary
GROUP BY country
ORDER BY revenue DESC;
