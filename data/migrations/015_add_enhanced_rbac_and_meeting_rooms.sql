-- Enhanced RBAC and Meeting Room System Migration
-- Adds comprehensive role-based access control and MS Teams/Zoom integration

-- Create enhanced role types
CREATE TYPE enhanced_role_type AS ENUM (
    'site_admin',
    'organization_admin', 
    'instructor',
    'student'
);

-- Create meeting platform types
CREATE TYPE meeting_platform AS ENUM (
    'teams',
    'zoom'
);

-- Create room types
CREATE TYPE room_type AS ENUM (
    'track_room',
    'instructor_room', 
    'project_room',
    'organization_room'
);

-- Enhanced organization memberships table
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role_type enhanced_role_type NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    project_ids UUID[] DEFAULT '{}',
    track_ids UUID[] DEFAULT '{}',
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'inactive')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, organization_id, role_type)
);

-- Track assignments table (instructors and students to tracks)
CREATE TABLE track_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    role_type enhanced_role_type NOT NULL CHECK (role_type IN ('instructor', 'student')),
    assigned_by UUID NOT NULL REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed')),
    
    UNIQUE(user_id, track_id, role_type)
);

-- Meeting rooms table
CREATE TABLE meeting_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    platform meeting_platform NOT NULL,
    room_type room_type NOT NULL,
    
    -- Context associations
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    instructor_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Platform-specific data
    external_room_id VARCHAR(255),
    join_url TEXT,
    host_url TEXT,
    meeting_id VARCHAR(255),
    passcode VARCHAR(50),
    
    -- Room settings
    settings JSONB DEFAULT '{}',
    is_recurring BOOLEAN DEFAULT true,
    max_participants INTEGER,
    
    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deleted')),
    
    -- Constraints based on room type
    CONSTRAINT check_track_room CHECK (
        room_type != 'track_room' OR track_id IS NOT NULL
    ),
    CONSTRAINT check_instructor_room CHECK (
        room_type != 'instructor_room' OR instructor_id IS NOT NULL
    ),
    CONSTRAINT check_project_room CHECK (
        room_type != 'project_room' OR project_id IS NOT NULL
    )
);

-- Meeting room usage tracking
CREATE TABLE meeting_room_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    INDEX ON (room_id, joined_at),
    INDEX ON (user_id, joined_at)
);

-- Meeting room invitations
CREATE TABLE meeting_room_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
    invitee_email VARCHAR(255) NOT NULL,
    invitee_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    access_level VARCHAR(20) DEFAULT 'participant' CHECK (access_level IN ('host', 'co-host', 'participant')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired')),
    
    INDEX ON (room_id),
    INDEX ON (invitee_email),
    INDEX ON (status)
);

-- Student-to-project enrollments (enhanced)
CREATE TABLE IF NOT EXISTS student_project_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    enrolled_by UUID NOT NULL REFERENCES users(id),
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed', 'dropped')),
    
    UNIQUE(student_id, project_id)
);

-- Indexes for performance
CREATE INDEX idx_organization_memberships_user_org ON organization_memberships(user_id, organization_id);
CREATE INDEX idx_organization_memberships_org_role ON organization_memberships(organization_id, role_type);
CREATE INDEX idx_organization_memberships_status ON organization_memberships(status);

CREATE INDEX idx_track_assignments_user ON track_assignments(user_id);
CREATE INDEX idx_track_assignments_track ON track_assignments(track_id);
CREATE INDEX idx_track_assignments_role ON track_assignments(role_type);
CREATE INDEX idx_track_assignments_status ON track_assignments(status);

CREATE INDEX idx_meeting_rooms_org ON meeting_rooms(organization_id);
CREATE INDEX idx_meeting_rooms_project ON meeting_rooms(project_id);
CREATE INDEX idx_meeting_rooms_track ON meeting_rooms(track_id);
CREATE INDEX idx_meeting_rooms_instructor ON meeting_rooms(instructor_id);
CREATE INDEX idx_meeting_rooms_platform ON meeting_rooms(platform);
CREATE INDEX idx_meeting_rooms_type ON meeting_rooms(room_type);
CREATE INDEX idx_meeting_rooms_status ON meeting_rooms(status);

