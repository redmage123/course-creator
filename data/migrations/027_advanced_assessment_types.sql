-- Migration: 027_advanced_assessment_types.sql
-- Enhancement 7: Advanced Assessment Types System
--
-- WHAT: Creates comprehensive database schema for advanced assessment types beyond traditional quizzes
-- WHERE: PostgreSQL database supporting content-management service
-- WHY: Enable diverse assessment methodologies including performance-based, peer review, portfolio,
--      competency-based, and project-based assessments for comprehensive learning evaluation
--
-- Business Requirements:
-- 1. Support multiple assessment types (performance, peer, portfolio, competency, project, rubric)
-- 2. Enable rich rubric-based evaluation with criteria and proficiency levels
-- 3. Track peer reviews with reviewer assignments and feedback
-- 4. Manage portfolio submissions over time
-- 5. Support competency mapping to learning objectives
-- 6. Enable project-based assessments with milestones and deliverables
-- 7. Provide comprehensive analytics and progress tracking
--
-- Created: 2025-11-28

-- ============================================================================
-- ENUM TYPES FOR ASSESSMENT CLASSIFICATION
-- ============================================================================

-- Assessment type classification for different evaluation methodologies
-- Extends beyond traditional quiz types to support diverse pedagogical approaches
CREATE TYPE assessment_type AS ENUM (
    'performance',      -- Practical demonstrations evaluated by instructor
    'peer_review',      -- Work evaluated by peers using structured rubrics
    'portfolio',        -- Collection of work demonstrating growth over time
    'competency',       -- Skill verification against defined competencies
    'project',          -- Comprehensive projects with milestones
    'rubric',           -- General rubric-based evaluation
    'presentation',     -- Live or recorded presentations
    'interview',        -- Oral assessments and interviews
    'simulation',       -- Scenario-based problem solving
    'self_reflection'   -- Self-assessment with guided reflection
);

-- Assessment status lifecycle tracking
-- Supports complex workflows including peer review and multi-stage assessments
CREATE TYPE assessment_status AS ENUM (
    'draft',            -- Created but not yet published
    'published',        -- Available for students
    'in_progress',      -- Student has started
    'submitted',        -- Awaiting evaluation
    'under_review',     -- Being evaluated (peer or instructor)
    'requires_revision',-- Needs student revision
    'completed',        -- Fully evaluated and scored
    'archived'          -- No longer active
);

-- Submission status for individual student work
CREATE TYPE submission_status AS ENUM (
    'not_started',      -- Student hasn't begun
    'in_progress',      -- Work in progress
    'submitted',        -- Ready for review
    'under_review',     -- Currently being evaluated
    'needs_revision',   -- Requires student changes
    'revised',          -- Student has made revisions
    'graded',           -- Evaluation complete
    'approved',         -- Passed/approved
    'rejected'          -- Did not meet requirements
);

-- Proficiency level classification for competency-based assessment
CREATE TYPE proficiency_level AS ENUM (
    'not_demonstrated', -- No evidence of skill
    'emerging',         -- Beginning to show skill
    'developing',       -- Progressing but not proficient
    'proficient',       -- Meets expected standard
    'advanced',         -- Exceeds expectations
    'expert'            -- Demonstrates mastery
);

-- Review type for peer assessments
CREATE TYPE review_type AS ENUM (
    'single_blind',     -- Reviewer knows author, author doesn't know reviewer
    'double_blind',     -- Neither party knows the other
    'open',             -- Both parties know each other
    'collaborative'     -- Group review process
);

-- ============================================================================
-- RUBRIC SYSTEM TABLES
-- Foundation for all rubric-based evaluations
-- ============================================================================

