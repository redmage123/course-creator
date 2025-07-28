-- Update quiz_attempts table to include course_instance_id for proper tracking
-- This enables analytics to track quiz performance per course instance

-- Add course_instance_id column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='quiz_attempts' AND column_name='course_instance_id'
    ) THEN
        ALTER TABLE quiz_attempts ADD COLUMN course_instance_id UUID;
        
        -- Add foreign key constraint
        ALTER TABLE quiz_attempts 
        ADD CONSTRAINT fk_quiz_attempts_course_instance 
        FOREIGN KEY (course_instance_id) REFERENCES course_instances(id) ON DELETE CASCADE;
        
        -- Add index for better performance
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_course_instance_id 
        ON quiz_attempts(course_instance_id);
        
        -- Add composite index for analytics queries
        CREATE INDEX IF NOT EXISTS idx_quiz_attempts_instance_quiz 
        ON quiz_attempts(course_instance_id, quiz_id);
        
        -- Update comment
        COMMENT ON COLUMN quiz_attempts.course_instance_id IS 'Links quiz attempts to specific course instances for proper analytics tracking';
    END IF;
END $$;

-- Ensure the table is properly structured for analytics integration
COMMENT ON TABLE quiz_attempts IS 'Tracks student quiz attempts and scores for analytics - includes course instance tracking';