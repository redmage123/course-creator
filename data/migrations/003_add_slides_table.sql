-- Migration: Add slides table for persistent slide storage
-- Date: 2025-07-11
-- Purpose: Store course slides in database instead of memory

-- Create slides table
CREATE TABLE IF NOT EXISTS slides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    slide_type VARCHAR(50) NOT NULL DEFAULT 'content',
    order_number INTEGER NOT NULL,
    module_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_slides_course_id ON slides(course_id);
CREATE INDEX IF NOT EXISTS idx_slides_order ON slides(course_id, order_number);
CREATE INDEX IF NOT EXISTS idx_slides_module ON slides(course_id, module_number);

-- Create trigger to update updated_at column
CREATE OR REPLACE FUNCTION update_slides_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_slides_updated_at
    BEFORE UPDATE ON slides
    FOR EACH ROW
    EXECUTE FUNCTION update_slides_updated_at();

-- Grant permissions to course_user
GRANT SELECT, INSERT, UPDATE, DELETE ON slides TO course_user;