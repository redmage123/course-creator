-- Migration 008: Add Feedback System Tables
-- Add comprehensive feedback system to the existing course creator database
-- Supports both course feedback from students and individual student feedback from instructors

-- Course Feedback table - students provide feedback about courses
CREATE TABLE IF NOT EXISTS course_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Rating scores (1-5 scale)
    overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
    content_quality INTEGER CHECK (content_quality >= 1 AND content_quality <= 5),
    instructor_effectiveness INTEGER CHECK (instructor_effectiveness >= 1 AND instructor_effectiveness <= 5),
    difficulty_appropriateness INTEGER CHECK (difficulty_appropriateness >= 1 AND difficulty_appropriateness <= 5),
    lab_quality INTEGER CHECK (lab_quality >= 1 AND lab_quality <= 5),
    
    -- Text feedback
    positive_aspects TEXT,
    areas_for_improvement TEXT,
    additional_comments TEXT,
    would_recommend BOOLEAN DEFAULT NULL,
    
    -- Metadata
    is_anonymous BOOLEAN DEFAULT false,
    submission_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'flagged')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one feedback per student per course
    UNIQUE(student_id, course_id)
);

-- Student Feedback table - instructors provide feedback about individual students
CREATE TABLE IF NOT EXISTS student_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    
    -- Performance ratings (1-5 scale)
    overall_performance INTEGER CHECK (overall_performance >= 1 AND overall_performance <= 5),
    participation INTEGER CHECK (participation >= 1 AND participation <= 5),
    lab_performance INTEGER CHECK (lab_performance >= 1 AND lab_performance <= 5),
    quiz_performance INTEGER CHECK (quiz_performance >= 1 AND quiz_performance <= 5),
    improvement_trend INTEGER CHECK (improvement_trend >= 1 AND improvement_trend <= 5),
    
    -- Text feedback
    strengths TEXT,
    areas_for_improvement TEXT,
    specific_recommendations TEXT,
    notable_achievements TEXT,
    concerns TEXT,
    
    -- Progress tracking
    progress_assessment VARCHAR(20) CHECK (progress_assessment IN ('excellent', 'good', 'satisfactory', 'needs_improvement', 'poor')),
    expected_outcome VARCHAR(20) CHECK (expected_outcome IN ('exceeds_expectations', 'meets_expectations', 'below_expectations', 'at_risk')),
    
    -- Metadata
    feedback_type VARCHAR(20) DEFAULT 'regular' CHECK (feedback_type IN ('regular', 'midterm', 'final', 'intervention')),
    is_shared_with_student BOOLEAN DEFAULT false,
    submission_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'draft', 'archived')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feedback Response table - for instructor responses to course feedback
