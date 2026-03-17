-- Migration: Add user sessions table for session management
-- Date: 2025-07-10
-- Purpose: Implement proper session timeout and multi-user session management

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);

-- Create function to automatically clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to limit concurrent sessions per user
CREATE OR REPLACE FUNCTION limit_user_sessions(
    p_user_id UUID,
    p_max_sessions INTEGER DEFAULT 3
)
RETURNS INTEGER AS $$
DECLARE
    current_sessions INTEGER;
    sessions_to_delete INTEGER;
BEGIN
    -- Count current active sessions for user
    SELECT COUNT(*) INTO current_sessions
    FROM user_sessions 
    WHERE user_id = p_user_id AND expires_at > CURRENT_TIMESTAMP;
    
    -- If we exceed the limit, delete oldest sessions
    IF current_sessions >= p_max_sessions THEN
        sessions_to_delete := current_sessions - p_max_sessions + 1;
        
        DELETE FROM user_sessions 
        WHERE id IN (
            SELECT id FROM user_sessions 
            WHERE user_id = p_user_id 
            ORDER BY created_at ASC 
            LIMIT sessions_to_delete
        );
        
        RETURN sessions_to_delete;
    END IF;
    
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to automatically update last_accessed_at
CREATE OR REPLACE FUNCTION update_session_access_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_access_time
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_session_access_time();

-- Grant permissions to the course_user
GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO course_user;
GRANT EXECUTE ON FUNCTION cleanup_expired_sessions() TO course_user;
GRANT EXECUTE ON FUNCTION limit_user_sessions(UUID, INTEGER) TO course_user;

-- Insert some sample data for testing (optional)
-- This would be removed in production
/*
INSERT INTO user_sessions (user_id, token_hash, ip_address, user_agent, expires_at)
SELECT 
    u.id,
    'sample_token_hash_' || u.id,
    '127.0.0.1',
    'Sample User Agent',
    CURRENT_TIMESTAMP + INTERVAL '30 minutes'
FROM users u 
LIMIT 1;
*/