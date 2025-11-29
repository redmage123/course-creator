-- Migration: 023_peer_learning_system.sql
-- WHAT: Creates tables for Peer Learning system
-- WHERE: Used by course-management service for collaborative learning
-- WHY: Enables study groups, peer reviews, discussions, and help requests
--      to improve learning outcomes through peer collaboration

-- Enhancement 3: Peer Learning System
-- Features:
-- 1. Study Groups - Collaborative learning groups
-- 2. Peer Reviews - Student-to-student feedback
-- 3. Discussion Threads - Course forums
-- 4. Help Requests - Peer-to-peer assistance
-- 5. Reputation System - Gamified peer contribution tracking

-- ============================================================================
-- STUDY GROUPS TABLE
-- ============================================================================
-- WHAT: Stores collaborative study groups for courses
-- WHERE: Created by students, accessed via course interface
-- WHY: Enables peer-to-peer learning and collaboration

CREATE TABLE IF NOT EXISTS study_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Group identity
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Association
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    creator_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Status and configuration
    status VARCHAR(20) NOT NULL DEFAULT 'forming'
        CHECK (status IN ('forming', 'active', 'paused', 'completed', 'disbanded')),
    is_public BOOLEAN NOT NULL DEFAULT true,
    min_members INTEGER NOT NULL DEFAULT 2 CHECK (min_members >= 2),
    max_members INTEGER NOT NULL DEFAULT 10 CHECK (max_members >= min_members),
    current_member_count INTEGER NOT NULL DEFAULT 0 CHECK (current_member_count >= 0),

    -- Meeting info
    meeting_schedule TEXT,  -- JSON or cron expression
    meeting_platform VARCHAR(50),  -- zoom, discord, in_app, etc.
    meeting_link TEXT,

    -- Goals and tags
    goals JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_study_groups_course ON study_groups(course_id);
CREATE INDEX idx_study_groups_track ON study_groups(track_id);
CREATE INDEX idx_study_groups_org ON study_groups(organization_id);
CREATE INDEX idx_study_groups_status ON study_groups(status);
CREATE INDEX idx_study_groups_public ON study_groups(is_public) WHERE is_public = true;

COMMENT ON TABLE study_groups IS 'Collaborative study groups for peer learning';

-- ============================================================================
-- STUDY GROUP MEMBERSHIPS TABLE
-- ============================================================================
-- WHAT: Links users to study groups with roles
-- WHERE: Referenced when checking group membership and permissions
-- WHY: Tracks membership details, roles, and activity

CREATE TABLE IF NOT EXISTS study_group_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    study_group_id UUID NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role and status
    role VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('leader', 'co_leader', 'member', 'observer')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'inactive', 'left', 'removed')),

    -- Activity tracking
    contribution_score INTEGER NOT NULL DEFAULT 0,
    sessions_attended INTEGER NOT NULL DEFAULT 0,
    last_active_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    joined_at TIMESTAMP WITH TIME ZONE,
    left_at TIMESTAMP WITH TIME ZONE,

    -- One membership per user per group
    CONSTRAINT unique_group_membership UNIQUE (study_group_id, user_id)
);

CREATE INDEX idx_memberships_group ON study_group_memberships(study_group_id);
CREATE INDEX idx_memberships_user ON study_group_memberships(user_id);
CREATE INDEX idx_memberships_status ON study_group_memberships(status);
CREATE INDEX idx_memberships_active ON study_group_memberships(study_group_id, status)
    WHERE status = 'active';

COMMENT ON TABLE study_group_memberships IS 'User memberships in study groups';

-- ============================================================================
-- PEER REVIEWS TABLE
-- ============================================================================
-- WHAT: Stores peer review assignments and feedback
-- WHERE: Created when assignments require peer review
-- WHY: Enables structured peer feedback for learning improvement