-- Rubrics define the evaluation criteria structure
-- Rubrics can be reused across multiple assessments
CREATE TABLE IF NOT EXISTS assessment_rubrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership and context
    organization_id UUID,
    course_id UUID,
    created_by UUID NOT NULL,

    -- Rubric identity
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Configuration
    is_template BOOLEAN DEFAULT FALSE,          -- Can be used as template
    max_score DECIMAL(10, 2) NOT NULL,          -- Maximum possible score
    passing_score DECIMAL(10, 2),               -- Minimum score to pass
    passing_percentage DECIMAL(5, 2) DEFAULT 70.0, -- Alternative passing threshold

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,             -- Tags for organization
    version INTEGER DEFAULT 1,                   -- For tracking changes
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_passing_score CHECK (passing_score IS NULL OR passing_score <= max_score),
    CONSTRAINT valid_passing_percentage CHECK (passing_percentage >= 0 AND passing_percentage <= 100)
);

-- Rubric criteria define individual evaluation dimensions
-- Each criterion has multiple proficiency levels with descriptions
CREATE TABLE IF NOT EXISTS rubric_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_id UUID NOT NULL REFERENCES assessment_rubrics(id) ON DELETE CASCADE,

    -- Criterion definition
    name VARCHAR(255) NOT NULL,
    description TEXT,                           -- What is being evaluated
    weight DECIMAL(5, 2) DEFAULT 1.0,          -- Relative importance (for weighted scoring)
    max_points DECIMAL(10, 2) NOT NULL,        -- Maximum points for this criterion

    -- Order and organization
    sort_order INTEGER DEFAULT 0,
    category VARCHAR(100),                      -- Group related criteria

    -- Configuration
    is_required BOOLEAN DEFAULT TRUE,          -- Must be scored to complete evaluation
    allow_partial_credit BOOLEAN DEFAULT TRUE, -- Enable fractional scoring

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_weight CHECK (weight > 0),
    CONSTRAINT valid_max_points CHECK (max_points > 0)
);

-- Performance levels define the proficiency descriptions for each criterion
-- Provides clear expectations and consistent evaluation
CREATE TABLE IF NOT EXISTS rubric_performance_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_id UUID NOT NULL REFERENCES rubric_criteria(id) ON DELETE CASCADE,

    -- Level definition
    level proficiency_level NOT NULL,
    name VARCHAR(100) NOT NULL,                 -- Display name (e.g., "Excellent", "Needs Improvement")
    description TEXT NOT NULL,                  -- What this level looks like

    -- Scoring
    points DECIMAL(10, 2) NOT NULL,            -- Points awarded for this level
    percentage_of_max DECIMAL(5, 2),           -- Alternative: percentage of criterion max

    -- Visual indicators
    color VARCHAR(7),                          -- Hex color for UI display
    icon VARCHAR(50),                          -- Icon identifier

    -- Order
    sort_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_points CHECK (points >= 0),
    CONSTRAINT unique_criterion_level UNIQUE (criterion_id, level)
);

-- ============================================================================
-- ASSESSMENT DEFINITION TABLES
-- Define assessments that can be assigned to students
-- ============================================================================

-- Main assessment definition table
-- Stores configuration for all assessment types
CREATE TABLE IF NOT EXISTS advanced_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership and context
    organization_id UUID,
    course_id UUID NOT NULL,
    module_id UUID,                            -- Optional: within specific module
    created_by UUID NOT NULL,

    -- Assessment identity
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,                          -- Detailed instructions for students

    -- Type and configuration
    assessment_type assessment_type NOT NULL,
    status assessment_status DEFAULT 'draft',
    rubric_id UUID REFERENCES assessment_rubrics(id),

    -- Scoring configuration
    max_score DECIMAL(10, 2) DEFAULT 100.0,
    passing_score DECIMAL(10, 2),
    weight DECIMAL(5, 2) DEFAULT 1.0,          -- Weight in course grade

    -- Timing
    available_from TIMESTAMP WITH TIME ZONE,
    available_until TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    late_submission_allowed BOOLEAN DEFAULT FALSE,
    late_penalty_percentage DECIMAL(5, 2) DEFAULT 0,
    time_limit_minutes INTEGER,                 -- Optional time limit

    -- Attempt configuration
    max_attempts INTEGER DEFAULT 1,
    best_attempt_counts BOOLEAN DEFAULT TRUE,   -- Use best vs. latest attempt
    allow_revision BOOLEAN DEFAULT TRUE,

    -- Peer review specific settings
    peer_review_enabled BOOLEAN DEFAULT FALSE,
    peer_review_type review_type,
    min_peer_reviews INTEGER DEFAULT 3,
    peer_review_rubric_id UUID REFERENCES assessment_rubrics(id),

    -- Competency mapping
    competencies JSONB DEFAULT '[]'::jsonb,     -- List of competency IDs
    learning_objectives JSONB DEFAULT '[]'::jsonb, -- Mapped learning objectives

    -- Project-specific settings
    milestones JSONB DEFAULT '[]'::jsonb,       -- Project milestones with deadlines
    deliverables JSONB DEFAULT '[]'::jsonb,     -- Required deliverables

    -- Portfolio-specific settings
    required_artifacts INTEGER,                  -- Minimum artifacts for portfolio
    artifact_types JSONB DEFAULT '[]'::jsonb,   -- Allowed artifact types

    -- Resources and attachments
    resources JSONB DEFAULT '[]'::jsonb,        -- Reference materials, templates
    attachments JSONB DEFAULT '[]'::jsonb,      -- Files, media

    -- Analytics configuration
    analytics_enabled BOOLEAN DEFAULT TRUE,
    track_time_on_task BOOLEAN DEFAULT TRUE,

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_max_score CHECK (max_score > 0),
    CONSTRAINT valid_weight CHECK (weight > 0),
    CONSTRAINT valid_dates CHECK (available_until IS NULL OR available_from IS NULL OR available_until > available_from)
);

