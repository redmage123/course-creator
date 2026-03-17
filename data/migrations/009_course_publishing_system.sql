-- Migration 009: Course Publishing and Instance Management System
-- Purpose: Add comprehensive course publishing workflow with instances and enhanced enrollment
-- Features: Draft → Published workflow, Public/Private courses, Course instances with scheduling, 
--          Enhanced student enrollment with unique URLs and passwords

-- Add publishing fields to existing courses table
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'public')),
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS course_version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS last_modified_by UUID REFERENCES users(id);

-- Create course_instances table for scheduled course sessions
CREATE TABLE IF NOT EXISTS course_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Instance details
    instance_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Scheduling with timezone support
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    
    -- Instance status and metadata
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')),
    max_students INTEGER,
    current_enrollments INTEGER DEFAULT 0,
    
    -- Auto-calculated fields
    duration_days INTEGER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (end_date - start_date))
    ) STORED,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    
    -- Constraints
    CONSTRAINT valid_date_range CHECK (end_date > start_date),
    CONSTRAINT valid_max_students CHECK (max_students IS NULL OR max_students > 0)
);

-- Enhanced student enrollment table with unique URLs and passwords
CREATE TABLE IF NOT EXISTS student_course_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_instance_id UUID NOT NULL REFERENCES course_instances(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Allow nulls for pre-registration
    
    -- Student information (for cases where user doesn't exist yet)
    student_email VARCHAR(255) NOT NULL,
    student_first_name VARCHAR(100) NOT NULL,
    student_last_name VARCHAR(100) NOT NULL,
    
    -- Unique access credentials
    unique_access_url VARCHAR(500) NOT NULL UNIQUE,
    access_token VARCHAR(255) NOT NULL UNIQUE,
    temporary_password VARCHAR(255) NOT NULL, -- Hashed password for first login
    password_reset_required BOOLEAN DEFAULT true,
    
    -- Enrollment status and tracking
    enrollment_status VARCHAR(20) DEFAULT 'enrolled' CHECK (enrollment_status IN 
        ('enrolled', 'active', 'completed', 'suspended', 'withdrawn')),
    first_login_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE,
    
    -- Progress tracking
    progress_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    completed_at TIMESTAMP WITH TIME ZONE,
    certificate_issued BOOLEAN DEFAULT false,
    
    -- Metadata
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    enrolled_by UUID NOT NULL REFERENCES users(id), -- Instructor who enrolled the student
    notes TEXT,
    
    -- Constraints
    UNIQUE(course_instance_id, student_email)
);

-- Quiz publishing status table
CREATE TABLE IF NOT EXISTS quiz_publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    course_instance_id UUID NOT NULL REFERENCES course_instances(id) ON DELETE CASCADE,
    
    -- Publishing control
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    unpublished_at TIMESTAMP WITH TIME ZONE,
    published_by UUID NOT NULL REFERENCES users(id),
    
    -- Quiz instance settings
    available_from TIMESTAMP WITH TIME ZONE,
    available_until TIMESTAMP WITH TIME ZONE,
    time_limit_minutes INTEGER,
    max_attempts INTEGER DEFAULT 3,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(quiz_id, course_instance_id),
    CONSTRAINT valid_availability_window CHECK (
        available_until IS NULL OR available_from IS NULL OR available_until > available_from
    )
);

-- Course content visibility table (for controlling what students see)
CREATE TABLE IF NOT EXISTS course_content_visibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_instance_id UUID NOT NULL REFERENCES course_instances(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('syllabus', 'slides', 'lab', 'quiz', 'lesson')),
    content_id UUID NOT NULL, -- References slides.id, lessons.id, etc.
    
    -- Visibility control
    is_visible BOOLEAN DEFAULT true,
    visible_from TIMESTAMP WITH TIME ZONE,
    visible_until TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    updated_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(course_instance_id, content_type, content_id)
);

