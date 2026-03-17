-- Migration: 025_interactive_content_types.sql
-- Description: Creates tables for interactive content types (Enhancement 5)
-- Date: 2025-01-28

-- WHAT: Database schema for interactive learning content
-- WHERE: Used by content-management service for storing interactive elements
-- WHY: Enables creation and management of engaging, interactive educational content
--      including simulations, drag-drop activities, interactive diagrams,
--      code playgrounds, branching scenarios, timelines, flashcards, and videos

-- =============================================================================
-- Enum Types
-- =============================================================================

-- Interactive content types
DO $$ BEGIN
    CREATE TYPE interactive_content_type AS ENUM (
        'simulation',
        'drag_drop',
        'interactive_diagram',
        'code_playground',
        'branching_scenario',
        'interactive_timeline',
        'flashcard',
        'flashcard_deck',
        'interactive_video',
        'hotspot_image',
        'sorting_activity',
        'matching_pairs',
        'fill_in_blanks',
        'virtual_lab'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Interactive element status
DO $$ BEGIN
    CREATE TYPE interactive_element_status AS ENUM (
        'draft',
        'review',
        'approved',
        'published',
        'archived',
        'deprecated'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Difficulty levels
DO $$ BEGIN
    CREATE TYPE difficulty_level AS ENUM (
        'beginner',
        'intermediate',
        'advanced',
        'expert'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Code languages for playground
DO $$ BEGIN
    CREATE TYPE code_language AS ENUM (
        'python',
        'javascript',
        'typescript',
        'java',
        'csharp',
        'cpp',
        'go',
        'rust',
        'ruby',
        'php',
        'sql',
        'html',
        'css',
        'bash'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Interaction event types
DO $$ BEGIN
    CREATE TYPE interaction_event_type AS ENUM (
        'started',
        'interacted',
        'paused',
        'resumed',
        'completed',
        'skipped',
        'reset',
        'hint_requested',
        'answer_submitted',
        'feedback_viewed'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Interactive Elements (base table for all interactive content)
CREATE TABLE IF NOT EXISTS interactive_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    content_type interactive_content_type NOT NULL,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    module_id UUID REFERENCES modules(id) ON DELETE SET NULL,
    lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
    creator_id UUID NOT NULL REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Status and versioning
    status interactive_element_status NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,

    -- Learning attributes
    difficulty_level difficulty_level NOT NULL DEFAULT 'intermediate',
    estimated_duration_minutes INTEGER NOT NULL DEFAULT 10,
    learning_objectives TEXT[] DEFAULT '{}',
    prerequisites UUID[] DEFAULT '{}',

    -- Engagement settings
    max_attempts INTEGER NOT NULL DEFAULT 0, -- 0 = unlimited
    hints_enabled BOOLEAN NOT NULL DEFAULT true,
    feedback_immediate BOOLEAN NOT NULL DEFAULT true,
    allow_skip BOOLEAN NOT NULL DEFAULT true,
    points_value INTEGER NOT NULL DEFAULT 10,

    -- Accessibility
    accessibility_description TEXT DEFAULT '',
    screen_reader_text TEXT DEFAULT '',
    keyboard_navigable BOOLEAN NOT NULL DEFAULT true,
    high_contrast_available BOOLEAN NOT NULL DEFAULT false,

    -- Analytics (denormalized for performance)
    total_attempts INTEGER NOT NULL DEFAULT 0,
    total_completions INTEGER NOT NULL DEFAULT 0,
    avg_completion_time_seconds FLOAT NOT NULL DEFAULT 0.0,
    avg_score FLOAT NOT NULL DEFAULT 0.0,
    engagement_score FLOAT NOT NULL DEFAULT 0.0,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    custom_properties JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- Simulations
-- =============================================================================

CREATE TABLE IF NOT EXISTS simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    scenario_description TEXT NOT NULL,

    -- Configuration
    initial_state JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    expected_outcomes JSONB DEFAULT '[]',

    -- Execution settings
    simulation_type VARCHAR(50) NOT NULL DEFAULT 'guided', -- guided, sandbox, challenge
    time_limit_seconds INTEGER NOT NULL DEFAULT 0,
    max_steps INTEGER NOT NULL DEFAULT 0,
    allow_reset BOOLEAN NOT NULL DEFAULT true,
    save_checkpoints BOOLEAN NOT NULL DEFAULT true,

    -- Guided mode
    guided_steps JSONB DEFAULT '[]',
    show_hints BOOLEAN NOT NULL DEFAULT true,
    hint_penalty_percent INTEGER NOT NULL DEFAULT 10,

    -- Scoring
    scoring_rubric JSONB DEFAULT '{}',
    passing_score INTEGER NOT NULL DEFAULT 70,
    partial_credit BOOLEAN NOT NULL DEFAULT true,

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Drag & Drop Activities
-- =============================================================================

CREATE TABLE IF NOT EXISTS drag_drop_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- categorize, match, order, sort
    instructions TEXT NOT NULL,

    -- Behavior settings
    shuffle_items BOOLEAN NOT NULL DEFAULT true,
    shuffle_zones BOOLEAN NOT NULL DEFAULT false,
    show_item_count_per_zone BOOLEAN NOT NULL DEFAULT true,
    allow_reorder BOOLEAN NOT NULL DEFAULT true,
    snap_to_zone BOOLEAN NOT NULL DEFAULT true,

    -- Feedback settings
    show_correct_placement BOOLEAN NOT NULL DEFAULT true,
    show_feedback_on_drop BOOLEAN NOT NULL DEFAULT false,
    show_feedback_on_submit BOOLEAN NOT NULL DEFAULT true,

    -- Scoring
    partial_credit BOOLEAN NOT NULL DEFAULT true,
    deduct_for_incorrect BOOLEAN NOT NULL DEFAULT false,
    deduction_percent INTEGER NOT NULL DEFAULT 10,

    -- Visual settings
    item_style JSONB DEFAULT '{}',
    zone_style JSONB DEFAULT '{}',

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Drag drop items
CREATE TABLE IF NOT EXISTS drag_drop_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES drag_drop_activities(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    image_url TEXT,
    correct_zone_ids UUID[] DEFAULT '{}',
    feedback_correct TEXT DEFAULT '',
    feedback_incorrect TEXT DEFAULT '',
    points INTEGER NOT NULL DEFAULT 10,
    order_index INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Drop zones
CREATE TABLE IF NOT EXISTS drop_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES drag_drop_activities(id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    accepts_multiple BOOLEAN NOT NULL DEFAULT false,
    max_items INTEGER NOT NULL DEFAULT 1,
    position JSONB DEFAULT '{}',
    style JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Interactive Diagrams
-- =============================================================================

CREATE TABLE IF NOT EXISTS interactive_diagrams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    base_image_url TEXT NOT NULL,

    -- Interaction settings
    zoom_enabled BOOLEAN NOT NULL DEFAULT true,
    pan_enabled BOOLEAN NOT NULL DEFAULT true,
    min_zoom FLOAT NOT NULL DEFAULT 0.5,
    max_zoom FLOAT NOT NULL DEFAULT 3.0,

    -- Guided tour
    guided_tour_enabled BOOLEAN NOT NULL DEFAULT true,
    tour_hotspot_order UUID[] DEFAULT '{}',
    tour_auto_advance_seconds INTEGER NOT NULL DEFAULT 0,

    -- Quiz mode
    quiz_mode_enabled BOOLEAN NOT NULL DEFAULT false,
    quiz_passing_score INTEGER NOT NULL DEFAULT 70,

    -- Visual settings
    highlight_on_hover BOOLEAN NOT NULL DEFAULT true,
    show_labels BOOLEAN NOT NULL DEFAULT true,
    label_position VARCHAR(20) NOT NULL DEFAULT 'bottom',

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Diagram layers
CREATE TABLE IF NOT EXISTS diagram_layers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagram_id UUID NOT NULL REFERENCES interactive_diagrams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    image_url TEXT NOT NULL,
    is_visible BOOLEAN NOT NULL DEFAULT true,
    is_base_layer BOOLEAN NOT NULL DEFAULT false,
    opacity FLOAT NOT NULL DEFAULT 1.0,
    order_index INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hotspots
CREATE TABLE IF NOT EXISTS hotspots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagram_id UUID NOT NULL REFERENCES interactive_diagrams(id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    shape VARCHAR(50) NOT NULL DEFAULT 'circle',
    coordinates JSONB NOT NULL DEFAULT '{}',
    popup_content TEXT DEFAULT '',
    popup_media_url TEXT,
    linked_content_id UUID,
    is_quiz_point BOOLEAN NOT NULL DEFAULT false,
    quiz_question TEXT,
    quiz_answer TEXT,
    style JSONB DEFAULT '{}',
    order_index INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Code Playgrounds
-- =============================================================================

CREATE TABLE IF NOT EXISTS code_playgrounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    instructions TEXT NOT NULL,

    -- Language settings
    language code_language NOT NULL DEFAULT 'python',
    language_version VARCHAR(20) NOT NULL DEFAULT '3.10',

    -- Code templates
    starter_code TEXT DEFAULT '',
    solution_code TEXT DEFAULT '',
    test_code TEXT DEFAULT '',
    hidden_test_code TEXT DEFAULT '',

    -- Execution settings
    timeout_seconds INTEGER NOT NULL DEFAULT 30,
    memory_limit_mb INTEGER NOT NULL DEFAULT 128,
    allowed_imports TEXT[] DEFAULT '{}',
    blocked_imports TEXT[] DEFAULT '{}',

    -- Test cases stored as JSONB array
    test_cases JSONB DEFAULT '[]',

    -- Behavior settings
    show_expected_output BOOLEAN NOT NULL DEFAULT false,
    show_test_cases BOOLEAN NOT NULL DEFAULT true,
    allow_solution_view BOOLEAN NOT NULL DEFAULT false,
    auto_run_on_change BOOLEAN NOT NULL DEFAULT false,

    -- Scoring
    passing_score INTEGER NOT NULL DEFAULT 70,
    partial_credit BOOLEAN NOT NULL DEFAULT true,

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Branching Scenarios
-- =============================================================================

CREATE TABLE IF NOT EXISTS branching_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    introduction TEXT NOT NULL,

    -- Configuration
    start_branch_id UUID,
    max_score INTEGER NOT NULL DEFAULT 100,
    passing_score INTEGER NOT NULL DEFAULT 70,
    track_path BOOLEAN NOT NULL DEFAULT true,

    -- Behavior settings
    allow_backtrack BOOLEAN NOT NULL DEFAULT false,
    show_path_on_complete BOOLEAN NOT NULL DEFAULT true,
    show_optimal_path BOOLEAN NOT NULL DEFAULT false,

    -- Visual settings
    visual_style VARCHAR(50) NOT NULL DEFAULT 'cards',
    show_progress BOOLEAN NOT NULL DEFAULT true,

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scenario branches
CREATE TABLE IF NOT EXISTS scenario_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES branching_scenarios(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    media_url TEXT,

    -- Options (JSONB array)
    options JSONB DEFAULT '[]',

    -- Branch properties
    is_start BOOLEAN NOT NULL DEFAULT false,
    is_end BOOLEAN NOT NULL DEFAULT false,
    is_success_end BOOLEAN NOT NULL DEFAULT false,
    is_failure_end BOOLEAN NOT NULL DEFAULT false,
    points_value INTEGER NOT NULL DEFAULT 0,

    -- Feedback
    branch_feedback TEXT DEFAULT '',
    style JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Interactive Timelines
-- =============================================================================

CREATE TABLE IF NOT EXISTS interactive_timelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT DEFAULT '',

    -- Time range
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    time_scale VARCHAR(20) NOT NULL DEFAULT 'years',

    -- Categories as JSONB array
    categories JSONB DEFAULT '[]',

    -- Interaction settings
    zoom_enabled BOOLEAN NOT NULL DEFAULT true,
    filter_by_category BOOLEAN NOT NULL DEFAULT true,
    show_milestones_only BOOLEAN NOT NULL DEFAULT false,
    comparison_mode BOOLEAN NOT NULL DEFAULT false,

    -- Visual settings
    orientation VARCHAR(20) NOT NULL DEFAULT 'horizontal',
    event_density VARCHAR(20) NOT NULL DEFAULT 'normal',
    show_event_images BOOLEAN NOT NULL DEFAULT true,

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Timeline events
CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES interactive_timelines(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT DEFAULT '',
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,
    date_display VARCHAR(255) DEFAULT '',

    -- Content
    content TEXT DEFAULT '',
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    media_url TEXT,

    -- Properties
    category VARCHAR(100) DEFAULT '',
    importance INTEGER NOT NULL DEFAULT 1,
    is_milestone BOOLEAN NOT NULL DEFAULT false,
    linked_content_ids UUID[] DEFAULT '{}',

    -- Visual
    icon VARCHAR(100) DEFAULT '',
    color VARCHAR(20) DEFAULT '',
    style JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Flashcard Decks
-- =============================================================================

CREATE TABLE IF NOT EXISTS flashcard_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    description TEXT DEFAULT '',

    -- Study settings
    new_cards_per_day INTEGER NOT NULL DEFAULT 20,
    reviews_per_day INTEGER NOT NULL DEFAULT 100,
    shuffle_new BOOLEAN NOT NULL DEFAULT true,
    shuffle_review BOOLEAN NOT NULL DEFAULT true,

    -- Display settings
    show_remaining BOOLEAN NOT NULL DEFAULT true,
    flip_animation BOOLEAN NOT NULL DEFAULT true,
    auto_flip_seconds INTEGER NOT NULL DEFAULT 0,

    -- Progress (denormalized)
    total_reviews INTEGER NOT NULL DEFAULT 0,
    correct_reviews INTEGER NOT NULL DEFAULT 0,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_study_date TIMESTAMP WITH TIME ZONE,

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Flashcards
CREATE TABLE IF NOT EXISTS flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID NOT NULL REFERENCES flashcard_decks(id) ON DELETE CASCADE,
    front_content TEXT NOT NULL,
    back_content TEXT NOT NULL,
    front_content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    back_content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    front_media_url TEXT,
    back_media_url TEXT,

    -- Spaced repetition data
    difficulty FLOAT NOT NULL DEFAULT 2.5,
    interval_days INTEGER NOT NULL DEFAULT 1,
    repetitions INTEGER NOT NULL DEFAULT 0,
    next_review TIMESTAMP WITH TIME ZONE,
    last_reviewed TIMESTAMP WITH TIME ZONE,

    -- Learning data
    times_correct INTEGER NOT NULL DEFAULT 0,
    times_incorrect INTEGER NOT NULL DEFAULT 0,

    -- Tags
    tags TEXT[] DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- Interactive Videos
-- =============================================================================

CREATE TABLE IF NOT EXISTS interactive_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT DEFAULT '',

    -- Video source
    video_url TEXT NOT NULL,
    video_duration_seconds FLOAT NOT NULL DEFAULT 0.0,
    thumbnail_url TEXT,

    -- Chapters as JSONB array
    chapters JSONB DEFAULT '[]',

    -- Transcript
    transcript_url TEXT,
    captions_url TEXT,
    show_transcript BOOLEAN NOT NULL DEFAULT true,

    -- Playback settings
    allow_skip_interactions BOOLEAN NOT NULL DEFAULT false,
    require_all_interactions BOOLEAN NOT NULL DEFAULT false,
    allow_playback_speed BOOLEAN NOT NULL DEFAULT true,
    allow_seek BOOLEAN NOT NULL DEFAULT true,

    -- Completion criteria
    watch_percentage_required INTEGER NOT NULL DEFAULT 80,
    interactions_percentage_required INTEGER NOT NULL DEFAULT 100,
    passing_score INTEGER NOT NULL DEFAULT 70,

    -- State
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video interactions
CREATE TABLE IF NOT EXISTS video_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES interactive_videos(id) ON DELETE CASCADE,
    timestamp_seconds FLOAT NOT NULL,
    interaction_type VARCHAR(50) NOT NULL, -- question, hotspot, branch, pause, note

    -- Content
    title VARCHAR(255) DEFAULT '',
    content TEXT DEFAULT '',
    media_url TEXT,

    -- Question data
    question TEXT,
    options JSONB DEFAULT '[]',
    correct_answer TEXT,
    explanation TEXT DEFAULT '',
    points INTEGER NOT NULL DEFAULT 10,

    -- Behavior
    pause_video BOOLEAN NOT NULL DEFAULT true,
    required BOOLEAN NOT NULL DEFAULT false,
    skip_allowed BOOLEAN NOT NULL DEFAULT true,

    -- Display
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    position JSONB DEFAULT '{}',
    style JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- User Interaction Sessions
-- =============================================================================

CREATE TABLE IF NOT EXISTS interaction_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID NOT NULL REFERENCES interactive_elements(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Session timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT NOT NULL DEFAULT 0.0,

    -- Progress
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress', -- in_progress, completed, abandoned
    completion_percentage FLOAT NOT NULL DEFAULT 0.0,

    -- Scoring
    score FLOAT NOT NULL DEFAULT 0.0,
    max_score FLOAT NOT NULL DEFAULT 100.0,
    passed BOOLEAN NOT NULL DEFAULT false,

    -- Engagement
    attempts INTEGER NOT NULL DEFAULT 1,
    hints_used INTEGER NOT NULL DEFAULT 0,
    actions_count INTEGER NOT NULL DEFAULT 0,

    -- Data
    state_data JSONB DEFAULT '{}',
    actions JSONB DEFAULT '[]',

    -- Metadata
    device_type VARCHAR(50) DEFAULT '',
    browser VARCHAR(100) DEFAULT ''
);

-- User-specific flashcard progress (separate from deck-level progress)
CREATE TABLE IF NOT EXISTS user_flashcard_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,

    -- Spaced repetition data (user-specific)
    difficulty FLOAT NOT NULL DEFAULT 2.5,
    interval_days INTEGER NOT NULL DEFAULT 1,
    repetitions INTEGER NOT NULL DEFAULT 0,
    next_review TIMESTAMP WITH TIME ZONE,
    last_reviewed TIMESTAMP WITH TIME ZONE,

    -- Learning data
    times_correct INTEGER NOT NULL DEFAULT 0,
    times_incorrect INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, card_id)
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Interactive elements indexes
CREATE INDEX IF NOT EXISTS idx_interactive_elements_course ON interactive_elements(course_id);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_module ON interactive_elements(module_id);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_lesson ON interactive_elements(lesson_id);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_creator ON interactive_elements(creator_id);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_org ON interactive_elements(organization_id);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_type ON interactive_elements(content_type);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_status ON interactive_elements(status);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_difficulty ON interactive_elements(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_interactive_elements_tags ON interactive_elements USING GIN(tags);

-- Simulations
CREATE INDEX IF NOT EXISTS idx_simulations_element ON simulations(element_id);

-- Drag drop
CREATE INDEX IF NOT EXISTS idx_drag_drop_element ON drag_drop_activities(element_id);
CREATE INDEX IF NOT EXISTS idx_drag_drop_items_activity ON drag_drop_items(activity_id);
CREATE INDEX IF NOT EXISTS idx_drop_zones_activity ON drop_zones(activity_id);

-- Diagrams
CREATE INDEX IF NOT EXISTS idx_diagrams_element ON interactive_diagrams(element_id);
CREATE INDEX IF NOT EXISTS idx_diagram_layers_diagram ON diagram_layers(diagram_id);
CREATE INDEX IF NOT EXISTS idx_hotspots_diagram ON hotspots(diagram_id);

-- Code playgrounds
CREATE INDEX IF NOT EXISTS idx_code_playgrounds_element ON code_playgrounds(element_id);
CREATE INDEX IF NOT EXISTS idx_code_playgrounds_language ON code_playgrounds(language);

-- Branching scenarios
CREATE INDEX IF NOT EXISTS idx_branching_element ON branching_scenarios(element_id);
CREATE INDEX IF NOT EXISTS idx_scenario_branches_scenario ON scenario_branches(scenario_id);

-- Timelines
CREATE INDEX IF NOT EXISTS idx_timelines_element ON interactive_timelines(element_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_timeline ON timeline_events(timeline_id);
CREATE INDEX IF NOT EXISTS idx_timeline_events_date ON timeline_events(event_date);

-- Flashcards
CREATE INDEX IF NOT EXISTS idx_flashcard_decks_element ON flashcard_decks(element_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_deck ON flashcards(deck_id);
CREATE INDEX IF NOT EXISTS idx_flashcards_next_review ON flashcards(next_review);
CREATE INDEX IF NOT EXISTS idx_user_flashcard_progress_user ON user_flashcard_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_flashcard_progress_card ON user_flashcard_progress(card_id);
CREATE INDEX IF NOT EXISTS idx_user_flashcard_progress_next_review ON user_flashcard_progress(next_review);

-- Videos
CREATE INDEX IF NOT EXISTS idx_videos_element ON interactive_videos(element_id);
CREATE INDEX IF NOT EXISTS idx_video_interactions_video ON video_interactions(video_id);
CREATE INDEX IF NOT EXISTS idx_video_interactions_timestamp ON video_interactions(timestamp_seconds);

-- Sessions
CREATE INDEX IF NOT EXISTS idx_interaction_sessions_element ON interaction_sessions(element_id);
CREATE INDEX IF NOT EXISTS idx_interaction_sessions_user ON interaction_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_interaction_sessions_status ON interaction_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interaction_sessions_started ON interaction_sessions(started_at);

-- =============================================================================
-- Triggers
-- =============================================================================

-- Update timestamps trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_interactive_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
DROP TRIGGER IF EXISTS trg_interactive_elements_updated ON interactive_elements;
CREATE TRIGGER trg_interactive_elements_updated
    BEFORE UPDATE ON interactive_elements
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_simulations_updated ON simulations;
CREATE TRIGGER trg_simulations_updated
    BEFORE UPDATE ON simulations
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_drag_drop_updated ON drag_drop_activities;
CREATE TRIGGER trg_drag_drop_updated
    BEFORE UPDATE ON drag_drop_activities
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_diagrams_updated ON interactive_diagrams;
CREATE TRIGGER trg_diagrams_updated
    BEFORE UPDATE ON interactive_diagrams
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_code_playgrounds_updated ON code_playgrounds;
CREATE TRIGGER trg_code_playgrounds_updated
    BEFORE UPDATE ON code_playgrounds
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_branching_updated ON branching_scenarios;
CREATE TRIGGER trg_branching_updated
    BEFORE UPDATE ON branching_scenarios
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_timelines_updated ON interactive_timelines;
CREATE TRIGGER trg_timelines_updated
    BEFORE UPDATE ON interactive_timelines
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_flashcard_decks_updated ON flashcard_decks;
CREATE TRIGGER trg_flashcard_decks_updated
    BEFORE UPDATE ON flashcard_decks
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_flashcards_updated ON flashcards;
CREATE TRIGGER trg_flashcards_updated
    BEFORE UPDATE ON flashcards
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_videos_updated ON interactive_videos;
CREATE TRIGGER trg_videos_updated
    BEFORE UPDATE ON interactive_videos
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

DROP TRIGGER IF EXISTS trg_user_flashcard_progress_updated ON user_flashcard_progress;
CREATE TRIGGER trg_user_flashcard_progress_updated
    BEFORE UPDATE ON user_flashcard_progress
    FOR EACH ROW EXECUTE FUNCTION update_interactive_updated_at();

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE interactive_elements IS 'Base table for all interactive learning content with common attributes';
COMMENT ON TABLE simulations IS 'Virtual simulations with configurable parameters and outcomes';
COMMENT ON TABLE drag_drop_activities IS 'Drag-and-drop activities for categorization, matching, and ordering';
COMMENT ON TABLE interactive_diagrams IS 'Interactive images/diagrams with clickable hotspots and layers';
COMMENT ON TABLE code_playgrounds IS 'In-browser code editing and execution environments';
COMMENT ON TABLE branching_scenarios IS 'Decision-tree based interactive learning scenarios';
COMMENT ON TABLE interactive_timelines IS 'Chronological exploration of events and concepts';
COMMENT ON TABLE flashcard_decks IS 'Collections of flashcards with spaced repetition support';
COMMENT ON TABLE flashcards IS 'Individual flashcards with front/back content';
COMMENT ON TABLE interactive_videos IS 'Videos with embedded questions and interactions';
COMMENT ON TABLE interaction_sessions IS 'User session tracking for interactive content analytics';