CREATE TABLE IF NOT EXISTS peer_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Assignment context
    assignment_id UUID NOT NULL,  -- References assignment system
    submission_id UUID NOT NULL,  -- The work being reviewed
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Participants
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Work author
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- Reviewer

    -- Configuration
    is_anonymous BOOLEAN NOT NULL DEFAULT true,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'submitted', 'revised', 'disputed', 'accepted')),

    -- Review content
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    rubric_scores JSONB DEFAULT '{}',  -- criterion: score
    strengths TEXT,
    improvements TEXT,
    detailed_feedback TEXT,

    -- Timing
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    due_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE,

    -- Quality tracking
    quality_rating VARCHAR(20) CHECK (quality_rating IN ('poor', 'fair', 'good', 'excellent')),
    helpfulness_score INTEGER CHECK (helpfulness_score >= 1 AND helpfulness_score <= 5),
    reviewer_reputation_delta INTEGER DEFAULT 0,

    -- Metadata
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Prevent self-review
    CONSTRAINT no_self_review CHECK (author_id != reviewer_id)
);

CREATE INDEX idx_peer_reviews_assignment ON peer_reviews(assignment_id);
CREATE INDEX idx_peer_reviews_author ON peer_reviews(author_id);
CREATE INDEX idx_peer_reviews_reviewer ON peer_reviews(reviewer_id);
CREATE INDEX idx_peer_reviews_status ON peer_reviews(status);
CREATE INDEX idx_peer_reviews_due ON peer_reviews(due_at) WHERE status = 'pending';
CREATE INDEX idx_peer_reviews_course ON peer_reviews(course_id);

COMMENT ON TABLE peer_reviews IS 'Peer review assignments and feedback';

-- ============================================================================
-- DISCUSSION THREADS TABLE
-- ============================================================================
-- WHAT: Forum discussion threads for courses and study groups
-- WHERE: Displayed in course forums and group discussions
-- WHY: Enables asynchronous peer discussions and Q&A

CREATE TABLE IF NOT EXISTS discussion_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,

    -- Context
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    study_group_id UUID REFERENCES study_groups(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    parent_thread_id UUID REFERENCES discussion_threads(id) ON DELETE CASCADE,

    -- Status and flags
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'answered', 'locked', 'archived', 'hidden')),
    is_question BOOLEAN NOT NULL DEFAULT false,
    is_answered BOOLEAN NOT NULL DEFAULT false,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    best_answer_id UUID,  -- References discussion_replies(id), added later

    -- Categorization
    tags JSONB DEFAULT '[]',

    -- Engagement metrics
    view_count INTEGER NOT NULL DEFAULT 0,
    reply_count INTEGER NOT NULL DEFAULT 0,
    upvote_count INTEGER NOT NULL DEFAULT 0,
    downvote_count INTEGER NOT NULL DEFAULT 0,

    -- Activity tracking
    last_reply_at TIMESTAMP WITH TIME ZONE,
    last_reply_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_threads_course ON discussion_threads(course_id);
CREATE INDEX idx_threads_group ON discussion_threads(study_group_id);
CREATE INDEX idx_threads_author ON discussion_threads(author_id);
CREATE INDEX idx_threads_status ON discussion_threads(status);
CREATE INDEX idx_threads_pinned ON discussion_threads(course_id, is_pinned) WHERE is_pinned = true;
CREATE INDEX idx_threads_recent ON discussion_threads(course_id, last_reply_at DESC NULLS LAST);
CREATE INDEX idx_threads_popular ON discussion_threads(course_id, view_count DESC);

COMMENT ON TABLE discussion_threads IS 'Forum discussion threads for peer learning';

-- ============================================================================
-- DISCUSSION REPLIES TABLE
-- ============================================================================
-- WHAT: Replies to discussion threads
-- WHERE: Linked to discussion_threads
-- WHY: Enables threaded discussions

CREATE TABLE IF NOT EXISTS discussion_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    thread_id UUID NOT NULL REFERENCES discussion_threads(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_reply_id UUID REFERENCES discussion_replies(id) ON DELETE CASCADE,

    -- Content
    content TEXT NOT NULL,

    -- Flags
    is_best_answer BOOLEAN NOT NULL DEFAULT false,
    is_edited BOOLEAN NOT NULL DEFAULT false,
    is_hidden BOOLEAN NOT NULL DEFAULT false,

    -- Engagement
    upvote_count INTEGER NOT NULL DEFAULT 0,
    downvote_count INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE
);

-- Add foreign key for best_answer_id after discussion_replies exists
ALTER TABLE discussion_threads
    ADD CONSTRAINT fk_best_answer
    FOREIGN KEY (best_answer_id) REFERENCES discussion_replies(id) ON DELETE SET NULL;