-- ============================================================================
-- SUBMISSION AND EVALUATION TABLES
-- Track student work and evaluations
-- ============================================================================

-- Student submissions for assessments
CREATE TABLE IF NOT EXISTS assessment_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES advanced_assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL,

    -- Submission tracking
    attempt_number INTEGER DEFAULT 1,
    status submission_status DEFAULT 'not_started',

    -- Content
    content TEXT,                               -- Text content for written assessments
    attachments JSONB DEFAULT '[]'::jsonb,      -- Files, videos, artifacts
    portfolio_artifacts JSONB DEFAULT '[]'::jsonb, -- For portfolio assessments

    -- Project-specific
    milestone_progress JSONB DEFAULT '{}'::jsonb, -- Progress on each milestone
    deliverable_status JSONB DEFAULT '{}'::jsonb, -- Status of each deliverable

    -- Self-reflection
    self_reflection TEXT,                       -- Student's self-assessment
    reflection_responses JSONB DEFAULT '{}'::jsonb, -- Structured reflection answers

    -- Scoring
    raw_score DECIMAL(10, 2),                   -- Score before adjustments
    adjusted_score DECIMAL(10, 2),              -- Score after late penalty, etc.
    final_score DECIMAL(10, 2),                 -- Final recorded score
    percentage DECIMAL(5, 2),
    passed BOOLEAN,

    -- Feedback
    instructor_feedback TEXT,
    private_notes TEXT,                         -- Internal notes not shown to student

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE,
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by UUID,

    -- Time tracking
    time_spent_minutes INTEGER DEFAULT 0,
    is_late BOOLEAN DEFAULT FALSE,
    late_days INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_submission_attempt UNIQUE (assessment_id, student_id, attempt_number)
);

-- Individual rubric criterion evaluations
-- One record per criterion per submission
CREATE TABLE IF NOT EXISTS rubric_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES assessment_submissions(id) ON DELETE CASCADE,
    criterion_id UUID NOT NULL REFERENCES rubric_criteria(id) ON DELETE CASCADE,

    -- Evaluation
    evaluated_by UUID NOT NULL,
    proficiency_level proficiency_level,
    points_awarded DECIMAL(10, 2),

    -- Feedback
    feedback TEXT,
    strengths TEXT,
    areas_for_improvement TEXT,

    -- Evidence
    evidence_references JSONB DEFAULT '[]'::jsonb, -- References to specific parts of submission

    -- Timestamps
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_evaluation UNIQUE (submission_id, criterion_id, evaluated_by)
);

-- ============================================================================
-- PEER REVIEW TABLES
-- Manage peer assessment process
-- ============================================================================

