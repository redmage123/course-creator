-- Migration 012: Fix admin user and create instructor user bbrelin
-- Admin should be username: admin, password: admin123!
-- bbrelin should be instructor with proper details

-- First, remove any existing admin or bbrelin users to avoid conflicts
DELETE FROM users WHERE username IN ('admin', 'bbrelin');

-- Create proper admin user
-- Password hash for 'admin123!' using bcrypt
INSERT INTO users (
    id,
    email,
    username,
    full_name,
    first_name,
    last_name,
    organization,
    hashed_password,
    is_active,
    is_verified,
    role,
    created_at,
    updated_at
) VALUES (
    uuid_generate_v4(),
    'admin@course-creator.com',
    'admin',
    'System Administrator',
    'System',
    'Administrator',
    'Course Creator Platform',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- bcrypt hash for 'admin123!'
    true,
    true,
    'admin',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Create instructor user bbrelin with corrected email
INSERT INTO users (
    id,
    email,
    username,
    full_name,
    first_name,
    last_name,
    organization,
    hashed_password,
    is_active,
    is_verified,
    role,
    created_at,
    updated_at
) VALUES (
    uuid_generate_v4(),
    'bbrelin@gmail.com',
    'bbrelin',
    'Braun Brelin',
    'Braun',
    'Brelin',
    'AI Elevate',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- Using same hash temporarily - user should change password
    true,
    true,
    'instructor',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Add comment for documentation
COMMENT ON TABLE users IS 'Updated with correct admin user (admin/admin123!) and instructor user (bbrelin)';