-- Email notifications log
CREATE TABLE IF NOT EXISTS enrollment_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enrollment_id UUID NOT NULL REFERENCES student_course_enrollments(id) ON DELETE CASCADE,
    
    -- Email details
    recipient_email VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL CHECK (email_type IN ('enrollment', 'reminder', 'welcome', 'completion')),
    email_subject VARCHAR(500) NOT NULL,
    email_body TEXT NOT NULL,
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE,
    delivery_status VARCHAR(20) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')),
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_by UUID NOT NULL REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_courses_status_visibility ON courses(status, visibility);
CREATE INDEX IF NOT EXISTS idx_courses_instructor_published ON courses(instructor_id, status) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_course_instances_instructor ON course_instances(instructor_id);
CREATE INDEX IF NOT EXISTS idx_course_instances_dates ON course_instances(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_course_instances_status ON course_instances(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_instance ON student_course_enrollments(course_instance_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON student_course_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_email ON student_course_enrollments(student_email);
CREATE INDEX IF NOT EXISTS idx_enrollments_access_token ON student_course_enrollments(access_token);
CREATE INDEX IF NOT EXISTS idx_quiz_publications_instance ON quiz_publications(course_instance_id, is_published);
CREATE INDEX IF NOT EXISTS idx_content_visibility_instance ON course_content_visibility(course_instance_id, content_type);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_course_instances_updated_at 
    BEFORE UPDATE ON course_instances 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_enrollments_updated_at 
    BEFORE UPDATE ON student_course_enrollments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quiz_publications_updated_at 
    BEFORE UPDATE ON quiz_publications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW published_public_courses AS
SELECT 
    c.id,
    c.title,
    c.description,
    c.instructor_id,
    u.full_name AS instructor_name,
    c.category,
    c.difficulty_level,
    c.estimated_duration,
    c.duration_unit,
    c.price,
    c.thumbnail_url,
    c.published_at,
    COUNT(ci.id) AS total_instances,
    COUNT(CASE WHEN ci.status = 'active' THEN 1 END) AS active_instances
FROM courses c
JOIN users u ON c.instructor_id = u.id
LEFT JOIN course_instances ci ON c.id = ci.course_id
WHERE c.status = 'published' AND c.visibility = 'public'
GROUP BY c.id, c.title, c.description, c.instructor_id, u.full_name, c.category, 
         c.difficulty_level, c.estimated_duration, c.duration_unit, c.price, 
         c.thumbnail_url, c.published_at;

CREATE OR REPLACE VIEW instructor_course_overview AS
SELECT 
    c.id AS course_id,
    c.title,
    c.status,
    c.visibility,
    c.instructor_id,
    COUNT(ci.id) AS total_instances,
    COUNT(CASE WHEN ci.status = 'active' THEN 1 END) AS active_instances,
    COUNT(sce.id) AS total_enrollments,
    COUNT(CASE WHEN sce.enrollment_status = 'active' THEN 1 END) AS active_enrollments,
    AVG(sce.progress_percentage) AS average_progress
FROM courses c
LEFT JOIN course_instances ci ON c.id = ci.course_id
LEFT JOIN student_course_enrollments sce ON ci.id = sce.course_instance_id
GROUP BY c.id, c.title, c.status, c.visibility, c.instructor_id;

CREATE OR REPLACE VIEW student_course_access AS
SELECT 
    sce.id AS enrollment_id,
    sce.unique_access_url,
    sce.student_email,
    sce.student_first_name,
    sce.student_last_name,
    sce.enrollment_status,
    sce.progress_percentage,
    c.title AS course_title,
    ci.instance_name,
    ci.start_date,
    ci.end_date,
    ci.timezone,
    u.full_name AS instructor_name
FROM student_course_enrollments sce
JOIN course_instances ci ON sce.course_instance_id = ci.id
JOIN courses c ON ci.course_id = c.id
JOIN users u ON ci.instructor_id = u.id
WHERE sce.enrollment_status IN ('enrolled', 'active');

-- Add comments for documentation
COMMENT ON TABLE course_instances IS 'Scheduled instances of published courses with specific start/end dates';
COMMENT ON TABLE student_course_enrollments IS 'Enhanced enrollment with unique URLs and temporary passwords for students';
COMMENT ON TABLE quiz_publications IS 'Controls which quizzes are published/visible to students in course instances';
COMMENT ON TABLE course_content_visibility IS 'Fine-grained control over content visibility in course instances';
COMMENT ON TABLE enrollment_notifications IS 'Tracks email notifications sent to enrolled students';

COMMENT ON COLUMN courses.status IS 'Course lifecycle: draft → published → archived';
COMMENT ON COLUMN courses.visibility IS 'Course visibility: private (instructor only) or public (visible to all)';
COMMENT ON COLUMN course_instances.duration_days IS 'Auto-calculated course duration in days';
COMMENT ON COLUMN student_course_enrollments.unique_access_url IS 'Unique URL for student to access their specific course instance';
COMMENT ON COLUMN student_course_enrollments.access_token IS 'Unique token for authentication (part of the URL)';
COMMENT ON COLUMN student_course_enrollments.temporary_password IS 'Temporary password sent via email for first login';