CREATE INDEX idx_replies_thread ON discussion_replies(thread_id);
CREATE INDEX idx_replies_author ON discussion_replies(author_id);
CREATE INDEX idx_replies_parent ON discussion_replies(parent_reply_id);
CREATE INDEX idx_replies_best ON discussion_replies(thread_id, is_best_answer) WHERE is_best_answer = true;

COMMENT ON TABLE discussion_replies IS 'Replies to discussion threads';

-- ============================================================================
-- HELP REQUESTS TABLE
-- ============================================================================
-- WHAT: Peer-to-peer help requests
-- WHERE: Created when students need assistance
-- WHY: Connects students needing help with knowledgeable peers

CREATE TABLE IF NOT EXISTS help_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Requester info
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,

    -- Classification
    category VARCHAR(30) NOT NULL DEFAULT 'general'
        CHECK (category IN ('concept', 'practice', 'debugging', 'project', 'exam_prep', 'career', 'general')),
    skill_topic VARCHAR(255),

    -- Context
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Status and helper
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'claimed', 'in_progress', 'resolved', 'cancelled', 'expired')),
    helper_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_anonymous BOOLEAN NOT NULL DEFAULT false,

    -- Priority
    urgency INTEGER NOT NULL DEFAULT 5 CHECK (urgency >= 1 AND urgency <= 10),

    -- Duration tracking
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,

    -- Resolution
    resolution_notes TEXT,
    requester_rating INTEGER CHECK (requester_rating >= 1 AND requester_rating <= 5),
    helper_rating INTEGER CHECK (helper_rating >= 1 AND helper_rating <= 5),
    reputation_earned INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    claimed_at TIMESTAMP WITH TIME ZONE,
    session_started_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_help_requests_requester ON help_requests(requester_id);
CREATE INDEX idx_help_requests_helper ON help_requests(helper_id);
CREATE INDEX idx_help_requests_status ON help_requests(status);
CREATE INDEX idx_help_requests_course ON help_requests(course_id);
CREATE INDEX idx_help_requests_category ON help_requests(category);
CREATE INDEX idx_help_requests_open ON help_requests(status, urgency DESC)
    WHERE status = 'open';
CREATE INDEX idx_help_requests_skill ON help_requests(skill_topic)
    WHERE skill_topic IS NOT NULL;

COMMENT ON TABLE help_requests IS 'Peer-to-peer help requests';

-- ============================================================================
-- PEER REPUTATIONS TABLE
-- ============================================================================
-- WHAT: Tracks peer learning reputation scores
-- WHERE: Updated on peer interactions
-- WHY: Gamifies peer learning and identifies helpful students

CREATE TABLE IF NOT EXISTS peer_reputations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User reference
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Score breakdown
    overall_score INTEGER NOT NULL DEFAULT 0,
    review_score INTEGER NOT NULL DEFAULT 0,
    help_score INTEGER NOT NULL DEFAULT 0,
    discussion_score INTEGER NOT NULL DEFAULT 0,
    group_score INTEGER NOT NULL DEFAULT 0,

    -- Activity counts
    reviews_given INTEGER NOT NULL DEFAULT 0,
    reviews_received INTEGER NOT NULL DEFAULT 0,
    help_sessions_given INTEGER NOT NULL DEFAULT 0,
    help_sessions_received INTEGER NOT NULL DEFAULT 0,
    discussions_started INTEGER NOT NULL DEFAULT 0,
    helpful_answers INTEGER NOT NULL DEFAULT 0,

    -- Level and badges
    level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1 AND level <= 10),
    badges JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- One reputation record per user per organization
    CONSTRAINT unique_user_reputation UNIQUE (user_id, organization_id)
);

CREATE INDEX idx_reputation_user ON peer_reputations(user_id);
CREATE INDEX idx_reputation_org ON peer_reputations(organization_id);
CREATE INDEX idx_reputation_score ON peer_reputations(overall_score DESC);
CREATE INDEX idx_reputation_level ON peer_reputations(level);

COMMENT ON TABLE peer_reputations IS 'Peer learning reputation tracking';

-- ============================================================================
-- THREAD VOTES TABLE
-- ============================================================================
-- WHAT: Tracks upvotes/downvotes on threads and replies
-- WHERE: Referenced when users vote
-- WHY: Prevents duplicate votes and tracks voting history

