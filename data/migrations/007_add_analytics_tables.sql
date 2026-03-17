-- Migration 007: Add Student Analytics Tables
-- Add comprehensive analytics tables to the existing course creator database

-- Student Activities table - tracks all student interactions
CREATE TABLE IF NOT EXISTS student_activities (
    activity_id VARCHAR PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    activity_type VARCHAR NOT NULL, -- login, logout, lab_access, quiz_start, quiz_complete, content_view
    activity_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for student_activities
CREATE INDEX IF NOT EXISTS idx_student_activities_student_course ON student_activities(student_id, course_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_student_activities_type ON student_activities(activity_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_student_activities_session ON student_activities(session_id);

-- Lab Usage Metrics table - detailed lab session tracking
CREATE TABLE IF NOT EXISTS lab_usage_metrics (
    metric_id VARCHAR PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lab_id VARCHAR NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    actions_performed INTEGER DEFAULT 0,
    code_executions INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    completion_status VARCHAR DEFAULT 'in_progress', -- in_progress, completed, abandoned
    final_code TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for lab_usage_metrics
CREATE INDEX IF NOT EXISTS idx_lab_usage_student_course ON lab_usage_metrics(student_id, course_id);
CREATE INDEX IF NOT EXISTS idx_lab_usage_lab_session ON lab_usage_metrics(lab_id, session_start);
CREATE INDEX IF NOT EXISTS idx_lab_usage_status ON lab_usage_metrics(completion_status);

-- Quiz Performance table - quiz attempt tracking
CREATE TABLE IF NOT EXISTS quiz_performance (
    performance_id VARCHAR PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    quiz_id VARCHAR NOT NULL,
    attempt_number INTEGER DEFAULT 1,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    questions_total INTEGER NOT NULL,
    questions_answered INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    score_percentage DECIMAL(5,2),
    answers JSONB DEFAULT '{}',
    time_per_question JSONB DEFAULT '{}',
    status VARCHAR DEFAULT 'in_progress', -- in_progress, completed, abandoned
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for quiz_performance
CREATE INDEX IF NOT EXISTS idx_quiz_performance_student_course ON quiz_performance(student_id, course_id);
CREATE INDEX IF NOT EXISTS idx_quiz_performance_quiz ON quiz_performance(quiz_id, start_time);
CREATE INDEX IF NOT EXISTS idx_quiz_performance_score ON quiz_performance(score_percentage);

-- Student Progress table - content item progress tracking
CREATE TABLE IF NOT EXISTS student_progress (
    progress_id VARCHAR PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    content_item_id VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL, -- module, lesson, lab, quiz, assignment
    status VARCHAR DEFAULT 'not_started', -- not_started, in_progress, completed, mastered
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,
    time_spent_minutes INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE NOT NULL,
    completion_date TIMESTAMP WITH TIME ZONE,
    mastery_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for student_progress
CREATE INDEX IF NOT EXISTS idx_student_progress_student_course ON student_progress(student_id, course_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_content ON student_progress(content_item_id, status);
CREATE INDEX IF NOT EXISTS idx_student_progress_accessed ON student_progress(last_accessed);

-- Unique constraint to prevent duplicate progress entries
CREATE UNIQUE INDEX IF NOT EXISTS idx_student_progress_unique ON student_progress(student_id, course_id, content_item_id);

-- Learning Analytics table - computed analytics and insights
CREATE TABLE IF NOT EXISTS learning_analytics (
    analytics_id VARCHAR PRIMARY KEY,
    student_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id VARCHAR NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    engagement_score DECIMAL(5,2) DEFAULT 0.0,
    progress_velocity DECIMAL(8,2) DEFAULT 0.0,
    lab_proficiency DECIMAL(5,2) DEFAULT 0.0,
    quiz_performance DECIMAL(5,2) DEFAULT 0.0,
    time_on_platform INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    risk_level VARCHAR DEFAULT 'low', -- low, medium, high
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for learning_analytics
CREATE INDEX IF NOT EXISTS idx_learning_analytics_student_course ON learning_analytics(student_id, course_id, analysis_date);
CREATE INDEX IF NOT EXISTS idx_learning_analytics_risk ON learning_analytics(risk_level);
CREATE INDEX IF NOT EXISTS idx_learning_analytics_engagement ON learning_analytics(engagement_score);

-- Update trigger for student_progress updated_at field
CREATE OR REPLACE FUNCTION update_student_progress_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_student_progress_updated_at
    BEFORE UPDATE ON student_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_student_progress_updated_at();