-- Add the Meta Ads insights table to an existing database.
-- Safe to run after 01_schema.sql, which creates this table for new databases.

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
