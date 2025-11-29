-- Migration: 021_adaptive_learning_paths.sql
-- WHAT: Creates tables for adaptive learning paths system
-- WHERE: Used by course-management and analytics services
-- WHY: Enables personalized learning journeys with prerequisite enforcement,
--      difficulty adjustment, and AI-driven path recommendations

-- ============================================================================
-- PREREQUISITE RULES TABLE
-- ============================================================================
-- WHAT: Defines prerequisite relationships between learning content
-- WHERE: Referenced by enrollment service and path recommendation engine
-- WHY: Enforces learning sequence requirements and enables prerequisite validation

CREATE TABLE IF NOT EXISTS prerequisite_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The content that requires prerequisites
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('course', 'module', 'lesson', 'quiz', 'lab')),
    target_id UUID NOT NULL,

    -- The required prerequisite content
    prerequisite_type VARCHAR(50) NOT NULL CHECK (prerequisite_type IN ('course', 'module', 'lesson', 'quiz', 'lab')),
    prerequisite_id UUID NOT NULL,

    -- Requirement configuration
    requirement_type VARCHAR(30) NOT NULL DEFAULT 'completion'
        CHECK (requirement_type IN ('completion', 'minimum_score', 'time_spent', 'mastery_level')),
    requirement_value DECIMAL(5,2) DEFAULT NULL, -- e.g., 80.00 for 80% score requirement

    -- Organizational context
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,

    -- Rule metadata
    is_mandatory BOOLEAN NOT NULL DEFAULT true,
    bypass_allowed BOOLEAN NOT NULL DEFAULT false,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    -- Prevent duplicate rules
    CONSTRAINT unique_prerequisite_rule UNIQUE (target_type, target_id, prerequisite_type, prerequisite_id)
);

CREATE INDEX idx_prerequisite_rules_target ON prerequisite_rules(target_type, target_id);
CREATE INDEX idx_prerequisite_rules_prereq ON prerequisite_rules(prerequisite_type, prerequisite_id);
CREATE INDEX idx_prerequisite_rules_org ON prerequisite_rules(organization_id);

COMMENT ON TABLE prerequisite_rules IS 'Defines prerequisite relationships between learning content items';

-- ============================================================================
-- LEARNING PATHS TABLE
-- ============================================================================
-- WHAT: Stores personalized learning paths for students
-- WHERE: Created by adaptive learning service, displayed in student dashboard
-- WHY: Provides students with customized learning journeys based on their
--      goals, performance, and learning style

CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Path ownership
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,

    -- Path identification
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Path configuration
    path_type VARCHAR(30) NOT NULL DEFAULT 'recommended'
        CHECK (path_type IN ('recommended', 'custom', 'mandatory', 'remedial', 'accelerated')),
    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'adaptive'
        CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'adaptive')),

    -- Progress tracking
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('draft', 'active', 'paused', 'completed', 'abandoned')),
    overall_progress DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (overall_progress >= 0 AND overall_progress <= 100),
    estimated_duration_hours INTEGER,
    actual_duration_hours INTEGER DEFAULT 0,

    -- Completion tracking
    total_nodes INTEGER NOT NULL DEFAULT 0,
    completed_nodes INTEGER NOT NULL DEFAULT 0,
    current_node_id UUID, -- References learning_path_nodes(id), added after table creation

    -- Adaptive settings
    adapt_to_performance BOOLEAN NOT NULL DEFAULT true,
    adapt_to_pace BOOLEAN NOT NULL DEFAULT true,
    target_completion_date DATE,

    -- AI/ML metadata
    recommendation_confidence DECIMAL(3,2) CHECK (recommendation_confidence >= 0 AND recommendation_confidence <= 1),
    last_adaptation_at TIMESTAMP WITH TIME ZONE,
    adaptation_count INTEGER NOT NULL DEFAULT 0,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_learning_paths_student ON learning_paths(student_id);
CREATE INDEX idx_learning_paths_org ON learning_paths(organization_id);
CREATE INDEX idx_learning_paths_status ON learning_paths(status);
CREATE INDEX idx_learning_paths_track ON learning_paths(track_id);

COMMENT ON TABLE learning_paths IS 'Personalized learning paths for students with adaptive progression';

-- ============================================================================
-- LEARNING PATH NODES TABLE
-- ============================================================================
-- WHAT: Individual nodes (steps) within a learning path
-- WHERE: Linked to learning_paths, references courses/modules/content
-- WHY: Enables granular progress tracking and flexible path composition

