-- Migration 019: Add site_admin role and update admin user
--
-- BUSINESS CONTEXT:
-- The platform needs a distinct site_admin role separate from organization_admin.
-- Site admins have platform-wide access, while organization admins only manage
-- their specific organization.
--
-- TECHNICAL IMPLEMENTATION:
-- 1. Add CHECK constraint to enforce valid roles
-- 2. Update admin user to have site_admin role
-- 3. Document role hierarchy

-- Step 1: Add CHECK constraint for valid roles (if not exists)
-- Note: We drop existing constraint first if it exists with wrong values
DO $$
BEGIN
    -- Drop old constraint if exists
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_role_check'
        AND conrelid = 'course_creator.users'::regclass
    ) THEN
        ALTER TABLE course_creator.users DROP CONSTRAINT users_role_check;
        RAISE NOTICE 'Dropped existing role check constraint';
    END IF;

    -- Add new constraint with site_admin included
    ALTER TABLE course_creator.users
    ADD CONSTRAINT users_role_check
    CHECK (role IN ('student', 'instructor', 'organization_admin', 'site_admin'));

    RAISE NOTICE 'Added role check constraint with site_admin';
END $$;

-- Step 2: Update admin user to have site_admin role
UPDATE course_creator.users
SET role = 'site_admin'
WHERE username = 'admin'
AND email = 'admin@finallyworkinguniversity.edu';

-- Step 3: Add comment documenting the role hierarchy
COMMENT ON COLUMN course_creator.users.role IS
'User role: student (basic access), instructor (course management), organization_admin (organization management), site_admin (platform-wide administration)';

-- Verify the changes
DO $$
DECLARE
    admin_role VARCHAR(50);
BEGIN
    SELECT role INTO admin_role
    FROM course_creator.users
    WHERE username = 'admin';

    IF admin_role = 'site_admin' THEN
        RAISE NOTICE 'SUCCESS: Admin user now has site_admin role';
    ELSE
        RAISE WARNING 'FAILED: Admin user role is % instead of site_admin', admin_role;
    END IF;
END $$;
