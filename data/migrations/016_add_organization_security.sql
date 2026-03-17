-- Migration 016: Critical Multi-Tenant Security Fix
-- Adds organization_id to all core tables for proper tenant isolation
-- Date: 2025-08-05
-- Priority: CRITICAL SECURITY FIX

-- ================================
-- ADD ORGANIZATION_ID TO CORE TABLES
-- ================================

-- Users table - links users to their primary organization
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS primary_organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL;

-- Slides table - ensure slides belong to organization through course
ALTER TABLE slides 
ADD COLUMN IF NOT EXISTS organization_id UUID;

-- Update slides organization_id from courses
UPDATE slides 
SET organization_id = c.organization_id 
FROM courses c 
WHERE slides.course_id = c.id 
AND slides.organization_id IS NULL;

-- Make organization_id NOT NULL for slides
ALTER TABLE slides 
ALTER COLUMN organization_id SET NOT NULL,
ADD CONSTRAINT fk_slides_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Quiz attempts table - critical for student data isolation
ALTER TABLE quiz_attempts 
ADD COLUMN IF NOT EXISTS organization_id UUID;

-- Update quiz_attempts organization_id from course_instances
UPDATE quiz_attempts 
SET organization_id = c.organization_id 
FROM course_instances ci
JOIN courses c ON ci.course_id = c.id
WHERE quiz_attempts.course_instance_id = ci.id 
AND quiz_attempts.organization_id IS NULL;

-- Make organization_id NOT NULL for quiz_attempts
ALTER TABLE quiz_attempts 
ALTER COLUMN organization_id SET NOT NULL,
ADD CONSTRAINT fk_quiz_attempts_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Lab sessions table - ensure lab data is isolated by organization
ALTER TABLE lab_sessions 
ADD COLUMN IF NOT EXISTS organization_id UUID;

-- Update lab_sessions organization_id from courses
UPDATE lab_sessions 
SET organization_id = c.organization_id 
FROM courses c 
WHERE lab_sessions.course_id = c.id 
AND lab_sessions.organization_id IS NULL;

-- Make organization_id NOT NULL for lab_sessions
ALTER TABLE lab_sessions 
ALTER COLUMN organization_id SET NOT NULL,
ADD CONSTRAINT fk_lab_sessions_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Student course enrollments - critical for access control
ALTER TABLE student_course_enrollments 
ADD COLUMN IF NOT EXISTS organization_id UUID;

-- Update enrollments organization_id from course_instances
UPDATE student_course_enrollments 
SET organization_id = c.organization_id 
FROM course_instances ci
JOIN courses c ON ci.course_id = c.id
WHERE student_course_enrollments.course_instance_id = ci.id 
AND student_course_enrollments.organization_id IS NULL;

-- Make organization_id NOT NULL for enrollments
ALTER TABLE student_course_enrollments 
ALTER COLUMN organization_id SET NOT NULL,
ADD CONSTRAINT fk_enrollments_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Course instances table
ALTER TABLE course_instances 
ADD COLUMN IF NOT EXISTS organization_id UUID;

-- Update course_instances organization_id from courses
UPDATE course_instances 
SET organization_id = c.organization_id 
FROM courses c 
WHERE course_instances.course_id = c.id 
AND course_instances.organization_id IS NULL;

-- Make organization_id NOT NULL for course_instances
ALTER TABLE course_instances 
ALTER COLUMN organization_id SET NOT NULL,
ADD CONSTRAINT fk_course_instances_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- Quiz publications table
ALTER TABLE quiz_publications 
ADD COLUMN IF NOT EXISTS organization_id UUID;

-- Update quiz_publications organization_id from course_instances
UPDATE quiz_publications 
SET organization_id = ci.organization_id 
FROM course_instances ci
WHERE quiz_publications.course_instance_id = ci.id 
AND quiz_publications.organization_id IS NULL;

-- Make organization_id NOT NULL for quiz_publications
ALTER TABLE quiz_publications 
ALTER COLUMN organization_id SET NOT NULL,
ADD CONSTRAINT fk_quiz_publications_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- ================================
-- CREATE SECURITY INDEXES
-- ================================

