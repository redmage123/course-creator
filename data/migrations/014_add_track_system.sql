-- Migration 014: Track-Based Learning Path System
-- Adds tracks to projects for specialized learning paths (App Dev, Business Analyst, Ops tracks)

-- Track types enum
CREATE TYPE track_type AS ENUM (
    'sequential',       -- Students must complete classes in order
    'flexible',         -- Students can take classes in any order  
    'milestone_based'   -- Based on milestone achievements
);

-- Track status enum  
CREATE TYPE track_status AS ENUM (
    'draft',
    'active', 
    'completed',
    'archived'
);

-- Tracks table (learning paths within projects)
CREATE TABLE tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL, -- URL-friendly identifier within project
    description TEXT,
    track_type track_type DEFAULT 'sequential',
    target_audience TEXT[], -- ['Application Developer', 'Junior Developer']
    prerequisites TEXT[], -- ['Basic Programming', 'Git Knowledge']
    duration_weeks INTEGER,
    max_enrolled INTEGER,
    learning_objectives TEXT[],
    skills_taught TEXT[], -- ['React', 'Node.js', 'Docker']
    difficulty_level VARCHAR(20) DEFAULT 'beginner', -- beginner, intermediate, advanced
    sequence_order INTEGER DEFAULT 0, -- Order within project
    auto_enroll_enabled BOOLEAN DEFAULT true, -- Automatic enrollment when student joins project
    status track_status DEFAULT 'draft',
    settings JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, slug)
);

-- Track enrollments (which students are enrolled in which tracks)
CREATE TABLE track_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    auto_enrolled BOOLEAN DEFAULT false, -- Was this an automatic enrollment?
    settings JSONB DEFAULT '{}',
    UNIQUE(user_id, track_id)
);

-- Track classes (classes/modules within tracks)
CREATE TABLE track_classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL DEFAULT 0,
    is_required BOOLEAN DEFAULT true,
    prerequisites UUID[], -- Array of class IDs that must be completed first
    estimated_hours INTEGER, -- Estimated completion time
    is_published BOOLEAN DEFAULT false, -- Organization admin can control publication
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(track_id, course_id),
    UNIQUE(track_id, sequence_order)
);

-- Student progress on track classes
CREATE TABLE track_class_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_class_id UUID NOT NULL REFERENCES track_classes(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,
    grade DECIMAL(5,2), -- Grade achieved (0-100)
    attempts INTEGER DEFAULT 0,
    lab_completion_status JSONB DEFAULT '{}', -- Track lab completion
    quiz_scores JSONB DEFAULT '{}', -- Track quiz scores
    notes TEXT,
    UNIQUE(user_id, track_class_id)
);

-- Create indexes for performance
CREATE INDEX idx_tracks_project ON tracks(project_id);
CREATE INDEX idx_tracks_status ON tracks(status);
CREATE INDEX idx_tracks_slug ON tracks(project_id, slug);
CREATE INDEX idx_tracks_sequence ON tracks(project_id, sequence_order);
CREATE INDEX idx_tracks_auto_enroll ON tracks(project_id, auto_enroll_enabled, status);
CREATE INDEX idx_tracks_difficulty ON tracks(difficulty_level);
CREATE INDEX idx_tracks_target_audience ON tracks USING GIN(target_audience);
CREATE INDEX idx_tracks_skills ON tracks USING GIN(skills_taught);

CREATE INDEX idx_track_enrollments_user ON track_enrollments(user_id);
CREATE INDEX idx_track_enrollments_track ON track_enrollments(track_id);
CREATE INDEX idx_track_enrollments_active ON track_enrollments(is_active);
CREATE INDEX idx_track_enrollments_auto ON track_enrollments(auto_enrolled);

CREATE INDEX idx_track_classes_track ON track_classes(track_id);
CREATE INDEX idx_track_classes_course ON track_classes(course_id);
CREATE INDEX idx_track_classes_sequence ON track_classes(track_id, sequence_order);
CREATE INDEX idx_track_classes_published ON track_classes(is_published);

CREATE INDEX idx_track_progress_user ON track_class_progress(user_id);
CREATE INDEX idx_track_progress_class ON track_class_progress(track_class_id);
CREATE INDEX idx_track_progress_completed ON track_class_progress(completed_at);

-- Add triggers for updated_at
CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample track data for the graduate developer program
INSERT INTO tracks (project_id, name, slug, description, target_audience, skills_taught, difficulty_level, sequence_order, status)
SELECT 
    p.id,
    'Application Developer Track',
    'app-dev-track', 
    'Comprehensive full-stack development training covering React, Node.js, databases, and DevOps practices',
    ARRAY['Application Developer', 'Full-Stack Developer', 'Junior Developer'],
    ARRAY['React', 'Node.js', 'PostgreSQL', 'Docker', 'Git', 'REST APIs'],
    'intermediate',
    1,
    'active'
FROM projects p 
JOIN organizations o ON p.organization_id = o.id 
WHERE o.slug = 'tech-university' AND p.slug = 'grad-dev-program';

INSERT INTO tracks (project_id, name, slug, description, target_audience, skills_taught, difficulty_level, sequence_order, status)
SELECT 
    p.id,
    'Business Analyst Track',
    'business-analyst-track',
    'Business analysis fundamentals including requirements gathering, process modeling, and stakeholder management',
    ARRAY['Business Analyst', 'Product Owner', 'System Analyst'],
    ARRAY['Requirements Analysis', 'Process Modeling', 'SQL', 'Data Analysis', 'Stakeholder Management'],
    'beginner',
    2, 
    'active'
FROM projects p 
JOIN organizations o ON p.organization_id = o.id 
WHERE o.slug = 'tech-university' AND p.slug = 'grad-dev-program';

INSERT INTO tracks (project_id, name, slug, description, target_audience, skills_taught, difficulty_level, sequence_order, status)
SELECT 
    p.id,
    'Operations Engineer Track', 
    'ops-engineer-track',
    'DevOps and infrastructure management including CI/CD, cloud platforms, monitoring, and automation',
    ARRAY['Operations Engineer', 'DevOps Engineer', 'Site Reliability Engineer'],
    ARRAY['Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Monitoring', 'Infrastructure as Code'],
    'advanced',
    3,
    'active'
FROM projects p 
JOIN organizations o ON p.organization_id = o.id 
WHERE o.slug = 'tech-university' AND p.slug = 'grad-dev-program';

-- Comments for documentation
COMMENT ON TABLE tracks IS 'Learning paths within projects, targeting specific roles/audiences';
COMMENT ON TABLE track_enrollments IS 'Student enrollment in specific tracks with auto-enrollment support';
COMMENT ON TABLE track_classes IS 'Classes/modules within tracks with publication control';
COMMENT ON TABLE track_class_progress IS 'Student progress tracking for individual classes within tracks';
COMMENT ON COLUMN tracks.target_audience IS 'Array of job roles this track is designed for';
COMMENT ON COLUMN tracks.auto_enroll_enabled IS 'Whether students are automatically enrolled when joining project';
COMMENT ON COLUMN track_classes.is_published IS 'Organization admin controls whether class is available to students';
COMMENT ON COLUMN track_enrollments.auto_enrolled IS 'Whether this enrollment was automatic or manual';