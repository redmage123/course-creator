-- ============================================================================
-- Migration 024: AI-Powered Content Generation V2
-- ============================================================================
--
-- WHAT: Database schema for advanced AI content generation system
-- WHERE: Enhancement 4 of course-creator platform
-- WHY: Provides structured tracking of generation requests, quality metrics,
--      templates, refinements, batch operations, and analytics for improved
--      AI content quality and performance monitoring
--
-- Tables Created:
--   - generation_requests: Tracks all content generation requests
--   - generation_results: Stores generated content with metadata
--   - content_quality_scores: Multi-dimensional quality assessment
--   - generation_templates: Customizable generation templates
--   - content_refinements: Iterative content improvements
--   - batch_generations: Bulk generation operations
--   - generation_analytics: Performance and quality tracking
--
-- Business Rules:
--   - All generated content must be scored for quality before publishing
--   - Templates define generation parameters and expected output structure
--   - Refinements are limited to prevent infinite loops
--   - Batch operations have size limits for resource management
-- ============================================================================

-- Enum Types for Content Generation V2
-- ============================================================================

-- Content types that can be generated
CREATE TYPE generation_content_type AS ENUM (
    'syllabus',
    'slides',
    'quiz',
    'exercise',
    'learning_objectives',
    'summary',
    'assessment_rubric',
    'discussion_prompts',
    'case_study'
);