-- Peer review assignments
-- Links reviewers to submissions
CREATE TABLE IF NOT EXISTS peer_review_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES assessment_submissions(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL,

    -- Assignment details
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP WITH TIME ZONE,

    -- Review status
    status submission_status DEFAULT 'not_started',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Review configuration
    is_anonymous BOOLEAN DEFAULT TRUE,          -- Hide reviewer identity from author
    show_author_to_reviewer BOOLEAN DEFAULT FALSE, -- Hide author from reviewer

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_review_assignment UNIQUE (submission_id, reviewer_id)
);

-- Peer reviews (the actual feedback)
CREATE TABLE IF NOT EXISTS peer_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES peer_review_assignments(id) ON DELETE CASCADE,
    submission_id UUID NOT NULL REFERENCES assessment_submissions(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL,

    -- Rubric-based evaluation (if rubric exists)
    rubric_scores JSONB DEFAULT '{}'::jsonb,    -- criterion_id: {level, points, feedback}

    -- General feedback
    overall_score DECIMAL(10, 2),
    overall_feedback TEXT,
    strengths TEXT,
    areas_for_improvement TEXT,
    specific_suggestions TEXT,

    -- Review quality (meta-evaluation)
    helpfulness_rating INTEGER,                 -- 1-5 rating by submission author
    helpfulness_feedback TEXT,
    instructor_quality_score DECIMAL(5, 2),     -- Instructor rating of review quality

    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_helpfulness_rating CHECK (helpfulness_rating IS NULL OR helpfulness_rating BETWEEN 1 AND 5)
);

-- ============================================================================
-- COMPETENCY MANAGEMENT TABLES
-- Define and track competencies
-- ============================================================================

-- Competency definitions
CREATE TABLE IF NOT EXISTS competencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,

    -- Competency identity
    code VARCHAR(50) NOT NULL,                  -- Short code (e.g., "PROG-001")
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Hierarchy
    parent_id UUID REFERENCES competencies(id),
    level INTEGER DEFAULT 1,                    -- Depth in hierarchy

    -- Requirements
    required_proficiency proficiency_level DEFAULT 'proficient',
    evidence_requirements TEXT,                 -- What evidence is needed

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_competency_code UNIQUE (organization_id, code)
);

-- Student competency progress
CREATE TABLE IF NOT EXISTS competency_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    competency_id UUID NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,

    -- Progress tracking
    current_level proficiency_level DEFAULT 'not_demonstrated',
    previous_level proficiency_level,

    -- Evidence
    evidence_submissions JSONB DEFAULT '[]'::jsonb, -- Submission IDs demonstrating competency
    assessor_notes TEXT,

    -- Verification
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID,

    -- Timestamps
    first_demonstrated_at TIMESTAMP WITH TIME ZONE,
    level_achieved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_student_competency UNIQUE (student_id, competency_id)
);

-- ============================================================================
-- PROJECT MANAGEMENT TABLES
-- Track project-based assessments
-- ============================================================================

-- Project milestones
CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES advanced_assessments(id) ON DELETE CASCADE,

    -- Milestone definition
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,

    -- Requirements
    required_deliverables JSONB DEFAULT '[]'::jsonb,
    acceptance_criteria TEXT,

    -- Timing
    due_date TIMESTAMP WITH TIME ZONE,
    weight DECIMAL(5, 2) DEFAULT 1.0,           -- Weight in overall project grade

    -- Scoring
    max_points DECIMAL(10, 2),
    rubric_id UUID REFERENCES assessment_rubrics(id),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Milestone submissions
CREATE TABLE IF NOT EXISTS milestone_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    milestone_id UUID NOT NULL REFERENCES project_milestones(id) ON DELETE CASCADE,
    submission_id UUID NOT NULL REFERENCES assessment_submissions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL,

    -- Submission content
    content TEXT,
    attachments JSONB DEFAULT '[]'::jsonb,

    -- Status and scoring
    status submission_status DEFAULT 'not_started',
    score DECIMAL(10, 2),
    feedback TEXT,

    -- Timing
    submitted_at TIMESTAMP WITH TIME ZONE,
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by UUID,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_milestone_submission UNIQUE (milestone_id, submission_id)
);

