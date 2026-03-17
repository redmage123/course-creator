-- Migration 009: Add course completion and access control fields
-- Adds support for course completion tracking and student access control

-- Add completion tracking fields to course_instances
ALTER TABLE course_instances 
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS cleanup_completed_at TIMESTAMP WITH TIME ZONE;

-- Add access control fields to student_course_enrollments
ALTER TABLE student_course_enrollments 
ADD COLUMN IF NOT EXISTS access_disabled_at TIMESTAMP WITH TIME ZONE;

-- Create index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_course_instances_completed_cleanup 
ON course_instances (status, completed_at, cleanup_completed_at);

-- Create index for access control queries
CREATE INDEX IF NOT EXISTS idx_student_enrollments_access_disabled 
ON student_course_enrollments (access_disabled_at);

-- Add quiz_attempts table if it doesn't exist (for cleanup functionality)
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL,
    course_instance_id UUID NOT NULL REFERENCES course_instances(id) ON DELETE CASCADE,
    student_email VARCHAR(255) NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    answers JSONB,
    time_taken_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for quiz_attempts
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_course_instance 
ON quiz_attempts (course_instance_id);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student 
ON quiz_attempts (student_email);

-- Update any existing course instances that have passed their end date to be completed
UPDATE course_instances 
SET status = 'completed', completed_at = end_date, updated_at = CURRENT_TIMESTAMP
WHERE status IN ('scheduled', 'active') 
AND end_date < CURRENT_TIMESTAMP;

-- Update student enrollments for completed courses
UPDATE student_course_enrollments 
SET enrollment_status = 'completed', access_disabled_at = CURRENT_TIMESTAMP
WHERE course_instance_id IN (
    SELECT id FROM course_instances WHERE status = 'completed'
) AND enrollment_status = 'enrolled';

-- Add comments for documentation
COMMENT ON COLUMN course_instances.completed_at IS 'Timestamp when the course instance was manually completed by instructor';
COMMENT ON COLUMN course_instances.cleanup_completed_at IS 'Timestamp when student data cleanup was completed for this instance';
COMMENT ON COLUMN student_course_enrollments.access_disabled_at IS 'Timestamp when student access was disabled (course completion or manual action)';
COMMENT ON TABLE quiz_attempts IS 'Student quiz attempts for tracking and cleanup purposes';