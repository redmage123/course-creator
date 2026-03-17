-- Migration 010: Add separate first_name, last_name, and organization fields to users table
-- Improves data structure for better user management and reporting

-- Add new columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS organization VARCHAR(255);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_users_first_name ON users (first_name);
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users (last_name);
CREATE INDEX IF NOT EXISTS idx_users_organization ON users (organization);

-- Migrate existing full_name data to first_name/last_name where possible
-- This attempts to split full_name on first space
UPDATE users 
SET 
    first_name = CASE 
        WHEN position(' ' in full_name) > 0 
        THEN trim(substring(full_name from 1 for position(' ' in full_name) - 1))
        ELSE full_name
    END,
    last_name = CASE 
        WHEN position(' ' in full_name) > 0 
        THEN trim(substring(full_name from position(' ' in full_name) + 1))
        ELSE NULL
    END
WHERE full_name IS NOT NULL 
AND (first_name IS NULL OR last_name IS NULL);

-- Add comments for documentation
COMMENT ON COLUMN users.first_name IS 'User first name for personalized communication and reporting';
COMMENT ON COLUMN users.last_name IS 'User last name for personalized communication and reporting';
COMMENT ON COLUMN users.organization IS 'User organization or institution for institutional reporting and analytics';

-- Note: We keep full_name for backward compatibility, but new registrations should populate first_name/last_name
-- The application can generate full_name from first_name + last_name when needed