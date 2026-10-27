CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL UNIQUE,
    category_id INTEGER NOT NULL,
    current_price NUMERIC(10,2) NOT NULL CHECK (current_price > 0),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('completed', 'cancelled', 'returned')),
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),
    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS meta_ads_insights (
    account_id VARCHAR(32) NOT NULL,
    campaign_id VARCHAR(64) NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    date_start DATE NOT NULL,
    date_stop DATE NOT NULL,
    impressions BIGINT NOT NULL CHECK (impressions >= 0),
    reach BIGINT NOT NULL CHECK (reach >= 0),
    clicks BIGINT NOT NULL CHECK (clicks >= 0),
    inline_link_clicks BIGINT NOT NULL CHECK (inline_link_clicks >= 0),
    spend NUMERIC(18,4) NOT NULL CHECK (spend >= 0),
    purchases NUMERIC(18,4) NOT NULL CHECK (purchases >= 0),
    purchase_conversion_value NUMERIC(18,4) NOT NULL
        CHECK (purchase_conversion_value >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id, campaign_id, date_start, date_stop),
    CHECK (date_start <= date_stop)
);