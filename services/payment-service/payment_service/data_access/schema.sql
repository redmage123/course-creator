-- Payment Service Database Schema
-- Run against the course_creator database within course_creator schema.
-- All tables use UUID primary keys and UTC timestamps to match platform conventions.

-- ============================================================================
-- 1. PAYMENT PROVIDERS — registered provider configurations
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.payment_providers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(50) UNIQUE NOT NULL,       -- e.g. 'null', 'stripe', 'square'
    display_name    VARCHAR(100) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    config          JSONB NOT NULL DEFAULT '{}',       -- provider-specific config (no secrets)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. SUBSCRIPTION PLANS — defines available tiers (Free, Pro, Enterprise)
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.subscription_plans (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(100) NOT NULL,
    description       TEXT NOT NULL DEFAULT '',
    price_cents       INTEGER NOT NULL DEFAULT 0,      -- stored in cents to avoid float
    currency          VARCHAR(3) NOT NULL DEFAULT 'USD',
    billing_interval  VARCHAR(20) NOT NULL DEFAULT 'monthly',
    features          JSONB NOT NULL DEFAULT '{}',     -- e.g. {"max_users": 10, "max_courses": 5}
    trial_days        INTEGER NOT NULL DEFAULT 0,
    sort_order        INTEGER NOT NULL DEFAULT 0,
    provider_name     VARCHAR(50) NOT NULL DEFAULT 'null' REFERENCES course_creator.payment_providers(name),
    is_active         BOOLEAN NOT NULL DEFAULT true,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscription_plans_active
    ON course_creator.subscription_plans(is_active) WHERE is_active = true;

-- ============================================================================
-- 3. SUBSCRIPTIONS — org-to-plan binding with lifecycle tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.subscriptions (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id           UUID NOT NULL,            -- FK to organizations table
    plan_id                   UUID NOT NULL REFERENCES course_creator.subscription_plans(id),
    status                    VARCHAR(20) NOT NULL DEFAULT 'trial',
    provider_name             VARCHAR(50) NOT NULL DEFAULT 'null' REFERENCES course_creator.payment_providers(name),
    provider_subscription_id  VARCHAR(255),             -- external provider reference
    current_period_start      TIMESTAMPTZ,
    current_period_end        TIMESTAMPTZ,
    trial_end                 TIMESTAMPTZ,
    cancelled_at              TIMESTAMPTZ,
    cancel_reason             TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_org
    ON course_creator.subscriptions(organization_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status
    ON course_creator.subscriptions(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_active_org
    ON course_creator.subscriptions(organization_id) WHERE status IN ('trial', 'active', 'past_due', 'paused');

-- ============================================================================
-- 4. INVOICES — billing documents
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.invoices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     UUID NOT NULL,
    subscription_id     UUID REFERENCES course_creator.subscriptions(id),
    invoice_number      VARCHAR(50) UNIQUE,
    amount_cents        INTEGER NOT NULL DEFAULT 0,
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    status              VARCHAR(20) NOT NULL DEFAULT 'draft',
    provider_invoice_id VARCHAR(255),
    issued_at           TIMESTAMPTZ,
    due_at              TIMESTAMPTZ,
    paid_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_org
    ON course_creator.invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoices_subscription
    ON course_creator.invoices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status
    ON course_creator.invoices(status);

-- ============================================================================
-- 5. INVOICE LINE ITEMS — individual charges on an invoice
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.invoice_line_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES course_creator.invoices(id) ON DELETE CASCADE,
    description     TEXT NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1,
    unit_price_cents INTEGER NOT NULL DEFAULT 0,
    amount_cents    INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoice_line_items_invoice
    ON course_creator.invoice_line_items(invoice_id);

-- ============================================================================
-- 6. TRANSACTIONS — actual money movements (payments and refunds)
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.transactions (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id           UUID NOT NULL,
    invoice_id                UUID REFERENCES course_creator.invoices(id),
    amount_cents              INTEGER NOT NULL,
    currency                  VARCHAR(3) NOT NULL DEFAULT 'USD',
    status                    VARCHAR(30) NOT NULL DEFAULT 'pending',
    provider_name             VARCHAR(50) NOT NULL DEFAULT 'null' REFERENCES course_creator.payment_providers(name),
    provider_transaction_id   VARCHAR(255),
    payment_method_id         UUID,                    -- FK added after payment_methods table
    refund_amount_cents       INTEGER NOT NULL DEFAULT 0,
    failure_reason            TEXT,
    metadata                  JSONB NOT NULL DEFAULT '{}',
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_org
    ON course_creator.transactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_transactions_invoice
    ON course_creator.transactions(invoice_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status
    ON course_creator.transactions(status);

-- ============================================================================
-- 7. PAYMENT METHODS — tokenized payment instruments per org
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.payment_methods (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    method_type     VARCHAR(30) NOT NULL DEFAULT 'platform_credit',
    provider_name   VARCHAR(50) NOT NULL DEFAULT 'null' REFERENCES course_creator.payment_providers(name),
    provider_token  VARCHAR(255),
    label           VARCHAR(100),
    last_four       VARCHAR(4),
    expiry_month    SMALLINT,
    expiry_year     SMALLINT,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_org
    ON course_creator.payment_methods(organization_id);

-- Add FK from transactions to payment_methods (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_transactions_payment_method'
    ) THEN
        ALTER TABLE course_creator.transactions
            ADD CONSTRAINT fk_transactions_payment_method
            FOREIGN KEY (payment_method_id) REFERENCES course_creator.payment_methods(id);
    END IF;
END $$;

-- ============================================================================
-- 8. PAYMENT AUDIT LOG — immutable audit trail for all payment mutations
-- ============================================================================
CREATE TABLE IF NOT EXISTS course_creator.payment_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50) NOT NULL,              -- 'subscription', 'invoice', 'transaction', etc.
    entity_id       UUID NOT NULL,
    action          VARCHAR(50) NOT NULL,              -- 'created', 'updated', 'cancelled', etc.
    actor_id        UUID,                              -- user who triggered the action (null for system)
    organization_id UUID,
    old_values      JSONB,
    new_values      JSONB,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_audit_entity
    ON course_creator.payment_audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_org
    ON course_creator.payment_audit_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_created
    ON course_creator.payment_audit_log(created_at);

-- ============================================================================
-- SEED DATA — NullProvider + Free plan
-- ============================================================================

-- Register the NullProvider (always available)
INSERT INTO course_creator.payment_providers (name, display_name, is_active, config)
VALUES ('null', 'Platform Credit (Free)', true, '{"description": "Built-in provider for free and trial plans"}')
ON CONFLICT (name) DO NOTHING;

-- Free plan (default for all new organizations)
INSERT INTO course_creator.subscription_plans (
    name, description, price_cents, currency, billing_interval,
    features, trial_days, sort_order, provider_name, is_active
) VALUES (
    'Free', 'Free tier with basic features', 0, 'USD', 'monthly',
    '{"max_users": 5, "max_courses": 3, "max_storage_gb": 1, "ai_assistant": false}',
    0, 0, 'null', true
) ON CONFLICT DO NOTHING;

-- Pro plan (placeholder — no real provider yet)
INSERT INTO course_creator.subscription_plans (
    name, description, price_cents, currency, billing_interval,
    features, trial_days, sort_order, provider_name, is_active
) VALUES (
    'Pro', 'Professional tier with advanced features', 4900, 'USD', 'monthly',
    '{"max_users": 50, "max_courses": 25, "max_storage_gb": 50, "ai_assistant": true}',
    14, 1, 'null', true
) ON CONFLICT DO NOTHING;

-- Enterprise plan (placeholder)
INSERT INTO course_creator.subscription_plans (
    name, description, price_cents, currency, billing_interval,
    features, trial_days, sort_order, provider_name, is_active
) VALUES (
    'Enterprise', 'Enterprise tier with unlimited features and dedicated support', 19900, 'USD', 'monthly',
    '{"max_users": -1, "max_courses": -1, "max_storage_gb": 500, "ai_assistant": true, "dedicated_support": true}',
    14, 2, 'null', true
) ON CONFLICT DO NOTHING;