-- Functions for automatic permission assignment
CREATE OR REPLACE FUNCTION assign_default_permissions()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-assign permissions based on role type
    IF NEW.role_type = 'site_admin' THEN
        NEW.permissions = ARRAY[
            'delete_any_organization', 'view_all_organizations', 'manage_site_settings',
            'manage_organization', 'add_organization_admins', 'remove_organization_admins',
            'add_instructors_to_org', 'remove_instructors_from_org', 'create_projects',
            'delete_projects', 'create_tracks', 'delete_tracks', 'assign_students_to_tracks',
            'assign_instructors_to_tracks', 'manage_track_modules', 'create_teams_rooms',
            'create_zoom_rooms', 'manage_meeting_rooms', 'add_students_to_project',
            'remove_students_from_project', 'view_student_progress'
        ];
    ELSIF NEW.role_type = 'organization_admin' THEN
        NEW.permissions = ARRAY[
            'manage_organization', 'add_organization_admins', 'remove_organization_admins',
            'add_instructors_to_org', 'remove_instructors_from_org', 'create_projects',
            'delete_projects', 'create_tracks', 'delete_tracks', 'assign_students_to_tracks',
            'assign_instructors_to_tracks', 'manage_track_modules', 'create_teams_rooms',
            'create_zoom_rooms', 'manage_meeting_rooms', 'add_students_to_project',
            'remove_students_from_project', 'view_student_progress'
        ];
    ELSIF NEW.role_type = 'instructor' THEN
        NEW.permissions = ARRAY[
            'teach_tracks', 'grade_students', 'view_assigned_students',
            'manage_assigned_content', 'view_student_progress'
        ];
    ELSIF NEW.role_type = 'student' THEN
        NEW.permissions = ARRAY[
            'access_assigned_tracks', 'submit_assignments', 'view_own_progress'
        ];
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-permission assignment
CREATE TRIGGER assign_permissions_trigger
    BEFORE INSERT ON organization_memberships
    FOR EACH ROW
    EXECUTE FUNCTION assign_default_permissions();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at timestamps
CREATE TRIGGER update_organization_memberships_timestamp
    BEFORE UPDATE ON organization_memberships
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_meeting_rooms_timestamp
    BEFORE UPDATE ON meeting_rooms
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Views for easier querying
CREATE VIEW active_organization_memberships AS
SELECT 
    om.*,
    u.email as user_email,
    u.name as user_name,
    o.name as organization_name
FROM organization_memberships om
JOIN users u ON om.user_id = u.id
JOIN organizations o ON om.organization_id = o.id
WHERE om.status = 'active';

CREATE VIEW active_track_assignments AS
SELECT 
    ta.*,
    u.email as user_email,
    u.name as user_name,
    t.name as track_name,
    t.project_id
FROM track_assignments ta
JOIN users u ON ta.user_id = u.id
JOIN tracks t ON ta.track_id = t.id
WHERE ta.status = 'active';

CREATE VIEW active_meeting_rooms AS
SELECT 
    mr.*,
    o.name as organization_name,
    p.name as project_name,
    t.name as track_name,
    u.name as instructor_name
FROM meeting_rooms mr
JOIN organizations o ON mr.organization_id = o.id
LEFT JOIN projects p ON mr.project_id = p.id
LEFT JOIN tracks t ON mr.track_id = t.id
LEFT JOIN users u ON mr.instructor_id = u.id
WHERE mr.status = 'active';

-- Insert default site admin if not exists
INSERT INTO users (id, email, name, password_hash, role, is_active)
VALUES (
    gen_random_uuid(),
    'admin@course-creator.com',
    'Site Administrator',
    '$2b$12$dummy_hash_for_site_admin',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- Grant site admin permissions to the default admin user
INSERT INTO organization_memberships (user_id, organization_id, role_type, status, accepted_at)
SELECT 
    u.id,
    (SELECT id FROM organizations LIMIT 1), -- Use first org or create default
    'site_admin',
    'active',
    CURRENT_TIMESTAMP
FROM users u 
WHERE u.email = 'admin@course-creator.com'
ON CONFLICT DO NOTHING;

COMMIT;