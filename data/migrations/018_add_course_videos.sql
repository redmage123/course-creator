-- Migration 018: Add Course Videos Support
-- This migration adds support for video uploads and external video links to courses
-- Allows instructors to attach multiple videos to their courses for enhanced learning

-- =============================================================================
-- COURSES TABLE (if not exists)
-- =============================================================================

-- Create courses table if it doesn't exist
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    instructor_id UUID NOT NULL,
    category VARCHAR(100),
    difficulty_level VARCHAR(50) DEFAULT 'beginner',
    estimated_duration INTEGER,
    duration_unit VARCHAR(50) DEFAULT 'weeks',
    price DECIMAL(10,2) DEFAULT 0.00,
    thumbnail_url TEXT,
    is_published BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Statistics
    total_enrollments INTEGER DEFAULT 0,
    active_enrollments INTEGER DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0.00,

    -- Metadata
    last_updated_by UUID,
    published_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for courses table
CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);
CREATE INDEX IF NOT EXISTS idx_courses_published ON courses(is_published);

-- =============================================================================
-- COURSE VIDEOS TABLE
-- =============================================================================

-- Create enum for video types (uploaded files vs external links)
DO $$ BEGIN
    CREATE TYPE video_type_enum AS ENUM ('upload', 'link', 'youtube', 'vimeo');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Course videos table supporting both file uploads and external links
CREATE TABLE IF NOT EXISTS course_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    video_type video_type_enum NOT NULL DEFAULT 'upload',
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    order_index INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    CONSTRAINT fk_course_videos_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_course_videos_course_id
    ON course_videos(course_id);

CREATE INDEX IF NOT EXISTS idx_course_videos_order
    ON course_videos(course_id, order_index);

CREATE INDEX IF NOT EXISTS idx_course_videos_active
    ON course_videos(course_id, is_active);

-- =============================================================================
-- VIDEO UPLOAD TRACKING
-- =============================================================================

-- Table to track video upload progress for large file uploads
CREATE TABLE IF NOT EXISTS video_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    instructor_id UUID NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    upload_status VARCHAR(50) DEFAULT 'pending',
    upload_progress INTEGER DEFAULT 0,
    error_message TEXT,
    storage_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Foreign key constraints
    CONSTRAINT fk_video_uploads_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_video_uploads_instructor
        FOREIGN KEY (instructor_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Index for tracking uploads by instructor
CREATE INDEX IF NOT EXISTS idx_video_uploads_instructor
    ON video_uploads(instructor_id, upload_status);

-- =============================================================================
-- TRIGGER FOR AUTO-UPDATE TIMESTAMPS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_course_videos_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for course_videos table
CREATE TRIGGER trigger_update_course_videos_timestamp
    BEFORE UPDATE ON course_videos
    FOR EACH ROW
    EXECUTE FUNCTION update_course_videos_updated_at();

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE course_videos IS 'Stores video content associated with courses, supporting both uploaded files and external video links';
COMMENT ON COLUMN course_videos.video_type IS 'Type of video: upload (local/S3 file), link (generic URL), youtube, vimeo';
COMMENT ON COLUMN course_videos.video_url IS 'URL or path to the video file';
COMMENT ON COLUMN course_videos.order_index IS 'Display order of videos within a course (0-based)';
COMMENT ON COLUMN course_videos.is_active IS 'Soft delete flag - allows hiding videos without removing them';

COMMENT ON TABLE video_uploads IS 'Tracks the progress of large video file uploads with chunking support';
COMMENT ON COLUMN video_uploads.upload_status IS 'Status: pending, uploading, processing, completed, failed';
COMMENT ON COLUMN video_uploads.upload_progress IS 'Upload progress percentage (0-100)';
