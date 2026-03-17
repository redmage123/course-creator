-- Course Creator Platform Database Schema
-- Complete schema creation script for PostgreSQL
-- Generated from migration files stored in memory system

-- =============================================================================
-- DATABASE AND SCHEMA SETUP
-- =============================================================================

-- Create the course_creator database if it doesn't exist
-- Note: This should be run as postgres superuser
-- CREATE DATABASE course_creator;

-- Connect to course_creator database and create schema
\c course_creator;

-- Create course_creator schema (if not exists)
CREATE SCHEMA IF NOT EXISTS course_creator;
SET search_path TO course_creator, public;

-- =============================================================================
-- INITIAL CORE TABLES (Migration 001)
-- =============================================================================

-- Users table with authentication and profile information
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Course outlines for structured course content
CREATE TABLE IF NOT EXISTS course_outlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    target_audience VARCHAR(255),
    difficulty_level VARCHAR(50),
    total_duration_hours DECIMAL(5,2),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SESSION MANAGEMENT (Migration 002)
-- =============================================================================

-- User sessions for authentication and security
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Index for session lookup performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- =============================================================================
-- CONTENT MANAGEMENT (Migration 003)
-- =============================================================================

-- Slides table for course presentation content
CREATE TABLE IF NOT EXISTS slides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_outline_id UUID NOT NULL REFERENCES course_outlines(id) ON DELETE CASCADE,
    slide_number INTEGER NOT NULL,
    title VARCHAR(500),
    content TEXT,
    slide_type VARCHAR(50) DEFAULT 'content',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient slide ordering
CREATE INDEX IF NOT EXISTS idx_slides_course_outline ON slides(course_outline_id, slide_number);

-- =============================================================================
-- LAB CONTAINER SYSTEM (Migrations 004-005)
-- =============================================================================

-- Lab sessions for interactive coding environments
CREATE TABLE IF NOT EXISTS lab_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES course_outlines(id) ON DELETE SET NULL,
    container_id VARCHAR(255),
    container_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'creating',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    port_mapping JSONB,
    environment_config JSONB
);

-- Lab environments for predefined development setups
CREATE TABLE IF NOT EXISTS lab_environments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_image VARCHAR(255) NOT NULL,
    packages JSONB,
    environment_variables JSONB,
    port_mappings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for lab management performance
CREATE INDEX IF NOT EXISTS idx_lab_sessions_user_id ON lab_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_lab_sessions_status ON lab_sessions(status);

-- =============================================================================
-- ANALYTICS SYSTEM (Migration 007)
-- =============================================================================

-- Student analytics for progress tracking
CREATE TABLE IF NOT EXISTS student_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES course_outlines(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    ip_address INET
);

-- Performance tracking metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES course_outlines(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    measurement_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_student_analytics_user_course ON student_analytics(user_id, course_id);
CREATE INDEX IF NOT EXISTS idx_student_analytics_timestamp ON student_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_course ON performance_metrics(user_id, course_id);

-- =============================================================================
-- FEEDBACK SYSTEM (Migration 008)
-- =============================================================================

-- Course feedback from students
CREATE TABLE IF NOT EXISTS course_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES course_outlines(id) ON DELETE CASCADE,
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    instructor_rating INTEGER CHECK (instructor_rating >= 1 AND instructor_rating <= 5),
    content_quality_rating INTEGER CHECK (content_quality_rating >= 1 AND content_quality_rating <= 5),
    difficulty_rating INTEGER CHECK (difficulty_rating >= 1 AND difficulty_rating <= 5),
    feedback_text TEXT,
    anonymous BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Student feedback from instructors
CREATE TABLE IF NOT EXISTS student_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES course_outlines(id) ON DELETE CASCADE,
    academic_performance INTEGER CHECK (academic_performance >= 1 AND academic_performance <= 5),
    participation_level INTEGER CHECK (participation_level >= 1 AND participation_level <= 5),
    improvement_trend INTEGER CHECK (improvement_trend >= 1 AND improvement_trend <= 5),
    feedback_text TEXT,
    recommendations TEXT,
    visible_to_student BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- QUIZ SYSTEM (Migration 011)
-- =============================================================================

-- Quizzes for assessments
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES course_outlines(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    questions JSONB NOT NULL,
    answer_key JSONB NOT NULL,
    time_limit INTEGER,
    max_attempts INTEGER DEFAULT 3,
    passing_score DECIMAL(5,2) DEFAULT 70.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Quiz attempts with course instance tracking
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_instance_id UUID,
    answers JSONB NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER NOT NULL,
    time_taken INTEGER,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    attempt_number INTEGER DEFAULT 1
);

-- Quiz publications for course instance control
CREATE TABLE IF NOT EXISTS quiz_publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    course_instance_id UUID NOT NULL,
    published BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    unpublished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ENHANCED RBAC SYSTEM (Migration 015)
-- =============================================================================

-- Organizations for multi-tenant support
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Organization memberships with roles
CREATE TABLE IF NOT EXISTS organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('site_admin', 'organization_admin', 'instructor', 'student')),
    is_active BOOLEAN DEFAULT true,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, organization_id)
);