-- Status states for generation requests
CREATE TYPE generation_status AS ENUM (
    'pending',
    'validating',
    'generating',
    'enhancing',
    'reviewing',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

-- Quality classification for generated content
CREATE TYPE quality_level AS ENUM (
    'excellent',
    'good',
    'acceptable',
    'needs_work',
    'poor'
);

-- Types of content refinement operations
CREATE TYPE refinement_type AS ENUM (
    'expand',
    'simplify',
    'restructure',
    'correct',
    'tone_adjust',
    'difficulty_adjust',
    'add_examples',
    'add_exercises'
);

-- Status states for batch generation operations
CREATE TYPE batch_status AS ENUM (
    'created',
    'queued',
    'processing',
    'completed',
    'partial',
    'failed',
    'cancelled'
);

-- Categories for generation templates
CREATE TYPE template_category AS ENUM (
    'standard',
    'technical',
    'business',
    'creative',
    'scientific',
    'language',
    'compliance',
    'custom'
);


-- ============================================================================
-- Table: generation_requests
-- ============================================================================
-- WHAT: Tracks all content generation requests with full parameters
-- WHERE: Created when user initiates content generation
-- WHY: Enables auditing, caching, analytics, and retry functionality
-- ============================================================================

CREATE TABLE IF NOT EXISTS generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    content_type generation_content_type NOT NULL,
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    module_id UUID,  -- Optional reference to specific module
    template_id UUID,  -- Reference to generation_templates

    -- Status tracking
    status generation_status NOT NULL DEFAULT 'pending',

    -- Generation parameters (stored as JSONB for flexibility)
    parameters JSONB NOT NULL DEFAULT '{}',
    difficulty_level VARCHAR(50) NOT NULL DEFAULT 'intermediate',
    target_audience VARCHAR(50) NOT NULL DEFAULT 'general',
    language VARCHAR(10) NOT NULL DEFAULT 'en',

    -- Model settings
    model_name VARCHAR(100) NOT NULL DEFAULT 'claude-3-sonnet-20240229',
    max_tokens INTEGER NOT NULL DEFAULT 4096,
    temperature DECIMAL(3, 2) NOT NULL DEFAULT 0.70,
    use_rag BOOLEAN NOT NULL DEFAULT TRUE,
    use_cache BOOLEAN NOT NULL DEFAULT TRUE,

    -- Retry configuration
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_count INTEGER NOT NULL DEFAULT 0,

    -- Timing
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Results
    result_id UUID,  -- Reference to generation_results
    error_message TEXT,

    -- Token usage and costs
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for generation_requests
CREATE INDEX idx_generation_requests_course ON generation_requests(course_id);
CREATE INDEX idx_generation_requests_requester ON generation_requests(requester_id);
CREATE INDEX idx_generation_requests_org ON generation_requests(organization_id);
CREATE INDEX idx_generation_requests_status ON generation_requests(status);
CREATE INDEX idx_generation_requests_content_type ON generation_requests(content_type);
CREATE INDEX idx_generation_requests_created ON generation_requests(created_at DESC);
CREATE INDEX idx_generation_requests_template ON generation_requests(template_id);

-- ============================================================================
-- Table: generation_results
-- ============================================================================
-- WHAT: Stores generated content with metadata
-- WHERE: Created when generation completes successfully
-- WHY: Preserves both raw and processed content for retrieval, caching, versioning
-- ============================================================================

CREATE TABLE IF NOT EXISTS generation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES generation_requests(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    content_type generation_content_type NOT NULL,

    -- Content storage
    raw_output TEXT NOT NULL,  -- Raw AI-generated text
    processed_content JSONB NOT NULL DEFAULT '{}',  -- Parsed/structured content

    -- Quality tracking
    quality_score_id UUID,  -- Reference to content_quality_scores
    quality_level quality_level NOT NULL DEFAULT 'acceptable',

    -- Generation metadata
    model_used VARCHAR(100) NOT NULL DEFAULT '',
    generation_method VARCHAR(20) NOT NULL DEFAULT 'ai',  -- ai, template, hybrid
    rag_context_used BOOLEAN NOT NULL DEFAULT FALSE,
    cached BOOLEAN NOT NULL DEFAULT FALSE,
    cache_key VARCHAR(255),

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    parent_result_id UUID REFERENCES generation_results(id),  -- For refinements

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ  -- For cache expiration
);

-- Indexes for generation_results
CREATE INDEX idx_generation_results_request ON generation_results(request_id);
CREATE INDEX idx_generation_results_course ON generation_results(course_id);
CREATE INDEX idx_generation_results_content_type ON generation_results(content_type);
CREATE INDEX idx_generation_results_quality ON generation_results(quality_level);
CREATE INDEX idx_generation_results_cache_key ON generation_results(cache_key);
CREATE INDEX idx_generation_results_created ON generation_results(created_at DESC);
CREATE INDEX idx_generation_results_parent ON generation_results(parent_result_id);

-- ============================================================================
-- Table: content_quality_scores
-- ============================================================================
-- WHAT: Multi-dimensional quality assessment for generated content
-- WHERE: Created during quality review phase
-- WHY: Provides detailed quality metrics for content evaluation and feedback
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_quality_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID NOT NULL REFERENCES generation_results(id) ON DELETE CASCADE,

    -- Dimension scores (0-100)
    accuracy_score INTEGER NOT NULL DEFAULT 0 CHECK (accuracy_score BETWEEN 0 AND 100),
    relevance_score INTEGER NOT NULL DEFAULT 0 CHECK (relevance_score BETWEEN 0 AND 100),
    completeness_score INTEGER NOT NULL DEFAULT 0 CHECK (completeness_score BETWEEN 0 AND 100),
    clarity_score INTEGER NOT NULL DEFAULT 0 CHECK (clarity_score BETWEEN 0 AND 100),
    structure_score INTEGER NOT NULL DEFAULT 0 CHECK (structure_score BETWEEN 0 AND 100),
    engagement_score INTEGER NOT NULL DEFAULT 0 CHECK (engagement_score BETWEEN 0 AND 100),
    difficulty_alignment_score INTEGER NOT NULL DEFAULT 0 CHECK (difficulty_alignment_score BETWEEN 0 AND 100),

    -- Calculated scores
    overall_score INTEGER NOT NULL DEFAULT 0 CHECK (overall_score BETWEEN 0 AND 100),
    quality_level quality_level NOT NULL DEFAULT 'acceptable',

    -- Dimension weights (stored as JSONB for flexibility)
    weights JSONB NOT NULL DEFAULT '{
        "accuracy": 0.20,
        "relevance": 0.15,
        "completeness": 0.15,
        "clarity": 0.20,
        "structure": 0.10,
        "engagement": 0.10,
        "difficulty_alignment": 0.10
    }',

    -- Scoring metadata
    scoring_method VARCHAR(20) NOT NULL DEFAULT 'automated',  -- automated, manual, hybrid
    scorer_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- For manual scoring
    confidence DECIMAL(3, 2) NOT NULL DEFAULT 0.00 CHECK (confidence BETWEEN 0 AND 1),

    -- Feedback (stored as JSONB arrays)
    strengths JSONB NOT NULL DEFAULT '[]',
    weaknesses JSONB NOT NULL DEFAULT '[]',
    improvement_suggestions JSONB NOT NULL DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for content_quality_scores
