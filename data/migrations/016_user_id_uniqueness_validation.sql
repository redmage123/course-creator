-- Migration 016: User ID Uniqueness Validation Enhancement
-- Ensures robust user ID uniqueness constraints and custom ID support

-- =============================================================================
-- USER ID UNIQUENESS CONSTRAINTS
-- =============================================================================

-- The users table already has a PRIMARY KEY constraint on the id field which ensures
-- uniqueness. This migration documents and validates the constraint for custom user IDs.

-- Verify existing PRIMARY KEY constraint on users.id
-- PostgreSQL PRIMARY KEY automatically creates a UNIQUE constraint
DO $$
BEGIN
    -- Check if the primary key constraint exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE table_name = 'users' 
        AND constraint_type = 'PRIMARY KEY'
        AND table_schema = 'course_creator'
    ) THEN
        -- This should never happen, but add constraint if missing
        ALTER TABLE course_creator.users ADD CONSTRAINT users_pkey PRIMARY KEY (id);
        RAISE NOTICE 'Added PRIMARY KEY constraint to users.id';
    ELSE
        RAISE NOTICE 'PRIMARY KEY constraint on users.id already exists - user ID uniqueness is enforced';
    END IF;
END $$;

-- Add check constraint to ensure user IDs are valid UUIDs or custom strings
-- This allows both auto-generated UUIDs and custom user-specified IDs
ALTER TABLE course_creator.users 
ADD CONSTRAINT users_id_format_check 
CHECK (
    id IS NOT NULL AND 
    length(trim(id::text)) > 0 AND 
    length(trim(id::text)) <= 50
);

-- Create index for efficient user ID lookups (if not already exists from PRIMARY KEY)
-- PRIMARY KEY automatically creates an index, but this documents the intent
CREATE INDEX IF NOT EXISTS idx_users_id_lookup ON course_creator.users(id);

-- =============================================================================
-- ADDITIONAL USER TABLE ENHANCEMENTS FOR CUSTOM ID SUPPORT
-- =============================================================================

-- Add username field if it doesn't exist (for alternative authentication)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'username'
        AND table_schema = 'course_creator'
    ) THEN
        ALTER TABLE course_creator.users ADD COLUMN username VARCHAR(50) UNIQUE;
        RAISE NOTICE 'Added username column to users table';
    END IF;
END $$;

-- Add role field if it doesn't exist 
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'role'
        AND table_schema = 'course_creator'  
    ) THEN
        ALTER TABLE course_creator.users ADD COLUMN role VARCHAR(20) DEFAULT 'student' 
        CHECK (role IN ('student', 'instructor', 'org_admin', 'site_admin'));
        RAISE NOTICE 'Added role column to users table';
    END IF;
END $$;

-- Add additional profile fields if they don't exist
DO $$
BEGIN
    -- Add organization field
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'organization'
        AND table_schema = 'course_creator'
    ) THEN
        ALTER TABLE course_creator.users ADD COLUMN organization VARCHAR(255);
    END IF;
    
    -- Add status field  
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'status'
        AND table_schema = 'course_creator'
    ) THEN
        ALTER TABLE course_creator.users ADD COLUMN status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'pending', 'suspended'));
    END IF;
    
    -- Add updated_at field
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'updated_at'
        AND table_schema = 'course_creator'
    ) THEN
        ALTER TABLE course_creator.users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- Add last_login field
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'last_login'
        AND table_schema = 'course_creator'
    ) THEN
        ALTER TABLE course_creator.users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- =============================================================================
-- VALIDATION AND VERIFICATION
-- =============================================================================

-- Function to validate user ID uniqueness
CREATE OR REPLACE FUNCTION course_creator.validate_user_id_unique(user_id_to_check TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 FROM course_creator.users WHERE id::text = user_id_to_check
    );
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION course_creator.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_users_updated_at'
        AND event_object_table = 'users'
        AND trigger_schema = 'course_creator'
    ) THEN
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON course_creator.users
            FOR EACH ROW
            EXECUTE FUNCTION course_creator.update_updated_at_column();
        RAISE NOTICE 'Created updated_at trigger for users table';
    END IF;
END $$;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify table structure
\echo 'Users table structure after migration:';
\d course_creator.users;

-- Verify constraints
\echo 'User table constraints:';
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'course_creator.users'::regclass;

-- Test user ID uniqueness validation function
\echo 'Testing user ID uniqueness validation:';
SELECT 
    'test-id-123' as test_id,
    course_creator.validate_user_id_unique('test-id-123') as is_unique;

-- =============================================================================
-- MIGRATION COMPLETION
-- =============================================================================

\echo 'Migration 016 completed: User ID uniqueness validation enhanced';
\echo 'Features added:';
\echo '  - Verified PRIMARY KEY constraint ensures user ID uniqueness';
\echo '  - Added format validation for custom user IDs';
\echo '  - Enhanced user table with username, role, and profile fields';
\echo '  - Created validation function for user ID uniqueness checks';
\echo '  - Added automatic updated_at timestamp management';