-- ============================================================================
-- PORTFOLIO ARTIFACT TABLES
-- Track portfolio collections
-- ============================================================================

-- Portfolio artifacts (individual pieces in a portfolio)
CREATE TABLE IF NOT EXISTS portfolio_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES assessment_submissions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL,

    -- Artifact identity
    title VARCHAR(255) NOT NULL,
    description TEXT,
    artifact_type VARCHAR(100),                 -- Document, video, code, image, etc.

    -- Content
    content_url VARCHAR(2048),                  -- URL to artifact
    content_text TEXT,                          -- Text content if applicable
    attachments JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    creation_date TIMESTAMP WITH TIME ZONE,     -- When artifact was originally created
    context TEXT,                               -- Why this artifact is included
    tags JSONB DEFAULT '[]'::jsonb,

    -- Reflection
    student_reflection TEXT,                    -- Student explanation of artifact
    learning_demonstrated TEXT,                 -- What learning this shows

    -- Evaluation
    score DECIMAL(10, 2),
    feedback TEXT,
    evaluated_by UUID,
    evaluated_at TIMESTAMP WITH TIME ZONE,

    -- Sort order in portfolio
    sort_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,          -- Highlighted artifact

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ANALYTICS TABLES
-- Track assessment analytics and insights
-- ============================================================================

-- Assessment analytics aggregates
CREATE TABLE IF NOT EXISTS assessment_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES advanced_assessments(id) ON DELETE CASCADE,

    -- Participation metrics
    total_students INTEGER DEFAULT 0,
    submissions_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    in_progress_count INTEGER DEFAULT 0,

    -- Score metrics
    average_score DECIMAL(10, 2),
    median_score DECIMAL(10, 2),
    highest_score DECIMAL(10, 2),
    lowest_score DECIMAL(10, 2),
    score_std_deviation DECIMAL(10, 2),

    -- Pass/fail metrics
    pass_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    pass_rate DECIMAL(5, 2),

    -- Time metrics
    average_time_minutes INTEGER,
    median_time_minutes INTEGER,

    -- Criterion-level analytics (for rubric assessments)
    criterion_averages JSONB DEFAULT '{}'::jsonb, -- criterion_id: average_score
    criterion_distributions JSONB DEFAULT '{}'::jsonb, -- criterion_id: {level: count}

    -- Peer review metrics (if applicable)
    peer_review_completion_rate DECIMAL(5, 2),
    average_peer_review_score DECIMAL(10, 2),
    peer_review_variance DECIMAL(10, 2),

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Rubric indexes
CREATE INDEX idx_assessment_rubrics_org ON assessment_rubrics(organization_id);
CREATE INDEX idx_assessment_rubrics_course ON assessment_rubrics(course_id);
CREATE INDEX idx_assessment_rubrics_template ON assessment_rubrics(is_template) WHERE is_template = TRUE;
CREATE INDEX idx_rubric_criteria_rubric ON rubric_criteria(rubric_id);
CREATE INDEX idx_rubric_performance_levels_criterion ON rubric_performance_levels(criterion_id);

-- Assessment indexes
CREATE INDEX idx_advanced_assessments_org ON advanced_assessments(organization_id);
CREATE INDEX idx_advanced_assessments_course ON advanced_assessments(course_id);
CREATE INDEX idx_advanced_assessments_type ON advanced_assessments(assessment_type);
CREATE INDEX idx_advanced_assessments_status ON advanced_assessments(status);
CREATE INDEX idx_advanced_assessments_due ON advanced_assessments(due_date);
CREATE INDEX idx_advanced_assessments_available ON advanced_assessments(available_from, available_until);

-- Submission indexes
CREATE INDEX idx_assessment_submissions_assessment ON assessment_submissions(assessment_id);
CREATE INDEX idx_assessment_submissions_student ON assessment_submissions(student_id);
CREATE INDEX idx_assessment_submissions_status ON assessment_submissions(status);
CREATE INDEX idx_assessment_submissions_graded ON assessment_submissions(graded_at);
CREATE INDEX idx_rubric_evaluations_submission ON rubric_evaluations(submission_id);

