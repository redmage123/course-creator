-- Migration 017: Enhanced Instructor and Student Management for Projects
-- Adds comprehensive instructor assignment and student enrollment management

-- =============================================================================
-- ENHANCED PROJECT INSTANTIATION AND MANAGEMENT
-- =============================================================================

-- Add instantiation fields to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_instantiated BOOLEAN DEFAULT false;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS instantiated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS instantiated_by UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS ai_description_processed TEXT; -- AI processed description
ALTER TABLE projects ADD COLUMN IF NOT EXISTS default_tracks_created BOOLEAN DEFAULT false;

-- Add instructor assignment table for tracks
CREATE TABLE IF NOT EXISTS track_instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'instructor' CHECK (role IN ('lead_instructor', 'instructor', 'assistant')),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(track_id, instructor_id)
);

-- Add module instructor assignments (support for multiple instructors per module)
CREATE TABLE IF NOT EXISTS module_instructors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'instructor' CHECK (role IN ('lead_instructor', 'co_instructor', 'assistant')),
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(module_id, instructor_id)
);

-- Enhanced student track enrollments with analytics support
CREATE TABLE IF NOT EXISTS student_track_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrolled_by UUID REFERENCES users(id) ON DELETE SET NULL, -- org admin who enrolled them
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expected_completion_date DATE,
    actual_completion_date TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    current_module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'active', 'paused', 'completed', 'dropped', 'failed')),
    
    -- Analytics tracking
    total_time_spent_minutes INTEGER DEFAULT 0,
    assignments_completed INTEGER DEFAULT 0,
    assignments_total INTEGER DEFAULT 0,
    quiz_attempts INTEGER DEFAULT 0,
    quiz_average_score DECIMAL(5,2),
    lab_sessions_completed INTEGER DEFAULT 0,
    
    -- Engagement metrics
    last_activity_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    forum_posts INTEGER DEFAULT 0,
    help_requests INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    UNIQUE(project_id, track_id, student_id)
);

-- Project analytics summary table
CREATE TABLE IF NOT EXISTS project_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Enrollment statistics
    total_enrolled_students INTEGER DEFAULT 0,
    active_students INTEGER DEFAULT 0,
    completed_students INTEGER DEFAULT 0,
    dropped_students INTEGER DEFAULT 0,
    
    -- Progress statistics
    average_progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    median_completion_time_days INTEGER,
    fastest_completion_time_days INTEGER,
    slowest_completion_time_days INTEGER,
    
    -- Performance statistics
    average_quiz_score DECIMAL(5,2),
    total_lab_sessions INTEGER DEFAULT 0,
    total_assignments_submitted INTEGER DEFAULT 0,
    
    -- Engagement statistics
    average_time_spent_minutes INTEGER DEFAULT 0,
    total_forum_posts INTEGER DEFAULT 0,
    total_help_requests INTEGER DEFAULT 0,
    
    -- Analytics metadata
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculation_version VARCHAR(10) DEFAULT '1.0',
    
    -- Ensure one record per project
    UNIQUE(project_id)
);

-- Default project templates for AI-generated content
CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_roles JSONB DEFAULT '[]',
    default_tracks JSONB NOT NULL, -- Array of track configurations
    ai_prompt_template TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Track instructor indexes
CREATE INDEX IF NOT EXISTS idx_track_instructors_track ON track_instructors(track_id);
CREATE INDEX IF NOT EXISTS idx_track_instructors_instructor ON track_instructors(instructor_id);
CREATE INDEX IF NOT EXISTS idx_track_instructors_active ON track_instructors(is_active);

-- Module instructor indexes
CREATE INDEX IF NOT EXISTS idx_module_instructors_module ON module_instructors(module_id);
CREATE INDEX IF NOT EXISTS idx_module_instructors_instructor ON module_instructors(instructor_id);
CREATE INDEX IF NOT EXISTS idx_module_instructors_active ON module_instructors(is_active);

-- Student enrollment indexes
CREATE INDEX IF NOT EXISTS idx_student_track_enrollments_project ON student_track_enrollments(project_id);
CREATE INDEX IF NOT EXISTS idx_student_track_enrollments_track ON student_track_enrollments(track_id);
CREATE INDEX IF NOT EXISTS idx_student_track_enrollments_student ON student_track_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_student_track_enrollments_status ON student_track_enrollments(status);
CREATE INDEX IF NOT EXISTS idx_student_track_enrollments_active ON student_track_enrollments(is_active);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_project_analytics_project ON project_analytics(project_id);

-- =============================================================================
-- INSERT DEFAULT PROJECT TEMPLATES
-- =============================================================================