-- Learning tracks for curriculum management
CREATE TABLE IF NOT EXISTS tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty_level VARCHAR(50) DEFAULT 'intermediate',
    estimated_duration_hours INTEGER,
    prerequisites JSONB DEFAULT '[]',
    learning_objectives JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Track enrollments for student progress
CREATE TABLE IF NOT EXISTS track_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    current_module VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, track_id)
);

-- Meeting rooms for Teams/Zoom integration
CREATE TABLE IF NOT EXISTS meeting_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    room_type VARCHAR(50) NOT NULL CHECK (room_type IN ('organization', 'track', 'instructor')),
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('teams', 'zoom')),
    room_url TEXT,
    room_id VARCHAR(255),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ADDITIONAL TABLES FOR COMPLETENESS
-- =============================================================================

-- Course instances for session management
CREATE TABLE IF NOT EXISTS course_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES course_outlines(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    instance_name VARCHAR(255),
    start_date DATE,
    end_date DATE,
    instructor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    max_enrollment INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Student course enrollments
CREATE TABLE IF NOT EXISTS student_course_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_instance_id UUID NOT NULL REFERENCES course_instances(id) ON DELETE CASCADE,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    final_grade DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'enrolled',
    UNIQUE(student_id, course_instance_id)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Organization and membership indexes
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_org_memberships_user ON organization_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_org_memberships_org ON organization_memberships(organization_id);

-- Track and enrollment indexes
CREATE INDEX IF NOT EXISTS idx_tracks_organization ON tracks(organization_id);
CREATE INDEX IF NOT EXISTS idx_track_enrollments_user ON track_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_track_enrollments_track ON track_enrollments(track_id);

-- Meeting room indexes
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_org ON meeting_rooms(organization_id);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_type ON meeting_rooms(room_type);

-- Course instance and enrollment indexes
CREATE INDEX IF NOT EXISTS idx_course_instances_course ON course_instances(course_id);
CREATE INDEX IF NOT EXISTS idx_course_instances_org ON course_instances(organization_id);
CREATE INDEX IF NOT EXISTS idx_student_enrollments_student ON student_course_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_student_enrollments_instance ON student_course_enrollments(course_instance_id);

-- Quiz system indexes
CREATE INDEX IF NOT EXISTS idx_quizzes_course ON quizzes(course_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user ON quiz_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_publications_quiz ON quiz_publications(quiz_id);

-- =============================================================================
-- SAMPLE DATA INSERTION (OPTIONAL)
-- =============================================================================

-- Insert default organization if none exists
INSERT INTO organizations (name, slug, description) 
VALUES ('Default Organization', 'default', 'Default organization for initial setup')
ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- SCHEMA CREATION COMPLETE
-- =============================================================================

-- Display schema information
\echo 'Course Creator database schema created successfully!'
\echo 'Available tables:'
\dt course_creator.*;

-- Display current search path
\echo 'Current search path:'
SHOW search_path;

-- Final verification
\echo 'Schema creation completed. Ready for Course Creator platform!'