COPY categories
FROM '/data/categories.csv'
WITH (FORMAT CSV, HEADER TRUE);

COPY products
FROM '/data/products.csv'
WITH (FORMAT CSV, HEADER TRUE);

COPY customers
FROM '/data/customers.csv'
WITH (FORMAT CSV, HEADER TRUE);

COPY orders
FROM '/data/orders.csv'
WITH (FORMAT CSV, HEADER TRUE);

COPY order_items
FROM '/data/order_items.csv'
WITH (FORMAT CSV, HEADER TRUE);