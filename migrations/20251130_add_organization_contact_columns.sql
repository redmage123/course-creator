-- Migration: Add contact and address columns to organizations table
-- Date: 2025-11-30
-- Purpose: Support organization registration with full contact details

-- Add missing columns for organization contact information
ALTER TABLE course_creator.organizations
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS street_address VARCHAR(255),
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS state_province VARCHAR(100),
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS country VARCHAR(2) DEFAULT 'US',
ADD COLUMN IF NOT EXISTS address TEXT,
ADD COLUMN IF NOT EXISTS logo_url TEXT,
ADD COLUMN IF NOT EXISTS domain VARCHAR(255);

-- Add index on domain for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_domain ON course_creator.organizations(domain);

-- Add index on contact_email for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_contact_email ON course_creator.organizations(contact_email);