-- Peer review indexes
CREATE INDEX idx_peer_review_assignments_submission ON peer_review_assignments(submission_id);
CREATE INDEX idx_peer_review_assignments_reviewer ON peer_review_assignments(reviewer_id);
CREATE INDEX idx_peer_reviews_assignment ON peer_reviews(assignment_id);
CREATE INDEX idx_peer_reviews_reviewer ON peer_reviews(reviewer_id);

-- Competency indexes
CREATE INDEX idx_competencies_org ON competencies(organization_id);
CREATE INDEX idx_competencies_parent ON competencies(parent_id);
CREATE INDEX idx_competency_progress_student ON competency_progress(student_id);
CREATE INDEX idx_competency_progress_competency ON competency_progress(competency_id);

-- Project indexes
CREATE INDEX idx_project_milestones_assessment ON project_milestones(assessment_id);
CREATE INDEX idx_milestone_submissions_milestone ON milestone_submissions(milestone_id);

-- Portfolio indexes
CREATE INDEX idx_portfolio_artifacts_submission ON portfolio_artifacts(submission_id);
CREATE INDEX idx_portfolio_artifacts_student ON portfolio_artifacts(student_id);
CREATE INDEX idx_portfolio_artifacts_type ON portfolio_artifacts(artifact_type);

-- Analytics indexes
CREATE INDEX idx_assessment_analytics_assessment ON assessment_analytics(assessment_id);

-- GIN indexes for JSONB columns
CREATE INDEX idx_advanced_assessments_competencies ON advanced_assessments USING GIN (competencies);
CREATE INDEX idx_advanced_assessments_tags ON advanced_assessments USING GIN (tags);
CREATE INDEX idx_competencies_tags ON competencies USING GIN (tags);
CREATE INDEX idx_portfolio_artifacts_tags ON portfolio_artifacts USING GIN (tags);

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Update timestamp trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_advanced_assessment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for all tables with updated_at
DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'assessment_rubrics',
        'rubric_criteria',
        'advanced_assessments',
        'assessment_submissions',
        'rubric_evaluations',
        'peer_review_assignments',
        'peer_reviews',
        'competencies',
        'competency_progress',
        'project_milestones',
        'milestone_submissions',
        'portfolio_artifacts',
        'assessment_analytics'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_timestamp ON %I;
            CREATE TRIGGER update_%I_timestamp
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_advanced_assessment_timestamp();
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END;
$$;

-- ============================================================================
-- INITIAL SEED DATA
-- Sample rubric templates for common assessment types
-- ============================================================================

-- Insert sample rubric template for presentation assessments
INSERT INTO assessment_rubrics (id, name, description, is_template, max_score, passing_score, passing_percentage, tags)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Presentation Assessment Rubric',
    'Standard rubric for evaluating student presentations including content, delivery, and visual aids.',
    TRUE,
    100.0,
    70.0,
    70.0,
    '["presentation", "communication", "template"]'::jsonb
);

-- Insert criteria for presentation rubric
INSERT INTO rubric_criteria (rubric_id, name, description, weight, max_points, sort_order, category, is_required)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'Content Quality', 'Accuracy, depth, and relevance of presented content', 2.0, 30.0, 1, 'Content', TRUE),
    ('00000000-0000-0000-0000-000000000001', 'Organization', 'Logical flow, clear structure, effective transitions', 1.5, 20.0, 2, 'Content', TRUE),
    ('00000000-0000-0000-0000-000000000001', 'Delivery', 'Voice projection, pacing, eye contact, confidence', 1.5, 25.0, 3, 'Delivery', TRUE),
    ('00000000-0000-0000-0000-000000000001', 'Visual Aids', 'Quality and effectiveness of slides/materials', 1.0, 15.0, 4, 'Materials', TRUE),
    ('00000000-0000-0000-0000-000000000001', 'Q&A Handling', 'Ability to respond to questions effectively', 1.0, 10.0, 5, 'Delivery', FALSE);