-- Performance indexes for organization-based queries
CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_primary_organization ON users(primary_organization_id);
CREATE INDEX IF NOT EXISTS idx_slides_organization ON slides(organization_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_organization ON quiz_attempts(organization_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_organization ON lab_sessions(organization_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_organization ON student_course_enrollments(organization_id);
CREATE INDEX IF NOT EXISTS idx_course_instances_organization ON course_instances(organization_id);
CREATE INDEX IF NOT EXISTS idx_quiz_publications_organization ON quiz_publications(organization_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_slides_course_org ON slides(course_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student_org ON quiz_attempts(student_email, organization_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_user_org ON lab_sessions(user_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student_org ON student_course_enrollments(student_email, organization_id);

-- ================================
-- ROW LEVEL SECURITY POLICIES
-- ================================

-- Enable RLS on critical tables
ALTER TABLE slides ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE lab_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_course_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_publications ENABLE ROW LEVEL SECURITY;

-- Create RLS policies - slides
CREATE POLICY slides_organization_isolation ON slides
    FOR ALL TO course_user
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Create RLS policies - quiz_attempts
CREATE POLICY quiz_attempts_organization_isolation ON quiz_attempts
    FOR ALL TO course_user
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Create RLS policies - lab_sessions
CREATE POLICY lab_sessions_organization_isolation ON lab_sessions
    FOR ALL TO course_user
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Create RLS policies - enrollments
CREATE POLICY enrollments_organization_isolation ON student_course_enrollments
    FOR ALL TO course_user
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Create RLS policies - course_instances
CREATE POLICY course_instances_organization_isolation ON course_instances
    FOR ALL TO course_user
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- Create RLS policies - quiz_publications
CREATE POLICY quiz_publications_organization_isolation ON quiz_publications
    FOR ALL TO course_user
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- ================================
-- SECURITY FUNCTIONS
-- ================================

-- Function to set organization context for session
CREATE OR REPLACE FUNCTION set_organization_context(org_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', org_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current organization context
CREATE OR REPLACE FUNCTION get_organization_context()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to verify organization access
CREATE OR REPLACE FUNCTION verify_organization_access(user_id UUID, org_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    has_access BOOLEAN := FALSE;
BEGIN
    -- Check if user is member of the organization
    SELECT EXISTS(
        SELECT 1 FROM organization_memberships 
        WHERE user_id = verify_organization_access.user_id 
        AND organization_id = org_id 
        AND status = 'active'
    ) INTO has_access;
    
    RETURN has_access;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================
-- DATA INTEGRITY CHECKS
-- ================================

-- Verify all critical tables have organization_id
DO $$
DECLARE
    missing_org_id INTEGER := 0;
BEGIN
    -- Check slides
    SELECT COUNT(*) INTO missing_org_id FROM slides WHERE organization_id IS NULL;
    IF missing_org_id > 0 THEN
        RAISE EXCEPTION 'Security Error: % slides missing organization_id', missing_org_id;
    END IF;
    
    -- Check quiz_attempts
    SELECT COUNT(*) INTO missing_org_id FROM quiz_attempts WHERE organization_id IS NULL;
    IF missing_org_id > 0 THEN
        RAISE EXCEPTION 'Security Error: % quiz_attempts missing organization_id', missing_org_id;
    END IF;
    
    -- Check lab_sessions
    SELECT COUNT(*) INTO missing_org_id FROM lab_sessions WHERE organization_id IS NULL;
    IF missing_org_id > 0 THEN
        RAISE EXCEPTION 'Security Error: % lab_sessions missing organization_id', missing_org_id;
    END IF;
    
    -- Check enrollments
    SELECT COUNT(*) INTO missing_org_id FROM student_course_enrollments WHERE organization_id IS NULL;
    IF missing_org_id > 0 THEN
        RAISE EXCEPTION 'Security Error: % enrollments missing organization_id', missing_org_id;
    END IF;
    
    RAISE NOTICE 'Security migration completed successfully - all tables have organization isolation';
END $$;

-- Grant permissions for security functions
GRANT EXECUTE ON FUNCTION set_organization_context(UUID) TO course_user;
GRANT EXECUTE ON FUNCTION get_organization_context() TO course_user;
GRANT EXECUTE ON FUNCTION verify_organization_access(UUID, UUID) TO course_user;

-- Create security audit log
CREATE TABLE IF NOT EXISTS security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    organization_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    attempted_organization_id UUID,
    success BOOLEAN NOT NULL,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_security_audit_user ON security_audit_log(user_id);
CREATE INDEX idx_security_audit_org ON security_audit_log(organization_id);
CREATE INDEX idx_security_audit_action ON security_audit_log(action);
CREATE INDEX idx_security_audit_timestamp ON security_audit_log(created_at);

-- Security audit function
CREATE OR REPLACE FUNCTION log_security_event(
    p_user_id UUID,
    p_organization_id UUID,
    p_action VARCHAR(100),
    p_resource_type VARCHAR(50),
    p_resource_id UUID,
    p_attempted_organization_id UUID,
    p_success BOOLEAN,
    p_details JSONB DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO security_audit_log (
        user_id, organization_id, action, resource_type, resource_id,
        attempted_organization_id, success, details, ip_address, user_agent
    ) VALUES (
        p_user_id, p_organization_id, p_action, p_resource_type, p_resource_id,
        p_attempted_organization_id, p_success, p_details, p_ip_address, p_user_agent
    ) RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION log_security_event(UUID, UUID, VARCHAR, VARCHAR, UUID, UUID, BOOLEAN, JSONB, INET, TEXT) TO course_user;