CREATE TABLE IF NOT EXISTS feedback_responses (
    response_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_feedback_id UUID NOT NULL REFERENCES course_feedback(feedback_id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    response_text TEXT NOT NULL,
    action_items TEXT,
    acknowledgment_type VARCHAR(20) DEFAULT 'standard' CHECK (acknowledgment_type IN ('standard', 'detailed', 'action_plan')),
    
    response_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_public BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feedback Analytics table - aggregate feedback metrics
CREATE TABLE IF NOT EXISTS feedback_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Aggregated course feedback metrics
    total_feedback_count INTEGER DEFAULT 0,
    average_overall_rating DECIMAL(3,2),
    average_content_quality DECIMAL(3,2),
    average_instructor_effectiveness DECIMAL(3,2),
    average_difficulty_rating DECIMAL(3,2),
    average_lab_quality DECIMAL(3,2),
    
    recommendation_rate DECIMAL(5,2), -- percentage who would recommend
    response_rate DECIMAL(5,2), -- percentage of enrolled students who provided feedback
    
    -- Student performance metrics from instructor feedback
    student_feedback_count INTEGER DEFAULT 0,
    average_student_performance DECIMAL(3,2),
    students_at_risk_count INTEGER DEFAULT 0,
    students_exceeding_expectations_count INTEGER DEFAULT 0,
    
    -- Time period for analytics
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    calculation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one analytics record per course per period
    UNIQUE(course_id, period_start, period_end)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_course_feedback_course ON course_feedback(course_id, submission_date);
CREATE INDEX IF NOT EXISTS idx_course_feedback_student ON course_feedback(student_id, submission_date);
CREATE INDEX IF NOT EXISTS idx_course_feedback_instructor ON course_feedback(instructor_id, submission_date);
CREATE INDEX IF NOT EXISTS idx_course_feedback_rating ON course_feedback(overall_rating, submission_date);
CREATE INDEX IF NOT EXISTS idx_course_feedback_status ON course_feedback(status);

CREATE INDEX IF NOT EXISTS idx_student_feedback_instructor ON student_feedback(instructor_id, submission_date);
CREATE INDEX IF NOT EXISTS idx_student_feedback_student ON student_feedback(student_id, submission_date);
CREATE INDEX IF NOT EXISTS idx_student_feedback_course ON student_feedback(course_id, submission_date);
CREATE INDEX IF NOT EXISTS idx_student_feedback_type ON student_feedback(feedback_type, submission_date);
CREATE INDEX IF NOT EXISTS idx_student_feedback_status ON student_feedback(status);
CREATE INDEX IF NOT EXISTS idx_student_feedback_shared ON student_feedback(is_shared_with_student);

CREATE INDEX IF NOT EXISTS idx_feedback_responses_course_feedback ON feedback_responses(course_feedback_id);
CREATE INDEX IF NOT EXISTS idx_feedback_responses_instructor ON feedback_responses(instructor_id, response_date);

CREATE INDEX IF NOT EXISTS idx_feedback_analytics_course ON feedback_analytics(course_id, calculation_date);
CREATE INDEX IF NOT EXISTS idx_feedback_analytics_instructor ON feedback_analytics(instructor_id, calculation_date);

-- Triggers for updated_at fields
CREATE OR REPLACE FUNCTION update_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_course_feedback_updated_at
    BEFORE UPDATE ON course_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

CREATE TRIGGER trg_student_feedback_updated_at
    BEFORE UPDATE ON student_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

CREATE TRIGGER trg_feedback_responses_updated_at
    BEFORE UPDATE ON feedback_responses
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

CREATE TRIGGER trg_feedback_analytics_updated_at
    BEFORE UPDATE ON feedback_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

-- Views for common queries
CREATE OR REPLACE VIEW course_feedback_summary AS
SELECT 
    cf.course_id,
    c.title as course_title,
    cf.instructor_id,
    u.full_name as instructor_name,
    COUNT(*) as total_feedback,
    AVG(cf.overall_rating) as avg_overall_rating,
    AVG(cf.content_quality) as avg_content_quality,
    AVG(cf.instructor_effectiveness) as avg_instructor_effectiveness,
    AVG(cf.difficulty_appropriateness) as avg_difficulty_rating,
    AVG(cf.lab_quality) as avg_lab_quality,
    ROUND(
        (COUNT(CASE WHEN cf.would_recommend = true THEN 1 END) * 100.0) / 
        NULLIF(COUNT(CASE WHEN cf.would_recommend IS NOT NULL THEN 1 END), 0), 
        2
    ) as recommendation_rate
FROM course_feedback cf
JOIN courses c ON cf.course_id = c.id
JOIN users u ON cf.instructor_id = u.id
WHERE cf.status = 'active'
GROUP BY cf.course_id, c.title, cf.instructor_id, u.full_name;

CREATE OR REPLACE VIEW student_performance_summary AS
SELECT 
    sf.student_id,
    u.full_name as student_name,
    sf.course_id,
    c.title as course_title,
    sf.instructor_id,
    COUNT(*) as feedback_count,
    AVG(sf.overall_performance) as avg_performance,
    AVG(sf.participation) as avg_participation,
    AVG(sf.lab_performance) as avg_lab_performance,
    AVG(sf.quiz_performance) as avg_quiz_performance,
    sf.progress_assessment,
    sf.expected_outcome,
    MAX(sf.submission_date) as latest_feedback_date
FROM student_feedback sf
JOIN users u ON sf.student_id = u.id
JOIN courses c ON sf.course_id = c.id
WHERE sf.status = 'active'
GROUP BY sf.student_id, u.full_name, sf.course_id, c.title, sf.instructor_id, sf.progress_assessment, sf.expected_outcome;