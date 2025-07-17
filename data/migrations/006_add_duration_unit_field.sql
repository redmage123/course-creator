-- Migration: Add duration_unit field to courses table
-- Date: 2025-07-17
-- Purpose: Add duration_unit field to support structured duration input (number + time unit)

-- Add duration_unit column to courses table
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS duration_unit VARCHAR(20) DEFAULT 'weeks';

-- Update existing courses to have default duration_unit if null
UPDATE courses 
SET duration_unit = 'weeks' 
WHERE duration_unit IS NULL;

-- Add constraint to ensure valid duration units
ALTER TABLE courses 
ADD CONSTRAINT check_duration_unit 
CHECK (duration_unit IN ('hours', 'days', 'weeks'));

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_courses_duration_unit ON courses(duration_unit);

-- Add comment for documentation
COMMENT ON COLUMN courses.duration_unit IS 'Duration unit for estimated_duration field (hours, days, weeks)';
COMMENT ON COLUMN courses.estimated_duration IS 'Estimated duration number (to be used with duration_unit)';