CREATE INDEX idx_content_quality_scores_result ON content_quality_scores(result_id);
CREATE INDEX idx_content_quality_scores_level ON content_quality_scores(quality_level);
CREATE INDEX idx_content_quality_scores_overall ON content_quality_scores(overall_score);
CREATE INDEX idx_content_quality_scores_scorer ON content_quality_scores(scorer_id);

-- ============================================================================
-- Table: generation_templates
-- ============================================================================
-- WHAT: Customizable templates defining content generation parameters
-- WHERE: Used to standardize and customize content generation
-- WHY: Enables consistent generation across similar content types
-- ============================================================================

CREATE TABLE IF NOT EXISTS generation_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    content_type generation_content_type NOT NULL,
    category template_category NOT NULL DEFAULT 'standard',

    -- Template configuration
    system_prompt TEXT NOT NULL DEFAULT '',
    user_prompt_template TEXT NOT NULL DEFAULT '',
    output_schema JSONB NOT NULL DEFAULT '{}',  -- JSON Schema for expected output
    required_variables JSONB NOT NULL DEFAULT '[]',  -- Variables needed in prompts

    -- Default generation parameters
    default_parameters JSONB NOT NULL DEFAULT '{}',
    difficulty_levels JSONB NOT NULL DEFAULT '["beginner", "intermediate", "advanced"]',
    target_audiences JSONB NOT NULL DEFAULT '["general", "technical", "business"]',

    -- Ownership
    creator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    is_global BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,

    -- Quality settings
    min_quality_score INTEGER NOT NULL DEFAULT 60,
    auto_retry_on_low_quality BOOLEAN NOT NULL DEFAULT TRUE,
    max_auto_retries INTEGER NOT NULL DEFAULT 2,

    -- Usage tracking
    usage_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    avg_quality_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMPTZ,

    -- Ensure unique names within organization
    CONSTRAINT unique_template_name_per_org UNIQUE NULLS NOT DISTINCT (name, organization_id)
);