CREATE TABLE IF NOT EXISTS learning_path_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Parent path
    learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,

    -- Node content reference
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('course', 'module', 'lesson', 'quiz', 'lab', 'assessment', 'milestone')),
    content_id UUID NOT NULL,

    -- Sequencing
    sequence_order INTEGER NOT NULL,
    parent_node_id UUID REFERENCES learning_path_nodes(id) ON DELETE SET NULL,

    -- Node status
    status VARCHAR(20) NOT NULL DEFAULT 'locked'
        CHECK (status IN ('locked', 'available', 'in_progress', 'completed', 'skipped', 'failed')),
    is_required BOOLEAN NOT NULL DEFAULT true,
    is_unlocked BOOLEAN NOT NULL DEFAULT false,

    -- Progress tracking
    progress_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    score DECIMAL(5,2) CHECK (score >= 0 AND score <= 100),
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER,

    -- Time tracking
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER DEFAULT 0,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,

    -- Adaptive metadata
    difficulty_adjustment DECIMAL(3,2) DEFAULT 0.00, -- -1.0 to +1.0 adjustment factor
    was_recommended BOOLEAN NOT NULL DEFAULT false,
    recommendation_reason TEXT,

    -- Unlock conditions (JSONB for flexibility)
    unlock_conditions JSONB DEFAULT '{}',
    -- Example: {"min_score": 70, "prerequisites": ["node-uuid-1", "node-uuid-2"]}

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Unique sequence per path
    CONSTRAINT unique_path_sequence UNIQUE (learning_path_id, sequence_order)
);

-- Add foreign key for current_node_id after learning_path_nodes exists
ALTER TABLE learning_paths
    ADD CONSTRAINT fk_current_node
    FOREIGN KEY (current_node_id) REFERENCES learning_path_nodes(id) ON DELETE SET NULL;

CREATE INDEX idx_path_nodes_path ON learning_path_nodes(learning_path_id);
CREATE INDEX idx_path_nodes_content ON learning_path_nodes(content_type, content_id);
CREATE INDEX idx_path_nodes_status ON learning_path_nodes(status);
CREATE INDEX idx_path_nodes_sequence ON learning_path_nodes(learning_path_id, sequence_order);

COMMENT ON TABLE learning_path_nodes IS 'Individual steps within a learning path with progress tracking';

-- ============================================================================
-- ADAPTIVE RECOMMENDATIONS TABLE
-- ============================================================================
-- WHAT: Stores AI-generated learning recommendations for students
-- WHERE: Generated by recommendation engine, displayed in student dashboard
-- WHY: Provides actionable next-step suggestions based on performance analytics

CREATE TABLE IF NOT EXISTS adaptive_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recommendation target
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    learning_path_id UUID REFERENCES learning_paths(id) ON DELETE CASCADE,

    -- Recommendation details
    recommendation_type VARCHAR(50) NOT NULL
        CHECK (recommendation_type IN (
            'next_content', 'review_content', 'skip_content',
            'adjust_difficulty', 'take_break', 'practice_more',
            'seek_help', 'accelerate', 'remediation'
        )),

    -- Content reference (what's being recommended)
    content_type VARCHAR(50) CHECK (content_type IN ('course', 'module', 'lesson', 'quiz', 'lab', 'assessment')),
    content_id UUID,

    -- Recommendation metadata
    title VARCHAR(255) NOT NULL,
    description TEXT,
    reason TEXT NOT NULL, -- Explanation of why this is recommended

    -- Priority and confidence
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Performance context (what triggered this recommendation)
    trigger_metrics JSONB DEFAULT '{}',
    -- Example: {"quiz_score": 65, "time_on_task": 120, "attempts": 3}

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'viewed', 'accepted', 'dismissed', 'completed', 'expired')),

    -- Validity period
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,

    -- User interaction
    viewed_at TIMESTAMP WITH TIME ZONE,
    acted_on_at TIMESTAMP WITH TIME ZONE,
    user_feedback VARCHAR(20) CHECK (user_feedback IN ('helpful', 'not_helpful', 'too_easy', 'too_hard')),

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_student ON adaptive_recommendations(student_id);
CREATE INDEX idx_recommendations_path ON adaptive_recommendations(learning_path_id);
CREATE INDEX idx_recommendations_status ON adaptive_recommendations(status);
CREATE INDEX idx_recommendations_type ON adaptive_recommendations(recommendation_type);
CREATE INDEX idx_recommendations_priority ON adaptive_recommendations(priority DESC);
CREATE INDEX idx_recommendations_valid ON adaptive_recommendations(valid_from, valid_until) WHERE status = 'pending';

COMMENT ON TABLE adaptive_recommendations IS 'AI-generated learning recommendations based on student performance';

-- ============================================================================
-- STUDENT MASTERY LEVELS TABLE
-- ============================================================================
-- WHAT: Tracks mastery levels for specific skills/topics per student
-- WHERE: Updated by assessment results, used by adaptive engine
-- WHY: Enables fine-grained skill tracking for personalized recommendations