CREATE TABLE IF NOT EXISTS discussion_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference (either thread or reply)
    thread_id UUID REFERENCES discussion_threads(id) ON DELETE CASCADE,
    reply_id UUID REFERENCES discussion_replies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Vote type
    vote_type VARCHAR(10) NOT NULL CHECK (vote_type IN ('upvote', 'downvote')),

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Exactly one of thread_id or reply_id must be set
    CONSTRAINT vote_target_check CHECK (
        (thread_id IS NOT NULL AND reply_id IS NULL) OR
        (thread_id IS NULL AND reply_id IS NOT NULL)
    ),

    -- One vote per user per target
    CONSTRAINT unique_thread_vote UNIQUE (thread_id, user_id),
    CONSTRAINT unique_reply_vote UNIQUE (reply_id, user_id)
);

CREATE INDEX idx_votes_thread ON discussion_votes(thread_id) WHERE thread_id IS NOT NULL;
CREATE INDEX idx_votes_reply ON discussion_votes(reply_id) WHERE reply_id IS NOT NULL;
CREATE INDEX idx_votes_user ON discussion_votes(user_id);

COMMENT ON TABLE discussion_votes IS 'Voting records for discussions';

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Active study groups with member counts
CREATE OR REPLACE VIEW v_active_study_groups AS
SELECT
    sg.id,
    sg.name,
    sg.description,
    sg.course_id,
    sg.track_id,
    sg.organization_id,
    sg.status,
    sg.is_public,
    sg.min_members,
    sg.max_members,
    sg.current_member_count,
    sg.meeting_schedule,
    sg.meeting_platform,
    sg.created_at,
    sg.activated_at,
    c.title AS course_title,
    t.name AS track_name,
    o.name AS organization_name,
    (sg.max_members - sg.current_member_count) AS spots_available
FROM study_groups sg
LEFT JOIN courses c ON sg.course_id = c.id
LEFT JOIN tracks t ON sg.track_id = t.id
LEFT JOIN organizations o ON sg.organization_id = o.id
WHERE sg.status IN ('forming', 'active');

COMMENT ON VIEW v_active_study_groups IS 'Active study groups with availability info';

-- View: Open help requests by urgency
CREATE OR REPLACE VIEW v_open_help_requests AS
SELECT
    hr.id,
    hr.title,
    hr.description,
    hr.category,
    hr.skill_topic,
    hr.course_id,
    hr.organization_id,
    hr.urgency,
    hr.is_anonymous,
    hr.estimated_duration_minutes,
    hr.created_at,
    hr.expires_at,
    CASE WHEN hr.is_anonymous THEN NULL ELSE hr.requester_id END AS requester_id,
    CASE WHEN hr.is_anonymous THEN 'Anonymous' ELSE u.username END AS requester_name,
    c.title AS course_title,
    EXTRACT(EPOCH FROM (hr.expires_at - CURRENT_TIMESTAMP)) / 3600 AS hours_until_expiry
FROM help_requests hr
LEFT JOIN users u ON hr.requester_id = u.id
LEFT JOIN courses c ON hr.course_id = c.id
WHERE hr.status = 'open'
  AND (hr.expires_at IS NULL OR hr.expires_at > CURRENT_TIMESTAMP)
ORDER BY hr.urgency DESC, hr.created_at ASC;

COMMENT ON VIEW v_open_help_requests IS 'Open help requests ordered by urgency';

-- View: Discussion threads with activity
CREATE OR REPLACE VIEW v_discussion_threads_activity AS
SELECT
    dt.id,
    dt.title,
    dt.author_id,
    dt.course_id,
    dt.study_group_id,
    dt.status,
    dt.is_question,
    dt.is_answered,
    dt.is_pinned,
    dt.view_count,
    dt.reply_count,
    dt.upvote_count - dt.downvote_count AS net_votes,
    dt.created_at,
    dt.last_reply_at,
    u.username AS author_name,
    c.title AS course_title,
    COALESCE(dt.last_reply_at, dt.created_at) AS last_activity
FROM discussion_threads dt
JOIN users u ON dt.author_id = u.id
LEFT JOIN courses c ON dt.course_id = c.id
WHERE dt.status NOT IN ('hidden', 'archived')
ORDER BY dt.is_pinned DESC, last_activity DESC;