-- Insert default project templates for AI-powered project creation
INSERT INTO project_templates (name, description, target_roles, default_tracks, ai_prompt_template) VALUES 
(
    'Software Development Bootcamp',
    'Comprehensive software development training program',
    '["Application Developer", "Full Stack Developer", "Software Engineer"]',
    '[
        {
            "name": "Foundation Track",
            "description": "Programming fundamentals and development environment setup",
            "difficulty_level": "beginner",
            "estimated_duration_hours": 80,
            "modules": [
                {
                    "name": "Development Environment Setup",
                    "ai_description": "Teach students how to set up a modern development environment including IDE, version control, and basic tools"
                },
                {
                    "name": "Programming Fundamentals", 
                    "ai_description": "Cover basic programming concepts including variables, data types, control structures, and functions"
                }
            ]
        },
        {
            "name": "Web Development Track",
            "description": "Modern web development using JavaScript, HTML, CSS, and frameworks",
            "difficulty_level": "intermediate", 
            "estimated_duration_hours": 120,
            "modules": [
                {
                    "name": "Frontend Development",
                    "ai_description": "Comprehensive frontend development covering HTML, CSS, JavaScript, and modern frameworks"
                },
                {
                    "name": "Backend Development",
                    "ai_description": "Server-side development including APIs, databases, and cloud deployment"
                }
            ]
        }
    ]',
    'Create a comprehensive software development training program that covers: {description}. Target roles: {target_roles}. Include practical projects, assessments, and hands-on labs.'
),
(
    'Business Analysis Program',
    'Professional business analyst training with stakeholder management focus',
    '["Business Analyst", "Product Manager", "Requirements Analyst"]',
    '[
        {
            "name": "Business Analysis Fundamentals",
            "description": "Core business analysis principles and methodologies",
            "difficulty_level": "beginner",
            "estimated_duration_hours": 60,
            "modules": [
                {
                    "name": "Requirements Gathering",
                    "ai_description": "Teach students how to effectively gather, document, and validate business requirements from stakeholders"
                },
                {
                    "name": "Process Analysis",
                    "ai_description": "Cover business process analysis, modeling, and improvement methodologies"
                }
            ]
        }
    ]',
    'Create a business analysis training program focused on: {description}. Target roles: {target_roles}. Include real-world case studies, stakeholder simulation exercises, and documentation templates.'
);

-- =============================================================================
-- FUNCTIONS FOR ANALYTICS CALCULATION
-- =============================================================================

-- Function to update project analytics
CREATE OR REPLACE FUNCTION update_project_analytics(p_project_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Upsert project analytics
    INSERT INTO project_analytics (
        project_id,
        total_enrolled_students,
        active_students, 
        completed_students,
        dropped_students,
        average_progress_percentage,
        average_quiz_score,
        average_time_spent_minutes,
        last_calculated_at
    )
    SELECT 
        p_project_id,
        COUNT(*) as total_enrolled,
        COUNT(*) FILTER (WHERE status IN ('enrolled', 'active')) as active,
        COUNT(*) FILTER (WHERE status = 'completed') as completed,
        COUNT(*) FILTER (WHERE status IN ('dropped', 'failed')) as dropped,
        COALESCE(AVG(progress_percentage), 0) as avg_progress,
        COALESCE(AVG(quiz_average_score), 0) as avg_quiz_score,
        COALESCE(AVG(total_time_spent_minutes), 0) as avg_time_spent,
        CURRENT_TIMESTAMP
    FROM student_track_enrollments 
    WHERE project_id = p_project_id AND is_active = true
    ON CONFLICT (project_id) 
    DO UPDATE SET
        total_enrolled_students = EXCLUDED.total_enrolled_students,
        active_students = EXCLUDED.active_students,
        completed_students = EXCLUDED.completed_students,
        dropped_students = EXCLUDED.dropped_students,
        average_progress_percentage = EXCLUDED.average_progress_percentage,
        average_quiz_score = EXCLUDED.average_quiz_score,
        average_time_spent_minutes = EXCLUDED.average_time_spent_minutes,
        last_calculated_at = EXCLUDED.last_calculated_at;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC ANALYTICS UPDATES
-- =============================================================================

-- Trigger function to update analytics when student enrollments change
CREATE OR REPLACE FUNCTION trigger_update_project_analytics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update analytics for the affected project
    IF TG_OP = 'DELETE' THEN
        PERFORM update_project_analytics(OLD.project_id);
        RETURN OLD;
    ELSE
        PERFORM update_project_analytics(NEW.project_id);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic analytics updates
DROP TRIGGER IF EXISTS trigger_student_enrollment_analytics ON student_track_enrollments;
CREATE TRIGGER trigger_student_enrollment_analytics
    AFTER INSERT OR UPDATE OR DELETE ON student_track_enrollments
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_project_analytics();

-- =============================================================================
-- PERMISSIONS AND CONSTRAINTS
-- =============================================================================

-- Add constraints for instructor role validation
ALTER TABLE track_instructors ADD CONSTRAINT track_instructors_min_lead_instructor 
CHECK (role IN ('lead_instructor', 'instructor', 'assistant'));

ALTER TABLE module_instructors ADD CONSTRAINT module_instructors_min_instructors 
CHECK (role IN ('lead_instructor', 'co_instructor', 'assistant'));

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO course_creator_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO course_creator_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO course_creator_app;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

SELECT 'Migration 017: Enhanced Instructor and Student Management completed successfully' as status;