CREATE TABLE IF NOT EXISTS student_mastery_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Student and skill reference
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_topic VARCHAR(255) NOT NULL, -- e.g., "Python Loops", "SQL Joins"

    -- Organizational context
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    course_id UUID, -- Optional: track mastery per course

    -- Mastery tracking
    mastery_level VARCHAR(20) NOT NULL DEFAULT 'novice'
        CHECK (mastery_level IN ('novice', 'beginner', 'intermediate', 'proficient', 'expert', 'master')),
    mastery_score DECIMAL(5,2) NOT NULL DEFAULT 0.00 CHECK (mastery_score >= 0 AND mastery_score <= 100),

    -- Evidence tracking
    assessments_completed INTEGER NOT NULL DEFAULT 0,
    assessments_passed INTEGER NOT NULL DEFAULT 0,
    average_score DECIMAL(5,2),
    best_score DECIMAL(5,2),

    -- Time and practice tracking
    total_practice_time_minutes INTEGER NOT NULL DEFAULT 0,
    last_practiced_at TIMESTAMP WITH TIME ZONE,
    practice_streak_days INTEGER NOT NULL DEFAULT 0,

    -- Decay and retention (for spaced repetition)
    last_assessment_at TIMESTAMP WITH TIME ZONE,
    retention_estimate DECIMAL(3,2) DEFAULT 1.00, -- Estimated knowledge retention (0-1)
    next_review_recommended_at TIMESTAMP WITH TIME ZONE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- One mastery record per student per skill per course
    CONSTRAINT unique_student_skill_mastery UNIQUE (student_id, skill_topic, course_id)
);

CREATE INDEX idx_mastery_student ON student_mastery_levels(student_id);
CREATE INDEX idx_mastery_skill ON student_mastery_levels(skill_topic);
CREATE INDEX idx_mastery_level ON student_mastery_levels(mastery_level);
CREATE INDEX idx_mastery_review ON student_mastery_levels(next_review_recommended_at) WHERE next_review_recommended_at IS NOT NULL;

COMMENT ON TABLE student_mastery_levels IS 'Fine-grained skill mastery tracking for adaptive learning';

-- ============================================================================
-- PATH ADAPTATION HISTORY TABLE
-- ============================================================================
-- WHAT: Audit log of all adaptations made to learning paths
-- WHERE: Written by adaptive service, used for ML training and debugging
-- WHY: Enables analysis of adaptation effectiveness and model improvement

CREATE TABLE IF NOT EXISTS path_adaptation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Adaptation details
    adaptation_type VARCHAR(50) NOT NULL
        CHECK (adaptation_type IN (
            'difficulty_increase', 'difficulty_decrease',
            'content_added', 'content_removed', 'content_reordered',
            'pace_accelerated', 'pace_slowed',
            'remediation_added', 'milestone_adjusted'
        )),

    -- What changed
    previous_state JSONB NOT NULL,
    new_state JSONB NOT NULL,
    affected_node_ids UUID[],

    -- Why it changed
    trigger_reason TEXT NOT NULL,
    trigger_metrics JSONB DEFAULT '{}',

    -- Model information
    model_version VARCHAR(50),
    confidence_score DECIMAL(3,2),

    -- Outcome tracking (filled in later)
    outcome_measured_at TIMESTAMP WITH TIME ZONE,
    outcome_positive BOOLEAN,
    outcome_notes TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_adaptation_history_path ON path_adaptation_history(learning_path_id);
CREATE INDEX idx_adaptation_history_student ON path_adaptation_history(student_id);
CREATE INDEX idx_adaptation_history_type ON path_adaptation_history(adaptation_type);
CREATE INDEX idx_adaptation_history_created ON path_adaptation_history(created_at);

COMMENT ON TABLE path_adaptation_history IS 'Audit trail of all learning path adaptations for analysis';

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Active learning paths with progress summary
CREATE OR REPLACE VIEW v_active_learning_paths AS
SELECT
    lp.id,
    lp.student_id,
    lp.name,
    lp.path_type,
    lp.difficulty_level,
    lp.overall_progress,
    lp.total_nodes,
    lp.completed_nodes,
    lp.status,
    lp.started_at,
    lp.target_completion_date,
    u.username AS student_name,
    o.name AS organization_name,
    t.name AS track_name,
    CASE
        WHEN lp.target_completion_date IS NOT NULL AND lp.target_completion_date < CURRENT_DATE
        THEN true
        ELSE false
    END AS is_overdue
FROM learning_paths lp
JOIN users u ON lp.student_id = u.id
LEFT JOIN organizations o ON lp.organization_id = o.id
LEFT JOIN tracks t ON lp.track_id = t.id
WHERE lp.status = 'active';