-- Insert sample rubric template for peer code review
INSERT INTO assessment_rubrics (id, name, description, is_template, max_score, passing_score, passing_percentage, tags)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    'Peer Code Review Rubric',
    'Rubric for evaluating code quality in peer review assessments.',
    TRUE,
    100.0,
    70.0,
    70.0,
    '["code", "peer-review", "programming", "template"]'::jsonb
);

-- Insert criteria for code review rubric
INSERT INTO rubric_criteria (rubric_id, name, description, weight, max_points, sort_order, category, is_required)
VALUES
    ('00000000-0000-0000-0000-000000000002', 'Functionality', 'Code works correctly and meets requirements', 2.0, 30.0, 1, 'Technical', TRUE),
    ('00000000-0000-0000-0000-000000000002', 'Code Quality', 'Clean, readable, well-organized code', 1.5, 25.0, 2, 'Technical', TRUE),
    ('00000000-0000-0000-0000-000000000002', 'Documentation', 'Clear comments and documentation', 1.0, 15.0, 3, 'Documentation', TRUE),
    ('00000000-0000-0000-0000-000000000002', 'Error Handling', 'Proper handling of edge cases and errors', 1.0, 15.0, 4, 'Technical', TRUE),
    ('00000000-0000-0000-0000-000000000002', 'Testing', 'Adequate test coverage and quality', 1.0, 15.0, 5, 'Quality', TRUE);

-- Insert sample rubric template for portfolio assessment
INSERT INTO assessment_rubrics (id, name, description, is_template, max_score, passing_score, passing_percentage, tags)
VALUES (
    '00000000-0000-0000-0000-000000000003',
    'Portfolio Assessment Rubric',
    'Comprehensive rubric for evaluating student portfolios demonstrating growth and learning.',
    TRUE,
    100.0,
    70.0,
    70.0,
    '["portfolio", "growth", "reflection", "template"]'::jsonb
);

-- Insert criteria for portfolio rubric
INSERT INTO rubric_criteria (rubric_id, name, description, weight, max_points, sort_order, category, is_required)
VALUES
    ('00000000-0000-0000-0000-000000000003', 'Artifact Quality', 'Quality and relevance of included artifacts', 2.0, 30.0, 1, 'Content', TRUE),
    ('00000000-0000-0000-0000-000000000003', 'Growth Evidence', 'Clear demonstration of learning and improvement over time', 2.0, 25.0, 2, 'Development', TRUE),
    ('00000000-0000-0000-0000-000000000003', 'Self-Reflection', 'Depth and insight of reflective commentary', 1.5, 20.0, 3, 'Reflection', TRUE),
    ('00000000-0000-0000-0000-000000000003', 'Organization', 'Logical organization and professional presentation', 1.0, 15.0, 4, 'Presentation', TRUE),
    ('00000000-0000-0000-0000-000000000003', 'Goal Alignment', 'Alignment of artifacts with learning objectives', 1.0, 10.0, 5, 'Alignment', TRUE);

COMMENT ON TABLE assessment_rubrics IS 'Rubric definitions for structured assessment evaluation';
COMMENT ON TABLE rubric_criteria IS 'Individual evaluation criteria within rubrics';
COMMENT ON TABLE rubric_performance_levels IS 'Proficiency level descriptions for each criterion';
COMMENT ON TABLE advanced_assessments IS 'Main assessment definitions supporting multiple assessment types';
COMMENT ON TABLE assessment_submissions IS 'Student submissions for assessments';
COMMENT ON TABLE rubric_evaluations IS 'Individual criterion evaluations for submissions';
COMMENT ON TABLE peer_review_assignments IS 'Peer reviewer assignments to submissions';
COMMENT ON TABLE peer_reviews IS 'Peer review feedback and scores';
COMMENT ON TABLE competencies IS 'Competency definitions for competency-based assessment';
COMMENT ON TABLE competency_progress IS 'Student progress on competencies';
COMMENT ON TABLE project_milestones IS 'Milestones for project-based assessments';
COMMENT ON TABLE milestone_submissions IS 'Student submissions for project milestones';
COMMENT ON TABLE portfolio_artifacts IS 'Individual artifacts in portfolio assessments';
COMMENT ON TABLE assessment_analytics IS 'Aggregated analytics for assessments';