COMMENT ON VIEW v_discussion_threads_activity IS 'Discussion threads with activity metrics';

-- View: Top peer helpers (leaderboard)
CREATE OR REPLACE VIEW v_peer_leaderboard AS
SELECT
    pr.user_id,
    pr.organization_id,
    pr.overall_score,
    pr.level,
    pr.reviews_given,
    pr.help_sessions_given,
    pr.helpful_answers,
    u.username,
    u.email,
    o.name AS organization_name,
    pr.badges,
    RANK() OVER (PARTITION BY pr.organization_id ORDER BY pr.overall_score DESC) AS org_rank
FROM peer_reputations pr
JOIN users u ON pr.user_id = u.id
LEFT JOIN organizations o ON pr.organization_id = o.id
WHERE pr.overall_score > 0
ORDER BY pr.overall_score DESC;

COMMENT ON VIEW v_peer_leaderboard IS 'Peer learning reputation leaderboard';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Update thread reply count
CREATE OR REPLACE FUNCTION update_thread_reply_count() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE discussion_threads
        SET reply_count = reply_count + 1,
            last_reply_at = NEW.created_at,
            last_reply_by = NEW.author_id,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.thread_id;
    ELSIF TG_OP = 'DELETE' AND NOT OLD.is_hidden THEN
        UPDATE discussion_threads
        SET reply_count = GREATEST(0, reply_count - 1),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.thread_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_thread_reply_count
    AFTER INSERT OR DELETE ON discussion_replies
    FOR EACH ROW
    EXECUTE FUNCTION update_thread_reply_count();

-- Function: Update study group member count
CREATE OR REPLACE FUNCTION update_study_group_member_count() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'active' THEN
        UPDATE study_groups
        SET current_member_count = current_member_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.study_group_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != 'active' AND NEW.status = 'active' THEN
            UPDATE study_groups
            SET current_member_count = current_member_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.study_group_id;
        ELSIF OLD.status = 'active' AND NEW.status != 'active' THEN
            UPDATE study_groups
            SET current_member_count = GREATEST(0, current_member_count - 1),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.study_group_id;
        END IF;
    ELSIF TG_OP = 'DELETE' AND OLD.status = 'active' THEN
        UPDATE study_groups
        SET current_member_count = GREATEST(0, current_member_count - 1),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.study_group_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_member_count
    AFTER INSERT OR UPDATE OR DELETE ON study_group_memberships
    FOR EACH ROW
    EXECUTE FUNCTION update_study_group_member_count();

-- Function: Update vote counts
CREATE OR REPLACE FUNCTION update_vote_counts() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.thread_id IS NOT NULL THEN
            IF NEW.vote_type = 'upvote' THEN
                UPDATE discussion_threads SET upvote_count = upvote_count + 1 WHERE id = NEW.thread_id;
            ELSE
                UPDATE discussion_threads SET downvote_count = downvote_count + 1 WHERE id = NEW.thread_id;
            END IF;
        ELSIF NEW.reply_id IS NOT NULL THEN
            IF NEW.vote_type = 'upvote' THEN
                UPDATE discussion_replies SET upvote_count = upvote_count + 1 WHERE id = NEW.reply_id;
            ELSE
                UPDATE discussion_replies SET downvote_count = downvote_count + 1 WHERE id = NEW.reply_id;
            END IF;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.thread_id IS NOT NULL THEN
            IF OLD.vote_type = 'upvote' THEN
                UPDATE discussion_threads SET upvote_count = GREATEST(0, upvote_count - 1) WHERE id = OLD.thread_id;
            ELSE
                UPDATE discussion_threads SET downvote_count = GREATEST(0, downvote_count - 1) WHERE id = OLD.thread_id;
            END IF;
        ELSIF OLD.reply_id IS NOT NULL THEN
            IF OLD.vote_type = 'upvote' THEN
                UPDATE discussion_replies SET upvote_count = GREATEST(0, upvote_count - 1) WHERE id = OLD.reply_id;
            ELSE
                UPDATE discussion_replies SET downvote_count = GREATEST(0, downvote_count - 1) WHERE id = OLD.reply_id;
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_vote_counts
    AFTER INSERT OR DELETE ON discussion_votes
    FOR EACH ROW
    EXECUTE FUNCTION update_vote_counts();

-- Migration complete