-- Indexes for generation_templates
CREATE INDEX idx_generation_templates_content_type ON generation_templates(content_type);
CREATE INDEX idx_generation_templates_category ON generation_templates(category);
CREATE INDEX idx_generation_templates_creator ON generation_templates(creator_id);
CREATE INDEX idx_generation_templates_org ON generation_templates(organization_id);
CREATE INDEX idx_generation_templates_active ON generation_templates(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_generation_templates_global ON generation_templates(is_global) WHERE is_global = TRUE;

-- ============================================================================
-- Table: content_refinements
-- ============================================================================
-- WHAT: Tracks refinement operations on generated content
-- WHERE: Created when user requests content improvement
-- WHY: Enables iterative content improvements based on feedback
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_refinements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id UUID NOT NULL REFERENCES generation_results(id) ON DELETE CASCADE,
    refinement_type refinement_type NOT NULL,
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Refinement details
    feedback TEXT NOT NULL DEFAULT '',
    specific_instructions TEXT NOT NULL DEFAULT '',
    target_sections JSONB NOT NULL DEFAULT '[]',  -- Specific sections to refine

    -- Configuration
    preserve_structure BOOLEAN NOT NULL DEFAULT TRUE,
    max_changes INTEGER NOT NULL DEFAULT 5,

    -- Results
    refined_result_id UUID REFERENCES generation_results(id),
    status generation_status NOT NULL DEFAULT 'pending',
    changes_made JSONB NOT NULL DEFAULT '[]',

    -- Quality comparison
    original_quality_score INTEGER NOT NULL DEFAULT 0,
    refined_quality_score INTEGER NOT NULL DEFAULT 0,
    quality_improvement INTEGER NOT NULL DEFAULT 0,

    -- Iteration tracking
    iteration_number INTEGER NOT NULL DEFAULT 1,
    max_iterations INTEGER NOT NULL DEFAULT 5,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

-- Indexes for content_refinements
CREATE INDEX idx_content_refinements_result ON content_refinements(result_id);
CREATE INDEX idx_content_refinements_requester ON content_refinements(requester_id);
CREATE INDEX idx_content_refinements_type ON content_refinements(refinement_type);
CREATE INDEX idx_content_refinements_status ON content_refinements(status);
CREATE INDEX idx_content_refinements_refined ON content_refinements(refined_result_id);

-- ============================================================================
-- Table: batch_generations
-- ============================================================================
-- WHAT: Tracks batch generation operations
-- WHERE: Created for bulk content generation
-- WHY: Enables efficient generation of multiple related content pieces
-- ============================================================================

CREATE TABLE IF NOT EXISTS batch_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,

    -- Batch configuration
    shared_parameters JSONB NOT NULL DEFAULT '{}',
    content_types JSONB NOT NULL DEFAULT '[]',  -- Array of content types
    target_modules JSONB NOT NULL DEFAULT '[]',  -- Array of module UUIDs

    -- Batch limits
    max_batch_size INTEGER NOT NULL DEFAULT 50,
    parallel_workers INTEGER NOT NULL DEFAULT 5,

    -- Items tracking
    request_ids JSONB NOT NULL DEFAULT '[]',  -- Array of request UUIDs

    -- Status tracking
    status batch_status NOT NULL DEFAULT 'created',
    total_items INTEGER NOT NULL DEFAULT 0,
    completed_items INTEGER NOT NULL DEFAULT 0,
    failed_items INTEGER NOT NULL DEFAULT 0,

    -- Progress
    progress_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    current_item_index INTEGER NOT NULL DEFAULT 0,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    estimated_completion TIMESTAMPTZ,

    -- Costs
    total_estimated_cost DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,
    actual_cost DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for batch_generations
CREATE INDEX idx_batch_generations_course ON batch_generations(course_id);
CREATE INDEX idx_batch_generations_requester ON batch_generations(requester_id);
CREATE INDEX idx_batch_generations_org ON batch_generations(organization_id);
CREATE INDEX idx_batch_generations_status ON batch_generations(status);
CREATE INDEX idx_batch_generations_created ON batch_generations(created_at DESC);

-- ============================================================================
-- Table: generation_analytics
-- ============================================================================
-- WHAT: Analytics tracking for content generation operations
-- WHERE: Updated after each generation operation
-- WHY: Provides insights into generation performance, costs, and quality
-- ============================================================================

CREATE TABLE IF NOT EXISTS generation_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    period_start TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    period_end TIMESTAMPTZ,

    -- Volume metrics
    total_requests INTEGER NOT NULL DEFAULT 0,
    completed_requests INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0,
    cached_responses INTEGER NOT NULL DEFAULT 0,

    -- Performance metrics
    avg_generation_time_seconds DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    min_generation_time_seconds DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    max_generation_time_seconds DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_generation_time_seconds DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    -- Token metrics
    total_input_tokens BIGINT NOT NULL DEFAULT 0,
    total_output_tokens BIGINT NOT NULL DEFAULT 0,
    avg_tokens_per_request DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    -- Cost metrics
    total_cost DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,
    avg_cost_per_request DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,
    cost_savings_from_cache DECIMAL(10, 4) NOT NULL DEFAULT 0.0000,

    -- Quality metrics
    avg_quality_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    excellent_count INTEGER NOT NULL DEFAULT 0,
    good_count INTEGER NOT NULL DEFAULT 0,
    acceptable_count INTEGER NOT NULL DEFAULT 0,
    needs_work_count INTEGER NOT NULL DEFAULT 0,
    poor_count INTEGER NOT NULL DEFAULT 0,

    -- Content type breakdown
    content_type_counts JSONB NOT NULL DEFAULT '{}',

    -- Refinement metrics
    total_refinements INTEGER NOT NULL DEFAULT 0,
    successful_refinements INTEGER NOT NULL DEFAULT 0,
    avg_quality_improvement DECIMAL(5, 2) NOT NULL DEFAULT 0.00,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for generation_analytics
CREATE INDEX idx_generation_analytics_org ON generation_analytics(organization_id);
CREATE INDEX idx_generation_analytics_period ON generation_analytics(period_start, period_end);
CREATE INDEX idx_generation_analytics_created ON generation_analytics(created_at DESC);


-- ============================================================================
-- Add foreign key from generation_requests to generation_results
-- ============================================================================
ALTER TABLE generation_requests
    ADD CONSTRAINT fk_generation_requests_result
    FOREIGN KEY (result_id) REFERENCES generation_results(id) ON DELETE SET NULL;

-- Add foreign key from generation_requests to generation_templates
ALTER TABLE generation_requests
    ADD CONSTRAINT fk_generation_requests_template
    FOREIGN KEY (template_id) REFERENCES generation_templates(id) ON DELETE SET NULL;

-- Add foreign key from generation_results to content_quality_scores
ALTER TABLE generation_results
    ADD CONSTRAINT fk_generation_results_quality
    FOREIGN KEY (quality_score_id) REFERENCES content_quality_scores(id) ON DELETE SET NULL;


-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to update generation_requests.updated_at timestamp
CREATE OR REPLACE FUNCTION update_generation_requests_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update generation_templates.updated_at timestamp
CREATE OR REPLACE FUNCTION update_generation_templates_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update batch_generations.updated_at timestamp
CREATE OR REPLACE FUNCTION update_batch_generations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update content_quality_scores.updated_at timestamp
CREATE OR REPLACE FUNCTION update_content_quality_scores_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update generation_analytics.updated_at timestamp
CREATE OR REPLACE FUNCTION update_generation_analytics_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Triggers for timestamp updates
-- ============================================================================

CREATE TRIGGER trigger_update_generation_requests_timestamp
    BEFORE UPDATE ON generation_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_generation_requests_timestamp();

CREATE TRIGGER trigger_update_generation_templates_timestamp
    BEFORE UPDATE ON generation_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_generation_templates_timestamp();

CREATE TRIGGER trigger_update_batch_generations_timestamp
    BEFORE UPDATE ON batch_generations
    FOR EACH ROW
    EXECUTE FUNCTION update_batch_generations_timestamp();

CREATE TRIGGER trigger_update_content_quality_scores_timestamp
    BEFORE UPDATE ON content_quality_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_content_quality_scores_timestamp();

CREATE TRIGGER trigger_update_generation_analytics_timestamp
    BEFORE UPDATE ON generation_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_generation_analytics_timestamp();


-- ============================================================================
-- Insert default global templates
-- ============================================================================

INSERT INTO generation_templates (
    id,
    name,
    description,
    content_type,
    category,
    system_prompt,
    user_prompt_template,
    output_schema,
    required_variables,
    is_global,
    is_active
) VALUES
(
    gen_random_uuid(),
    'Standard Syllabus Generator',
    'Generates comprehensive course syllabi with learning objectives, topics, and assessment methods',
    'syllabus',
    'standard',
    'You are an expert curriculum designer. Create detailed, well-structured syllabi that align with learning objectives and best practices in instructional design.',
    'Create a syllabus for a course titled "{{course_title}}" for {{target_audience}} learners at the {{difficulty_level}} level. The course should cover: {{topics}}',
    '{"type": "object", "properties": {"overview": {"type": "string"}, "objectives": {"type": "array"}, "topics": {"type": "array"}, "assessment": {"type": "object"}}}',
    '["course_title", "target_audience", "difficulty_level", "topics"]',
    TRUE,
    TRUE
),
(
    gen_random_uuid(),
    'Interactive Quiz Generator',
    'Generates quiz questions with multiple formats including multiple choice, true/false, and short answer',
    'quiz',
    'standard',
    'You are an expert assessment designer. Create engaging quiz questions that effectively test understanding while being fair and clear.',
    'Create {{question_count}} quiz questions for the topic "{{topic}}" at the {{difficulty_level}} level. Include a mix of question types suitable for {{target_audience}} learners.',
    '{"type": "object", "properties": {"questions": {"type": "array", "items": {"type": "object", "properties": {"question": {"type": "string"}, "type": {"type": "string"}, "options": {"type": "array"}, "correct_answer": {"type": "string"}, "explanation": {"type": "string"}}}}}}',
    '["topic", "question_count", "difficulty_level", "target_audience"]',
    TRUE,
    TRUE
),
(
    gen_random_uuid(),
    'Slide Deck Generator',
    'Generates presentation slide content with clear structure and engaging visuals suggestions',
    'slides',
    'standard',
    'You are an expert presentation designer. Create slide content that is clear, engaging, and visually organized with appropriate use of bullet points and visual cues.',
    'Create slide content for a {{slide_count}}-slide presentation on "{{topic}}" for {{target_audience}} learners. Focus on key concepts and include speaker notes.',
    '{"type": "object", "properties": {"slides": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "array"}, "speaker_notes": {"type": "string"}, "visual_suggestions": {"type": "array"}}}}}}',
    '["topic", "slide_count", "target_audience"]',
    TRUE,
    TRUE
),
(
    gen_random_uuid(),
    'Learning Objectives Generator',
    'Generates measurable learning objectives using Blooms taxonomy',
    'learning_objectives',
    'standard',
    'You are an expert in instructional design and Blooms taxonomy. Create measurable, actionable learning objectives that guide effective instruction.',
    'Create {{objective_count}} learning objectives for the topic "{{topic}}" at the {{difficulty_level}} level. Use action verbs from Blooms taxonomy appropriate for {{target_audience}} learners.',
    '{"type": "object", "properties": {"objectives": {"type": "array", "items": {"type": "object", "properties": {"objective": {"type": "string"}, "bloom_level": {"type": "string"}, "assessment_method": {"type": "string"}}}}}}',
    '["topic", "objective_count", "difficulty_level", "target_audience"]',
    TRUE,
    TRUE
),
(
    gen_random_uuid(),
    'Case Study Generator',
    'Generates realistic case studies with scenarios, questions, and teaching notes',
    'case_study',
    'business',
    'You are an expert case study writer. Create realistic, engaging case studies that promote critical thinking and practical application of concepts.',
    'Create a case study on "{{topic}}" for {{target_audience}} learners. The case should present a realistic {{industry}} scenario with clear decision points and discussion questions.',
    '{"type": "object", "properties": {"title": {"type": "string"}, "scenario": {"type": "string"}, "background": {"type": "string"}, "challenges": {"type": "array"}, "questions": {"type": "array"}, "teaching_notes": {"type": "string"}}}',
    '["topic", "target_audience", "industry"]',
    TRUE,
    TRUE
);


-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE generation_requests IS 'Tracks all AI content generation requests with parameters, status, and results';
COMMENT ON TABLE generation_results IS 'Stores generated content with raw output, processed content, and quality metrics';
COMMENT ON TABLE content_quality_scores IS 'Multi-dimensional quality assessment for generated content';
COMMENT ON TABLE generation_templates IS 'Customizable templates defining content generation parameters and prompts';
COMMENT ON TABLE content_refinements IS 'Tracks iterative refinement operations on generated content';
COMMENT ON TABLE batch_generations IS 'Manages bulk content generation operations with progress tracking';
COMMENT ON TABLE generation_analytics IS 'Aggregated analytics for generation performance, costs, and quality';

COMMENT ON TYPE generation_content_type IS 'Types of educational content that can be AI-generated';
COMMENT ON TYPE generation_status IS 'Lifecycle states for content generation requests';
COMMENT ON TYPE quality_level IS 'Quality classification levels for generated content';
COMMENT ON TYPE refinement_type IS 'Types of content refinement operations';
COMMENT ON TYPE batch_status IS 'Status states for batch generation operations';
COMMENT ON TYPE template_category IS 'Categories for organizing generation templates';
