-- Migration 013: Project-Based Organization Management System
-- Implements multi-tenant organization structure with projects and enhanced role management

-- Organizations table (replaces simple organization string)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- URL-friendly identifier
    description TEXT,
    logo_url VARCHAR(500),
    domain VARCHAR(255), -- Optional domain for email-based auto-assignment
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Projects table (containers for training programs)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL, -- URL-friendly identifier within org
    description TEXT,
    objectives TEXT[], -- Array of learning objectives
    target_roles TEXT[], -- e.g., ['Application Developer', 'Business Analyst', 'Operations Engineer']
    duration_weeks INTEGER,
    max_participants INTEGER,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, completed, archived
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, slug)
);

-- Enhanced roles enum
CREATE TYPE user_role AS ENUM (
    'super_admin',      -- Platform super admin
    'org_admin',        -- Organization administrator
    'project_manager',  -- Can manage specific projects
    'instructor',       -- Can create/manage courses
    'student'          -- Course participant
);

-- Organization memberships (replaces simple organization string in users)
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'student',
    permissions JSONB DEFAULT '{}', -- Custom permissions per org
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, organization_id)
);

-- Project memberships (who can access which projects)
CREATE TABLE project_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'participant', -- participant, instructor, manager
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, project_id)
);

-- Project courses (courses within a project)
CREATE TABLE project_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL DEFAULT 0,
    is_required BOOLEAN DEFAULT true,
    prerequisites UUID[], -- Array of course IDs that must be completed first
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, course_id)
);

-- Update users table to remove direct organization field (migrate to memberships)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS user_role user_role DEFAULT 'student',
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS profile_data JSONB DEFAULT '{}';

-- Add foreign key to link courses to organizations
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id),
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id);

-- Create indexes for performance
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_domain ON organizations(domain);
CREATE INDEX idx_projects_organization ON projects(organization_id);
CREATE INDEX idx_projects_slug ON projects(organization_id, slug);
CREATE INDEX idx_org_memberships_user ON organization_memberships(user_id);
CREATE INDEX idx_org_memberships_org ON organization_memberships(organization_id);
CREATE INDEX idx_project_memberships_user ON project_memberships(user_id);
CREATE INDEX idx_project_memberships_project ON project_memberships(project_id);
CREATE INDEX idx_project_courses_project ON project_courses(project_id);
CREATE INDEX idx_users_role ON users(user_role);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO organizations (name, slug, description, domain) VALUES 
('Tech University', 'tech-university', 'Leading technology education institution', 'techuni.edu'),
('Global Corp Training', 'global-corp', 'Corporate training division of Global Corp', 'globalcorp.com'),
('Startup Accelerator', 'startup-accel', 'Fast-track training for startup teams', NULL);

-- Sample project data
INSERT INTO projects (organization_id, name, slug, description, target_roles, duration_weeks, max_participants, status)
SELECT 
    o.id,
    'Graduate Developer Training Program',
    'grad-dev-program',
    'Comprehensive training program for new graduate developers covering full-stack development, DevOps, and business analysis',
    ARRAY['Application Developer', 'Business Analyst', 'Operations Engineer'],
    16,
    50,
    'active'
FROM organizations o WHERE o.slug = 'tech-university';

-- Comments for documentation
COMMENT ON TABLE organizations IS 'Organizations/institutions using the platform';
COMMENT ON TABLE projects IS 'Training projects/programs within organizations';
COMMENT ON TABLE organization_memberships IS 'User membership and roles within organizations';
COMMENT ON TABLE project_memberships IS 'User participation in specific projects';
COMMENT ON TABLE project_courses IS 'Courses assigned to projects with sequencing';
COMMENT ON COLUMN projects.target_roles IS 'Array of job roles this project trains for';
COMMENT ON COLUMN projects.objectives IS 'Array of learning objectives for the project';
COMMENT ON COLUMN organization_memberships.permissions IS 'Custom permissions JSON for fine-grained access control';

-- Migrate existing organization data
-- Move existing organization strings to new organization_memberships table
DO $$
DECLARE
    org_record RECORD;
    user_record RECORD;
    default_org_id UUID;
BEGIN
    -- Create a default organization for existing users without organization
    INSERT INTO organizations (name, slug, description)
    VALUES ('Default Organization', 'default-org', 'Default organization for existing users')
    RETURNING id INTO default_org_id;
    
    -- Migrate users with organization data
    FOR user_record IN 
        SELECT id, organization, user_role FROM users 
        WHERE organization IS NOT NULL AND organization != ''
    LOOP
        -- Find or create organization
        SELECT id INTO org_record FROM organizations 
        WHERE name = user_record.organization;
        
        IF NOT FOUND THEN
            INSERT INTO organizations (name, slug, description)
            VALUES (
                user_record.organization,
                lower(replace(replace(user_record.organization, ' ', '-'), '.', '-')),
                'Automatically created from user data'
            ) RETURNING id INTO org_record;
        END IF;
        
        -- Create organization membership
        INSERT INTO organization_memberships (user_id, organization_id, role)
        VALUES (user_record.id, org_record, COALESCE(user_record.user_role, 'student'))
        ON CONFLICT (user_id, organization_id) DO NOTHING;
    END LOOP;
    
    -- Assign users without organization to default org
    INSERT INTO organization_memberships (user_id, organization_id, role)
    SELECT u.id, default_org_id, COALESCE(u.user_role, 'student')
    FROM users u
    WHERE u.organization IS NULL OR u.organization = ''
    ON CONFLICT (user_id, organization_id) DO NOTHING;
END $$;