COMMENT ON VIEW v_active_learning_paths IS 'Active learning paths with student and organization details';

-- View: Pending recommendations by priority
CREATE OR REPLACE VIEW v_pending_recommendations AS
SELECT
    ar.id,
    ar.student_id,
    ar.learning_path_id,
    ar.recommendation_type,
    ar.title,
    ar.description,
    ar.reason,
    ar.priority,
    ar.confidence_score,
    ar.content_type,
    ar.content_id,
    ar.valid_until,
    u.username AS student_name,
    lp.name AS path_name
FROM adaptive_recommendations ar
JOIN users u ON ar.student_id = u.id
LEFT JOIN learning_paths lp ON ar.learning_path_id = lp.id
WHERE ar.status = 'pending'
  AND (ar.valid_until IS NULL OR ar.valid_until > CURRENT_TIMESTAMP)
ORDER BY ar.priority DESC, ar.created_at ASC;

COMMENT ON VIEW v_pending_recommendations IS 'Pending recommendations ordered by priority';

-- ============================================================================
-- FUNCTIONS FOR ADAPTIVE LOGIC
-- ============================================================================

-- Function: Calculate prerequisite completion status
CREATE OR REPLACE FUNCTION check_prerequisites_met(
    p_student_id UUID,
    p_target_type VARCHAR(50),
    p_target_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_unmet_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_unmet_count
    FROM prerequisite_rules pr
    WHERE pr.target_type = p_target_type
      AND pr.target_id = p_target_id
      AND pr.is_mandatory = true
      AND NOT EXISTS (
          SELECT 1 FROM student_course_enrollments sce
          WHERE sce.student_id = p_student_id
            AND sce.enrollment_status = 'completed'
            AND (
                (pr.prerequisite_type = 'course' AND sce.course_instance_id IN (
                    SELECT ci.id FROM course_instances ci WHERE ci.course_id = pr.prerequisite_id
                ))
            )
            AND (
                pr.requirement_type = 'completion'
                OR (pr.requirement_type = 'minimum_score' AND sce.progress_percentage >= pr.requirement_value)
            )
      );

    RETURN v_unmet_count = 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_prerequisites_met IS 'Checks if a student has met all prerequisites for content';

-- Function: Update learning path progress
CREATE OR REPLACE FUNCTION update_learning_path_progress(p_path_id UUID) RETURNS VOID AS $$
DECLARE
    v_total INTEGER;
    v_completed INTEGER;
    v_progress DECIMAL(5,2);
BEGIN
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completed')
    INTO v_total, v_completed
    FROM learning_path_nodes
    WHERE learning_path_id = p_path_id;

    IF v_total > 0 THEN
        v_progress := (v_completed::DECIMAL / v_total) * 100;
    ELSE
        v_progress := 0;
    END IF;

    UPDATE learning_paths
    SET
        total_nodes = v_total,
        completed_nodes = v_completed,
        overall_progress = v_progress,
        updated_at = CURRENT_TIMESTAMP,
        completed_at = CASE WHEN v_completed = v_total AND v_total > 0 THEN CURRENT_TIMESTAMP ELSE NULL END,
        status = CASE WHEN v_completed = v_total AND v_total > 0 THEN 'completed' ELSE status END
    WHERE id = p_path_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_learning_path_progress IS 'Recalculates and updates learning path progress';

-- Trigger: Auto-update path progress when node status changes
CREATE OR REPLACE FUNCTION trigger_update_path_progress() RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_learning_path_progress(NEW.learning_path_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_node_status_change
    AFTER INSERT OR UPDATE OF status ON learning_path_nodes
    FOR EACH ROW
    EXECUTE FUNCTION trigger_update_path_progress();

-- ============================================================================
-- SEED DATA FOR TESTING (Optional - can be removed in production)
-- ============================================================================

-- Insert common skill topics for mastery tracking
INSERT INTO student_mastery_levels (student_id, skill_topic, organization_id, mastery_level, mastery_score)
SELECT
    u.id,
    skill.topic,
    u.organization_id,
    'novice',
    0.00
FROM users u
CROSS JOIN (
    VALUES
        ('Python Fundamentals'),
        ('SQL Basics'),
        ('Data Structures'),
        ('Algorithms'),
        ('Web Development'),
        ('API Design'),
        ('Testing'),
        ('Version Control')
) AS skill(topic)
WHERE u.role_name = 'student'
  AND NOT EXISTS (
      SELECT 1 FROM student_mastery_levels sml
      WHERE sml.student_id = u.id AND sml.skill_topic = skill.topic
  )
LIMIT 100; -- Limit for safety

-- Migration complete
