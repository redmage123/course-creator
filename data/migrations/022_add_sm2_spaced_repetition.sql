-- Migration: 022_add_sm2_spaced_repetition.sql
-- WHAT: Adds SM-2 spaced repetition algorithm fields to student_mastery_levels table
-- WHERE: Used by course-management service's adaptive learning system
-- WHY: Enables evidence-based memory retention scheduling using the SuperMemo 2 algorithm
--      for optimal review timing and long-term knowledge retention

-- ============================================================================
-- SM-2 ALGORITHM FIELDS
-- ============================================================================
-- The SM-2 (SuperMemo 2) algorithm is a spaced repetition algorithm that schedules
-- reviews based on:
--   1. Ease Factor (EF): How easy the material is for the student (1.3-2.5)
--   2. Repetition Count: Consecutive successful reviews (quality >= 3)
--   3. Current Interval: Days until next review
--   4. Quality Rating: User's assessment of recall (0-5 scale)
--
-- Reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2

-- Add ease_factor column
-- WHAT: SuperMemo 2 ease factor representing material difficulty for this student
-- WHERE: Updated after each assessment in record_assessment()
-- WHY: Adjusts review intervals based on how easily the student recalls the material
--      Higher EF = easier material = longer intervals between reviews
ALTER TABLE student_mastery_levels
ADD COLUMN IF NOT EXISTS ease_factor DECIMAL(3,2) NOT NULL DEFAULT 2.50
    CHECK (ease_factor >= 1.30 AND ease_factor <= 2.50);

COMMENT ON COLUMN student_mastery_levels.ease_factor IS
    'SM-2 ease factor (1.3-2.5). Higher values indicate easier recall, resulting in longer review intervals';

-- Add repetition_count column
-- WHAT: Number of consecutive successful reviews (quality >= 3)
-- WHERE: Reset to 0 on failed review, incremented on successful review
-- WHY: Tracks learning progress; higher counts indicate more stable memory
ALTER TABLE student_mastery_levels
ADD COLUMN IF NOT EXISTS repetition_count INTEGER NOT NULL DEFAULT 0
    CHECK (repetition_count >= 0);

COMMENT ON COLUMN student_mastery_levels.repetition_count IS
    'Count of consecutive successful reviews (quality >= 3). Reset to 0 on failure';

-- Add current_interval_days column
-- WHAT: Current inter-repetition interval in days
-- WHERE: Updated by SM-2 algorithm after each assessment
-- WHY: Determines when the next review should occur; grows exponentially with success
ALTER TABLE student_mastery_levels
ADD COLUMN IF NOT EXISTS current_interval_days INTEGER NOT NULL DEFAULT 1
    CHECK (current_interval_days >= 1);

COMMENT ON COLUMN student_mastery_levels.current_interval_days IS
    'Current review interval in days. Grows exponentially with successful reviews';

-- Add last_quality_rating column
-- WHAT: Most recent SM-2 quality rating from assessment (0-5 scale)
-- WHERE: Set during record_assessment() based on score or explicit quality
-- WHY: Quality ratings drive the SM-2 algorithm's scheduling decisions
--      0 = Complete blackout, 5 = Perfect response with no hesitation
ALTER TABLE student_mastery_levels
ADD COLUMN IF NOT EXISTS last_quality_rating INTEGER NOT NULL DEFAULT 0
    CHECK (last_quality_rating >= 0 AND last_quality_rating <= 5);

COMMENT ON COLUMN student_mastery_levels.last_quality_rating IS
    'Most recent SM-2 quality rating (0-5). 0=blackout, 3=correct with difficulty, 5=perfect recall';

-- ============================================================================
-- PERFORMANCE INDEX
-- ============================================================================
-- WHAT: Composite index for efficient SM-2 review scheduling queries
-- WHERE: Used by get_due_for_review() and batch review scheduling
-- WHY: Optimizes queries that find items needing review based on multiple criteria

CREATE INDEX IF NOT EXISTS idx_mastery_sm2_review_schedule
ON student_mastery_levels(student_id, next_review_recommended_at, ease_factor)
WHERE next_review_recommended_at IS NOT NULL;

COMMENT ON INDEX idx_mastery_sm2_review_schedule IS
    'Optimizes SM-2 review scheduling queries by student and due date';

-- ============================================================================
-- VIEW: Students needing review today
-- ============================================================================
-- WHAT: View of all mastery records due for review
-- WHERE: Used by instructor dashboards and student review queues
-- WHY: Provides quick access to items requiring immediate attention

CREATE OR REPLACE VIEW v_due_for_review AS
SELECT
    sml.id,
    sml.student_id,
    sml.skill_topic,
    sml.organization_id,
    sml.course_id,
    sml.mastery_level,
    sml.mastery_score,
    sml.ease_factor,
    sml.repetition_count,
    sml.current_interval_days,
    sml.last_quality_rating,
    sml.next_review_recommended_at,
    sml.last_assessment_at,
    u.username AS student_name,
    u.email AS student_email,
    o.name AS organization_name,
    CASE
        WHEN sml.next_review_recommended_at <= CURRENT_TIMESTAMP THEN 'overdue'
        WHEN sml.next_review_recommended_at <= CURRENT_TIMESTAMP + INTERVAL '1 day' THEN 'due_today'
        WHEN sml.next_review_recommended_at <= CURRENT_TIMESTAMP + INTERVAL '7 days' THEN 'due_this_week'
        ELSE 'scheduled'
    END AS review_urgency
FROM student_mastery_levels sml
JOIN users u ON sml.student_id = u.id
LEFT JOIN organizations o ON sml.organization_id = o.id
WHERE sml.next_review_recommended_at IS NOT NULL
ORDER BY sml.next_review_recommended_at ASC;

