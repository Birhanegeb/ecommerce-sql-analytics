-- Load and upsert the latest Meta Ads campaign insights CSV.
-- Run after extracting data with extract_meta_ads.py:
-- docker compose exec -T postgres psql -U user -d ecommerce -v ON_ERROR_STOP=1 < sql/06_load_meta_ads.sql

BEGIN;

CREATE TEMP TABLE meta_ads_insights_staging (
    LIKE public.meta_ads_insights INCLUDING DEFAULTS
) ON COMMIT DROP;

COPY meta_ads_insights_staging (
    account_id,
    campaign_id,
    campaign_name,
    date_start,
    date_stop,
    impressions,
    reach,
    clicks,
    inline_link_clicks,
    spend,
    purchases,
    purchase_conversion_value
)
FROM '/data/meta_ads_insights.csv'
WITH (FORMAT CSV, HEADER TRUE);

INSERT INTO public.meta_ads_insights (
    account_id,
    campaign_id,
    campaign_name,
    date_start,
    date_stop,
    impressions,
    reach,
    clicks,
    inline_link_clicks,
    spend,
    purchases,
    purchase_conversion_value
)
SELECT
    account_id,
    campaign_id,
    campaign_name,
    date_start,
    date_stop,
    impressions,
    reach,
    clicks,
    inline_link_clicks,
    spend,
    purchases,
    purchase_conversion_value
FROM meta_ads_insights_staging
ON CONFLICT (account_id, campaign_id, date_start, date_stop)
DO UPDATE SET
    campaign_name = EXCLUDED.campaign_name,
    impressions = EXCLUDED.impressions,
    reach = EXCLUDED.reach,
    clicks = EXCLUDED.clicks,
    inline_link_clicks = EXCLUDED.inline_link_clicks,
    spend = EXCLUDED.spend,
    purchases = EXCLUDED.purchases,
    purchase_conversion_value = EXCLUDED.purchase_conversion_value,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;
