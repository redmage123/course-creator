-- Migration: Add lab sessions table for persistent student lab state
-- Date: 2025-07-11
-- Purpose: Store student lab sessions with AI agent memory and code state

-- Create lab_sessions table
CREATE TABLE IF NOT EXISTS lab_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_data JSONB NOT NULL DEFAULT '{}',
    ai_conversation_history JSONB NOT NULL DEFAULT '[]',
    code_files JSONB NOT NULL DEFAULT '{}',
    current_exercise VARCHAR(255),
    progress_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, student_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_lab_sessions_course_student ON lab_sessions(course_id, student_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_student ON lab_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_course ON lab_sessions(course_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_last_accessed ON lab_sessions(last_accessed_at);

-- Create trigger to update updated_at and last_accessed_at columns
CREATE OR REPLACE FUNCTION update_lab_sessions_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.last_accessed_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_lab_sessions_timestamps
    BEFORE UPDATE ON lab_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_lab_sessions_timestamps();

-- Create function to clean up old lab sessions (optional - older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_lab_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM lab_sessions 
    WHERE last_accessed_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to course_user
GRANT SELECT, INSERT, UPDATE, DELETE ON lab_sessions TO course_user;
GRANT EXECUTE ON FUNCTION cleanup_old_lab_sessions() TO course_user;