COMMENT ON VIEW v_due_for_review IS
    'Items due for spaced repetition review, ordered by urgency';

-- ============================================================================
-- VIEW: Student SM-2 Statistics
-- ============================================================================
-- WHAT: Aggregate SM-2 statistics per student
-- WHERE: Used by analytics dashboards and learning effectiveness reports
-- WHY: Provides insight into student learning patterns and algorithm effectiveness

CREATE OR REPLACE VIEW v_student_sm2_stats AS
SELECT
    sml.student_id,
    u.username AS student_name,
    u.email AS student_email,
    sml.organization_id,
    o.name AS organization_name,
    COUNT(*) AS total_skills_tracked,
    COUNT(*) FILTER (WHERE sml.mastery_level IN ('proficient', 'expert', 'master')) AS skills_mastered,
    AVG(sml.ease_factor) AS avg_ease_factor,
    AVG(sml.repetition_count) AS avg_repetition_count,
    AVG(sml.current_interval_days) AS avg_interval_days,
    AVG(sml.mastery_score) AS avg_mastery_score,
    COUNT(*) FILTER (WHERE sml.next_review_recommended_at <= CURRENT_TIMESTAMP) AS reviews_overdue,
    COUNT(*) FILTER (WHERE sml.next_review_recommended_at <= CURRENT_TIMESTAMP + INTERVAL '1 day') AS reviews_due_today,
    MIN(sml.next_review_recommended_at) AS next_review_due
FROM student_mastery_levels sml
JOIN users u ON sml.student_id = u.id
LEFT JOIN organizations o ON sml.organization_id = o.id
GROUP BY sml.student_id, u.username, u.email, sml.organization_id, o.name;

COMMENT ON VIEW v_student_sm2_stats IS
    'Aggregate SM-2 spaced repetition statistics per student';

-- ============================================================================
-- FUNCTION: Calculate optimal review time
-- ============================================================================
-- WHAT: Calculates when a skill should next be reviewed based on SM-2
-- WHERE: Called by adaptive learning service after assessments
-- WHY: Centralizes SM-2 interval calculation in database for consistency

CREATE OR REPLACE FUNCTION calculate_sm2_next_review(
    p_current_interval INTEGER,
    p_ease_factor DECIMAL(3,2),
    p_repetition_count INTEGER,
    p_quality INTEGER
) RETURNS TABLE (
    next_interval INTEGER,
    new_ease_factor DECIMAL(3,2),
    new_repetition_count INTEGER
) AS $$
DECLARE
    v_next_interval INTEGER;
    v_new_ef DECIMAL(3,2);
    v_new_rep INTEGER;
    v_ef_adjustment DECIMAL(5,3);
BEGIN
    -- SM-2 Algorithm Implementation
    IF p_quality < 3 THEN
        -- Failed: reset repetition count, start over with 1-day interval
        v_new_rep := 0;
        v_next_interval := 1;
    ELSE
        -- Success: increment repetition count and calculate new interval
        v_new_rep := p_repetition_count + 1;

        IF v_new_rep = 1 THEN
            v_next_interval := 1;  -- First successful review: 1 day
        ELSIF v_new_rep = 2 THEN
            v_next_interval := 6;  -- Second successful review: 6 days
        ELSE
            -- Subsequent reviews: multiply by ease factor
            v_next_interval := ROUND(p_current_interval * p_ease_factor);
        END IF;
    END IF;

    -- Calculate new ease factor using SM-2 formula:
    -- EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    -- where q is quality rating (0-5)
    v_ef_adjustment := 0.1 - (5 - p_quality) * (0.08 + (5 - p_quality) * 0.02);
    v_new_ef := p_ease_factor + v_ef_adjustment;

    -- Clamp ease factor to valid range [1.3, 2.5]
    v_new_ef := GREATEST(1.30, LEAST(2.50, v_new_ef));

    RETURN QUERY SELECT v_next_interval, v_new_ef, v_new_rep;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_sm2_next_review IS
    'Calculates SM-2 algorithm outputs: next interval, new ease factor, and repetition count';

-- ============================================================================
-- UPDATE EXISTING RECORDS
-- ============================================================================
-- WHAT: Initialize SM-2 fields for existing mastery records
-- WHERE: Applied to all existing student_mastery_levels rows
-- WHY: Ensures existing data works with the new SM-2 system

-- Set initial ease factor based on current mastery level
UPDATE student_mastery_levels
SET
    ease_factor = CASE mastery_level
        WHEN 'master' THEN 2.50
        WHEN 'expert' THEN 2.40
        WHEN 'proficient' THEN 2.30
        WHEN 'intermediate' THEN 2.20
        WHEN 'beginner' THEN 2.10
        ELSE 2.50  -- novice gets default
    END,
    -- Set repetition count based on assessments completed
    repetition_count = LEAST(assessments_passed, 10),
    -- Set interval based on practice streak or default
    current_interval_days = GREATEST(1, LEAST(practice_streak_days, 30)),
    -- Estimate quality from average score
    last_quality_rating = CASE
        WHEN average_score IS NULL THEN 0
        WHEN average_score >= 95 THEN 5
        WHEN average_score >= 80 THEN 4
        WHEN average_score >= 60 THEN 3
        WHEN average_score >= 40 THEN 2
        WHEN average_score >= 20 THEN 1
        ELSE 0
    END
WHERE ease_factor = 2.50
  AND repetition_count = 0
  AND current_interval_days = 1
  AND last_quality_rating = 0;

-- Migration complete
