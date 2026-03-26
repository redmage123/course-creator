-- Migration 033: Add Stripe Price/Product ID columns to subscription_plans
-- Required for Stripe subscriptions — the provider needs a price_xxx ID, not a local UUID.
-- Run: docker exec course-creator-postgres-1 psql -U postgres course_creator -f /migrations/033_stripe_price_ids.sql

ALTER TABLE course_creator.subscription_plans
    ADD COLUMN IF NOT EXISTS stripe_price_id   VARCHAR(255),
    ADD COLUMN IF NOT EXISTS stripe_product_id VARCHAR(255);

COMMENT ON COLUMN course_creator.subscription_plans.stripe_price_id   IS 'Stripe Price ID (price_xxx) — required for Stripe subscription creation';
COMMENT ON COLUMN course_creator.subscription_plans.stripe_product_id IS 'Stripe Product ID (prod_xxx) — parent product in Stripe Dashboard';

-- Index for fast lookup when resolving plan → Stripe price
CREATE INDEX IF NOT EXISTS idx_subscription_plans_stripe_price
    ON course_creator.subscription_plans(stripe_price_id)
    WHERE stripe_price_id IS NOT NULL;
