-- Migration: Add lab environments table for persistent lab environment configurations
-- Date: 2025-07-13
-- Purpose: Store lab environment configurations per course

-- Create lab_environments table
CREATE TABLE IF NOT EXISTS lab_environments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    environment_type VARCHAR(100) NOT NULL DEFAULT 'ai_assisted',
    config JSONB NOT NULL DEFAULT '{}',
    exercises JSONB NOT NULL DEFAULT '[]',
    status VARCHAR(50) NOT NULL DEFAULT 'ready',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_lab_environments_course ON lab_environments(course_id);
CREATE INDEX IF NOT EXISTS idx_lab_environments_status ON lab_environments(status);
CREATE INDEX IF NOT EXISTS idx_lab_environments_type ON lab_environments(environment_type);

-- Create trigger to update updated_at column
CREATE OR REPLACE FUNCTION update_lab_environments_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_lab_environments_timestamps
    BEFORE UPDATE ON lab_environments
    FOR EACH ROW
    EXECUTE FUNCTION update_lab_environments_timestamps();

-- Grant permissions to course_user
GRANT SELECT, INSERT, UPDATE, DELETE ON lab_environments TO course_user;